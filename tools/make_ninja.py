# Draws the built-in ninja: a side view (facing right) sprite strip of 9 square frames.
# Frames 0-7 are a Naruto-style run (leaning forward, arms and sword trailing behind),
# frame 8 is the idle pose. Usage: python tools/make_ninja.py
import math
from PIL import Image, ImageDraw, ImageFilter

N = 1024            # supersampled frame
OUT = 320
FRAMES = 8

BODY = (34, 38, 70)
BODY_LIGHT = (70, 80, 140)
OUTLINE = (8, 10, 24)
SKIN = (255, 214, 170)
SCARF = (230, 40, 70)
BAND = (60, 110, 220)
PLATE = (200, 215, 235)
BLADE = (215, 245, 255)
HILT = (120, 70, 40)
GLOW = (90, 170, 255)


def limb(d, a, b, w, col):
    d.line([a, b], fill=OUTLINE, width=w + 14)
    for p in (a, b):
        d.ellipse((p[0] - (w + 14) / 2, p[1] - (w + 14) / 2, p[0] + (w + 14) / 2, p[1] + (w + 14) / 2), fill=OUTLINE)
    d.line([a, b], fill=col, width=w)
    for p in (a, b):
        d.ellipse((p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2), fill=col)


def polar(p, length, ang):
    """Point at `length` from p; angle in degrees, 0 = straight down, positive = forward (right)."""
    r = math.radians(ang)
    return (p[0] + length * math.sin(r), p[1] + length * math.cos(r))


def frame(phase, idle=False):
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s = math.sin(phase)
    bob = 0 if idle else -22 * abs(math.sin(phase))
    hip = (470, 640 + bob)
    lean = 8 if idle else 52                  # torso angle from vertical, forward
    shoulder = polar(hip, 210, 180 - lean)
    neck = polar(shoulder, 40, 180 - lean)
    head = (neck[0] + (40 if not idle else 8), neck[1] - 62)

    # scarf trailing behind (drawn first, behind the body)
    pts = [neck]
    for i in range(1, 7):
        wave = 0 if idle else 26 * math.sin(phase * 2 + i * 0.9)
        pts.append((neck[0] - i * (70 if not idle else 18), neck[1] + i * (6 if not idle else 48) + wave))
    d.line(pts, fill=OUTLINE, width=52, joint="curve")
    d.line(pts, fill=SCARF, width=36, joint="curve")

    # far leg and far arm (darker)
    def leg(ph, col):
        if idle:
            thigh, bend = (6 if ph == 0 else -6), 4
        else:
            thigh = 42 * math.sin(ph)
            bend = 25 + 70 * (0.5 + 0.5 * math.cos(ph - 0.9))
        knee = polar(hip, 175, thigh)
        ankle = polar(knee, 175, thigh - bend)
        foot = polar(ankle, 60, thigh - bend + 95)
        limb(d, hip, knee, 52, col)
        limb(d, knee, ankle, 44, col)
        limb(d, ankle, foot, 34, col)

    dark = tuple(int(c * 0.7) for c in BODY)
    leg(0 if idle else phase + math.pi, dark)

    if idle:
        far_hand = polar(shoulder, 200, -12)
        limb(d, shoulder, far_hand, 36, dark)
    else:
        far_hand = polar(shoulder, 210, -100 + 6 * s)
        limb(d, shoulder, far_hand, 36, dark)

    # torso
    limb(d, hip, shoulder, 120, BODY)
    d.line([polar(hip, 10, 180 - lean), polar(shoulder, -10, 180 - lean)], fill=BODY_LIGHT, width=30)
    belt_a, belt_b = polar(hip, 30, 180 - lean + 90), polar(hip, 30, 180 - lean - 90)
    d.line([belt_a, belt_b], fill=SCARF, width=26)

    leg(1 if idle else phase, BODY)

    # head: hood, face slit, headband with tails
    r = 78
    d.ellipse((head[0] - r - 7, head[1] - r - 7, head[0] + r + 7, head[1] + r + 7), fill=OUTLINE)
    d.ellipse((head[0] - r, head[1] - r, head[0] + r, head[1] + r), fill=BODY)
    d.rounded_rectangle((head[0] - 10, head[1] - 22, head[0] + r - 6, head[1] + 14), radius=14, fill=SKIN)
    d.ellipse((head[0] + 36, head[1] - 12, head[0] + 54, head[1] + 4), fill=OUTLINE)
    d.line([(head[0] - r + 6, head[1] - 38), (head[0] + r - 4, head[1] - 34)], fill=BAND, width=26)
    d.rectangle((head[0] + 22, head[1] - 50, head[0] + 64, head[1] - 22), fill=PLATE, outline=OUTLINE, width=4)
    tail = [(head[0] - r + 6, head[1] - 38)]
    for i in range(1, 4):
        wave = 0 if idle else 18 * math.sin(phase * 2 + i)
        tail.append((tail[0][0] - i * (50 if not idle else 16), tail[0][1] + i * (4 if not idle else 30) + wave))
    d.line(tail, fill=BAND, width=18, joint="curve")

    # near arm holding the katana
    if idle:
        hand = polar(shoulder, 200, 20)
        blade_dir = 160                     # blade pointing up and back, resting on the shoulder
    else:
        hand = polar(shoulder, 215, -112 - 6 * s)
        blade_dir = -118                    # blade trailing behind, slightly raised
    limb(d, shoulder, hand, 40, BODY)
    tip = polar(hand, 390, blade_dir)
    guard_a, guard_b = polar(hand, 26, blade_dir + 90), polar(hand, 26, blade_dir - 90)
    pommel = polar(hand, -70, blade_dir)

    glow = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    ImageDraw.Draw(glow).line([hand, tip], fill=GLOW + (255,), width=40)
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(16)))
    d = ImageDraw.Draw(img)
    d.line([hand, tip], fill=OUTLINE, width=26)
    d.line([hand, tip], fill=BLADE, width=14)
    d.line([pommel, hand], fill=OUTLINE, width=30)
    d.line([pommel, hand], fill=HILT, width=18)
    d.line([guard_a, guard_b], fill=OUTLINE, width=18)
    d.ellipse((hand[0] - 24, hand[1] - 24, hand[0] + 24, hand[1] + 24), fill=SKIN, outline=OUTLINE, width=6)

    # soft blue rim glow around the whole figure, like the other creatures
    a = img.split()[3]
    halo = a.filter(ImageFilter.GaussianBlur(20)).point(lambda v: int(v * 0.6))
    out = Image.merge("RGBA", [Image.new("L", (N, N), c) for c in GLOW] + [halo])
    out.alpha_composite(img)
    return out.resize((OUT, OUT), Image.LANCZOS)


strip = Image.new("RGBA", (OUT * (FRAMES + 1), OUT), (0, 0, 0, 0))
for i in range(FRAMES):
    strip.paste(frame(2 * math.pi * i / FRAMES), (i * OUT, 0))
strip.paste(frame(0, idle=True), (FRAMES * OUT, 0))
strip.save("src/ninja.png")
print("saved src/ninja.png", strip.size)
