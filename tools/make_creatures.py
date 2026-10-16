# Draws the built-in glowing creatures (beetle, spider, snail) as 320x320 RGBA sprites.
# Beetle and spider are seen from above with the head pointing up; the snail is a side view facing right.
# Usage: python tools/make_creatures.py
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

N = 1280          # supersampled canvas
OUT = 320
DARK = (6, 14, 30)


class Canvas:
    def __init__(self):
        self.img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
        yy, xx = np.mgrid[0:N, 0:N]
        self.xx, self.yy = xx.astype(np.float32), yy.astype(np.float32)

    def part(self, draw_fn, inner, outer, center=None, radius=None, outline=12, mirror=False):
        """Draws a shape with a dark outline and a radial gradient fill."""
        mask = Image.new("L", (N, N), 0)
        draw_fn(ImageDraw.Draw(mask))
        if mirror:
            mask = Image.fromarray(np.maximum(np.asarray(mask), np.asarray(mask)[:, ::-1]))
        if outline:
            fat = mask.filter(ImageFilter.GaussianBlur(outline)).point(lambda v: 255 if v > 30 else 0)
            fat = fat.filter(ImageFilter.GaussianBlur(1.5))
            self.img.paste(Image.new("RGBA", (N, N), DARK + (255,)), (0, 0), fat)
        m = np.asarray(mask)
        ys, xs = np.nonzero(m)
        if center is None:
            center = (xs.mean(), ys.mean())
        if radius is None:
            radius = max(xs.max() - xs.min(), ys.max() - ys.min()) / 2.0
        d = np.sqrt((self.xx - center[0]) ** 2 + (self.yy - center[1]) ** 2) / radius
        t = np.clip(d, 0, 1)[..., None]
        rgb = np.array(inner, np.float32) * (1 - t) + np.array(outer, np.float32) * t
        layer = Image.fromarray(np.dstack([rgb, m[..., None]]).astype(np.uint8), "RGBA")
        soft = mask.filter(ImageFilter.GaussianBlur(1.5))
        self.img.paste(layer, (0, 0), soft)

    def shine(self, box, alpha=90):
        layer = Image.new("RGBA", (N, N), (0, 0, 0, 0))
        ImageDraw.Draw(layer).ellipse(box, fill=(255, 255, 255, alpha))
        self.img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(14)))

    def save(self, path, glow):
        a = self.img.split()[3]
        out = Image.new("RGBA", (N, N), (0, 0, 0, 0))
        for radius, strength in ((46, 0.55), (16, 0.75)):
            halo = a.filter(ImageFilter.GaussianBlur(radius)).point(lambda v: int(min(255, v * strength)))
            out.alpha_composite(Image.merge("RGBA", [Image.new("L", (N, N), c) for c in glow] + [halo]))
        out.alpha_composite(self.img)
        out.resize((OUT, OUT), Image.LANCZOS).save(path)
        print("saved", path)


def poly(points, width):
    def fn(d):
        d.line(points, fill=255, width=width, joint="curve")
        r = width / 2
        for x, y in points:
            d.ellipse((x - r, y - r, x + r, y + r), fill=255)
    return fn


def ell(cx, cy, rx, ry):
    return lambda d: d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=255)


def beetle():
    c = Canvas()
    leg_in, leg_out = (150, 255, 210), (30, 190, 150)
    for pts in ([(560, 480), (400, 400), (350, 270)],
                [(520, 660), (320, 650), (230, 770)],
                [(540, 880), (370, 980), (330, 1120)]):
        c.part(poly(pts, 26), leg_in, leg_out, mirror=True, outline=9)
    c.part(poly([(600, 290), (530, 180), (440, 150)], 14), leg_in, leg_out, mirror=True, outline=8)
    c.part(ell(640, 320, 105, 90), (40, 150, 150), (8, 50, 70))
    c.part(ell(640, 470, 215, 130), (90, 240, 190), (0, 110, 110), center=(600, 430))
    c.part(ell(640, 800, 275, 345), (150, 255, 200), (0, 130, 120), center=(560, 680), radius=480)
    c.part(lambda d: d.line([(640, 560), (640, 1140)], fill=255, width=9), DARK, DARK, outline=0)
    for x, y, r in ((500, 720, 46), (470, 900, 38), (540, 1030, 30), (560, 600, 26)):
        c.part(ell(x, y, r, r * 1.15), (235, 255, 240), (150, 255, 215), mirror=True, outline=7)
    c.part(ell(585, 290, 20, 20), (220, 255, 255), (120, 240, 255), mirror=True, outline=6)
    c.shine((440, 560, 600, 800), 70)
    c.save("src/beetle.png", (40, 255, 170))


def spider():
    c = Canvas()
    leg_in, leg_out = (225, 185, 255), (150, 90, 250)
    for pts in ([(580, 470), (440, 320), (390, 120)],
                [(560, 510), (330, 400), (170, 500)],
                [(560, 560), (320, 640), (180, 800)],
                [(590, 600), (430, 800), (370, 1060)]):
        c.part(poly(pts, 22), leg_in, leg_out, mirror=True, outline=9)
    c.part(poly([(610, 430), (585, 350)], 22), leg_in, leg_out, mirror=True, outline=8)
    c.part(ell(640, 830, 205, 250), (215, 160, 255), (80, 30, 170), center=(590, 740), radius=360)
    c.part(ell(640, 525, 135, 125), (200, 140, 255), (70, 30, 150), center=(610, 490))
    # hourglass mark on the abdomen
    c.part(lambda d: d.polygon([(640, 700), (700, 800), (640, 880), (580, 800)], fill=255),
           (255, 235, 255), (240, 150, 255), outline=7)
    c.part(ell(640, 960, 34, 44), (255, 235, 255), (240, 150, 255), outline=7)
    for x, y, r in ((612, 440, 15), (575, 470, 11)):
        c.part(ell(x, y, r, r), (255, 255, 255), (200, 240, 255), mirror=True, outline=5)
    c.shine((510, 660, 620, 820), 60)
    c.save("src/spider.png", (170, 90, 255))


def snail():
    c = Canvas()
    body_in, body_out = (255, 240, 160), (235, 160, 50)
    for pts in ([(1035, 740), (1010, 560)], [(1075, 760), (1140, 610)]):
        c.part(poly(pts, 24), body_in, body_out, outline=9)
        x, y = pts[1]
        c.part(ell(x, y, 34, 34), (255, 255, 235), (255, 210, 110), outline=9)
        c.part(ell(x + 6, y - 4, 13, 13), DARK, DARK, outline=0)

    def body(d):
        d.line([(250, 960), (980, 960)], fill=255, width=110)
        d.ellipse((925, 905, 1035, 1015), fill=255)
        d.polygon([(110, 1015), (260, 905), (300, 1015)], fill=255)
        d.line([(950, 950), (1045, 770)], fill=255, width=120)
        d.ellipse((985, 710, 1105, 830), fill=255)
    c.part(body, body_in, body_out, center=(800, 880), radius=620)

    c.part(ell(560, 640, 330, 330), (255, 200, 150), (225, 60, 140), center=(470, 540), radius=520)
    spiral = []
    for i in range(0, 420):
        th = i / 420 * 4.6 * math.pi
        r = 285 * (1 - i / 420) ** 0.85 + 12
        spiral.append((560 + r * math.cos(th + 0.6), 640 + r * math.sin(th + 0.6)))
    c.part(lambda d: d.line(spiral, fill=255, width=20, joint="curve"), (120, 20, 90), (90, 10, 70), outline=0)
    c.shine((360, 380, 560, 560), 80)
    c.save("src/snail.png", (255, 190, 80))


beetle()
spider()
snail()
