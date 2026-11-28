#!/usr/bin/env python3
"""Friday 27 November 2026 — The World in One Day.

A deterministic program that draws one 1024x1024 front page summing up
27 November 2026 world news. No network, no randomness, no clock: the same
bytes come out on every run. draw.py builds entry.png; main.py (stdlib only) copies it to /output.

All pictures are drawn in code (PIL) from fixed coordinates; the world map
is the supplied colour map (map.png) with pins placed by a lat/lon fit.
Every story is dated Friday 27 November 2026 in UTC (it happened or was
first reported that day). See the DATE CHECK box on the page
for the big older stories deliberately left out.
"""
import math
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = "/output/entry.png"

PAPER = (246, 241, 229)
INK = (25, 23, 19)
RED = (163, 33, 38)
NAVY = (29, 47, 77)
GOLD = (185, 138, 30)
GREY = (90, 86, 78)
LIGHT = (233, 226, 208)
SEA = (207, 227, 234)
LAND = (222, 210, 176)
RULE = (180, 170, 148)

# ---------------------------------------------------------------- fonts
def F(name, size):
    return ImageFont.truetype(os.path.join(BASE, "fonts", name), size)

SERIF_B = "DejaVuSerif-Bold.ttf"
SERIF = "DejaVuSerif.ttf"
SANS_B = "DejaVuSans-Bold.ttf"
SANS = "DejaVuSans.ttf"
SANS_O = "DejaVuSans-Oblique.ttf"

# ---------------------------------------------------------------- helpers
def wrap(text, font, max_w, draw):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def grad(d, box, top, bottom):
    x0, y0, x1, y1 = box
    n = max(1, y1 - y0)
    for i in range(n):
        t = i / n
        c = tuple(int(top[k] + (bottom[k] - top[k]) * t) for k in range(3))
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=c)

def rrect(d, box, fill=None, outline=None, width=1, rad=3):
    d.rounded_rectangle(box, radius=rad, fill=fill, outline=outline, width=width)

def sun(d, cx, cy, r, col=(250, 200, 80)):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)

def cloud(d, x, y, s, col=(250, 250, 248)):
    d.ellipse([x, y, x + 3 * s, y + 1.6 * s], fill=col)
    d.ellipse([x + 0.6 * s, y - 0.8 * s, x + 2.6 * s, y + 1.2 * s], fill=col)
    d.ellipse([x + 1.6 * s, y - 0.4 * s, x + 3.4 * s, y + 1.4 * s], fill=col)

def buildings(d, x, y, w, h, col, lit=(255, 214, 110)):
    """A row of lit-window towers inside (x, y, w, h). Fixed heights."""
    n = 5
    bw = w // n
    hs = [0.55, 0.85, 0.65, 1.0, 0.75]
    for i in range(n):
        bh = int(h * hs[i])
        bx = x + i * bw + 2
        d.rectangle([bx, y + h - bh, bx + bw - 4, y + h], fill=col)
        for wy in range(y + h - bh + 5, y + h - 4, 9):
            for wx in range(bx + 3, bx + bw - 7, 8):
                if (wx + wy) % 17 < 8:
                    d.rectangle([wx, wy, wx + 3, wy + 4], fill=lit)

def tag_chip(d, x, y, tag, font):
    cols = {"CONFIRMED": (31, 110, 46), "REPORTED": (90, 86, 78),
            "CLAIM": (163, 33, 38), "OFFICIAL": (29, 47, 77),
            "FORECAST": (150, 100, 10)}
    c = cols.get(tag, (90, 86, 78))
    tw = d.textlength(tag, font=font)
    d.rounded_rectangle([x, y, x + tw + 10, y + 13], radius=2, fill=c)
    d.text((x + 5, y + 2), tag, font=font, fill=(255, 255, 255))
    return tw + 10

# ---------------------------------------------------------------- data
# Every story below was reported on Friday 27 November 2026 (UTC). Sources and
# times are listed in src/fact_ledger_v3.md. Older stories sit in LEFT_OUT.
# tag letters for the index: C CONFIRMED, R REPORTED, O OFFICIAL, L CLAIM
HEROES = [
    dict(n=1, place="GULF OF OMAN  \u2022  IRAN WAR", scene="ship", reg="MIDDLE EAST",
         head="US disables ship running Iran blockade",
         deck="CENTCOM says the Palau-flagged Pacific Archer was hit at the "
              "stern after leaving Bandar Abbas; crew unharmed. Iran says "
              "Hormuz stays shut.",
         tag="OFFICIAL"),
    dict(n=2, place="NEW YORK  \u2022  MARKETS", scene="wallst", reg="N AMERICA",
         head="S&P 500 ends best week since April 2025",
         deck="Half-day session: S&P +1.6% to 7,297.49, Dow +592 to "
              "50,774.94, Nasdaq +2.3%. The Dow logs its best week since 2022.",
         tag="CONFIRMED"),
    dict(n=3, place="WELLINGTON  \u2022  ELECTION", scene="nzseats", reg="OCEANIA",
         head="NZ coalition ends one seat short",
         deck="Final count: Luxon\u2019s bloc wins 65 of 130 seats, one short "
              "of the 66 needed. Opportunity\u2019s 7 seats now hold the key.",
         tag="OFFICIAL"),
]

CARDS = [
    dict(n=4, place="SHANGHAI", scene="candles", reg="E ASIA",
         head="China stocks log best day since 2024",
         sub="CSI300 +4.2%; chip index +19%", tag="CONFIRMED"),
    dict(n=5, place="TOKYO", scene="skater", reg="E ASIA",
         head="Malinin sets short-program record",
         sub="Beats Chen\u2019s 113.97 (2022)", tag="CONFIRMED"),
    dict(n=6, place="USA", scene="cart", reg="N AMERICA",
         head="Black Friday: $9.7bn spent online",
         sub="Adobe, by 6:30pm ET; up 12.8%", tag="REPORTED"),
    dict(n=7, place="MOMBASA", scene="gavel", reg="AFRICA",
         head="Kenya cult leader guilty over 123 deaths",
         sub="Manslaughter, Shakahola case", tag="CONFIRMED"),
    dict(n=8, place="BERLIN", scene="dome", reg="EUROPE",
         head="Bundestag passes \u20ac556bn 2027 budget",
         sub="Debt \u20ac210bn; defence \u20ac109.7bn", tag="OFFICIAL"),
    dict(n=9, place="OTTAWA", scene="court", reg="N AMERICA",
         head="Canada top court upholds Bill 21",
         sub="Religious-symbols ban stands", tag="OFFICIAL"),
    dict(n=10, place="MADRID", scene="rally", reg="EUROPE",
         head="Spain\u2019s campaign ends; vote Sunday",
         sub="S\u00e1nchez vows to defy polls",
         tag="CONFIRMED"),
    dict(n=11, place="CANARY ISLANDS", scene="boat", reg="EUROPE",
         head="At least 8 dead on migrant boat",
         sub="About 100 people aboard rescued", tag="OFFICIAL"),
    dict(n=12, place="GERMANY", scene="strike", reg="EUROPE",
         head="Amazon strikes hit 11 German sites",
         sub="Protests in 20+ countries", tag="REPORTED"),
    dict(n=13, place="GAZA", scene="gaza", reg="MIDDLE EAST",
         head="Hamas chief\u2019s son survives strike",
         sub="Hamas: several hurt, no deaths", tag="CLAIM"),
]

INDEX = [
    (14, "EUROPE", "Russia fires 155 drones at Ukraine", "O"),
    (15, "EUROPE", "Estonia scrambles NATO jets", "R"),
    (16, "GLOBAL", "UN warns of hunger in 16 hotspots", "O"),
    (17, "GLOBAL", "Brent falls 1.2% to $95.44", "C"),
    (18, "GLOBAL", "OPEC+ set to hold Q1 output", "R"),
    (19, "E ASIA", "Taiwan sees 13.28% growth in 2026", "O"),
    (20, "SE ASIA", "CPTPP opens talks with 3 states", "O"),
    (21, "SE ASIA", "Sara Duterte doubts fair ICC trial", "R"),
    (22, "SE ASIA", "AirAsia delays pay, cuts 90 pilots", "R"),
    (23, "OCEANIA", "NZ 246-5 on day 1 v India", "C"),
    (24, "AFRICA", "Gunmen kill 17 in Nigeria\u2019s Plateau", "O"),
    (25, "AFRICA", "Niger: militants kill 13 soldiers", "O"),
    (26, "S AMERICA", "$18bn regional gas-grid plan", "R"),
    (27, "S ASIA", "Pakistan A reach Rising Stars final", "R"),
]

NUMBERS = [
    ("7,297.49", "S&P 500 CLOSE"),
    ("65 / 130", "NZ COALITION SEATS"),
    ("+4.2%", "CHINA CSI300"),
    ("114.81", "MALININ RECORD"),
    ("$9.7B", "US ONLINE BY 6:30PM ET"),
    ("\u20ac556B", "GERMAN 2027 BUDGET"),
]

REGION_COL = {"N AMERICA": (29, 47, 77), "S AMERICA": (120, 70, 40),
              "EUROPE": (90, 60, 110), "AFRICA": (60, 110, 60),
              "MIDDLE EAST": (150, 100, 10), "S ASIA": (176, 74, 30),
              "E ASIA": (40, 130, 130), "SE ASIA": (31, 110, 46),
              "OCEANIA": (40, 110, 140), "GLOBAL": (90, 86, 78)}

def region_counts():
    """Chip counts are computed from the story lists, never typed by hand."""
    regs = [h["reg"] for h in HEROES] + [c["reg"] for c in CARDS] + \
           [i[1] for i in INDEX]
    return [(r, regs.count(r), REGION_COL[r]) for r in REGION_COL if regs.count(r)]

N_STORIES = len(HEROES) + len(CARDS) + len(INDEX)

LEFT_OUT = [
    "Kuwait drone kills two Italians \u2014 Thu 26 Nov",
    "US Thanksgiving storm outages \u2014 Thu 26 Nov",
    "Ibiza diesel tanker capsizes \u2014 Thu 26 Nov",
    "Depardieu sent for rape trial \u2014 Thu 26 Nov",
    "Bangkok refinery blast \u2014 Thu 26 Nov",
    "Chess title Game 3 drawn \u2014 Thu 26 Nov",
    "UK net migration 77,000 (ONS) \u2014 Thu 26 Nov",
    "EU budget summit collapses \u2014 Thu 26 Nov",
    "Serbia calls presidential vote \u2014 Thu 26 Nov",
    "Tokyo CPI 2.9% \u2014 out 23:30 UTC Thu 26 Nov",
    "India cabinet Rs 11,000-crore plan \u2014 Wed 25 Nov",
    "Congo Ebola passes 12,000 \u2014 Wed 25 Nov",
]

UTC_ITEMS = ("01:00 NZ final count  \u2022  03:00 Gaza dawn strike  \u2022  07:00 "
             "China stocks close  \u2022  15:00 Bill 21 ruling  \u2022  18:00 Wall "
             "St half-day close  \u2022  23:30 Adobe: $9.7bn online")

# ---------------------------------------------------------------- scenes
# Flat-vector painters. One light source for every scene: upper left. Lit faces
# use the base colour + LIFT, shaded faces the base colour - DROP. Nothing
# random, nothing from the clock.
def lit(c, k=28):
    return tuple(min(255, v + k) for v in c)

def shade(c, k=34):
    return tuple(max(0, v - k) for v in c)

def scene_ship(d, x, y, w, h):
    grad(d, (x, y, x + w, y + int(h * 0.55)), (232, 170, 110), (250, 214, 160))
    grad(d, (x, y + int(h * 0.55), x + w, y + h), (52, 96, 128), (28, 58, 86))
    sun(d, x + 40, y + 24, 13, (255, 236, 190))
    hz = y + int(h * 0.55)
    d.polygon([(x + w * 0.62, hz), (x + w * 0.70, hz - 9), (x + w * 0.80, hz - 6),
               (x + w * 0.92, hz - 12), (x + w, hz - 8), (x + w, hz)],
              fill=(150, 120, 100))
    # cargo ship, bow left, stern right
    hx0, hx1, hy = x + int(w * 0.12), x + int(w * 0.70), hz + 12
    hull = (60, 66, 76)
    d.polygon([(hx0, hy - 10), (hx1, hy - 10), (hx1 - 6, hy + 10), (hx0 + 16, hy + 10)],
              fill=hull)
    d.line([(hx0, hy - 10), (hx1, hy - 10)], fill=lit(hull, 60), width=2)
    d.rectangle([hx0 + 14, hy + 6, hx1 - 8, hy + 10], fill=(150, 40, 36))
    cols = [(196, 70, 50), (40, 96, 150), (210, 160, 50), (60, 130, 90)]
    for i in range(7):
        bx = hx0 + 22 + i * 21
        c = cols[i % 4]
        d.rectangle([bx, hy - 24, bx + 18, hy - 11], fill=c)
        d.rectangle([bx, hy - 24, bx + 18, hy - 22], fill=lit(c))
        d.rectangle([bx + 15, hy - 22, bx + 18, hy - 11], fill=shade(c))
    sx = hx1 - 34
    d.rectangle([sx, hy - 40, sx + 22, hy - 11], fill=(236, 232, 222))
    d.rectangle([sx + 18, hy - 40, sx + 22, hy - 11], fill=(196, 190, 178))
    d.rectangle([sx + 3, hy - 36, sx + 17, hy - 32], fill=(40, 50, 60))
    d.rectangle([sx + 6, hy - 50, sx + 12, hy - 40], fill=(60, 60, 64))
    # hit at the stern: flash + smoke drifting downwind
    fx, fy = hx1 - 4, hy - 6
    d.ellipse([fx - 12, fy - 12, fx + 12, fy + 12], fill=(255, 150, 40))
    d.ellipse([fx - 6, fy - 6, fx + 6, fy + 6], fill=(255, 232, 120))
    for i, r in enumerate([9, 12, 15, 18]):
        cx = fx + 10 + i * 16
        cy = fy - 18 - i * 9
        d.ellipse([cx - r, cy - r * 0.8, cx + r, cy + r * 0.8], fill=(90 - i * 6, 86 - i * 6, 84 - i * 6))
    # stopped: no wake, only ripples
    for i in range(3):
        yy = hy + 16 + i * 6
        d.line([(hx0 + 10 + i * 8, yy), (hx1 - 20 - i * 8, yy)], fill=(90, 140, 170), width=1)
    # small US warship on the horizon
    d.polygon([(x + 12, hz + 2), (x + 70, hz + 2), (x + 64, hz + 7), (x + 18, hz + 7)],
              fill=(110, 116, 126))
    d.rectangle([x + 36, hz - 6, x + 50, hz + 2], fill=(110, 116, 126))
    d.line([(x + 43, hz - 14), (x + 43, hz - 6)], fill=(110, 116, 126), width=2)


def scene_wallst(d, x, y, w, h):
    grad(d, (x, y, x + w, y + h), (24, 44, 70), (44, 70, 100))
    # exchange facade: pediment + 6 columns, lit from the left
    fx0, fx1 = x + 16, x + int(w * 0.46)
    stone = (214, 206, 188)
    d.polygon([(fx0 - 4, y + 34), ((fx0 + fx1) // 2, y + 14), (fx1 + 4, y + 34)], fill=stone)
    d.polygon([((fx0 + fx1) // 2, y + 14), (fx1 + 4, y + 34), ((fx0 + fx1) // 2, y + 34)],
              fill=shade(stone, 24))
    d.rectangle([fx0 - 4, y + 34, fx1 + 4, y + 39], fill=shade(stone, 40))
    cw = (fx1 - fx0) / 6
    for i in range(6):
        cx = int(fx0 + i * cw + cw * 0.2)
        d.rectangle([cx, y + 39, cx + int(cw * 0.6), y + h - 14], fill=stone)
        d.rectangle([cx + int(cw * 0.42), y + 39, cx + int(cw * 0.6), y + h - 14],
                    fill=shade(stone, 30))
    d.rectangle([fx0 - 8, y + h - 14, fx1 + 8, y + h - 8], fill=shade(stone, 40))
    # flag
    d.line([(fx1 - 6, y + 14), (fx1 - 6, y - 0)], fill=(200, 200, 200), width=1)
    # ticker board: green rising line and week arrow
    bx0, by0, bx1, by1 = x + int(w * 0.52), y + 10, x + w - 10, y + h - 10
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=4, fill=(10, 20, 30),
                        outline=(70, 90, 110))
    for i in range(1, 4):
        yy = by0 + i * (by1 - by0) // 4
        d.line([(bx0 + 6, yy), (bx1 - 6, yy)], fill=(30, 48, 62), width=1)
    pts = [(0.0, 0.80), (0.16, 0.72), (0.30, 0.76), (0.46, 0.55), (0.60, 0.50),
           (0.76, 0.34), (0.90, 0.22), (1.0, 0.14)]
    pw, ph = bx1 - bx0 - 16, by1 - by0 - 16
    P = [(bx0 + 8 + fx * pw, by0 + 8 + fy * ph) for fx, fy in pts]
    d.polygon(P + [(bx1 - 8, by1 - 8), (bx0 + 8, by1 - 8)], fill=(20, 70, 46))
    d.line(P, fill=(80, 230, 120), width=3, joint="curve")
    d.text((bx0 + 10, by0 + 6), "S&P 500  +5.6% WEEK", font=F(SANS_B, 11),
           fill=(150, 255, 170))


def scene_nzseats(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(236, 230, 214))
    # 130 seats in a hemicycle: 65 coalition (navy) | 7 Opportunity (gold) | 58 left (red)
    cx, cy = x + w // 2, y + h - 10
    rows = [(46, 24), (55, 30), (64, 36), (73, 40)]
    seats = []
    for r, n in rows:
        for k in range(n):
            a = 3.14159 * (k + 0.5) / n
            seats.append((a, r))
    seats.sort(key=lambda s: -s[0])          # left to right
    for i, (a, r) in enumerate(seats):
        if i < 65:
            col = (29, 47, 77)
        elif i < 72:
            col = (205, 150, 30)
        else:
            col = (180, 40, 44)
        sx = cx + r * math.cos(a) * 1.85
        sy = cy - r * math.sin(a) * 0.85
        d.ellipse([sx - 3, sy - 3, sx + 3, sy + 3], fill=col)
        d.ellipse([sx - 2, sy - 3, sx, sy - 1], fill=lit(col, 50))
    fb = F(SANS_B, 12)
    d.text((x + 34, y + 4), "COALITION 65", font=fb, fill=(29, 47, 77))
    t = "LEFT 58"
    d.text((x + w - 8 - d.textlength(t, font=fb), y + 6), t, font=fb, fill=(180, 40, 44))
    t = "OPPORTUNITY 7"
    d.text((cx - d.textlength(t, font=F(SANS_B, 10)) / 2, cy - 30), t,
           font=F(SANS_B, 10), fill=(150, 100, 10))
    t = "66 for majority"
    d.text((cx - d.textlength(t, font=F(SANS, 10)) / 2, cy - 17), t,
           font=F(SANS, 10), fill=(90, 86, 78))


def scene_candles(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(28, 22, 26))
    vals = [(0.62, 0.70), (0.66, 0.60), (0.58, 0.64), (0.62, 0.52), (0.50, 0.56),
            (0.54, 0.40), (0.40, 0.30), (0.30, 0.12)]
    cw = (w - 40) / len(vals)
    for i, (o, c) in enumerate(vals):
        bx = x + 30 + i * cw
        up = c < o
        col = (226, 52, 48) if up else (40, 170, 90)     # China: red = up
        top, bot = y + min(o, c) * h, y + max(o, c) * h
        d.line([(bx + cw * 0.35, top - 4), (bx + cw * 0.35, bot + 4)], fill=col, width=1)
        d.rectangle([bx + cw * 0.15, top, bx + cw * 0.55, bot], fill=col)
    d.text((x + 28, y + 4), "CSI300 +4.2%", font=F(SANS_B, 12), fill=(255, 110, 90))


def scene_skater(d, x, y, w, h):
    grad(d, (x, y, x + w, y + h), (30, 50, 96), (120, 160, 210))
    d.ellipse([x - 20, y + h - 14, x + w + 20, y + h + 30], fill=(226, 238, 248))
    # spin trails
    for i, r in enumerate([20, 15, 10]):
        d.arc([x + w // 2 - r * 2, y + h - 18 - r, x + w // 2 + r * 2, y + h - 18 + r // 2],
              200, 340, fill=(255, 255, 255), width=1)
    # skater mid-jump, arms in
    cx, cy = x + w // 2, y + 18
    d.ellipse([cx - 4, cy - 12, cx + 4, cy - 4], fill=(230, 190, 160))
    d.polygon([(cx - 5, cy - 3), (cx + 5, cy - 3), (cx + 4, cy + 12), (cx - 4, cy + 12)],
              fill=(20, 24, 40))
    d.line([(cx - 2, cy + 12), (cx - 7, cy + 24)], fill=(20, 24, 40), width=3)
    d.line([(cx + 2, cy + 12), (cx + 9, cy + 22)], fill=(20, 24, 40), width=3)
    d.line([(cx - 10, cy + 25), (cx - 3, cy + 25)], fill=(220, 220, 230), width=2)
    d.text((x + 28, y + 4), "114.81", font=F(SANS_B, 14), fill=(255, 225, 120))
    d.text((x + w - 66, y + 6), "RECORD", font=F(SANS_B, 11), fill=(255, 255, 255))


def scene_cart(d, x, y, w, h):
    grad(d, (x, y, x + w, y + h), (26, 26, 32), (60, 30, 40))
    # laptop with a checkout screen
    lx0, lx1 = x + 22, x + 112
    d.rectangle([lx0, y + 6, lx1, y + h - 12], fill=(200, 204, 210))
    d.rectangle([lx0 + 4, y + 10, lx1 - 4, y + h - 16], fill=(250, 250, 248))
    d.rectangle([lx0 + 4, y + 10, lx1 - 4, y + 16], fill=(200, 40, 44))
    d.text((lx0 + 8, y + 17), "BUY NOW", font=F(SANS_B, 9), fill=(25, 23, 19))
    d.rectangle([lx0 + 54, y + 18, lx1 - 8, y + 27], fill=(40, 140, 80))
    d.polygon([(lx0 - 10, y + h - 12), (lx1 + 10, y + h - 12), (lx1 + 4, y + h - 6),
               (lx0 - 4, y + h - 6)], fill=(150, 154, 160))
    # trolley icon
    tx = x + 130
    d.line([(tx, y + 12), (tx + 8, y + 12), (tx + 14, y + 32), (tx + 44, y + 32),
            (tx + 48, y + 18), (tx + 10, y + 18)], fill=(255, 205, 80), width=3)
    d.ellipse([tx + 14, y + 35, tx + 20, y + 41], fill=(255, 205, 80))
    d.ellipse([tx + 38, y + 35, tx + 44, y + 41], fill=(255, 205, 80))


def scene_gavel(d, x, y, w, h):
    grad(d, (x, y, x + w, y + h), (120, 82, 50), (70, 44, 26))
    wood = (150, 96, 50)
    d.rectangle([x + 40, y + h - 12, x + 110, y + h - 4], fill=lit(wood, 40))
    d.rectangle([x + 40, y + h - 6, x + 110, y + h - 4], fill=shade(wood))
    # gavel head (rotated block) + handle
    d.polygon([(x + 66, y + 10), (x + 94, y + 4), (x + 100, y + 22), (x + 72, y + 28)],
              fill=lit(wood, 30))
    d.polygon([(x + 72, y + 28), (x + 100, y + 22), (x + 101, y + 26), (x + 73, y + 32)],
              fill=shade(wood))
    d.line([(x + 86, y + 20), (x + 150, y + 40)], fill=(110, 70, 36), width=5)
    d.text((x + 120, y + 6), "123", font=F(SERIF_B, 18), fill=(250, 230, 190))
    d.line([(x + 50, y + 32), (x + 44, y + 30)], fill=(250, 230, 190), width=2)
    d.line([(x + 54, y + 38), (x + 46, y + 40)], fill=(250, 230, 190), width=2)


def scene_dome(d, x, y, w, h):
    grad(d, (x, y, x + w, y + h), (150, 180, 210), (215, 222, 228))
    stone = (200, 190, 170)
    d.rectangle([x + 20, y + 26, x + w - 20, y + h - 4], fill=stone)
    d.rectangle([x + w - 34, y + 26, x + w - 20, y + h - 4], fill=shade(stone, 26))
    for i in range(6):
        cx = x + 48 + i * 18
        d.rectangle([cx, y + 30, cx + 6, y + h - 6], fill=lit(stone, 30))
        d.rectangle([cx + 4, y + 30, cx + 6, y + h - 6], fill=shade(stone, 20))
    # glass dome
    d.chord([x + w // 2 - 26, y + 2, x + w // 2 + 26, y + 50], 180, 360, fill=(170, 210, 230))
    for k in range(-2, 3):
        d.line([(x + w // 2 + k * 9, y + 26), (x + w // 2 + k * 5, y + 4)], fill=(110, 140, 160))
    d.chord([x + w // 2 + 2, y + 2, x + w // 2 + 26, y + 50], 270, 360, fill=(140, 180, 205))
    # flag colours band
    for i, c in enumerate([(20, 20, 20), (200, 30, 30), (240, 200, 40)]):
        d.rectangle([x + 22, y + 20 + i * 2, x + 46, y + 22 + i * 2], fill=c)
    d.text((x + w - 62, y + 4), "\u20ac556bn", font=F(SANS_B, 11), fill=(29, 47, 77))


def scene_court(d, x, y, w, h):
    grad(d, (x, y, x + w, y + h), (180, 200, 220), (230, 226, 214))
    stone = (214, 206, 188)
    d.rectangle([x + 46, y + 22, x + 144, y + h - 6], fill=stone)
    d.rectangle([x + 132, y + 22, x + 144, y + h - 6], fill=shade(stone, 28))
    # copper-green roof (Supreme Court of Canada)
    roof = (90, 160, 140)
    d.polygon([(x + 40, y + 22), (x + 95, y + 2), (x + 150, y + 22)], fill=roof)
    d.polygon([(x + 95, y + 2), (x + 150, y + 22), (x + 95, y + 22)], fill=shade(roof, 26))
    for i in range(5):
        cx = x + 56 + i * 18
        d.rectangle([cx, y + 26, cx + 6, y + h - 8], fill=lit(stone, 24))
    # maple leaf flag
    d.rectangle([x + 162, y + 8, x + 186, y + 20], fill=(255, 255, 255))
    d.rectangle([x + 162, y + 8, x + 167, y + 20], fill=(210, 30, 36))
    d.rectangle([x + 181, y + 8, x + 186, y + 20], fill=(210, 30, 36))
    d.polygon([(x + 174, y + 9), (x + 177, y + 14), (x + 174, y + 19), (x + 171, y + 14)],
              fill=(210, 30, 36))
    d.line([(x + 162, y + 8), (x + 162, y + h - 6)], fill=(90, 86, 78), width=1)
    d.text((x + 20, y + 22), "7", font=F(SERIF_B, 16), fill=(29, 47, 77))
    d.text((x + 16, y + 38), "judges", font=F(SANS, 8), fill=(29, 47, 77))


def scene_rally(d, x, y, w, h):
    grad(d, (x, y, x + w, y + h), (40, 24, 50), (120, 40, 50))
    # stage lights
    for lx in (x + 30, x + 95, x + 160):
        d.polygon([(lx - 3, y), (lx + 3, y), (lx + 18, y + h), (lx - 18, y + h)],
                  fill=(90, 50, 70))
    # crowd silhouettes with Spanish flags
    for i in range(12):
        hx = x + 6 + i * 16
        d.ellipse([hx, y + h - 18, hx + 10, y + h - 8], fill=(24, 14, 22))
        d.rectangle([hx - 1, y + h - 9, hx + 11, y + h], fill=(24, 14, 22))
    for fx in (x + 26, x + 92, x + 150):
        d.line([(fx, y + h - 14), (fx, y + 12)], fill=(180, 170, 160), width=1)
        d.rectangle([fx + 1, y + 12, fx + 19, y + 15], fill=(200, 30, 36))
        d.rectangle([fx + 1, y + 15, fx + 19, y + 21], fill=(250, 200, 40))
        d.rectangle([fx + 1, y + 21, fx + 19, y + 24], fill=(200, 30, 36))
    d.text((x + w - 48, y + 4), "29 NOV", font=F(SANS_B, 10), fill=(255, 230, 160))


def scene_boat(d, x, y, w, h):
    grad(d, (x, y, x + w, y + h), (120, 160, 190), (30, 70, 110))
    for i in range(4):
        yy = y + 30 + i * 5
        d.line([(x, yy), (x + w, yy)], fill=(70, 110, 150), width=1)
    # crowded open boat (cayuco)
    d.polygon([(x + 30, y + 24), (x + 140, y + 24), (x + 128, y + 36), (x + 42, y + 36)],
              fill=(210, 120, 40))
    d.line([(x + 30, y + 24), (x + 140, y + 24)], fill=(240, 170, 90), width=2)
    for i in range(12):
        px = x + 38 + i * 8
        d.ellipse([px, y + 14, px + 6, y + 20], fill=(40, 34, 30))
        d.rectangle([px, y + 19, px + 6, y + 24], fill=(220, 140, 40) if i % 3 == 0 else (60, 60, 80))
    # rescue vessel, orange hull (Salvamento Maritimo)
    d.polygon([(x + 146, y + 26), (x + 186, y + 26), (x + 182, y + 36), (x + 150, y + 36)],
              fill=(240, 110, 30))
    d.rectangle([x + 158, y + 16, x + 176, y + 26], fill=(250, 250, 248))
    d.rectangle([x + 172, y + 16, x + 176, y + 26], fill=(205, 205, 200))


def scene_strike(d, x, y, w, h):
    grad(d, (x, y, x + w, y + h), (150, 165, 180), (205, 205, 200))
    # warehouse
    shed = (120, 128, 138)
    d.rectangle([x + 8, y + 10, x + w - 8, y + h - 12], fill=shed)
    d.rectangle([x + w - 26, y + 10, x + w - 8, y + h - 12], fill=shade(shed, 24))
    for i in range(4):
        d.rectangle([x + 18 + i * 34, y + 22, x + 42 + i * 34, y + h - 12], fill=(80, 86, 96))
    # pickets
    for i, px in enumerate((x + 44, x + 86, x + 128, x + 170)):
        d.line([(px, y + h - 2), (px, y + 18)], fill=(90, 70, 50), width=2)
        d.rectangle([px - 14, y + 6, px + 14, y + 20], fill=(255, 255, 255),
                    outline=(200, 30, 36))
        d.text((px - 12, y + 8), "STRIKE", font=F(SANS_B, 7), fill=(200, 30, 36))
        d.ellipse([px - 4, y + h - 14, px + 4, y + h - 6], fill=(40, 34, 30))


def scene_gaza(d, x, y, w, h):
    grad(d, (x, y, x + w, y + h), (60, 54, 80), (210, 140, 90))
    # apartment blocks at dawn, one struck
    blocks = [(0.02, 0.18, 0.55), (0.22, 0.16, 0.75), (0.40, 0.20, 0.62),
              (0.62, 0.16, 0.80), (0.80, 0.18, 0.58)]
    for i, (bx, bw, bh) in enumerate(blocks):
        c = (40, 34, 42)
        x0, x1 = x + int(w * bx), x + int(w * (bx + bw))
        y0 = y + h - int(h * bh)
        d.rectangle([x0, y0, x1, y + h], fill=c)
        d.rectangle([x0, y0, x0 + 3, y + h], fill=lit(c, 30))
        for wy in range(y0 + 5, y + h - 4, 8):
            for wx in range(x0 + 6, x1 - 4, 8):
                d.rectangle([wx, wy, wx + 2, wy + 3], fill=(90, 80, 70))
    sx0, sx1 = x + int(w * 0.40), x + int(w * 0.60)
    sy = y + h - int(h * 0.62)
    d.polygon([(sx0 + 8, sy), (sx0 + 16, sy + 8), (sx0 + 26, sy + 2), (sx1 - 4, sy + 10),
               (sx1 - 4, sy - 1)], fill=(255, 150, 50))
    for i, r in enumerate([7, 9, 11]):
        cx, cy = sx0 + 20 + i * 4, sy - 8 - i * 9
        d.ellipse([cx - r, cy - r * 0.8, cx + r, cy + r * 0.8], fill=(110, 100, 98))


def blit(img, name, x, y, w, h):
    tile = Image.new("RGB", (w, h), PAPER)
    td = ImageDraw.Draw(tile)
    SCENES[name](td, 0, 0, w, h)
    img.paste(tile, (x, y))

SCENES = {"ship": scene_ship, "wallst": scene_wallst, "nzseats": scene_nzseats,
          "candles": scene_candles, "skater": scene_skater, "cart": scene_cart,
          "gavel": scene_gavel, "dome": scene_dome, "court": scene_court,
          "rally": scene_rally, "boat": scene_boat, "strike": scene_strike,
          "gaza": scene_gaza}

# ---------------------------------------------------------------- map
# story number -> (lon, lat) of the real place
PINS = {1: (57.9, 24.6),      # Gulf of Oman, off Bandar Abbas/Hormuz approaches
        2: (-74.01, 40.71),   # NYSE, New York
        3: (174.78, -41.29),  # Wellington
        4: (121.47, 31.23),   # Shanghai
        5: (139.69, 35.68),   # Tokyo
        6: (-98.0, 39.0),     # USA (nationwide online sales)
        7: (39.67, -4.04),    # Mombasa
        8: (13.38, 52.52),    # Berlin
        9: (-75.70, 45.42),   # Ottawa
        10: (-3.70, 40.42),   # Madrid
        11: (-15.4, 28.1),    # Canary Islands
        12: (9.7, 50.9),      # Germany (Bad Hersfeld, Amazon site)
        13: (34.45, 31.50)}   # Gaza
PIN_OFF = {1: (10, 9), 2: (12, 4), 3: (-11, -4), 4: (-8, 9), 5: (10, -6),
           6: (-8, 10), 7: (10, 6), 8: (11, -9), 9: (-6, -13), 10: (3, 14),
           11: (-14, -3), 12: (-7, -14), 13: (-4, 13)}

# Obenk's colour-coded world map (his screenshot, cropped to lon -180..180,
# lat ~80N..57S). Pins use a lat/lon fit on 12 grounded cities (equirectangular,
# rms ~6 px on the 1113 px source) plus an inverse-distance residual correction.
MAP_FIT = dict(ax=3.0279813817141754, bx=539.6389747783718,
               ay=-3.1622554035875488, by=281.575468661099, x0=0, y0=25)
MAP_REF = [  # (lat, lon, true source x, true source y)
    (51.51, -0.13, 528.7, 113.8), (30.04, 31.24, 646.7, 189.8),
    (35.68, 139.69, 957.2, 164.8), (-33.87, 151.21, 996.1, 384.1),
    (40.71, -74.0, 318.3, 162.6), (-22.91, -43.17, 405.1, 344.1),
    (-33.92, 18.42, 596.6, 394.1), (1.35, 103.82, 857.0, 271.4),
    (19.08, 72.88, 770.2, 221.4), (-55.98, -67.27, 339.5, 462.3),
    (-41.29, 174.78, 1062.9, 417.4), (61.22, -149.9, 80.1, 89.9),
    (29.3, 47.9, 690.1, 198.1), (13.75, 100.5, 850.3, 245.9),
    (38.9, -77.0, 307.2, 169.3), (27.7, 85.3, 804.7, 203.1),
    (39.0, 1.4, 546.5, 168.2)]
MAP_LEGEND = [("AMERICAS", (169, 194, 228)), ("EUROPE", (196, 181, 222)),
              ("AFRICA", (245, 190, 150)), ("ASIA + MID-EAST", (241, 234, 163)),
              ("SE ASIA + OCEANIA", (183, 221, 186))]

def map_px(lat, lon):
    f = MAP_FIT
    x = f["ax"] * lon + f["bx"]
    y = f["ay"] * lat + f["by"]
    wsum = dx = dy = 0.0
    for rla, rlo, rx, ry in MAP_REF:
        ex = rx - (f["ax"] * rlo + f["bx"])
        ey = ry - (f["ay"] * rla + f["by"])
        dist2 = (rla - lat) ** 2 + (rlo - lon) ** 2
        if dist2 < 1e-6:
            return rx - f["x0"], ry - f["y0"]
        wt = 1.0 / dist2
        wsum += wt; dx += wt * ex; dy += wt * ey
    return x + dx / wsum - f["x0"], y + dy / wsum - f["y0"]

def draw_map(img, d, x, y, w, h):
    base = Image.open(os.path.join(BASE, "map.png")).convert("RGB")
    s = w / base.width
    mh = round(base.height * s)
    d.rectangle([x, y, x + w, y + h], fill=(183, 224, 246))
    img.paste(base.resize((w, mh), Image.LANCZOS), (x, y))
    # colour key in the strip under the map
    fk = F(SANS_B, 9)
    kx, ky = x + 6, y + mh + 6
    for name, col in MAP_LEGEND:
        tw = d.textlength(name, font=fk)
        if kx + 14 + tw > x + w - 4:
            kx, ky = x + 6, ky + 15
        d.rectangle([kx, ky + 1, kx + 10, ky + 10], fill=col, outline=(90, 86, 78))
        d.text((kx + 14, ky), name, font=fk, fill=INK)
        kx += 14 + tw + 12
    fnum = F(SANS_B, 10)
    for n, (lon, lat) in PINS.items():
        sx, sy = map_px(lat, lon)
        px, py = x + sx * s, y + sy * s
        ox, oy = PIN_OFF.get(n, (0, 0))
        bx, by = px + ox, py + oy
        d.line([px, py, bx, by], fill=INK, width=1)
        d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=INK)
        d.ellipse([bx - 8, by - 8, bx + 8, by + 8], fill=RED,
                  outline=(255, 255, 255), width=1)
        t = str(n)
        tw = d.textlength(t, font=fnum)
        d.text((bx - tw / 2, by - 5), t, font=fnum, fill=(255, 255, 255))

# ---------------------------------------------------------------- page
def build():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W - 1, H - 1], outline=NAVY, width=3)

    # ---- top strap
    d.rectangle([3, 3, W - 4, 27], fill=RED)
    fstrap = F(SANS_B, 13)
    d.text((14, 8), "THE WORLD IN ONE DAY", font=fstrap, fill=(255, 255, 255))
    nreg = len([r for r in region_counts() if r[0] != "GLOBAL"])
    mid = "%d STORIES  \u2022  %d REGIONS + GLOBAL  \u2022  EVERY ONE DATED 27 NOV (UTC)" % (N_STORIES, nreg)
    mw = d.textlength(mid, font=fstrap)
    d.text(((W - mw) / 2, 8), mid, font=fstrap, fill=(255, 225, 150))
    d.text((W - 162, 8), "FRIDAY 27 NOV 2026", font=fstrap, fill=(255, 255, 255))
    y = 35

    # ---- masthead: full-width date glyph
    size = 72
    while size > 58:
        fdate = F(SERIF_B, size)
        if d.textlength("Friday 27 November 2026", font=fdate) <= 990:
            break
        size -= 2
    fdate = F(SERIF_B, size)
    tw = d.textlength("Friday 27 November 2026", font=fdate)
    d.text(((W - tw) / 2, y), "Friday 27 November 2026", font=fdate, fill=INK)
    y += size + 4
    fdeck = F(SERIF, 16)
    deck = ("US disables an Iran blockade runner, Wall St has its best week since "
            "April 2025, NZ coalition falls one seat short")
    tw = d.textlength(deck, font=fdeck)
    if tw > W - 32:
        raise ValueError("deck too long")
    d.text(((W - tw) / 2, y), deck, font=fdeck, fill=(60, 56, 48))
    y += 22
    d.line([16, y, W - 16, y], fill=RED, width=2)
    y += 6

    # ---- DAY IN UTC strip
    futcb = F(SANS_B, 11)
    label = "THE DAY IN UTC  \u2022  "
    lw = d.textlength(label, font=futcb)
    rest = UTC_ITEMS
    usz = 11
    while usz > 8:
        futc = F(SANS, usz)
        if lw + d.textlength(rest, font=futc) <= 990:
            break
        usz -= 1
    futc = F(SANS, usz)
    total = lw + d.textlength(rest, font=futc)
    x0 = int((W - total) / 2)
    d.text((x0, y), label, font=futcb, fill=RED)
    d.text((x0 + lw, y), rest, font=futc, fill=INK)
    y += 18
    d.line([16, y, W - 16, y], fill=RULE, width=1)
    y += 5

    # ---- numbers strip
    fnum = F(SERIF_B, 25)
    flab = F(SANS_B, 9)
    cw = (W - 32) / 6
    for i, (num, lab) in enumerate(NUMBERS):
        cx = 16 + i * cw
        nw = d.textlength(num, font=fnum)
        d.text((cx + (cw - nw) / 2, y), num, font=fnum, fill=RED)
        lw2 = d.textlength(lab, font=flab)
        d.text((cx + (cw - lw2) / 2, y + 29), lab, font=flab, fill=GREY)
        if i:
            d.line([cx, y + 2, cx, y + 42], fill=RULE, width=1)
    y += 44
    d.line([16, y, W - 16, y], fill=RULE, width=1)
    y += 5

    # ---- region chips
    fchip = F(SANS_B, 11)
    chips = []
    for name, cnt, col in region_counts():
        t = "%s %d" % (name, cnt)
        chips.append((t, col, d.textlength(t, font=fchip) + 16))
    tot = sum(w for _, _, w in chips) + 6 * (len(chips) - 1)
    cx = int((W - tot) / 2)
    for t, col, w in chips:
        d.rounded_rectangle([cx, y, cx + w, y + 18], radius=3, fill=col)
        d.text((cx + 8, y + 3), t, font=fchip, fill=(255, 255, 255))
        cx += w + 6
    y += 24

    # ---- heroes: 3 columns, pictorial scene + headline + deck
    hero_y = y
    col_w, gap = 324, 10
    x0 = int((W - (3 * col_w + 2 * gap)) / 2)
    fkick = F(SANS_B, 11)
    fhead = F(SERIF_B, 21)
    fdeck2 = F(SANS, 12)
    ftag = F(SANS_B, 8)
    scene_h = 100
    for i, hro in enumerate(HEROES):
        hx = x0 + i * (col_w + gap)
        blit(img, hro["scene"], hx, hero_y, col_w, scene_h)
        # numbered badge on the scene
        d.ellipse([hx + 5, hero_y + 5, hx + 27, hero_y + 27], fill=RED,
                  outline=(255, 255, 255), width=1)
        t = str(hro["n"])
        tw2 = d.textlength(t, font=F(SANS_B, 12))
        d.text((hx + 16 - tw2 / 2, hero_y + 10), t, font=F(SANS_B, 12),
               fill=(255, 255, 255))
        ky = hero_y + scene_h + 6
        d.text((hx, ky), hro["place"], font=fkick, fill=RED)
        tag_chip(d, hx + col_w - 62, ky, hro["tag"], ftag)
        hy = ky + 17
        for ln in wrap(hro["head"], fhead, col_w, d)[:2]:
            d.text((hx, hy), ln, font=fhead, fill=INK)
            hy += 24
        hy += 2
        if len(wrap(hro["deck"], fdeck2, col_w, d)) > 3 or \
                len(wrap(hro["head"], fhead, col_w, d)) > 2:
            raise ValueError("hero text too long: %r" % hro["head"])
        for ln in wrap(hro["deck"], fdeck2, col_w, d)[:3]:
            d.text((hx, hy), ln, font=fdeck2, fill=(60, 56, 48))
            hy += 15
    y = hero_y + scene_h + 6 + 17 + 48 + 2 + 45
    d.line([16, y, W - 16, y], fill=RED, width=2)
    y += 7

    # ---- cards: 2 rows x 5
    card_w, card_gap = 190, 10
    cx0 = int((W - (5 * card_w + 4 * card_gap)) / 2)
    fck = F(SANS_B, 10)
    fch = F(SERIF_B, 13)
    fsub = F(SANS, 11)
    scene_h2 = 48
    for row in range(2):
        row_y = y
        for col in range(5):
            c = CARDS[row * 5 + col]
            x = cx0 + col * (card_w + card_gap)
            blit(img, c["scene"], x, row_y, card_w, scene_h2)
            d.ellipse([x + 4, row_y + 4, x + 22, row_y + 22], fill=RED,
                      outline=(255, 255, 255), width=1)
            t = str(c["n"])
            tw2 = d.textlength(t, font=F(SANS_B, 10))
            d.text((x + 13 - tw2 / 2, row_y + 8), t, font=F(SANS_B, 10),
                   fill=(255, 255, 255))
            ky = row_y + scene_h2 + 4
            d.text((x, ky), c["place"].split("  \u2022  ")[0], font=fck, fill=RED)
            tag_chip(d, x + card_w - 58, ky, c["tag"], ftag)
            hy = ky + 14
            for ln in wrap(c["head"], fch, card_w, d)[:2]:
                d.text((x, hy), ln, font=fch, fill=INK)
                hy += 16
            if d.textlength(c["sub"], font=fsub) > card_w:
                raise ValueError("card sub too long: %r" % c["sub"])
            if len(wrap(c["head"], fch, card_w, d)) > 2:
                raise ValueError("card head too long: %r" % c["head"])
            for ln in wrap(c["sub"], fsub, card_w, d)[:1]:
                d.text((x, hy), ln, font=fsub, fill=(60, 56, 48))
                hy += 13
        y = row_y + scene_h2 + 4 + 14 + 30 + 12 + 4
        if row == 0:
            y += 4
    d.line([16, y, W - 16, y], fill=RULE, width=1)
    y += 5

    # ---- map + index header
    fsec = F(SANS_B, 13)
    d.text((16, y), "WHERE IT HAPPENED", font=fsec, fill=INK)
    d.text((16 + d.textlength("WHERE IT HAPPENED", font=fsec) + 8, y),
           "\u2014 pins match story numbers", font=F(SANS, 11), fill=GREY)
    ix = 358
    d.text((ix, y), "ALSO ON FRIDAY 27 NOVEMBER \u2014 %d MORE STORIES" % len(INDEX),
           font=fsec, fill=INK)
    y += 19
    map_y = y
    map_h = 182
    draw_map(img, d, 16, map_y, 330, map_h)
    d.rectangle([16, map_y, 346, map_y + map_h], outline=RULE, width=1)
    # index, two columns
    fidx = F(SANS, 12)
    fidxb = F(SANS_B, 11)
    fidxn = F(SANS_B, 12)
    colw = 322
    per_col = (len(INDEX) + 1) // 2
    for k, (n, reg, head, tg) in enumerate(INDEX):
        col = k // per_col
        row = k % per_col
        x = ix + col * (colw + 8)
        ly = map_y + 4 + row * 25
        if row:
            d.line([x, ly - 6, x + colw, ly - 6], fill=LIGHT, width=1)
        d.text((x, ly), str(n), font=fidxn, fill=RED)
        d.text((x + 22, ly), reg, font=fidxb, fill=NAVY)
        rw = d.textlength(reg, font=fidxb)
        hx0 = x + 24 + rw
        avail = x + colw - hx0 - 16
        hd = head
        if d.textlength(" \u2014 " + hd, font=fidx) > avail:
            raise ValueError("index line too long: %r" % head)
        d.text((hx0, ly), " \u2014 " + hd, font=fidx, fill=INK)
        tw3 = d.textlength(" \u2014 " + hd, font=fidx)
        d.text((hx0 + tw3 + 4, ly), tg, font=fidxb, fill=GREY)
    y = map_y + map_h + 6

    # ---- DATE CHECK: exclusion list
    d.rectangle([16, y, W - 16, y + 80], outline=RED, width=2)
    d.text((26, y + 6), "DATE CHECK \u2014 WHAT WE LEFT OUT", font=F(SANS_B, 12),
           fill=RED)
    d.text((26 + d.textlength("DATE CHECK \u2014 WHAT WE LEFT OUT", font=F(SANS_B, 12)) + 10,
            y + 7), "Big stories from other days. They are NOT in today\u2019s %d." % N_STORIES,
           font=F(SANS, 11), fill=GREY)
    fdc = F(SANS, 11)
    for k, item in enumerate(LEFT_OUT):
        col = k // 4
        row = k % 4
        x = 26 + col * 330
        ly = y + 24 + row * 13
        d.text((x, ly), "\u2715", font=fdc, fill=RED)
        d.text((x + 14, ly), item, font=fdc, fill=INK)
    y += 84

    # ---- footer: legend + sources
    fleg = F(SANS, 10)
    d.text((16, y), "HOW WE CHECKED  \u2022  CONFIRMED = 2+ outlets  \u2022  OFFICIAL = on the "
           "record  \u2022  REPORTED = one outlet  \u2022  CLAIM = one side\u2019s account  "
           "\u2022  times in UTC", font=fleg, fill=GREY)
    y += 13
    d.text((16, y), "Sources: Reuters \u2022 AP \u2022 CENTCOM \u2022 NZ Electoral Commission "
           "\u2022 Supreme Court of Canada \u2022 Bundestag \u2022 Adobe \u2022 FAO/WFP  |  "
           "Scenes are drawn illustrations, not photos. Map: supplied colour map.",
           font=fleg, fill=GREY)
    y += 13
    d.text((16, y), "THE WORLD IN ONE DAY  \u2022  Friday 27 November 2026  \u2022  %d stories" % N_STORIES,
           font=F(SANS_B, 10), fill=NAVY)
    d.text((W - 16 - d.textlength("27 NOV 2026", font=F(SANS_B, 10)), y),
           "27 NOV 2026", font=F(SANS_B, 10), fill=NAVY)
    return img

def main():
    img = build()
    os.makedirs("/output", exist_ok=True)
    img.save(OUT, format="PNG")
    print("wrote", OUT, img.size)

if __name__ == "__main__":
    main()
