#!/usr/bin/env python3
"""results.json -> results.md (every number on the page is read from the JSON, nothing is typed by hand). Usage: python3 scripts/make_results_md.py [results.json] [results.md]"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "results.json"
dst = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "results.md"
d = json.loads(src.read_text())
ORDER = ["base20", "lx8", "pika6", "lx4", "hyper6"]
DAG = {"hyper6": " †", "base20_rig": " †"}
FOOT = "† 2nd ComfyUI instance, same card"
LABEL = {"hyper6": "HyperFlow H3 Flash (fast model, own loader, 6 steps)"}   # display only: results.json keeps its frozen label
S = d["settings"]; PL = d["pass_lines"]; BB = d["base_band"]


def f2(v): return f"{v + 1e-9:.2f}"          # round half up (the JSON holds values like 146.705)
def sec(k, v): return f2(v) + DAG.get(k, "")


out = ["# Results (generated from results.json by scripts/make_results_md.py)", "",
       f"Rule file: RULE.md and its two amendments (last freeze line: {d['rule_last_line'][:40]}...). Metrics generated {d['generated']}.",
       f"Constants: tolerance {d['constants']['tol']}, floor R1 min >= {d['constants']['floor']}, {d['constants']['seeds_needed']} of 3 seeds per shot, seeds {', '.join(map(str, d['constants']['seeds']))}.", "",
       "## Pass lines and the base's own seed spread", "",
       "| Shot | base20 mean of seed means | base20 seed range | Line (mean - 0.028) |", "|---|---|---|---|"]
for sh in ("wide", "close"):
    out.append(f"| {sh} | {PL[sh]['base_mean']:.4f} | {BB[sh]['min']:.4f} to {BB[sh]['max']:.4f} (spread {BB[sh]['range']:.4f}) | {PL[sh]['line']:.4f} |")
out += ["", "## Seconds per clip (median of warm clips, both shots pooled)", "",
        "| Setting | Steps | Seconds | Sampler seconds | Wh (whole card) | Peak VRAM, whole card (MiB) | Warm clips |", "|---|---|---|---|---|---|---|"]
for k in ORDER + ["lx8s12", "base20_rig"]:
    s = S[k]
    out.append(f"| {k}{' (report only)' if not s['headline'] else ''}: {LABEL.get(k, s['label'])} | {s['steps']} | {sec(k, s['seconds_median_warm'])} | {sec(k, s['sampler_s_median_warm'])} | {f2(s['wh_median_warm'])}{DAG.get(k, '')} | {s['peak_mib_max']} | {s['seconds_n_warm']} |")
out += ["", FOOT + ". Peak VRAM is the whole card with two ComfyUI instances sharing it, so it does not show what a setting needs.", "",
        "## Face check, every seed (R1 mean / R1 min; pass = mean >= line and min >= 0.37)", "",
        "| Setting | Shot | Seed 1766580932 | Seed 4103 | Seed 5207 | Seeds passed | Verdict |", "|---|---|---|---|---|---|---|"]
for k in ORDER + ["lx8s12", "base20_rig"]:
    for sh in ("wide", "close"):
        x = S[k]["shots"][sh]
        cells = []
        for sd in ("1766580932", "4103", "5207"):
            v = x["seeds"].get(sd)
            cells.append("-" if not v else f"{v['r1_mean']:.4f} / {v['r1_min']:.4f} {'pass' if v['pass_'] else 'FAIL'}")
        verdict = "not decided (anchor clip only)" if x.get("kept") is None else ("passes the rule" if x["kept"] else "fails the rule")
        out.append(f"| {k}{DAG.get(k, '')} | {sh} | {' | '.join(cells)} | {x['seeds_passed']} of {x['seeds_scored']} | {verdict}; seeds under the base's lowest seed: {x['seeds_below_base_lowest']} |")
out += ["", "## Every clip", "", "| Clip | Instance | Cold | Seconds | Sampler s | Peak MiB | Wh | Peak W | R1 mean | R1 min |", "|---|---|---|---|---|---|---|---|---|---|"]
for c in d["clips"]:
    k = c["setting"]
    out.append(f"| {c['name']} | {c['instance']} | {'cold' if c['cold'] else ''} | {sec(k, c['gen_s'])} | {sec(k, c['sampler_s'])} | {c['peak_mib']} | {c['wh']}{DAG.get(k, '')} | {c['power_peak_w']} | {c['aura_r1_mean']:.4f} | {c['aura_r1_min']:.4f} |")
out += ["", FOOT + ". 'Cold' = the first clip a process ran for a setting (model load and LoRA patch); it is left out of the median.", ""]
dst.write_text("\n".join(out))
print("wrote", dst)
