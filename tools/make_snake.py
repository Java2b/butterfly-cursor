# Draws the snake seen from above (a green python with dark saddle markings), head pointing up.
# The program turns the picture towards where it crawls.
# Strip of 11 square frames: 0-7 slithering (an S-wave runs from the head to the tail, the tongue flicks),
# 8-10 resting: coiled up, head on top of the coil, tongue in / out / in.
# Drawn at 1024 px and scaled down to 320 px for smooth edges.
# Usage: python tools/make_snake.py
import math
from PIL import Image, ImageDraw, ImageFilter

N, OUT = 1024, 320
OUTLINE = (14, 30, 14)
SKIN = (84, 150, 60)
SKIN_D = (52, 104, 40)
SKIN_L = (150, 205, 96)
SADDLE = (30, 62, 26)
SADDLE_EDGE = (178, 176, 96)
EYE = (240, 200, 60)
PUPIL = (12, 12, 12)
TONGUE = (220, 40, 64)
GLOW = (120, 230, 110)
FRAMES = 8


def width_at(s):
    """Body width along the snake, s = 0 at the head .. 1 at the tail tip."""
    if s < 0.06:
        return 62 + 30 * (s / 0.06)          # neck widens behind the head
    if s < 0.45:
        return 92
    return 92 * max(0.08, 1 - (s - 0.45) / 0.55) ** 0.9


def tube(img, pts, ws):
    """Draws a shaded tube through the points: outline, dark sides, body, a light ridge, markings."""
    d = ImageDraw.Draw(img)
    for extra, col in ((14, OUTLINE), (0, SKIN_D)):
        for (x, y), w in zip(pts, ws):
            r = (w + extra) / 2
            d.ellipse((x - r, y - r, x + r, y + r), fill=col)
    for (x, y), w in zip(pts, ws):
        r = w * 0.36
        d.ellipse((x - r, y - r, x + r, y + r), fill=SKIN)
    # blotches along the back, staggered left and right like a python's pattern
    step = max(8, len(pts) // 24)
    for n, k in enumerate(range(step, len(pts) - 4, step)):
        (x0, y0), (x1, y1) = pts[k - 1], pts[k + 1]
        ang = math.atan2(y1 - y0, x1 - x0)
        nx, ny = -math.sin(ang), math.cos(ang)
        w = ws[k]
        if w < 22:
            continue
        off = (0.14 if n % 2 else -0.14) * w
        cx, cy, r = pts[k][0] + nx * off, pts[k][1] + ny * off, w * 0.24
        d.ellipse((cx - r - 3, cy - r - 3, cx + r + 3, cy + r + 3), fill=SADDLE_EDGE)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=SADDLE)
    for (x, y), w in zip(pts, ws):                       # light ridge along the spine
        r = w * 0.09
        d.ellipse((x - r - w * 0.08, y - r - w * 0.08, x + r - w * 0.08, y + r - w * 0.08), fill=SKIN_L)


def head(img, x, y, ang, tongue, scale=1.0):
    """Head at (x, y) pointing along ang (radians, 0 = up)."""
    hd = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(hd)
    cx, cy, s = N / 2, N / 2, scale
    if tongue:
        d.line([(cx, cy - 70 * s), (cx, cy - 128 * s)], fill=TONGUE, width=int(8 * s))
        d.line([(cx, cy - 126 * s), (cx - 14 * s, cy - 150 * s)], fill=TONGUE, width=int(7 * s))
        d.line([(cx, cy - 126 * s), (cx + 14 * s, cy - 150 * s)], fill=TONGUE, width=int(7 * s))
    d.ellipse((cx - 58 * s, cy - 82 * s, cx + 58 * s, cy + 52 * s), fill=OUTLINE)
    d.ellipse((cx - 51 * s, cy - 75 * s, cx + 51 * s, cy + 45 * s), fill=SKIN_D)
    d.ellipse((cx - 38 * s, cy - 70 * s, cx + 38 * s, cy + 36 * s), fill=SKIN)
    d.polygon([(cx - 18 * s, cy - 10 * s), (cx + 18 * s, cy - 10 * s), (cx, cy + 40 * s)], fill=SADDLE)   # marking
    d.ellipse((cx - 10 * s, cy - 62 * s, cx + 10 * s, cy - 40 * s), fill=SKIN_L)
    for sx in (-1, 1):                                                               # eyes on the sides
        ex = cx + sx * 40 * s
        d.ellipse((ex - 14 * s, cy - 44 * s, ex + 14 * s, cy - 16 * s), fill=OUTLINE)
        d.ellipse((ex - 10 * s, cy - 40 * s, ex + 10 * s, cy - 20 * s), fill=EYE)
        d.ellipse((ex - 3 * s, cy - 39 * s, ex + 3 * s, cy - 21 * s), fill=PUPIL)
        d.ellipse((cx + sx * 12 * s - 4 * s, cy - 76 * s, cx + sx * 12 * s + 4 * s, cy - 68 * s), fill=OUTLINE)  # nostrils
    hd = hd.rotate(-math.degrees(ang), resample=Image.BICUBIC, center=(cx, cy))
    img.alpha_composite(hd, (int(x - cx), int(y - cy)))


def finish(img):
    small = img.resize((OUT, OUT), Image.LANCZOS)
    a = small.split()[3]
    halo = a.filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.45))
    out = Image.merge("RGBA", [Image.new("L", (OUT, OUT), c) for c in GLOW] + [halo])
    out.alpha_composite(small)
    return out


def slither(i):
    ph = i / FRAMES * 2 * math.pi
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    count = 500
    length = 760.0
    pts, ws = [], []
    for k in range(count):
        s = k / (count - 1)
        y = 215 + s * length
        amp = 30 + 120 * min(1.0, s * 1.6)          # small near the head, wide along the body
        x = N / 2 + amp * math.sin(s * 2 * math.pi * 1.25 - ph) - 30 * math.sin(-ph)
        pts.append((x, y))
        ws.append(width_at(s))
    pts.reverse(); ws.reverse()                       # tail first, so the front is drawn on top
    tube(img, pts, ws)
    hx, hy = pts[-1]
    px_, py_ = pts[-6]
    ang = math.atan2(hx - px_, -(hy - py_))
    head(img, hx + math.sin(ang) * 30, hy - math.cos(ang) * 30, ang, tongue=i in (2, 3, 6))
    return finish(img)


def coiled(tongue):
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    count = 700
    pts, ws = [], []
    for k in range(count):
        s = k / (count - 1)                           # 0 = tail tip (outside) .. 1 = neck (inside)
        a = 0.6 + s * 2 * math.pi * 1.75
        r = 320 - 230 * s
        pts.append((N / 2 + r * math.cos(a), N / 2 + 40 + r * math.sin(a) * 0.86))
        ws.append(width_at(1 - s) if s < 0.94 else 92)
    tube(img, pts, ws)
    # neck rising from the middle of the coil, head looking up
    head(img, N / 2 + 10, N / 2 - 40, -0.15, tongue, scale=1.12)
    return finish(img)


def main():
    frames = [slither(i) for i in range(FRAMES)] + [coiled(False), coiled(True), coiled(False)]
    strip = Image.new("RGBA", (OUT * len(frames), OUT), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        strip.paste(f, (i * OUT, 0))
    strip.save("src/snake.png")
    print("src/snake.png", strip.size)


if __name__ == "__main__":
    main()
