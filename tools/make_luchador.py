# Draws the built-in luchador, an original masked wrestler ("Mariposa": blue mask, golden trim,
# white butterfly wings around the eyes, a golden butterfly on the forehead).
# Strip of 9 square frames: 0-7 side view run cycle (facing right), 8 front view flexing pose.
# Usage: python tools/make_luchador.py
import math
from PIL import Image, ImageDraw, ImageFilter

N, OUT, FRAMES = 1024, 320, 8
OUTLINE = (20, 18, 34)
SKIN = (226, 168, 122)
SKIN_LIGHT = (240, 192, 150)
MASK = (36, 78, 205)
MASK_LIGHT = (70, 120, 240)
GOLD = (246, 196, 58)
WHITE = (248, 248, 252)
EYE = (25, 22, 40)
TRUNKS = (32, 66, 180)
GLOW = (110, 170, 255)


def dark(c, k=0.72):
    return tuple(int(v * k) for v in c)


def polar(p, length, ang):
    r = math.radians(ang)                      # 0 = straight down, positive = forward (right)
    return (p[0] + length * math.sin(r), p[1] + length * math.cos(r))


def limb(d, a, b, w, col, ow=7):
    for width, c in ((w + 2 * ow, OUTLINE), (w, col)):
        d.line([a, b], fill=c, width=int(width))
        for p in (a, b):
            d.ellipse((p[0] - width / 2, p[1] - width / 2, p[0] + width / 2, p[1] + width / 2), fill=c)


def ell(d, cx, cy, rx, ry, col, ow=7):
    d.ellipse((cx - rx - ow, cy - ry - ow, cx + rx + ow, cy + ry + ow), fill=OUTLINE)
    d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=col)


def butterfly(d, cx, cy, s):
    """The golden butterfly emblem."""
    for sx in (-1, 1):
        d.polygon([(cx, cy), (cx + sx * 1.0 * s, cy - 0.8 * s), (cx + sx * 0.9 * s, cy + 0.1 * s)], fill=GOLD, outline=OUTLINE)
        d.polygon([(cx, cy), (cx + sx * 0.75 * s, cy + 0.2 * s), (cx + sx * 0.5 * s, cy + 0.75 * s)], fill=GOLD, outline=OUTLINE)
    d.line([(cx, cy - 0.5 * s), (cx, cy + 0.5 * s)], fill=OUTLINE, width=max(2, int(s * 0.18)))


def finish(img):
    a = img.split()[3]
    halo = a.filter(ImageFilter.GaussianBlur(18)).point(lambda v: int(v * 0.55))
    out = Image.merge("RGBA", [Image.new("L", (N, N), c) for c in GLOW] + [halo])
    out.alpha_composite(img)
    return out.resize((OUT, OUT), Image.LANCZOS)


def run_frame(ph):
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    bob = -20 * abs(math.sin(ph))
    hip = (480, 590 + bob)
    lean = 14
    shoulder = polar(hip, 230, 180 - lean)
    head = (shoulder[0] + 34, shoulder[1] - 100)

    def leg(p, near):
        col = SKIN if near else dark(SKIN)
        boot = WHITE if near else dark(WHITE, 0.8)
        thigh = 42 * math.sin(p)
        bend = 20 + 80 * (0.5 + 0.5 * math.cos(p - 0.9))
        knee = polar(hip, 190, thigh)
        ankle = polar(knee, 185, thigh - bend)
        mid = ((knee[0] + ankle[0]) / 2, (knee[1] + ankle[1]) / 2)
        toe = polar(ankle, 72, thigh - bend + 95)
        limb(d, hip, knee, 76, col)
        limb(d, knee, mid, 64, col)
        limb(d, mid, ankle, 66, boot)                 # high white wrestling boot
        limb(d, ankle, toe, 52, boot)
        d.line([mid, ankle], fill=GOLD, width=6)      # golden laces

    def arm(p, near):
        col = SKIN if near else dark(SKIN)
        upper = -50 * math.sin(p)                     # hangs down and swings opposite to the leg
        elbow = polar(shoulder, 150, upper)
        fist = polar(elbow, 135, upper + 100)         # bent elbow, fist pumping forward and up
        limb(d, shoulder, elbow, 58, col)
        limb(d, elbow, fist, 50, col)
        band = polar(elbow, 100, upper + 100)
        limb(d, band, fist, 54, GOLD if near else dark(GOLD))
        ell(d, fist[0], fist[1], 30, 30, col)

    # far side first
    arm(ph, False)
    leg(ph + math.pi, False)

    # torso: broad chest leaning forward, trunks with a golden stripe
    limb(d, hip, shoulder, 150, SKIN)
    chest = polar(shoulder, 70, -lean - 20)
    ell(d, chest[0] + 18, chest[1] + 10, 78, 70, SKIN_LIGHT, 0)
    ell(d, hip[0], hip[1] + 10, 92, 70, TRUNKS)
    d.line([(hip[0] - 85, hip[1] - 20), (hip[0] + 85, hip[1] - 30)], fill=GOLD, width=16)

    leg(ph, True)

    # head in profile: the blue mask leaves the chin and mouth bare
    hx, hy = head
    ell(d, hx, hy, 84, 88, MASK)
    d.pieslice((hx - 60, hy - 10, hx + 96, hy + 88), -10, 110, fill=SKIN)       # chin and mouth
    d.arc((hx - 84, hy - 88, hx + 84, hy + 88), 170, 330, fill=MASK_LIGHT, width=10)
    # white butterfly wing around the eye, golden edge
    wing = [(hx + 18, hy - 6), (hx + 70, hy - 48), (hx + 88, hy - 18), (hx + 70, hy + 8), (hx + 30, hy + 10)]
    d.polygon(wing, fill=WHITE, outline=GOLD, width=6)
    ell(d, hx + 60, hy - 14, 13, 10, EYE, 0)
    butterfly(d, hx + 30, hy - 62, 26)
    # mask laces fluttering behind
    for k, off in ((0, 0), (1, 18)):
        pts = [(hx - 78, hy - 8 + off)]
        for i in range(1, 4):
            pts.append((pts[0][0] - i * 42, pts[0][1] + 10 * i + 14 * math.sin(ph * 2 + i + k)))
        d.line(pts, fill=GOLD, width=10, joint="curve")

    arm(ph + math.pi, True)
    return finish(img)


def flex_frame():
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = N // 2

    # legs and boots
    for sx in (-1, 1):
        hip, knee, ankle = (cx + sx * 55, 650), (cx + sx * 95, 800), (cx + sx * 100, 950)
        limb(d, hip, knee, 86, SKIN)
        limb(d, knee, ((knee[0] + ankle[0]) / 2, 870), 72, SKIN)
        limb(d, (knee[0] + sx * 2, 870), ankle, 76, WHITE)
        d.line([(knee[0], 875), ankle], fill=GOLD, width=6)
    # trunks and the champion's belt with the butterfly plate
    d.rounded_rectangle((cx - 115 - 7, 590 - 7, cx + 115 + 7, 700 + 7), radius=40, fill=OUTLINE)
    d.rounded_rectangle((cx - 115, 590, cx + 115, 700), radius=36, fill=TRUNKS)
    d.rectangle((cx - 120, 585, cx + 120, 625), fill=GOLD, outline=OUTLINE, width=5)
    ell(d, cx, 605, 46, 34, GOLD, 5)
    butterfly(d, cx, 606, 26)

    # torso: V-shape with chest and abs
    torso = [(cx - 175, 395), (cx + 175, 395), (cx + 100, 600), (cx - 100, 600)]
    d.polygon([(x + (-8 if x < cx else 8), y - 8) for x, y in torso[:2]] + [(x + (8 if x > cx else -8), y + 8) for x, y in torso[2:]], fill=OUTLINE)
    d.polygon(torso, fill=SKIN)
    for sx in (-1, 1):
        d.chord((cx + (0 if sx > 0 else -150), 410, cx + (150 if sx > 0 else 0), 520), 0, 180, fill=SKIN_LIGHT)
    d.line([(cx, 420), (cx, 590)], fill=dark(SKIN, 0.85), width=5)
    for y in (530, 562):
        d.line([(cx - 50, y), (cx + 50, y)], fill=dark(SKIN, 0.85), width=4)

    # arms up in a double-biceps flex
    for sx in (-1, 1):
        shoulder, elbow, fist = (cx + sx * 165, 420), (cx + sx * 300, 410), (cx + sx * 285, 270)
        limb(d, shoulder, elbow, 72, SKIN)
        ell(d, cx + sx * 235, 392, 52, 34, SKIN_LIGHT, 0)            # biceps
        limb(d, elbow, fist, 60, SKIN)
        limb(d, ((elbow[0] + fist[0]) / 2 + sx * 2, 320), fist, 64, GOLD)
        ell(d, fist[0], fist[1] - 10, 38, 36, SKIN)

    # head, front view
    hx, hy = cx, 300
    ell(d, hx, hy - 10, 92, 100, MASK)
    d.chord((hx - 70, hy + 10, hx + 70, hy + 95), 0, 180, fill=SKIN)              # mouth and chin
    d.arc((hx - 40, hy + 40, hx + 40, hy + 70), 20, 160, fill=OUTLINE, width=6)    # confident grin
    for sx in (-1, 1):
        wing = [(hx + sx * 8, hy - 20), (hx + sx * 50, hy - 75), (hx + sx * 92, hy - 52),
                (hx + sx * 86, hy - 8), (hx + sx * 40, hy + 8)]
        d.polygon(wing, fill=WHITE, outline=GOLD, width=6)
        ell(d, hx + sx * 46, hy - 26, 16, 12, EYE, 0)
    butterfly(d, hx, hy - 88, 30)
    d.arc((hx - 92, hy - 110, hx + 92, hy + 90), 200, 250, fill=MASK_LIGHT, width=12)
    return finish(img)


strip = Image.new("RGBA", (OUT * (FRAMES + 1), OUT), (0, 0, 0, 0))
for i in range(FRAMES):
    strip.paste(run_frame(2 * math.pi * i / FRAMES), (i * OUT, 0))
strip.paste(flex_frame(), (FRAMES * OUT, 0))
strip.save("src/luchador.png")
print("saved src/luchador.png", strip.size)
