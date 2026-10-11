from pathlib import Path
import base64
import hashlib
import os
import subprocess
import time

p = Path("_render/mattpocock-skills-catalog-check")
out = Path("mattpocock-skills/catalog-check")
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
    3,
    894190,
    "c1d583cb2006d4586ae6ec08cf26c7c26b1ae68d4011974dadf5a5eb7c940f7c",
)
mp4 = load(
    "mp4",
    8,
    2244934,
    "83ad2f27b4a4915aff1e24af39a12edb7530cbcbaeb3f9dae5283dd8a04a82a6",
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
        "mattpocock-skills/catalog-check/demo.gif",
        "mattpocock-skills/catalog-check/demo.mp4",
    ]
)
run(
    [
        "git",
        "commit",
        "-m",
        "Add mattpocock-skills catalog-check walkthrough GIF and MP4",
    ]
)

wf = Path(".github/workflows/ingest-mattpocock-skills-catalog-check.yml")
if wf.exists():
    wf.unlink()
    run(["git", "add", "-u", str(wf)])
run(["git", "rm", "-r", "-f", "_render/mattpocock-skills-catalog-check"])
run(["git", "commit", "-m", "Remove mattpocock-skills catalog-check ingest scaffolding"])

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
