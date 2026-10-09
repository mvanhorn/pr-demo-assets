#!/usr/bin/env python3
from pathlib import Path
import base64, gzip, hashlib, os, shutil, subprocess, sys, time

ROOT = Path("_render/at_mcp-suggested-feeds")
DEST = Path("at_mcp/suggested-feeds")
EXPECTED_HTML = "7a7ddf040292b0550bcac11f2c4268670057e3dcb6f7d81d08979c161f538c91"
HF = "hyperframes@0.8.143"


def run(cmd, cwd=None):
    print("+", " ".join(cmd), flush=True)
    subprocess.check_call(cmd, cwd=str(cwd) if cwd else None)


def decode_html():
    raw = "".join((ROOT / "index.html.gz.b64").read_text().split())
    raw += "=" * ((4 - len(raw) % 4) % 4)
    html = gzip.decompress(base64.b64decode(raw))
    digest = hashlib.sha256(html).hexdigest()
    assert digest == EXPECTED_HTML, digest
    (ROOT / "index.html").write_bytes(html)
    print("html", len(html), digest, flush=True)


def probe(path, key):
    out = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            f"stream={key}",
            "-of",
            "default=nw=1:nk=1",
            str(path),
        ],
        text=True,
    ).strip()
    return out


def duration(path):
    out = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            str(path),
        ],
        text=True,
    ).strip()
    return float(out)


def main():
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

    gif = ROOT / "preview.gif"
    mp4 = ROOT / "out.mp4"
    assert mp4.is_file() and mp4.stat().st_size > 0
    assert gif.is_file() and gif.stat().st_size > 0
    assert gif.stat().st_size < 8_000_000, gif.stat().st_size
    assert probe(mp4, "width") == "1920", probe(mp4, "width")
    assert probe(mp4, "height") == "1080", probe(mp4, "height")
    assert probe(gif, "width") == "720", probe(gif, "width")
    d_mp4 = duration(mp4)
    d_gif = duration(gif)
    assert 30.0 <= d_mp4 <= 40.5, d_mp4
    assert 30.0 <= d_gif <= 40.5, d_gif
    print("mp4", mp4.stat().st_size, d_mp4, flush=True)
    print("gif", gif.stat().st_size, d_gif, flush=True)

    DEST.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(gif, DEST / "demo.gif")
    shutil.copyfile(mp4, DEST / "demo.mp4")

    env = dict(os.environ)
    env["GIT_AUTHOR_NAME"] = "Matt Van Horn"
    env["GIT_AUTHOR_EMAIL"] = "mvanhorn@users.noreply.github.com"
    env["GIT_COMMITTER_NAME"] = "Matt Van Horn"
    env["GIT_COMMITTER_EMAIL"] = "mvanhorn@users.noreply.github.com"

    def git(args):
        subprocess.check_call(args, env=env)

    git(["git", "config", "user.name", "Matt Van Horn"])
    git(["git", "config", "user.email", "mvanhorn@users.noreply.github.com"])
    subprocess.call(["git", "rm", "-rf", "--ignore-unmatch", str(ROOT)], env=env)
    subprocess.call(
        ["git", "rm", "-f", ".github/workflows/ingest-at-mcp-suggested-feeds.yml"],
        env=env,
    )
    git(["git", "add", "at_mcp/suggested-feeds/demo.gif", "at_mcp/suggested-feeds/demo.mp4"])
    git(
        [
            "git",
            "commit",
            "-m",
            "Add at_mcp suggested-feeds walkthrough GIF and MP4\n\nSilent 40s HyperFrames demo of get_suggested_feeds then get_feed.",
        ]
    )
    last = None
    for i in range(1, 7):
        try:
            git(["git", "pull", "--rebase", "origin", "main"])
            git(["git", "push", "origin", "HEAD:main"])
            return
        except subprocess.CalledProcessError as e:
            last = e
            subprocess.call(["git", "rebase", "--abort"], env=env)
            time.sleep(i * 3)
    raise last


if __name__ == "__main__":
    main()
