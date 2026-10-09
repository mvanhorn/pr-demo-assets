#!/usr/bin/env python3
from pathlib import Path
import base64
import gzip
import hashlib
import os
import shutil
import subprocess
import time
import urllib.request

ROOT = Path("_render/ladybug-list-has-any")
DEST = Path("ladybug/list-has-any")
HF = "hyperframes@0.8.143"
MAX_GIF = 8_000_000
HTML_SHA = "1dda11767f9b1aa65c387666379cdec62c7e05fda3a9e726bdf58772b982cb61"
MONTSERRAT_FACE = """      @font-face {
        font-family: Montserrat;
        src: url("assets/Montserrat-Regular.ttf") format("truetype");
        font-weight: 400;
        font-style: normal;
      }
      @font-face {
        font-family: Montserrat;
        src: url("assets/Montserrat-Bold.ttf") format("truetype");
        font-weight: 700;
        font-style: normal;
      }
"""


def run(cmd, cwd=None):
    print("+", " ".join(cmd), flush=True)
    subprocess.check_call(cmd, cwd=str(cwd) if cwd else None)


def decode_html():
    b64 = "".join((ROOT / "index.html.gz.b64").read_text().split())
    b64 += "=" * ((4 - len(b64) % 4) % 4)
    html = gzip.decompress(base64.b64decode(b64))
    digest = hashlib.sha256(html).hexdigest()
    if digest != HTML_SHA:
        raise SystemExit("html sha256 %s != %s" % (digest, HTML_SHA))
    if b"font-family: Montserrat;" in html and b"Montserrat-Bold.ttf" not in html:
        html = html.replace(b"      * { margin: 0;", MONTSERRAT_FACE.encode() + b"      * { margin: 0;", 1)
    (ROOT / "index.html").write_bytes(html)
    print("html", len(html), digest, flush=True)


def fetch(url, dest):
    print("fetch", url, "->", dest, flush=True)
    req = urllib.request.Request(url, headers={"User-Agent": "ladybug-demo-ingest"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        dest.write_bytes(resp.read())
    if dest.stat().st_size < 1000:
        raise SystemExit("tiny download %s" % dest)


def prepare_fonts():
    assets = ROOT / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    dejavu = Path("/usr/share/fonts/truetype/dejavu")
    shutil.copyfile(dejavu / "DejaVuSansMono.ttf", assets / "DejaVuSansMono.ttf")
    shutil.copyfile(dejavu / "DejaVuSansMono-Bold.ttf", assets / "DejaVuSansMono-Bold.ttf")
    fetch(
        "https://raw.githubusercontent.com/JetBrains/JetBrainsMono/master/fonts/ttf/JetBrainsMono-Regular.ttf",
        assets / "JetBrainsMono-Regular.ttf",
    )
    fetch(
        "https://raw.githubusercontent.com/JetBrains/JetBrainsMono/master/fonts/ttf/JetBrainsMono-Bold.ttf",
        assets / "JetBrainsMono-Bold.ttf",
    )
    fetch(
        "https://raw.githubusercontent.com/JulietaUla/Montserrat/master/fonts/ttf/Montserrat-Regular.ttf",
        assets / "Montserrat-Regular.ttf",
    )
    fetch(
        "https://raw.githubusercontent.com/JulietaUla/Montserrat/master/fonts/ttf/Montserrat-Bold.ttf",
        assets / "Montserrat-Bold.ttf",
    )


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    decode_html()
    prepare_fonts()
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
    if "32." not in probe and '"duration": "32' not in probe:
        print("duration warning", probe, flush=True)

    shutil.copyfile(gif, DEST / "demo.gif")
    shutil.copyfile(mp4, DEST / "demo.mp4")

    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = "Matt Van Horn"
    env["GIT_AUTHOR_EMAIL"] = "mvanhorn@users.noreply.github.com"
    env["GIT_COMMITTER_NAME"] = "Matt Van Horn"
    env["GIT_COMMITTER_EMAIL"] = "mvanhorn@users.noreply.github.com"
    env["GIT_EDITOR"] = "true"

    def run_env(cmd):
        print("+", " ".join(cmd), flush=True)
        subprocess.check_call(cmd, env=env)

    run_env(["git", "config", "user.name", "Matt Van Horn"])
    run_env(["git", "config", "user.email", "mvanhorn@users.noreply.github.com"])
    run_env(["git", "add", "ladybug/list-has-any/demo.gif", "ladybug/list-has-any/demo.mp4"])
    run_env(["git", "commit", "-m", "Add Ladybug list_has_any walkthrough GIF and MP4"])
    subprocess.call(["git", "rm", "-rf", "--ignore-unmatch", str(ROOT)])
    subprocess.call(
        ["git", "rm", "-f", "--ignore-unmatch", ".github/workflows/ingest-ladybug-list-has-any.yml"]
    )
    run_env(["git", "commit", "-m", "Remove ladybug list-has-any ingest scaffolding"])

    last = None
    for i in range(1, 9):
        try:
            run_env(["git", "fetch", "origin", "main"])
            run_env(["git", "pull", "--rebase", "origin", "main"])
            run_env(["git", "push", "origin", "HEAD:main"])
            return
        except subprocess.CalledProcessError as exc:
            last = exc
            subprocess.call(["git", "rebase", "--abort"])
            subprocess.call(["git", "merge", "--abort"])
            time.sleep(i * 3)
    raise SystemExit("push failed: %s" % last)


if __name__ == "__main__":
    main()
