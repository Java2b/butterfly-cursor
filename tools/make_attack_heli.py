# Draws the original attack helicopter (smooth, not pixel art): slim olive body, two seats one behind the other,
# stub wings with a rocket pod and missiles, a chin gun, wheels.
# Strip of 6 square 320 px frames: 0-3 flying (main and tail rotor turn), 4-5 landed (rotor turning slowly).
# Drawn at 1024 px and scaled down for smooth edges.
# Usage: python tools/make_attack_heli.py
import math
from PIL import Image, ImageDraw, ImageFilter, ImageChops

N, OUT = 1024, 320
OUTLINE = (20, 22, 16, 255)
OLIVE_L = (132, 146, 88)
OLIVE = (90, 102, 58)
OLIVE_D = (54, 62, 34)
GLASS_T = (150, 200, 225)
GLASS_B = (50, 84, 104)
METAL = (66, 70, 76)
METAL_L = (140, 146, 156)
TIRE = (30, 30, 32)
GLOW = (170, 200, 120)


def gradient(top, bottom, y0=0, y1=N):
    g = Image.new("RGBA", (N, N))
    d = ImageDraw.Draw(g)
    for y in range(N):
        t = min(1.0, max(0.0, (y - y0) / max(1, y1 - y0)))
        d.line([(0, y), (N, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(top, bottom)) + (255,))
    return g


def shape(draw_fn):
    m = Image.new("L", (N, N), 0)
    draw_fn(ImageDraw.Draw(m))
    return m


def put(canvas, mask, top, bottom, y0, y1, ow=7):
    """Paints a part: dark outline around it, filled with a vertical gradient."""
    ring = mask.filter(ImageFilter.MaxFilter(ow * 2 + 1))
    canvas.paste(Image.new("RGBA", (N, N), OUTLINE), (0, 0), ring)
    canvas.paste(gradient(top, bottom, y0, y1), (0, 0), mask)


def heli(frame, landed=False):
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    dy = 30 if landed else 0

    # tail fin and tail rotor (behind the boom)
    fin = shape(lambda m: m.polygon([(40, 300 + dy), (112, 296 + dy), (150, 470 + dy), (78, 482 + dy)], fill=255))
    put(img, fin, OLIVE_L, OLIVE_D, 300 + dy, 480 + dy)
    hub = (92, 380 + dy)
    if not landed:
        d.ellipse((hub[0] - 78, hub[1] - 78, hub[0] + 78, hub[1] + 78), fill=(170, 176, 190, 70))
    a = math.radians(frame * 50)
    for k in (0, 1):
        ang = a + k * math.pi / 2
        ex, ey = math.cos(ang) * 74, math.sin(ang) * 74
        d.line([(hub[0] - ex, hub[1] - ey), (hub[0] + ex, hub[1] + ey)], fill=METAL + (255,), width=9)
    d.ellipse((hub[0] - 13, hub[1] - 13, hub[0] + 13, hub[1] + 13), fill=METAL_L + (255,), outline=OUTLINE, width=4)

    # tail boom
    boom = shape(lambda m: m.polygon([(110, 430 + dy), (380, 410 + dy), (390, 520 + dy), (110, 470 + dy)], fill=255))
    put(img, boom, OLIVE_L, OLIVE_D, 410 + dy, 520 + dy)
    stab = shape(lambda m: m.polygon([(96, 470 + dy), (196, 462 + dy), (200, 484 + dy), (100, 492 + dy)], fill=255))
    put(img, stab, OLIVE, OLIVE_D, 460 + dy, 492 + dy, 5)

    # engines on top, with exhausts
    eng = shape(lambda m: m.rounded_rectangle((330, 296 + dy, 610, 362 + dy), radius=30, fill=255))
    put(img, eng, OLIVE_L, OLIVE_D, 296 + dy, 362 + dy)
    for ex in (300,):
        d.rounded_rectangle((ex, 312 + dy, ex + 50, 344 + dy), radius=10, fill=METAL + (255,), outline=OUTLINE, width=5)

    # body: slim, nose pointing right
    body_pts = [(330, 400), (470, 362), (600, 352), (720, 372), (830, 440), (890, 512), (884, 566), (800, 600),
                (640, 612), (460, 612), (350, 580), (318, 500)]
    body = shape(lambda m: m.polygon([(x, y + dy) for x, y in body_pts], fill=255))
    body = body.filter(ImageFilter.GaussianBlur(6)).point(lambda v: 255 if v > 128 else 0)   # round the corners
    put(img, body, OLIVE_L, OLIVE_D, 360 + dy, 612 + dy)
    d.line([(360, 560 + dy), (860, 560 + dy)], fill=OLIVE_D + (255,), width=6)               # panel line
    d.line([(470, 380 + dy), (470, 600 + dy)], fill=OLIVE_D + (255,), width=5)
    d.ellipse((380, 452 + dy, 404, 476 + dy), fill=OLIVE_D + (255,))                          # a hatch
    d.line([(350, 410 + dy), (590, 372 + dy)], fill=OLIVE_L + (255,), width=6)               # light along the top

    # canopies: the pilot sits higher at the back, the gunner lower in front
    for pts in ([(560, 360), (640, 316), (716, 338), (722, 404), (560, 410)],
                [(724, 394), (796, 362), (856, 444), (846, 476), (724, 470)]):
        glass = shape(lambda m, p=pts: m.polygon([(x, y + dy) for x, y in p], fill=255))
        put(img, glass, GLASS_T, GLASS_B, min(y for _, y in pts) + dy, max(y for _, y in pts) + dy, 6)
    d.line([(600, 352 + dy), (660, 330 + dy)], fill=(235, 248, 255, 200), width=7)          # reflections
    d.line([(760, 392 + dy), (800, 376 + dy)], fill=(235, 248, 255, 200), width=6)

    # stub wing with a rocket pod and two missiles
    wing = shape(lambda m: m.polygon([(430, 552 + dy), (650, 548 + dy), (660, 578 + dy), (440, 584 + dy)], fill=255))
    put(img, wing, OLIVE, OLIVE_D, 548 + dy, 584 + dy, 6)
    pod = shape(lambda m: m.rounded_rectangle((440, 600 + dy, 572, 650 + dy), radius=24, fill=255))
    put(img, pod, OLIVE, OLIVE_D, 600 + dy, 650 + dy, 6)
    d.line([(500, 584 + dy), (500, 600 + dy)], fill=OUTLINE, width=8)
    for k, mx in enumerate((588, 588)):
        y = 598 + k * 26 + dy
        d.rounded_rectangle((mx, y, mx + 110, y + 18), radius=9, fill=METAL_L + (255,), outline=OUTLINE, width=4)
        d.polygon([(mx + 110, y + 2), (mx + 128, y + 9), (mx + 110, y + 16)], fill=(200, 60, 50, 255), outline=OUTLINE)
    d.line([(620, 584 + dy), (620, 598 + dy)], fill=OUTLINE, width=8)

    # chin gun
    d.ellipse((770, 580 + dy, 836, 640 + dy), fill=METAL + (255,), outline=OUTLINE, width=6)
    d.line([(820, 614 + dy), (950, 622 + dy)], fill=OUTLINE, width=18)
    d.line([(820, 614 + dy), (946, 621 + dy)], fill=METAL_L + (255,), width=8)

    # wheels
    for (sx, sy, wx, wy, r) in ((540, 612, 520, 770, 42), (760, 604, 780, 770, 40), (150, 480, 156, 548, 22)):
        d.line([(sx, sy + dy), (wx, wy + dy)], fill=OUTLINE, width=18)
        d.line([(sx, sy + dy), (wx, wy + dy)], fill=METAL_L + (255,), width=8)
        d.ellipse((wx - r - 6, wy - r - 6 + dy, wx + r + 6, wy + r + 6 + dy), fill=OUTLINE)
        d.ellipse((wx - r, wy - r + dy, wx + r, wy + r + dy), fill=TIRE + (255,))
        d.ellipse((wx - r * 0.4, wy - r * 0.4 + dy, wx + r * 0.4, wy + r * 0.4 + dy), fill=METAL_L + (255,))

    # main rotor: the blur of the disc while flying, two blades seen from the side
    hubx, huby = 470, 262 + dy
    d.rectangle((hubx - 14, huby, hubx + 14, 300 + dy), fill=METAL + (255,), outline=OUTLINE, width=5)
    if not landed:
        d.ellipse((30, huby - 16, 960, huby + 16), fill=(170, 176, 190, 80))
    a = math.radians(frame * (45 if not landed else 30))
    for k in (0, 1):
        L = abs(math.cos(a + k * math.pi / 2)) * 470
        d.line([(hubx - L, huby), (hubx + L, huby)], fill=OUTLINE, width=16)
        d.line([(hubx - L, huby), (hubx + L, huby)], fill=METAL + (255,), width=7)
    d.ellipse((hubx - 22, huby - 18, hubx + 22, huby + 18), fill=METAL_L + (255,), outline=OUTLINE, width=5)
    return img


def finish(img):
    small = img.resize((OUT, OUT), Image.LANCZOS)
    a = small.split()[3]
    halo = a.filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.4))
    out = Image.merge("RGBA", [Image.new("L", (OUT, OUT), c) for c in GLOW] + [halo])
    out.alpha_composite(small)
    return out


def main():
    frames = [finish(heli(i)) for i in range(4)] + [finish(heli(0, True)), finish(heli(1, True))]
    strip = Image.new("RGBA", (OUT * len(frames), OUT), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        strip.paste(f, (i * OUT, 0))
    strip.save("src/attack_heli.png")
    print("src/attack_heli.png", strip.size)


if __name__ == "__main__":
    main()
