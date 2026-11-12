"""«Ü в Німеччині»: cartoon series. Mascot Ü (the two dots are its eyes) makes one phrase faux-pas at Oma's table.
Structure (cfg): say -> Oma freezes -> 3-s guess -> what it really means -> correct phrase -> Oma's punchline -> follow card.
CFG=examples/ue01.json python3 ue_cartoon.py out.mp4 | preview <dir> t.. | audio out.wav
"""
import json, math, os, sys
from pathlib import Path
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kino as K, follow_card as FC, clean_audio as CA
from kino import seg, ease, back, out3, clamp, INK, YEL, WHITE

CFG = json.load(open(os.environ["CFG"], encoding="utf-8"))
T_SAY, T_FREEZE, T_THINK, T_WRONG, T_RIGHT, T_PUNCH, T_END = 0.15, 1.1, 2.3, 5.3, 8.6, 11.4, 13.6
DUR = 17.6
WALL, WALL2, TABLE, TABLE2 = (250, 236, 212), (243, 224, 196), (186, 120, 72), (150, 92, 52)
ORANGE, LAV, RED, GREEN, PINK, SKY = (255, 178, 64), (176, 158, 226), (214, 48, 49), (34, 160, 90), (255, 140, 150), (120, 190, 240)
CARDS = FC.make(CFG); TAG = FC.series_tag(CFG["series"])

# ---------------- characters ----------------
def ue(c, cx, cy, s, mood="happy", look=(0, 0), blush=0., sweat=0., arm=0.):
    P = lambda x, y: (cx + x * s, cy + y * s)
    path = [P(-40, -60), P(-40, 10)] + [P(-40 * math.cos(a), 10 + 40 * math.sin(a)) for a in [i * math.pi / 16 for i in range(17)]] + [P(40, 10), P(40, -60)]
    for (x, y), (x2, y2) in [((-40, 0), (-92, -18 - 30 * arm)), ((40, 0), (88, 8))]:               # arms (left one pushes the plate)
        c.line([P(x, y), P(x2, y2)], INK, 15 * s); c.circ(*P(x2, y2), 9 * s, INK)
    pts = []
    for (x0, y0), (x1, y1) in zip(path, path[1:]):
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) / 3))
        pts += [(x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n) for k in range(n)]
    pts.append(path[-1])
    for r, col in ((34 * s, INK), (26 * s, YEL)):
        for x, y in pts: c.circ(x, y, r, col)
    if blush:
        for x in (-40, 40): c.ell((*P(x - 20, 18), *P(x + 20, 32)), K.mix(YEL, (240, 90, 90), blush))
    # eyes = the umlaut dots
    big = 1.25 if mood == "shock" else 1.0
    for x in (-40, 40):
        ex, ey = P(x, -112); r = 23 * s * big
        c.circ(ex, ey, r + 5 * s, INK); c.circ(ex, ey, r, WHITE)
        c.circ(ex + look[0] * 8 * s, ey + look[1] * 8 * s, 10 * s * (0.8 if mood == "shock" else 1), INK)
        c.circ(ex + look[0] * 8 * s - 3 * s, ey + look[1] * 8 * s - 4 * s, 3 * s, WHITE)
    mx, my = P(0, 50)
    if mood == "happy": c.chord((mx - 20 * s, my - 16 * s, mx + 20 * s, my + 16 * s), 0, 180, INK)
    elif mood == "shock": c.ell((mx - 9 * s, my - 11 * s, mx + 9 * s, my + 11 * s), INK)
    elif mood == "oops": c.line([(mx - 16 * s, my + 4 * s), (mx - 6 * s, my - 4 * s), (mx + 4 * s, my + 4 * s), (mx + 14 * s, my - 4 * s)], INK, 5 * s)
    else: c.line([(mx - 14 * s, my), (mx + 14 * s, my)], INK, 5 * s)
    if sweat:
        sx, sy = P(78, -138 + 30 * sweat); c.poly([(sx, sy - 22 * s), (sx - 10 * s, sy), (sx + 10 * s, sy)], SKY); c.circ(sx, sy + 2 * s, 10 * s, SKY)

def oma(c, cx, cy, s, mood="happy", shake=0.):
    cx += shake
    P = lambda x, y: (cx + x * s, cy + y * s)
    c.circ(*P(0, -128), 40 * s, INK); c.circ(*P(0, -128), 34 * s, (232, 232, 238))                   # hair bun
    c.circ(*P(0, 0), 126 * s, INK); c.circ(*P(0, 0), 118 * s, LAV)
    c.chord((*P(-104, -112), *P(104, 40)), 180, 360, (232, 232, 238))                                   # hair
    r = 26 * s * (1.25 if mood == "shock" else 1)
    for x in (-44, 44):
        c.circ(*P(x, -8), r + 6 * s, INK); c.circ(*P(x, -8), r, WHITE)
        c.circ(*P(x, -8), (7 if mood == "shock" else 9) * s, INK)
    c.line([P(-44 + 26, -12), P(44 - 26, -12)], INK, 6 * s)
    mx, my = P(0, 58)
    if mood == "shock": c.ell((mx - 14 * s, my - 18 * s, mx + 14 * s, my + 18 * s), INK)
    else: c.chord((mx - 26 * s, my - 18 * s, mx + 26 * s, my + 18 * s), 0, 180, INK)
    for x in (-74, 74): c.ell((*P(x - 18, 30), *P(x + 18, 44)), PINK)

def bubble(c, x, y, lines, size, fill=WHITE, fg=INK, tail=-1, p=1.0, w="Black"):
    if p <= 0: return
    s = .4 + .6 * back(min(1, p))
    tw = max(c.tw(l, size * s, w) for l in lines); lh = size * s * 1.22
    bw, bh = tw + 70 * s, lh * len(lines) + 46 * s
    x0, y0 = x - bw / 2, y - bh / 2
    tx = x + tail * bw * .25
    c.poly([(tx - 26 * s, y0 + bh - 4), (tx + 26 * s, y0 + bh - 4), (tx - tail * 40 * s, y0 + bh + 46 * s)], INK)
    c.rrect((x0 - 6, y0 - 6, x0 + bw + 6, y0 + bh + 6), 36 * s, INK); c.rrect((x0, y0, x0 + bw, y0 + bh), 32 * s, fill)
    c.poly([(tx - 18 * s, y0 + bh - 8), (tx + 18 * s, y0 + bh - 8), (tx - tail * 30 * s, y0 + bh + 32 * s)], fill)
    for i, l in enumerate(lines): c.text((x, y0 + 23 * s + lh * (i + .5)), l, size * s, fg, w)

def card(c, cy, lines, p, fill=WHITE, border=INK):
    """caption card under the table: lines = [(text, size, colour, weight)]"""
    if p <= 0: return
    s = .85 + .15 * back(min(1, p)); off = (1 - out3(min(1, p))) * 60
    hs = [sz * 1.25 for _, sz, _, _ in lines]; h = sum(hs) + 60
    c.rrect((70, cy - h / 2 + off, 1010, cy + h / 2 + off), 34, border); c.rrect((76, cy - h / 2 + 6 + off, 1004, cy + h / 2 - 6 + off), 30, fill)
    y = cy - h / 2 + 30 + off
    for (t, sz, col, w), hh in zip(lines, hs):
        sz = c.fit(t, sz * s, 880, w); c.text((540, y + hh / 2), t, sz, col, w); y += hh

def strike(c, x0, x1, y, p):
    if p > 0: c.line([(x0, y + 8), (x0 + (x1 - x0) * p, y - 8)], RED, 12)

# ---------------- frame ----------------
def render(t):
    c = K.Canvas(WALL, S=2)
    c.rect((0, 380, 1080, 1100), WALL2)
    for i in range(9): c.rect((i * 130 - 10, 380, i * 130 + 50, 1100), WALL)                          # wallpaper stripes
    c.rrect((640, 440, 960, 700), 16, (255, 255, 255)); c.rect((652, 452, 948, 688), (190, 225, 250)); c.rect((794, 452, 806, 688), WHITE); c.rect((652, 564, 948, 576), WHITE)
    c.circ(585, 455, 44, INK); c.circ(585, 455, 38, (250, 250, 250)); c.line([(585, 455), (585, 428)], INK, 5); c.line([(585, 455), (606, 462)], INK, 5)
    # characters
    frz = T_FREEZE <= t < T_WRONG
    um = "happy"; om = "happy"; look = (.5, 0); blush = sweat = 0
    if t >= T_FREEZE: om = "shock"; um = "shock" if t < T_THINK + .6 else "neutral"; look = (.6, 0)
    if t >= T_WRONG: um = "oops"; blush = seg(t, T_WRONG, T_WRONG + .5); sweat = seg(t, T_WRONG + .3, T_RIGHT)
    if t >= T_RIGHT: um = "happy"; om = "happy"; blush = 1 - seg(t, T_RIGHT, T_RIGHT + .6); sweat = 0
    if t >= T_PUNCH + .5: um = "shock"; om = "happy"; sweat = seg(t, T_PUNCH + .5, T_PUNCH + 1.2); look = (.7, -.3)
    bob = math.sin(t * 5) * 4 if not frz else 0
    shake = math.sin(t * 60) * 7 * (1 - seg(t, T_FREEZE, T_FREEZE + .5)) if t >= T_FREEZE else 0
    oma(c, 770, 920 + bob * .6, 1.25, om, shake)
    ue(c, 320, 905 + bob, 2.15, um, look, blush, sweat, arm=ease(seg(t, .2, .8)) * (1 - seg(t, T_THINK, T_THINK + .4)))
    # table + plates
    c.rect((0, 1060, 1080, 1100), TABLE); c.rect((0, 1100, 1080, 1290), TABLE2)
    px = 330 + 190 * ease(seg(t, .25, .85))
    c.ell((px - 120, 1030, px + 120, 1090), INK); c.ell((px - 112, 1034, px + 112, 1084), WHITE); c.ell((px - 66, 1046, px + 66, 1074), (238, 238, 240))
    if t >= T_PUNCH:
        q = back(seg(t, T_PUNCH, T_PUNCH + .45)); kx = 700
        c.ell((kx - 100, 1036, kx + 100, 1088), INK); c.ell((kx - 94, 1040, kx + 94, 1084), WHITE)
        if q > 0: c.poly([(kx - 60 * q, 1062), (kx + 60 * q, 1062), (kx + 40 * q, 1010 - 0 * q), (kx - 40 * q, 1030)], (196, 140, 80)); c.rect((kx - 60 * q, 1040, kx + 60 * q, 1062), (240, 200, 140))
    # speech
    if t < T_RIGHT: bubble(c, 330, 530, [CFG["say"]], 66, tail=-1, p=seg(t, T_SAY, T_SAY + .35))
    else: bubble(c, 330, 530, [CFG["right"]], 66, fill=(225, 246, 232), fg=GREEN, tail=-1, p=seg(t, T_RIGHT, T_RIGHT + .35))
    if T_FREEZE <= t < T_RIGHT:
        p = back(seg(t, T_FREEZE, T_FREEZE + .3)); c.text((800, 690), "?!", 120 * max(p, .01), RED)
    if t >= T_PUNCH: bubble(c, 785, 600, CFG["punch"], 52, tail=1, p=seg(t, T_PUNCH, T_PUNCH + .35), w="Bold")
    # header
    c.text((540, 168), CFG["header"], c.fit(CFG["header"], 78, 960), INK)
    c.text((540, 248), CFG["sub"], c.fit(CFG["sub"], 44, 960, "SemiBold"), (90, 96, 110), "SemiBold")
    # captions under the table
    if T_THINK <= t < T_WRONG:
        left = T_WRONG - t; p = seg(t, T_THINK, T_THINK + .3)
        card(c, 1440, [("Чому бабуся в шоці?", 60, INK, "Black"), ("Вгадай за 3 секунди", 46, (90, 96, 110), "SemiBold")], p, fill=(255, 248, 220))
        cx, cy, r = 540, 1640, 62; c.circ(cx, cy, r + 8, INK); c.circ(cx, cy, r, WHITE)
        c.d.pieslice([(cx - r) * 2, (cy - r) * 2, (cx + r) * 2, (cy + r) * 2], -90, -90 + 360 * (left / 3), fill=(255, 214, 70))
        c.text((cx, cy), str(min(3, math.ceil(left))), 64, INK)
    elif T_WRONG <= t < T_RIGHT:
        p = seg(t, T_WRONG, T_WRONG + .3)
        card(c, 1470, [(CFG["say"], 64, RED, "Black"), (CFG["wrong_ua"], 50, INK, "Bold"), (CFG["wrong_note"], 38, (90, 96, 110), "SemiBold")], p, fill=(255, 236, 236), border=RED)
        tw = c.tw(CFG["say"], 64); y0 = 1470 - (64 * 1.25 + 50 * 1.25 + 38 * 1.25 + 60) / 2 + 30 + 40
        strike(c, 540 - tw / 2 - 10, 540 + tw / 2 + 10, y0, seg(t, T_WRONG + .5, T_WRONG + .9))
    elif t >= T_RIGHT:
        p = seg(t, T_RIGHT, T_RIGHT + .3)
        card(c, 1470, [("Правильно:", 42, (90, 96, 110), "SemiBold"), (CFG["right"], 72, GREEN, "Black"), (CFG["right_ua"], 50, INK, "Bold")], p, fill=(232, 248, 238), border=GREEN)
    fr = c.done().convert("RGBA")
    fr.alpha_composite(TAG, ((K.W - TAG.width) // 2, 286))
    if t >= T_END:
        dim = Image.new("RGBA", fr.size, (20, 22, 30, int(150 * seg(t, T_END, T_END + .4)))); fr.alpha_composite(dim)
        FC.draw_end(fr, t, T_END, CARDS, y=1050)
    return fr

def audio(path):
    tr = K.Track(DUR)
    m = CA.music(DUR, 104)
    import numpy as np
    env = np.ones(len(m)); i0, i1 = int(T_FREEZE * K.SR), int(T_WRONG * K.SR)
    env[i0:i1] = .12; env[i1:i1 + int(.4 * K.SR)] = np.linspace(.12, 1, int(.4 * K.SR))
    tr.add(m * env * 1.6, 0)
    tr.add(K.tone(523, .14, 18, ((1, 1), (2, .3))), T_SAY, .5); tr.add(K.tone(659, .16, 16, ((1, 1), (2, .3))), T_SAY + .1, .5)
    tr.add(K.tone(330, .5, 5, ((1, 1), (2, .4))), T_FREEZE, .8); tr.add(K.tone(311, .6, 4, ((1, 1), (2, .4))), T_FREEZE + .18, .8)
    for k in range(3): tr.add(CA.tick(k == 2), T_THINK + k + .02, .6)
    tr.add(K.tone(392, .25, 10, ((1, 1), (2, .3))), T_WRONG, .6); tr.add(K.tone(370, .45, 7, ((1, 1), (2, .3))), T_WRONG + .2, .6)
    tr.add(K.ding(), T_RIGHT, .55); tr.add(K.ding(1318.5), T_RIGHT + .12, .4)
    tr.add(K.tone(784, .12, 20), T_PUNCH, .4); tr.add(K.ding(), T_END + 1.3, .35)
    tr.save(path)

if __name__ == "__main__": K.main(render, DUR, audio)
