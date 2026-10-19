# Packs the macOS / Linux version into a single program with PyInstaller.
#   macOS: dist/Butterfly Cursor.app (runs without a Dock icon, lives in the menu bar)
#   Linux: dist/butterfly-cursor (one file)
# Usage: python cross/build.py   (needs: pip install pyside6-essentials pyinstaller)
import glob, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(HERE, "assets")

# the creature pictures come from the Windows version
shutil.rmtree(ASSETS, ignore_errors=True)
os.makedirs(ASSETS)
for f in glob.glob(os.path.join(ROOT, "src", "*.png")):
    shutil.copy(f, ASSETS)

mac = sys.platform == "darwin"
name = "Butterfly Cursor" if mac else "butterfly-cursor"
args = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--windowed", "--name", name,
        "--add-data", ASSETS + os.pathsep + "assets",
        "--exclude-module", "tkinter", "--distpath", os.path.join(HERE, "dist"), "--workpath", os.path.join(HERE, "build")]
if mac:
    args += ["--osx-bundle-identifier", "com.jb.butterflycursor"]
else:
    args += ["--onefile"]
args.append(os.path.join(HERE, "butterfly_cursor.py"))
subprocess.check_call(args)

if mac:
    # no Dock icon: the program lives only in the menu bar
    plist = os.path.join(HERE, "dist", name + ".app", "Contents", "Info.plist")
    subprocess.call(["plutil", "-insert", "LSUIElement", "-bool", "true", plist])
print("done:", os.listdir(os.path.join(HERE, "dist")))
