# Draws the weather companions: rain cloud, snow cloud, sun (disc + separate rotating rays) and moon.
# Usage: python tools/make_weather.py
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

N, OUT = 1280, 320
yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)


def gradient_fill(mask, top, bottom, y0, y1):
    t = np.clip((yy - y0) / max(1, y1 - y0), 0, 1)[..., None]
    rgb = np.array(top, np.float32) * (1 - t) + np.array(bottom, np.float32) * t
    return Image.fromarray(np.dstack([rgb, np.asarray(mask)]).astype(np.uint8), "RGBA")


def radial_fill(mask, inner, outer, cx, cy, r):
    t = np.clip(np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r, 0, 1)[..., None]
    rgb = np.array(inner, np.float32) * (1 - t) + np.array(outer, np.float32) * t
    return Image.fromarray(np.dstack([rgb, np.asarray(mask)]).astype(np.uint8), "RGBA")


def outline(mask, color, width):
    fat = mask.filter(ImageFilter.GaussianBlur(width)).point(lambda v: 255 if v > 30 else 0).filter(ImageFilter.GaussianBlur(1.5))
    return Image.merge("RGBA", [Image.new("L", (N, N), c) for c in color] + [fat])


def finish(img, glow, path, strength=0.6, radius=40):
    a = img.split()[3]
    halo = a.filter(ImageFilter.GaussianBlur(radius)).point(lambda v: int(min(255, v * strength)))
    out = Image.merge("RGBA", [Image.new("L", (N, N), c) for c in glow] + [halo])
    out.alpha_composite(img)
    out.resize((OUT, OUT), Image.LANCZOS).save(path)
    print("saved", path)


def cute_cloud(path, top, bottom, line, glow, happy):
    """A cloud the way children draw it: uneven puffy bumps, a lumpy bottom, thick soft outline and a face."""
    rng = np.random.RandomState(7 if happy else 3)
    m = Image.new("L", (N, N), 0)
    d = ImageDraw.Draw(m)
    bumps = [(330, 730, 128), (470, 615, 160), (655, 545, 205), (850, 600, 165), (1000, 715, 132),   # top puffs
             (365, 850, 96), (505, 880, 104), (650, 888, 108), (795, 878, 100), (935, 848, 92)]       # lumpy bottom
    for cx, cy, r in bumps:
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
    d.ellipse((300, 560, 1040, 900), fill=255)
    # hand-drawn wobble: a smooth random field pushes the edge in and out a little
    noise = Image.fromarray((rng.rand(10, 10) * 255).astype(np.uint8)).resize((N, N), Image.BICUBIC)
    soft = np.asarray(m.filter(ImageFilter.GaussianBlur(14)), np.float32) + (np.asarray(noise, np.float32) - 128) * 0.55
    m = Image.fromarray(((soft > 128) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.8))

    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    img.alpha_composite(outline(m, line, 16))
    img.alpha_composite(gradient_fill(m, top, bottom, 380, 960))
    hl = Image.new("RGBA", (N, N), (255, 255, 255, 0))
    hd = ImageDraw.Draw(hl)
    for cx, cy, r in ((610, 470, 95), (430, 580, 60), (845, 545, 70)):
        hd.ellipse((cx - r, cy - r * 0.6, cx + r, cy + r * 0.6), fill=(255, 255, 255, 150))
    img.alpha_composite(Image.composite(hl.filter(ImageFilter.GaussianBlur(20)), Image.new("RGBA", (N, N)), m))

    # face
    f = ImageDraw.Draw(img)
    ink = (52, 48, 70)
    if happy:
        for ex in (575, 765):
            f.ellipse((ex - 20, 718, ex + 20, 768), fill=ink)
            f.ellipse((ex - 8, 728, ex + 4, 742), fill=(255, 255, 255))
        f.arc((630, 760, 710, 815), 20, 160, fill=ink, width=10)
    else:
        for ex in (575, 765):                     # calm, closed eyes
            f.arc((ex - 28, 715, ex + 28, 765), 200, 340, fill=ink, width=10)
        f.arc((640, 770, 700, 805), 20, 160, fill=ink, width=9)
    cheeks = Image.new("RGBA", (N, N), (255, 140, 160, 0))
    cd = ImageDraw.Draw(cheeks)
    for ex in (515, 825):
        cd.ellipse((ex - 42, 770, ex + 42, 806), fill=(255, 140, 160, 120))
    img.alpha_composite(cheeks.filter(ImageFilter.GaussianBlur(6)))
    finish(img, glow, path, 0.45, 34)


def cloud(path, top, bottom, line, glow):
    m = Image.new("L", (N, N), 0)
    d = ImageDraw.Draw(m)
    for cx, cy, r in ((430, 690, 190), (650, 590, 250), (880, 680, 200), (300, 790, 135), (1010, 790, 140)):
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
    d.rounded_rectangle((250, 690, 1060, 900), radius=105, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(1.5))
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    img.alpha_composite(outline(m, line, 10))
    img.alpha_composite(gradient_fill(m, top, bottom, 340, 900))
    # soft highlights on the puffs
    hl = Image.new("RGBA", (N, N), (255, 255, 255, 0))
    hd = ImageDraw.Draw(hl)
    for cx, cy, r in ((600, 470, 120), (400, 610, 80), (860, 590, 90)):
        hd.ellipse((cx - r, cy - r * 0.7, cx + r, cy + r * 0.7), fill=(255, 255, 255, 110))
    img.alpha_composite(Image.composite(hl.filter(ImageFilter.GaussianBlur(24)), Image.new("RGBA", (N, N)), m))
    finish(img, glow, path, 0.5, 36)


def sun():
    cx = cy = N // 2
    # rays: a separate picture, the program turns it slowly behind the disc
    rays = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    rm = Image.new("L", (N, N), 0)
    d = ImageDraw.Draw(rm)
    for i in range(12):
        a = i * math.pi / 6
        r0, r1, w = 330, (590 if i % 2 == 0 else 500), 0.17
        pts = [(cx + r0 * math.cos(a - w), cy + r0 * math.sin(a - w)),
               (cx + r1 * math.cos(a), cy + r1 * math.sin(a)),
               (cx + r0 * math.cos(a + w), cy + r0 * math.sin(a + w))]
        d.polygon(pts, fill=255)
    rm = rm.filter(ImageFilter.GaussianBlur(3))
    rays.alpha_composite(radial_fill(rm, (255, 245, 150), (255, 150, 30), cx, cy, 600))
    finish(rays, (255, 190, 60), "src/sun_rays.png", 0.45, 30)

    disc = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    dm = Image.new("L", (N, N), 0)
    ImageDraw.Draw(dm).ellipse((cx - 300, cy - 300, cx + 300, cy + 300), fill=255)
    dm = dm.filter(ImageFilter.GaussianBlur(1.5))
    disc.alpha_composite(outline(dm, (215, 110, 20), 9))
    disc.alpha_composite(radial_fill(dm, (255, 252, 215), (255, 175, 40), cx - 80, cy - 90, 430))
    finish(disc, (255, 200, 80), "src/sun.png", 0.7, 50)


def moon():
    cx = cy = N // 2
    m = Image.new("L", (N, N), 0)
    ImageDraw.Draw(m).ellipse((cx - 340, cy - 340, cx + 340, cy + 340), fill=255)
    cut = Image.new("L", (N, N), 0)
    ImageDraw.Draw(cut).ellipse((cx - 340 + 190, cy - 340 - 70, cx + 340 + 150, cy + 340 - 90), fill=255)
    m = ImageChops.subtract(m, cut).filter(ImageFilter.GaussianBlur(1.5))
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    img.alpha_composite(outline(m, (150, 130, 80), 8))
    img.alpha_composite(radial_fill(m, (255, 250, 220), (225, 205, 145), cx - 200, cy - 60, 520))
    # craters
    cr = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    cd = ImageDraw.Draw(cr)
    for x, y, r in ((cx - 210, cy - 120, 46), (cx - 240, cy + 90, 34), (cx - 120, cy + 210, 40), (cx - 90, cy - 250, 26)):
        cd.ellipse((x - r, y - r, x + r, y + r), fill=(190, 170, 115, 120))
    img.alpha_composite(Image.composite(cr.filter(ImageFilter.GaussianBlur(3)), Image.new("RGBA", (N, N)), m))
    finish(img, (255, 240, 190), "src/moon.png", 0.6, 46)


cute_cloud("src/cloud_rain.png", (226, 234, 248), (150, 168, 200), (70, 80, 110), (140, 180, 255), happy=False)
cute_cloud("src/cloud_snow.png", (255, 255, 255), (212, 228, 250), (95, 115, 155), (220, 235, 255), happy=True)
sun()
moon()
