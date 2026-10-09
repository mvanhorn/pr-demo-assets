from pathlib import Path
import base64
import hashlib
import os
import subprocess
import time

p = Path("_render/opentpu-lens-summary")
out = Path("openTPU/lens-summary")
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
    6,
    2787485,
    "fc0c6b7f6ee8da0699fa2f0b4225d61005d1bc9cb14a20c6a76c5bad67cb4b7a",
)
mp4 = load(
    "mp4",
    10,
    4814226,
    "e4a42a4ddb9d93d6e48570dcb7480c225ed4002d75f6e35475a3430bdb72b4d2",
)
(out / "demo.gif").write_bytes(gif)
(out / "demo.mp4").write_bytes(mp4)
(out / "README.md").write_text(
    "38s 1920x1080 MP4 and 720px GIF of otpu-lens summary: ISA record, "
    "dashboard (roofline, unit utilisation, MM class), info one-liner.\n"
)

env = dict(os.environ)
env["GIT_AUTHOR_NAME"] = "Matt Van Horn"
env["GIT_AUTHOR_EMAIL"] = "mvanhorn@users.noreply.github.com"
env["GIT_COMMITTER_NAME"] = "Matt Van Horn"
env["GIT_COMMITTER_EMAIL"] = "mvanhorn@users.noreply.github.com"


def run(args):
    subprocess.check_call(args, env=env)


run(["git", "config", "user.name", "Matt Van Horn"])
run(["git", "config", "user.email", "mvanhorn@users.noreply.github.com"])
run(
    [
        "git",
        "add",
        "openTPU/lens-summary/demo.gif",
        "openTPU/lens-summary/demo.mp4",
        "openTPU/lens-summary/README.md",
    ]
)
run(["git", "commit", "-m", "Add openTPU lens summary demo assets"])

wf = Path(".github/workflows/ingest-opentpu-lens-summary.yml")
if wf.exists():
    wf.unlink()
    run(["git", "add", "-u", str(wf)])
run(["git", "rm", "-r", "-f", "_render/opentpu-lens-summary"])
run(["git", "commit", "-m", "Remove opentpu-lens-summary ingest scaffolding"])

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
