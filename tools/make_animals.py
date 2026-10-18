# Draws the panda as a frame strip (320x320 frames).
#   panda.png     6 walking frames + 5 resting frames (sits, lifts the bamboo, bites, chews, chews)
# Usage: python tools/make_animals.py
import math
from PIL import Image, ImageDraw, ImageFilter

N, OUT = 1024, 320
OUTLINE = (24, 22, 36)


def dark(c, k=0.72):
    return tuple(int(v * k) for v in c)


def polar(p, length, ang):
    r = math.radians(ang)                     # 0 = straight down, positive = forward (right)
    return (p[0] + length * math.sin(r), p[1] + length * math.cos(r))


def limb(d, a, b, w, col, ow=7):
    for width, c in ((w + 2 * ow, OUTLINE), (w, col)):
        d.line([a, b], fill=c, width=int(width))
        for p in (a, b):
            d.ellipse((p[0] - width / 2, p[1] - width / 2, p[0] + width / 2, p[1] + width / 2), fill=c)


def ell(d, cx, cy, rx, ry, col, ow=7):
    if ow:
        d.ellipse((cx - rx - ow, cy - ry - ow, cx + rx + ow, cy + ry + ow), fill=OUTLINE)
    d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=col)


def poly(d, pts, col, ow=6):
    if ow:
        d.polygon(pts, fill=OUTLINE)
        d.line(pts + [pts[0]], fill=OUTLINE, width=ow * 2, joint="curve")
    d.polygon(pts, fill=col)


def finish(img, glow, strength=0.5):
    a = img.split()[3]
    halo = a.filter(ImageFilter.GaussianBlur(18)).point(lambda v: int(v * strength))
    out = Image.merge("RGBA", [Image.new("L", (N, N), c) for c in glow] + [halo])
    out.alpha_composite(img)
    return out.resize((OUT, OUT), Image.LANCZOS)


def strip(frames, path):
    s = Image.new("RGBA", (OUT * len(frames), OUT), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        s.paste(f, (i * OUT, 0))
    s.save(path)
    print("saved", path, len(frames), "frames")


def closed_eye(d, x, y, r):
    d.arc((x - r, y - r * 0.6, x + r, y + r * 0.9), 200, 340, fill=OUTLINE, width=max(4, int(r * 0.35)))


def zzz(d, x, y, s):
    for k in range(3):
        z = s * (1 - k * 0.25)
        zx, zy = x + k * s * 0.9, y - k * s * 1.1
        d.line([(zx, zy), (zx + z, zy), (zx, zy + z), (zx + z, zy + z)], fill=(230, 240, 255), width=max(4, int(z * 0.2)))


# ------------------------------------------------------------------ panda
WH = (250, 250, 248)
BK = (40, 40, 48)
BAND = (220, 40, 50)
BAMBOO = (120, 190, 70)


def panda_walk(ph):
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    bob = -12 * abs(math.sin(ph))
    hip = (500, 700 + bob)
    for p, near in ((ph + math.pi, False), (ph, True)):                  # short black legs, waddling
        col = BK if near else dark(BK, 0.8)
        sw = 26 * math.sin(p)
        knee = polar(hip, 90, sw)
        foot = polar(knee, 90, sw - 10)
        if not near:
            limb(d, (hip[0] - 20, hip[1]), knee, 70, col)
            limb(d, knee, foot, 66, col)
            ell(d, foot[0] + 18, foot[1] + 10, 42, 22, col, 5)
    far_arm_a = 30 * math.sin(ph)
    sh = (520, 500 + bob)
    limb(d, sh, polar(sh, 140, -far_arm_a), 64, dark(BK, 0.8))
    ell(d, 500, 590 + bob, 170, 170, WH)                                  # round belly
    sw = 26 * math.sin(ph)
    knee = polar(hip, 90, sw)
    foot = polar(knee, 90, sw - 10)
    limb(d, hip, knee, 76, BK)
    limb(d, knee, foot, 70, BK)
    ell(d, foot[0] + 18, foot[1] + 10, 46, 24, BK, 5)
    limb(d, (sh[0] + 10, sh[1] + 10), polar((sh[0] + 10, sh[1] + 10), 140, far_arm_a), 70, BK)
    # head with ears, eye patches and the red headband
    hx, hy = 560, 330 + bob
    for ox in (-90, 60):
        ell(d, hx + ox, hy - 110, 48, 48, BK)
    ell(d, hx, hy, 150, 135, WH)
    d.line([(hx - 150, hy - 60), (hx + 145, hy - 55)], fill=OUTLINE, width=40)
    d.line([(hx - 150, hy - 60), (hx + 145, hy - 55)], fill=BAND, width=28)
    for i in range(2):
        tail = [(hx - 140, hy - 58)]
        for k in range(1, 4):
            tail.append((tail[0][0] - k * 40, tail[0][1] + 14 * k + i * 22 + 12 * math.sin(ph * 2 + k)))
        d.line(tail, fill=BAND, width=16, joint="curve")
    ell(d, hx + 60, hy + 5, 38, 48, BK, 0)                                # eye patch (side view: one)
    ell(d, hx + 66, hy - 2, 13, 15, (255, 255, 255), 0)
    ell(d, hx + 68, hy, 7, 8, OUTLINE, 0)
    ell(d, hx + 135, hy + 40, 22, 16, BK, 0)                              # nose
    d.arc((hx + 90, hy + 45, hx + 140, hy + 85), 20, 140, fill=OUTLINE, width=6)
    return finish(img, (255, 255, 255), 0.4)


def panda_sit(step):
    """Front view, sitting. step 0 hold bamboo, 1 lift, 2 bite, 3 chew, 4 chew (happy)."""
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = N // 2
    # legs stretched out in front
    for sx in (-1, 1):
        ell(d, cx + sx * 130, 900, 85, 62, BK)
        ell(d, cx + sx * 140, 905, 42, 34, (90, 85, 95), 0)               # paw pad
    ell(d, cx, 720, 210, 200, WH)                                          # body
    # bamboo: held in the right paw (viewer's left), moves up to the mouth
    bamboo = {0: ((cx - 230, 840), (cx - 160, 560)), 1: ((cx - 150, 760), (cx - 60, 470)),
              2: ((cx - 90, 640), (cx + 10, 400)), 3: ((cx - 110, 690), (cx - 10, 460)),
              4: ((cx - 110, 690), (cx - 10, 470))}[step]
    (bx0, by0), (bx1, by1) = bamboo
    if step >= 3:                                                          # it got shorter: a bite is gone
        bx1, by1 = bx0 + (bx1 - bx0) * 0.82, by0 + (by1 - by0) * 0.82
    limb(d, (cx - 160, 600), (bx0 + (bx1 - bx0) * 0.25, by0 + (by1 - by0) * 0.25), 80, BK)
    limb(d, (bx0, by0), (bx1, by1), 44, BAMBOO, 6)
    for t in (0.3, 0.6):
        x, y = bx0 + (bx1 - bx0) * t, by0 + (by1 - by0) * t
        d.line([(x - 18, y + 6), (x + 18, y - 6)], fill=dark(BAMBOO, 0.6), width=6)
    leaf_base = (bx0 + (bx1 - bx0) * 0.45, by0 + (by1 - by0) * 0.45)
    poly(d, [leaf_base, (leaf_base[0] - 90, leaf_base[1] - 10), (leaf_base[0] - 30, leaf_base[1] + 20)], (140, 210, 90), 4)
    # arms: one holds the bamboo, the other rests on the belly
    paw = (bx0 + (bx1 - bx0) * 0.25, by0 + (by1 - by0) * 0.25)
    ell(d, paw[0], paw[1], 40, 40, BK)                                     # the paw wraps around the bamboo
    limb(d, (cx + 160, 600), (cx + 90, 760), 80, BK)
    # head
    hx, hy = cx, 400
    for sx in (-1, 1):
        ell(d, hx + sx * 130, hy - 115, 55, 55, BK)
    ell(d, hx, hy, 175, 150, WH)
    d.line([(hx - 172, hy - 70), (hx + 172, hy - 70)], fill=OUTLINE, width=40)
    d.line([(hx - 172, hy - 70), (hx + 172, hy - 70)], fill=BAND, width=28)
    for sx in (-1, 1):
        ell(d, hx + sx * 70, hy + 5, 48, 58, BK, 0)                         # eye patches
        if step == 4:
            closed_eye(d, hx + sx * 70, hy + 2, 20)                        # happy chewing
        else:
            ell(d, hx + sx * 66, hy - 2, 15, 17, (255, 255, 255), 0)
            ell(d, hx + sx * 64, hy + 2, 8, 9, OUTLINE, 0)
    ell(d, hx, hy + 60, 30, 20, BK, 0)                                     # nose
    if step == 2:
        ell(d, hx, hy + 110, 34, 26, (150, 40, 50))                        # mouth open for the bite
    elif step in (3, 4):
        for sx in (-1, 1):                                                 # puffed cheeks while chewing
            ell(d, hx + sx * (95 if step == 3 else 85), hy + 95, 46, 34, WH, 0)
            ell(d, hx + sx * (95 if step == 3 else 85), hy + 100, 22, 12, (255, 170, 180), 0)
        d.arc((hx - 30, hy + 80, hx + 30, hy + 120), 20, 160, fill=OUTLINE, width=6)
    else:
        d.arc((hx - 30, hy + 75, hx, hy + 110), 20, 160, fill=OUTLINE, width=6)
        d.arc((hx, hy + 75, hx + 30, hy + 110), 20, 160, fill=OUTLINE, width=6)
    return finish(img, (255, 255, 255), 0.4)


strip([panda_walk(2 * math.pi * i / 6) for i in range(6)] + [panda_sit(k) for k in range(5)], "src/panda.png")
