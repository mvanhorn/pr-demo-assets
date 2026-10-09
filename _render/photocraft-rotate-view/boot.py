from pathlib import Path
import hashlib, subprocess, sys
p = Path("_render/photocraft-rotate-view")
html = "".join((p / "index.html.gz.b64").read_text().split())
assert len(html) == 8380, len(html)
assert hashlib.sha256(html.encode()).hexdigest() == "76e1b2b3a26bfb02c31b221ed64e863880c18794d21371e28a6147e63aca6d74"
text = (p / "ingest.py").read_text()
assert hashlib.sha256(text.encode()).hexdigest() == "676e4212b8e2dde5b7aff3521107e7d2d49499d3a5560953427949f17fe95c5e"
raise SystemExit(subprocess.call([sys.executable, str(p / "ingest.py")]))
