# Builds src/flags.png (one atlas with every country flag) and src/flags.txt (code|name per cell)
# from the flag-icons SVG pack (https://github.com/lipis/flag-icons, MIT licence).
# The SVGs are rendered by headless Chrome/Edge, so no SVG library is needed.
# Usage: python tools/make_flags.py <path to unzipped flag-icons-main>
import json
import os
import subprocess
import sys
import tempfile

W, H, COLS = 128, 96, 16
src = os.path.abspath(sys.argv[1])
countries = sorted(json.load(open(os.path.join(src, "country.json"), encoding="utf-8")), key=lambda c: c["name"])
rows = (len(countries) + COLS - 1) // COLS

cells = "".join('<img src="file:///%s">' % os.path.join(src, "flags", "4x3", c["code"] + ".svg").replace("\\", "/")
                for c in countries)
html = """<!doctype html><html><head><style>
html,body{margin:0;padding:0;background:transparent}
body{width:%dpx;display:flex;flex-wrap:wrap}
img{width:%dpx;height:%dpx;display:block}
</style></head><body>%s</body></html>""" % (W * COLS, W, H, cells)

tmp = tempfile.mkdtemp()
page = os.path.join(tmp, "atlas.html")
open(page, "w", encoding="utf-8").write(html)

browsers = [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"]
browser = next(b for b in browsers if os.path.exists(b))
out = os.path.abspath("src/flags.png")
subprocess.run([browser, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                "--default-background-color=00000000", "--allow-file-access-from-files",
                "--window-size=%d,%d" % (W * COLS, H * rows), "--screenshot=" + out, "file:///" + page.replace("\\", "/")],
               check=True, timeout=120)

with open("src/flags.txt", "w", encoding="utf-8") as f:
    for c in countries:
        f.write("%s|%s\n" % (c["code"], c["name"]))
print("saved", out, "and src/flags.txt with", len(countries), "flags")
