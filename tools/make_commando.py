# Draws the built-in pixel-art commando (an original 8-bit style run-and-gun hero:
# red bandana, bare torso with a bandolier, green fatigues, a big rifle).
# Drawn on a 40x40 pixel grid and scaled 8x with nearest neighbour, so the pixels stay sharp.
# Strip of 10 square frames: 0-5 run cycle (facing right), 6 standing, 7-8 firing, 9 blinking.
# Usage: python tools/make_commando.py
from PIL import Image, ImageDraw, ImageFilter

G, SCALE = 40, 8
OUT = G * SCALE
OUTLINE = (16, 14, 26, 255)
SKIN = (222, 150, 100, 255)
SKIN_D = (170, 100, 66, 255)
SKIN_L = (246, 190, 140, 255)
HAIR = (40, 30, 30, 255)
BAND = (220, 40, 44, 255)
BAND_D = (150, 22, 30, 255)
PANTS = (70, 110, 60, 255)
PANTS_D = (44, 74, 40, 255)
BOOT = (50, 40, 36, 255)
BELT = (120, 80, 40, 255)
BUCKLE = (240, 200, 70, 255)
GUN = (90, 96, 110, 255)
GUN_D = (50, 54, 66, 255)
GUN_L = (170, 178, 196, 255)
EYE = (20, 20, 30, 255)
FLASH = (255, 230, 90, 255)
FLASH_W = (255, 255, 230, 255)
GLOW = (255, 120, 80)


def px(d, x, y, c):
    d.point((x, y), fill=c)


def rect(d, x0, y0, x1, y1, c):
    d.rectangle((x0, y0, x1, y1), fill=c)


def line(d, a, b, c, w=1):
    d.line([a, b], fill=c, width=w)


def leg(d, hip, knee, foot, back):
    col, dark = (PANTS_D, PANTS_D) if back else (PANTS, PANTS_D)
    line(d, hip, knee, col, 3)
    line(d, knee, (foot[0], foot[1] - 2), col, 3)
    # boot: a little block pointing forward
    fx, fy = foot
    rect(d, fx - 1, fy - 2, fx + 2, fy, BOOT if not back else (36, 28, 26, 255))
    px(d, knee[0], knee[1], dark)


def head(d, x, y, tail, blink=False):
    """Head at top-left (x, y), facing right; tail = bandana tail offset for waving."""
    rect(d, x, y, x + 6, y + 7, SKIN)
    rect(d, x, y, x + 6, y + 1, HAIR)            # hair
    rect(d, x, y + 2, x + 6, y + 3, BAND)        # bandana
    px(d, x, y + 3, BAND_D)
    rect(d, x, y + 4, x + 1, y + 5, HAIR)        # hair at the back
    px(d, x + 5, y + 4, SKIN_D if blink else EYE)  # eye
    px(d, x + 4, y + 4, SKIN_L)
    px(d, x + 7, y + 5, SKIN)                    # nose
    rect(d, x + 3, y + 7, x + 6, y + 7, SKIN_D)  # jaw shadow
    px(d, x + 5, y + 6, SKIN_D)                  # mouth
    # bandana knot and two tails flying back
    px(d, x - 1, y + 3, BAND)
    line(d, (x - 1, y + 3), (x - 4, y + 2 + tail), BAND)
    line(d, (x - 1, y + 4), (x - 5, y + 5 + tail), BAND_D)


def torso(d, x, y):
    """Torso with top-left at (x, y): 7 wide, 9 tall, then the belt."""
    rect(d, x, y, x + 6, y + 8, SKIN)
    rect(d, x, y, x + 1, y + 8, SKIN_D)          # back shading
    rect(d, x + 4, y + 2, x + 6, y + 3, SKIN_L)  # chest light
    px(d, x + 5, y + 5, SKIN_D)                  # abs
    px(d, x + 5, y + 7, SKIN_D)
    for i in range(9):                           # bandolier over the shoulder
        px(d, x + 1 + i * 6 // 9, y + i, BELT)
        if i % 2 == 0:
            px(d, x + 2 + i * 6 // 9, y + i, BUCKLE)
    rect(d, x, y + 9, x + 6, y + 10, BELT)       # belt
    px(d, x + 5, y + 9, BUCKLE)
    px(d, x + 5, y + 10, BUCKLE)


def rifle(d, x, y, up=False):
    """Rifle with the grip at (x, y); level, or pointing up over the shoulder."""
    if not up:
        rect(d, x - 4, y - 1, x + 11, y, GUN)           # body + barrel
        rect(d, x - 4, y + 1, x - 2, y + 2, GUN_D)      # stock
        rect(d, x, y + 1, x + 1, y + 3, GUN_D)          # grip
        rect(d, x + 4, y + 1, x + 5, y + 4, GUN_D)      # magazine
        line(d, (x - 3, y - 1), (x + 10, y - 1), GUN_L)  # highlight
        rect(d, x + 12, y - 1, x + 13, y - 1, GUN_D)    # muzzle
    else:
        for i in range(12):                              # diagonal, barrel up-back
            px(d, x - i // 2, y - i, GUN)
            px(d, x - i // 2 + 1, y - i, GUN_D if i % 3 else GUN_L)
        rect(d, x, y + 1, x + 2, y + 2, GUN_D)


def arm(d, shoulder, hand, back=False):
    c = SKIN_D if back else SKIN
    line(d, shoulder, hand, c, 2)
    rect(d, hand[0], hand[1], hand[0] + 1, hand[1] + 1, SKIN_D if back else SKIN)


def outline(img):
    """One-pixel dark outline around everything opaque (classic sprite look)."""
    src = img.load()
    out = img.copy()
    o = out.load()
    for y in range(G):
        for x in range(G):
            if src[x, y][3]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < G and 0 <= ny < G and src[nx, ny][3]:
                    o[x, y] = OUTLINE
                    break
    return out


def finish(img):
    img = outline(img).resize((OUT, OUT), Image.NEAREST)
    a = img.split()[3]
    halo = a.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.45))
    out = Image.merge("RGBA", [Image.new("L", (OUT, OUT), c) for c in GLOW] + [halo])
    out.alpha_composite(img)
    return out


# run cycle: (back leg knee, foot), (front leg knee, foot) relative to the hip, plus body bob
RUN = [
    ((-3, 4), (-6, 9), (3, 3), (6, 8), 0),
    ((-1, 4), (-3, 10), (2, 4), (3, 10), 1),
    ((1, 4), (0, 10), (0, 4), (-1, 10), 0),
    ((3, 3), (6, 8), (-3, 4), (-6, 9), 0),
    ((2, 4), (3, 10), (-1, 4), (-3, 10), 1),
    ((0, 4), (-1, 10), (1, 4), (0, 10), 0),
]


def body(d, bob, legs, tail, gun="level", lean=0, blink=False):
    hx, hy = 18 + lean, 26 + bob                  # hip
    (bk, bf, fk, ff) = legs
    leg(d, (hx, hy), (hx + bk[0], hy + bk[1]), (hx + bf[0], hy + bf[1]), True)
    tx, ty = 15 + lean, 15 + bob
    if gun == "up":
        arm(d, (tx + 1, ty + 1), (tx + 3, ty + 5), back=True)
    torso(d, tx, ty)
    leg(d, (hx + 1, hy), (hx + 1 + fk[0], hy + fk[1]), (hx + 1 + ff[0], hy + ff[1]), False)
    head(d, 16 + lean, 6 + bob, tail, blink)
    if gun == "up":
        rifle(d, tx + 3, ty + 4, up=True)
        arm(d, (tx + 5, ty + 1), (tx + 3, ty + 3))
    else:
        gx, gy = tx + 6, ty + 5
        arm(d, (tx + 1, ty + 1), (gx + 4, gy), back=True)   # support hand under the barrel
        rifle(d, gx, gy)
        arm(d, (tx + 5, ty + 1), (gx, gy + 1))              # trigger hand
    return tx + 6 + 14, ty + 4                               # muzzle tip


def frame(kind, i=0):
    img = Image.new("RGBA", (G, G), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    stand = ((-1, 5), (-2, 11), (1, 5), (2, 11))
    if kind == "run":
        bk, bf, fk, ff, bob = RUN[i]
        body(d, bob, (bk, bf, fk, ff), tail=(i % 3) - 1)
    elif kind == "stand":
        body(d, 0, stand, tail=1)
    elif kind == "fire":
        mx, my = body(d, 0, stand, tail=0, lean=-1 if i else 0)
        if i == 0:
            rect(d, mx, my - 2, mx + 2, my + 2, FLASH)
            rect(d, mx + 3, my - 1, mx + 4, my + 1, FLASH)
            px(d, mx + 1, my, FLASH_W)
            px(d, mx + 2, my, FLASH_W)
        else:
            px(d, 22, 15, BUCKLE)                     # an ejected shell
    elif kind == "blink":
        body(d, 0, stand, tail=1, blink=True)
    return finish(img)


def main():
    frames = [frame("run", i) for i in range(6)]
    frames += [frame("stand"), frame("fire", 0), frame("fire", 1), frame("blink")]
    strip = Image.new("RGBA", (OUT * len(frames), OUT), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        strip.paste(f, (i * OUT, 0))
    strip.save("src/commando.png")
    print("src/commando.png", strip.size)


if __name__ == "__main__":
    main()
