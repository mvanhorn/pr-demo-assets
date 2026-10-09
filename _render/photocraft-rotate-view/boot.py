from pathlib import Path
import hashlib, subprocess, sys
p = Path("_render/photocraft-rotate-view")
html = "".join((p / "index.html.gz.b64").read_text().split())
assert len(html) == 8380, len(html)
assert hashlib.sha256(html.encode()).hexdigest() == "76e1b2b3a26bfb02c31b221ed64e863880c18794d21371e28a6147e63aca6d74"
text = (p / "ingest.py").read_text()
assert hashlib.sha256(text.encode()).hexdigest() == "1c3ef9c90c55127881d06e4178b8c2a07f2d3ef3a76b3ee7b91f09235556d2af"
raise SystemExit(subprocess.call([sys.executable, str(p / "ingest.py")]))
