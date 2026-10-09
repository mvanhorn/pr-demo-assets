from pathlib import Path
import base64
import hashlib
import os
import subprocess
import time

p = Path("_render/ladybug-list-has-any")
out = Path("ladybug/list-has-any")
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
    20,
    1287206,
    "a62a24bf41d00f44e3ba0a1d5c6d54fda3fa3ec41b6ae8a6b063fd19df08c5e6",
)
mp4 = load(
    "mp4",
    40,
    2692993,
    "539ff59f011c258b093c7617d22d91a85c192f503d501490dfcebb16cb371d4d",
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
run(["git", "add", "ladybug/list-has-any/demo.gif", "ladybug/list-has-any/demo.mp4"])
run(
    [
        "git",
        "commit",
        "-m",
        "Add Ladybug list_has_any walkthrough GIF and MP4",
    ]
)

wf = Path(".github/workflows/ingest-ladybug-list-has-any.yml")
if wf.exists():
    wf.unlink()
    run(["git", "add", "-u", str(wf)])
run(["git", "rm", "-r", "-f", "_render/ladybug-list-has-any"])
run(["git", "commit", "-m", "Remove ladybug list-has-any ingest scaffolding"])

last_err = None
for attempt in range(8):
    try:
        run(["git", "pull", "--rebase", "origin", "main"])
        run(["git", "push", "origin", "HEAD:main"])
        last_err = None
        break
    except subprocess.CalledProcessError as exc:
        last_err = exc
        time.sleep(2**attempt)
if last_err is not None:
    raise last_err
