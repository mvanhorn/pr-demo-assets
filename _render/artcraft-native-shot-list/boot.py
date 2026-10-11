from pathlib import Path
import base64
import hashlib
import os
import subprocess
import time

p = Path("_render/artcraft-native-shot-list")
out = Path("artcraft/native-shot-list")
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
    8,
    8311818,
    "a56f7855bab239a026d2202e9d896b2ee619248747d8cdaa9fef31c9fd13d005",
)
mp4 = load(
    "mp4",
    16,
    17162754,
    "42d36beafafae1e72e45aa6299b2ed1729962a96411c4c52d9e1707e090e58b6",
)
before = load(
    "before",
    1,
    174753,
    "21c4a8c263f3eb4d3ffd2889252f580e7c0afcbc4d123f278a76b22ffb774a1c",
)
after_empty = load(
    "after_empty",
    1,
    113053,
    "d0d44b7c8d88c55ac31759e83afe24bbd2ec8332971d8c7cf4d76a48ee2a22a8",
)
after = load(
    "after",
    1,
    160100,
    "c7774f705a78a2415216d27c6727e67fe8d00e9565c9c5c39c874d95d7daec53",
)

(out / "demo.gif").write_bytes(gif)
(out / "demo.mp4").write_bytes(mp4)
(out / "before.png").write_bytes(before)
(out / "after-empty.png").write_bytes(after_empty)
(out / "after.png").write_bytes(after)

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
        "artcraft/native-shot-list/demo.gif",
        "artcraft/native-shot-list/demo.mp4",
        "artcraft/native-shot-list/before.png",
        "artcraft/native-shot-list/after-empty.png",
        "artcraft/native-shot-list/after.png",
    ]
)
run(
    [
        "git",
        "commit",
        "-m",
        "Add Artcraft native Shot List walkthrough GIF, MP4, and screenshots",
    ]
)

wf = Path(".github/workflows/ingest-artcraft-native-shot-list.yml")
if wf.exists():
    wf.unlink()
    run(["git", "add", "-u", str(wf)])
run(["git", "rm", "-r", "-f", "_render/artcraft-native-shot-list"])
run(["git", "commit", "-m", "Remove Artcraft native Shot List ingest scaffolding"])

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
