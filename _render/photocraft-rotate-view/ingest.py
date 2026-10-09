#!/usr/bin/env python3
from pathlib import Path
import base64, gzip, hashlib, shutil, subprocess, sys, time

ROOT = Path("_render/photocraft-rotate-view")
DEST = Path("photocraft/rotate-view")
EXPECTED = "c43c1504961595af6a5764e161dcbfb0213c6b3b7ee5d7060ef183992e4430ac"


def run(cmd, cwd=None):
    print("+", " ".join(cmd), flush=True)
    subprocess.check_call(cmd, cwd=str(cwd) if cwd else None)


def decode_html():
    raw = "".join((ROOT / "index.html.gz.b64").read_text().split())
    raw += "=" * ((4 - len(raw) % 4) % 4)
    html = gzip.decompress(base64.b64decode(raw))
    digest = hashlib.sha256(html).hexdigest()
    assert digest == EXPECTED, digest
    (ROOT / "index.html").write_bytes(html)
    print("html", len(html), digest, flush=True)


def pick_snapshot(snapshots, needle):
    if not snapshots.is_dir():
        return None
    for name in sorted(snapshots.iterdir()):
        if needle in name.name:
            return name
    return None


def main():
    decode_html()
    run(["npx", "--yes", "hyperframes@0.8.143", "browser", "ensure"], cwd=ROOT)
    run(
        [
            "npx",
            "--yes",
            "hyperframes@0.8.143",
            "render",
            "--format",
            "mp4",
            "--output",
            "out.mp4",
            "--workers",
            "1",
            "--no-browser-gpu",
        ],
        cwd=ROOT,
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            "out.mp4",
            "-vf",
            "fps=12,scale=720:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128:stats_mode=diff[p];[s1][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle",
            "preview.gif",
        ],
        cwd=ROOT,
    )
    run(
        [
            "npx",
            "--yes",
            "hyperframes@0.8.143",
            "snapshot",
            "--at",
            "1.2,4.4,7.5,12,22,27.2,30.5",
            "--no-end",
            "--timeout",
            "60000",
            "--output",
            "snapshots",
        ],
        cwd=ROOT,
    )
    mapping = {
        "at-1.2s": "rotate-view-demo.png",
        "at-4.4s": "before-hand-toolbar.png",
        "at-7.5s": "after-hand-flyout-triangle.png",
        "at-12s": "after-rotate-view-options.png",
        "at-22s": "after-canvas-45.png",
        "at-27.2s": "after-canvas-24mp-0.png",
        "at-30.5s": "after-canvas-24mp-37.png",
    }
    snaps = ROOT / "snapshots"
    for needle, dest_name in mapping.items():
        src = pick_snapshot(snaps, needle)
        dest = ROOT / dest_name
        if src:
            shutil.copyfile(src, dest)
        if not dest.is_file() or dest.stat().st_size == 0:
            ss = needle.replace("at-", "").replace("s", "")
            run(
                [
                    "ffmpeg",
                    "-y",
                    "-ss",
                    ss,
                    "-i",
                    "out.mp4",
                    "-update",
                    "1",
                    "-frames:v",
                    "1",
                    dest_name,
                ],
                cwd=ROOT,
            )
        assert dest.is_file() and dest.stat().st_size != 0, dest_name

    gif = ROOT / "preview.gif"
    mp4 = ROOT / "out.mp4"
    assert mp4.stat().st_size != 0
    assert gif.stat().st_size != 0
    max_gif = 8000000
    if min(gif.stat().st_size, max_gif) != gif.stat().st_size:
        raise SystemExit("gif too large %s" % gif.stat().st_size)

    DEST.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(gif, DEST / "demo.gif")
    shutil.copyfile(mp4, DEST / "demo.mp4")
    for name in mapping.values():
        shutil.copyfile(ROOT / name, DEST / name)

    run(["git", "config", "user.name", "Matt Van Horn"])
    run(["git", "config", "user.email", "mvanhorn@users.noreply.github.com"])
    subprocess.call(["git", "rm", "-rf", "--ignore-unmatch", str(ROOT)])
    subprocess.call(
        ["git", "rm", "-f", ".github/workflows/ingest-photocraft-rotate-view.yml"]
    )
    run(
        [
            "git",
            "add",
            "photocraft/rotate-view/demo.gif",
            "photocraft/rotate-view/demo.mp4",
            "photocraft/rotate-view/rotate-view-demo.png",
            "photocraft/rotate-view/before-hand-toolbar.png",
            "photocraft/rotate-view/after-hand-flyout-triangle.png",
            "photocraft/rotate-view/after-rotate-view-options.png",
            "photocraft/rotate-view/after-canvas-45.png",
            "photocraft/rotate-view/after-canvas-24mp-0.png",
            "photocraft/rotate-view/after-canvas-24mp-37.png",
        ]
    )
    run(
        [
            "git",
            "commit",
            "-m",
            "Add photocraft Rotate View walkthrough GIF, MP4, and screenshots",
        ]
    )
    for i in range(1, 6):
        try:
            run(["git", "pull", "--rebase", "origin", "main"])
            run(["git", "push", "origin", "HEAD:main"])
            return
        except subprocess.CalledProcessError:
            subprocess.call(["git", "rebase", "--abort"])
            time.sleep(i * 3)
    raise SystemExit("push failed")


if __name__ == "__main__":
    main()
