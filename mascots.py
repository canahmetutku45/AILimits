"""Preset mascots, drawn from simple shapes (original artwork).

kawaii: chibi anime girl with pink twin tails. Blinks, bobs, and gets
        flustered (> <) when a limit is almost used up.
googly: a wobbly blob with googly eyes that follow the mouse and a
        propeller cap that spins.
"""
import math


def _blink(clock, period=3.7):
    """True for ~0.13 s every period seconds (plus a double blink sometimes)."""
    ph = clock % period
    return ph < 0.13 or (int(clock / period) % 3 == 0 and 0.28 < ph < 0.38)


def draw(c, kind, cx, cy, size, t, s):
    if kind == "kawaii":
        kawaii(c, cx, cy, size, t, s)
    elif kind == "googly":
        googly(c, cx, cy, size, t, s)


def kawaii(c, cx, cy, r, t, s):
    clock = s.get("clock", 0.0)
    moving = bool(s.get("motion"))
    mood = s.get("mood", "ok")
    bob = math.sin(clock * 2.4) * 1.4 if moving else 0
    tilt = math.sin(clock * 1.1) * 0.06 if moving else 0
    cy = cy + bob
    hair, hair_d = "#ff8cc6", "#e0609f"
    skin, skin_d = "#ffe9dd", "#f4c7b6"
    eye, eye_l = "#4a1f45", "#b3528f"
    ribbon = "#7fd3ff"

    poke = s.get("poke")
    if poke is not None and poke < 1.0:            # happy hop when clicked
        cy -= 9 * math.exp(-5 * poke) * abs(math.sin(poke * 11))
    # twin tails swaying, tied high on both sides of the head
    for side in (-1, 1):
        sway = math.sin(clock * 2.0 + side) * 2.0 if moving else 0
        top = (cx + side * r * 0.62, cy - r * 0.5)
        tip = (cx + side * r * 1.02 + sway * side, cy + r * 0.82)
        pts = []
        for i in range(13):
            u = i / 12
            x = top[0] + (tip[0] - top[0]) * u + side * math.sin(u * math.pi) * r * 0.2
            y = top[1] + (tip[1] - top[1]) * u
            w = r * (0.1 + 0.2 * math.sin(min(1, u * 1.15) * math.pi))
            pts.append((x - w, y))
        for i in range(12, -1, -1):
            u = i / 12
            x = top[0] + (tip[0] - top[0]) * u + side * math.sin(u * math.pi) * r * 0.2
            y = top[1] + (tip[1] - top[1]) * u
            w = r * (0.1 + 0.2 * math.sin(min(1, u * 1.15) * math.pi))
            pts.append((x + w, y))
        c.polygon(pts, fill=hair, outline=hair_d, width=0.8)
        c.ellipse(top[0] - 3.2, top[1] - 3.2, top[0] + 3.2, top[1] + 3.2, fill=ribbon)
    # back hair + face
    c.ellipse(cx - r * 0.74, cy - r * 0.78, cx + r * 0.74, cy + r * 0.58, fill=hair,
              outline=hair_d, width=0.8)
    c.ellipse(cx - r * 0.56, cy - r * 0.42, cx + r * 0.56, cy + r * 0.58, fill=skin,
              outline=skin_d, width=0.6)
    # bangs: zig-zag fringe
    pts = [(cx - r * 0.66, cy - r * 0.1)]
    n = 5
    for i in range(n + 1):
        x = cx - r * 0.6 + (r * 1.2) * i / n
        pts.append((x, cy - r * 0.62 + tilt * r * (i - n / 2)))
        if i < n:
            pts.append((x + r * 1.2 / n / 2, cy - r * (0.12 if i % 2 else 0.22)))
    pts.append((cx + r * 0.66, cy - r * 0.1))
    pts.append((cx + r * 0.55, cy - r * 0.8))
    pts.append((cx - r * 0.55, cy - r * 0.8))
    c.polygon(pts, fill=hair)
    # bow on top
    by = cy - r * 0.8
    c.polygon([(cx, by), (cx - r * 0.34, by - r * 0.2), (cx - r * 0.34, by + r * 0.16)],
              fill=t.get("accent", "#ff7eb6"))
    c.polygon([(cx, by), (cx + r * 0.34, by - r * 0.2), (cx + r * 0.34, by + r * 0.16)],
              fill=t.get("accent", "#ff7eb6"))
    c.ellipse(cx - r * 0.08, by - r * 0.08, cx + r * 0.08, by + r * 0.08, fill="#ffffff")

    # eyes
    ey = cy + r * 0.08
    for side in (-1, 1):
        ex = cx + side * r * 0.25
        if mood == "bad":                       # > <
            c.line([(ex - side * r * 0.1, ey - r * 0.1), (ex + side * r * 0.06, ey),
                    (ex - side * r * 0.1, ey + r * 0.1)], eye, width=1.6)
        elif moving and _blink(clock):          # ^ ^ closed
            c.arc(ex - r * 0.12, ey - r * 0.06, ex + r * 0.12, ey + r * 0.14, 200, 340,
                  eye, width=1.6)
        else:
            c.ellipse(ex - r * 0.12, ey - r * 0.17, ex + r * 0.12, ey + r * 0.17, fill=eye)
            c.ellipse(ex - r * 0.09, ey + r * 0.0, ex + r * 0.09, ey + r * 0.15, fill=eye_l)
            c.ellipse(ex - r * 0.08, ey - r * 0.13, ex + r * 0.0, ey - r * 0.04, fill="#ffffff")
            c.ellipse(ex + r * 0.03, ey + r * 0.05, ex + r * 0.07, ey + r * 0.09, fill="#ffffff")
        # blush
        c.ellipse(ex + side * r * 0.04 - r * 0.11, ey + r * 0.2, ex + side * r * 0.04 + r * 0.11,
                  ey + r * 0.29, fill="#ff9ec2", alpha=170)
    # mouth
    my = cy + r * 0.38
    if mood == "bad":
        c.ellipse(cx - r * 0.06, my - r * 0.03, cx + r * 0.06, my + r * 0.09, fill="#c2456f")
    elif mood == "warn":
        c.line([(cx - r * 0.08, my), (cx - r * 0.03, my + r * 0.03), (cx + r * 0.02, my),
                (cx + r * 0.07, my + r * 0.03)], "#c2456f", width=1.1)
    else:                                         # cat mouth
        c.arc(cx - r * 0.1, my - r * 0.06, cx, my + r * 0.05, 10, 170, "#c2456f", width=1.1)
        c.arc(cx, my - r * 0.06, cx + r * 0.1, my + r * 0.05, 10, 170, "#c2456f", width=1.1)
    if mood == "bad":                             # sweat drop
        c.ellipse(cx + r * 0.5, cy - r * 0.3, cx + r * 0.62, cy - r * 0.12, fill="#9fdcff")


def googly(c, cx, cy, r, t, s):
    clock = s.get("clock", 0.0)
    moving = bool(s.get("motion"))
    mood = s.get("mood", "ok")
    look = s.get("look", (0.0, 0.0))
    ink = "#111111"
    body = {"ok": "#b6ff3b", "warn": "#ffb000", "bad": "#ff4f7b"}.get(mood, "#b6ff3b")
    ph = clock * 2.2 if moving else 0
    squash = 1 + (0.06 * math.sin(clock * 6) if moving else 0)
    poke = s.get("poke")
    if poke is not None and poke < 1.2:            # boing!
        squash += 0.35 * math.exp(-4 * poke) * math.sin(poke * 18)
        clock += poke * 6                          # propeller goes brrr
    pts = []
    for i in range(48):
        a = 2 * math.pi * i / 48
        rr = r * 0.78 * (1 + 0.07 * math.sin(3 * a + ph) + 0.05 * math.sin(5 * a - ph * 1.3))
        pts.append((cx + rr * math.cos(a) * squash, cy + 4 + rr * math.sin(a) / squash))
    c.polygon(pts, fill=body, outline=ink, width=1.8)
    # propeller cap
    capy = cy + 4 - r * 0.74
    c.ellipse(cx - r * 0.34, capy - r * 0.22, cx + r * 0.34, capy + r * 0.22, fill="#3d7bff",
              outline=ink, width=1.4)
    c.line([(cx, capy - r * 0.2), (cx, capy - r * 0.42)], ink, width=1.3)
    spin = math.cos(clock * 14) if moving else 1
    bw = r * 0.5 * abs(spin) + 1.5
    c.ellipse(cx - bw, capy - r * 0.48, cx + bw, capy - r * 0.38, fill="#ff2e63", outline=ink,
              width=1)
    # googly eyes (different sizes, pupils follow the mouse and jiggle)
    for ex, er in ((cx - r * 0.28, r * 0.25), (cx + r * 0.26, r * 0.32)):
        ey = cy - r * 0.02
        c.ellipse(ex - er, ey - er, ex + er, ey + er, fill="#ffffff", outline=ink, width=1.4)
        pr = er * 0.48
        jx = math.sin(clock * 9 + ex) * 0.12 if moving else 0
        jy = math.cos(clock * 7.3 + ex) * 0.12 if moving else 0
        dx = max(-1, min(1, look[0] + jx))
        dy = max(-1, min(1, look[1] + jy))
        n = math.hypot(dx, dy) or 1
        reach = (er - pr - 1) * min(1, n)
        px, py = ex + dx / n * reach, ey + dy / n * reach
        c.ellipse(px - pr, py - pr, px + pr, py + pr, fill=ink)
    # mouth
    my = cy + r * 0.4
    if mood == "bad":
        c.ellipse(cx - r * 0.16, my - r * 0.1, cx + r * 0.16, my + r * 0.16, fill=ink)
    else:
        wob = math.sin(clock * 4) * r * 0.04 if moving else 0
        c.line([(cx - r * 0.24, my), (cx - r * 0.08, my + r * 0.08 + wob),
                (cx + r * 0.08, my - wob), (cx + r * 0.24, my + r * 0.07)], ink, width=1.4)
        c.ellipse(cx + r * 0.02, my + r * 0.02, cx + r * 0.14, my + r * 0.16, fill="#ff6fa3",
                  outline=ink, width=1)
