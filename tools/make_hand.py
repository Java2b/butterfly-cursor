# Draws the built-in "helper hand": a pale hand that scuttles on its fingertips.
# Side view facing right, a strip of 9 square frames: 0-7 run cycle, 8 idle (standing, index finger tapping).
# Usage: python tools/make_hand.py
import math
from PIL import Image, ImageDraw, ImageFilter

N, OUT, FRAMES = 1024, 320, 8
SKIN = (238, 222, 206)
SKIN_DARK = (196, 176, 160)
NAIL = (250, 238, 230)
LINE = (70, 50, 45)
SCAR = (150, 60, 60)
GLOW = (255, 230, 200)


def polar(p, length, ang):
    r = math.radians(ang)                 # 0 = straight down, positive = forward (right)
    return (p[0] + length * math.sin(r), p[1] + length * math.cos(r))


def seg(d, a, b, w, col):
    for width, c in ((w + 12, LINE), (w, col)):
        d.line([a, b], fill=c, width=width)
        for p in (a, b):
            d.ellipse((p[0] - width / 2, p[1] - width / 2, p[0] + width / 2, p[1] + width / 2), fill=c)


def finger(d, base, ph, near, idle=False, tap=False):
    col = SKIN if near else SKIN_DARK
    if idle:
        a1, a2 = 66, -6
        if tap:
            a1, a2 = 100, 55              # raised index finger
    else:
        a1 = 66 + 16 * math.sin(ph)       # the arched finger swings back and forth
        lift = max(0.0, math.cos(ph))     # fingertip lifts while swinging forward
        a2 = -6 + 22 * math.sin(ph) + 32 * lift
    joint = polar(base, 150, a1)
    tip = polar(joint, 215, a2)
    seg(d, base, joint, 54, col)
    seg(d, joint, tip, 46, col)
    # fingernail at the tip
    nx, ny = polar(tip, -22, a2)
    d.ellipse((nx - 14, ny - 9, nx + 14, ny + 9), fill=NAIL, outline=LINE, width=4)


def frame(ph, idle=False, tap=False):
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    bob = 0 if idle else -16 * abs(math.sin(ph))
    y0 = 430 + bob
    knuckles = [(540, y0 + 80), (598, y0 + 80), (655, y0 + 76), (708, y0 + 66)]

    # far fingers (2 and 4) behind the hand
    finger(d, knuckles[1], ph + math.pi, False, idle)
    finger(d, knuckles[3], ph + math.pi, False, idle)
    # thumb on the far side, used as a fifth leg
    th_base = (470, y0 + 80)
    a = 10 + (0 if idle else 18 * math.sin(ph + math.pi / 2))
    tj = polar(th_base, 150, a - 10)
    tt = polar(tj, 150, a - 35)
    seg(d, th_base, tj, 56, SKIN_DARK)
    seg(d, tj, tt, 48, SKIN_DARK)

    # back of the hand (seen from the side) and the wrist with its stitched scar
    d.rounded_rectangle((300, y0 - 10, 735, y0 + 115), radius=62, fill=LINE)
    d.rounded_rectangle((306, y0 - 4, 729, y0 + 109), radius=56, fill=SKIN)
    d.line([(380, y0 + 12), (690, y0 + 20)], fill=(250, 238, 226), width=20)      # light on the knuckles
    for kx in (560, 610, 660, 705):
        d.arc((kx - 26, y0 - 2, kx + 26, y0 + 40), 200, 340, fill=SKIN_DARK, width=5)
    # wrist end
    d.ellipse((270, y0 - 6, 350, y0 + 111), fill=LINE)
    d.ellipse((276, y0, 344, y0 + 105), fill=SKIN_DARK)
    d.line([(352, y0 + 2), (342, y0 + 106)], fill=SCAR, width=8)
    for k in range(5):
        sy = y0 + 14 + k * 20
        d.line([(336, sy), (358, sy + 6)], fill=SCAR, width=5)

    # near fingers (1 and 3) in front
    finger(d, knuckles[0], ph, True, idle, tap)
    finger(d, knuckles[2], ph, True, idle)

    a = img.split()[3]
    halo = a.filter(ImageFilter.GaussianBlur(18)).point(lambda v: int(v * 0.5))
    out = Image.merge("RGBA", [Image.new("L", (N, N), c) for c in GLOW] + [halo])
    out.alpha_composite(img)
    return out.resize((OUT, OUT), Image.LANCZOS)


strip = Image.new("RGBA", (OUT * (FRAMES + 1), OUT), (0, 0, 0, 0))
for i in range(FRAMES):
    strip.paste(frame(2 * math.pi * i / FRAMES), (i * OUT, 0))
strip.paste(frame(0, idle=True, tap=True), (FRAMES * OUT, 0))
strip.save("src/hand.png")
print("saved src/hand.png", strip.size)
