#!/usr/bin/env python3
from pathlib import Path
import base64
import gzip
import hashlib
import os
import shutil
import subprocess
import time

ROOT = Path("_render/holmesgpt-doctor-cli")
DEST = Path("holmesgpt/doctor-cli")
HF = "hyperframes@0.8.143"
MAX_GIF = 8_000_000
WORKFLOW = ".github/workflows/ingest-holmesgpt-doctor-cli.yml"
HTML_SHA = "644e69ca9439ff78d5799ff44e9bb45e38f903e6cf30b8ae0fc728db11309b10"


def run(cmd, cwd=None, env=None):
    print("+", " ".join(cmd), flush=True)
    subprocess.check_call(cmd, cwd=str(cwd) if cwd else None, env=env)


def decode_html():
    b64 = "".join((ROOT / ("html.b64.%d" % i)).read_text() for i in range(4))
    b64 += "=" * ((4 - len(b64) % 4) % 4)
    html = gzip.decompress(base64.b64decode(b64))
    digest = hashlib.sha256(html).hexdigest()
    if digest != HTML_SHA:
        raise SystemExit("html sha256 %s != %s" % (digest, HTML_SHA))
    if b"cdn.jsdelivr.net/fontsource/fonts" not in html:
        raise SystemExit("index.html is missing font CDN urls")
    (ROOT / "index.html").write_bytes(html)
    print("html", len(html), digest, flush=True)


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    decode_html()

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
            "looks",
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
            "fps=12,scale=720:-2:flags=lanczos,split[s0][s1];[s0]palettegen=stats_mode=diff:max_colors=128[p];[s1][p]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle",
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
        "36s 1920x1080 MP4 and 720px GIF of holmes doctor: help, "
        "fail-closed credentials, redacted key presence, --json, and toolset counts.\n"
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
