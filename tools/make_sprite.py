# Cuts the butterfly out of its dark background and writes src/butterfly.png (RGBA).
# Usage: python tools/make_sprite.py "picture.png"
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

src = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else "src/butterfly.png"
SIZE = 320

rgb = np.asarray(Image.open(src).convert("RGB")).astype(np.float32)
lum = rgb.max(axis=2)

# Solid part: bright wing cells, closed over the black veins/borders, holes filled.
yy, xx = np.ogrid[-14:15, -14:15]
disk = (xx * xx + yy * yy) <= 14 * 14
bright = lum > 70
solid = ndi.binary_fill_holes(ndi.binary_closing(np.pad(bright, 20), structure=disk))[20:-20, 20:-20]
solid = ndi.binary_opening(solid, structure=np.ones((3, 3), bool))
labels, n = ndi.label(solid)
if n > 1:
    sizes = ndi.sum(solid, labels, range(1, n + 1))
    solid = labels == (1 + int(np.argmax(sizes)))
solid_a = ndi.gaussian_filter(solid.astype(np.float32), 1.2)

# Everything else keeps only its glow: brightness becomes alpha.
glow_a = np.clip((lum - 22.0) / 110.0, 0.0, 1.0) ** 1.2
alpha = np.maximum(solid_a, glow_a * (1.0 - solid_a))

scale = 255.0 / np.maximum(lum, 1.0)
glow_rgb = np.clip(rgb * scale[..., None], 0, 255)
color = rgb * solid_a[..., None] + glow_rgb * (1.0 - solid_a[..., None])

rgba = np.dstack([color, alpha * 255.0]).clip(0, 255).astype(np.uint8)

# Square crop centred on the body axis so the wings can be folded around it.
ys, xs = np.where(alpha > 0.03)
col = solid.sum(axis=0).astype(np.float64)
axis_x = int(round((col * np.arange(col.size)).sum() / col.sum()))
half = max(axis_x - xs.min(), xs.max() - axis_x, (ys.max() - ys.min()) // 2 + 1) + 4
cy = (ys.min() + ys.max()) // 2
img = Image.fromarray(rgba, "RGBA")
canvas = Image.new("RGBA", (2 * half, 2 * half), (0, 0, 0, 0))
canvas.paste(img, (half - axis_x, half - cy))
canvas = canvas.resize((SIZE, SIZE), Image.LANCZOS)
canvas.save(out)
print("saved", out, "axis", axis_x, "half", half)
