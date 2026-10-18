# Builds the pixel-art baby elephant and the fox from CC0 sprites (see THIRD-PARTY-NOTICES.md).
#   elephant.png  6 walking frames (drawn here in the style of the original) + sit, sit blinking, sit trunk up
#                 base: "pixel art elephant" by zonked, CC0 (tools/assets/elephant_sit_zonked_cc0.png)
#   fox.png       6 running frames + 6 idle frames, mirrored to face right
#                 source: "Animated Wild Animals" by ScratchIO, CC0 (tools/assets/fox_*_scratchio_cc0.png)
# Frames are square and scaled with nearest neighbour so the pixels stay sharp.
# Usage: python tools/make_pixel_animals.py
import math
from PIL import Image, ImageFilter

OUT = 320
A = (39, 0, 98, 255)        # outline
B = (138, 133, 164, 255)    # body
C = (76, 106, 131, 255)     # shading
H = (109, 103, 138, 255)    # far side, darker
F = (214, 203, 186, 255)    # toes, tusk
G = (191, 177, 156, 255)
E = (255, 130, 130, 255)    # blush


class Layer:
    def __init__(self, n=32):
        self.n = n
        self.img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
        self.p = self.img.load()

    def put(self, x, y, c):
        if 0 <= x < self.n and 0 <= y < self.n:
            self.p[x, y] = c

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.put(x, y, c)

    def ellipse(self, x0, y0, x1, y1, c):
        cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2 + 0.5, (y1 - y0) / 2 + 0.5
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                    self.put(x, y, c)

    def outlined(self, top=True):
        """A copy with a one-pixel outline around the opaque pixels."""
        out = self.img.copy()
        o = out.load()
        for y in range(self.n):
            for x in range(self.n):
                if self.p[x, y][3]:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if not top and dy == 1:
                        continue
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.n and 0 <= ny < self.n and self.p[nx, ny][3]:
                        o[x, y] = A
                        break
        return out


def leg(x, y0, lift, far):
    """A stubby leg: 3 wide, from y0 down to the ground (row 29), toes at the bottom."""
    L = Layer()
    bottom = 29 - lift
    L.rect(x, y0, x + 2, bottom, H if far else B)
    if not far:
        L.rect(x, y0 + 2, x, bottom, C)
    L.rect(x, bottom, x + 2, bottom, G if far else F)
    return L.outlined(top=False)


def elephant_walk(i):
    ph = i / 6 * 2 * math.pi
    bob = 1 if i % 3 == 1 else 0
    canvas = Image.new("RGBA", (32, 32), (0, 0, 0, 0))

    def step(off):
        s = math.sin(ph + off)
        return int(round(1.4 * s)), 1 if math.cos(ph + off) > 0.55 else 0

    # far legs (behind the body)
    for base, off in ((9, math.pi), (18, 0)):
        dx, lift = step(off + math.pi)
        canvas.alpha_composite(leg(base + dx, 20 + bob, lift, True))

    body = Layer()
    body.ellipse(4, 11 + bob, 22, 24 + bob, B)
    for x in range(6, 21):                       # belly shading
        body.put(x, 23 + bob, C)
    body.rect(6, 22 + bob, 8, 22 + bob, C)
    body.put(3, 15 + bob, B); body.put(2, 16 + bob, B); body.put(2, 17 + bob, B)   # tail
    body.put(1, 18 + bob, C); body.put(2, 18 + bob, C)
    canvas.alpha_composite(body.outlined())

    # near legs
    for base, off in ((6, 0), (15, math.pi)):
        dx, lift = step(off)
        canvas.alpha_composite(leg(base + dx, 20 + bob, lift, False))

    head = Layer()
    head.ellipse(15, 4 + bob, 27, 16 + bob, B)
    # trunk: down from the face, the tip swings a little with the step
    sway = int(round(math.sin(ph) * 1.0))
    for y in range(11, 21):
        head.put(26, y + bob, B); head.put(27, y + bob, B)
    head.put(28, 20 + bob, B); head.put(28, 21 + bob, B)       # the tip curls forward
    head.put(29, 19 + bob + (1 if sway < 0 else 0), B)
    head.put(29, 20 + bob, B)
    canvas.alpha_composite(head.outlined())
    hp = canvas.load()
    hp[23, 9 + bob] = A; hp[23, 10 + bob] = A    # eye
    hp[24, 12 + bob] = E                          # blush
    hp[25, 15 + bob] = F; hp[24, 16 + bob] = F    # tusk
    for y in range(13, 21, 2):                    # trunk wrinkles
        hp[26, y + bob] = C

    ear = Layer()
    ear.ellipse(12, 5 + bob, 20, 17 + bob, B)
    ear.rect(13, 8 + bob, 13, 14 + bob, C)
    ear.put(15, 15 + bob, C); ear.put(16, 15 + bob, C)
    canvas.alpha_composite(ear.outlined())
    return canvas


def elephant_frames():
    sit = Image.open("tools/assets/elephant_sit_zonked_cc0.png").convert("RGBA")
    walk = [elephant_walk(i) for i in range(6)]
    blink = sit.copy()
    blink.load()[17, 13] = B                      # eye closed
    blink.load()[16, 13] = C; blink.load()[18, 13] = C
    trunk = sit.copy()
    # trunk raised higher: shift the trunk pixels (right of column 22, rows 4-12) up by 2
    tp = trunk.load(); sp = sit.load()
    for y in range(4, 13):
        for x in range(23, 32):
            tp[x, y] = (0, 0, 0, 0)
    for y in range(6, 13):
        for x in range(23, 32):
            if sp[x, y][3]:
                tp[x, y - 2] = sp[x, y]
    for y in range(11, 13):                        # keep the base of the trunk joined
        for x in range(23, 27):
            if sp[x, y][3]:
                tp[x, y] = sp[x, y]
    return walk + [sit, blink, trunk]


def fox_frames():
    run = Image.open("tools/assets/fox_run_scratchio_cc0.png").convert("RGBA")
    idle = Image.open("tools/assets/fox_idle_scratchio_cc0.png").convert("RGBA")
    def cut(sheet):
        w = sheet.height and sheet.width // (sheet.width // 64)
        return [sheet.crop((i * 64, 0, i * 64 + 64, sheet.height)).transpose(Image.FLIP_LEFT_RIGHT)
                for i in range(sheet.width // 64)]
    return cut(run) + cut(idle)


def squares(frames, glow):
    """Cuts all frames to one common square around their union, feet on the same line."""
    box = None
    for f in frames:
        b = f.getbbox()
        box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    w, h = box[2] - box[0], box[3] - box[1]
    side = max(w, h) + 2
    scale = OUT // side
    out = []
    for f in frames:
        sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        sq.alpha_composite(f.crop(box), ((side - w) // 2, side - h - 1))
        big = sq.resize((side * scale, side * scale), Image.NEAREST)
        canvas = Image.new("RGBA", (OUT, OUT), (0, 0, 0, 0))
        canvas.alpha_composite(big, ((OUT - big.width) // 2, OUT - big.height))
        a = canvas.split()[3]
        halo = a.filter(ImageFilter.GaussianBlur(12)).point(lambda v: int(v * 0.4))
        res = Image.merge("RGBA", [Image.new("L", (OUT, OUT), c) for c in glow] + [halo])
        res.alpha_composite(canvas)
        out.append(res)
    return out


def strip(frames, path):
    s = Image.new("RGBA", (OUT * len(frames), OUT), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        s.paste(f, (i * OUT, 0))
    s.save(path)
    print(path, s.size)


if __name__ == "__main__":
    strip(squares(elephant_frames(), (170, 160, 255)), "src/elephant.png")
    strip(squares(fox_frames(), (255, 150, 70)), "src/fox.png")
