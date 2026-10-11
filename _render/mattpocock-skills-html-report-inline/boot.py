from pathlib import Path
import base64
import hashlib
import os
import subprocess
import time

p = Path("_render/mattpocock-skills-html-report-inline")
out = Path("mattpocock-skills/html-report-inline")
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
    39,
    2319668,
    "e5125875c6e86801f5ead6c5cb00544035522c635291b9455f8cd779057bb7e7",
)
mp4 = load(
    "mp4",
    30,
    1790006,
    "e0a6bbe326f7ea98eecb5f3936f59a65a7f455acbf2042c28abf65525f83e004",
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
        "mattpocock-skills/html-report-inline/demo.gif",
        "mattpocock-skills/html-report-inline/demo.mp4",
    ]
)
run(
    [
        "git",
        "commit",
        "-m",
        "Add mattpocock-skills html-report-inline walkthrough GIF and MP4",
    ]
)

wf = Path(".github/workflows/ingest-mattpocock-skills-html-report-inline.yml")
if wf.exists():
    wf.unlink()
    run(["git", "add", "-u", str(wf)])
run(["git", "rm", "-r", "-f", "_render/mattpocock-skills-html-report-inline"])
run(["git", "commit", "-m", "Remove mattpocock-skills html-report-inline ingest scaffolding"])

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
