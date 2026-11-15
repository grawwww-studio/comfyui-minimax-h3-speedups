# Face metric used in EP07 and EP09. CPU only.
# Detector: YuNet (OpenCV Zoo, MIT) for every column. Shown metric: AuraFace glintr100.onnx (fal/AuraFace-v1, Apache-2.0, ONLY the recognition file).
# Cross-check: SFace (OpenCV Zoo, Apache-2.0). The optional --buffalo column needs a research-only model and is NOT used for any result in this repo: leave it off.
# Same logic as the EP07 scorer: frames normalised to 1920x1080 (centre crop to 16:9 then Lanczos/area), first 120 frames, every 4th frame,
# largest face with score > 0.5; R1 = cosine to the mean of the normed embeddings of the 2 sheet refs (face close-up + front full); R0 = cosine of the arm's
# face vs the DRAFT's face at the same frame (mean/min). Per-frame series saved so any later rule can be re-derived.
# usage (python3 -I, with onnxruntime, opencv-python, numpy installed):
#   score_face.py --refs FACE.png FRONT.png --out DIR NAME|CLIP|DRAFT ...     resumable per NAME -> DIR/face_scores.jsonl (+ DIR/series/NAME.npz)
# Embeddings of a clip are cached in DIR/series/emb_<sha1 of path>.npz so a draft shared by several arms is scanned once.
import os, sys, json, time, hashlib, argparse, resource
import numpy as np, cv2

M = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weights")
AURA = f"{M}/auraface/glintr100.onnx"; SFACE = f"{M}/opencv_zoo/sface.onnx"; YUNET = f"{M}/opencv_zoo/yunet.onnx"
EXPECT = {AURA: "a7933ea5330113b01c9b60351d8f4c33003f145d8470ac5f0e52ee2effe25c60", SFACE: "0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79",
          YUNET: "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4"}
ARC = np.array([[38.2946, 51.6963], [73.5318, 51.5014], [56.0252, 71.7366], [41.5493, 92.3655], [70.7299, 92.2041]], np.float32)   # ArcFace 112 template
NFR, STEP, THR = 120, 4, 0.5


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""): h.update(b)
    return h.hexdigest()


def n1080(f):
    h, w = f.shape[:2]
    if abs(w / h - 16 / 9) > 0.02:
        ch = round(w * 9 / 16); y0 = (h - ch) // 2; f = f[y0:y0 + ch]
    if f.shape[1] == 1920 and f.shape[0] == 1080: return f
    return cv2.resize(f, (1920, 1080), interpolation=cv2.INTER_LANCZOS4 if f.shape[1] < 1920 else cv2.INTER_AREA)


class Metric:
    def __init__(self, buffalo=False):
        for p, h in EXPECT.items():
            if sha(p) != h: sys.exit(f"hash mismatch {p}")
        self.det = cv2.FaceDetectorYN.create(YUNET, "", (1920, 1080), THR, 0.3, 5000)
        self.sf = cv2.FaceRecognizerSF.create(SFACE, "")
        import onnxruntime as ort
        so = ort.SessionOptions(); so.intra_op_num_threads = 4
        self.au = ort.InferenceSession(AURA, so, providers=["CPUExecutionProvider"]); self.au_in = self.au.get_inputs()[0].name
        self.bf = None
        if buffalo:
            from insightface.app import FaceAnalysis
            root = os.environ.get("INSIGHTFACE_ROOT", "insightface")
            self.bf = FaceAnalysis(name="buffalo_l", root=root, providers=["CPUExecutionProvider"]); self.bf.prepare(ctx_id=-1, det_size=(640, 640))

    def face(self, img):
        h, w = img.shape[:2]; self.det.setInputSize((w, h)); _, fs = self.det.detect(img)
        if fs is None: return None
        fs = [r for r in fs if r[14] > THR]
        return max(fs, key=lambda r: r[2] * r[3]) if fs else None

    def emb(self, img):
        """-> dict(aura, sface, buffalo?, box) or None. aura/sface L2-normalised."""
        r = self.face(img)
        if r is None: return None
        lm = r[4:14].reshape(5, 2).astype(np.float32)
        A, _ = cv2.estimateAffinePartial2D(lm, ARC, method=cv2.LMEDS)
        crop = cv2.warpAffine(img, A, (112, 112), borderValue=0)
        blob = cv2.dnn.blobFromImage(crop, 1 / 127.5, (112, 112), (127.5, 127.5, 127.5), swapRB=True)
        a = self.au.run(None, {self.au_in: blob})[0][0]; a = a / np.linalg.norm(a)
        s = self.sf.feature(self.sf.alignCrop(img, r)).reshape(-1); s = s / np.linalg.norm(s)
        out = dict(aura=a, sface=s, box=r[:4].astype(float))
        if self.bf is not None:
            fs = [f for f in self.bf.get(img) if f.det_score > THR]
            out["buffalo"] = max(fs, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1])).normed_embedding if fs else None
        return out


def scan(M_, path, series_dir, buffalo):
    key = hashlib.sha1(os.path.abspath(path).encode()).hexdigest()[:12] + ("_b" if buffalo else "")
    cp = f"{series_dir}/emb_{key}.npz"
    if os.path.exists(cp):
        z = np.load(cp, allow_pickle=True); return {int(i): dict(aura=a, sface=s, buffalo=(b if b is not None and b.ndim else None)) for i, a, s, b in zip(z["idx"], z["aura"], z["sface"], z["buffalo"])}, int(z["n_sampled"]), 0.0
    t0 = time.time(); cap = cv2.VideoCapture(path); res = {}; n = 0; i = 0; nsamp = 0
    while i < NFR:
        if i % STEP:
            if not cap.grab(): break
            i += 1; continue
        ok, f = cap.read()
        if not ok: break
        nsamp += 1; e = M_.emb(n1080(f))
        if e is not None: res[i] = e
        i += 1
    dt = time.time() - t0
    idx = sorted(res); zb = [res[i].get("buffalo") if res[i].get("buffalo") is not None else np.array(0) for i in idx]
    np.savez(cp, idx=idx, aura=np.array([res[i]["aura"] for i in idx]), sface=np.array([res[i]["sface"] for i in idx]), buffalo=np.array(zb, dtype=object), n_sampled=nsamp)
    return res, nsamp, dt


def stats(v):
    return dict(mean=float(np.mean(v)), min=float(np.min(v)), p10=float(np.percentile(v, 10)), n=len(v)) if len(v) else dict(mean=None, min=None, p10=None, n=0)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--refs", nargs=2, required=True); ap.add_argument("--out", required=True); ap.add_argument("--buffalo", action="store_true")
    ap.add_argument("specs", nargs="+"); a = ap.parse_args()
    sd = f"{a.out}/series"; os.makedirs(sd, exist_ok=True); outp = f"{a.out}/face_scores.jsonl"; bufp = f"{a.out}/internal_buffalo.jsonl"
    done = {json.loads(l)["name"] for l in open(outp)} if os.path.exists(outp) else set()
    todo = [s for s in a.specs if s.split("|")[0] not in done]
    if not todo: print("nothing to do"); return
    M_ = Metric(a.buffalo)
    refs = []
    for p in a.refs:
        e = M_.emb(cv2.imread(p)); assert e is not None, f"no face in ref {p}"; refs.append(e)
    R = {k: np.mean([r[k] for r in refs], 0) for k in ("aura", "sface")}; R = {k: v / np.linalg.norm(v) for k, v in R.items()}
    RB = None
    if a.buffalo:
        RB = np.mean([r["buffalo"] for r in refs], 0); RB /= np.linalg.norm(RB)
    ref_self = {k: float(refs[0][k] @ refs[1][k]) for k in ("aura", "sface")}
    for spec in todo:
        name, clip, draft, take = spec.split("|"); t0 = time.time()
        ea, ns, dta = scan(M_, clip, sd, a.buffalo); ed, nd, dtd = scan(M_, draft, sd, a.buffalo)
        row = dict(name=name, clip=clip, draft=draft, take=take, sampled=ns, ref_self=ref_self, wall_s=round(time.time() - t0, 1), scan_s_clip=round(dta, 1), scan_s_draft=round(dtd, 1),
                   peak_rss_mib=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024), metrics_versions=EXPECT)
        ser = {}
        for k in ("aura", "sface"):
            r1 = {i: float(e[k] @ R[k]) for i, e in ea.items()}
            r0 = {i: float(e[k] @ ed[i][k]) for i, e in ea.items() if i in ed}
            row[k] = dict(r1=stats(list(r1.values())), r0=stats(list(r0.values())), detected=len(r1)); ser[f"{k}_r1"] = r1; ser[f"{k}_r0"] = r0
        np.savez(f"{sd}/{name}.npz", **{k: np.array(sorted(v.items())) for k, v in ser.items()})
        open(outp, "a").write(json.dumps(row) + "\n")
        if a.buffalo:
            r1 = {i: float(e["buffalo"] @ RB) for i, e in ea.items() if e.get("buffalo") is not None}
            r0 = {i: float(e["buffalo"] @ ed[i]["buffalo"]) for i, e in ea.items() if e.get("buffalo") is not None and i in ed and ed[i].get("buffalo") is not None}
            open(bufp, "a").write(json.dumps(dict(name=name, INTERNAL_ONLY="buffalo_l research-only: never shown, never in the repo", r1=stats(list(r1.values())), r0=stats(list(r0.values())))) + "\n")
            np.savez(f"{sd}/{name}_buffalo_INTERNAL.npz", r1=np.array(sorted(r1.items())), r0=np.array(sorted(r0.items())))
        print(json.dumps({k: row[k] for k in ("name", "wall_s", "peak_rss_mib")} | {"aura_r1": row["aura"]["r1"]["mean"], "sface_r1": row["sface"]["r1"]["mean"]}), flush=True)


if __name__ == "__main__":
    main()
