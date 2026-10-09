from pathlib import Path
import hashlib, subprocess, sys

p = Path("_render/at_mcp-suggested-feeds")
b64 = "".join((p / "index.html.gz.b64").read_text().split())
assert hashlib.sha256(b64.encode()).hexdigest() == "13cf6ef4707fd7f8b386a94083a0bc699602a89aa7c16520f31cdd43bf19ca80"
text = (p / "ingest.py").read_text()
assert hashlib.sha256(text.encode()).hexdigest() == "2b375dd00c741713e08373e16f6c7eafecbd7dbde414051de2acb30eaf20b311"
raise SystemExit(subprocess.call([sys.executable, str(p / "ingest.py")]))
