from pathlib import Path
import hashlib, subprocess, sys
p = Path("_render/diagram-design-plantuml-import")
html = "".join("".join((p / f"html.b64.{i}").read_text().split()) for i in range(10))
assert len(html) == 8840, len(html)
assert hashlib.sha256(html.encode()).hexdigest() == "d2e378d6d6c607838c6b2a1730b82d6d0d7f7734fed257aa549847109097fa3c"
(p / "index.html.gz.b64").write_text(html)
text = "".join((p / f"ingest.py.part{i}").read_text() for i in range(7))
assert hashlib.sha256(text.encode()).hexdigest() == "d84b2b1468ce5f154d01191d492f785e46f8a1a8f9a86bee210356635c9eb7a2"
(p / "ingest.py").write_text(text)
raise SystemExit(subprocess.call([sys.executable, str(p / "ingest.py")]))
