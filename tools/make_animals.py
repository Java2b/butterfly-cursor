# Draws the dragon, the lion head, the baby elephant and the panda as frame strips (320x320 frames).
#   dragon.png    6 wing-flap frames + 2 sleeping frames (curled up, breathing)
#   lion_head.png 3 frames: normal, blink, roar
#   elephant.png  6 walking frames + 2 resting frames (trunk up / trunk curled)
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


# ------------------------------------------------------------------ dragon
DR = (58, 186, 138)
DR_BELLY = (246, 224, 150)
DR_WING = (120, 222, 186)
DR_SPIKE = (250, 150, 60)


def dragon_fly(ph):
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    bob = -14 * math.sin(ph)
    flap = 15 + 60 * math.sin(ph)                         # wing angle: up when positive
    sh = (500, 470 + bob)

    def wing(near):
        col = DR_WING if near else dark(DR_WING, 0.7)
        bone = dark(DR, 0.8) if near else dark(DR, 0.55)
        a = 180 - flap - (0 if near else 12)               # 180 = straight up
        wrist = polar(sh, 190, a - 10)                     # arm bone, up and slightly forward
        tips = [polar(wrist, 200, a + 25), polar(wrist, 210, a + 70), polar(wrist, 170, a + 115)]
        root = (sh[0] - 120, sh[1] + 10)
        # bat-like membrane: scalloped between the finger tips
        mem = [sh, wrist, tips[0]]
        for t0, t1 in ((tips[0], tips[1]), (tips[1], tips[2]), (tips[2], root)):
            mid = ((t0[0] + t1[0]) / 2, (t0[1] + t1[1]) / 2)
            mem.append((mid[0] + (wrist[0] - mid[0]) * 0.28, mid[1] + (wrist[1] - mid[1]) * 0.28))
            mem.append(t1)
        poly(d, [(int(x), int(y)) for x, y in mem], col)
        for t in tips:
            d.line([wrist, t], fill=bone, width=8)
        limb(d, sh, wrist, 18, bone, 4)

    wing(False)
    # tail: a chain of shrinking circles curling back, with an arrow tip
    pts = []
    for i in range(14):
        t = i / 13
        pts.append((430 - t * 330, 560 + bob + math.sin(t * 3.2 + ph * 0.5) * 40 * t, 58 - 46 * t))
    for x, y, r in pts:
        ell(d, x, y, r, r, DR)
    tx, ty, _ = pts[-1]
    poly(d, [(tx - 10, ty), (tx - 60, ty - 30), (tx - 45, ty + 5), (tx - 60, ty + 35)], DR_SPIKE, 5)
    # body and belly
    ell(d, 470, 530 + bob, 120, 85, DR)
    ell(d, 485, 565 + bob, 90, 45, DR_BELLY, 0)
    for k in range(5):                                     # belly stripes
        x = 420 + k * 30
        d.arc((x - 18, 535 + bob, x + 18, 600 + bob), 20, 160, fill=dark(DR_BELLY, 0.8), width=4)
    # legs tucked in flight
    for lx, k in ((540, 1.0), (410, 0.85)):
        knee = (lx + 20, 600 + bob)
        foot = (lx + 50, 625 + bob)
        limb(d, (lx, 570 + bob), knee, 34 * k, DR)
        limb(d, knee, foot, 26 * k, DR)
    # neck and head
    for i in range(6):
        t = i / 5
        ell(d, 560 + t * 110, 470 + bob - t * 90, 48 - 8 * t, 48 - 8 * t, DR)
    hx, hy = 690, 370 + bob
    poly(d, [(hx - 40, hy - 40), (hx - 95, hy - 95), (hx - 20, hy - 55)], DR_SPIKE, 5)    # horns
    poly(d, [(hx - 10, hy - 50), (hx - 40, hy - 115), (hx + 10, hy - 58)], DR_SPIKE, 5)
    ell(d, hx, hy, 72, 58, DR)
    ell(d, hx + 70, hy + 18, 55, 36, DR)                   # snout
    ell(d, hx + 72, hy + 34, 40, 14, DR_BELLY, 0)
    ell(d, hx + 108, hy + 8, 7, 5, OUTLINE, 0)             # nostril
    ell(d, hx + 10, hy - 12, 20, 22, (255, 255, 255), 5)
    ell(d, hx + 16, hy - 10, 10, 13, OUTLINE, 0)
    ell(d, hx + 19, hy - 15, 4, 4, (255, 255, 255), 0)
    d.arc((hx + 40, hy + 20, hx + 100, hy + 52), 20, 120, fill=OUTLINE, width=5)          # smile
    # back spikes
    for i in range(7):
        x = 350 + i * 45
        y = 455 + bob + (0 if i < 5 else (i - 4) * 10)
        poly(d, [(x - 16, y + 8), (x, y - 26), (x + 16, y + 8)], DR_SPIKE, 4)
    wing(True)
    return finish(img, (120, 255, 200))


def dragon_sleep(k):
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    breath = 1 + 0.03 * k
    cx, cy = 512, 700
    # curled body (front view): a big round body with the tail wrapped around
    for i in range(16):
        a = math.pi * (0.15 + i / 15 * 1.5)
        r = 210 * breath
        ell(d, cx + math.cos(a) * r, cy + math.sin(a) * r * 0.45 + 30, 40 - i * 1.6, 40 - i * 1.6, DR)
    ell(d, cx, cy, 190 * breath, 130 * breath, DR)
    ell(d, cx, cy + 40, 130 * breath, 70 * breath, DR_BELLY, 0)
    poly(d, [(cx - 120, cy - 110), (cx - 40, cy - 190), (cx + 10, cy - 100)], dark(DR_WING, 0.85))   # folded wing
    for i in range(5):
        x = cx - 140 + i * 50
        poly(d, [(x - 14, cy - 110 - (i % 2) * 6), (x, cy - 145), (x + 14, cy - 110)], DR_SPIKE, 4)
    # head resting on the body, eyes closed
    hx, hy = cx + 140, cy - 40
    poly(d, [(hx - 30, hy - 40), (hx - 80, hy - 90), (hx - 10, hy - 55)], DR_SPIKE, 5)
    ell(d, hx, hy, 70, 56, DR)
    ell(d, hx + 62, hy + 16, 50, 32, DR)
    closed_eye(d, hx + 8, hy - 8, 22)
    ell(d, hx + 98, hy + 6, 6, 4, OUTLINE, 0)
    zzz(d, hx + 60, hy - 120 - k * 14, 44)
    return finish(img, (120, 255, 200))


# ------------------------------------------------------------------ lion head
MANE = (214, 120, 40)
MANE_LIGHT = (240, 160, 60)
FACE = (246, 196, 110)
MUZZLE = (255, 240, 214)


def lion_head(mode):
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = 512, 520
    grow = 1.08 if mode == "roar" else 1.0
    # mane: two rings of tufts
    for ring, (rad, size, col) in enumerate(((330, 120, MANE), (270, 105, MANE_LIGHT))):
        for i in range(16):
            a = i / 16 * 2 * math.pi + ring * 0.2
            x, y = cx + math.cos(a) * rad * grow, cy + math.sin(a) * rad * grow
            tip = (cx + math.cos(a) * (rad + size) * grow, cy + math.sin(a) * (rad + size) * grow)
            side = 0.33
            poly(d, [(cx + math.cos(a - side) * rad * 0.8 * grow, cy + math.sin(a - side) * rad * 0.8 * grow),
                     tip,
                     (cx + math.cos(a + side) * rad * 0.8 * grow, cy + math.sin(a + side) * rad * 0.8 * grow)], col, 5)
    # ears and face
    for sx in (-1, 1):
        ell(d, cx + sx * 175, cy - 190, 58, 58, FACE)
        ell(d, cx + sx * 175, cy - 190, 30, 30, dark(FACE, 0.8), 0)
    ell(d, cx, cy, 240, 230, FACE)
    # eyes
    for sx in (-1, 1):
        ex, ey = cx + sx * 90, cy - 50
        if mode == "blink":
            closed_eye(d, ex, ey, 30)
        elif mode == "roar":
            d.line([(ex - 34, ey - 8 + sx * 0), (ex + 34, ey + 8 * (1 if sx < 0 else -1))], fill=OUTLINE, width=12)   # fierce squint
        else:
            ell(d, ex, ey, 30, 34, (255, 255, 255), 5)
            ell(d, ex + 4, ey + 4, 17, 21, (70, 45, 20), 0)
            ell(d, ex + 9, ey - 4, 6, 6, (255, 255, 255), 0)
        d.line([(ex - 40, ey - 58), (ex + 30, ey - 50 - (14 if mode == "roar" else 0) * sx * -1)], fill=dark(MANE, 0.7), width=10)  # brows
    # muzzle, nose and mouth
    if mode == "roar":
        ell(d, cx, cy + 110, 105, 115, (120, 25, 35))                     # open mouth
        ell(d, cx, cy + 165, 60, 40, (230, 90, 110), 0)                   # tongue
        for sx in (-1, 1):                                                # fangs
            poly(d, [(cx + sx * 70, cy + 30), (cx + sx * 50, cy + 30), (cx + sx * 60, cy + 80)], (255, 255, 250), 3)
            poly(d, [(cx + sx * 70, cy + 200), (cx + sx * 50, cy + 200), (cx + sx * 60, cy + 160)], (255, 255, 250), 3)
        for sx in (-1, 1):
            ell(d, cx + sx * 75, cy + 15, 70, 50, MUZZLE)
    else:
        for sx in (-1, 1):
            ell(d, cx + sx * 55, cy + 70, 70, 55, MUZZLE)
        ell(d, cx, cy + 130, 40, 26, MUZZLE, 0)
        d.arc((cx - 60, cy + 70, cx, cy + 130), 20, 160, fill=OUTLINE, width=7)
        d.arc((cx, cy + 70, cx + 60, cy + 130), 20, 160, fill=OUTLINE, width=7)
    poly(d, [(cx - 42, cy + (0 if mode == "roar" else 20)), (cx + 42, cy + (0 if mode == "roar" else 20)), (cx, cy + (40 if mode == "roar" else 60))], (90, 50, 40), 4)
    for sx in (-1, 1):                                                    # whisker dots
        for k in range(3):
            ell(d, cx + sx * (55 + k * 22), cy + (55 if mode == "roar" else 75) + (k % 2) * 14, 5, 5, dark(FACE, 0.6), 0)
    return finish(img, (255, 190, 90), 0.45)


# ------------------------------------------------------------------ baby elephant
EL = (150, 170, 196)
EL_EAR = (232, 170, 190)


def elephant(ph, rest=None):
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    walking = rest is None
    bob = -10 * abs(math.sin(ph)) if walking else 0
    by = 600 + bob
    # legs: far pair first
    def leg(x, p, near):
        col = EL if near else dark(EL, 0.78)
        swing = 18 * math.sin(p) if walking else 0
        top = (x, by + 40)
        foot = polar(top, 190, swing)
        limb(d, top, foot, 78, col)
        ell(d, foot[0] + 4, foot[1] + 18, 40, 16, col, 5)
        for k in (-18, 0, 18):
            ell(d, foot[0] + k + 4, foot[1] + 24, 8, 6, (245, 240, 235), 0)
    leg(400, ph + math.pi, False)
    leg(590, ph, False)
    # tail
    d.line([(300, by - 10), (250, by + 40 + 10 * math.sin(ph * 2))], fill=OUTLINE, width=18)
    d.line([(300, by - 10), (250, by + 40 + 10 * math.sin(ph * 2))], fill=EL, width=8)
    ell(d, 470, by - 10, 190, 140, EL)                                    # body
    leg(360, ph, True)
    leg(560, ph + math.pi, True)
    # head
    hx, hy = 650, by - 110
    ell(d, hx, hy, 120, 110, EL)
    # trunk
    if walking:
        sway = 12 * math.sin(ph)
        tr = [(hx + 90, hy + 30), (hx + 140, hy + 100), (hx + 150 + sway, hy + 180), (hx + 130 + sway, hy + 230)]
    elif rest == 0:
        tr = [(hx + 90, hy + 20), (hx + 150, hy - 20), (hx + 170, hy - 110), (hx + 140, hy - 170)]   # trumpet up
    else:
        tr = [(hx + 90, hy + 30), (hx + 150, hy + 80), (hx + 150, hy + 150), (hx + 100, hy + 160)]   # curled
    for i in range(len(tr) - 1):
        limb(d, tr[i], tr[i + 1], 54 - i * 8, EL)
    ell(d, tr[-1][0], tr[-1][1], 22, 16, EL, 5)
    # ear (flaps)
    ear_a = (12 * math.sin(ph * 2)) if walking else (10 if rest == 0 else -6)
    ex, ey = hx - 70, hy + 15
    ear = []
    for i in range(14):
        a = math.radians(-100 + i * 15 + ear_a)
        r = 115 if 2 < i < 11 else 90
        ear.append((ex + math.cos(a) * r * 0.62, ey + math.sin(a) * r))
    poly(d, ear, EL)
    inner = [((x - ex) * 0.7 + ex + 4, (y - ey) * 0.7 + ey) for x, y in ear]
    d.polygon(inner, fill=EL_EAR)
    # eye and cheek
    ell(d, hx + 45, hy - 25, 16, 20, OUTLINE, 0)
    ell(d, hx + 50, hy - 32, 6, 6, (255, 255, 255), 0)
    d.line([(hx + 30, hy - 48), (hx + 22, hy - 60)], fill=OUTLINE, width=5)          # lashes
    d.line([(hx + 42, hy - 50), (hx + 40, hy - 64)], fill=OUTLINE, width=5)
    ell(d, hx + 60, hy + 25, 22, 13, (250, 160, 180), 0)
    return finish(img, (190, 210, 255), 0.45)


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


strip([dragon_fly(2 * math.pi * i / 6) for i in range(6)] + [dragon_sleep(0), dragon_sleep(1)], "src/dragon.png")
strip([lion_head("normal"), lion_head("blink"), lion_head("roar")], "src/lion_head.png")
strip([elephant(2 * math.pi * i / 6) for i in range(6)] + [elephant(0, 0), elephant(0, 1)], "src/elephant.png")
strip([panda_walk(2 * math.pi * i / 6) for i in range(6)] + [panda_sit(k) for k in range(5)], "src/panda.png")
