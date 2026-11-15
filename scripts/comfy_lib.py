"""Helpers for the benchmark runner: ComfyUI HTTP + websocket client, nvidia-smi sampler (whole card: memory, utilisation, power at 4 Hz) and
process-memory sampler, one profiled run per prompt (wall seconds from execution_start to the end of execution, per-node seconds, peak VRAM, energy).
Stdlib only. Instance port and container name are set by bench.py (environment variables), defaults are for a stock install."""
import base64, json, os, socket, struct, subprocess, sys, threading, time, urllib.error, urllib.request, uuid
from pathlib import Path

HOST, PORT = os.environ.get("COMFY_HOST", "localhost"), int(os.environ.get("COMFY_PORT", "8188"))
BASE = f"http://{HOST}:{PORT}"
CONTAINER = os.environ.get("COMFY_CONTAINER", "comfyui")


def api(path, data=None, timeout=60):
    req = urllib.request.Request(BASE + path, data=None if data is None else json.dumps(data).encode(),
                                 headers={"Content-Type": "application/json"} if data is not None else {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    return json.loads(raw) if raw else {}


class WS:
    def __init__(self, cid):
        self.s = socket.create_connection((HOST, PORT), timeout=30)
        key = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall((f"GET /ws?clientId={cid} HTTP/1.1\r\nHost: {HOST}:{PORT}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                        f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            buf += self.s.recv(4096)
        self.buf = buf.split(b"\r\n\r\n", 1)[1]
        self.s.settimeout(5)

    def _read(self, n):
        while len(self.buf) < n:
            c = self.s.recv(65536)
            if not c:
                raise EOFError
            self.buf += c
        o, self.buf = self.buf[:n], self.buf[n:]
        return o

    def recv(self):
        b1, b2 = self._read(2)
        op = b1 & 15
        ln = b2 & 127
        if ln == 126:
            ln = struct.unpack(">H", self._read(2))[0]
        elif ln == 127:
            ln = struct.unpack(">Q", self._read(8))[0]
        data = self._read(ln)
        if op == 9:
            m = os.urandom(4)
            self.s.sendall(bytes([0x8A, 0x80 | len(data)]) + m + bytes(b ^ m[i % 4] for i, b in enumerate(data)))
        return op, data


class Trace:
    """nvidia-smi 4 Hz (whole card: memory MiB, util, power W) + 1 Hz RAM of the lab ComfyUI process."""

    def __init__(self, pid=None, cgroup=None):
        self.rows, self.ram = [], []          # (t, mem, util, power) ; (t, anon_mib, file_mib, cg_mib)
        self.pid, self.cg = pid, cgroup
        self.p = subprocess.Popen(["nvidia-smi", "--query-gpu=memory.used,utilization.gpu,power.draw", "--format=csv,noheader,nounits", "-lms", "250"],
                                  stdout=subprocess.PIPE, text=True)
        self.alive = True
        self.low = 0
        self.tripped = None          # time the RAM watchdog interrupted the lab (host MemAvailable < 1.2 GiB for 4 samples)
        threading.Thread(target=self._r, daemon=True).start()
        threading.Thread(target=self._ram, daemon=True).start()

    def _r(self):
        for l in self.p.stdout:
            try:
                m, u, w = [float(x) for x in l.split(",")]
                self.rows.append((time.time(), m, u, w))
            except ValueError:
                pass

    def _ram(self):
        while self.alive:
            try:
                an = fi = 0
                for line in open(f"/proc/{self.pid}/status"):
                    if line.startswith("RssAnon:"):
                        an = int(line.split()[1]) / 1024
                    elif line.startswith("RssFile:"):
                        fi = int(line.split()[1]) / 1024
                cg = int(open(self.cg + "/memory.current").read()) / 2 ** 20 if self.cg else 0
                ma = 0
                for line in open("/proc/meminfo"):
                    if line.startswith("MemAvailable:"):
                        ma = int(line.split()[1]) / 1024
                        break
                self.ram.append((time.time(), an, fi, cg, ma))
                self.low = self.low + 1 if ma < 3000 else 0
                if self.low >= 4 and not self.tripped:
                    self.tripped = time.time()
                    try:
                        api("/interrupt", {}, timeout=5)
                        subprocess.run(["docker", "kill", CONTAINER], timeout=20)
                    except Exception:
                        pass
            except Exception:
                pass
            time.sleep(1.0)

    def stop(self):
        self.alive = False
        self.p.terminate()
        try:
            self.p.wait(5)
        except subprocess.TimeoutExpired:
            self.p.kill()

    def window(self, t0, t1):
        r = [x for x in self.rows if t0 <= x[0] <= t1]
        m = [x for x in self.ram if t0 <= x[0] <= t1]
        out = dict(peak_mib=None, util=None, wh=None, ram_anon_peak_mib=None, ram_file_peak_mib=None, ram_cgroup_peak_mib=None)
        if r:
            out.update(peak_mib=int(max(x[1] for x in r)), util=round(sum(x[2] for x in r) / len(r)),
                       wh=round(sum(x[3] for x in r) * 0.25 / 3600, 2), power_peak_w=int(max(x[3] for x in r)))
        if m:
            out.update(ram_anon_peak_mib=int(max(x[1] for x in m)), ram_file_peak_mib=int(max(x[2] for x in m)),
                       ram_cgroup_peak_mib=int(max(x[3] for x in m)), ram_anon_end_mib=int(m[-1][1]),
                       host_memavail_min_mib=int(min(x[4] for x in m)))
        return out

    def ram_series(self, t0, t1, step=2.0):
        out, last = [], -1e9
        for x in self.ram:
            if t0 <= x[0] <= t1 and x[0] - last >= step:
                out.append((round(x[0] - t0, 1), int(x[1]), int(x[2]), int(x[4])))   # t, anon MiB, file MiB, host MemAvailable MiB
                last = x[0]
        return out

    def series(self, t0, t1, step=2.0):
        """whole-card VRAM MiB every `step` s inside the window (for the log)."""
        r = [x for x in self.rows if t0 <= x[0] <= t1]
        out, last = [], -1e9
        for x in r:
            if x[0] - last >= step:
                out.append((round(x[0] - t0, 1), int(x[1]), round(x[3])))
                last = x[0]
        return out


def container_pid_cgroup():
    pid = int(subprocess.check_output(["docker", "inspect", "-f", "{{.State.Pid}}", CONTAINER], text=True).strip())
    cid = subprocess.check_output(["docker", "inspect", "-f", "{{.Id}}", CONTAINER], text=True).strip()
    for cand in (f"/sys/fs/cgroup/system.slice/docker-{cid}.scope", f"/sys/fs/cgroup/docker/{cid}"):
        if os.path.isdir(cand):
            return pid, cand
    return pid, None


def run_profiled(graph, trace, timeout=3000):
    cid = uuid.uuid4().hex
    ws = WS(cid)
    t_q = time.time()
    try:
        pid = api("/prompt", {"prompt": graph, "client_id": cid})["prompt_id"]
    except urllib.error.HTTPError as e:
        return dict(ok=False, error="validation: " + e.read().decode()[:3000], t_start=t_q, t_end=time.time())
    except Exception as e:
        return dict(ok=False, error="submit failed (lab down?): " + str(e)[:300], t_start=t_q, t_end=time.time())
    cur = None; node_t = {}; last = t_q
    steps = []; cached = []; order = []
    ok = None; err = None; t_start = None
    while True:
        if time.time() - t_q > timeout:
            err = "timeout"; break
        try:
            op, data = ws.recv()
        except socket.timeout:
            continue
        except EOFError:
            err = "websocket closed"; break
        if op != 1:
            continue
        m = json.loads(data); t = time.time(); ty = m.get("type"); d = m.get("data", {})
        if d.get("prompt_id") not in (None, pid):
            continue
        if ty == "execution_start":
            t_start = t
        elif ty == "execution_cached":
            cached = d.get("nodes", [])
        elif ty == "executing":
            if cur is not None:
                node_t[cur] = node_t.get(cur, 0) + (t - last)
            cur = d.get("node"); last = t; order.append((cur, round(t - (t_start or t_q), 2)))
            if cur is None:
                ok = True; break
        elif ty == "progress":
            steps.append((t, d["value"], d["max"], d.get("node")))
        elif ty == "execution_error":
            ok = False; err = json.dumps(d)[:3000]; break
        elif ty == "execution_interrupted":
            ok = False; err = "interrupted"; break
    t_end = time.time()
    ws.s.close()
    h = {}
    try:
        h = api(f"/history/{pid}").get(pid, {})
    except Exception:
        pass
    outs = []
    for nid, n in h.get("outputs", {}).items():
        for key in ("images", "gifs", "videos"):
            for i in n.get(key, []):
                if i.get("type") == "output":
                    outs.append(i)
    st = list(steps)
    sampler_start = next((tt for (nid, tt) in order if nid == "23"), None)
    p_rel = [round(s[0] - (t_start or t_q), 2) for s in st]
    return dict(ok=bool(ok), error=err, node_s={k: round(v, 2) for k, v in node_t.items()}, cached=cached, t_start=t_start, t_end=t_end,
                node_order=order, outputs=outs, prompt_id=pid, sampler_start_rel=sampler_start, progress_rel=p_rel,
                wall_s=round(t_end - (t_start or t_q), 2))


def docker_log(since_epoch):
    iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(since_epoch - 2))
    p = subprocess.run(["docker", "logs", CONTAINER, "--since", iso], capture_output=True, text=True)
    return (p.stdout + p.stderr)


