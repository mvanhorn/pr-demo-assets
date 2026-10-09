from pathlib import Path
import hashlib, subprocess, sys
p = Path("_render/rea-export-shape-presence")
text = "".join((p / f"ingest.py.part{i}").read_text() for i in range(6))
assert hashlib.sha256(text.encode()).hexdigest() == "4efab4574fe11af0e9ef2eb78491b5a08c0ac0f62d05932ce700ca7189b6c091"
(p / "ingest.py").write_text(text)
raise SystemExit(subprocess.call([sys.executable, str(p / "ingest.py")]))
