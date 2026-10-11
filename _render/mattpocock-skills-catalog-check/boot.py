#!/usr/bin/env python3
from pathlib import Path
import base64
import hashlib
import os
import shutil
import subprocess
import time

ROOT = Path("_render/mattpocock-skills-catalog-check")
COMP = ROOT / "comp"
OUT = Path("mattpocock-skills/catalog-check")
OUT.mkdir(parents=True, exist_ok=True)

FONTS = (
    "EBGaramond-400.woff2",
    "Inter-400.woff2",
    "Inter-700.woff2",
    "JetBrainsMono-400.woff2",
    "JetBrainsMono-700.woff2",
)


def decode_font(name):
    text = "".join((ROOT / f"{name}.b64").read_text().split())
    pad = (4 - len(text) % 4) % 4
    return base64.b64decode(text + "=" * pad)


if COMP.exists():
    shutil.rmtree(COMP)
(COMP / "assets" / "fonts").mkdir(parents=True)
(COMP / "compositions").mkdir(parents=True)
shutil.copy(ROOT / "index.html", COMP / "index.html")
shutil.copy(ROOT / "hyperframes.json", COMP / "hyperframes.json")
shutil.copy(ROOT / "package.json", COMP / "package.json")
for name in FONTS:
    (COMP / "assets" / "fonts" / name).write_bytes(decode_font(name))

env = dict(os.environ)
env["GIT_AUTHOR_NAME"] = "Matt Van Horn"
env["GIT_AUTHOR_EMAIL"] = "mvanhorn@users.noreply.github.com"
env["GIT_COMMITTER_NAME"] = "Matt Van Horn"
env["GIT_COMMITTER_EMAIL"] = "mvanhorn@users.noreply.github.com"
env["CI"] = "1"


def run(args, **kwargs):
    print("+", " ".join(str(a) for a in args), flush=True)
    subprocess.check_call(args, env=env, **kwargs)


run(["git", "config", "user.name", "Matt Van Horn"])
run(["git", "config", "user.email", "mvanhorn@users.noreply.github.com"])
run(["npx", "--yes", "hyperframes@0.8.145", "browser", "ensure"], cwd=str(COMP))
run(
    [
        "npx",
        "--yes",
        "hyperframes@0.8.145",
        "render",
        "--format",
        "mp4",
        "--fps",
        "30",
        "--crf",
        "20",
        "--workers",
        "1",
        "--low-memory-mode",
        "--output",
        str((OUT / "demo.mp4").resolve()),
    ],
    cwd=str(COMP),
)

mp4 = OUT / "demo.mp4"
if not mp4.exists() or mp4.stat().st_size < 100_000:
    raise SystemExit(f"mp4 missing or tiny: {mp4}")

gif = OUT / "demo.gif"
palette = Path("/tmp/catalog-check-palette.png")


def encode_gif(fps, colors, scale=5):
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(mp4),
            "-vf",
            f"fps={fps},scale=720:-1:flags=lanczos,palettegen=stats_mode=full:max_colors={colors}",
            str(palette),
        ]
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(mp4),
            "-i",
            str(palette),
            "-lavfi",
            f"fps={fps},scale=720:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale={scale}",
            "-loop",
            "0",
            str(gif),
        ]
    )


encode_gif(12, 96)
if gif.stat().st_size >= 8 * 1024 * 1024:
    print("gif too large, retrying with 10fps/72 colors", flush=True)
    encode_gif(10, 72)
if gif.stat().st_size >= 8 * 1024 * 1024:
    print("gif too large, retrying with 10fps/64 colors", flush=True)
    encode_gif(10, 64, scale=4)
if gif.stat().st_size >= 8 * 1024 * 1024:
    raise SystemExit(f"gif still too large: {gif.stat().st_size}")

probe = subprocess.check_output(
    [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,r_frame_rate",
        "-show_entries",
        "format=duration,size",
        "-of",
        "json",
        str(mp4),
    ],
    env=env,
    text=True,
)
print("mp4 probe", probe, flush=True)
print("gif bytes", gif.stat().st_size, flush=True)
print("mp4 sha256", hashlib.sha256(mp4.read_bytes()).hexdigest(), flush=True)
print("gif sha256", hashlib.sha256(gif.read_bytes()).hexdigest(), flush=True)

run(
    [
        "git",
        "add",
        "mattpocock-skills/catalog-check/demo.gif",
        "mattpocock-skills/catalog-check/demo.mp4",
    ]
)
run(
    [
        "git",
        "commit",
        "-m",
        "Add mattpocock-skills catalog-check walkthrough GIF and MP4",
    ]
)

for wf_name in (
    "ingest-mattpocock-skills-catalog-check.yml",
    "fetch-catalog-mp4-0-18.yml",
):
    wf = Path(".github/workflows") / wf_name
    if wf.exists():
        wf.unlink()
        run(["git", "add", "-u", str(wf)])

if ROOT.exists():
    run(["git", "rm", "-r", "-f", str(ROOT)])
run(["git", "commit", "-m", "Remove mattpocock-skills catalog-check ingest scaffolding"])

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
