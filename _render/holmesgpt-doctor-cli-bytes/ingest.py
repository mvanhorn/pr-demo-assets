#!/usr/bin/env python3
"""Pull exact local holmes doctor demo bytes through a short-lived tunnel and commit them."""
from __future__ import annotations

import hashlib
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

DEST = Path("holmesgpt/doctor-cli")
WORKFLOW = ".github/workflows/ingest-holmesgpt-doctor-cli-bytes.yml"
ROOT = Path("_render/holmesgpt-doctor-cli-bytes")
BASE = os.environ.get("DOCTOR_BYTES_BASE", "https://silly-rabbits-pull.loca.lt").rstrip("/")

FILES = {
    "demo.gif": {
        "url_name": "demo.gif",
        "sha256": "8e75f34ae5a54fdfa6d1cd60b4ff9cccbd8165f5dc9312cb200b273f0d2a31fc",
        "size": 1376772,
        "magic": (b"GIF89a",),
    },
    "demo.mp4": {
        "url_name": "demo.mp4",
        "sha256": "bd652accb499a203cdbd34b5ecd42a232c981299baed8afd4dd33004129787b7",
        "size": 3117783,
        "magic": (b"\x00\x00\x00\x20ftypisom", b"\x00\x00\x00\x18ftypisom"),
    },
}


def run(cmd: list[str], env=None) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.check_call(cmd, env=env)


def looks_like_media(data: bytes, dest_name: str) -> bool:
    if dest_name.endswith(".gif"):
        return data.startswith(b"GIF89a") or data.startswith(b"GIF87a")
    if dest_name.endswith(".mp4"):
        return len(data) > 12 and data[4:8] == b"ftyp"
    return False


def fetch(dest_name: str, spec: dict) -> bytes:
    url = f"{BASE}/{spec['url_name']}"
    headers = {
        "Bypass-Tunnel-Reminder": "true",
        "User-Agent": "curl/8.5.0",
        "Accept": "*/*",
    }
    last = "no attempt"
    for i in range(1, 10):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = resp.read()
            sha = hashlib.sha256(data).hexdigest()
            print(
                f"fetched {dest_name} status=ok bytes={len(data)} sha256={sha} head={data[:16]!r}",
                flush=True,
            )
            if not looks_like_media(data, dest_name):
                last = f"not media (html interstitial?): bytes={len(data)} head={data[:80]!r}"
            elif len(data) != spec["size"]:
                last = f"size {len(data)} != {spec['size']}"
            elif sha != spec["sha256"]:
                last = f"sha256 {sha} != {spec['sha256']}"
            else:
                return data
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last = str(exc)
        print(f"retry {i} {dest_name}: {last}", flush=True)
        time.sleep(i * 2)
    raise SystemExit(f"failed to fetch exact {dest_name}: {last}")


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    for name, spec in FILES.items():
        data = fetch(name, spec)
        (DEST / name).write_bytes(data)
        print(f"wrote {DEST / name} {len(data)}", flush=True)

    run(["git", "config", "user.name", "Matt Van Horn"])
    run(["git", "config", "user.email", "mvanhorn@users.noreply.github.com"])
    subprocess.call(["git", "rm", "-rf", "--ignore-unmatch", str(ROOT)])
    subprocess.call(["git", "rm", "-f", "--ignore-unmatch", WORKFLOW])
    run(["git", "add", str(DEST / "demo.gif"), str(DEST / "demo.mp4")])
    run(
        [
            "git",
            "commit",
            "-m",
            "Add holmes doctor CLI walkthrough demo\n\n"
            "36s 1920x1080 MP4 and 720px GIF of holmes doctor: help, "
            "fail-closed credentials, redacted key presence, --json, and toolset counts.",
        ]
    )

    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = "Matt Van Horn"
    env["GIT_AUTHOR_EMAIL"] = "mvanhorn@users.noreply.github.com"
    env["GIT_COMMITTER_NAME"] = "Matt Van Horn"
    env["GIT_COMMITTER_EMAIL"] = "mvanhorn@users.noreply.github.com"
    env["GIT_EDITOR"] = "true"

    last = None
    for i in range(1, 9):
        try:
            run(["git", "fetch", "origin", "main"])
            merged = subprocess.call(["git", "merge", "--no-edit", "origin/main"])
            if merged != 0:
                subprocess.call(["git", "rm", "-rf", "--ignore-unmatch", str(ROOT)])
                subprocess.call(["git", "rm", "-f", "--ignore-unmatch", WORKFLOW])
                subprocess.call(["git", "add", "-A", str(DEST)])
                subprocess.check_call(["git", "-c", "core.editor=true", "commit", "--no-edit"], env=env)
            run(["git", "push", "origin", "HEAD:main"])
            return
        except subprocess.CalledProcessError as exc:
            last = exc
            subprocess.call(["git", "merge", "--abort"])
            subprocess.call(["git", "rebase", "--abort"])
            time.sleep(i * 3)
    raise SystemExit(f"push failed: {last}")


if __name__ == "__main__":
    main()
