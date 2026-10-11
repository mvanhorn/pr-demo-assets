from pathlib import Path
import base64
import hashlib
import os
import subprocess
import time

p = Path("_render/yue-request-validate")
out = Path("YuE/request-validate")
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
    11,
    965908,
    "66e0c93d2002f5c712b587ff1ea0c06a2bc17995773a1c63f15af9e14151095e",
)
mp4 = load(
    "mp4",
    22,
    1934612,
    "78b354f199f98e9db6f03f04db53eaca802abcbe9570804fc0d5d9df5efe3b92",
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
        "YuE/request-validate/demo.gif",
        "YuE/request-validate/demo.mp4",
    ]
)
run(
    [
        "git",
        "commit",
        "-m",
        "Add YuE yue2 validate walkthrough GIF and MP4",
    ]
)

wf = Path(".github/workflows/ingest-yue-request-validate.yml")
if wf.exists():
    wf.unlink()
    run(["git", "add", "-u", str(wf)])
run(["git", "rm", "-r", "-f", "_render/yue-request-validate"])
run(["git", "commit", "-m", "Remove YuE request-validate ingest scaffolding"])

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
