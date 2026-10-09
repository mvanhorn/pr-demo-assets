from pathlib import Path
import base64
import hashlib
import os
import subprocess
import time
import urllib.request

p = Path("_render/ladybug-list-min-max")
out = Path("ladybug/list-min-max")
out.mkdir(parents=True, exist_ok=True)

EXPECTED = {("gif", i): 90000 for i in range(17)}
EXPECTED[("gif", 17)] = 64628
EXPECTED.update({("mp4", i): 90000 for i in range(37)})
EXPECTED[("mp4", 37)] = 7216

FETCH = {
    "mp4.0": "https://litter.catbox.moe/oqzpqc.0",
    "mp4.1": "https://litter.catbox.moe/wndqby.1",
    "mp4.2": "https://litter.catbox.moe/7n1dmy.2",
    "mp4.3": "https://litter.catbox.moe/dc3zwt.3",
    "mp4.4": "https://litter.catbox.moe/6s77uk.4",
    "mp4.5": "https://litter.catbox.moe/mcy5ad.5",
    "mp4.6": "https://litter.catbox.moe/zdi93c.6",
    "mp4.7": "https://litter.catbox.moe/m62t2m.7",
    "mp4.8": "https://litter.catbox.moe/p356qy.8",
    "mp4.9": "https://litter.catbox.moe/64a07r.9",
    "mp4.10": "https://litter.catbox.moe/7h9ecl.10",
    "mp4.11": "https://litter.catbox.moe/shuysa.11",
    "mp4.12": "https://litter.catbox.moe/v75bhc.12",
}

UA = {"User-Agent": "ladybug-ingest/1.0"}


def http_get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("ascii")


def resolve_text(text):
    t = text.strip()
    if t.startswith("http://") or t.startswith("https://"):
        t = http_get(t.split()[0])
    return "".join(t.split())


def chunk_body(prefix, i):
    want = EXPECTED.get((prefix, i))
    parts = []
    j = 0
    while True:
        fp = p / f"{prefix}.{i}.{j}"
        if not fp.exists():
            break
        parts.append(fp.read_text())
        j += 1
    if parts:
        joined = "".join(resolve_text(x) for x in parts)
        if not want or len(joined) == want:
            return joined
    fp = p / f"{prefix}.{i}"
    name = f"{prefix}.{i}"
    body = fp.read_text() if fp.exists() else ""
    stripped = resolve_text(body) if body else ""
    if want and len(stripped) == want:
        return stripped
    if name in FETCH:
        got = "".join(http_get(FETCH[name]).split())
        if not want or len(got) == want:
            return got
    if stripped:
        return stripped
    return None


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
