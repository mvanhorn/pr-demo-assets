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

ROOT = Path("_render/at_mcp-search-posts-filters")
DEST = Path("at_mcp/search-posts-filters")
WORKFLOW = ".github/workflows/ingest-at-mcp-search-posts-filters.yml"
HF = "hyperframes@0.8.143"
MAX_GIF = 8_000_000
HTML_SHA = "f061c1e9eeefbd63daee45d0dbaccf0a5ebecb02ae3786c715d4c98bdd134ac5"

FONT_FACE = """
      @font-face {
        font-family: Inter;
        src: url("assets/Inter-Regular.ttf") format("truetype");
        font-weight: 400 500;
        font-style: normal;
        font-display: block;
      }
      @font-face {
        font-family: Inter;
        src: url("assets/Inter-SemiBold.ttf") format("truetype");
        font-weight: 600 700;
        font-style: normal;
        font-display: block;
      }
      @font-face {
        font-family: "JetBrains Mono";
        src: url("assets/JetBrainsMono-Regular.ttf") format("truetype");
        font-weight: 400 500;
        font-style: normal;
        font-display: block;
      }
      @font-face {
        font-family: "JetBrains Mono";
        src: url("assets/JetBrainsMono-Bold.ttf") format("truetype");
        font-weight: 600 700;
        font-style: normal;
        font-display: block;
      }
"""

HYPERFRAMES_JSON = """{
  "$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
  "registry": "https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry",
  "paths": {
    "blocks": "compositions",
    "components": "compositions/components",
    "assets": "assets"
  },
  "media": { "autoProxy": true }
}
"""

PACKAGE_JSON = """{
  "name": "at-mcp-search-posts-filters",
  "private": true,
  "type": "module"
}
"""


def run(cmd, cwd=None):
    print("+", " ".join(cmd), flush=True)
    subprocess.check_call(cmd, cwd=str(cwd) if cwd else None)


def fetch(url, dest):
    print("fetch", url, "->", dest, flush=True)
    req = urllib.request.Request(url, headers={"User-Agent": "at-mcp-demo-ingest"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        dest.write_bytes(resp.read())
    if dest.stat().st_size < 1000:
        raise SystemExit("tiny download %s (%s bytes)" % (dest, dest.stat().st_size))


def write_html():
    b64_path = ROOT / "index.html.gz.b64"
    if b64_path.is_file():
        b64 = "".join(b64_path.read_text().split())
    else:
        b64 = "".join((ROOT / "html.b64").read_text().split())
    b64 += "=" * ((4 - len(b64) % 4) % 4)
    html = gzip.decompress(base64.b64decode(b64))
    digest = hashlib.sha256(html).hexdigest()
    if digest != HTML_SHA:
        raise SystemExit("html sha256 %s != %s" % (digest, HTML_SHA))
    needle = b"      * { margin: 0; padding: 0; box-sizing: border-box; }"
    if needle in html and b"Inter-Regular.ttf" not in html:
        html = html.replace(needle, FONT_FACE.encode() + needle, 1)
    (ROOT / "index.html").write_bytes(html)
    (ROOT / "hyperframes.json").write_text(HYPERFRAMES_JSON)
    (ROOT / "package.json").write_text(PACKAGE_JSON)
    (ROOT / "compositions").mkdir(parents=True, exist_ok=True)
    (ROOT / "compositions" / ".gitkeep").write_text("")
    print("html", len(html), digest, flush=True)


def prepare_fonts():
    assets = ROOT / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    fetch(
        "https://cdn.jsdelivr.net/fontsource/fonts/inter@5.2.5/latin-400-normal.ttf",
        assets / "Inter-Regular.ttf",
    )
    fetch(
        "https://cdn.jsdelivr.net/fontsource/fonts/inter@5.2.5/latin-600-normal.ttf",
        assets / "Inter-SemiBold.ttf",
    )
    fetch(
        "https://cdn.jsdelivr.net/fontsource/fonts/jetbrains-mono@5.2.5/latin-400-normal.ttf",
        assets / "JetBrainsMono-Regular.ttf",
    )
    fetch(
        "https://cdn.jsdelivr.net/fontsource/fonts/jetbrains-mono@5.2.5/latin-700-normal.ttf",
        assets / "JetBrainsMono-Bold.ttf",
    )


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    write_html()
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
            "fps=12,scale=720:-2:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128:stats_mode=diff[p];[s1][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle",
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
    if "40." not in probe and '"duration": "40' not in probe:
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
    subprocess.call(
        ["git", "rm", "-f", "--ignore-unmatch", "at_mcp/search-posts-filters/.ingest-probe"]
    )
    run_env(["git", "add", str(DEST / "demo.gif"), str(DEST / "demo.mp4")])
    run_env(
        [
            "git",
            "commit",
            "-m",
            "Add at_mcp search_posts filters walkthrough demo\n\n"
            "GIF and MP4 for optional author, mentions, sort, since, until and lang\n"
            "on search_posts.",
        ]
    )
    subprocess.call(["git", "rm", "-rf", "--ignore-unmatch", str(ROOT)])
    subprocess.call(["git", "rm", "-f", "--ignore-unmatch", WORKFLOW])
    run_env(["git", "commit", "-m", "Remove at_mcp search_posts filters ingest scaffolding"])

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
