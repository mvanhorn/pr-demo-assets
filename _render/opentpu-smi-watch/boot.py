from pathlib import Path
import base64
import hashlib
import os
import subprocess
import time

p = Path("_render/opentpu-smi-watch")
out = Path("openTPU/smi-watch")
out.mkdir(parents=True, exist_ok=True)


def load(prefix, n, raw_len, digest):
    missing = [f"{prefix}.{i}" for i in range(n) if not (p / f"{prefix}.{i}").exists()]
    if missing:
        raise SystemExit("missing chunks: " + ", ".join(missing[:12]))
    b64 = "".join("".join((p / f"{prefix}.{i}").read_text().split()) for i in range(n))
    pad = (4 - len(b64) % 4) % 4
    data = base64.b64decode(b64 + "=" * pad)
    if len(data) != raw_len:
        raise SystemExit(f"{prefix} length {len(data)} != {raw_len}")
    got = hashlib.sha256(data).hexdigest()
    if got != digest:
        raise SystemExit(f"{prefix} sha256 {got} != {digest}")
    return data


gif = load(
    "gif",
    18,
    1614523,
    "dfee56ff5cf2100eb28739b84d5955b986b1fe46616ebd5cc8c5369761cbf3e2",
)
mp4 = load(
    "mp4",
    36,
    3226788,
    "0117ed9cf466e4feb1d3a6f926ff4e9ea3adc988218f75a9e80cabc1340a2fd6",
)
(out / "demo.gif").write_bytes(gif)
(out / "demo.mp4").write_bytes(mp4)

env = dict(os.environ)
env["GIT_AUTHOR_NAME"] = "Matt Van Horn"
env["GIT_AUTHOR_EMAIL"] = "mvanhorn@users.noreply.github.com"
env["GIT_COMMITTER_NAME"] = "Matt Van Horn"
env["GIT_COMMITTER_EMAIL"] = "mvanhorn@users.noreply.github.com"


def run(args):
    subprocess.check_call(args, env=env)


run(["git", "config", "user.name", "Matt Van Horn"])
run(["git", "config", "user.email", "mvanhorn@users.noreply.github.com"])
run(["git", "add", "openTPU/smi-watch/demo.gif", "openTPU/smi-watch/demo.mp4"])
run(
    [
        "git",
        "commit",
        "-m",
        "Add openTPU otpu-smi Caps/Watch/CSV demo assets",
    ]
)

wf = Path(".github/workflows/ingest-opentpu-smi-watch.yml")
if wf.exists():
    wf.unlink()
    run(["git", "add", "-u", str(wf)])
run(["git", "rm", "-r", "-f", "_render/opentpu-smi-watch"])
run(["git", "commit", "-m", "Remove opentpu-smi-watch ingest scaffolding"])

last_err = None
for attempt in range(8):
    try:
        run(["git", "pull", "--rebase", "origin", "main"])
        run(["git", "push", "origin", "HEAD:main"])
        last_err = None
        break
    except subprocess.CalledProcessError as exc:
        last_err = exc
        time.sleep(2 ** attempt)
if last_err is not None:
    raise last_err
