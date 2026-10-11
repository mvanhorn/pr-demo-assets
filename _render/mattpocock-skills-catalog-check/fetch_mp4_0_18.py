#!/usr/bin/env python3
import hashlib
import os
import re
import subprocess
import time
import urllib.request
from pathlib import Path

DEST = Path("_render/mattpocock-skills-catalog-check")
DEST.mkdir(parents=True, exist_ok=True)

CHUNKS = {
    0: ("https://tmpfiles.org/wfA661or683v/mp4.0", "652e39431fb51286cadd78190bb798d23c331ce6b77678b69042462cac8c88c7"),
    1: ("https://tmpfiles.org/wCAB6Eoc6kYg/mp4.1", "4390a52e9d42cb77427c8f7395342710a6369e18abde4a720b1feb9c9ff95327"),
    2: ("https://tmpfiles.org/wWAz6Vo96p1R/mp4.2", "1eeb68b0e4ee5910170945d27fa19d941fff3a6d28f3a9ad023c27da206beefb"),
    3: ("https://tmpfiles.org/wWAC6Bof6fuC/mp4.3", "19685377093b1840310e22fda9e0f3161f4f8b871a182b48f1112e8a33cdfb4f"),
    4: ("https://tmpfiles.org/wbAe6Ao96I9I/mp4.4", "ab78fbfcd8fffc0105328da819171d3594ce321f0998e148b039917c3ba5a6aa"),
    5: ("https://tmpfiles.org/wDAR6yo16OzF/mp4.5", "7b2f0718ae31c5075070f6688a6f7dd0b366a27bd1d1a5b4cc457e3e8a19a694"),
    6: ("https://tmpfiles.org/wjA86Hoj6XR6/mp4.6", "413ad6dd1412b6fba89cfaa58346d21abba34842f0b9df5f8095e40e3a7bd44a"),
    7: ("https://tmpfiles.org/w6AE6UoY6AIO/mp4.7", "9bf296937a13c0005aa00491801da0b29ba482af967f745b8ad29b8a972db6f3"),
    8: ("https://tmpfiles.org/wnAL6Ioq6QFI/mp4.8", "a118f7e12cd378cc3d448aeeda06fa8238cc1f9509e645d3aa653b1f04140679"),
    9: ("https://tmpfiles.org/weAq6HoJ6lDb/mp4.9", "b17ec02f5fad27de24af8df281333013e0169cbd80f8246e42979726b5157fff"),
    10: ("https://tmpfiles.org/wqAT6zok6dCD/mp4.10", "e184c455c973e0b69c6c8edca9e6c2683cac4d1213f259ee537d33b96527fd6e"),
    11: ("https://tmpfiles.org/wjAI6WoF6oGP/mp4.11", "94e87b4b26f4257abfd7a23310dbb13087a8de523c8e5acef56b3e5243ba6c0e"),
    12: ("https://tmpfiles.org/wZA16ZoT60BN/mp4.12", "2efd597d460e9d4e23dadf8fc1282b4dc2b8679a6723423a1bf56b7fe2cd34b3"),
    13: ("https://tmpfiles.org/wMAP6qoY6nh3/mp4.13", "aaf2f488061461b0f09f74595cd3029df75c2f626d52d7031de010ea55b7d536"),
    14: ("https://tmpfiles.org/wsAP6RoT6V4C/mp4.14", "0f1fe689cb75cd3094cfc3aa0468fc9a8a6a67a4a3feb5fcf496fab3c74c67bc"),
    15: ("https://tmpfiles.org/w8Au6joX6hmR/mp4.15", "8d8ad175947a35513ddd9044d2a8d6fe6e2d2a4b199458edf9ba0c952011a463"),
    16: ("https://tmpfiles.org/wfAS6foS6fq4/mp4.16", "d92c861791a1478768992d59486d4b8aa678610029753b631f6e21696ea96746"),
    17: ("https://tmpfiles.org/wGAI6cod6INL/mp4.17", "0b3acb0bc20b5c9e6b8dccfc02a7e4179beb597556e2d128bc10d85cb60139f9"),
    18: ("https://tmpfiles.org/whAQ6poN6dxj/mp4.18", "5f256e55d8424f68e139bcf6fbc333dfe1dfe9e90448479fd21695f09ab8e32e"),
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
    if len(data) != 80000:
        raise SystemExit(f"length {len(data)} != 80000 for {page_url}")
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

for i in range(19):
    page, digest = CHUNKS[i]
    data = get_bytes(page, digest)
    path = DEST / f"mp4.{i}"
    path.write_bytes(data)
    run(["git", "add", str(path)])
    run(["git", "commit", "-m", f"Add catalog-check ingest chunk mp4.{i}"])

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
