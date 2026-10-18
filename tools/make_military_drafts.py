# Draft sheet: four original military helicopter designs in the pixel style of the other vehicles.
# Not used by the program; it only shows the options. Writes docs/mockups/military_helicopters.png
# Usage: python tools/make_military_drafts.py
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

G, SCALE = 40, 8
OUT = G * SCALE
OUTLINE = (16, 14, 26, 255)
GLASS = (110, 190, 240, 255)
GLASS_L = (210, 240, 255, 255)
GLASS_D = (50, 110, 170, 255)
METAL = (80, 84, 92, 255)
METAL_L = (150, 156, 166, 255)
BLADE = (50, 52, 58, 255)
BLUR = (170, 176, 196, 140)
TIRE = (30, 30, 34, 255)


def outline(img):
    src = img.load()
    out = img.copy()
    o = out.load()
    for y in range(G):
        for x in range(G):
            if src[x, y][3]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < G and 0 <= ny < G and src[nx, ny][3] and src[nx, ny] != BLUR:
                    o[x, y] = OUTLINE
                    break
    return out


def finish(img, glow):
    img = outline(img).resize((OUT, OUT), Image.NEAREST)
    a = img.split()[3]
    halo = a.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.4))
    out = Image.merge("RGBA", [Image.new("L", (OUT, OUT), c) for c in glow] + [halo])
    out.alpha_composite(img)
    return out


def rotor(d, x0, x1, y, L=None):
    d.line([(x0, y), (x1, y)], fill=BLUR)
    c = (x0 + x1) // 2
    L = L or (x1 - x0) // 2
    d.line([(c - L, y), (c + L, y)], fill=BLADE)
    d.rectangle((c - 1, y, c + 1, y + 1), fill=METAL)


def wheel(d, x, y):
    d.rectangle((x - 1, y - 1, x + 1, y + 1), fill=TIRE)


# 1 - attack helicopter: slim, two seats one behind the other, stub wings with rocket pods, chin gun
def attack():
    img = Image.new("RGBA", (G, G), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    C, CD, CL = (92, 104, 56, 255), (60, 70, 36, 255), (130, 142, 84, 255)
    d.polygon([(2, 15), (16, 19), (16, 22), (3, 18)], fill=C)                 # tail boom
    d.polygon([(1, 10), (4, 10), (6, 17), (3, 18)], fill=C)                   # fin
    d.line([(0, 18), (3, 18)], fill=C)                                        # tail plane
    d.line([(2, 10), (2, 16)], fill=BLADE)                                    # tail rotor
    d.polygon([(14, 16), (30, 15), (36, 20), (34, 24), (15, 24)], fill=C)     # slim body
    d.line([(16, 23), (33, 23)], fill=CD)
    d.polygon([(19, 15), (24, 12), (27, 15)], fill=GLASS)                     # rear (pilot) canopy, higher
    d.polygon([(26, 16), (30, 13), (33, 17)], fill=GLASS)                     # front (gunner) canopy, lower
    d.point((23, 13), fill=GLASS_L); d.point((29, 14), fill=GLASS_L)
    d.rectangle((17, 11, 24, 14), fill=CD)                                     # engines
    d.rectangle((18, 11, 23, 12), fill=C)
    d.rectangle((20, 9, 21, 10), fill=METAL)
    d.rectangle((18, 20, 26, 21), fill=CD)                                     # stub wing
    d.rectangle((19, 22, 24, 24), fill=METAL)                                  # rocket pod
    d.point((25, 23), fill=METAL_L)
    d.line([(33, 25), (37, 25)], fill=METAL)                                   # chin gun
    d.point((32, 24), fill=METAL)
    d.line([(17, 24), (17, 27)], fill=METAL); wheel(d, 17, 28)                 # wheels
    d.line([(31, 24), (31, 27)], fill=METAL); wheel(d, 31, 28)
    d.point((4, 19), fill=METAL); wheel(d, 4, 21)
    d.point((15, 17), fill=CL); d.point((16, 17), fill=CL)
    rotor(d, 4, 38, 8)
    return finish(img, (190, 210, 120))


# 2 - utility transport: bulky cabin with a sliding door, big windows, wheels
def transport():
    img = Image.new("RGBA", (G, G), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    C, CD, CL = (66, 78, 62, 255), (42, 50, 40, 255), (100, 114, 94, 255)
    d.polygon([(2, 14), (14, 17), (14, 21), (3, 17)], fill=C)
    d.polygon([(1, 9), (4, 9), (6, 16), (3, 17)], fill=C)
    d.line([(2, 9), (2, 15)], fill=BLADE)
    d.rounded_rectangle((12, 13, 34, 27), radius=4, fill=C)                  # cabin
    d.polygon([(30, 14), (36, 19), (36, 23), (32, 26)], fill=C)                # nose
    d.polygon([(30, 15), (35, 19), (30, 20)], fill=GLASS)                      # cockpit glass
    d.point((32, 17), fill=GLASS_L)
    d.rectangle((19, 16, 26, 25), fill=CD)                                     # open sliding door
    d.rectangle((20, 17, 25, 24), fill=(30, 34, 30, 255))
    d.rectangle((14, 16, 17, 19), fill=GLASS)                                  # window
    d.point((15, 17), fill=GLASS_L)
    d.rectangle((15, 10, 29, 13), fill=CD)                                     # engine housing
    d.rectangle((16, 10, 28, 11), fill=C)
    d.rectangle((22, 8, 23, 9), fill=METAL)
    d.line([(13, 26), (33, 26)], fill=CD)
    d.line([(14, 14), (28, 14)], fill=CL)
    d.text((27, 21), "", fill=CL)
    d.line([(16, 27), (16, 30)], fill=METAL); wheel(d, 16, 31)
    d.line([(31, 27), (31, 30)], fill=METAL); wheel(d, 31, 31)
    d.point((4, 18), fill=METAL); wheel(d, 4, 20)
    rotor(d, 3, 39, 7)
    return finish(img, (150, 190, 140))


# 3 - heavy gunship in desert camouflage: two bubble canopies, wings with rockets, a cabin for troops
def gunship():
    img = Image.new("RGBA", (G, G), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    C, CD, CAMO = (196, 168, 110, 255), (140, 112, 66, 255), (118, 92, 56, 255)
    d.polygon([(2, 14), (14, 18), (14, 22), (3, 17)], fill=C)
    d.polygon([(1, 9), (4, 9), (6, 16), (3, 17)], fill=C)
    d.line([(0, 12), (5, 12)], fill=BLADE)
    d.polygon([(12, 15), (30, 14), (36, 20), (35, 25), (13, 26)], fill=C)     # body
    for (x, y, w, h) in ((15, 17, 4, 2), (23, 22, 5, 2), (19, 15, 3, 1), (8, 16, 3, 1), (29, 23, 3, 1)):
        d.rectangle((x, y, x + w, y + h), fill=CAMO)                           # camouflage patches
    d.ellipse((27, 14, 32, 19), fill=GLASS)                                    # pilot bubble
    d.ellipse((31, 18, 36, 23), fill=GLASS)                                    # gunner bubble, in front and lower
    d.point((29, 15), fill=GLASS_L); d.point((33, 19), fill=GLASS_L)
    d.rectangle((15, 10, 28, 14), fill=CD)                                     # engines
    d.rectangle((16, 10, 27, 11), fill=C)
    d.rectangle((21, 8, 22, 9), fill=METAL)
    d.rectangle((16, 21, 26, 22), fill=CD)                                     # wings
    d.rectangle((15, 23, 18, 24), fill=METAL); d.rectangle((22, 23, 25, 24), fill=METAL)   # rockets
    d.rectangle((19, 17, 22, 20), fill=GLASS_D)                                # cabin window
    d.line([(16, 26), (16, 29)], fill=METAL); wheel(d, 16, 30)
    d.line([(32, 25), (32, 29)], fill=METAL); wheel(d, 32, 30)
    rotor(d, 2, 39, 7)
    return finish(img, (230, 200, 130))


# 4 - twin-rotor heavy lifter: long body, a rotor at each end
def twin():
    img = Image.new("RGBA", (G, G), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    C, CD, CL = (84, 92, 70, 255), (54, 60, 44, 255), (120, 128, 100, 255)
    d.rounded_rectangle((3, 15, 35, 27), radius=4, fill=C)                    # long body
    d.polygon([(31, 15), (37, 19), (37, 24), (33, 27)], fill=C)                # nose
    d.polygon([(31, 16), (36, 19.5), (31, 21)], fill=GLASS)
    d.point((33, 18), fill=GLASS_L)
    d.polygon([(2, 9), (8, 9), (9, 16), (3, 16)], fill=C)                      # rear pylon
    d.rectangle((26, 11, 31, 15), fill=C)                                      # front pylon
    d.rectangle((5, 7, 6, 8), fill=METAL); d.rectangle((28, 9, 29, 10), fill=METAL)
    for x in range(9, 30, 4):
        d.rectangle((x, 18, x + 1, 19), fill=GLASS_D)                          # row of windows
    d.line([(4, 26), (34, 26)], fill=CD)
    d.line([(6, 16), (30, 16)], fill=CL)
    d.rectangle((10, 12, 22, 14), fill=CD)                                     # engines on the back
    d.line([(8, 27), (8, 30)], fill=METAL); wheel(d, 8, 31)
    d.line([(14, 27), (14, 30)], fill=METAL); wheel(d, 14, 31)
    d.line([(30, 27), (30, 30)], fill=METAL); wheel(d, 30, 31)
    rotor(d, 0, 14, 6, 7)
    rotor(d, 21, 39, 8, 8)
    return finish(img, (170, 190, 140))


def main():
    designs = [("1", "Ударный", attack()), ("2", "Транспортный", transport()),
               ("3", "Тяжёлый штурмовой (камуфляж пустыни)", gunship()), ("4", "Двухвинтовой грузовой", twin())]
    cell = 360
    sheet = Image.new("RGBA", (cell * 2, cell * 2 + 0), (30, 32, 44, 255))
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 26)
        small = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 17)
    except OSError:
        font = small = ImageFont.load_default()
    for k, (num, name, img) in enumerate(designs):
        x, y = (k % 2) * cell, (k // 2) * cell
        d.rounded_rectangle((x + 6, y + 6, x + cell - 6, y + cell - 6), radius=14, outline=(70, 76, 96), width=2)
        sheet.alpha_composite(img, (x + 20, y + 30))
        d.ellipse((x + 16, y + 14, x + 54, y + 52), fill=(96, 158, 255))
        d.text((x + 35, y + 33), num, font=font, fill="white", anchor="mm")
        d.text((x + cell // 2, y + cell - 26), name, font=small, fill=(220, 224, 236), anchor="mm")
    os.makedirs("docs/mockups", exist_ok=True)
    sheet.save("docs/mockups/military_helicopters.png")
    print("docs/mockups/military_helicopters.png")


if __name__ == "__main__":
    main()
