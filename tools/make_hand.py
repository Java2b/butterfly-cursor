# Draws the built-in "helper hand": a pale hand that scuttles on its fingertips, seen from the side and a
# little from above (back of the hand up). Strip of 9 square frames: 0-7 run cycle, 8 idle (index finger tapping).
# Usage: python tools/make_hand.py
import math
from PIL import Image, ImageDraw, ImageFilter

N, OUT, FRAMES = 1024, 320, 8
LINE = (92, 62, 56)
SKIN = (240, 216, 198)
SKIN_HI = (252, 236, 222)
NAIL = (250, 234, 228)
NAIL_EDGE = (214, 160, 150)
SCAR = (150, 62, 62)
GLOW = (255, 225, 205)
DY = 150                                   # moves the whole figure down so the fingertips touch the bottom


def shade(c, k):
    return tuple(int(v * k) for v in c)


def polar(p, length, ang):
    r = math.radians(ang)                  # 0 = straight down, positive = forward (right)
    return (p[0] + length * math.sin(r), p[1] + length * math.cos(r))


def segment(d, a, b, wa, wb, col, outline=True):
    """A tapered limb segment with rounded ends, outline and a highlight along its top side."""
    ax, ay = a; bx, by = b
    l = math.hypot(bx - ax, by - ay) or 1
    nx, ny = -(by - ay) / l, (bx - ax) / l
    def quad(ea, eb):
        return [(ax + nx * ea, ay + ny * ea), (bx + nx * eb, by + ny * eb), (bx - nx * eb, by - ny * eb), (ax - nx * ea, ay - ny * ea)]
    if outline:
        d.polygon(quad(wa / 2 + 6, wb / 2 + 6), fill=LINE)
        for (x, y), w in ((a, wa), (b, wb)):
            d.ellipse((x - w / 2 - 6, y - w / 2 - 6, x + w / 2 + 6, y + w / 2 + 6), fill=LINE)
    d.polygon(quad(wa / 2, wb / 2), fill=col)
    for (x, y), w in ((a, wa), (b, wb)):
        d.ellipse((x - w / 2, y - w / 2, x + w / 2, y + w / 2), fill=col)
    # highlight on the side facing up / towards the light
    hx, hy = (nx, ny) if ny < 0 else (-nx, -ny)
    hi = tuple(min(255, int(v * 1.06) + 6) for v in col)
    d.line([(ax + hx * wa * 0.22, ay + hy * wa * 0.22), (bx + hx * wb * 0.22, by + hy * wb * 0.22)], fill=hi, width=int(min(wa, wb) * 0.28))


def finger(d, base, ph, k, col, idle=False, tap=False):
    """Three segments with joint creases and a nail; k scales length and width (pinky smaller)."""
    if idle:
        a1, a2, a3 = 62, 7, -18
        if tap:
            a1, a2, a3 = 98, 66, 44
    else:
        lift = max(0.0, math.cos(ph))      # the fingertip lifts while it swings forward
        a1 = 62 + 18 * math.sin(ph)
        a2 = a1 - 55 + 12 * lift
        a3 = a2 - 25 + 38 * lift
    j1 = polar(base, 120 * k, a1)
    j2 = polar(j1, 86 * k, a2)
    tip = polar(j2, 70 * k, a3)
    segment(d, base, j1, 54 * k, 48 * k, col)
    segment(d, j1, j2, 48 * k, 42 * k, col)
    segment(d, j2, tip, 42 * k, 34 * k, col)
    for j, w in ((j1, 48 * k), (j2, 42 * k)):
        d.arc((j[0] - w * 0.35, j[1] - w * 0.35, j[0] + w * 0.35, j[1] + w * 0.35), 200, 340, fill=shade(col, 0.78), width=4)
    # nail on the back of the last segment
    nx, ny = polar(tip, -24 * k, a3)
    ex, ey = polar((nx, ny), 0, 0)
    r = math.radians(a3)
    ox, oy = math.cos(r) * -10 * k, math.sin(r) * 10 * k
    d.ellipse((nx + ox - 14 * k, ny + oy - 9 * k, nx + ox + 14 * k, ny + oy + 9 * k), fill=NAIL, outline=NAIL_EDGE, width=3)


def frame(ph, idle=False, tap=False):
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    bob = 0 if idle else -14 * abs(math.sin(ph))
    o = DY + bob

    # far fingers first (they are partly hidden by the back of the hand)
    finger(d, (612, 468 + o), ph + math.pi, 0.80, shade(SKIN, 0.74), idle)          # little finger
    finger(d, (650, 486 + o), ph, 0.96, shade(SKIN, 0.82), idle)                   # ring finger
    finger(d, (684, 506 + o), ph + math.pi, 1.06, shade(SKIN, 0.90), idle)         # middle finger

    # back of the hand, slightly from above: wrist on the left, knuckles on the right
    body = [(430, 470 + o), (500, 444 + o), (580, 440 + o), (690, 462 + o), (735, 505 + o),
            (725, 560 + o), (620, 590 + o), (520, 590 + o), (430, 574 + o)]
    d.polygon([(x, y) for x, y in body], fill=LINE)
    inner = [(x + (6 if x < 560 else -6), y + (6 if y < 520 + o else -6)) for x, y in body]
    d.polygon(inner, fill=SKIN)
    d.ellipse((398, 462 + o, 466, 580 + o), fill=LINE)
    d.ellipse((404, 468 + o, 460, 574 + o), fill=shade(SKIN, 0.86))                 # cut wrist
    # light on the back of the hand, knuckle bumps, tendons
    d.line([(480, 470 + o), (680, 482 + o)], fill=SKIN_HI, width=26)
    for kx, ky in ((610, 452), (650, 466), (688, 486), (716, 512)):
        d.arc((kx - 26, ky + o - 18, kx + 26, ky + o + 18), 190, 350, fill=shade(SKIN, 0.82), width=4)
    for kx, ky in ((610, 458), (650, 472), (688, 492)):
        d.line([(490, 505 + o), (kx - 20, ky + o + 12)], fill=shade(SKIN, 0.92), width=5)
    # stitched scar around the wrist
    d.line([(476, 462 + o), (470, 586 + o)], fill=SCAR, width=7)
    for k in range(6):
        sy = 474 + k * 19 + o
        d.line([(462, sy), (486, sy + 7)], fill=SCAR, width=5)

    # thumb and index finger in front
    tb = (585, 582 + o)
    ta = 30 if idle else 30 + 16 * math.sin(ph + math.pi / 2)
    tj = polar(tb, 96, ta)
    tt = polar(tj, 80, ta - 30)
    segment(d, tb, tj, 58, 50, SKIN)
    segment(d, tj, tt, 50, 40, SKIN)
    finger(d, (712, 540 + o), ph, 1.0, SKIN, idle, tap)                             # index finger

    a = img.split()[3]
    halo = a.filter(ImageFilter.GaussianBlur(18)).point(lambda v: int(v * 0.45))
    out = Image.merge("RGBA", [Image.new("L", (N, N), c) for c in GLOW] + [halo])
    out.alpha_composite(img)
    return out.resize((OUT, OUT), Image.LANCZOS)


strip = Image.new("RGBA", (OUT * (FRAMES + 1), OUT), (0, 0, 0, 0))
for i in range(FRAMES):
    strip.paste(frame(2 * math.pi * i / FRAMES), (i * OUT, 0))
strip.paste(frame(0, idle=True, tap=True), (FRAMES * OUT, 0))
strip.save("src/hand.png")
print("saved src/hand.png", strip.size)
