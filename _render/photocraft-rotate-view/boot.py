from pathlib import Path
import base64
import hashlib
import subprocess
import sys

p = Path("_render/photocraft-rotate-view")

html = "".join("".join((p / ("html.b64.%d" % i)).read_text().split()) for i in range(10))
assert len(html) == 8672, len(html)
assert hashlib.sha256(html.encode()).hexdigest() == "fedced47e92b23e462755e6201657d1d920d3150a2100415b75c1ed708ae0ae5"
(p / "index.html.gz.b64").write_text(html)

py = "".join("".join((p / ("py.b64.%d" % i)).read_text().split()) for i in range(2))
assert len(py) == 1092, len(py)
assert hashlib.sha256(py.encode()).hexdigest() == "a36c49bf2c8c76fd634b438cc9bbe244293e52c7a382aba18c49e502f78c0382"
(p / "gen_assets.py.gz.b64").write_text(py)

ing = "".join("".join((p / ("ing.b64.%d" % i)).read_text().split()) for i in range(11))
assert len(ing) == 9388, len(ing)
assert hashlib.sha256(ing.encode()).hexdigest() == "93a71cc08c5553b0baa4ee53df8ada3f83d785f849df9185bceae7123214213b"
pad = (4 - len(ing) % 4) % 4
raw = base64.b64decode(ing + "=" * pad)
assert hashlib.sha256(raw).hexdigest() == "65ee8832c955c70a965d212b8659765c45c63ebee9551c29989652e523f56a13"
(p / "ingest.py").write_bytes(raw)
raise SystemExit(subprocess.call([sys.executable, str(p / "ingest.py")]))
