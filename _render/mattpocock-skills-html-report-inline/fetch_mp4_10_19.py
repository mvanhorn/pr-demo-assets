#!/usr/bin/env python3
import hashlib
import os
import re
import subprocess
import time
import urllib.request
from pathlib import Path

DEST = Path("_render/mattpocock-skills-html-report-inline")
BRANCH = "ingest/html-report-mp4-b"
CHUNKS = {
    10: ("https://tmpfiles.org/wFAU6YJsrjNC/mp4.10", "93611f7e83d5d44bc257e9d5e23d735e412831cafbd8ba22181fa8d1dd2f7e3f"),
    11: ("https://tmpfiles.org/wFA76AJgrzxj/mp4.11", "abe75f98aec966085feae20060d29ec85474691fc931b1831d7c4258070ba1e4"),
    12: ("https://tmpfiles.org/wAAq6qJ0rk8d/mp4.12", "643cb10b022ad5b2d960c2b9ec98accf5085cd829a2641323327d2c2ee74c869"),
    13: ("https://tmpfiles.org/wbAK6NJQrfEk/mp4.13", "d79842a84d9d0cceccf78233cd8ac48c9a009fabaeddccb96807379aa81b05da"),
    14: ("https://tmpfiles.org/wQAQ6iJOrWpW/mp4.14", "06d8528939e35d91edc417b97c02efbb45512d8a6c027dc89de89566bda12302"),
    15: ("https://tmpfiles.org/wJAV6AJy2qwj/mp4.15", "633bdd5edee6230953882140525e01320d3ec059ef438a370bf37c0170993fba"),
    16: ("https://tmpfiles.org/wPAU6eJW23Ak/mp4.16", "758b652094c2108070930afd51a55aa729d18154365750257fe1ad22159d33ad"),
    17: ("https://tmpfiles.org/wNAD6fJx2wf7/mp4.17", "dd75a472b9063a394d4b02160f73cd3b9cd1e1d4b743a671dcb9c9c193033064"),
    18: ("https://tmpfiles.org/wFAr6zJt2blz/mp4.18", "e914c7f2d14b71bc20e2a6d0ee4cd7ee9dbb452ba1e0dff7e99181f52cb37062"),
    19: ("https://tmpfiles.org/w1AM6LJN2lgX/mp4.19", "b0736fd2d5066804c90d3dafb452061875f7637f2fb0d8ac8358527f399ede96"),
}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8.5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def get_bytes(page_url, digest):
    html = fetch(page_url).decode("utf-8", "replace")
    match = re.search(r"https://tmpfiles.org/dl/[^\"\s<]+", html)
    if not match:
        raise SystemExit(f"no download link in {page_url}")
    data = fetch(match.group(0))
    if data.lstrip()[:1] == b"<":
        raise SystemExit(f"html instead of chunk from {page_url}")
    got = hashlib.sha256(data).hexdigest()
    if got != digest:
        raise SystemExit(f"sha256 {got} != {digest} for {page_url}")
    if len(data) != 81053:
        raise SystemExit(f"length {len(data)} != 81053 for {page_url}")
    return data


env = dict(os.environ)
env["GIT_AUTHOR_NAME"] = "Matt Van Horn"
env["GIT_AUTHOR_EMAIL"] = "mvanhorn@users.noreply.github.com"
env["GIT_COMMITTER_NAME"] = "Matt Van Horn"
env["GIT_COMMITTER_EMAIL"] = "mvanhorn@users.noreply.github.com"


def run(args):
    subprocess.check_call(args, env=env)


run(["git", "config", "user.name", "Matt Van Horn"])
run(["git", "config", "user.email", "mvanhorn@users.noreply.github.com"])

for i in range(10, 20):
    page, digest = CHUNKS[i]
    data = get_bytes(page, digest)
    path = DEST / f"mp4.{i}"
    path.write_bytes(data)
    run(["git", "add", str(path)])
    run(["git", "commit", "-m", f"Add html-report-inline ingest chunk mp4.{i}"])

last_err = None
for attempt in range(8):
    try:
        run(["git", "pull", "--rebase", "origin", BRANCH])
        run(["git", "push", "origin", f"HEAD:{BRANCH}"])
        last_err = None
        break
    except subprocess.CalledProcessError as exc:
        last_err = exc
        time.sleep(2**attempt)
if last_err is not None:
    raise last_err
