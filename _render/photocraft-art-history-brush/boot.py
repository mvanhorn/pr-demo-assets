from pathlib import Path
import base64, hashlib, subprocess, sys
p = Path("_render/photocraft-art-history-brush")
html = "".join("".join((p / ("html.b64.%d" % i)).read_text().split()) for i in range(8))
assert len(html) == 7072, len(html)
assert hashlib.sha256(html.encode()).hexdigest() == "51f81525ee492b5b4dc5cbb7e22510168c60ed95c443df27dd6260273e602f76"
(p / "index.html.gz.b64").write_text(html)
py = "".join("".join((p / ("py.b64.%d" % i)).read_text().split()) for i in range(4))
assert len(py) == 3356, len(py)
assert hashlib.sha256(py.encode()).hexdigest() == "489c44b1126f2aace82167c54d69577a0bb192fe04f0a987817b69fb4c7c42e0"
(p / "gen_assets.py.gz.b64").write_text(py)
ing = "".join("".join((p / ("ing.b64.%d" % i)).read_text().split()) for i in range(7))
assert len(ing) == 6164, len(ing)
assert hashlib.sha256(ing.encode()).hexdigest() == "3863f9ee3091e26262585ce078c2ebdd19ba0f8ade45ac1bac80311992d74314"
pad = (4 - len(ing) % 4) % 4
raw = base64.b64decode(ing + "=" * pad)
assert hashlib.sha256(raw).hexdigest() == "b6b256ef246d651605f72a90c7ca8e3e331792b1c009d8171b978424a9a5b758"
(p / "ingest.py").write_bytes(raw)
raise SystemExit(subprocess.call([sys.executable, str(p / "ingest.py")]))
