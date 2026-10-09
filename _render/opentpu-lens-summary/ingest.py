#!/usr/bin/env python3
from pathlib import Path
import os
import shutil
import subprocess
import time

ROOT = Path("_render/opentpu-lens-summary")
DEST = Path("openTPU/lens-summary")
HF = "hyperframes@0.8.143"
MAX_GIF = 8_000_000
WORKFLOW = ".github/workflows/ingest-opentpu-lens-summary.yml"


def run(cmd, cwd=None, env=None):
    print("+", " ".join(cmd), flush=True)
    subprocess.check_call(cmd, cwd=str(cwd) if cwd else None, env=env)


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    html = (ROOT / "index.html").read_bytes()
    if b"cdn.jsdelivr.net/fontsource/fonts" not in html:
        raise SystemExit("index.html is missing font CDN urls")

    run(["npx", "--yes", HF, "browser", "ensure"], cwd=ROOT)
    run(
        [
            "npx",
            "--yes",
            HF,
            "render",
            "--format",
            "mp4",
            "--quality",
            "delivery",
            "--fps",
            "30",
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
            "fps=12,scale=720:-2:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128:stats_mode=diff[p];[s1][p]paletteuse=dither=none",
            "-loop",
            "0",
            "preview.gif",
        ],
        cwd=ROOT,
    )

    gif = ROOT / "preview.gif"
    mp4 = ROOT / "out.mp4"
    if not mp4.is_file() or mp4.stat().st_size == 0:
        raise SystemExit("missing mp4")
    if not gif.is_file() or gif.stat().st_size == 0:
        raise SystemExit("missing gif")
    if gif.stat().st_size >= MAX_GIF:
        raise SystemExit("gif too large %s" % gif.stat().st_size)

    probe = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,codec_name",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(mp4),
        ]
    ).decode()
    print(probe, flush=True)
    if '"width": 1920' not in probe or '"height": 1080' not in probe:
        raise SystemExit("mp4 is not 1920x1080")

    shutil.copyfile(gif, DEST / "demo.gif")
    shutil.copyfile(mp4, DEST / "demo.mp4")
    (DEST / "README.md").write_text(
        "38s 1920x1080 MP4 and 720px GIF of otpu-lens summary: ISA record, "
        "dashboard (roofline, unit utilisation, MM class), info one-liner.\n"
    )

    run(["git", "config", "user.name", "Matt Van Horn"])
    run(["git", "config", "user.email", "mvanhorn@users.noreply.github.com"])
    subprocess.call(["git", "rm", "-rf", "--ignore-unmatch", str(ROOT)])
    subprocess.call(["git", "rm", "-f", "--ignore-unmatch", WORKFLOW])
    run(["git", "add", str(DEST / "demo.gif"), str(DEST / "demo.mp4"), str(DEST / "README.md")])
    run(
        [
            "git",
            "commit",
            "-m",
            "Add openTPU lens summary demo assets",
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
                subprocess.check_call(
                    ["git", "-c", "core.editor=true", "commit", "--no-edit"],
                    env=env,
                )
            run(["git", "push", "origin", "HEAD:main"])
            return
        except subprocess.CalledProcessError as exc:
            last = exc
            subprocess.call(["git", "merge", "--abort"])
            subprocess.call(["git", "rebase", "--abort"])
            time.sleep(i * 3)
    raise SystemExit("push failed: %s" % last)


if __name__ == "__main__":
    main()
