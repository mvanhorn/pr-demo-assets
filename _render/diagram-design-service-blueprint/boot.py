from pathlib import Path
import hashlib, subprocess, sys
p = Path("_render/diagram-design-service-blueprint")
html = "".join("".join((p / f"html.b64.{i}").read_text().split()) for i in range(10))
assert len(html) == 8940, len(html)
assert hashlib.sha256(html.encode()).hexdigest() == "81f83e9dc0875d91e1454ca0ec1d26fd3f2b579fd7346c623f4e53e9744bbf84"
(p / "index.html.gz.b64").write_text(html)
text = "".join((p / f"ingest.py.part{i}").read_text() for i in range(6))
assert hashlib.sha256(text.encode()).hexdigest() == "58a2b70f7aabafa342c0a3654797271046e7fbe93b7f80f12e36b6d248af3aad"
(p / "ingest.py").write_text(text)
raise SystemExit(subprocess.call([sys.executable, str(p / "ingest.py")]))
