from pathlib import Path
import base64
import hashlib
import os
import subprocess
import time

p = Path("_render/ppt-master-agenda-slide")
out = Path("ppt-master/agenda-slide")
out.mkdir(parents=True, exist_ok=True)


def load(prefix, n, raw_len, digest):
    texts = []
    for i in range(n):
        fp = p / f"{prefix}.{i}"
        if not fp.exists():
            raise SystemExit(f"missing {fp}")
        texts.append("".join(fp.read_text().split()))
    b64 = "".join(texts)
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
    34,
    496811,
    "1ccc6b4d37da96248cc72c7e9f10f160d69b12ca6fa3b0d5cf7d48d3c89b67e2",
)
mp4 = load(
    "mp4",
    69,
    1029775,
    "d1a8a463d8e098290f16d46878471ec1431ec69f5dfb8a5b0ee5528c524aeb9a",
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
run(
    [
        "git",
        "add",
        "ppt-master/agenda-slide/demo.gif",
        "ppt-master/agenda-slide/demo.mp4",
    ]
)
run(
    [
        "git",
        "commit",
        "-m",
        "Add ppt-master/agenda-slide demo",
    ]
)

wf = Path(".github/workflows/ingest-ppt-master-agenda-slide.yml")
if wf.exists():
    wf.unlink()
    run(["git", "add", "-u", str(wf)])
run(["git", "rm", "-r", "-f", "_render/ppt-master-agenda-slide"])
run(["git", "commit", "-m", "Remove ppt-master agenda-slide ingest scaffolding"])

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
