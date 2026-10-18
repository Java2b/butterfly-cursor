# Draws the original pixel-art black samurai: dark lacquered armour with gold trim, a helmet with a golden
# crescent crest, a black face mask, black hakama and a katana. Drawn on a 64x64 grid and scaled 5x with
# nearest neighbour so the pixels stay sharp.
# Strip of 10 square frames: 0-5 running with the katana held low behind, 6-7 on guard with the katana raised
# (breathing), 8-9 a slash with a white arc.
# Usage: python tools/make_samurai.py
import math
from PIL import Image, ImageDraw, ImageFilter

G, SCALE = 64, 5
OUT = G * SCALE
OUTLINE = (8, 8, 14, 255)
ARM = (30, 34, 56, 255)          # lacquered plates
ARM_L = (60, 68, 106, 255)
ARM_D = (18, 20, 34, 255)
GOLD = (236, 176, 48, 255)
GOLD_D = (168, 112, 24, 255)
CLOTH = (22, 22, 30, 255)        # hakama
CLOTH_L = (48, 48, 64, 255)
CORD = (150, 40, 40, 255)        # red lacing
BLADE = (214, 222, 236, 255)
BLADE_L = (255, 255, 255, 255)
HILT = (40, 30, 26, 255)
SLASH = (235, 245, 255, 210)
GLOW = (120, 140, 230)


def poly(d, pts, c):
    d.polygon([(round(x), round(y)) for x, y in pts], fill=c)


def line(d, a, b, c, w=1):
    d.line([(round(a[0]), round(a[1])), (round(b[0]), round(b[1]))], fill=c, width=w)


def outline(img, skip=(SLASH,)):
    src = img.load()
    out = img.copy()
    o = out.load()
    for y in range(G):
        for x in range(G):
            if src[x, y][3]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < G and 0 <= ny < G and src[nx, ny][3] and src[nx, ny] not in skip:
                    o[x, y] = OUTLINE
                    break
    return out


def finish(img):
    img = outline(img).resize((OUT, OUT), Image.NEAREST)
    a = img.split()[3]
    halo = a.filter(ImageFilter.GaussianBlur(12)).point(lambda v: int(v * 0.62))   # dark armour needs a stronger glow to show on a dark taskbar
    out = Image.merge("RGBA", [Image.new("L", (OUT, OUT), c) for c in GLOW] + [halo])
    out.alpha_composite(img)
    return out


def leg(d, hip, knee, foot, back):
    """A wide hakama leg: a trouser that flares towards the ankle, and a black foot."""
    c, cl = (CLOTH, CLOTH) if back else (CLOTH, CLOTH_L)
    kx, ky = knee
    fx, fy = foot
    poly(d, [(hip[0] - 3, hip[1]), (hip[0] + 3, hip[1]), (kx + 3, ky), (fx + 4, fy - 1), (fx - 4, fy - 1), (kx - 3, ky)], c)
    line(d, (hip[0] + 1, hip[1] + 1), (fx + 2, fy - 2), cl)                      # fold
    d.rectangle((fx - 2, fy - 1, fx + 3, fy), fill=ARM_D if back else OUTLINE)  # foot


def torso(d, x, y, lean=0):
    """Chest armour with gold-trimmed rows, red lacing, skirt plates and big shoulder plates; (x, y) = neck."""
    sx = lean
    poly(d, [(x - 4 + sx, y), (x + 5 + sx, y), (x + 5, y + 15), (x - 5, y + 15)], ARM)
    line(d, (x - 4 + sx, y), (x + 5 + sx, y), GOLD_D)
    for k, yy in enumerate((y + 4, y + 8, y + 12)):
        line(d, (x - 4 + sx * (1 - k / 3), yy), (x + 5 + sx * (1 - k / 3), yy), ARM_D)
        line(d, (x - 2 + sx, yy - 2), (x + 4 + sx, yy - 2), ARM_L)
    d.point((x + 1 + sx, y + 2), fill=GOLD)
    # skirt plates (kusazuri)
    for k, (ox, w) in enumerate(((-6, 4), (-2, 4), (2, 4))):
        poly(d, [(x + ox, y + 15), (x + ox + w, y + 15), (x + ox + w + 1, y + 21), (x + ox - 1, y + 21)], ARM if k != 1 else ARM_L)
        line(d, (x + ox - 1, y + 21), (x + ox + w + 1, y + 21), GOLD)
    line(d, (x - 5, y + 15), (x + 5, y + 15), GOLD)                               # belt


def shoulder(d, x, y, front):
    poly(d, [(x - 3, y), (x + 3, y), (x + 4, y + 7), (x - 4, y + 7)], ARM_L if front else ARM)
    line(d, (x - 3, y + 3), (x + 3, y + 3), ARM_D)
    line(d, (x - 4, y + 7), (x + 4, y + 7), GOLD)


def head(d, x, y):
    """Helmet with a flaring neck guard and a golden crescent crest; black mask with a gold mouth; (x, y) = chin."""
    poly(d, [(x - 8, y - 4), (x + 6, y - 4), (x + 8, y), (x - 9, y + 1)], ARM)        # neck guard (shikoro)
    line(d, (x - 8, y - 2), (x + 7, y - 2), GOLD_D)
    line(d, (x - 9, y + 1), (x + 8, y), GOLD)
    d.ellipse((x - 5, y - 13, x + 5, y - 4), fill=ARM)                                 # bowl
    line(d, (x - 3, y - 12), (x + 2, y - 12), ARM_L)
    d.rectangle((x + 1, y - 7, x + 6, y - 2), fill=OUTLINE)                            # face mask
    line(d, (x + 3, y - 6), (x + 6, y - 6), GOLD)                                      # eye slit glint
    line(d, (x + 3, y - 3), (x + 5, y - 3), GOLD_D)                                    # mouth of the mask
    # crest: a crescent rising from the brow
    line(d, (x + 2, y - 11), (x + 1, y - 17), GOLD)
    line(d, (x + 2, y - 11), (x + 7, y - 16), GOLD)
    d.point((x + 2, y - 11), fill=GOLD_D)


def katana(d, hand, ang, length=24):
    """Hilt in the hand, blade along ang (degrees; 0 = to the right, positive = down)."""
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    hb = (hand[0] - ux * 4, hand[1] - uy * 4)
    line(d, hb, hand, HILT, 2)                                                         # hilt
    d.point((round(hb[0]), round(hb[1])), fill=GOLD)
    tsuba = (hand[0] + ux, hand[1] + uy)
    line(d, (tsuba[0] - uy * 1.5, tsuba[1] + ux * 1.5), (tsuba[0] + uy * 1.5, tsuba[1] - ux * 1.5), GOLD, 1)
    tip = (hand[0] + ux * length, hand[1] + uy * length)
    line(d, (hand[0] + ux * 2, hand[1] + uy * 2), tip, BLADE, 1)
    d.point((round(tip[0]), round(tip[1])), fill=BLADE_L)


def scabbard(d, x, y):
    line(d, (x, y), (x - 15, y + 4), OUTLINE, 2)
    line(d, (x - 1, y), (x - 15, y + 4), ARM_D)
    d.point((x - 15, y + 4), fill=GOLD)


def arm(d, a, b, c=ARM_L):
    line(d, a, b, c, 2)
    t = 0.75
    w = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    line(d, w, b, GOLD_D if c == ARM_D else GOLD, 2)                                 # bracer and glove
    d.point((round(b[0]), round(b[1])), fill=OUTLINE)


def run(i):
    img = Image.new("RGBA", (G, G), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    ph = i / 6 * 2 * math.pi
    bob = round(1 - abs(math.sin(ph)) * 1.5)
    nx, ny = 33, 26 + bob                         # neck, leaning forward
    hip = (30, 42 + bob)
    s = math.sin(ph)
    # back leg then (after the body) the front leg; they swap every half cycle
    fa = (hip, (hip[0] + 6 * s + 1, 51 + bob), (hip[0] + 11 * s, 61 - max(0, -s) * 3))
    fb = (hip, (hip[0] - 6 * s + 1, 51 + bob), (hip[0] - 11 * s, 61 - max(0, s) * 3))
    leg(d, *fb, back=True)
    scabbard(d, hip[0] - 1, hip[1] - 3)
    shoulder(d, nx - 5, ny + 1, False)
    arm(d, (nx - 3, ny + 4), (nx + 4, ny + 12), ARM)                               # back arm to the hilt
    torso(d, nx - 1, ny, lean=2)
    leg(d, *fa, back=False)
    head(d, nx + 2, ny - 1)
    shoulder(d, nx + 4, ny + 1, True)
    arm(d, (nx + 4, ny + 5), (nx + 7, ny + 12))
    katana(d, (nx + 7, ny + 13), 160, 25)                                            # blade trailing low behind
    return finish(img)


def guard(breath):
    img = Image.new("RGBA", (G, G), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    nx, ny = 31, 26 + breath
    hip = (30, 42)
    leg(d, hip, (24, 51), (20, 61), True)
    scabbard(d, hip[0] - 1, hip[1] - 3)
    shoulder(d, nx - 5, ny + 1, False)
    arm(d, (nx - 3, ny + 3), (nx + 6, ny - 12), ARM)                               # both hands up over the head
    torso(d, nx, ny)
    leg(d, hip, (37, 51), (42, 61), False)
    head(d, nx + 2, ny - 1)
    shoulder(d, nx + 5, ny + 1, True)
    arm(d, (nx + 4, ny + 4), (nx + 8, ny - 12))
    katana(d, (nx + 8, ny - 13), 200, 27)                                            # jodan: blade back over the head
    return finish(img)


def slash(k):
    img = Image.new("RGBA", (G, G), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    nx, ny = 33, 28
    hip = (31, 43)
    leg(d, hip, (24, 52), (19, 61), True)
    scabbard(d, hip[0] - 1, hip[1] - 3)
    shoulder(d, nx - 5, ny + 1, False)
    hand = (nx + 9, ny + 8) if k == 0 else (nx + 8, ny + 11)
    arm(d, (nx - 3, ny + 4), hand, ARM)
    torso(d, nx, ny, lean=2)
    leg(d, hip, (39, 52), (45, 61), False)
    if k == 0:
        d.arc((nx - 8, ny - 22, nx + 30, ny + 16), 250, 30, fill=SLASH, width=2)       # the cut through the air
    head(d, nx + 3, ny - 1)
    shoulder(d, nx + 5, ny + 1, True)
    arm(d, (nx + 4, ny + 5), hand)
    katana(d, hand, 20 if k == 0 else 40, 22)
    return finish(img)


def main():
    frames = [run(i) for i in range(6)] + [guard(0), guard(1), slash(0), slash(1)]
    strip = Image.new("RGBA", (OUT * len(frames), OUT), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        strip.paste(f, (i * OUT, 0))
    strip.save("src/samurai.png")
    print("src/samurai.png", strip.size)


if __name__ == "__main__":
    main()
