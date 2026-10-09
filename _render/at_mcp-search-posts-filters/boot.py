from pathlib import Path
import base64, hashlib, subprocess, sys

p = Path("_render/at_mcp-search-posts-filters")
out = Path("at_mcp/search-posts-filters")
out.mkdir(parents=True, exist_ok=True)

def load(prefix, n, raw_len, digest):
    b64 = "".join((p / f"{prefix}.{i}").read_text() for i in range(n))
    pad = (4 - len(b64) % 4) % 4
    data = base64.b64decode(b64 + "=" * pad)
    assert len(data) == raw_len, (prefix, len(data), raw_len)
    assert hashlib.sha256(data).hexdigest() == digest, prefix
    return data

gif = load("gif", 3, 1650727, "d39495eceb96d3bc5725c0164923a1410d6d1ee331e8c76626cd3686e0b047d8")
mp4 = load("mp4", 4, 2636647, "4b203edaf02bf80b373dc70a6a4a2f16f464dff3206b995c73b8de62cd8dbe72")
(out / "demo.gif").write_bytes(gif)
(out / "demo.mp4").write_bytes(mp4)

env = dict(**{k: v for k, v in __import__("os").environ.items()})
env["GIT_AUTHOR_NAME"] = "Matt Van Horn"
env["GIT_AUTHOR_EMAIL"] = "mvanhorn@users.noreply.github.com"
env["GIT_COMMITTER_NAME"] = "Matt Van Horn"
env["GIT_COMMITTER_EMAIL"] = "mvanhorn@users.noreply.github.com"

def run(args):
    subprocess.check_call(args, env=env)

run(["git", "rm", "-f", "--ignore-unmatch", "at_mcp/search-posts-filters/.ingest-probe"])
run(["git", "add", "at_mcp/search-posts-filters/demo.gif", "at_mcp/search-posts-filters/demo.mp4"])
run(["git", "commit", "-m", "Add at_mcp search_posts filters walkthrough demo\n\nGIF and MP4 for optional author, mentions, sort, since, until and lang\non search_posts."])

wf = Path(".github/workflows/ingest-at-mcp-search-posts-filters.yml")
if wf.exists():
    wf.unlink()
    run(["git", "add", "-u", str(wf)])
run(["git", "rm", "-r", "-f", "_render/at_mcp-search-posts-filters"])
run(["git", "commit", "-m", "Remove at_mcp search_posts filters ingest scaffolding"])
run(["git", "push"])
