from pathlib import Path
import base64
import hashlib
import os
import subprocess
import time

p = Path("_render/at_mcp-search-posts-filters")
out = Path("at_mcp/search-posts-filters")
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
    31,
    1650727,
    "d39495eceb96d3bc5725c0164923a1410d6d1ee331e8c76626cd3686e0b047d8",
)
mp4 = load(
    "mp4",
    49,
    2636647,
    "4b203edaf02bf80b373dc70a6a4a2f16f464dff3206b995c73b8de62cd8dbe72",
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
run(["git", "rm", "-f", "--ignore-unmatch", "at_mcp/search-posts-filters/.ingest-probe"])
run(["git", "add", "at_mcp/search-posts-filters/demo.gif", "at_mcp/search-posts-filters/demo.mp4"])
run(
    [
        "git",
        "commit",
        "-m",
        "Add at_mcp search_posts filters walkthrough demo\n\nGIF and MP4 for optional author, mentions, sort, since, until and lang\non search_posts.",
    ]
)

wf = Path(".github/workflows/ingest-at-mcp-search-posts-filters.yml")
if wf.exists():
    wf.unlink()
    run(["git", "add", "-u", str(wf)])
run(["git", "rm", "-r", "-f", "_render/at_mcp-search-posts-filters"])
run(["git", "commit", "-m", "Remove at_mcp search_posts filters ingest scaffolding"])

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
