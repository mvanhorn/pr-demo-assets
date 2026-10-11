#!/usr/bin/env python3
from pathlib import Path
import base64
import hashlib
import os
import shutil
import subprocess
import time

ROOT = Path("_render/artcraft-native-frame-extract")
COMP = Path("_render/artcraft-native-frame-extract/comp")
OUT = Path("artcraft/native-frame-extract")
OUT.mkdir(parents=True, exist_ok=True)

ASSETS = (
    ("before", 8, "before.png", 115167, "61c024d3def4afc80886d89b432d26c10657fef4f10eac60998493bdad0569f9"),
    ("afterempty", 8, "after-empty.png", 117442, "7e608626a8bb3bbdad3f75e27d242ef400ad69f36828eb99182481349734007d"),
    ("after", 15, "after.png", 215906, "99a6ca4117a6599e27c606955c198de0c3447cce49ace78668dd081f73b7e35f"),
    ("loaded", 10, "loaded.png", 144413, "90542b891e5624e1c0d239046bc58bc8b092c48e9c02109cb8e1ba4634af26b4"),
    ("frame01", 5, "frame-01-00-00-000.png", 64535, "ca4cbf57f848af9e81bf598b76dc044285169b76aa39cc09f1427d82018cb679"),
    ("frame10", 5, "frame-10-00-00-900.png", 67371, "3d0ccb94bbd108e84e16fab5ab18f9a02920e90b169e68722fefb9aeaf8556fc"),
)


def load(prefix, n, raw_len, digest):
    texts = []
    for i in range(n):
        fp = ROOT / f"{prefix}.{i}"
        if not fp.exists():
            raise SystemExit(f"missing {fp}")
        texts.append("".join(fp.read_text().split()))
    b64 = "".join(texts)
    pad = (4 - len(b64) % 4) % 4
    data = base64.b64decode(b64 + "=" * pad)
    if len(data) != raw_len:
        raise SystemExit(f"{prefix} length {len(data)} != {raw_len}")
    got = hashlib.sha256(data).hexdigest()
    if got != digest:
        raise SystemExit(f"{prefix} sha256 {got} != {digest}")
    return data


if COMP.exists():
    shutil.rmtree(COMP)
(COMP / "assets").mkdir(parents=True)
(COMP / "compositions").mkdir(parents=True)
shutil.copy(ROOT / "index.html", COMP / "index.html")
shutil.copy(ROOT / "hyperframes.json", COMP / "hyperframes.json")
shutil.copy(ROOT / "package.json", COMP / "package.json")

decoded = {}
for prefix, n, png_name, raw_len, digest in ASSETS:
    data = load(prefix, n, raw_len, digest)
    decoded[png_name] = data
    (COMP / "assets" / png_name).write_bytes(data)

(OUT / "before.png").write_bytes(decoded["before.png"])
(OUT / "after-empty.png").write_bytes(decoded["after-empty.png"])
(OUT / "after.png").write_bytes(decoded["after.png"])

env = dict(os.environ)
env["GIT_AUTHOR_NAME"] = "Matt Van Horn"
env["GIT_AUTHOR_EMAIL"] = "mvanhorn@users.noreply.github.com"
env["GIT_COMMITTER_NAME"] = "Matt Van Horn"
env["GIT_COMMITTER_EMAIL"] = "mvanhorn@users.noreply.github.com"
env["CI"] = "1"


def run(args, **kwargs):
    print("+", " ".join(args), flush=True)
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
palette = Path("/tmp/artcraft-palette.png")
run(
    [
        "ffmpeg",
        "-y",
        "-i",
        str(mp4),
        "-vf",
        "fps=10,scale=720:-1:flags=lanczos,palettegen=stats_mode=full:max_colors=96",
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
        "fps=10,scale=720:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=5",
        "-loop",
        "0",
        str(gif),
    ]
)

gif_bytes = gif.stat().st_size
if gif_bytes >= 8 * 1024 * 1024:
    print(f"gif {gif_bytes} too large, retrying with 72 colors", flush=True)
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(mp4),
            "-vf",
            "fps=10,scale=720:-1:flags=lanczos,palettegen=stats_mode=full:max_colors=72",
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
            "fps=10,scale=720:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=5",
            "-loop",
            "0",
            str(gif),
        ]
    )
    gif_bytes = gif.stat().st_size
if gif_bytes >= 8 * 1024 * 1024:
    raise SystemExit(f"gif still too large: {gif_bytes}")

probe = subprocess.check_output(
    [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-show_entries",
        "format=duration",
        "-of",
        "csv=p=0",
        str(mp4),
    ],
    env=env,
    text=True,
).strip()
print("mp4 probe", probe, "size", mp4.stat().st_size, flush=True)
print("gif size", gif_bytes, flush=True)

run(
    [
        "git",
        "add",
        "artcraft/native-frame-extract/demo.gif",
        "artcraft/native-frame-extract/demo.mp4",
        "artcraft/native-frame-extract/before.png",
        "artcraft/native-frame-extract/after-empty.png",
        "artcraft/native-frame-extract/after.png",
    ]
)
run(
    [
        "git",
        "commit",
        "-m",
        "Add ArtCraft native Frame Extract walkthrough GIF and MP4",
    ]
)

wf = Path(".github/workflows/ingest-artcraft-native-frame-extract.yml")
if wf.exists():
    wf.unlink()
    run(["git", "add", "-u", str(wf)])
run(["git", "rm", "-r", "-f", "_render/artcraft-native-frame-extract"])
run(["git", "commit", "-m", "Remove ArtCraft native Frame Extract ingest scaffolding"])

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
