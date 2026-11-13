"""«Слово, якого немає в українській»: mini-film in cinema style (dark screen, letterbox, calm titles).
A: the word -> splits into two parts with literal meanings -> B: 3-s guess -> C: real meaning + clock running to the end of the working day
-> D: two phrases from real life -> follow card.
CFG=examples/wort01.json python3 wort_film.py out.mp4 | preview <dir> t.. | audio out.wav
"""
import json, math, os, sys
from pathlib import Path
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kino as K, follow_card as FC, clean_audio as CA
from kino import seg, ease, back, out3, lerp, INK, YEL, WHITE

CFG = json.load(open(os.environ["CFG"], encoding="utf-8"))
P1, P2 = CFG["parts"]; PH = CFG["phrases"]
T_SPLIT, T_Q, T_R, T_USE, T_USE2, T_END = 1.3, 2.9, 6.0, 9.8, 11.9, 14.3
DUR = T_END + 3.8
BG, BG2, GREY, DIM, RED, GREEN, CREAM = (16, 15, 22), (30, 28, 40), (150, 152, 166), (70, 72, 86), (235, 87, 87), (80, 210, 140), (255, 244, 214)
CARDS = FC.make(CFG); TAG = FC.series_tag(CFG["series"])

def fade(c, xy, s, size, col, p, w="Black", dy=24, maxw=940):
    if p <= 0: return
    p = min(1, p); size = c.fit(s, size, maxw, w)
    c.text((xy[0], xy[1] + (1 - out3(p)) * dy), s, size, K.mix(BG, col, p), w)

def clock(c, cx, cy, r, hour, glow):
    c.circ(cx, cy, r + 14, K.mix(DIM, YEL, glow)); c.circ(cx, cy, r, K.mix(BG2, CREAM, glow))
    fg = K.mix(WHITE, INK, glow)
    for i in range(12):
        a = i * math.pi / 6; r0 = r * (.8 if i % 3 == 0 else .88)
        c.line([(cx + math.sin(a) * r0, cy - math.cos(a) * r0), (cx + math.sin(a) * r * .94, cy - math.cos(a) * r * .94)], fg, 8 if i % 3 == 0 else 4)
    ah = hour / 12 * 2 * math.pi; am = (hour % 1) * 2 * math.pi
    c.line([(cx, cy), (cx + math.sin(am) * r * .74, cy - math.cos(am) * r * .74)], fg, 9)
    c.line([(cx, cy), (cx + math.sin(ah) * r * .48, cy - math.cos(ah) * r * .48)], K.mix(YEL, RED, glow), 14)
    c.circ(cx, cy, 13, fg)

def render(t):
    c = K.Canvas(BG, S=2)
    c.rect((0, 0, 1080, 96), (0, 0, 0)); c.rect((0, 1824, 1080, 1920), (0, 0, 0))            # letterbox
    c.text((540, 176), CFG["header"][0], c.fit(CFG["header"][0], 70, 960), WHITE)
    c.text((540, 262), CFG["header"][1], c.fit(CFG["header"][1], 70, 960), YEL)
    # --- the word: whole -> two parts ---
    word = P1["de"] + P2["de"].lower(); size = c.fit(word, 170, 960)
    w1, w2 = c.tw(P1["de"], size), c.tw(P2["de"].lower(), size)
    sp = ease(seg(t, T_SPLIT, T_SPLIT + .5)) * (1 - ease(seg(t, T_R - .1, T_R + .4)))
    up = ease(seg(t, T_USE - .3, T_USE + .2))
    wy = 640; gap = 46 * sp; x0 = 540 - (w1 + w2 + gap) / 2
    k = 1 + .25 * (1 - out3(seg(t, 0, .35)))
    if t < T_USE + .2 or True:
        c.text((x0 + w1 / 2, wy), P1["de"], size * k, K.mix(WHITE, YEL, 1 - sp)); c.text((x0 + w1 + gap + w2 / 2, wy), P2["de"].lower() if sp < .5 else P2["de"], size * k, K.mix((120, 200, 255), YEL, 1 - sp))
    c.text((540, wy - size * .82), CFG["article"], 44, GREY, "SemiBold")
    if T_SPLIT + .3 <= t < T_R:
        fade(c, (x0 + w1 / 2, wy + size * .78), P1["ua"], 54, WHITE, (t - T_SPLIT - .3) / .3, "Bold", maxw=w1 + 60)
        fade(c, (x0 + w1 + gap + w2 / 2, wy + size * .78), P2["ua"], 54, (120, 200, 255), (t - T_SPLIT - .7) / .3, "Bold", maxw=w2 + 60)
        c.text((x0 + w1 + gap / 2, wy + size * .78), "+", 54, GREY) if t >= T_SPLIT + .7 else None
    # --- B: guess ---
    if T_Q <= t < T_R:
        left = T_R - t
        fade(c, (540, 1010), CFG["guess"], 76, CREAM, (t - T_Q) / .3)
        fade(c, (540, 1110), "Вгадай значення за 3 секунди", 46, GREY, (t - T_Q - .15) / .3, "SemiBold")
        cx, cy, r = 540, 1330, 70; c.circ(cx, cy, r + 8, DIM); c.circ(cx, cy, r, BG2)
        c.d.pieslice([(cx - r) * 2, (cy - r) * 2, (cx + r) * 2, (cy + r) * 2], -90, -90 + 360 * min(1, left / 3), fill=YEL)
        c.circ(cx, cy, r - 16, BG2); c.text((cx, cy), str(min(3, math.ceil(left))), 64, WHITE)
    # --- C: real meaning ---
    if T_R <= t < T_USE:
        a = 1 - seg(t, T_USE - .3, T_USE)
        hour = lerp(9, 17, ease(seg(t, T_R + .2, T_R + 1.7))); glow = seg(t, T_R + 1.7, T_R + 2.0) * a
        if a > 0.05:
            clock(c, 540, 1000, 170 * (.6 + .4 * back(seg(t, T_R, T_R + .35))), hour, glow)
            if t >= T_R + 1.7: fade(c, (540, 1236), CFG["clock_label"], 56, YEL, (t - T_R - 1.7) / .3)
        fade(c, (540, 1400), CFG["meaning"][0], 72, GREEN, min(a, (t - T_R - 2.0) / .3))
        fade(c, (540, 1496), CFG["meaning"][1], 50, WHITE, min(a, (t - T_R - 2.3) / .3), "Bold")
        fade(c, (540, 1590), CFG["not"], 44, RED, min(a, (t - T_R - .2) / .3), "Bold")
    # --- D: phrases from life ---
    if t >= T_USE:
        for i, (ph, t0) in enumerate(zip(PH, (T_USE, T_USE2))):
            y = 880 + i * 400; p = (t - t0) / .35
            if p <= 0: continue
            sz = c.fit(ph["de"], 84, 880); tw = c.tw(ph["de"], sz); q = out3(min(1, p))
            c.rrect((540 - tw / 2 - 44, y - 78, 540 + tw / 2 + 44, y + 78), 40, K.mix(BG, BG2 if i else YEL, q))
            c.text((540, y), ph["de"], sz, K.mix(BG, WHITE if i else INK, q))
            fade(c, (540, y + 130), ph["ua"], 50, CREAM, p - .4, "Bold")
            fade(c, (540, y + 196), ph["note"], 40, GREY, p - .7, "SemiBold")
    fr = c.done().convert("RGBA")
    fr.alpha_composite(TAG, ((K.W - TAG.width) // 2, 318))
    if t >= T_END:
        fr.alpha_composite(Image.new("RGBA", fr.size, (6, 6, 10, int(175 * seg(t, T_END, T_END + .4)))))
        FC.draw_end(fr, t, T_END, CARDS, y=1050)
    return fr

def audio(path):
    tr = K.Track(DUR)
    for i, t0 in enumerate([x * 3.2 for x in range(int(DUR / 3.2) + 1)]):                  # slow cinematic pad: Am - F - C - G
        for f in ((110, 220, 261.63, 329.63), (87.31, 174.61, 220, 261.63), (130.81, 196, 261.63, 329.63), (98, 196, 246.94, 293.66))[i % 4]:
            tr.add(K.tone(f, 3.4, .5, ((1, 1), (2, .25)), att=.5), t0, .16 if not (T_Q <= t0 < T_R - 1) else .09)
    tr.add(K.tone(110, 1.2, 3, ((1, 1), (2, .5))), 0, .7); tr.add(K.ding(659.25), .05, .3)
    tr.add(K.ding(880), T_SPLIT + .3, .25); tr.add(K.ding(1046.5), T_SPLIT + .7, .25)
    for k in range(3): tr.add(CA.tick(k == 2), T_R - 3 + k + .02, .6)
    for i in range(8): tr.add(K.tone(1200, .04, 70), T_R + .25 + i * .18, .14)             # clock hands run
    tr.add(K.ding(), T_R + 1.7, .5); tr.add(K.ding(1318.5), T_R + 1.82, .35); tr.add(K.ding(1568), T_R + 1.94, .25)
    tr.add(K.ding(784), T_USE, .35); tr.add(K.ding(880), T_USE2, .35); tr.add(K.ding(), T_END + 1.3, .35)
    tr.save(path)

if __name__ == "__main__": K.main(render, DUR, audio)
