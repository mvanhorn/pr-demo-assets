from pathlib import Path
import base64, hashlib, os, subprocess, sys, time

p = Path("_render/at_mcp-suggested-feeds")
out = Path("at_mcp/suggested-feeds")
out.mkdir(parents=True, exist_ok=True)

def load(prefix, n, raw_len, digest):
    b64 = "".join((p / f"{prefix}.{i}").read_text() for i in range(n))
    pad = (4 - len(b64) % 4) % 4
    data = base64.b64decode(b64 + "=" * pad)
    assert len(data) == raw_len, (prefix, len(data), raw_len)
    assert hashlib.sha256(data).hexdigest() == digest, prefix
    return data

gif = load("gif", 26, 1688120, "3401849f44dc055ede9ba8ca8c0bccc60f1b836d48ffdb131c8f827768d3ae14")
mp4 = load("mp4", 52, 3496903, "a58b2d400a547eea7df9e51b04670130874d89df0fcf20627b80a5b904b41e07")
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
run(["git", "add", "at_mcp/suggested-feeds/demo.gif", "at_mcp/suggested-feeds/demo.mp4"])
run([
    "git", "commit", "-m",
    "Add at_mcp suggested-feeds walkthrough GIF and MP4\n\nSilent 40s HyperFrames demo of get_suggested_feeds then get_feed.",
])

wf = Path(".github/workflows/ingest-at-mcp-suggested-feeds.yml")
if wf.exists():
    wf.unlink()
    run(["git", "add", "-u", str(wf)])
run(["git", "rm", "-r", "-f", "_render/at_mcp-suggested-feeds"])
run(["git", "commit", "-m", "Remove at_mcp suggested-feeds ingest scaffolding"])

def push():
    last = None
    for i in range(6):
        try:
            subprocess.check_call(["git", "pull", "--rebase", "origin", "main"], env=env)
            subprocess.check_call(["git", "push", "origin", "HEAD:main"], env=env)
            return
        except subprocess.CalledProcessError as e:
            last = e
            time.sleep(2 ** i)
    raise last

push()
