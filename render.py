"""AI Limits - rendering layer (Pillow).

Shapes are drawn on a supersampled canvas and scaled down (smooth edges);
text and logos are added at final size (crisp). Tk only hosts the windows
and the clicks.
"""
import math
import os
import re
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont


def resource(*parts):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)


# ----------------------------------------------------------------------- font
WEIGHTS = {"regular": 400, "medium": 500, "semibold": 600, "bold": 700}
_WIN_FONTS = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
# family -> (file, kind) ; kind: "wght" variable, "wght+wdth" variable, "static", "system"
FONTS = {
    "Geist": ("Geist.ttf", "wght"),
    "Geist Mono": ("GeistMono.ttf", "wght"),
    "Fredoka": ("Fredoka.ttf", "wght+wdth"),
    "Chewy": ("Chewy.ttf", "static"),
    "Segoe UI": (None, "system"),
}
_family = "Geist"
_font_cache = {}


def set_family(name):
    global _family
    _family = name if name in FONTS else "Geist"


def font(px, weight="regular", family=None):
    fam = family or _family
    key = (int(round(px)), weight, fam)
    if key not in _font_cache:
        fname, kind = FONTS.get(fam, FONTS["Geist"])
        f = None
        if kind != "system":
            try:
                f = ImageFont.truetype(resource("assets", fname), key[0])
                wv = WEIGHTS[weight]
                if kind == "wght":
                    f.set_variation_by_axes([wv])
                elif kind == "wght+wdth":
                    f.set_variation_by_axes([max(300, min(700, wv)), 100])
            except Exception:
                f = None
        if f is None:
            name = "seguisb.ttf" if weight in ("semibold", "bold") else "segoeui.ttf"
            try:
                f = ImageFont.truetype(os.path.join(_WIN_FONTS, name), key[0])
            except OSError:
                f = ImageFont.load_default()
        _font_cache[key] = f
    return _font_cache[key]


# --------------------------------------------------------------------- presets
_BASE = {
    "dark": dict(bg="#0b0b0c", card="#141416", border="#25252a", fg="#f4f4f5",
                 muted="#8b8b94", faint="#5a5a62", track="#26262c", chip="#18181b",
                 chip_on="#2a2a30", accent="#9be15d", knob="#f4f4f5",
                 ok="#6fd08c", warn="#f2b544", bad="#f0605d",
                 warn_bg="#2a2213", bad_bg="#2b1514"),
    "light": dict(bg="#f2f2f3", card="#ffffff", border="#e2e2e6", fg="#141416",
                  muted="#6b6b74", faint="#a3a3ab", track="#e8e8ec", chip="#f6f6f7",
                  chip_on="#ffffff", accent="#4fae2a", knob="#ffffff",
                  ok="#2fae63", warn="#d48a06", bad="#e0403c",
                  warn_bg="#fdf3e1", bad_bg="#fde8e7"),
}
THEMES = _BASE   # used for the taskbar strip text colors

PRESETS = {
    "minimal": dict(
        label="Minimal", font="Geist Mono", motion="calm", mascot=None, rs=0.4, bw=1,
        tagline="Quiet. Monochrome.",
        dark=dict(bg="#090909", card="#090909", border="#262626", fg="#ededed",
                  muted="#8a8a8a", faint="#555555", track="#1f1f1f", chip="#111111",
                  chip_on="#1f1f1f", accent="#ededed", knob="#090909",
                  ok="#d4d4d4", warn="#f5b14a", bad="#ff5a4e",
                  warn_bg="#1d170c", bad_bg="#1f0f0e"),
        light=dict(bg="#fafafa", card="#fafafa", border="#e4e4e4", fg="#111111",
                   muted="#7a7a7a", faint="#b0b0b0", track="#ececec", chip="#f2f2f2",
                   chip_on="#ffffff", accent="#111111", knob="#fafafa",
                   ok="#2b2b2b", warn="#c77d00", bad="#d63a2f",
                   warn_bg="#fbf2e2", bad_bg="#fbe9e7")),
    "modern": dict(
        label="Modern", font="Geist", motion="lively", mascot=None, rs=1.0, bw=1,
        tagline="Dashboard sharp.", dark=_BASE["dark"], light=_BASE["light"]),
    "kawaii": dict(
        label="Kawaii", font="Fredoka", motion="lively", mascot="kawaii", rs=1.35, bw=1.5,
        tagline="Pink, soft & sparkly",
        dark=dict(bg="#21121c", card="#2c1826", border="#4a2840", fg="#ffe4f1",
                  muted="#d29bbb", faint="#8f5f7c", track="#3d2135", chip="#341d2e",
                  chip_on="#4a2840", accent="#ff7eb6", knob="#fff0f7",
                  ok="#8fe0bd", warn="#ffc46b", bad="#ff6b9a",
                  warn_bg="#3a2a1a", bad_bg="#3d1726"),
        light=dict(bg="#fff0f6", card="#ffffff", border="#ffd1e6", fg="#5a2a46",
                   muted="#b46d93", faint="#e2a6c4", track="#ffe1ee", chip="#fff6fa",
                   chip_on="#ffffff", accent="#ff7eb6", knob="#ffffff",
                   ok="#5cc79a", warn="#f5a524", bad="#ff4f8b",
                   warn_bg="#fff3dc", bad_bg="#ffe3ee")),
    "goofy": dict(
        label="Goofy", font="Chewy", motion="wild", mascot="googly", rs=1.15, bw=2.5,
        tagline="Absolutely unhinged",
        dark=dict(bg="#2a0f45", card="#3b1763", border="#0b0b0b", fg="#fff8d6",
                  muted="#d9c2ff", faint="#9f7fd6", track="#24093d", chip="#4b1f7a",
                  chip_on="#ff5c00", accent="#c6ff00", knob="#0b0b0b",
                  ok="#c6ff00", warn="#ffb000", bad="#ff2e63",
                  warn_bg="#4a2e00", bad_bg="#4a0f22"),
        light=dict(bg="#fff36d", card="#ffffff", border="#111111", fg="#111111",
                   muted="#5b3fa0", faint="#9b87c9", track="#ffe7a8", chip="#ffffff",
                   chip_on="#ff5c00", accent="#7c3aed", knob="#ffffff",
                   ok="#00b85c", warn="#ff8a00", bad="#ff1f57",
                   warn_bg="#fff0c2", bad_bg="#ffd9e3")),
}

MOTION = {
    "off": None,
    "calm": dict(spring=18, damp=11.0, freq=8.0, amp=0.9, speed=0.07, stagger=0.06,
                 slosh=1.5, title=0.5),
    "lively": dict(spring=44, damp=7.5, freq=12.5, amp=1.8, speed=0.16, stagger=0.09,
                   slosh=5.0, title=1.0),
    "wild": dict(spring=84, damp=5.0, freq=15.0, amp=2.8, speed=0.30, stagger=0.12,
                 slosh=9.0, title=1.6, wobble=True),
}


def theme(preset, mode):
    p = PRESETS.get(preset, PRESETS["modern"])
    t = dict(p["dark" if mode == "dark" else "light"])
    t.update(preset=preset, rs=p["rs"], bw=p["bw"], mode=mode)
    return t


def strip_theme(preset, sys_light):
    """Strip colors: preset's status colors, Windows-taskbar text colors."""
    t = theme(preset, "light" if sys_light else "dark")
    base = _BASE["light" if sys_light else "dark"]
    for k in ("fg", "muted", "faint", "track"):
        t[k] = base[k]
    return t


def rgb(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def status_color(t, pct):
    return t["ok"] if pct < 60 else t["warn"] if pct < 85 else t["bad"]


def fit(text, f, maxw):
    if f.getlength(text) <= maxw:
        return text
    while text and f.getlength(text + "…") > maxw:
        text = text[:-1]
    return text + "…"


def ease_out(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def ease_back(x, s=1.7):
    x = max(0.0, min(1.0, x))
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


# ---------------------------------------------------------------------- logos
# Official marks: Claude and OpenAI from Simple Icons (CC0),
# Antigravity from the Antigravity app's own bundle.
LOGO_PATHS = {
    "claude": "m4.7144 15.9555 4.7174-2.6471.079-.2307-.079-.1275h-.2307l-.7893-.0486-2.6956-.0729-2.3375-.0971-2.2646-.1214-.5707-.1215-.5343-.7042.0546-.3522.4797-.3218.686.0608 1.5179.1032 2.2767.1578 1.6514.0972 2.4468.255h.3886l.0546-.1579-.1336-.0971-.1032-.0972L6.973 9.8356l-2.55-1.6879-1.3356-.9714-.7225-.4918-.3643-.4614-.1578-1.0078.6557-.7225.8803.0607.2246.0607.8925.686 1.9064 1.4754 2.4893 1.8336.3643.3035.1457-.1032.0182-.0728-.164-.2733-1.3539-2.4467-1.445-2.4893-.6435-1.032-.17-.6194c-.0607-.255-.1032-.4674-.1032-.7285L6.287.1335 6.6997 0l.9957.1336.419.3642.6192 1.4147 1.0018 2.2282 1.5543 3.0296.4553.8985.2429.8318.091.255h.1579v-.1457l.1275-1.706.2368-2.0947.2307-2.6957.0789-.7589.3764-.9107.7468-.4918.5828.2793.4797.686-.0668.4433-.2853 1.8517-.5586 2.9021-.3643 1.9429h.2125l.2429-.2429.9835-1.3053 1.6514-2.0643.7286-.8196.85-.9046.5464-.4311h1.0321l.759 1.1293-.34 1.1657-1.0625 1.3478-.8804 1.1414-1.2628 1.7-.7893 1.36.0729.1093.1882-.0183 2.8535-.607 1.5421-.2794 1.8396-.3157.8318.3886.091.3946-.3278.8075-1.967.4857-2.3072.4614-3.4364.8136-.0425.0304.0486.0607 1.5482.1457.6618.0364h1.621l3.0175.2247.7892.522.4736.6376-.079.4857-1.2142.6193-1.6393-.3886-3.825-.9107-1.3113-.3279h-.1822v.1093l1.0929 1.0686 2.0035 1.8092 2.5075 2.3314.1275.5768-.3218.4554-.34-.0486-2.2039-1.6575-.85-.7468-1.9246-1.621h-.1275v.17l.4432.6496 2.3436 3.5214.1214 1.0807-.17.3521-.6071.2125-.6679-.1214-1.3721-1.9246L14.38 17.959l-1.1414-1.9428-.1397.079-.674 7.2552-.3156.3703-.7286.2793-.6071-.4614-.3218-.7468.3218-1.4753.3886-1.9246.3157-1.53.2853-1.9004.17-.6314-.0121-.0425-.1397.0182-1.4328 1.9672-2.1796 2.9446-1.7243 1.8456-.4128.164-.7164-.3704.0667-.6618.4008-.5889 2.386-3.0357 1.4389-1.882.929-1.0868-.0062-.1579h-.0546l-6.3385 4.1164-1.1293.1457-.4857-.4554.0608-.7467.2307-.2429 1.9064-1.3114Z",
    "codex": "M22.2819 9.8211a5.9847 5.9847 0 0 0-.5157-4.9108 6.0462 6.0462 0 0 0-6.5098-2.9A6.0651 6.0651 0 0 0 4.9807 4.1818a5.9847 5.9847 0 0 0-3.9977 2.9 6.0462 6.0462 0 0 0 .7427 7.0966 5.98 5.98 0 0 0 .511 4.9107 6.051 6.051 0 0 0 6.5146 2.9001A5.9847 5.9847 0 0 0 13.2599 24a6.0557 6.0557 0 0 0 5.7718-4.2058 5.9894 5.9894 0 0 0 3.9977-2.9001 6.0557 6.0557 0 0 0-.7475-7.0729zm-9.022 12.6081a4.4755 4.4755 0 0 1-2.8764-1.0408l.1419-.0804 4.7783-2.7582a.7948.7948 0 0 0 .3927-.6813v-6.7369l2.02 1.1686a.071.071 0 0 1 .038.052v5.5826a4.504 4.504 0 0 1-4.4945 4.4944zm-9.6607-4.1254a4.4708 4.4708 0 0 1-.5346-3.0137l.142.0852 4.783 2.7582a.7712.7712 0 0 0 .7806 0l5.8428-3.3685v2.3324a.0804.0804 0 0 1-.0332.0615L9.74 19.9502a4.4992 4.4992 0 0 1-6.1408-1.6464zM2.3408 7.8956a4.485 4.485 0 0 1 2.3655-1.9728V11.6a.7664.7664 0 0 0 .3879.6765l5.8144 3.3543-2.0201 1.1685a.0757.0757 0 0 1-.071 0l-4.8303-2.7865A4.504 4.504 0 0 1 2.3408 7.872zm16.5963 3.8558L13.1038 8.364 15.1192 7.2a.0757.0757 0 0 1 .071 0l4.8303 2.7913a4.4944 4.4944 0 0 1-.6765 8.1042v-5.6772a.79.79 0 0 0-.407-.667zm2.0107-3.0231l-.142-.0852-4.7735-2.7818a.7759.7759 0 0 0-.7854 0L9.409 9.2297V6.8974a.0662.0662 0 0 1 .0284-.0615l4.8303-2.7866a4.4992 4.4992 0 0 1 6.6802 4.66zM8.3065 12.863l-2.02-1.1638a.0804.0804 0 0 1-.038-.0567V6.0742a4.4992 4.4992 0 0 1 7.3757-3.4537l-.142.0805L8.704 5.459a.7948.7948 0 0 0-.3927.6813zm1.0976-2.3654l2.602-1.4998 2.6069 1.4998v2.9994l-2.5974 1.4997-2.6067-1.4997Z",
    "antigravity": "M144.248 149.062C151.748 154.688 162.998 150.938 152.685 140.625C121.748 110.625 128.31 28.125 89.8727 28.125C51.4352 28.125 57.9977 110.625 27.0602 140.625C15.8102 151.875 27.9977 154.688 35.4977 149.062C64.5602 129.375 62.6852 94.6875 89.8727 94.6875C117.06 94.6875 115.185 129.375 144.248 149.062Z",
}

_NUM = r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?"
_ARGS = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2, "A": 7, "Z": 0}


def _arc_points(x1, y1, rx, ry, phi, fa, fs, x2, y2):
    """SVG endpoint arc -> points (F.6.5 of the SVG spec)."""
    if rx == 0 or ry == 0:
        return [(x2, y2)]
    rx, ry = abs(rx), abs(ry)
    cp, sp = math.cos(math.radians(phi)), math.sin(math.radians(phi))
    dx, dy = (x1 - x2) / 2, (y1 - y2) / 2
    x1p, y1p = cp * dx + sp * dy, -sp * dx + cp * dy
    lam = (x1p ** 2) / rx ** 2 + (y1p ** 2) / ry ** 2
    if lam > 1:
        rx, ry = rx * math.sqrt(lam), ry * math.sqrt(lam)
    num = rx ** 2 * ry ** 2 - rx ** 2 * y1p ** 2 - ry ** 2 * x1p ** 2
    den = rx ** 2 * y1p ** 2 + ry ** 2 * x1p ** 2
    co = math.sqrt(max(0, num / den)) if den else 0
    if fa == fs:
        co = -co
    cxp, cyp = co * rx * y1p / ry, -co * ry * x1p / rx
    cx = cp * cxp - sp * cyp + (x1 + x2) / 2
    cy = sp * cxp + cp * cyp + (y1 + y2) / 2

    def ang(ux, uy, vx, vy):
        a = math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)
        return a

    t1 = ang(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dt = ang((x1p - cxp) / rx, (y1p - cyp) / ry, (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if not fs and dt > 0:
        dt -= 2 * math.pi
    elif fs and dt < 0:
        dt += 2 * math.pi
    n = max(4, int(abs(dt) / (math.pi / 16)))
    pts = []
    for i in range(1, n + 1):
        a = t1 + dt * i / n
        x, y = rx * math.cos(a), ry * math.sin(a)
        pts.append((cp * x - sp * y + cx, sp * x + cp * y + cy))
    return pts


def parse_path(d):
    """SVG path data -> list of closed polygons (curves flattened)."""
    toks = re.findall(r"[MmLlHhVvCcSsQqTtAaZz]|" + _NUM, d)
    subs, cur = [], []
    x = y = sx = sy = 0.0
    lc = None   # last control point
    i, cmd = 0, None
    while i < len(toks):
        if re.match(r"[A-Za-z]", toks[i]):
            cmd = toks[i]
            i += 1
            if cmd in "Zz":
                if cur:
                    subs.append(cur)
                cur = []
                x, y = sx, sy
                lc = None
                continue
        U, rel = cmd.upper(), cmd.islower()
        n = _ARGS[U]
        a = [float(v) for v in toks[i:i + n]]
        i += n
        ox, oy = (x, y) if rel else (0, 0)
        if U == "M":
            if cur:
                subs.append(cur)
            x, y = ox + a[0], oy + a[1]
            sx, sy = x, y
            cur = [(x, y)]
            cmd = "l" if rel else "L"
            lc = None
        elif U == "L":
            x, y = ox + a[0], oy + a[1]
            cur.append((x, y))
            lc = None
        elif U == "H":
            x = (x if rel else 0) + a[0]
            cur.append((x, y))
            lc = None
        elif U == "V":
            y = (y if rel else 0) + a[0]
            cur.append((x, y))
            lc = None
        elif U in "CS":
            if U == "C":
                c1 = (ox + a[0], oy + a[1])
                c2, e = (ox + a[2], oy + a[3]), (ox + a[4], oy + a[5])
            else:
                c1 = (2 * x - lc[0], 2 * y - lc[1]) if lc else (x, y)
                c2, e = (ox + a[0], oy + a[1]), (ox + a[2], oy + a[3])
            for k in range(1, 13):
                t = k / 12
                mt = 1 - t
                cur.append((mt ** 3 * x + 3 * mt * mt * t * c1[0] + 3 * mt * t * t * c2[0] + t ** 3 * e[0],
                            mt ** 3 * y + 3 * mt * mt * t * c1[1] + 3 * mt * t * t * c2[1] + t ** 3 * e[1]))
            lc = c2
            x, y = e
        elif U in "QT":
            if U == "Q":
                c, e = (ox + a[0], oy + a[1]), (ox + a[2], oy + a[3])
            else:
                c = (2 * x - lc[0], 2 * y - lc[1]) if lc else (x, y)
                e = (ox + a[0], oy + a[1])
            for k in range(1, 11):
                t = k / 10
                mt = 1 - t
                cur.append((mt * mt * x + 2 * mt * t * c[0] + t * t * e[0],
                            mt * mt * y + 2 * mt * t * c[1] + t * t * e[1]))
            lc = c
            x, y = e
        elif U == "A":
            e = (ox + a[5], oy + a[6])
            cur += _arc_points(x, y, a[0], a[1], a[2], int(a[3]), int(a[4]), e[0], e[1])
            x, y = e
            lc = None
    if cur:
        subs.append(cur)
    return subs


_logo_cache = {}


def logo_mask(kind, px, style="outline", stroke=1.0):
    """Exact logo silhouette as an anti-aliased L mask (px x px).
    style 'outline' keeps only the shape's border, 'fill' the full shape."""
    key = (kind, int(px), style, round(stroke, 2))
    if key in _logo_cache:
        return _logo_cache[key]
    subs = parse_path(LOGO_PATHS[kind])
    xs = [p[0] for s in subs for p in s]
    ys = [p[1] for s in subs for p in s]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    ss = 4
    size = int(px) * ss
    sc = size * 0.98 / max(w, h)
    offx = (size - w * sc) / 2 - min(xs) * sc
    offy = (size - h * sc) / 2 - min(ys) * sc
    acc = Image.new("1", (size, size), 0)
    for s in subs:
        m = Image.new("1", (size, size), 0)
        ImageDraw.Draw(m).polygon([(offx + x * sc, offy + y * sc) for x, y in s], fill=1)
        acc = ImageChops.logical_xor(acc, m)            # even-odd fill
    mask = acc.convert("L")
    if style == "outline":
        k = max(3, int(round(stroke * ss)) | 1)
        mask = ImageChops.subtract(mask, mask.filter(ImageFilter.MinFilter(k)))
    mask = mask.resize((int(px), int(px)), Image.LANCZOS)
    _logo_cache[key] = mask
    return mask


# ----------------------------------------------------------------- primitives
def _ring(d, cx, cy, r, w, pct, color, track):
    box = (cx - r, cy - r, cx + r, cy + r)
    d.ellipse(box, outline=track, width=int(w))
    if pct <= 0:
        return
    ext = 360 * min(pct, 100) / 100
    d.arc(box, -90, -90 + ext, fill=color, width=int(w))
    rm = r - w / 2
    for a in (-90, -90 + ext):
        x = cx + rm * math.cos(math.radians(a))
        y = cy + rm * math.sin(math.radians(a))
        d.ellipse((x - w / 2, y - w / 2, x + w / 2, y + w / 2), fill=color)


def _liquid(img, cx, cy, r, pct, color, phase, amp):
    """Wavy liquid inside a circle, filled up to pct (on the big canvas)."""
    ri = int(r)
    if ri < 2:
        return
    size = 2 * ri + 2
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    p = max(0.0, min(1.0, pct / 100))
    level = size - 1 - (size - 2) * p
    lam = size * 0.9
    for k, (ph, alpha, lift) in enumerate(((phase + 2.1, 0.30, amp * 0.9), (phase, 0.62, 0))):
        pts = [(0, size)]
        steps = 28
        for i in range(steps + 1):
            x = size * i / steps
            yy = level - lift + amp * math.sin(2 * math.pi * x / lam + ph * (1.0 if k else -1.3))
            pts.append((x, yy))
        pts.append((size, size))
        ld.polygon(pts, fill=color[:3] + (int(255 * alpha),))
    circle = Image.new("L", (size, size), 0)
    ImageDraw.Draw(circle).ellipse((1, 1, size - 2, size - 2), fill=255)
    a = ImageChops.multiply(layer.getchannel("A"), circle)
    layer.putalpha(a)
    img.alpha_composite(layer, (int(cx - size / 2), int(cy - size / 2)))


class Canvas2x:
    """Draws shapes big, text and logos at final size."""

    def __init__(self, w, h, scale, bg, ss=3):
        self.w, self.h, self.k, self.ss = w, h, scale, ss
        self.big = Image.new("RGBA", (max(1, int(w * scale * ss)), max(1, int(h * scale * ss))),
                             rgb(bg) if bg else (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.big)
        self.texts = []
        self.logos = []

    def S(self, v):
        return v * self.k * self.ss

    def rrect(self, x1, y1, x2, y2, r, fill=None, outline=None, width=1, alpha=255):
        S = self.S
        self.d.rounded_rectangle((S(x1), S(y1), S(x2), S(y2)), radius=S(r),
                                 fill=rgb(fill, alpha) if fill else None,
                                 outline=rgb(outline) if outline else None,
                                 width=int(S(width)) if outline else 0)

    def ring(self, cx, cy, r, w, pct, color, track):
        S = self.S
        _ring(self.d, S(cx), S(cy), S(r), S(w), pct, rgb(color), rgb(track))

    def liquid(self, cx, cy, r, pct, color, phase, amp):
        S = self.S
        _liquid(self.big, S(cx), S(cy), S(r), pct, rgb(color), phase, S(amp))

    def gauge(self, cx, cy, r, w, pct, color, track, liquid=None):
        """Ring gauge; with liquid=(phase, amp) also fills the inside."""
        if liquid:
            self.liquid(cx, cy, r - w - 1.2, pct, color, *liquid)
        self.ring(cx, cy, r, w, pct, color, track)

    def logo(self, kind, cx, cy, r, color, style="outline", stroke=1.0):
        if kind not in LOGO_PATHS:
            return
        px = int(round(2 * r * self.k))
        m = logo_mask(kind, px, style, stroke * self.k)
        self.logos.append((int(round(cx * self.k - px / 2)), int(round(cy * self.k - px / 2)),
                           m, rgb(color)))

    def icon(self, kind, cx, cy, r, color, w=1.4):
        S = self.S
        icon(self.d, self.big, kind, S(cx), S(cy), S(r), rgb(color), S(w))

    # free shapes in logical coords (used by mascots and decorations)
    def ellipse(self, x1, y1, x2, y2, fill=None, outline=None, width=1, alpha=255):
        S = self.S
        self.d.ellipse((S(x1), S(y1), S(x2), S(y2)), fill=rgb(fill, alpha) if fill else None,
                       outline=rgb(outline) if outline else None,
                       width=int(S(width)) if outline else 0)

    def polygon(self, pts, fill=None, outline=None, width=1, alpha=255):
        S = self.S
        self.d.polygon([(S(x), S(y)) for x, y in pts], fill=rgb(fill, alpha) if fill else None,
                       outline=rgb(outline) if outline else None,
                       width=int(S(width)) if outline else 0)

    def line(self, pts, color, width=1, alpha=255, round_caps=True):
        S = self.S
        self.d.line([(S(x), S(y)) for x, y in pts], fill=rgb(color, alpha), width=int(S(width)),
                    joint="curve")
        if round_caps:
            for x, y in (pts[0], pts[-1]):
                r = S(width) / 2
                self.d.ellipse((S(x) - r, S(y) - r, S(x) + r, S(y) + r), fill=rgb(color, alpha))

    def arc(self, x1, y1, x2, y2, a1, a2, color, width=1):
        S = self.S
        self.d.arc((S(x1), S(y1), S(x2), S(y2)), a1, a2, fill=rgb(color), width=int(S(width)))

    def text(self, x, y, s, size, color, weight="regular", anchor="la", maxw=None, alpha=255,
             family=None):
        f = font(size * self.k, weight, family)
        if maxw:
            s = fit(s, f, maxw * self.k)
        self.texts.append((x * self.k, y * self.k, s, f, rgb(color, alpha), anchor))
        return f.getlength(s) / self.k

    def image(self):
        im = self.big.resize((max(1, int(self.w * self.k)), max(1, int(self.h * self.k))),
                             Image.LANCZOS)
        for x, y, m, c in self.logos:
            im.paste(Image.new("RGBA", m.size, c), (x, y), m)
        d = ImageDraw.Draw(im)
        for x, y, s, f, c, anchor in self.texts:
            d.text((x, y), s, font=f, fill=c, anchor=anchor)
        return im


def measure(size, k, s, weight="regular", family=None):
    return font(size * k, weight, family).getlength(s) / k


def _thick_line(d, p1, p2, w, color):
    d.line([p1, p2], fill=color, width=int(w))
    for x, y in (p1, p2):
        d.ellipse((x - w / 2, y - w / 2, x + w / 2, y + w / 2), fill=color)


def icon(d, img, kind, cx, cy, r, color, w):
    """Small UI icons for the panel controls."""
    if kind == "sun":
        d.ellipse((cx - r * .38, cy - r * .38, cx + r * .38, cy + r * .38), outline=color,
                  width=int(w))
        for i in range(8):
            a = math.radians(i * 45)
            _thick_line(d, (cx + r * .62 * math.cos(a), cy + r * .62 * math.sin(a)),
                        (cx + r * .9 * math.cos(a), cy + r * .9 * math.sin(a)), w * .9, color)
    elif kind == "moon":
        R = r * .82
        size = int(R * 2 + w * 4)
        m = Image.new("L", (size, size), 0)
        md = ImageDraw.Draw(m)
        o = size / 2
        md.ellipse((o - R, o - R, o + R, o + R), fill=255)
        md.ellipse((o - R * .35, o - R * 1.25, o + R * 1.35, o + R * .45), fill=0)
        edge = ImageChops.subtract(m, m.filter(ImageFilter.MinFilter(int(w) | 1)))
        img.paste(Image.new("RGBA", m.size, color), (int(cx - o), int(cy - o)), edge)
    elif kind == "spark":
        pts = []
        for i in range(8):
            a = math.radians(i * 45 - 90)
            rr = r * (0.95 if i % 2 == 0 else 0.28)
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        d.polygon(pts, outline=color, width=int(w))
        d.ellipse((cx + r * .55, cy - r * .95, cx + r * .95, cy - r * .55), outline=color,
                  width=int(max(1, w * .8)))
    elif kind == "carousel":
        d.rounded_rectangle((cx - r * .5, cy - r * .55, cx + r * .5, cy + r * .55),
                            radius=r * .18, outline=color, width=int(w))
        for s in (-1, 1):
            x = cx + s * r * .82
            d.line([(x - s * r * .14, cy - r * .22), (x + s * r * .06, cy),
                    (x - s * r * .14, cy + r * .22)], fill=color, width=int(w))
    elif kind == "rings":
        for dx in (-r * .62, 0, r * .62):
            d.ellipse((cx + dx - r * .34, cy - r * .34, cx + dx + r * .34, cy + r * .34),
                      outline=color, width=int(w))
    elif kind == "refresh":
        d.arc((cx - r * .7, cy - r * .7, cx + r * .7, cy + r * .7), 20, 320, fill=color,
              width=int(w))
        a = math.radians(320)
        x, y = cx + r * .7 * math.cos(a), cy + r * .7 * math.sin(a)
        d.polygon([(x - r * .32, y - r * .12), (x + r * .14, y - r * .36),
                   (x + r * .12, y + r * .14)], fill=color)
    elif kind == "clock":
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=color, width=int(w))
        d.line([(cx, cy - r * .55), (cx, cy), (cx + r * .45, cy + r * .25)], fill=color,
               width=int(w))
    elif kind in ("down", "right"):
        if kind == "down":
            pts = [(cx - r * .5, cy - r * .22), (cx, cy + r * .28), (cx + r * .5, cy - r * .22)]
        else:
            pts = [(cx - r * .22, cy - r * .5), (cx + r * .28, cy), (cx - r * .22, cy + r * .5)]
        d.line(pts, fill=color, width=int(w), joint="curve")
    elif kind == "check":
        d.line([(cx - r * .55, cy), (cx - r * .12, cy + r * .42), (cx + r * .6, cy - r * .45)],
               fill=color, width=int(w), joint="curve")
    elif kind == "mouse":
        d.rounded_rectangle((cx - r * .55, cy - r * .85, cx + r * .55, cy + r * .85),
                            radius=r * .55, outline=color, width=int(w))
        d.line([(cx, cy - r * .55), (cx, cy - r * .2)], fill=color, width=int(w))
    elif kind == "gear":
        pts = []
        n = 8
        for i in range(n * 4):
            a = 2 * math.pi * i / (n * 4) - math.pi / (n * 4) * 1.5
            rr = r * (0.95 if (i % 4) in (0, 1) else 0.72)
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        d.polygon(pts, outline=color, width=int(w))
        d.ellipse((cx - r * .3, cy - r * .3, cx + r * .3, cy + r * .3), outline=color,
                  width=int(w))
    elif kind == "back":
        d.line([(cx + r * .25, cy - r * .55), (cx - r * .3, cy), (cx + r * .25, cy + r * .55)],
               fill=color, width=int(w), joint="curve")
    elif kind == "heart":
        pts = []
        for i in range(60):
            a = 2 * math.pi * i / 60
            x = 16 * math.sin(a) ** 3
            y = -(13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a))
            pts.append((cx + x * r / 17, cy + y * r / 17))
        d.polygon(pts, fill=color)
    elif kind == "star":            # four-point sparkle, filled
        pts = []
        for i in range(8):
            a = math.radians(i * 45 - 90)
            rr = r * (1.0 if i % 2 == 0 else 0.3)
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        d.polygon(pts, fill=color)


# ---------------------------------------------------------------------- strip
def pill_cycle(w, h, k, bg, t, item, hover, hover_bg, offset=1.0, prev=None, liquid=None):
    """Cycle strip: gauge + two lines. offset 0..1 slide progress (prev -> item)."""
    c = Canvas2x(w, h, k, bg)
    if hover:
        c.rrect(1, 1, w - 1, h - 1, 6, fill=hover_bg)

    def draw(it, dy, alpha=255):
        if not it:
            return
        title, b = it
        col = status_color(t, b["pct"])
        dd = h - 12
        cx, cy = 6 + dd / 2, h / 2 + dy
        c.gauge(cx, cy, dd / 2, 2.6, b["pct"], col, t["track"], liquid)
        c.text(cx, cy, f"{b['pct']:.0f}", 9, t["fg"], "semibold", anchor="mm", alpha=alpha)
        tx = 6 + dd + 9
        c.text(tx, h / 2 - 8 + dy, f"{b['pct']:.0f}% · {b['label']}", 11.5, t["fg"],
               "semibold", anchor="lm", maxw=w - tx - 6, alpha=alpha)
        sub = title + (f" · {b['reset_txt']}" if b.get("reset_txt") else "")
        c.text(tx, h / 2 + 9 + dy, sub, 10.5, t["muted"], anchor="lm", maxw=w - tx - 6,
               alpha=alpha)

    if prev is not None and offset < 1:
        e = ease_out(offset)
        draw(prev, -e * h * .7, int(255 * (1 - e)))
        draw(item, (1 - e) * h * .7, int(255 * e))
    else:
        draw(item, 0)
    return c.image()


def pill_rings(w, h, k, bg, t, rings, hover, hover_bg, liquid=None):
    """Rings strip: one gauge per service with its logo in the middle."""
    c = Canvas2x(w, h, k, bg)
    if hover:
        c.rrect(1, 1, w - 1, h - 1, 6, fill=hover_bg)
    dd = h - 10
    x = 8
    for i, (kind, pct) in enumerate(rings):
        cx, cy = x + dd / 2, h / 2
        lq = (liquid[0] + i * 1.7, liquid[1]) if liquid else None
        c.gauge(cx, cy, dd / 2, 2.6, pct, status_color(t, pct), t["track"], lq)
        c.logo(kind, cx, cy, dd * 0.25, t["fg"], "outline", 1.0)
        x += dd + 8
    return c.image()


def rings_width(n, h):
    dd = h - 10
    return 8 + n * (dd + 8)


# ---------------------------------------------------------------------- panel
NAMES = {"claude": "Claude", "codex": "ChatGPT", "antigravity": "Antigravity"}
TITLE = "AI Limits"


def _mix(c1, c2, f):
    a, b = rgb(c1), rgb(c2)
    return "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * f) for i in range(3))


def _title(c, t, s, x, base_y):
    """'AI Limits' heading. Intro: letters fly in from the right and fade in.
    Afterwards it breathes: a shimmer sweeps through it and a live dot pulses."""
    mo = s.get("motion")
    size = 19
    f = font(size * c.k, "bold")
    clock = s.get("clock", 0.0)
    it = s.get("title_t")
    xs, cx = [], x
    for ch in TITLE:
        xs.append(cx)
        cx += f.getlength(ch) / c.k
    width = cx - x
    goofy = t.get("preset") == "goofy"
    for i, ch in enumerate(TITLE):
        dx, dy, alpha, col = 0.0, 0.0, 255, t["fg"]
        if mo:
            amt = mo.get("title", 1.0)
            if it is not None:
                p = ease_out((it - 0.06 - i * 0.045) / 0.42)
                dx = (1 - p) * 30 * amt
                alpha = int(255 * p)
                if goofy:
                    dy = (1 - p) * -18 * math.sin(i * 1.7)
            # shimmer band moving left -> right every ~3.6 s
            sweep = ((clock / 3.6) % 1.0) * (width + 120) - 60
            g = math.exp(-((xs[i] + 5 - x - sweep) / 16.0) ** 2)
            col = _mix(t["fg"], t["accent"], min(1.0, g * 0.85 * amt))
            if goofy:
                dy += math.sin(clock * 5 + i * 0.9) * 1.6
        if ch != " ":
            c.text(xs[i] + dx, base_y + dy, ch, size, col, "bold", anchor="ls", alpha=alpha)
    # live dot (a heart for kawaii)
    dxp = x + width + 9
    dyp = base_y - 12
    pulse = (clock * 0.9) % 1.0 if mo else 0.0
    if mo and (it is None or it > 0.5):
        rr = 3 + 7 * pulse
        c.ellipse(dxp - rr, dyp - rr, dxp + rr, dyp + rr, outline=t["accent"], width=1.1,
                  alpha=int(200 * (1 - pulse)))
    breathe = 1 + (0.18 * math.sin(clock * 3.2) if mo else 0)
    if t.get("preset") == "kawaii":
        c.icon("heart", dxp, dyp, 4.6 * breathe, t["accent"])
    else:
        r0 = 3.0 * breathe
        c.ellipse(dxp - r0, dyp - r0, dxp + r0, dyp + r0, fill=t["accent"])
    return width


def _deco(c, t, W, H, clock):
    """Kawaii: hearts and sparkles drifting up behind the header."""
    if t.get("preset") != "kawaii":
        return
    for i in range(7):
        sp = 0.06 + 0.03 * (i % 3)
        p = (clock * sp + i * 0.37) % 1.0
        x = 30 + (i * 53) % (W - 60) + math.sin(clock * 1.3 + i) * 6
        y = H - p * (H + 10)
        a = int(110 * math.sin(math.pi * p))
        if i % 2:
            c.icon("heart", x, y, 3.2 + (i % 3), _mix(t["bg"], t["accent"], a / 255))
        else:
            c.icon("star", x, y, 3.0 + (i % 2) * 1.5, _mix(t["bg"], t["accent"], a / 255))


def panel_header(W, k, t, s, ss=3):
    """Fixed top: title, gear/refresh, three controls, hero gauges.
    -> (image, hits, height)"""
    import mascots
    rings = s.get("rings") or []
    rs = t.get("rs", 1)
    H = 132 + (124 if rings else 0)
    c = Canvas2x(W, H, k, t["bg"], ss)
    hits = []
    clock = s.get("clock", 0.0)
    if s.get("motion"):
        _deco(c, t, W, 128, clock)
    _title(c, t, s, 18, 31)
    c.text(18, 51, s["subtitle"], 11, t["muted"], anchor="ls")

    # buttons: settings + refresh
    for j, (ic, act) in enumerate((("refresh", "refresh"), ("gear", "settings"))):
        bx = W - 18 - 32 - j * 40
        c.rrect(bx, 14, bx + 32, 46, 16, fill=t["chip"], outline=t["border"], width=t["bw"])
        spin = 0
        col = t["fg"] if not (act == "refresh" and s["busy"]) else t["faint"]
        c.icon(ic, bx + 16, 30, 7.5 if ic == "gear" else 7, col, 1.5)
        hits.append(((bx, 14, bx + 32, 46), act))

    # mascot peeking next to the buttons
    mk = s.get("mascot")
    if mk:
        mascots.draw(c, mk, W - 128, 32, 25, t, s)
        hits.append(((W - 156, 4, W - 100, 60), "mascot"))

    gap = 8
    cw = (W - 36 - 2 * gap) / 3
    y1, y2 = 66, 100
    for i, (kind, label) in enumerate((("theme", "Theme"), ("anim", "Motion"),
                                       ("mode", "Taskbar"))):
        x1 = 18 + i * (cw + gap)
        x2 = x1 + cw
        c.rrect(x1, y1, x2, y2, 17 * min(rs, 1), fill=t["chip"], outline=t["border"],
                width=t["bw"])
        if kind == "mode":
            half = (x2 - x1 - 8) / 2
            for j, m in enumerate(("cycle", "rings")):
                sx1 = x1 + 4 + j * half
                on = s["mode"] == m
                if on:
                    c.rrect(sx1, y1 + 4, sx1 + half, y2 - 4, 13 * min(rs, 1), fill=t["chip_on"],
                            outline=t["border"], width=t["bw"])
                c.icon("carousel" if m == "cycle" else "rings", sx1 + half / 2, (y1 + y2) / 2,
                       7.5, t["fg"] if on else t["faint"], 1.4)
                hits.append(((sx1, y1, sx1 + half, y2), "mode:" + m))
        else:
            on = (s["theme"] == "dark") if kind == "theme" else s["anim"]
            ic = ("moon" if s["theme"] == "dark" else "sun") if kind == "theme" else "spark"
            c.icon(ic, x1 + 20, (y1 + y2) / 2, 7.5, t["fg"], 1.4)
            _switch(c, t, x2 - 8 - 34, (y1 + y2) / 2, on,
                    (s.get("knob_anim") or {}).get(kind, 0))
            hits.append(((x1, y1, x2, y2), kind))
        c.text((x1 + x2) / 2, y2 + 14, label, 10, t["muted"], anchor="mm")

    if rings:
        hy = 132
        c.rrect(12, hy, W - 12, hy + 112, 16 * rs, fill=t["card"], outline=t["border"],
                width=t["bw"])
        n = len(rings)
        p = s.get("hero_p", 1.0)
        for i, (key, pct) in enumerate(rings):
            cx = 12 + (W - 24) * (i + .5) / n
            cy = hy + 44
            shown = pct * ease_out(p - i * 0.08) if p < 1.2 else pct
            col = status_color(t, pct)
            lq = (s.get("phase", 0) + i * 1.9, s.get("amp", 0)) if s.get("liquid") else None
            c.gauge(cx, cy, 28, 3, shown, col, t["track"], lq)
            c.logo(key, cx, cy, 10.5, t["fg"], "outline", 1.1)
            c.text(cx, hy + 88, f"{shown:.0f}%", 14, t["fg"], "semibold", anchor="mm")
            c.text(cx, hy + 103, NAMES.get(key, key), 10, t["muted"], anchor="mm")
            hits.append(((cx - 40, hy, cx + 40, hy + 112), "jump:" + key))
    return c.image(), hits, H


def _switch(c, t, x1, cy, on, knob_off=0.0, w=34, h=20):
    c.rrect(x1, cy - h / 2, x1 + w, cy + h / 2, h / 2, fill=t["accent"] if on else t["track"],
            outline=t["border"] if t.get("bw", 1) > 2 else None, width=t.get("bw", 1))
    kx = (x1 + w - h / 2) if on else (x1 + h / 2)
    kx += knob_off
    c.rrect(kx - 7, cy - h / 2 + 3, kx + 7, cy + h / 2 - 3, 7, fill=t["knob"])


def _card_height(key, data, err, collapsed):
    h = 52
    if err:
        h += 30
    if key in collapsed:
        return h + 2
    group = None
    for b in data["bars"]:
        if b.get("group") and b["group"] != group:
            group = b["group"]
            h += 24
        h += 40
    return h + 10


def _draw_card(W, k, t, key, data, err, stale, collapsed, ch, bar_p, ss):
    """One service card on its own canvas (so it can slide/fade on its own)."""
    goofy = t.get("preset") == "goofy"
    pad = 4 if goofy else 0
    c = Canvas2x(W, ch + pad, k, None, ss)
    rs = t.get("rs", 1)
    x1, x2, y = 12, W - 12 - pad, 0
    if goofy:   # chunky cartoon shadow
        c.rrect(x1 + 4, y + 4, x2 + 4, y + ch + 4, 16 * rs, fill=t["border"])
    c.rrect(x1, y, x2, y + ch, 16 * rs, fill=t["card"], outline=t["border"], width=t["bw"])
    c.rrect(x1 + 12, y + 12, x1 + 40, y + 40, 14 * min(rs, 1), fill=t["chip"],
            outline=t["border"], width=t["bw"])
    c.logo(key, x1 + 26, y + 26, 8, t["fg"], "outline", 1.0)
    tw = c.text(x1 + 50, y + 26, data["title"], 13.5, t["fg"], "semibold", anchor="lm")
    if data.get("plan"):
        px = x1 + 50 + tw + 8
        pw = measure(10, k, data["plan"], "medium") + 14
        c.rrect(px, y + 17, px + pw, y + 35, 9, outline=t["border"], fill=t["card"],
                width=min(t["bw"], 1.5))
        c.text(px + pw / 2, y + 26, data["plan"], 10, t["muted"], "medium", anchor="mm")
    coll = key in collapsed
    if data["bars"] and coll:
        worst = max(b["pct"] for b in data["bars"])
        c.text(x2 - 36, y + 26, f"{worst:.0f}%", 12, status_color(t, worst), "semibold",
               anchor="rm")
    c.icon("right" if coll else "down", x2 - 20, y + 26, 7, t["muted"], 1.6)
    yy = y + 52
    if err:
        c.rrect(x1 + 12, yy - 4, x2 - 12, yy + 22, 9, fill=t["warn_bg"])
        msg = err + (f" · last data {stale}" if stale else "")
        c.text(x1 + 22, yy + 9, msg, 10, t["warn"], anchor="lm", maxw=x2 - x1 - 44)
        yy += 30
    if not coll:
        group = None
        for i, b in enumerate(data["bars"]):
            if b.get("group") and b["group"] != group:
                group = b["group"]
                c.text(x1 + 16, yy + 10, group.upper(), 9.5, t["faint"], "semibold",
                       anchor="lm", maxw=x2 - x1 - 32)
                yy += 24
            bp = ease_out(bar_p - i * 0.07) if bar_p < 1.5 else 1.0
            val = b["pct"] * bp
            col = status_color(t, b["pct"])
            c.text(x1 + 16, yy + 8, b["label"], 12, t["fg"], anchor="lm", maxw=x2 - x1 - 150)
            pct_txt = f"{val:.0f}%"
            c.text(x2 - 16, yy + 8, pct_txt, 12, col, "semibold", anchor="rm")
            pw = measure(12, k, f"{b['pct']:.0f}%", "semibold")
            if b.get("reset_txt") or b.get("note"):
                rt = " · ".join(x for x in (b.get("note"), b.get("reset_txt")) if x)
                rw = measure(10.5, k, rt)
                rx = x2 - 16 - pw - 12 - rw
                c.icon("clock", rx - 9, yy + 8, 4.2, t["muted"], 1.1)
                c.text(rx, yy + 8, rt, 10.5, t["muted"], anchor="lm")
            bh = 6 if not goofy else 8
            c.rrect(x1 + 16, yy + 20, x2 - 16, yy + 20 + bh, bh / 2, fill=t["track"],
                    outline=t["border"] if goofy else None, width=1.5)
            fw = (x2 - x1 - 32) * min(val, 100) / 100
            if fw > 0.5:
                c.rrect(x1 + 16, yy + 20, x1 + 16 + max(fw, bh), yy + 20 + bh, bh / 2, fill=col)
            yy += 40
    return c.image()


def panel_body(W, k, t, sections, collapsed, intro=None, ss=3, motion=None):
    """Scrollable service cards. sections: [(key, data, err, stale)].
    intro: seconds since the panel opened (None = final state)."""
    mo = motion or MOTION["lively"]
    heights = [_card_height(key, d, e, collapsed) for key, d, e, _ in sections]
    H = max(60, 6 + sum(h + 10 for h in heights) + 10)
    out = Image.new("RGBA", (int(W * k), int(H * k)), rgb(t["bg"]))
    hits = []
    if not sections:
        c = Canvas2x(W, 60, k, t["bg"], ss)
        c.text(W / 2, 30, "No supported AI account found on this PC", 11, t["muted"],
               anchor="mm")
        out.paste(c.image(), (0, 0))
    y = 6
    for i, ((key, data, err, stale), ch) in enumerate(zip(sections, heights)):
        if intro is None:
            cp, bar_p = 1.0, 9.0
        else:
            start = 0.10 + i * mo["stagger"]
            cp = (intro - start) / 0.42
            bar_p = (intro - start - 0.12) / 0.7
        hits.append(((12, y, W - 12, y + 52), "toggle:" + key))
        if cp > 0:
            img = _draw_card(W, k, t, key, data, err, stale, collapsed, ch, bar_p, ss)
            dy = (1 - ease_back(cp, 1.4)) * 22 * (mo["spring"] / 44) if cp < 1 else 0
            ox = 0
            if cp < 1:
                a = img.getchannel("A").point(lambda v, f=ease_out(cp * 1.6): int(v * f))
                img.putalpha(a)
                if mo.get("wobble"):
                    ang = math.sin(cp * 9) * 6 * (1 - cp)
                    w0, h0 = img.size
                    img = img.rotate(ang, resample=Image.BICUBIC, expand=True)
                    ox = (w0 - img.size[0]) // 2
                    dy += (h0 - img.size[1]) / 2 / k
            out.alpha_composite(img, (int(ox), int((y + dy) * k)))
        y += ch + 10
    return out, hits, H


# ------------------------------------------------------------------- settings
FONT_CHOICES = ["Geist", "Geist Mono", "Fredoka", "Chewy", "Segoe UI"]
MOTION_CHOICES = [("off", "Off"), ("calm", "Calm"), ("lively", "Lively"), ("wild", "Wild")]


def settings_header(W, k, t, ss=3):
    H = 62
    c = Canvas2x(W, H, k, t["bg"], ss)
    c.rrect(14, 14, 46, 46, 16, fill=t["chip"], outline=t["border"], width=t["bw"])
    c.icon("back", 30, 30, 8, t["fg"], 1.7)
    c.text(58, 37, "Settings", 18, t["fg"], "bold", anchor="ls")
    return c.image(), [((14, 14, 46, 46), "back")], H


def settings_body(W, k, t, s, ss=3):
    """Settings page. s: preset, theme, font, motion, liquid, mascot, mode,
    interval, knob_anim. -> (image, hits, height)"""
    c = Canvas2x(W, 1100, k, t["bg"], ss)
    hits = []
    rs = t.get("rs", 1)
    y = 6

    def label(txt):
        nonlocal y
        c.text(18, y + 10, txt.upper(), 9.5, t["faint"], "semibold", anchor="lm")
        y += 24

    def seg(options, current, prefix, h=34):
        nonlocal y
        x1, x2 = 14, W - 14
        c.rrect(x1, y, x2, y + h, h / 2 * min(rs, 1), fill=t["chip"], outline=t["border"],
                width=t["bw"])
        n = len(options)
        sw = (x2 - x1 - 8) / n
        for i, (val, lab) in enumerate(options):
            sx = x1 + 4 + i * sw
            on = val == current
            if on:
                c.rrect(sx, y + 4, sx + sw, y + h - 4, (h - 8) / 2 * min(rs, 1),
                        fill=t["chip_on"], outline=t["border"], width=t["bw"])
            c.text(sx + sw / 2, y + h / 2, lab, 11.5, t["fg"] if on else t["muted"],
                   "semibold" if on else "medium", anchor="mm")
            hits.append(((sx, y, sx + sw, y + h), f"{prefix}:{val}"))
        y += h + 14

    def toggle_row(title, desc, on, act):
        nonlocal y
        h = 50
        c.rrect(14, y, W - 14, y + h, 14 * rs, fill=t["card"], outline=t["border"],
                width=t["bw"])
        c.text(28, y + 19, title, 12.5, t["fg"], "semibold", anchor="lm")
        c.text(28, y + 35, desc, 10.5, t["muted"], anchor="lm", maxw=W - 110)
        _switch(c, t, W - 28 - 34, y + h / 2, on, (s.get("knob_anim") or {}).get(act, 0))
        hits.append(((14, y, W - 14, y + h), act))
        y += h + 8

    # presets
    label("Style preset")
    cw = (W - 28 - 10) / 2
    chh = 92
    for i, (name, p) in enumerate(PRESETS.items()):
        col, row = i % 2, i // 2
        x1 = 14 + col * (cw + 10)
        y1 = y + row * (chh + 10)
        pal = p["dark" if s["theme"] == "dark" else "light"]
        sel = s["preset"] == name
        c.rrect(x1, y1, x1 + cw, y1 + chh, 14 * p["rs"] if p["rs"] < 1.3 else 18,
                fill=pal["bg"], outline=t["accent"] if sel else pal["border"],
                width=2.2 if sel else max(1, p["bw"]))
        c.text(x1 + 14, y1 + 24, p["label"], 15, pal["fg"], "bold", anchor="lm",
               family=p["font"])
        c.text(x1 + 14, y1 + 42, p["tagline"], 9.5, pal["muted"], anchor="lm",
               family=p["font"], maxw=cw - 24)
        for j, key in enumerate(("card", "accent", "ok", "warn", "bad")):
            sx = x1 + 14 + j * 15
            c.ellipse(sx, y1 + 62, sx + 12, y1 + 74, fill=pal[key], outline=pal["border"],
                      width=1)
        c.ring(x1 + cw - 26, y1 + 68, 11, 2.6, 62, pal["ok"], pal["track"])
        if sel:
            c.ellipse(x1 + cw - 26, y1 + 8, x1 + cw - 8, y1 + 26, fill=t["accent"])
            c.icon("check", x1 + cw - 17, y1 + 17, 5.5, t["knob"] if s["theme"] == "dark"
                   else "#ffffff", 1.8)
        hits.append(((x1, y1, x1 + cw, y1 + chh), "preset:" + name))
    y += 2 * (chh + 10) + 6

    label("Appearance")
    seg([("dark", "Dark"), ("light", "Light")], s["theme"], "theme")

    label("Font")
    x = 14
    for fam in FONT_CHOICES:
        wch = measure(12, k, fam, "medium", fam) + 26
        if x + wch > W - 14:
            x = 14
            y += 40
        on = s["font"] == fam
        c.rrect(x, y, x + wch, y + 32, 16 * min(rs, 1),
                fill=t["chip_on"] if on else t["chip"],
                outline=t["accent"] if on else t["border"], width=2 if on else t["bw"])
        c.text(x + wch / 2, y + 16, fam, 12, t["fg"] if on else t["muted"], "medium",
               anchor="mm", family=fam)
        hits.append(((x, y, x + wch, y + 32), "font:" + fam))
        x += wch + 8
    y += 32 + 14

    label("Motion")
    seg(MOTION_CHOICES, s["motion"], "motion")
    toggle_row("Liquid gauges", "Waves inside the rings while Motion is on",
               s["liquid"], "liquid")
    toggle_row("Mascot", "Your preset's little buddy in the panel", s["mascot"], "mascot")

    label("Taskbar strip")
    seg([("cycle", "Cycle"), ("rings", "Rings")], s["mode"], "mode")
    label("Switch every")
    seg([(5, "5 s"), (10, "10 s"), (20, "20 s"), (30, "30 s")], s["interval"], "interval")

    c.rrect(14, y, W - 14, y + 38, 19 * min(rs, 1), fill=t["chip"], outline=t["border"],
            width=t["bw"])
    c.text(W / 2, y + 19, "Reset to preset defaults", 12, t["fg"], "semibold", anchor="mm")
    hits.append(((14, y, W - 14, y + 38), "reset"))
    y += 38 + 16
    for line in ("Claude, ChatGPT and Antigravity are refreshed in the background,",
                 "so you never need to open them just to see your limits."):
        c.text(W / 2, y, line, 10, t["faint"], anchor="mm")
        y += 15
    y += 10
    im = c.image().crop((0, 0, int(W * k), int(y * k)))
    return im, hits, y


# ------------------------------------------------------------------- tutorial
def tutorial(W, H, k, t, step, steps, s, ss=3):
    """First-run walkthrough card. steps[i] = dict(title, body, art).
    s: phase, amp, anim, slide (0..1 entry progress), dir (+1/-1)."""
    c = Canvas2x(W, H, k, t["bg"], ss)
    hits = []
    st = steps[step]
    sl = ease_out(s.get("slide", 1.0))
    dx = (1 - sl) * 28 * s.get("dir", 1)
    al = int(255 * sl)

    # top bar: step counter + skip
    c.text(20, 26, f"{step + 1} / {len(steps)}", 10.5, t["muted"], "medium", anchor="lm")
    if step < len(steps) - 1:
        sw = measure(10.5, k, "Skip", "medium")
        c.text(W - 20, 26, "Skip", 10.5, t["muted"], "medium", anchor="rm")
        hits.append(((W - 30 - sw, 12, W - 10, 40), "skip"))

    # illustration area
    ay1, ay2 = 44, 170
    c.rrect(16, ay1, W - 16, ay2, 18, fill=t["card"], outline=t["border"])
    _tutorial_art(c, st["art"], W, ay1, ay2, t, s, dx)

    # text
    c.text(22 + dx, 200, st["title"], 17, t["fg"], "bold", anchor="ls", alpha=al)
    y = 222
    f = font(12 * k)
    for para in st["body"]:
        words, line = para.split(), ""
        for wd in words:
            cand = (line + " " + wd).strip()
            if f.getlength(cand) / k > W - 44:
                c.text(22 + dx, y, line, 12, t["muted"], anchor="la", alpha=al)
                y += 18
                line = wd
            else:
                line = cand
        if line:
            c.text(22 + dx, y, line, 12, t["muted"], anchor="la", alpha=al)
            y += 18
        y += 6

    # dots
    by = H - 34
    n = len(steps)
    for i in range(n):
        wdot = 18 if i == step else 6
        x0 = 22 + sum((18 if j == step else 6) + 6 for j in range(i))
        c.rrect(x0, by - 3, x0 + wdot, by + 3, 3, fill=t["fg"] if i == step else t["track"])
        hits.append(((x0 - 3, by - 10, x0 + wdot + 3, by + 10), f"dot:{i}"))

    # buttons
    last = step == n - 1
    label = "Get started" if last else "Next"
    bw = measure(12, k, label, "semibold") + 36
    bx2, bx1 = W - 18, W - 18 - bw
    c.rrect(bx1, by - 17, bx2, by + 17, 17, fill=t["fg"])
    c.text((bx1 + bx2) / 2, by, label, 12, t["bg"], "semibold", anchor="mm")
    hits.append(((bx1, by - 17, bx2, by + 17), "finish" if last else "next"))
    if step > 0:
        bw2 = measure(12, k, "Back", "medium") + 28
        c.rrect(bx1 - 8 - bw2, by - 17, bx1 - 8, by + 17, 17, outline=t["border"],
                fill=t["chip"])
        c.text(bx1 - 8 - bw2 / 2, by, "Back", 12, t["fg"], "medium", anchor="mm")
        hits.append(((bx1 - 8 - bw2, by - 17, bx1 - 8, by + 17), "back"))
    return c.image(), hits


def _tutorial_art(c, art, W, y1, y2, t, s, dx):
    cy = (y1 + y2) / 2
    cx = W / 2 + dx
    lq = (s.get("phase", 0), s.get("amp", 0)) if s.get("anim") else None
    if art == "welcome":
        for i, (key, pct) in enumerate((("claude", 42), ("codex", 18), ("antigravity", 71))):
            x = cx + (i - 1) * 84
            c.gauge(x, cy, 30, 3, pct, status_color(t, pct), t["track"],
                    (lq[0] + i * 1.9, lq[1]) if lq else None)
            c.logo(key, x, cy, 11, t["fg"], "outline", 1.1)
    elif art == "strip":
        # mini taskbar with the strip on the left
        c.rrect(cx - 130, cy - 26, cx + 130, cy + 26, 10, fill="#1c1c1c")
        c.rrect(cx - 124, cy - 20, cx + 10, cy + 20, 8, fill="#2e2e2e")
        c.gauge(cx - 104, cy, 15, 2.2, 55, t["ok"], "#3a3d44", lq)
        c.text(cx - 84, cy - 7, "55% · Weekly", 10.5, "#f4f4f5", "semibold", anchor="lm")
        c.text(cx - 84, cy + 8, "Claude · 1d 16h", 9.5, "#9aa0a6", anchor="lm")
        for i in range(4):
            c.rrect(cx + 40 + i * 22, cy - 8, cx + 56 + i * 22, cy + 8, 4, fill="#3a3a3a")
        c.icon("mouse", cx - 30, cy - 36, 9, t["muted"], 1.3)
    elif art == "panel":
        c.rrect(cx - 92, y1 + 14, cx + 92, y2 - 8, 12, fill=t["bg"], outline=t["border"])
        for i, (pct, w) in enumerate(((17, .9), (55, .7), (34, .8))):
            yy = y1 + 34 + i * 30
            c.rrect(cx - 78, yy, cx - 78 + 60 * w, yy + 6, 3, fill=t["faint"])
            c.rrect(cx - 78, yy + 12, cx + 78, yy + 17, 2.5, fill=t["track"])
            p = ease_out(s.get("slide", 1.0) * 1.3 - i * .15)
            c.rrect(cx - 78, yy + 12, cx - 78 + max(5, 156 * pct / 100 * p), yy + 17, 2.5,
                    fill=status_color(t, pct))
    elif art == "controls":
        for i, (ic, label) in enumerate((("moon", "Theme"), ("spark", "Motion"),
                                         ("rings", "Taskbar"))):
            x = cx + (i - 1) * 96
            c.rrect(x - 42, cy - 22, x + 42, cy + 12, 17, fill=t["chip"], outline=t["border"])
            c.icon(ic, x, cy - 5, 8, t["fg"], 1.4)
            c.text(x, cy + 30, label, 10.5, t["muted"], anchor="mm")
    elif art == "accounts":
        for i, key in enumerate(("claude", "codex", "antigravity")):
            x = cx + (i - 1) * 84
            c.rrect(x - 30, cy - 30, x + 30, cy + 30, 18, fill=t["chip"], outline=t["border"])
            c.logo(key, x, cy, 14, t["fg"], "outline", 1.1)
            c.rrect(x + 16, cy + 16, x + 34, cy + 34, 9, fill=t["accent"])
            c.icon("check", x + 25, cy + 25, 5, "#ffffff", 1.6)
    elif art == "done":
        c.gauge(cx, cy, 36, 3.2, 100, t["ok"], t["track"], lq)
        c.icon("check", cx, cy, 14, t["fg"], 3)
