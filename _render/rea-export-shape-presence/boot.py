from pathlib import Path
import base64, gzip, subprocess, sys
p = Path("_render/rea-export-shape-presence")
raw = "".join((p / "ingest.py.gz.b64").read_text().split())
raw += "=" * ((4 - len(raw) % 4) % 4)
(p / "ingest.py").write_bytes(gzip.decompress(base64.b64decode(raw)))
raise SystemExit(subprocess.call([sys.executable, str(p / "ingest.py")]))
