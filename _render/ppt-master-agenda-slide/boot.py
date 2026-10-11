#!/usr/bin/env python3
from pathlib import Path
import hashlib
import os
import re
import subprocess
import time
import urllib.request

out = Path("ppt-master/agenda-slide")
out.mkdir(parents=True, exist_ok=True)

FILES = (
    (
        "demo.gif",
        "https://tmpfiles.org/wEAY6GosHMog/demo.gif",
        496811,
        "1ccc6b4d37da96248cc72c7e9f10f160d69b12ca6fa3b0d5cf7d48d3c89b67e2",
    ),
    (
        "demo.mp4",
        "https://tmpfiles.org/w2An6PodH85R/demo.mp4",
        1029775,
        "d1a8a463d8e098290f16d46878471ec1431ec69f5dfb8a5b0ee5528c524aeb9a",
    ),
)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8.5.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def get_bytes(page_url, raw_len, digest):
    html = fetch(page_url).decode("utf-8", "replace")
    match = re.search(r"https://tmpfiles.org/dl/[^\"\s<]+", html)
    if not match:
        raise SystemExit(f"no download link in {page_url}")
    data = fetch(match.group(0))
    if data.lstrip()[:1] == b"<":
        raise SystemExit(f"html instead of file from {page_url}")
    if len(data) != raw_len:
        raise SystemExit(f"length {len(data)} != {raw_len} for {page_url}")
    got = hashlib.sha256(data).hexdigest()
    if got != digest:
        raise SystemExit(f"sha256 {got} != {digest} for {page_url}")
    return data


for name, page, raw_len, digest in FILES:
    (out / name).write_bytes(get_bytes(page, raw_len, digest))

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
        "ppt-master/agenda-slide/demo.gif",
        "ppt-master/agenda-slide/demo.mp4",
    ]
)
run(["git", "commit", "-m", "Add ppt-master/agenda-slide demo"])

wf = Path(".github/workflows/ingest-ppt-master-agenda-slide.yml")
if wf.exists():
    wf.unlink()
    run(["git", "add", "-u", str(wf)])
run(["git", "rm", "-r", "-f", "_render/ppt-master-agenda-slide"])
run(["git", "commit", "-m", "Remove ppt-master agenda-slide ingest scaffolding"])

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
