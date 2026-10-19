# Butterfly Cursor for macOS and Linux (and any system Qt runs on).
# The same creatures as the Windows version follow the mouse pointer in a transparent, click-through window
# on every screen; when the mouse rests they go to the Dock / panel and play their resting animation.
# Settings live in the tray menu. Run: python cross/butterfly_cursor.py   (needs PySide6)
import math
import os
import random
import sys
import time

if sys.platform.startswith("linux") and os.environ.get("XDG_SESSION_TYPE") == "wayland" and "QT_QPA_PLATFORM" not in os.environ:
    # Wayland does not tell programs where the pointer is, nor lets them float above other windows: use XWayland
    os.environ["QT_QPA_PLATFORM"] = "xcb"

from PySide6.QtCore import QLocale, QPointF, QRect, QRectF, QSettings, Qt, QTimer
from PySide6.QtGui import (QAction, QActionGroup, QColor, QCursor, QGuiApplication, QIcon, QPainter, QPainterPath,
                           QPen, QPixmap, QPolygonF, QRadialGradient, QImage)
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon, QWidget

VERSION = "1.5-preview"


def asset_dir():
    base = getattr(sys, "_MEIPASS", None)                      # inside a PyInstaller bundle
    if base:
        return os.path.join(base, "assets")
    here = os.path.dirname(os.path.abspath(__file__))
    for d in (os.path.join(here, "assets"), os.path.join(here, "..", "src")):
        if os.path.isdir(d):
            return d
    return here


# ---------------------------------------------------------------- creatures (same values as the Windows version)
FLY, CRAWL, SLIDE, FLOAT, RUN = range(5)
C = dict
CREATURES = [
    C(id="butterfly", ru="Бабочка", en="Butterfly", uz="Kapalak", style=FLY, pace=1.3, accel=0.5),
    C(id="beetle", ru="Жук", en="Beetle", uz="Qoʻngʻiz", style=CRAWL, pace=0.6, accel=0.5),
    C(id="spider", ru="Паук", en="Spider", uz="Oʻrgimchak", style=CRAWL, pace=0.9, accel=0.3),
    C(id="snail", ru="Улитка", en="Snail", uz="Shilliqqurt", style=SLIDE, pace=0.15, accel=0.8),
    C(id="snake", ru="Змея", en="Snake", uz="Ilon", style=CRAWL, pace=0.5, accel=1.2, snake=True),
    C(id="fox", ru="Лисичка", en="Fox", uz="Tulkicha", style=RUN, pace=1.1, accel=0.5, run=6, rest=[0, 1, 2, 3, 4, 5], step=0.16),
    C(id="elephant", ru="Слонёнок", en="Baby elephant", uz="Fil bolasi", style=RUN, pace=0.45, accel=0.9, run=6,
      rest=[0, 0, 0, 0, 0, 1, 0, 0, 0, 2, 2, 0, 0, 0, 1, 0], step=0.3),
    C(id="panda", ru="Панда-мастер", en="Panda master", uz="Panda usta", style=RUN, pace=0.45, accel=0.9, run=6,
      rest=[0, 0, 1, 2, 3, 4, 3, 4, 3, 4, 1], step=0.34),
    C(id="ninja", ru="Ниндзя", en="Ninja", uz="Ninja", style=RUN, pace=1.4, accel=0.35, sit="ninja_sit"),
    C(id="luchador", ru="Лучадор", en="Luchador", uz="Luchador", style=RUN, pace=0.8, accel=0.6),
    C(id="commando", ru="Коммандос", en="Commando", uz="Komandos", style=RUN, pace=0.9, accel=0.5, run=6,
      rest=[0, 0, 0, 0, 3, 0, 0, 0, 1, 2, 1, 2, 1, 2, 0, 0, 0, 3, 0, 0], step=0.16),
    C(id="hand", ru="Рука-помощница", en="Helper hand", uz="Yordamchi qoʻl", style=RUN, pace=0.75, accel=0.5),
    C(id="biker", ru="Байкер", en="Biker", uz="Bayker", style=RUN, pace=1.5, accel=0.9, run=4,
      rest=[0, 0, 0, 0, 2, 2, 0, 0, 0, 1, 1, 1, 0, 0], step=0.25),
    C(id="helicopter", ru="Вертолёт", en="Helicopter", uz="Vertolyot", style=RUN, pace=1.0, accel=1.1, run=4, rest=[0, 1], step=0.14, flies=True),
    C(id="attack_heli", ru="Ударный вертолёт", en="Attack helicopter", uz="Hujumchi vertolyot", style=RUN, pace=1.3, accel=1.0, run=4,
      rest=[0, 1], step=0.2, flies=True),
    C(id="cloud_rain", ru="Облако с дождём", en="Rain cloud", uz="Yomgʻirli bulut", style=FLOAT, pace=0.35, accel=1.5, weather="rain"),
    C(id="cloud_snow", ru="Облако со снегом", en="Snow cloud", uz="Qorli bulut", style=FLOAT, pace=0.35, accel=1.5, weather="snow"),
    C(id="sun", ru="Солнце", en="Sun", uz="Quyosh", style=FLOAT, pace=0.35, accel=1.5, rays="sun_rays"),
    C(id="moon", ru="Луна", en="Moon", uz="Oy", style=FLOAT, pace=0.35, accel=1.5),
]

TEXT = {
    "creature": ("Существо", "Creature", "Jonzot"), "size": ("Размер", "Size", "Oʻlcham"), "speed": ("Скорость", "Speed", "Tezlik"),
    "small": ("Маленький", "Small", "Kichik"), "medium": ("Средний", "Medium", "Oʻrtacha"), "large": ("Большой", "Large", "Katta"),
    "huge": ("Огромный", "Huge", "Juda katta"), "slower": ("Медленнее", "Slower", "Sekinroq"), "normal": ("Обычная", "Normal", "Oddiy"),
    "faster": ("Быстрее", "Faster", "Tezroq"), "dust": ("Светящаяся пыльца", "Glowing dust", "Yaltiroq chang"),
    "home": ("Отдыхать у панели, когда мышь не двигается", "Rest by the panel when the mouse is still", "Sichqoncha turganda panel yonida dam olish"),
    "autostart": ("Запускать при входе в систему", "Start when I log in", "Tizimga kirganda ishga tushirish"),
    "hide": ("Спрятать", "Hide", "Yashirish"), "quit": ("Выход", "Quit", "Chiqish"),
}
LANG = 0


def T(key):
    return TEXT[key][LANG]


def title(c):
    return (c["ru"], c["en"], c["uz"])[LANG]


# ---------------------------------------------------------------- settings and autostart
class Settings:
    def __init__(self):
        self.q = QSettings("JB", "ButterflyCursor")
        self.creature = self.q.value("creature", "butterfly")
        self.size = int(self.q.value("size", 90))
        self.speed = float(self.q.value("speed", 1.0))
        self.dust = self.q.value("dust", "true") in (True, "true")
        self.home = self.q.value("home", "true") in (True, "true")
        self.idle = 4.0

    def save(self):
        for k in ("creature", "size", "speed", "dust", "home"):
            v = getattr(self, k)
            self.q.setValue(k, ("true" if v else "false") if isinstance(v, bool) else v)


def launch_command():
    if getattr(sys, "frozen", False):
        return [os.environ.get("APPIMAGE") or sys.executable]
    return [sys.executable, os.path.abspath(__file__)]


def autostart_file():
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/LaunchAgents/com.jb.butterflycursor.plist")
    return os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")), "autostart", "butterfly-cursor.desktop")


def autostart_on():
    return os.path.exists(autostart_file())


def set_autostart(on):
    path = autostart_file()
    if not on:
        if os.path.exists(path):
            os.remove(path)
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cmd = launch_command()
    if sys.platform == "darwin":
        args = "".join("<string>%s</string>" % a for a in cmd)
        text = ('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
                '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n<plist version="1.0"><dict>'
                '<key>Label</key><string>com.jb.butterflycursor</string>'
                '<key>ProgramArguments</key><array>%s</array><key>RunAtLoad</key><true/></dict></plist>\n' % args)
    else:
        text = ("[Desktop Entry]\nType=Application\nName=Butterfly Cursor\nComment=A glowing companion for the mouse pointer\n"
                "Exec=%s\nX-GNOME-Autostart-enabled=true\n" % " ".join('"%s"' % a for a in cmd))
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


# ---------------------------------------------------------------- sprites
def load_frames(name):
    path = os.path.join(asset_dir(), name + ".png")
    img = QImage(path)
    if img.isNull():
        return []
    h = img.height()
    n = img.width() // h if img.width() >= 2 * h and img.width() % h == 0 else 1
    w = img.width() // n
    return [img.copy(i * w, 0, w, h) for i in range(n)]


def bottom_of(img):
    """Where the feet are: the lowest row with something visible, as a fraction of the height."""
    h = img.height()
    for y in range(h - 1, -1, -1):
        for x in range(0, img.width(), 2):
            if img.pixelColor(x, y).alpha() > 40:
                return (y + 1) / h
    return 1.0


def fit(img, size):
    dpr = QGuiApplication.primaryScreen().devicePixelRatio()
    px = int(size * dpr)
    pm = QPixmap.fromImage(img.scaled(px, px, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    pm.setDevicePixelRatio(dpr)
    return pm


class Sprites:
    def __init__(self, c, size):
        self.c = c
        raw = load_frames(c["id"]) if not c.get("snake") else []
        self.frames = [fit(f, size) for f in raw]
        n = len(raw)
        self.run = c.get("run") or (n - 1 if n >= 3 and n % 2 == 1 else n)
        self.idle = self.run if self.run < n else 0
        self.rest = c.get("rest")
        rest_img = raw[min(n - 1, self.run + self.rest[0])] if (self.rest and n) else (raw[self.idle] if n else None)
        self.feet = bottom_of(rest_img) if rest_img is not None else 1.0
        self.sit = None
        if c.get("sit"):
            s = load_frames(c["sit"])
            if s:
                self.sit = fit(s[0], size)
        self.rays = None
        if c.get("rays"):
            r = load_frames(c["rays"])
            if r:
                self.rays = fit(r[0], size)


# ---------------------------------------------------------------- the live snake (same drawing as the Windows version)
SN_OUT, SN_DARK, SN_SKIN = QColor(16, 34, 16), QColor(50, 102, 40), QColor(86, 152, 62)
SN_LIGHT, SN_BLOTCH, SN_EYE, SN_TONGUE = QColor(150, 204, 96), QColor(36, 72, 30), QColor(244, 204, 62), QColor(222, 40, 64)


def snake_width(frac, W):
    if frac < 0.06:
        return W * (0.68 + 0.32 * frac / 0.06)
    if frac < 0.45:
        return W
    return W * max(0.07, 1 - (frac - 0.45) / 0.55) ** 0.9


def draw_snake(p, pts, ws, W, tongue):
    n = len(pts)
    if n < 3:
        return
    ol = max(1.2, W * 0.08)
    pen = QPen()
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)

    def stroke(color, k, add, ox=0.0, oy=0.0):
        pen.setColor(color)
        for i in range(n - 1, 0, -1):
            pen.setWidthF(max(0.8, (ws[i] + ws[i - 1]) * 0.5 * k + add))
            p.setPen(pen)
            p.drawLine(QPointF(pts[i][0] + ox * ws[i], pts[i][1] + oy * ws[i]), QPointF(pts[i - 1][0] + ox * ws[i - 1], pts[i - 1][1] + oy * ws[i - 1]))

    stroke(SN_OUT, 1, ol * 2)
    stroke(SN_DARK, 1, 0)
    stroke(SN_SKIN, 0.7, 0)
    step = max(3, n // 16)
    ln = max(1, step // 2)
    pen.setColor(SN_BLOTCH)
    for k, i in enumerate(range(step // 2, n - ln, step)):
        w = ws[i]
        if w < W * 0.35:
            continue
        tx, ty = pts[i][0] - pts[i + ln][0], pts[i][1] - pts[i + ln][1]
        tl = math.hypot(tx, ty)
        if tl < 0.01:
            continue
        nx, ny = -ty / tl, tx / tl
        off = (0.13 if k % 2 == 0 else -0.13) * w
        pen.setWidthF(w * 0.42)
        p.setPen(pen)
        p.drawLine(QPointF(pts[i][0] + nx * off, pts[i][1] + ny * off), QPointF(pts[i + ln][0] + nx * off, pts[i + ln][1] + ny * off))
    stroke(SN_LIGHT, 0.14, 0, -0.1, -0.1)

    # the head: spade-shaped, eyes on the sides
    h, h2 = pts[0], pts[min(n - 1, 3)]
    ang = math.degrees(math.atan2(h[1] - h2[1], h[0] - h2[0]))
    p.save()
    p.translate(h[0], h[1])
    p.rotate(ang)
    hl = W * 1.75
    if tongue:
        tp = QPen(SN_TONGUE, max(1.2, W * 0.08))
        p.setPen(tp)
        x0, x1 = hl * 0.5, hl * 0.98
        p.drawLine(QPointF(x0, 0), QPointF(x1, 0))
        p.drawLine(QPointF(x1, 0), QPointF(x1 + W * 0.25, -W * 0.15))
        p.drawLine(QPointF(x1, 0), QPointF(x1 + W * 0.25, W * 0.15))
    shape = [(-0.56 * hl, -0.34 * W), (-0.24 * hl, -0.64 * W), (0.14 * hl, -0.56 * W), (0.44 * hl, -0.34 * W), (0.56 * hl, 0),
             (0.44 * hl, 0.34 * W), (0.14 * hl, 0.56 * W), (-0.24 * hl, 0.64 * W), (-0.56 * hl, 0.34 * W)]
    path = QPainterPath()
    path.moveTo(*shape[0])
    for i in range(len(shape)):          # smooth closed curve through the points
        a, b, c = shape[i], shape[(i + 1) % len(shape)], shape[(i + 2) % len(shape)]
        path.quadTo(QPointF(*b), QPointF((b[0] + c[0]) / 2, (b[1] + c[1]) / 2))
    p.setPen(QPen(SN_OUT, ol * 2))
    p.setBrush(SN_DARK)
    p.drawPath(path)
    p.setPen(Qt.NoPen)
    p.save()
    p.scale(0.76, 0.66)
    p.setBrush(SN_SKIN)
    p.drawPath(path)
    p.restore()
    p.setBrush(SN_BLOTCH)
    p.drawPolygon(QPolygonF([QPointF(-hl * 0.5, -W * 0.27), QPointF(hl * 0.1, 0), QPointF(-hl * 0.5, W * 0.27), QPointF(-hl * 0.3, 0)]))
    for sgn in (-1, 1):
        ex, ey, er = hl * 0.18, sgn * W * 0.47, W * 0.15
        p.setBrush(SN_OUT)
        p.drawEllipse(QPointF(ex, ey), er + ol * 0.7, er + ol * 0.7)
        p.setBrush(SN_EYE)
        p.drawEllipse(QPointF(ex, ey), er, er)
        p.setBrush(SN_OUT)
        p.drawEllipse(QPointF(ex, ey), er * 0.8, er * 0.22)
    p.restore()


# ---------------------------------------------------------------- the creature and its world
class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max", "size", "color", "kind")


DUST_COLORS = [QColor(120, 220, 255), QColor(255, 255, 255), QColor(255, 226, 140), QColor(190, 160, 255), QColor(90, 170, 255)]


def glow_pixmap(color, r):
    size = int(r * 2) + 2
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    g = QRadialGradient(size / 2, size / 2, size / 2)
    c0, c1 = QColor(255, 255, 255, 230), QColor(color)
    c1.setAlpha(110)
    c2 = QColor(color)
    c2.setAlpha(0)
    g.setColorAt(0, c0)
    g.setColorAt(0.22, c1)
    g.setColorAt(1, c2)
    p.setPen(Qt.NoPen)
    p.setBrush(g)
    p.drawEllipse(0, 0, size, size)
    p.end()
    return pm


class World:
    def __init__(self, settings):
        self.s = settings
        self.particles = []
        self.glows = {}
        self.t0 = time.monotonic()
        pos = QCursor.pos()
        self.x, self.y = float(pos.x()), float(pos.y())
        self.vx = self.vy = 0.0
        self.facing = 1.0
        self.angle = 0.0
        self.tilt = 0.0
        self.phase = 0.0
        self.moving = 0.0
        self.resting = False
        self.rest_since = 0.0
        self.last_cursor = (pos.x(), pos.y())
        self.last_move = time.monotonic()
        self.hidden = False
        self.trail = []
        self.sn_head = 0.0
        self.sn_speed = 0.0
        self.sn_dist = 0.0
        self.coil = 0.0
        self.apply()

    def apply(self):
        self.c = next((c for c in CREATURES if c["id"] == self.s.creature), CREATURES[0])
        self.S = max(24, int(self.s.size))
        self.sp = Sprites(self.c, self.S)
        self.trail = []
        self.resting = False

    # ---------------- where to rest: by the Dock / panel
    def perch(self):
        cur = QCursor.pos()
        screen = QGuiApplication.screenAt(cur) or QGuiApplication.primaryScreen()
        g, a = screen.geometry(), screen.availableGeometry()
        S, c = self.S, self.c
        lift = {SLIDE: 0.30, FLOAT: 0.40, RUN: max(0.1, self.sp.feet - 0.5 - 0.02)}.get(c["style"], 0.12)
        if c.get("snake"):
            lift = self.coil_radius() * 0.8 / S
        if self.sp.sit is not None:
            lift = 0.42
        if a.left() > g.left():
            return a.left() + S * 0.5, a.top() + a.height() * 0.6
        if a.right() < g.right():
            return a.right() - S * 0.5, a.top() + a.height() * 0.6
        if a.top() > g.top() and a.bottom() >= g.bottom() - 2:     # panel at the top (GNOME) and nothing below
            return a.left() + a.width() * 0.1, a.top() + S * lift
        x = a.left() + a.width() * (0.32 if sys.platform == "darwin" else 0.08)
        return x, a.bottom() - S * lift

    def coil_radius(self):
        W = self.S * 0.15
        return math.sqrt(self.S * 2.6 * W * 1.1 / math.pi) + W

    # ---------------- one step of the simulation
    def step(self, dt):
        now = time.monotonic()
        cur = QCursor.pos()
        cx, cy = cur.x(), cur.y()
        if abs(cx - self.last_cursor[0]) + abs(cy - self.last_cursor[1]) > 1:
            self.last_move = now
            self.last_cursor = (cx, cy)
        idle = self.s.home and now - self.last_move > self.s.idle
        c, S = self.c, self.S
        max_speed = 180 * 5 * self.s.speed * c["pace"] * 0.55          # px/s; 0.55 matches the Windows default speed
        arrive = 5.0

        if idle:
            tx, ty = self.perch()
        else:
            screen = QGuiApplication.screenAt(cur) or QGuiApplication.primaryScreen()
            wa = screen.availableGeometry()
            sx = 1 if cx + S * 1.4 < wa.right() else -1
            sy = 1 if cy + S * 1.4 < wa.bottom() else -1
            tx, ty = cx + S * 0.62 * sx, cy + S * 0.55 * sy
            if c["style"] in (FLY, FLOAT) or c.get("flies"):
                t = now - self.t0
                tx += math.sin(t * 1.7) * S * 0.22
                ty += math.sin(t * 2.3 + 1) * S * 0.18
            self.resting = False

        dx, dy = tx - self.x, ty - self.y
        dist = math.hypot(dx, dy)
        if c.get("snake"):
            speed = self.snake_step(tx, ty, dist, idle, dt, max_speed)
        else:
            speed = math.hypot(self.vx, self.vy)
            if idle and not self.resting and dist < 3 and speed < 40:
                self.resting = True
                self.rest_since = now
            if self.resting and dist > 6:
                self.resting = False
            if self.resting:
                self.x, self.y, self.vx, self.vy, speed = tx, ty, 0.0, 0.0, 0.0
            else:
                # a steady push: it takes "accel" seconds to reach full speed; braking is a bit quicker
                want = min(max_speed, dist * arrive)
                wx, wy = (dx / dist * want, dy / dist * want) if dist > 0.01 else (0.0, 0.0)
                ax, ay = (wx - self.vx) * 12, (wy - self.vy) * 12
                braking = 1.8 if want < speed else 1.0
                acc, max_acc = math.hypot(ax, ay), max_speed / c["accel"] * braking
                if acc > max_acc:
                    ax, ay = ax * max_acc / acc, ay * max_acc / acc
                self.vx += ax * dt
                self.vy += ay * dt
                self.x += self.vx * dt
                self.y += self.vy * dt
                speed = math.hypot(self.vx, self.vy)
        if not self.resting:
            self.rest_since = now

        self.moving += (min(1.0, speed / max(1.0, max_speed * 0.45)) - self.moving) * min(1.0, dt * 8)
        if abs(self.vx) > 12:
            self.facing = 1.0 if self.vx > 0 else -1.0
        if c["style"] in (FLY, CRAWL) and speed > (70 if c["style"] == FLY else 12):
            want_angle = math.degrees(math.atan2(self.vx, -self.vy))
            da = ((want_angle - self.angle) % 360 + 540) % 360 - 180
            self.angle += da * min(1.0, dt * 9)
        elif self.resting:
            self.angle += (((0 - self.angle) % 360 + 540) % 360 - 180) * min(1.0, dt * 4)
        tilt_want = 14 * min(1.0, abs(self.vx) / max(1.0, max_speed * 0.5)) if c.get("flies") and not self.resting else 0.0
        self.tilt += (tilt_want - self.tilt) * min(1.0, dt * 3)
        style = c["style"]
        freq = {FLY: (0.33 if self.resting else 5 + 5 * self.moving), CRAWL: 6.5 * self.moving, SLIDE: 2.5 * self.moving,
                FLOAT: 0.9, RUN: 1.7 if c.get("flies") else 2.6 * self.moving}[style]
        self.phase += dt * freq * 2 * math.pi

        self.update_particles(dt, speed)

    def snake_step(self, tx, ty, dist, idle, dt, max_speed):
        vmax = max_speed * 0.35
        accel = self.c["accel"]
        now = time.monotonic()
        if self.resting and dist > self.S * 0.8:
            self.resting = False
        if not self.resting and idle and dist < max(4, self.S * 0.12):
            self.resting = True
            self.rest_since = now
        if self.resting:
            self.sn_speed = 0.0
            self.vx = self.vy = 0.0
        else:
            stop = 0 if idle else self.S * 0.5
            want = 0 if dist <= stop else min(vmax, (dist - stop) * 1.8 + 18)
            step = vmax / accel * dt * (1.8 if want < self.sn_speed else 1.0)
            self.sn_speed = min(want, self.sn_speed + step) if want > self.sn_speed else max(want, self.sn_speed - step)
            if self.sn_speed > 2:
                desired = math.atan2(ty - self.y, tx - self.x)
                rate = 2.2 + 3.5 * (1 - self.sn_speed / vmax)
                diff = (desired - self.sn_head + math.pi) % (2 * math.pi) - math.pi
                self.sn_head += max(-rate * dt, min(rate * dt, diff))
                self.sn_dist += self.sn_speed * dt
                wave = 0.55 * math.sin(self.sn_dist / (self.S * 2.6 * 0.62) * 2 * math.pi)
                eff = self.sn_head + wave
                self.x += math.cos(eff) * self.sn_speed * dt
                self.y += math.sin(eff) * self.sn_speed * dt
                self.vx, self.vy = math.cos(self.sn_head) * self.sn_speed, math.sin(self.sn_head) * self.sn_speed
        self.coil = max(0.0, min(1.0, self.coil + (dt / 1.6 if self.resting else -dt / 0.5)))
        if not self.trail:
            self.trail = [(self.x - math.cos(self.sn_head) * i * 4, self.y - math.sin(self.sn_head) * i * 4) for i in range(40)]
        self.trail[0] = (self.x, self.y)
        if math.hypot(self.x - self.trail[1][0], self.y - self.trail[1][1]) >= 1.5:
            self.trail.insert(0, (self.x, self.y))
        need, acc = self.S * 2.6 + 8, 0.0
        for i in range(1, len(self.trail)):
            acc += math.hypot(self.trail[i][0] - self.trail[i - 1][0], self.trail[i][1] - self.trail[i - 1][1])
            if acc > need:
                del self.trail[i + 1:]
                break
        return self.sn_speed

    def snake_points(self):
        L, W = self.S * 2.6, self.S * 0.15
        ds = max(1.5, W * 0.3)
        n = max(8, int(L / ds))
        pts, ws = [], []
        seg, a = 0, self.trail[0] if self.trail else (self.x, self.y)
        for i in range(n):
            ws.append(snake_width(i * ds / L, W))
            if i == 0:
                pts.append(a)
                continue
            left = ds
            while left > 0:
                if seg + 1 >= len(self.trail):
                    a = (a[0] - math.cos(self.sn_head) * left, a[1] - math.sin(self.sn_head) * left)
                    left = 0
                    break
                b = self.trail[seg + 1]
                sl = math.hypot(b[0] - a[0], b[1] - a[1])
                if sl <= left:
                    left -= sl
                    a = b
                    seg += 1
                else:
                    a = (a[0] + (b[0] - a[0]) / sl * left, a[1] + (b[1] - a[1]) / sl * left)
                    left = 0
            pts.append(a)
        if self.coil > 0:
            e = self.coil * self.coil * (3 - 2 * self.coil)
            r, th, bw = W * 0.85, self.sn_head + math.pi / 2, W * 1.1
            for i in range(1, n):
                th += ds / r
                r += bw / (2 * math.pi) * (ds / r)
                cx, cy = self.x + math.cos(th) * r, self.y + math.sin(th) * r * 0.92
                pts[i] = (pts[i][0] + (cx - pts[i][0]) * e, pts[i][1] + (cy - pts[i][1]) * e)
        return pts, ws

    # ---------------- dust and weather
    def update_particles(self, dt, speed):
        c, S = self.c, self.S
        if self.s.dust and not c.get("snake") and speed > 30 and random.random() < min(1.0, speed / 400):
            for _ in range(2):
                p = Particle()
                p.x = self.x - self.facing * S * 0.2 + random.uniform(-S * 0.1, S * 0.1)
                p.y = self.y + random.uniform(-S * 0.1, S * 0.15)
                p.vx, p.vy = -self.vx * 0.1 + random.uniform(-20, 20), -self.vy * 0.1 + random.uniform(-10, 30)
                p.life = p.max = random.uniform(0.6, 1.3)
                p.size = random.uniform(2.0, 4.5)
                p.color = random.randrange(len(DUST_COLORS))
                p.kind = 0
                self.particles.append(p)
        weather = c.get("weather")
        if weather and random.random() < (0.6 if weather == "rain" else 0.3):
            p = Particle()
            p.x, p.y = self.x + random.uniform(-S * 0.35, S * 0.35), self.y + S * 0.2
            p.vx, p.vy = (0.0, 420.0) if weather == "rain" else (random.uniform(-15, 15), 60.0)
            p.life = p.max = 0.6 if weather == "rain" else 1.8
            p.size, p.color, p.kind = (2.0, 0, 1) if weather == "rain" else (2.5, 1, 2)
            self.particles.append(p)
        for p in self.particles:
            p.life -= dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            if p.kind == 0:
                p.vy += 20 * dt
        self.particles = [p for p in self.particles if p.life > 0][-600:]

    def glow(self, color_index, size):
        key = (color_index, int(size * 2))
        pm = self.glows.get(key)
        if pm is None:
            pm = self.glows[key] = glow_pixmap(DUST_COLORS[color_index], size * 3)
        return pm

    # ---------------- drawing (in global screen coordinates; the windows shift the painter)
    def bounds(self):
        S = self.S
        r = S * 0.85
        x0, y0, x1, y1 = self.x - r, self.y - r, self.x + r, self.y + r
        if self.c.get("snake"):
            for px, py in self.snake_points()[0]:
                x0, y0, x1, y1 = min(x0, px - S * 0.3), min(y0, py - S * 0.3), max(x1, px + S * 0.3), max(y1, py + S * 0.3)
        for p in self.particles:
            m = p.size * 4
            x0, y0, x1, y1 = min(x0, p.x - m), min(y0, p.y - m), max(x1, p.x + m), max(y1, p.y + m)
        return QRect(int(x0) - 2, int(y0) - 2, int(x1 - x0) + 4, int(y1 - y0) + 4)

    def paint(self, p):
        if self.hidden:
            return
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        for q in self.particles:
            a = max(0.0, min(1.0, q.life / q.max))
            p.setOpacity(a)
            if q.kind == 1:
                p.setPen(QPen(QColor(150, 200, 255, 200), 1.6))
                p.drawLine(QPointF(q.x, q.y), QPointF(q.x, q.y + 8))
            elif q.kind == 2:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(255, 255, 255, 230))
                p.drawEllipse(QPointF(q.x, q.y), q.size, q.size)
            else:
                pm = self.glow(q.color, q.size)
                p.drawPixmap(QPointF(q.x - pm.width() / 2, q.y - pm.height() / 2), pm)
        p.setOpacity(1.0)
        self.draw_creature(p)

    def draw_creature(self, p):
        c, S, sp = self.c, self.S, self.sp
        half = S / 2
        now = time.monotonic()
        if c.get("snake"):
            pts, ws = self.snake_points()
            draw_snake(p, pts, ws, S * 0.15, (now % 2.4) < 0.28 or (self.resting and (now % 1.5) < 0.22))
            return
        if not sp.frames:
            return
        p.save()
        style = c["style"]
        if style == FLY:
            bob = 0 if self.resting else math.sin(self.phase) * S * 0.035
            p.translate(self.x, self.y + bob)
            p.rotate(self.angle if not self.resting else 14)
            wing = 0.56 + 0.44 * math.cos(self.phase)
            p.scale(max(0.15, wing), 1)
            p.drawPixmap(QRectF(-half, -half, S, S), sp.frames[0], QRectF())
        elif style == FLOAT:
            p.translate(self.x, self.y + math.sin(self.phase) * S * 0.05)
            if sp.rays is not None:
                p.save()
                p.rotate((now * 12) % 360)
                p.drawPixmap(QRectF(-half, -half, S, S), sp.rays, QRectF())
                p.restore()
            p.drawPixmap(QRectF(-half, -half, S, S), sp.frames[0], QRectF())
        elif style == CRAWL:
            s = math.sin(self.phase)
            p.translate(self.x, self.y)
            p.rotate(self.angle + 7 * s * self.moving)
            p.drawPixmap(QRectF(-half, -half, S, S), sp.frames[0], QRectF())
        elif style == SLIDE:
            s = math.sin(self.phase) * self.moving
            p.translate(self.x, self.y)
            p.scale(self.facing, 1)
            w, h = S * (1 + 0.07 * s), S * (1 - 0.05 * s)
            p.drawPixmap(QRectF(-w / 2, half - h, w, h), sp.frames[0], QRectF())
        else:
            idx = sp.idle
            if self.resting and sp.rest:
                k = int((now - self.rest_since) / c["step"]) % len(sp.rest)
                idx = sp.run + sp.rest[k]
            elif (self.moving > 0.12 or c.get("flies")) and sp.run > 0:
                idx = int(self.phase / (2 * math.pi) * sp.run) % sp.run
            elif sp.rest:
                idx = 0
            p.translate(self.x, self.y)
            if self.resting and sp.sit is not None:
                breath = 1 + 0.018 * math.sin(now * 1.6)
                p.drawPixmap(QRectF(-half, half - S * breath, S, S * breath), sp.sit, QRectF())
            else:
                p.scale(self.facing, 1)
                if self.tilt > 0.1:
                    p.rotate(self.tilt)
                f = sp.frames[min(idx, len(sp.frames) - 1)]
                p.drawPixmap(QRectF(-half, -half, S, S), f, QRectF())
        p.restore()


# ---------------------------------------------------------------- one transparent, click-through window per screen
class Overlay(QWidget):
    def __init__(self, world, screen):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowTransparentForInput
                         | Qt.WindowDoesNotAcceptFocus | Qt.NoDropShadowWindowHint)
        self.world = world
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_MacAlwaysShowToolWindow)        # stay visible when another program is active
        self.setGeometry(screen.geometry())
        self.last = QRect()

    def refresh(self, rect):
        g = self.geometry()
        local = rect.translated(-g.left(), -g.top()).intersected(self.rect())
        dirty = local.united(self.last) if not self.last.isNull() else local
        self.last = local
        if not dirty.isNull():
            self.update(dirty)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setCompositionMode(QPainter.CompositionMode_Source)
        p.fillRect(e.rect(), Qt.transparent)
        p.setCompositionMode(QPainter.CompositionMode_SourceOver)
        p.translate(-self.geometry().left(), -self.geometry().top())
        self.world.paint(p)
        p.end()


class App:
    def __init__(self):
        self.qt = QApplication.instance()
        self.qt.setQuitOnLastWindowClosed(False)
        self.s = Settings()
        self.world = World(self.s)
        self.overlays = []
        self.build_overlays()
        self.qt.screenAdded.connect(lambda *_: self.build_overlays())
        self.qt.screenRemoved.connect(lambda *_: self.build_overlays())
        self.build_tray()
        self.last = time.monotonic()
        self.timer = QTimer()
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.timeout.connect(self.tick)
        self.timer.start(16)

    def build_overlays(self):
        for o in self.overlays:
            o.close()
        self.overlays = [Overlay(self.world, sc) for sc in QGuiApplication.screens()]
        for o in self.overlays:
            o.show()

    def tick(self):
        now = time.monotonic()
        dt = min(0.05, now - self.last)
        self.last = now
        self.world.step(dt)
        b = self.world.bounds()
        for o in self.overlays:
            o.refresh(b)

    def build_tray(self):
        frames = load_frames("butterfly")
        icon = QIcon(QPixmap.fromImage(frames[0].scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))) if frames else QIcon()
        self.tray = QSystemTrayIcon(icon)
        self.tray.setToolTip("Butterfly Cursor " + VERSION)
        m = QMenu()
        who = m.addMenu(T("creature"))
        g = QActionGroup(m)
        for c in CREATURES:
            a = QAction(title(c), m, checkable=True, checked=c["id"] == self.s.creature)
            a.triggered.connect(lambda _=False, cid=c["id"]: self.set("creature", cid))
            g.addAction(a)
            who.addAction(a)
        size = m.addMenu(T("size"))
        g2 = QActionGroup(m)
        for key, v in (("small", 60), ("medium", 90), ("large", 130), ("huge", 180)):
            a = QAction(T(key), m, checkable=True, checked=abs(self.s.size - v) < 15)
            a.triggered.connect(lambda _=False, v=v: self.set("size", v))
            g2.addAction(a)
            size.addAction(a)
        speed = m.addMenu(T("speed"))
        g3 = QActionGroup(m)
        for key, v in (("slower", 0.6), ("normal", 1.0), ("faster", 1.6)):
            a = QAction(T(key), m, checkable=True, checked=abs(self.s.speed - v) < 0.1)
            a.triggered.connect(lambda _=False, v=v: self.set("speed", v))
            g3.addAction(a)
            speed.addAction(a)
        m.addSeparator()
        for key in ("dust", "home"):
            a = QAction(T(key), m, checkable=True, checked=getattr(self.s, key))
            a.toggled.connect(lambda on, key=key: self.set(key, on))
            m.addAction(a)
        auto = QAction(T("autostart"), m, checkable=True, checked=autostart_on())
        auto.toggled.connect(set_autostart)
        m.addAction(auto)
        hide = QAction(T("hide"), m, checkable=True)
        hide.toggled.connect(lambda on: setattr(self.world, "hidden", on))
        m.addAction(hide)
        m.addSeparator()
        m.addAction(T("quit"), self.qt.quit)
        self.menu = m
        self.tray.setContextMenu(m)
        self.tray.show()

    def set(self, key, value):
        setattr(self.s, key, value)
        self.s.save()
        if key in ("creature", "size"):
            self.world.apply()


def main():
    global LANG
    app = QApplication(sys.argv)
    loc = QLocale.system().name()
    LANG = 0 if loc.startswith("ru") else 2 if loc.startswith("uz") else 1
    app.setApplicationName("Butterfly Cursor")
    first_run = QSettings("JB", "ButterflyCursor").value("creature") is None
    keep = App()   # noqa: F841 - keeps the windows alive
    if first_run and getattr(sys, "frozen", False) and not autostart_on():
        set_autostart(True)                                     # like the Windows installer: start with the system
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
