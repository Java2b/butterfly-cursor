# Builds the pictures for the README from the creature sprites:
#   docs/hero.png                 a banner: the butterfly with a trail of glowing dust and a few friends
#   docs/screenshots/creatures.png a gallery of all built-in creatures with their names
# Usage: python tools/make_readme_images.py
import math, random, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

random.seed(7)
FONT_B = "C:/Windows/Fonts/segoeuib.ttf"
FONT = "C:/Windows/Fonts/segoeui.ttf"


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def frame(name, index=0):
    s = Image.open(f"src/{name}.png").convert("RGBA")
    h = s.height
    n = max(1, s.width // h)
    index = index % n
    return s.crop((index * h, 0, index * h + h, h))


def background(w, h, top=(14, 16, 34), bottom=(34, 30, 70)):
    bg = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(bg)
    for y in range(h):
        t = y / max(1, h - 1)
        d.line([(0, y), (w, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(top, bottom)) + (255,))
    return bg


def dust(img, pts, colors):
    """Glowing dots along a path, bigger and brighter near the butterfly."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i, (x, y) in enumerate(pts):
        k = i / max(1, len(pts) - 1)
        for _ in range(3):
            r = 1.5 + 4.5 * k * random.random()
            c = random.choice(colors)
            jx, jy = x + random.uniform(-14, 14) * (1 - k * 0.5), y + random.uniform(-14, 14) * (1 - k * 0.5)
            d.ellipse((jx - r * 3, jy - r * 3, jx + r * 3, jy + r * 3), fill=c + (int(40 * k) + 10,))
            d.ellipse((jx - r, jy - r, jx + r, jy + r), fill=(255, 255, 255, int(150 * k) + 60))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(1.2)))


def hero():
    W, H = 1280, 420
    img = background(W, H)
    # stars
    d = ImageDraw.Draw(img)
    for _ in range(140):
        x, y, a = random.randrange(W), random.randrange(H - 60), random.randrange(40, 160)
        d.point((x, y), fill=(255, 255, 255, a))
    # taskbar strip at the bottom
    d.rectangle((0, H - 48, W, H), fill=(24, 24, 32, 255))
    d.line([(0, H - 48), (W, H - 48)], fill=(50, 50, 64, 255))
    sx = W // 2 - 20
    for i, c in enumerate(((84, 170, 255), (84, 170, 255), (84, 170, 255), (84, 170, 255))):
        ox, oy = (i % 2) * 13, (i // 2) * 13
        d.rectangle((sx + ox, H - 38 + oy, sx + ox + 11, H - 38 + oy + 11), fill=c + (255,))
    # the dust trail curling across the banner
    pts = [(80 + t * 9.2, 250 - 90 * math.sin(t / 14) + t * 0.2) for t in range(0, 110)]
    dust(img, pts, [(120, 220, 255), (255, 226, 140), (190, 160, 255), (255, 255, 255)])
    bf = frame("butterfly", 0).resize((190, 190), Image.LANCZOS)
    img.alpha_composite(bf, (int(pts[-1][0]) - 60, int(pts[-1][1]) - 120))
    # friends resting along the taskbar
    for name, idx, size, x in (("ninja_sit", 0, 120, sx - 46), ("fox", 6, 120, 210), ("commando", 7, 110, 360),
                               ("panda", 9, 120, 900), ("attack_heli", 4, 130, 1080)):
        f = Image.open(f"src/{name}.png").convert("RGBA") if name == "ninja_sit" else frame(name, idx)
        f = f.resize((size, size), Image.LANCZOS)
        box = f.getbbox()
        img.alpha_composite(f, (x, H - 48 - box[3] + 4))
    d = ImageDraw.Draw(img)
    d.text((60, 46), "Butterfly Cursor", font=font(FONT_B, 58), fill=(240, 244, 255))
    d.text((64, 118), "A glowing companion for your mouse pointer · Windows 10 / 11", font=font(FONT, 24), fill=(170, 180, 220))
    img.convert("RGB").save("docs/hero.png", optimize=True)
    print("docs/hero.png")


def gallery():
    items = [("butterfly", 0, "Бабочка"), ("beetle", 0, "Жук"), ("spider", 0, "Паук"), ("snail", 0, "Улитка"),
             ("snake", 3, "Змея"), ("fox", 0, "Лисичка"), ("elephant", 2, "Слонёнок"), ("panda", 9, "Панда-мастер"),
             ("ninja", 1, "Ниндзя"), ("luchador", 8, "Лучадор"), ("commando", 7, "Коммандос"), ("hand", 2, "Рука"),
             ("biker", 0, "Байкер"), ("helicopter", 0, "Вертолёт"), ("attack_heli", 0, "Ударный вертолёт"),
             ("cloud_rain", 0, "Облако с дождём"), ("cloud_snow", 0, "Облако со снегом"), ("sun", 0, "Солнце"),
             ("moon", 0, "Луна")]
    cols, cell, label = 5, 220, 34
    rows = (len(items) + cols - 1) // cols
    W, H = cols * cell + 40, rows * (cell + label) + 40
    img = background(W, H, (18, 20, 34), (28, 30, 52))
    d = ImageDraw.Draw(img)
    f = font(FONT, 20)
    for i, (name, idx, title) in enumerate(items):
        x, y = 20 + (i % cols) * cell, 20 + (i // cols) * (cell + label)
        d.rounded_rectangle((x + 8, y + 8, x + cell - 8, y + cell + label - 8), radius=16, fill=(38, 41, 62, 255), outline=(60, 64, 92, 255))
        sp = frame(name, idx).resize((cell - 40, cell - 40), Image.LANCZOS)
        img.alpha_composite(sp, (x + 20, y + 12))
        d.text((x + cell // 2, y + cell + 4), title, font=f, fill=(225, 230, 245), anchor="mm")
    img.convert("RGB").save("docs/screenshots/creatures.png", optimize=True)
    print("docs/screenshots/creatures.png")


if __name__ == "__main__":
    os.makedirs("docs/screenshots", exist_ok=True)
    hero()
    gallery()
