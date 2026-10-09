#!/usr/bin/env python3
"""Decode Rotate View demo assets and commit them as Matt Van Horn."""

from __future__ import annotations

import base64
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path("_render/photocraft-rotate-view")
DEST = Path("photocraft/rotate-view")
WORKFLOW = Path(".github/workflows/ingest-photocraft-rotate-view.yml")
FILES = [
    "demo.gif",
    "demo.mp4",
    "rotate-view-demo.png",
    "before-hand-toolbar.png",
    "after-hand-flyout-triangle.png",
    "after-rotate-view-options.png",
    "after-canvas-45.png",
    "after-canvas-24mp-0.png",
    "after-canvas-24mp-37.png",
]


def decode(name: str) -> bytes:
    parts = sorted(ROOT.glob(f"{name}.b64.*"))
    if not parts:
        raise SystemExit(f"missing chunks for {name}")
    b64 = "".join(p.read_text().split() for p in parts)
    pad = (4 - len(b64) % 4) % 4
    return base64.b64decode(b64 + "=" * pad)


def git(*args: str) -> None:
    subprocess.check_call(["git", *args])


def main() -> None:
    os.environ.setdefault("GIT_AUTHOR_NAME", "Matt Van Horn")
    os.environ.setdefault("GIT_AUTHOR_EMAIL", "mvanhorn@users.noreply.github.com")
    os.environ.setdefault("GIT_COMMITTER_NAME", "Matt Van Horn")
    os.environ.setdefault("GIT_COMMITTER_EMAIL", "mvanhorn@users.noreply.github.com")
    DEST.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        data = decode(name)
        dest = DEST / name
        dest.write_bytes(data)
        print(f"wrote {dest} {len(data)} bytes")
    if WORKFLOW.exists():
        WORKFLOW.unlink()
    shutil.rmtree(ROOT, ignore_errors=True)
    git("add", "-A")
    status = subprocess.check_output(["git", "status", "--porcelain"], text=True)
    print(status)
    if not status.strip():
        print("nothing to commit")
        return
    git("commit", "--no-verify", "-m", "Add photocraft Rotate View walkthrough assets")
    git("push")


if __name__ == "__main__":
    main()
