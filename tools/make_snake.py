# Draws the original pixel-art snake (a green python with dark blotches) on a 40x40 grid, scaled 8x.
# Strip of 9 square frames: 0-5 slithering (a wave runs along the body, the tongue flicks),
# 6-8 resting: the head raised high, tongue in / out / in.
# Usage: python tools/make_snake.py
import math
from PIL import Image, ImageDraw, ImageFilter

G, SCALE = 40, 8
OUT = G * SCALE
OUTLINE = (12, 20, 10, 255)
SKIN = (78, 140, 56, 255)
SKIN_L = (130, 190, 80, 255)
SKIN_D = (44, 88, 34, 255)
BLOTCH = (34, 62, 26, 255)
BELLY = (214, 200, 128, 255)
BELLY_D = (170, 150, 90, 255)
EYE = (250, 210, 60, 255)
PUPIL = (10, 10, 10, 255)
TONGUE = (220, 40, 60, 255)
GLOW = (120, 230, 110)


def outline(img):
    src = img.load()
    out = img.copy()
    o = out.load()
    for y in range(G):
        for x in range(G):
            if src[x, y][3] or src[x, y] == TONGUE:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < G and 0 <= ny < G and src[nx, ny][3] and src[nx, ny] != TONGUE:
                    o[x, y] = OUTLINE
                    break
    return out


def finish(img):
    img = outline(img).resize((OUT, OUT), Image.NEAREST)
    a = img.split()[3]
    halo = a.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.4))
    out = Image.merge("RGBA", [Image.new("L", (OUT, OUT), c) for c in GLOW] + [halo])
    out.alpha_composite(img)
    return out


def column(p, x, top, bottom, pattern):
    """One vertical slice of the body: back light, side, blotch, belly."""
    for y in range(top, bottom + 1):
        if y == bottom:
            c = BELLY_D if bottom - top >= 3 else BELLY
        elif y == bottom - 1 and bottom - top >= 3:
            c = BELLY
        elif y == top:
            c = SKIN_L
        else:
            c = BLOTCH if pattern else SKIN
        if 0 <= x < G and 0 <= y < G:
            p[x, y] = c
    if pattern and bottom - top >= 3 and 0 <= x < G:
        p[x, top] = SKIN_D


def head(d, p, hx, hy, tongue, up=False):
    """Head pointing right, its back-left corner at (hx, hy)."""
    d.ellipse((hx, hy, hx + 7, hy + 5), fill=SKIN)
    d.rectangle((hx + 1, hy + 4, hx + 6, hy + 5), fill=BELLY)
    d.line([(hx + 1, hy + 1), (hx + 5, hy)], fill=SKIN_L)
    d.line([(hx + 2, hy + 3), (hx + 7, hy + 3)], fill=SKIN_D)     # mouth line
    p[hx + 5, hy + 1] = EYE
    p[hx + 6, hy + 1] = PUPIL
    p[hx + 1, hy + 2] = BLOTCH                                      # marking behind the eye
    p[hx + 2, hy + 2] = BLOTCH
    if tongue:
        tx, ty = hx + 8, hy + 3
        d.line([(tx, ty), (tx + 2, ty)], fill=TONGUE)
        p[tx + 3, ty - 1] = TONGUE
        p[tx + 3, ty + 1] = TONGUE


def slither(i):
    img = Image.new("RGBA", (G, G), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    p = img.load()
    ph = i / 6 * 2 * math.pi
    ground = 36
    for x in range(1, 28):
        t = (x - 1) / 26.0
        th = int(round(1 + 3.2 * min(1.0, t * 2.2)))        # the tail tapers
        wave = 1.4 * math.sin(x * 0.42 + ph) * (0.4 + 0.6 * t)
        cy = ground - th / 2.0 + wave
        if x >= 23:
            cy -= (x - 23) * 0.9                              # the neck lifts a little
        top = int(round(cy - th / 2.0))
        column(p, x, top, top + th, (x // 3) % 2 == 0 and x > 6)
    head(d, p, 27, int(round(ground - 9 + 1.4 * math.sin(27 * 0.42 + ph) * 0.9)), tongue=i in (1, 2, 4))
    return finish(img)


def raised(tongue):
    img = Image.new("RGBA", (G, G), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    p = img.load()
    ground = 36
    # body lying in a loose S on the ground, then rising into an S-shaped neck
    for x in range(2, 24):
        t = (x - 2) / 21.0
        th = int(round(1 + 3.2 * min(1.0, t * 2.2)))
        cy = ground - th / 2.0 + 0.8 * math.sin(x * 0.5)
        top = int(round(cy - th / 2.0))
        column(p, x, top, top + th, (x // 3) % 2 == 0 and x > 6)
    # neck: a thick curve from (23, 33) up to the head
    pts = []
    for k in range(13):
        s = k / 12.0
        pts.append((23 + 5 * math.sin(s * math.pi * 0.9), 33 - s * 15))
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        d.line([(x0, y0), (x1, y1)], fill=SKIN, width=4)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        d.line([(x0 + 1.5, y0), (x1 + 1.5, y1)], fill=BELLY, width=1)   # pale throat facing forward
    for k in range(1, 12, 3):
        x, y = pts[k]
        d.point((int(x) - 1, int(y)), fill=BLOTCH)
    head(d, p, 25, 14, tongue)
    return finish(img)


def main():
    frames = [slither(i) for i in range(6)] + [raised(False), raised(True), raised(False)]
    strip = Image.new("RGBA", (OUT * len(frames), OUT), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        strip.paste(f, (i * OUT, 0))
    strip.save("src/snake.png")
    print("src/snake.png", strip.size)


if __name__ == "__main__":
    main()
