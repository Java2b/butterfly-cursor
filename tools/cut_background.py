# Turns pictures with a plain light background (JPG stickers etc.) into transparent PNGs
# that the program can load from the "creatures" folder.
# Usage: python tools/cut_background.py creatures            (all .jpg/.jpeg/.webp/.bmp in the folder)
#        python tools/cut_background.py picture.jpg [tolerance]
import os
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi


def cut(path, tol=None):
    rgb = np.asarray(Image.open(path).convert("RGB")).astype(np.int16)
    h, w, _ = rgb.shape
    border = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
    bg = np.median(border, axis=0)
    if tol is None:
        # a white sticker outline on an off-white page needs a tight tolerance
        tol = 7 if bg.max() < 250 else 14
    diff = np.abs(rgb - bg).max(axis=2)
    similar = diff <= tol

    # background = pixels like the page colour that are connected to the picture's edge
    labels, _ = ndi.label(similar)
    edge = np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]]))
    outside = np.isin(labels, edge[edge > 0])

    inside = ndi.binary_opening(~outside, structure=np.ones((3, 3), bool))
    lab, n = ndi.label(inside)
    if n > 1:                                   # drop JPEG specks, keep real parts
        sizes = ndi.sum(inside, lab, range(1, n + 1))
        inside = np.isin(lab, 1 + np.nonzero(sizes >= sizes.max() * 0.01)[0])
    alpha = ndi.gaussian_filter(inside.astype(np.float32), 0.8)

    ys, xs = np.nonzero(inside)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    rgba = np.dstack([rgb, alpha * 255]).astype(np.uint8)[y0:y1, x0:x1]
    side = max(x1 - x0, y1 - y0) + 8
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(Image.fromarray(rgba, "RGBA"), ((side - (x1 - x0)) // 2, (side - (y1 - y0)) // 2))
    if side > 400:
        canvas = canvas.resize((400, 400), Image.LANCZOS)
    out = os.path.splitext(path)[0] + ".png"
    canvas.save(out)
    print("saved", out, "background", bg.astype(int).tolist(), "tolerance", tol)


target = sys.argv[1]
tol = int(sys.argv[2]) if len(sys.argv) > 2 else None
if os.path.isdir(target):
    for name in sorted(os.listdir(target)):
        if name.lower().endswith((".jpg", ".jpeg", ".webp", ".bmp")):
            cut(os.path.join(target, name), tol)
else:
    cut(target, tol)
