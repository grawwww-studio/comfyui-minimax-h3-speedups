#!/usr/bin/python3
"""EP09 speed-LoRA benchmark runner. Resumable: one record file per clip (settings x shots x seeds), done clips are skipped.
Rule: ../RULE.md (frozen 2026-11-11T21:42:23Z). Matrix: ../matrix.json. Stdlib only (comfy_lib.py is next to this file).

GPU part (needs a running ComfyUI; instance settings come from the environment, see INST below):
  bench.py --target lab|rig [--only id,id] [--seed N] [--shot wide|close] [--min-s 1500] [--max-clips N]
      runs the pending clips of that instance in matrix order. Stops at a SETTING boundary once --min-s seconds have run (so a setting is never split
      by a chunk), or when nothing is pending. The first clip this process runs for a setting is recorded cold=true (model load + LoRA patch).
CPU part (no GPU, no ComfyUI):
  bench.py --dry-run                  prints the matrix, the estimated GPU time and the output layout
  bench.py --status                   done / pending per setting
  bench.py --aggregate                review/speedlora_metrics.json from records + review/face/face_scores.jsonl (every on-screen figure is read from it)
Layout: clips/<setting>/<shot>_s<seed>.mp4 | review/records/<setting>__<shot>__s<seed>.json | review/face/ (scorer output) | review/speedlora_metrics.json | logs/events.jsonl
"""
import argparse, copy, hashlib, json, os, shutil, subprocess, sys, time, statistics, datetime
from pathlib import Path

E = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
MX = json.loads((E / "matrix.json").read_text())
SETTINGS = {s["id"]: s for s in MX["settings"]}
ORDER = [s["id"] for s in MX["settings"]]
# Two ComfyUI instances on the same card: "lab" runs every setting except hyper6, "rig" runs hyper6 and the base20 timing anchor (RULE.md, Amendment 2).
# Set per instance: COMFY_PORT_LAB / COMFY_CONTAINER_LAB / COMFY_INPUT_LAB / COMFY_OUTPUT_LAB (same with _RIG). The container name is used to read the
# process memory (docker inspect); the input and output folders are the ComfyUI folders as seen from this machine.
def _inst(k):
    return dict(port=int(os.environ.get(f"COMFY_PORT_{k}", "8188")), container=os.environ.get(f"COMFY_CONTAINER_{k}", "comfyui"),
                inp=Path(os.environ.get(f"COMFY_INPUT_{k}", "ComfyUI/input")), out=Path(os.environ.get(f"COMFY_OUTPUT_{k}", "ComfyUI/output")))
INST = {"lab": _inst("LAB"), "rig": _inst("RIG")}
REC = E / "review/records"; CLIPS = E / "clips"; EV = E / "logs/events.jsonl"
STAGE = ["sheet_T2.png", "plate_T2WIDE-L2.png", "plate_T2FRONT-z125-L2.png", "T2WIDE-L2_pad.wav"]
FIX_S, STEP_S = 38, 32.5   # measured on one smoke clip (lx4 wide s5207: gen 168.5 s, sampler 130.1 s / 4 steps); hyper6 uses its matrix estimate
def est_clip(s): return s["est_clip_s"] if s.get("unet") else round(FIX_S + s["steps"] * STEP_S)
WH_PER_S = 0.075      # earlier Pika clip on this card: 18.1 Wh / 242 s
COLD_S = 90           # est. extra seconds for a cold first clip of a setting


def now(): return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def ev(**k):
    EV.parent.mkdir(exist_ok=True); open(EV, "a").write(json.dumps(dict(utc=now(), **k)) + "\n")
def rid(s, shot, seed): return f"{s}__{shot}__s{seed}"
def matrix(target=None):
    for sid in ORDER:
        s = SETTINGS[sid]
        if target and s["instance"] != target: continue
        for shot in MX["shots"]:
            for seed in s.get("seeds", MX["seeds"]): yield sid, shot, seed
def done(sid, shot, seed):
    p = REC / (rid(sid, shot, seed) + ".json")
    if not p.exists(): return False
    d = json.loads(p.read_text()); return d.get("ok") or d.get("failed_twice")


def build_graph(sid, shot, seed):
    s = SETTINGS[sid]; g = json.loads((E / MX["shots"][shot]["graph"]).read_text()); g = copy.deepcopy(g)
    g["129"]["inputs"]["noise_seed"] = seed
    g["300"]["inputs"]["image"] = "h3_speedups/sheet_T2.png"; g["301"]["inputs"]["image"] = "h3_speedups/" + Path(MX["shots"][shot]["plate"]).name
    g["303"]["inputs"]["audio"] = "h3_speedups/T2WIDE-L2_pad.wav"; g["305"]["inputs"]["audio"] = "h3_speedups/T2WIDE-L2_pad.wav"
    g["312"]["inputs"]["filename_prefix"] = "h3_speedups/" + rid(sid, shot, seed)
    assert g["143"]["inputs"]["lora_name"].startswith("pika_h3_flex_ref2va"), "template drifted"
    model = ["127", 0]
    if s.get("unet"):                                                    # HyperFlow: its own loader replaces UNET + LoRA
        g["127"] = {"class_type": s["loader"], "inputs": {"unet_name": s["unet"]}}; del g["143"]
    elif s["lora"]:
        g["143"]["inputs"]["lora_name"] = s["lora"]; g["143"]["inputs"]["strength_model"] = s["lora_strength"]; model = ["143", 0]
    else:
        del g["143"]
    if s.get("shift_video") is not None:
        g["150"] = {"class_type": "MiniMaxH3SigmaShift", "inputs": {"model": model, "shift_video": s["shift_video"], "shift_audio": s["shift_audio"]}}; model = ["150", 0]
    g["126"]["inputs"]["model"] = model
    g["123"]["inputs"]["sampler_name"] = s["sampler"]
    sg = s["sigmas"]
    if sg.startswith("manual:"):
        g["124"]["inputs"]["sigmas"] = sg[7:]                              # the production graph's own ManualSigmas node
    elif sg == "simple":
        g["124"] = {"class_type": "BasicScheduler", "inputs": {"model": model, "scheduler": "simple", "steps": s["steps"], "denoise": 1.0}}
    elif sg.startswith("hyperflow:"):
        g["124"] = {"class_type": "HyperFlowSigmas", "inputs": {"model": model, "steps": int(sg.split(":")[1])}}
    else: raise SystemExit("unknown sigmas " + sg)
    return g


def ffprobe(p):
    o = subprocess.check_output(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries", "stream=width,height,nb_read_frames,r_frame_rate", "-of", "json", str(p)], text=True)
    return json.loads(o)["streams"][0]
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""): h.update(b)
    return h.hexdigest()


def run_target(a):
    import comfy_lib as L
    I = INST[a.target]; L.PORT = I["port"]; L.BASE = f"http://{L.HOST}:{L.PORT}"; L.CONTAINER = I["container"]
    try: L.api("/system_stats", timeout=10)
    except Exception as e: print("instance not up:", e); return 3
    (I["inp"] / "h3_speedups").mkdir(exist_ok=True)
    for n in STAGE: shutil.copy2(E / "inputs" / n, I["inp"] / "h3_speedups" / n)
    pend = [m for m in matrix(a.target) if not done(*m) and (not a.only or m[0] in a.only.split(",")) and (not a.seed or m[2] == a.seed) and (not a.shot or m[1] == a.shot)]
    print(f"{len(pend)} pending on {a.target}"); ev(stage="start", target=a.target, pending=len(pend))
    t_proc = time.time(); seen = set(); last = None; n = 0; rc = 0
    for sid, shot, seed in pend:
        if last and sid != last and time.time() - t_proc >= a.min_s: print("setting boundary after min-s: stop"); break
        if a.max_clips and n >= a.max_clips: break
        last = sid; cold = sid not in seen; seen.add(sid)
        rec = dict(setting=sid, shot=shot, seed=seed, instance=a.target, cold=cold, frames_asked=MX["frames"], size=f"{MX['width']}x{MX['height']}", steps=SETTINGS[sid]["steps"])
        for attempt in (1, 2):
            g = build_graph(sid, shot, seed); (E / "review/graphs").mkdir(parents=True, exist_ok=True)
            (E / f"review/graphs/{rid(sid, shot, seed)}.api.json").write_text(json.dumps(g, indent=1))
            cpid, cg = L.container_pid_cgroup(); tr = L.Trace(cpid, cg); time.sleep(1.5)
            r = L.run_profiled(g, tr, timeout=2400); w = tr.window(r["t_start"], r["t_end"]); tr.stop()
            rec.update(utc=now(), attempt=attempt, ok=r["ok"], error=r.get("error"), gen_s=r.get("wall_s"), node_s=r.get("node_s"), cached_nodes=len(r.get("cached") or []), **w)
            outs = [o for o in r.get("outputs", []) if o["filename"].endswith(".mp4")]
            if r["ok"] and outs:
                src = I["out"] / outs[-1].get("subfolder", "") / outs[-1]["filename"]; dst = CLIPS / sid / f"{shot}_s{seed}.mp4"; dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst); pr = ffprobe(dst); rec.update(clip=str(dst.relative_to(E)), clip_sha256=sha(dst), clip_frames=int(pr["nb_read_frames"]), clip_size=f"{pr['width']}x{pr['height']}", clip_fps=pr["r_frame_rate"])
                sampler = (r.get("node_s") or {}).get("125"); rec["sampler_s"] = sampler
                break
            rec["ok"] = False
        if not rec["ok"]: rec["failed_twice"] = True; rc = 2
        REC.mkdir(parents=True, exist_ok=True); (REC / (rid(sid, shot, seed) + ".json")).write_text(json.dumps(rec, indent=1))
        ev(stage="clip", id=rid(sid, shot, seed), ok=rec["ok"], gen_s=rec.get("gen_s"), peak_mib=rec.get("peak_mib"), cold=cold, instance=a.target)
        print(rid(sid, shot, seed), "ok" if rec["ok"] else "FAILED", rec.get("gen_s"), "s", rec.get("peak_mib"), "MiB", "cold" if cold else "", flush=True); n += 1
    ev(stage="end", target=a.target, clips=n, wall_s=round(time.time() - t_proc)); return rc


def dry_run():
    tot = 0; print(f"RULE sha/time: {open(E/'RULE.md').read().splitlines()[-1][:120]}")
    print(f"frames {MX['frames']} @ {MX['fps']} fps, {MX['width']}x{MX['height']}, seeds {MX['seeds']}, shots {list(MX['shots'])}")
    print(f"{'setting':8} {'inst':4} {'clips':>5} {'est s/clip':>10} {'est total s':>11}  label")
    for sid in ORDER:
        s = SETTINGS[sid]; n = len(MX["shots"]) * len(s.get("seeds", MX["seeds"])); t = n * est_clip(s) + COLD_S; tot += t
        print(f"{sid:8} {s['instance']:4} {n:5d} {est_clip(s):10d} {t:11d}  {s['label']}")
    print(f"TOTAL clips {sum(1 for _ in matrix())}  est GPU {tot} s = {tot/3600:.2f} h, est energy {tot*WH_PER_S:.0f} Wh (0.075 Wh/s)")
    print("headline settings (the five): " + ", ".join(i for i in ORDER if SETTINGS[i]["headline"]) + "; report-only: " + ", ".join(i for i in ORDER if not SETTINGS[i]["headline"]))
    print("matrix rows:"); [print("  ", rid(*m), "->", ("done" if done(*m) else "pending")) for m in matrix()]
    print(__doc__.split("Layout:")[1].strip())
    for sid in ORDER[:1]: g = build_graph(sid, "wide", MX["seeds"][0]); print("graph smoke-build ok:", {k: v["class_type"] for k, v in g.items() if k in ("123", "124", "126", "127", "143")})
    for sid in ORDER: build_graph(sid, "close", 1)
    print("all graphs build")


def status():
    for sid in ORDER:
        m = [x for x in matrix() if x[0] == sid]; d = sum(1 for x in m if done(*x)); print(f"{sid:8} {d}/{len(m)} done")


def pctile_med(v): return statistics.median(v) if v else None


def aggregate():
    faces = {}
    fp = E / "review/face/face_scores.jsonl"
    if fp.exists():
        for l in open(fp):
            d = json.loads(l); faces[d["name"]] = d
    recs = [json.loads(p.read_text()) for p in sorted(REC.glob("*.json"))]
    out = dict(rule="RULE.md", rule_last_line=open(E / "RULE.md").read().splitlines()[-1], generated=now(), constants=dict(tol=0.028, floor=0.37, seeds_needed=2, seeds=MX["seeds"]), settings={}, clips=[])
    for r in recs:
        name = rid(r["setting"], r["shot"], r["seed"]); f = faces.get(name); c = {k: r.get(k) for k in ("setting", "shot", "seed", "instance", "cold", "ok", "failed_twice", "gen_s", "sampler_s", "peak_mib", "wh", "power_peak_w", "clip", "clip_frames", "clip_size", "error", "utc")}
        c["name"] = name
        if f: c["aura_r1_mean"] = f["aura"]["r1"]["mean"]; c["aura_r1_min"] = f["aura"]["r1"]["min"]; c["aura_detected"] = f["aura"]["detected"]; c["sampled"] = f["sampled"]
        out["clips"].append(c)
    line = {}
    for shot in MX["shots"]:
        b = [c for c in out["clips"] if c["setting"] == "base20" and c["shot"] == shot and "aura_r1_mean" in c]
        if len(b) == len(MX["seeds"]):
            ms = [c["aura_r1_mean"] for c in b]; line[shot] = dict(base_mean=statistics.mean(ms), base_spread=max(ms) - min(ms), line=statistics.mean(ms) - 0.028)
    out["pass_lines"] = line
    for sid in ORDER:
        cs = [c for c in out["clips"] if c["setting"] == sid]; warm = [c for c in cs if c.get("ok") and not c.get("cold")]
        S = dict(label=SETTINGS[sid]["label"], headline=SETTINGS[sid]["headline"], steps=SETTINGS[sid]["steps"], instance=SETTINGS[sid]["instance"], clips_done=sum(1 for c in cs if c.get("ok")), clips_failed=sum(1 for c in cs if c.get("failed_twice")), clips_expected=len(MX["shots"]) * len(SETTINGS[sid].get("seeds", MX["seeds"])),
                 seconds_median_warm=pctile_med([c["gen_s"] for c in warm]), seconds_n_warm=len(warm), seconds_all=[c["gen_s"] for c in cs if c.get("ok")], seconds_cold=[c["gen_s"] for c in cs if c.get("ok") and c.get("cold")],
                 peak_mib_max=max([c["peak_mib"] for c in cs if c.get("peak_mib")] or [None]), wh_median_warm=pctile_med([c["wh"] for c in warm if c.get("wh")]), sampler_s_median_warm=pctile_med([c["sampler_s"] for c in warm if c.get("sampler_s")]), shots={})
        for shot in MX["shots"]:
            sc = [c for c in cs if c["shot"] == shot and c.get("ok")]; ws = [c for c in sc if not c.get("cold")]
            sh = dict(seconds_median_warm=pctile_med([c["gen_s"] for c in ws]), n_warm=len(ws), seeds={})
            for c in sc:
                if "aura_r1_mean" in c and shot in line:
                    p = c["aura_r1_mean"] >= line[shot]["line"] and c["aura_r1_min"] >= 0.37
                    sh["seeds"][str(c["seed"])] = dict(r1_mean=c["aura_r1_mean"], r1_min=c["aura_r1_min"], pass_=bool(p))
            if sh["seeds"]:
                np_ = sum(1 for v in sh["seeds"].values() if v["pass_"]); sh["seeds_passed"] = np_; sh["seeds_scored"] = len(sh["seeds"]); sh["kept"] = (np_ >= 2) if len(sh["seeds"]) == len(MX["seeds"]) else None
            S["shots"][shot] = sh
        for shot in MX["shots"]:                                           # Amendment 1 (b): wording decided here
            sh = S["shots"][shot]
            if shot in line and sh.get("seeds"):
                lo = min(c["aura_r1_mean"] for c in out["clips"] if c["setting"] == "base20" and c["shot"] == shot and "aura_r1_mean" in c)
                below = sum(1 for v in sh["seeds"].values() if v["r1_mean"] < lo); sh["seeds_below_base_lowest"] = below
                failed = sh.get("kept") is False
                sh["wording"] = ("may_say_lost_her" if (failed and below >= 2) else "below the line, inside the seed noise" if failed else "kept" if sh.get("kept") else "not decided")
        ks = [S["shots"][s].get("kept") for s in MX["shots"]]
        S["kept_her_face"] = (all(ks) if None not in ks else None)
        out["settings"][sid] = S
    for shot in MX["shots"]:                                               # Amendment 1 (a): base band
        b = [c["aura_r1_mean"] for c in out["clips"] if c["setting"] == "base20" and c["shot"] == shot and "aura_r1_mean" in c]
        if b: out.setdefault("base_band", {})[shot] = dict(min=min(b), max=max(b), range=max(b) - min(b), n=len(b))
    # Amendment 1 (e): lx8 vs lx8s12
    a8, b8 = out["settings"].get("lx8", {}).get("kept_her_face"), out["settings"].get("lx8s12", {}).get("kept_her_face")
    if a8 is not None and b8 is not None and a8 != b8: out["settings"]["lx8"]["wording_override"] = "depends on a setting its author has not published"
    # Amendment 1 (c): seconds per kept clip (all ok clips' seconds of the setting / its passing clips); winner named only with a margin of >= 2 passing clips
    rows = []
    for sid, S in out["settings"].items():
        if not S["headline"]: continue
        npass = sum(v["pass_"] for sh in S["shots"].values() for v in sh["seeds"].values()) if all(sh["seeds"] for sh in S["shots"].values()) else None
        tot = sum(c["gen_s"] for c in out["clips"] if c["setting"] == sid and c.get("ok"))
        S["passing_clips"] = npass; S["seconds_per_kept_clip"] = (tot / npass) if npass else None
        if npass: rows.append((tot / npass, sid, npass))
    rows.sort()
    if len(rows) >= 2:
        out["seconds_per_kept_clip_winner"] = dict(ranking=[dict(setting=r[1], s_per_kept=r[0], passing=r[2]) for r in rows], winner=rows[0][1], margin_passing_clips=rows[0][2] - rows[1][2],
                                                  named=(rows[0][2] - rows[1][2]) >= 2, text=(rows[0][1] if rows[0][2] - rows[1][2] >= 2 else "three seeds cannot separate them"))
    for sid, S in out["settings"].items():                                  # descriptive only
        w = [c for c in out["clips"] if c["setting"] == sid and c.get("ok") and not c.get("cold")]
        S["wall_s_median_warm_descriptive"] = pctile_med([c["gen_s"] for c in w]); S["sampler_share_descriptive"] = (S["sampler_s_median_warm"] / S["wall_s_median_warm_descriptive"]) if S["sampler_s_median_warm"] and S["wall_s_median_warm_descriptive"] else None
    (E / "review/speedlora_metrics.json").write_text(json.dumps(out, indent=1)); print("wrote review/speedlora_metrics.json", len(recs), "records,", len(faces), "scored")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--status", action="store_true"); ap.add_argument("--aggregate", action="store_true")
    ap.add_argument("--target", choices=["lab", "rig"]); ap.add_argument("--only"); ap.add_argument("--seed", type=int); ap.add_argument("--shot", choices=["wide", "close"])
    ap.add_argument("--min-s", type=int, default=1500); ap.add_argument("--max-clips", type=int, default=0)
    a = ap.parse_args()
    if a.dry_run: dry_run()
    elif a.status: status()
    elif a.aggregate: aggregate()
    elif a.target: sys.exit(run_target(a))
    else: ap.error("give --dry-run, --status, --aggregate or --target")
