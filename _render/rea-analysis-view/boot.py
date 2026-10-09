from pathlib import Path
import hashlib, subprocess, sys
p = Path("_render/rea-analysis-view")
html = "".join("".join((p / f"html.b64.{i}").read_text().split()) for i in range(7))
assert len(html) == 5832, len(html)
assert hashlib.sha256(html.encode()).hexdigest() == "f78f4440c683f3bae51b5cb06dbfe22e403c08e5e7582b18e8f54d5d2b743ef4"
(p / "index.html.gz.b64").write_text(html)
text = "".join((p / f"ingest.py.part{i}").read_text() for i in range(6))
assert hashlib.sha256(text.encode()).hexdigest() == "c681646ddc189e95f840c64aed86b3299c8ec0959827c88c3dd8dfebb1d3999b"
(p / "ingest.py").write_text(text)
raise SystemExit(subprocess.call([sys.executable, str(p / "ingest.py")]))
