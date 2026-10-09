from pathlib import Path
import base64
import hashlib
import os
import subprocess
import time

p = Path("_render/ladybug-list-min-max")
out = Path("ladybug/list-min-max")
out.mkdir(parents=True, exist_ok=True)


def chunk_body(prefix, i):
    parts = []
    j = 0
    while True:
        fp = p / f"{prefix}.{i}.{j}"
        if not fp.exists():
            break
        parts.append(fp.read_text())
        j += 1
    if parts:
        return "".join(parts)
    fp = p / f"{prefix}.{i}"
    if not fp.exists():
        return None
    return fp.read_text()


def load(prefix, n, raw_len, digest):
    texts = []
    missing = []
    for i in range(n):
        body = chunk_body(prefix, i)
        if body is None:
            missing.append(f"{prefix}.{i}")
            continue
        texts.append("".join(body.split()))
    if missing:
        raise SystemExit("missing chunks: " + ", ".join(missing[:12]))
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
    18,
    1195970,
    "55a059ce6e1a39dce90f940e9fd857628ec6538e0c893dcdcf0c0893a1752895",
)
mp4 = load(
    "mp4",
    38,
    2502910,
    "1313ea282a6d3aa7473141722b99a8bd1efac650da4ef457c074f7e01976b4ad",
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
run(["git", "add", "ladybug/list-min-max/demo.gif", "ladybug/list-min-max/demo.mp4"])
run(
    [
        "git",
        "commit",
        "-m",
        "Add Ladybug list_min and list_max walkthrough GIF and MP4",
    ]
)

wf = Path(".github/workflows/ingest-ladybug-list-min-max.yml")
if wf.exists():
    wf.unlink()
    run(["git", "add", "-u", str(wf)])
run(["git", "rm", "-r", "-f", "_render/ladybug-list-min-max"])
run(["git", "commit", "-m", "Remove ladybug list-min-max ingest scaffolding"])

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
