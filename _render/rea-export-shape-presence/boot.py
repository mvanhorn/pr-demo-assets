from pathlib import Path
import hashlib, subprocess, sys
p = Path("_render/rea-export-shape-presence")
html = "".join("".join((p / f"html.b64.{i}").read_text().split()) for i in range(5))
assert len(html) == 4440, len(html)
assert hashlib.sha256(html.encode()).hexdigest() == "ea575c91d8efe5b449b08cb64e7391c42448799e08c78f46a7912c8ce5e522df"
(p / "index.html.gz.b64").write_text(html)
text = "".join((p / f"ingest.py.part{i}").read_text() for i in range(6))
assert hashlib.sha256(text.encode()).hexdigest() == "4efab4574fe11af0e9ef2eb78491b5a08c0ac0f62d05932ce700ca7189b6c091"
(p / "ingest.py").write_text(text)
raise SystemExit(subprocess.call([sys.executable, str(p / "ingest.py")]))
