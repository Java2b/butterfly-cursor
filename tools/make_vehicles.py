# Draws two original pixel-art vehicles on a 40x40 grid, scaled 8x with nearest neighbour.
#   biker.png       4 riding frames (wheels turn, rider bobs, exhaust puffs) + 3 resting frames
#                   (parked on the kickstand: sitting, waving, revving with a puff of smoke)
#   helicopter.png  4 flying frames (main and tail rotor turn) + 2 landed frames (rotor turning slowly)
# Usage: python tools/make_vehicles.py
import math
from PIL import Image, ImageDraw, ImageFilter

G, SCALE = 40, 8
OUT = G * SCALE
OUTLINE = (16, 14, 26, 255)


def px(d, x, y, c):
    d.point((int(round(x)), int(round(y))), fill=c)


def rect(d, x0, y0, x1, y1, c):
    d.rectangle((x0, y0, x1, y1), fill=c)


def line(d, a, b, c, w=1):
    d.line([a, b], fill=c, width=w)


def outline(img, skip=()):
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


def finish(img, glow, skip=()):
    img = outline(img, skip).resize((OUT, OUT), Image.NEAREST)
    a = img.split()[3]
    halo = a.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.45))
    out = Image.merge("RGBA", [Image.new("L", (OUT, OUT), c) for c in glow] + [halo])
    out.alpha_composite(img)
    return out


# ------------------------------------------------------------------ biker
TIRE = (34, 32, 40, 255)
RIM = (150, 156, 170, 255)
CHROME = (205, 212, 226, 255)
CHROME_D = (120, 126, 140, 255)
PAINT = (232, 92, 30, 255)       # orange tank
PAINT_D = (160, 52, 18, 255)
PAINT_L = (255, 160, 90, 255)
SEAT = (40, 34, 34, 255)
ENGINE = (90, 94, 104, 255)
LIGHT = (255, 236, 120, 255)
JACKET = (96, 58, 40, 255)      # brown leather
JACKET_L = (150, 96, 64, 255)
JEANS = (52, 84, 150, 255)
JEANS_D = (34, 56, 104, 255)
HELMET = (200, 30, 40, 255)
HELMET_L = (255, 90, 90, 255)
VISOR = (30, 30, 44, 255)
VISOR_L = (120, 170, 220, 255)
SKIN = (222, 160, 112, 255)
BOOT = (30, 24, 22, 255)
SMOKE = (170, 170, 180, 200)
SMOKE_L = (210, 210, 220, 160)


def wheel(d, cx, cy, ang):
    d.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), fill=TIRE)
    d.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), fill=RIM)
    d.ellipse((cx - 3, cy - 3, cx + 3, cy + 3), fill=TIRE)
    for k in range(4):                                   # spokes
        a = ang + k * math.pi / 2
        px(d, cx + math.cos(a) * 2, cy + math.sin(a) * 2, RIM)
        px(d, cx + math.cos(a) * 3, cy + math.sin(a) * 3, RIM)
    rect(d, cx - 1, cy - 1, cx + 1, cy + 1, CHROME)     # hub
    px(d, cx - 4, cy - 5, (70, 68, 80, 255))             # tyre shine


def bike(d, bob, ang, stand=False):
    rw, fw = (9, 32), (31, 32)
    wheel(d, rw[0], rw[1], ang)
    wheel(d, fw[0], fw[1], ang)
    # rear fender and swing arm
    line(d, (4, 25), (12, 24), PAINT_D, 2)
    line(d, (9, 32), (17, 28), CHROME_D, 2)
    # exhaust
    line(d, (13, 30), (3, 29), CHROME, 2)
    px(d, 2, 29, CHROME_D); px(d, 2, 28, CHROME_D)
    # engine block
    rect(d, 15, 26, 23, 31, ENGINE)
    rect(d, 16, 27, 17, 30, CHROME_D)
    rect(d, 20, 27, 22, 28, CHROME)
    # tank and seat
    d.polygon([(14, 22 + bob), (25, 20 + bob), (27, 24 + bob), (15, 26 + bob)], fill=PAINT)
    line(d, (16, 22 + bob), (24, 21 + bob), PAINT_L)
    line(d, (16, 25 + bob), (26, 24 + bob), PAINT_D)
    rect(d, 8, 22 + bob, 15, 23 + bob, SEAT)
    # front fork, headlight, handlebar
    line(d, (31, 32), (27, 18 + bob), CHROME, 2)
    rect(d, 28, 20 + bob, 30, 22 + bob, CHROME_D)
    rect(d, 30, 20 + bob, 31, 22 + bob, LIGHT)
    line(d, (25, 17 + bob), (28, 16 + bob), CHROME_D)
    line(d, (26, 27), (33, 25), PAINT_D, 2)              # front fender
    if stand:
        line(d, (16, 31), (13, 37), CHROME_D)            # kickstand


def rider(d, bob, pose="ride"):
    lean = 0 if pose != "ride" else 1
    # leg: hip -> knee -> foot peg
    line(d, (13, 21 + bob), (19, 24 + bob), JEANS, 3)
    line(d, (19, 24 + bob), (17, 30), JEANS_D, 2)
    rect(d, 16, 30, 19, 31, BOOT)
    # torso (leaning forward when riding)
    hx, hy = (12, 21 + bob)
    sx, sy = (16 + 2 * lean, 13 + bob + lean)
    d.polygon([(hx - 3, hy), (hx + 3, hy), (sx + 4, sy), (sx - 2, sy)], fill=JACKET)
    line(d, (hx + 2, hy - 1), (sx + 2, sy + 1), JACKET_L)
    # arm
    if pose == "wave":
        line(d, (sx + 2, sy + 1), (sx + 7, sy - 1), JACKET, 2)
        line(d, (sx + 7, sy - 1), (sx + 9, sy - 6), JACKET, 2)
        rect(d, sx + 8, sy - 9, sx + 10, sy - 7, SKIN)
    else:
        line(d, (sx + 1, sy + 1), (sx + 6, sy + 3), JACKET, 2)
        line(d, (sx + 6, sy + 3), (25, 17 + bob), JACKET, 2)
        rect(d, 25, 16 + bob, 26, 17 + bob, BOOT)       # glove
    # helmet
    hx0, hy0 = sx - 2, sy - 8
    d.ellipse((hx0, hy0, hx0 + 8, hy0 + 8), fill=HELMET)
    rect(d, hx0 + 4, hy0 + 3, hx0 + 8, hy0 + 5, VISOR)
    px(d, hx0 + 6, hy0 + 3, VISOR_L)
    line(d, (hx0 + 1, hy0 + 2), (hx0 + 3, hy0 + 1), HELMET_L)
    line(d, (hx0, hy0 + 5), (hx0 + 3, hy0 + 8), (240, 240, 240, 255))   # white stripe


def puff(d, x, y, big):
    if big:
        d.ellipse((x - 3, y - 2, x + 1, y + 2), fill=SMOKE)
        d.ellipse((x - 6, y - 4, x - 3, y - 1), fill=SMOKE_L)
    else:
        d.ellipse((x - 2, y - 1, x, y + 1), fill=SMOKE_L)


def biker_frame(kind, i=0):
    img = Image.new("RGBA", (G, G), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if kind == "ride":
        bob = 1 if i % 2 else 0
        bike(d, bob, i * math.pi / 8)
        rider(d, bob)
        puff(d, 1, 28 - (i % 2), i % 2 == 0)
    else:
        bike(d, 0, 0, stand=True)
        rider(d, 0, "wave" if kind == "wave" else "sit")
        if kind == "rev":
            puff(d, 1, 28, True)
    return finish(img, (255, 140, 60), skip=(SMOKE, SMOKE_L))


# ------------------------------------------------------------------ helicopter
BODY = (214, 40, 46, 255)        # red helicopter
BODY_D = (150, 22, 30, 255)
BODY_L = (250, 110, 110, 255)
WHITE = (240, 240, 246, 255)
GLASS = (110, 190, 240, 255)
GLASS_L = (210, 240, 255, 255)
GLASS_D = (50, 110, 170, 255)
METAL = (90, 94, 108, 255)
METAL_L = (160, 166, 180, 255)
BLADE = (60, 60, 72, 255)
BLUR = (170, 176, 196, 140)


def heli(d, i, landed=False, slow=False):
    y = 2 if landed else 0
    # tail boom and fin
    d.polygon([(4, 15 + y), (16, 17 + y), (16, 21 + y), (5, 18 + y)], fill=BODY)
    line(d, (6, 18 + y), (15, 20 + y), BODY_D)
    d.polygon([(2, 10 + y), (5, 10 + y), (7, 16 + y), (4, 18 + y)], fill=BODY)
    px(d, 3, 11 + y, BODY_L)
    # tail rotor: a spinning disc, a blade in two positions
    if i % 2 == 0:
        line(d, (3, 11 + y), (3, 17 + y), BLADE)
    else:
        line(d, (0, 14 + y), (6, 14 + y), BLADE)
    rect(d, 2, 13 + y, 4, 15 + y, METAL)
    # cabin
    d.ellipse((13, 13 + y, 35, 29 + y), fill=BODY)
    rect(d, 14, 22 + y, 33, 27 + y, BODY)
    line(d, (15, 24 + y), (33, 24 + y), WHITE, 2)          # white stripe
    line(d, (15, 27 + y), (32, 27 + y), BODY_D)
    px(d, 18, 16 + y, BODY_L); px(d, 19, 15 + y, BODY_L)
    # cockpit glass
    d.pieslice((22, 13 + y, 36, 27 + y), 270, 360, fill=GLASS)
    rect(d, 29, 20 + y, 35, 22 + y, GLASS)
    line(d, (30, 15 + y), (33, 18 + y), GLASS_L)
    line(d, (29, 14 + y), (29, 22 + y), GLASS_D)
    # side window and door
    rect(d, 20, 16 + y, 25, 20 + y, GLASS)
    px(d, 21, 17 + y, GLASS_L)
    line(d, (19, 15 + y), (19, 26 + y), BODY_D)
    # engine hump, mast
    rect(d, 17, 10 + y, 28, 13 + y, BODY_D)
    rect(d, 18, 10 + y, 27, 11 + y, BODY)
    rect(d, 22, 8 + y, 23, 9 + y, METAL)
    # skids
    line(d, (18, 29 + y), (17, 32 + y), METAL)
    line(d, (30, 29 + y), (31, 32 + y), METAL)
    line(d, (13, 33 + y), (35, 33 + y), METAL_L)
    px(d, 36, 32 + y, METAL_L)
    # main rotor: seen from the side the blades sweep from long to short
    lengths = [17, 9, 3, 11] if not slow else [17, 12]
    L = lengths[i % len(lengths)]
    if not slow:
        line(d, (5, 7 + y), (39, 7 + y), BLUR)              # the blur of the spinning disc
    line(d, (22 - L, 7 + y), (23 + L, 7 + y), BLADE)
    rect(d, 21, 7 + y, 24, 8 + y, METAL)


def heli_frame(i, landed=False):
    img = Image.new("RGBA", (G, G), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    heli(d, i, landed, slow=landed)
    return finish(img, (255, 110, 100), skip=(BLUR,))


def strip(frames, path):
    s = Image.new("RGBA", (OUT * len(frames), OUT), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        s.paste(f, (i * OUT, 0))
    s.save(path)
    print(path, s.size)


if __name__ == "__main__":
    strip([biker_frame("ride", i) for i in range(4)] + [biker_frame("sit"), biker_frame("wave"), biker_frame("rev")],
          "src/biker.png")
    strip([heli_frame(i) for i in range(4)] + [heli_frame(0, True), heli_frame(1, True)], "src/helicopter.png")
