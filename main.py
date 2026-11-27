#!/usr/bin/env python3
"""Friday 27 November 2026 — The World in One Day.

A deterministic program that draws one 1024x1024 front page summing up
27 November 2026 world news. No network, no randomness, no clock: the same
bytes come out on every run. Run: python3 main.py -> writes /output/entry.png

All pictures and the map are drawn in code (PIL) from fixed coordinates.
All 36 stories are dated Friday 27 November 2026 (first reported that day in
some timezone, or a same-day development). See the DATE CHECK box on the page
for the big older stories deliberately left out.
"""
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
# tag letters for the index: C CONFIRMED, R REPORTED, O OFFICIAL, L CLAIM
HEROES = [
    dict(n=1, place="KUWAIT  \u2022  MIDDLE EAST", scene="kuwait",
         head="Drone strike kills two Italians in Kuwait",
         deck="Iran denies any role as Rome and Kuwait blame Tehran. Two "
              "technicians died at an air-defence site.",
         tag="CLAIM"),
    dict(n=2, place="USA  \u2022  BLACK FRIDAY", scene="blackfriday",
         head="Black Friday opens: $12.9bn day ahead",
         deck="Adobe forecasts a record $12.9bn in US online sales; 126m "
              "Americans to shop. Half of deals no cheaper.",
         tag="FORECAST"),
    dict(n=3, place="GAZA  \u2022  WAR", scene="gaza",
         head="Hamas weighs reply after 10 die in Gaza",
         deck="Israel kills 10 in a third night of strikes, including Hamas "
              "deputy minister Khaled Abu Nada and his wife.",
         tag="CONFIRMED"),
]

CARDS = [
    dict(n=4, place="NEW YORK  \u2022  WEATHER", scene="storm",
         head="Storm leaves 800,000 in the dark",
         sub="1,000+ flights hit on the East Coast",
         tag="CONFIRMED"),
    dict(n=5, place="LONDON  \u2022  MIGRATION", scene="ukchart",
         head="UK net migration lowest since 1997",
         sub="ONS: 77,000, down from 204,000",
         tag="OFFICIAL"),
    dict(n=6, place="IBIZA  \u2022  DISASTER", scene="ibiza",
         head="Diesel tanker capsizes, 1 dead",
         sub="17 rescued; up to 7,000 tonnes aboard",
         tag="CONFIRMED"),
    dict(n=7, place="PARIS  \u2022  LAW", scene="depardieu",
         head="Depardieu to stand trial for rape",
         sub="Trial ordered over alleged 2018 rape",
         tag="CONFIRMED"),
    dict(n=8, place="GENEVA  \u2022  CHESS", scene="chess",
         head="Gukesh\u2013Sindarov Game 3 ends drawn",
         sub="Marathon third game level at 1\u00bd\u20131\u00bd",
         tag="CONFIRMED"),
    dict(n=9, place="WASHINGTON  \u2022  POLITICS", scene="trumpgdp",
         head="Trump seeks probe of \u2018fake\u2019 GDP",
         sub="Growth revised up to 4.3%",
         tag="CLAIM"),
    dict(n=10, place="WELLINGTON  \u2022  POLITICS", scene="nzvote",
         head="NZ final count lands today",
         sub="Coalition holds 67 of 131 seats",
         tag="OFFICIAL"),
    dict(n=11, place="BANGKOK  \u2022  DISASTER", scene="bangkok",
         head="Nine hurt in Bangkok refinery blast",
         sub="Three critical; production shut",
         tag="CONFIRMED"),
    dict(n=12, place="NEW DELHI  \u2022  ECONOMY", scene="indiacabinet",
         head="Cabinet clears Rs 11,000-crore scheme",
         sub="Construction equipment boost",
         tag="REPORTED"),
    dict(n=13, place="KATHMANDU  \u2022  DISASTER", scene="nepal",
         head="4,000 landslide missing declared dead",
         sub="Nepal begins toll of the missing",
         tag="REPORTED"),
]

INDEX = [
    (14, "GLOBAL", "Amazon workers strike in 20 countries", "R"),
    (15, "S ASIA", "Karachi collapse kills 3, injures 14", "C"),
    (16, "AFRICA", "Congo Ebola passes 12,000 cases", "C"),
    (17, "AFRICA", "Mali: 300+ Russians killed for junta", "R"),
    (18, "E ASIA", "Myanmar rejects part of ICJ ruling", "R"),
    (19, "E ASIA", "Kim vows permanent nuclear armament", "R"),
    (20, "EUROPE", "Zelenskiy: US too focused on Mideast", "C"),
    (21, "N AMERICA", "Trump attacks foes in holiday message", "R"),
    (22, "MIDDLE EAST", "Saudi intercepts two Houthi missiles", "R"),
    (23, "EUROPE", "Russia hits two grain ships near Odesa", "R"),
    (24, "E ASIA", "N. Korea halts missile sales to Russia", "L"),
    (25, "EUROPE", "Kushner: Putin vows no nuclear use", "L"),
    (26, "MIDDLE EAST", "Israeli judges: drop PM charges", "R"),
    (27, "EUROPE", "France seizes suspected drug vessel", "R"),
    (28, "S ASIA", "India court: PMLA bench needs judge", "R"),
    (29, "S ASIA", "India U-19 women beat England by 36", "C"),
    (30, "S ASIA", "India v NZ 2nd Test begins today", "C"),
    (31, "OCEANIA", "Sinner out of Australian Open, knee", "R"),
    (32, "N AMERICA", "Musk: yearly SpaceX share for US kids", "R"),
    (33, "S ASIA", "Pakistan's 10th polio case of 2026", "R"),
    (34, "OCEANIA", "Australia braces for bushfire season", "R"),
    (35, "OCEANIA", "Sydney battles fire ant outbreak", "R"),
    (36, "AFRICA", "Kenya joins Africa CDC board", "R"),
]

NUMBERS = [
    ("2", "KILLED IN KUWAIT"),
    ("$12.9B", "BLACK FRIDAY SALES *"),
    ("800,000+", "WITHOUT POWER IN US"),
    ("77,000", "UK NET MIGRATION"),
    ("7,000t", "DIESEL ON TANKER"),
    ("400,000", "NZ SPECIAL VOTES"),
]

REGIONS = [
    ("N AMERICA", 5, (29, 47, 77)), ("EUROPE", 8, (90, 60, 110)),
    ("AFRICA", 3, (60, 110, 60)), ("MIDDLE EAST", 4, (150, 100, 10)),
    ("S ASIA", 7, (200, 90, 40)), ("E ASIA", 4, (40, 130, 130)),
    ("OCEANIA", 4, (40, 110, 140)), ("GLOBAL", 1, (90, 86, 78)),
]

LEFT_OUT = [
    "Macy\u2019s 100th parade postponed \u2014 announced Wed 25 Nov",
    "Musk: two SpaceX shares for every US child \u2014 Wed 25 Nov",
    "US tariffs on 14 trading partners proposed \u2014 Wed 26 Nov",
    "Houthi claim of attack on Saudi Ras Tanura refinery \u2014 Wed 25 Nov",
    "Murmansk governor detained \u2014 first reported Wed 25 Nov",
    "26/11 Mumbai attacks anniversary tributes \u2014 Thu 26 Nov",
    "FCC clears 1m SpaceX satellites \u2014 Wed 25 Nov",
    "De Cos set to be next ECB chief \u2014 Wed 26 Nov",
]

UTC_STRIP = ("THE DAY IN UTC  \u2022  01:00 NZ final count lands  \u2022  05:00 Black "
             "Friday opens in the US  \u2022  07:00 UK migration figures out  \u2022  "
             "11:00 Hamas weighs its reply  \u2022  14:00 Bangkok toll at nine  "
             "\u2022  18:00 Chess Game 3 ends drawn  \u2022  21:00 Amazon walkouts "
             "begin  \u2022  23:00 This front page goes to press")

# ---------------------------------------------------------------- scenes
# Each painter draws one pictorial scene inside (x, y, w, h). All coordinates
# are fixed; nothing random, nothing from the clock.

def scene_kuwait(d, x, y, w, h):
    grad(d, (x, y, x + w, y + h), (16, 22, 46), (64, 52, 40))
    d.ellipse([x + w - 52, y + 10, x + w - 22, y + 40], fill=(235, 225, 200))
    # desert ground + radar station
    d.polygon([(x, y + h), (x, y + h - 26), (x + w * 0.3, y + h - 34),
               (x + w * 0.6, y + h - 22), (x + w, y + h - 30), (x + w, y + h)],
              fill=(58, 44, 34))
    d.rectangle([x + w * 0.42, y + h - 62, x + w * 0.58, y + h - 34], fill=(30, 30, 34))
    d.pieslice([x + w * 0.42, y + h - 78, x + w * 0.58, y + h - 46],
               180, 360, fill=(210, 210, 205))
    d.line([x + w * 0.5, y + h - 62, x + w * 0.5, y + h - 40], fill=(210, 210, 205), width=3)
    # drone with red lights + burst
    cx, cy = x + w * 0.5, y + 34
    d.ellipse([cx - 26, cy - 6, cx - 14, cy + 6], fill=(20, 20, 22))
    d.ellipse([cx + 14, cy - 6, cx + 26, cy + 6], fill=(20, 20, 22))
    d.rectangle([cx - 16, cy - 3, cx + 16, cy + 3], fill=(20, 20, 22))
    d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(220, 40, 40))
    d.line([cx - 26, cy - 12, cx - 34, cy - 16], fill=(180, 180, 180), width=2)
    d.line([cx + 26, cy - 12, cx + 34, cy - 16], fill=(180, 180, 180), width=2)
    ex, ey = cx, cy + 26
    d.polygon([(ex - 12, ey + 6), (ex - 4, ey - 6), (ex, ey + 2), (ex + 5, ey - 8),
               (ex + 8, ey + 2), (ex + 13, ey + 8), (ex + 2, ey + 10),
               (ex - 4, ey + 12)], fill=(255, 170, 40))
    d.polygon([(ex - 5, ey + 4), (ex - 1, ey - 1), (ex + 3, ey + 3), (ex + 5, ey + 7),
               (ex - 1, ey + 8)], fill=(255, 220, 90))

def scene_blackfriday(d, x, y, w, h):
    grad(d, (x, y, x + w, y + h), (120, 40, 46), (70, 22, 30))
    # shopfront: awning stripes + windows + bags
    d.rectangle([x, y, x + w, y + 26], fill=(246, 241, 229))
    for i in range(8):
        if i % 2 == 0:
            d.rectangle([x + i * (w // 8), y, x + (i + 1) * (w // 8), y + 26],
                        fill=(29, 47, 77))
    d.rectangle([x + 8, y + 34, x + w - 8, y + h - 26], fill=(40, 26, 30))
    for i in range(3):
        wx = x + 16 + i * (w // 3)
        d.rectangle([wx, y + 42, wx + w // 3 - 20, y + h - 34], fill=(255, 214, 110))
        d.rectangle([wx + 6, y + 48, wx + w // 3 - 26, y + h - 40], fill=(40, 90, 110))
    d.text((x + 10, y + h - 24), "SALE", font=F(SANS_B, 15), fill=(255, 255, 255))
    # shopping bags on the pavement
    for bx, bc in [(x + w - 78, (30, 90, 140)), (x + w - 48, (185, 138, 30))]:
        d.polygon([(bx, y + h - 16), (bx + 22, y + h - 16), (bx + 19, y + h - 2),
                   (bx + 3, y + h - 2)], fill=bc)
        d.arc([bx + 6, y + h - 24, bx + 16, y + h - 12], 180, 360, fill=(255, 255, 255), width=2)

def scene_gaza(d, x, y, w, h):
    grad(d, (x, y, x + w, y + h), (52, 44, 66), (190, 110, 60))
    sun(d, x + w - 30, y + 26, 14, (255, 190, 90))
    # skyline + minaret + smoke columns
    d.rectangle([x, y + h - 52, x + w, y + h], fill=(38, 32, 40))
    for bx, bw, bh in [(0, 0.16, 34), (0.18, 0.12, 46), (0.32, 0.2, 28),
                       (0.55, 0.14, 40), (0.72, 0.16, 30), (0.88, 0.12, 44)]:
        d.rectangle([x + w * bx, y + h - bh, x + w * (bx + bw), y + h - 10],
                    fill=(24, 20, 26))
    d.rectangle([x + w * 0.46, y + h - 78, x + w * 0.46 + 7, y + h - 10], fill=(24, 20, 26))
    d.polygon([(x + w * 0.46 - 2, y + h - 78), (x + w * 0.46 + 9, y + h - 78),
               (x + w * 0.46 + 3, y + h - 92)], fill=(24, 20, 26))
    for sx in (0.22, 0.62):
        for i in range(3):
            d.ellipse([x + w * sx + i * 3, y + 18 + i * 12, x + w * sx + 16 + i * 3,
                       y + 34 + i * 12], fill=(120, 110, 105))

def scene_storm(d, x, y, w, h):
    grad(d, (x, y, x + w, y + h), (38, 48, 66), (90, 100, 118))
    cloud(d, x + 6, y + 2, 9, (52, 60, 74))
    cloud(d, x + w - 46, y + 0, 8, (52, 60, 74))
    cloud(d, x + w // 2 - 16, y + 6, 10, (44, 52, 66))
    lx = x + w // 2
    top, bot = y + int(h * 0.30), y + h - 4
    d.polygon([(lx, top), (lx - 6, top + (bot - top) // 2), (lx - 1, top + (bot - top) // 2),
               (lx - 8, bot), (lx + 3, top + (bot - top) // 2 + 4),
               (lx + 8, top + (bot - top) // 2 + 4), (lx + 2, top)],
              fill=(255, 220, 60))
    for i in range(12):
        rx = x + 6 + (i * 23) % (w - 12)
        ry = y + int(h * 0.30) + (i * 7) % max(6, int(h * 0.55))
        d.line([rx, ry, rx - 4, ry + 8], fill=(200, 215, 230), width=2)
    d.line([x + 8, y + h - 4, x + 26, y + h - 20], fill=(30, 28, 24), width=3)
    d.line([x, y + int(h * 0.22), x + w, y + int(h * 0.16)], fill=(20, 20, 22), width=2)


def scene_ukchart(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(246, 241, 229))
    d.line([x + 8, y + 6, x + 8, y + h - 10], fill=(25, 23, 19), width=2)
    d.line([x + 8, y + h - 10, x + w - 6, y + h - 10], fill=(25, 23, 19), width=2)
    fr = [(0.10, 0.16), (0.22, 0.22), (0.34, 0.30), (0.46, 0.36), (0.58, 0.48),
          (0.70, 0.54), (0.80, 0.62), (0.90, 0.72), (0.97, 0.82)]
    pts = [(x + int(fx * w), y + int(fy * h)) for fx, fy in fr]
    d.line(pts, fill=(163, 33, 38), width=3, joint="curve")
    d.ellipse([pts[-1][0] - 4, pts[-1][1] - 4, pts[-1][0] + 4, pts[-1][1] + 4],
              fill=(163, 33, 38))
    d.text((x + 12, y + h - 22), "204,000", font=F(SANS_B, 10), fill=(90, 86, 78))
    d.text((x + w - 58, y + h - 22), "77,000", font=F(SANS_B, 11), fill=(163, 33, 38))
    d.rectangle([x + w - 38, y + 5, x + w - 6, y + 19], fill=(29, 47, 77))
    d.line([x + w - 38, y + 5, x + w - 6, y + 19], fill=(255, 255, 255), width=2)
    d.line([x + w - 6, y + 5, x + w - 38, y + 19], fill=(255, 255, 255), width=2)


def scene_ibiza(d, x, y, w, h):
    grad(d, (x, y, x + w, y + h), (140, 190, 215), (40, 90, 130))
    sun(d, x + w - 22, y + 12, 9, (255, 220, 120))
    # listing tanker, relative to the box
    d.polygon([(x + int(w * 0.07), y + int(h * 0.52)),
               (x + int(w * 0.88), y + int(h * 0.30)),
               (x + int(w * 0.96), y + int(h * 0.44)),
               (x + int(w * 0.96), y + int(h * 0.62)),
               (x + int(w * 0.07), y + int(h * 0.68))], fill=(120, 30, 30))
    d.rectangle([x + int(w * 0.16), y + int(h * 0.30), x + int(w * 0.32), y + int(h * 0.46)],
                fill=(240, 240, 235))
    d.rectangle([x + int(w * 0.36), y + int(h * 0.26), x + int(w * 0.52), y + int(h * 0.42)],
                fill=(220, 180, 60))
    for i in range(3):
        yy = y + int(h * 0.74) + i * 5
        d.line([x + 4, yy, x + w - 4, yy], fill=(200, 225, 235), width=2)
    d.ellipse([x + w - 44, y + h - 13, x + w - 18, y + h - 4], fill=(255, 120, 30))


def scene_depardieu(d, x, y, w, h):
    grad(d, (x, y, x + w, y + h), (210, 205, 190), (150, 140, 125))
    ph = int(h * 0.30)
    d.polygon([(x + 6, y + ph), (x + w // 2, y + 4), (x + w - 6, y + ph)],
              fill=(120, 110, 95))
    d.rectangle([x + 6, y + ph, x + w - 6, y + ph + 5], fill=(90, 82, 70))
    for i in range(4):
        cx = x + 20 + i * (w - 40) // 3
        d.rectangle([cx - 5, y + ph + 5, cx + 5, y + h - 8], fill=(235, 230, 215))
    d.rectangle([x + 6, y + h - 8, x + w - 6, y + h - 3], fill=(90, 82, 70))
    cx, cy = x + w // 2, y + int(h * 0.52)
    d.line([cx, cy - 6, cx, cy + 8], fill=(60, 50, 40), width=2)
    d.line([cx - 11, cy - 6, cx + 11, cy - 6], fill=(60, 50, 40), width=2)
    d.polygon([(cx - 16, cy + 4), (cx - 6, cy + 4), (cx - 11, cy + 9)], fill=(200, 170, 60))
    d.polygon([(cx + 6, cy + 4), (cx + 16, cy + 4), (cx + 11, cy + 9)], fill=(200, 170, 60))


def scene_chess(d, x, y, w, h):
    # board, 8x8, seen slightly from above
    s = min(w, h)
    ox, oy = x + (w - s) // 2, y + (h - s) // 2
    cw = s // 8
    for r in range(8):
        for c in range(8):
            col = (240, 232, 214) if (r + c) % 2 == 0 else (40, 34, 30)
            d.rectangle([ox + c * cw, oy + r * cw, ox + (c + 1) * cw, oy + (r + 1) * cw],
                        fill=col)
    # two kings facing off
    for kx, col in [(ox + 2 * cw, (255, 255, 255)), (ox + 5 * cw, (25, 20, 18))]:
        ky = oy + 3 * cw
        d.ellipse([kx + 3, ky + 2, kx + cw - 3, ky + cw - 2], fill=col,
                  outline=(120, 110, 95))
        d.rectangle([kx + cw // 2 - 2, ky - 6, kx + cw // 2 + 2, ky + 2], fill=col)
        d.line([kx + cw // 2 - 6, ky - 3, kx + cw // 2 + 6, ky - 3], fill=col, width=2)
    # clock
    d.rounded_rectangle([x + w - 34, y + 4, x + w - 4, y + 22], radius=3,
                        fill=(25, 23, 19))
    d.text((x + w - 30, y + 8), "1:30", font=F(SANS_B, 10), fill=(255, 255, 255))

def scene_trumpgdp(d, x, y, w, h):
    grad(d, (x, y, x + w, y + h), (150, 175, 205), (220, 215, 200))
    # white house silhouette + rising bars
    d.rectangle([x + 8, y + h - 40, x + w - 8, y + h - 8], fill=(245, 244, 238))
    d.polygon([(x + w // 2 - 34, y + h - 40), (x + w // 2, y + h - 62),
               (x + w // 2 + 34, y + h - 40)], fill=(245, 244, 238))
    for i in range(5):
        d.rectangle([x + 18 + i * 14, y + h - 32, x + 26 + i * 14, y + h - 12],
                    fill=(29, 47, 77))
    bars = [(0.55, 0.45, 0.62, 0.78, 0.95)]
    bw = (w - 20) // 5
    for i, bh in enumerate([0.30, 0.42, 0.38, 0.55, 0.72]):
        bx = x + 10 + i * bw
        d.rectangle([bx, y + h - 14 - int(h * bh * 0.5), bx + bw - 6, y + h - 14],
                    fill=(163, 33, 38) if i == 4 else (90, 110, 140))
    d.text((x + w - 56, y + 6), "+4.3%", font=F(SANS_B, 14), fill=(163, 33, 38))

def scene_nzvote(d, x, y, w, h):
    grad(d, (x, y, x + w, y + h), (70, 110, 140), (200, 215, 205))
    # ballot box + tick + fern-ish leaves
    d.rectangle([x + w // 2 - 34, y + h - 46, x + w // 2 + 34, y + h - 10],
                fill=(29, 47, 77))
    d.rectangle([x + w // 2 - 40, y + h - 54, x + w // 2 + 40, y + h - 46],
                fill=(20, 34, 58))
    d.rectangle([x + w // 2 - 12, y + h - 52, x + w // 2 + 12, y + h - 49],
                fill=(246, 241, 229))
    d.text((x + w // 2 - 20, y + h - 42), "VOTE", font=F(SANS_B, 13),
           fill=(255, 255, 255))
    # ballot paper going in, with a tick
    d.polygon([(x + w // 2 - 16, y + 12), (x + w // 2 + 16, y + 8),
               (x + w // 2 + 12, y + 34), (x + w // 2 - 12, y + 36)],
              fill=(255, 255, 255))
    d.line([x + w // 2 - 8, y + 24, x + w // 2 - 1, y + 31, x + w // 2 + 10, y + 16],
           fill=(31, 110, 46), width=3)
    for lx in (x + 10, x + w - 18):
        d.line([lx, y + h - 6, lx + 6, y + h - 30], fill=(31, 110, 46), width=3)
        d.line([lx + 6, y + h - 30, lx + 12, y + h - 12], fill=(31, 110, 46), width=3)

def scene_bangkok(d, x, y, w, h):
    grad(d, (x, y, x + w, y + h), (60, 55, 70), (150, 120, 90))
    for tx, tw, th in [(0.06, 0.15, 0.55), (0.24, 0.18, 0.68), (0.46, 0.15, 0.60),
                       (0.64, 0.16, 0.46), (0.82, 0.13, 0.62)]:
        d.rectangle([x + int(w * tx), y + h - int(h * th), x + int(w * (tx + tw)),
                     y + h - 4], fill=(52, 48, 52))
        d.rectangle([x + int(w * tx) + 2, y + h - int(h * th) - 6,
                     x + int(w * (tx + tw)) - 2, y + h - int(h * th)], fill=(52, 48, 52))
    fx, fy = x + int(w * 0.33), y + int(h * 0.30)
    fh = int(h * 0.34)
    d.polygon([(fx - 9, fy + fh), (fx - 3, fy), (fx + 1, fy + fh // 2),
               (fx + 7, fy - fh // 4), (fx + 10, fy + fh)], fill=(255, 140, 30))
    d.polygon([(fx - 4, fy + fh), (fx - 1, fy + fh // 2), (fx + 3, fy + fh // 2 + 4),
               (fx + 5, fy + fh)], fill=(255, 210, 60))
    for sx in (0.55, 0.78):
        for i in range(2):
            d.ellipse([x + int(w * sx) + i * 2, y + 4 + i * 7,
                       x + int(w * sx) + 12 + i * 2, y + 15 + i * 7],
                      fill=(70, 62, 58))


def scene_indiacabinet(d, x, y, w, h):
    grad(d, (x, y, x + w, y + h), (190, 150, 90), (120, 80, 50))
    sun(d, x + w - 22, y + 12, 9, (255, 215, 130))
    d.rectangle([x + 8, y + int(h * 0.66), x + w - 8, y + h - 4], fill=(235, 228, 210))
    d.pieslice([x + w // 2 - 20, y + int(h * 0.30), x + w // 2 + 20, y + int(h * 0.72)],
               180, 360, fill=(200, 150, 60))
    d.rectangle([x + w // 2 - 2, y + int(h * 0.18), x + w // 2 + 2, y + int(h * 0.32)],
                fill=(200, 150, 60))
    for i in range(4):
        cx = x + 22 + i * (w - 44) // 3
        d.rectangle([cx - 3, y + int(h * 0.70), cx + 3, y + h - 6], fill=(150, 130, 100))
    gx, gy, gr = x + w - 24, y + h - 16, 8
    d.ellipse([gx - gr, gy - gr, gx + gr, gy + gr], fill=(90, 86, 78))
    d.ellipse([gx - 3, gy - 3, gx + 3, gy + 3], fill=(246, 241, 229))


def scene_nepal(d, x, y, w, h):
    grad(d, (x, y, x + w, y + h), (120, 160, 200), (210, 205, 195))
    sun(d, x + 24, y + 16, 11, (255, 220, 120))
    # himalaya range + snowcaps + rescue tent
    d.polygon([(x, y + h), (x + w * 0.18, y + 22), (x + w * 0.38, y + h)],
              fill=(70, 78, 92))
    d.polygon([(x + w * 0.30, y + h), (x + w * 0.55, y + 8), (x + w * 0.80, y + h)],
              fill=(52, 58, 74))
    d.polygon([(x + w * 0.62, y + h), (x + w * 0.85, y + 26), (x + w, y + h)],
              fill=(70, 78, 92))
    d.polygon([(x + w * 0.50, y + 18), (x + w * 0.55, y + 8), (x + w * 0.60, y + 18),
               (x + w * 0.57, y + 15), (x + w * 0.53, y + 15)], fill=(255, 255, 255))
    d.polygon([(x + w * 0.13, y + 30), (x + w * 0.18, y + 22), (x + w * 0.23, y + 30)],
              fill=(255, 255, 255))
    d.polygon([(x + w - 46, y + h - 8), (x + w - 30, y + h - 30), (x + w - 14, y + h - 8)],
              fill=(163, 33, 38))
    d.line([x + w - 30, y + h - 30, x + w - 30, y + h - 44], fill=(60, 50, 40), width=2)
    d.rectangle([x + w - 36, y + h - 50, x + w - 24, y + h - 44], fill=(220, 60, 60))

def blit(img, name, x, y, w, h):
    tile = Image.new("RGB", (w, h), PAPER)
    td = ImageDraw.Draw(tile)
    SCENES[name](td, 0, 0, w, h)
    img.paste(tile, (x, y))

SCENES = {"kuwait": scene_kuwait, "blackfriday": scene_blackfriday,
          "gaza": scene_gaza, "storm": scene_storm, "ukchart": scene_ukchart,
          "ibiza": scene_ibiza, "depardieu": scene_depardieu,
          "chess": scene_chess, "trumpgdp": scene_trumpgdp,
          "nzvote": scene_nzvote, "bangkok": scene_bangkok,
          "indiacabinet": scene_indiacabinet, "nepal": scene_nepal}

# ---------------------------------------------------------------- map
NORTH_AMERICA = [(-168, 66), (-157, 58), (-152, 60), (-140, 60), (-132, 56),
                 (-125, 49), (-124, 40), (-117, 33), (-110, 24), (-105, 20),
                 (-97, 16), (-92, 15), (-86, 12), (-83, 9), (-79, 9), (-81, 13),
                 (-85, 16), (-88, 21), (-91, 19), (-97, 22), (-97, 26),
                 (-93, 30), (-88, 30), (-84, 30), (-81, 26), (-80, 32),
                 (-75, 35), (-74, 40), (-70, 42), (-67, 45), (-60, 47),
                 (-55, 50), (-60, 55), (-65, 58), (-70, 62), (-78, 62),
                 (-85, 66), (-92, 66), (-100, 68), (-115, 68), (-130, 70),
                 (-145, 70), (-158, 71), (-168, 66)]
SOUTH_AMERICA = [(-79, 9), (-76, 10), (-71, 12), (-64, 11), (-60, 8),
                 (-54, 6), (-51, 4), (-50, 0), (-44, -3), (-38, -5),
                 (-35, -8), (-37, -13), (-39, -18), (-41, -23), (-48, -27),
                 (-52, -33), (-57, -38), (-62, -41), (-65, -45), (-68, -50),
                 (-69, -54), (-72, -53), (-73, -46), (-73, -38), (-71, -30),
                 (-70, -20), (-75, -15), (-80, -6), (-81, 0), (-80, 5), (-79, 9)]
AFRICA = [(-17, 15), (-16, 21), (-14, 27), (-10, 31), (-6, 35), (0, 36),
          (9, 37), (11, 34), (19, 32), (25, 32), (30, 31), (33, 27),
          (35, 23), (37, 19), (40, 15), (43, 12), (48, 11), (51, 12),
          (46, 6), (41, 1), (40, -5), (39, -10), (36, -18), (33, -26),
          (28, -33), (20, -35), (17, -32), (15, -27), (12, -18), (9, -2),
          (9, 4), (5, 6), (-2, 5), (-8, 5), (-13, 8), (-17, 12), (-17, 15)]
EUROPE = [(-10, 37), (-9, 38), (-9, 43), (-2, 44), (-1, 47), (-4, 48),
          (-1, 50), (2, 51), (5, 53), (8, 55), (8, 57), (10, 59), (6, 60),
          (6, 62), (12, 65), (18, 69), (25, 71), (30, 70), (28, 66),
          (24, 61), (21, 55), (18, 54), (13, 54), (8, 54), (5, 53), (2, 51),
          (-1, 49), (-2, 46), (-2, 43), (-6, 38), (-9, 37), (-10, 37)]
UK = [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53), (-1, 51),
      (-4, 50), (-5, 50)]
ASIA = [(28, 70), (35, 68), (45, 68), (55, 69), (65, 69), (75, 72), (85, 73),
        (95, 75), (105, 76), (115, 73), (125, 72), (135, 71), (145, 71),
        (155, 70), (165, 69), (175, 67), (178, 65), (170, 60), (162, 56),
        (156, 51), (150, 59), (142, 55), (140, 49), (135, 43), (130, 42),
        (127, 40), (122, 38), (120, 32), (121, 28), (117, 24), (110, 20),
        (108, 18), (105, 10), (103, 7), (100, 8), (98, 12), (94, 17),
        (92, 21), (89, 22), (86, 20), (80, 15), (77, 8), (75, 12), (72, 20),
        (68, 23), (66, 25), (62, 25), (58, 26), (56, 27), (52, 26), (50, 29),
        (48, 30), (44, 29), (41, 28), (39, 21), (39, 15), (42, 12), (48, 11),
        (51, 12), (55, 17), (58, 20), (60, 23), (58, 25), (55, 26), (52, 27),
        (50, 29), (48, 31), (44, 31), (40, 32), (36, 36), (33, 36), (30, 36),
        (28, 40), (28, 45), (28, 55), (28, 62), (28, 70)]
AUSTRALIA = [(113, -22), (114, -30), (115, -35), (120, -34), (124, -33),
             (129, -32), (132, -32), (135, -35), (138, -35), (140, -38),
             (145, -38), (150, -37), (153, -32), (153, -27), (150, -23),
             (146, -19), (142, -15), (142, -11), (136, -12), (132, -12),
             (130, -13), (126, -14), (122, -17), (118, -20), (113, -22)]
CONTINENTS = [NORTH_AMERICA, SOUTH_AMERICA, AFRICA, EUROPE, UK, ASIA, AUSTRALIA]

# story number -> (lon, lat) of the real place
PINS = {1: (47.9, 29.3), 2: (-74.0, 40.7), 3: (34.5, 31.5), 4: (-71.0, 42.3),
        5: (-0.1, 51.5), 6: (1.4, 39.0), 7: (2.35, 48.85), 8: (6.1, 46.2),
        9: (-77.0, 38.9), 10: (174.8, -41.3), 11: (100.5, 13.75),
        12: (77.2, 28.6), 13: (85.3, 27.7)}
# nudge the number badge away from its true dot where pins crowd
PIN_OFF = {1: (-9, -5), 2: (-7, -9), 3: (9, 7), 4: (8, 8), 5: (-9, -3),
           6: (-4, 9), 7: (-2, -10), 8: (11, 5), 9: (7, -8), 10: (-10, -4),
           11: (-9, 6), 12: (-9, 3), 13: (9, -7)}

def draw_map(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=SEA)
    def proj(lon, lat):
        px = x + (lon + 180) / 360.0 * w
        py = y + (75 - lat) / 130.0 * h
        return (px, py)
    for poly in CONTINENTS:
        d.polygon([proj(lon, lat) for lon, lat in poly], fill=LAND,
                  outline=(170, 158, 128))
    fnum = F(SANS_B, 10)
    for n, (lon, lat) in PINS.items():
        px, py = proj(lon, lat)
        ox, oy = PIN_OFF.get(n, (0, 0))
        bx, by = px + ox, py + oy
        d.line([px, py, bx, by], fill=RED, width=1)
        d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=RED)
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
    mid = "36 STORIES  \u2022  7 REGIONS + GLOBAL  \u2022  EVERY ONE DATED 27 NOV 2026"
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
    deck = ("A drone strike kills two Italians in Kuwait, Black Friday opens, "
            "and Hamas weighs its reply after 10 die in Gaza.")
    tw = d.textlength(deck, font=fdeck)
    d.text(((W - tw) / 2, y), deck, font=fdeck, fill=(60, 56, 48))
    y += 22
    d.line([16, y, W - 16, y], fill=RED, width=2)
    y += 6

    # ---- DAY IN UTC strip
    futcb = F(SANS_B, 11)
    label = "THE DAY IN UTC  \u2022  "
    lw = d.textlength(label, font=futcb)
    rest = ("01:00 NZ count  \u2022  05:00 Black Friday opens  \u2022  07:00 UK "
            "migration  \u2022  11:00 Hamas reply  \u2022  14:00 Bangkok toll  "
            "\u2022  18:00 Chess drawn  \u2022  21:00 Amazon walkouts")
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
    for name, cnt, col in REGIONS:
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
        for ln in wrap(hro["deck"], fdeck2, col_w, d)[:3]:
            d.text((hx, hy), ln, font=fdeck2, fill=(60, 56, 48))
            hy += 15
    y = hero_y + scene_h + 6 + 17 + 48 + 2 + 45 + 4
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
    d.text((ix, y), "ALSO ON FRIDAY 27 NOVEMBER \u2014 23 MORE STORIES",
           font=fsec, fill=INK)
    y += 19
    map_y = y
    map_h = 182
    draw_map(d, 16, map_y, 330, map_h)
    d.rectangle([16, map_y, 346, map_y + map_h], outline=RULE, width=1)
    # index, two columns
    fidx = F(SANS, 11)
    fidxb = F(SANS_B, 11)
    fidxn = F(SANS_B, 11)
    colw = 322
    for k, (n, reg, head, tg) in enumerate(INDEX):
        col = k // 12
        row = k % 12
        x = ix + col * (colw + 8)
        ly = map_y + 2 + row * 15
        d.text((x, ly), str(n), font=fidxn, fill=RED)
        d.text((x + 22, ly), reg, font=fidxb, fill=NAVY)
        rw = d.textlength(reg, font=fidxb)
        hx0 = x + 24 + rw
        avail = x + colw - hx0 - 16
        hd = head
        while hd and d.textlength(" \u2014 " + hd, font=fidx) > avail:
            hd = hd.rsplit(" ", 1)[0] if " " in hd else ""
        d.text((hx0, ly), " \u2014 " + hd, font=fidx, fill=INK)
        tw3 = d.textlength(" \u2014 " + hd, font=fidx)
        d.text((hx0 + tw3 + 4, ly), tg, font=fidxb, fill=GREY)
    y = map_y + map_h + 8

    # ---- DATE CHECK: exclusion list
    d.rectangle([16, y, W - 16, y + 86], outline=RED, width=2)
    d.text((26, y + 6), "DATE CHECK \u2014 WHAT WE LEFT OUT", font=F(SANS_B, 12),
           fill=RED)
    d.text((26 + d.textlength("DATE CHECK \u2014 WHAT WE LEFT OUT", font=F(SANS_B, 12)) + 10,
            y + 7), "Big stories from other days. They are NOT in today\u2019s 36.",
           font=F(SANS, 11), fill=GREY)
    fdc = F(SANS, 11)
    for k, item in enumerate(LEFT_OUT):
        col = k // 4
        row = k % 4
        x = 26 + col * 490
        ly = y + 26 + row * 14
        d.text((x, ly), "\u2715", font=fdc, fill=RED)
        d.text((x + 14, ly), item, font=fdc, fill=INK)
    y += 94

    # ---- footer: legend + sources
    fleg = F(SANS, 10)
    d.text((16, y), "HOW WE CHECKED  \u2022  CONFIRMED = 2+ outlets  \u2022  OFFICIAL = on the "
           "record  \u2022  REPORTED = one outlet  \u2022  CLAIM = one side\u2019s account  "
           "\u2022  FORECAST = scheduled for today", font=fleg, fill=GREY)
    y += 14
    d.text((16, y), "Sources: Reuters \u2022 AP \u2022 BBC \u2022 ONS \u2022 NZ Electoral "
           "Commission \u2022 Adobe \u2022 Consumer NZ  |  * $12.9bn is Adobe\u2019s "
           "forecast. Pictures and map: original, drawn in code.",
           font=fleg, fill=GREY)
    y += 14
    d.text((16, y), "THE WORLD IN ONE DAY  \u2022  Friday 27 November 2026  \u2022  36 stories",
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
