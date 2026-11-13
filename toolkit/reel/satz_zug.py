"""«Речення-потяг»: word order as a train. Every word is a wagon, the verb always rides in wagon №2;
'weil' sends the verb to the tail. Phases: s1 (rule) -> 3-s quiz -> s2 (inversion, verb stays in №2) -> s3 (weil, verb jumps to the tail) -> follow card.
CFG=examples/zug01.json python3 satz_zug.py out.mp4 | preview <dir> t.. | audio out.wav
"""
import json, math, os, sys
from pathlib import Path
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kino as K, follow_card as FC, clean_audio as CA
from kino import seg, ease, back, out3, lerp, INK, YEL, WHITE

CFG = json.load(open(os.environ["CFG"], encoding="utf-8"))
S1, S2, S3, QZ = CFG["s1"], CFG["s2"], CFG["s3"], CFG["quiz"]
VERB = S1["words"][S1["verb"]].lower()
T_Q, T_R, T_W, T_END = 3.3, 6.7, 10.3, 14.4
DUR = T_END + 3.8
SKY, HILL, HILL2, GROUND, RAIL = (206, 232, 250), (150, 205, 140), (120, 185, 120), (226, 204, 160), (92, 84, 80)
CORAL, GREEN, RED, GREY, BLUE = (255, 120, 96), (34, 160, 90), (214, 48, 49), (90, 96, 110), (60, 120, 220)
CARDS = FC.make(CFG); TAG = FC.series_tag(CFG["series"])
SIZE, PAD, GAP, LOCO, WH, RY = 66, 26, 14, 150, 118, 1010          # wagon font, padding, gap, loco width, wagon height, rail y
_F = K.F(SIZE)

def layout(words):
    """-> ({key: (cx, w, text)}, scale): train scaled to fit 1000 px, starts at x=40."""
    ws = [_F.getlength(w) + 2 * PAD for w in words]
    tot = LOCO + GAP + sum(ws) + GAP * (len(ws) - 1); k = min(1, 960 / tot)
    x = 40 + (LOCO + GAP) * k; out = {}
    for w, ww in zip(words, ws):
        out[w.lower()] = (x + ww * k / 2, ww * k, w); x += (ww + GAP) * k
    return out, k
L1, L2, L3 = layout(S1["words"]), layout(S2["words"]), layout(S3["words"])

def wheel(c, x, y, r, t):
    c.circ(x, y, r, INK); c.circ(x, y, r * .55, (200, 204, 214))
    a = t * 7; c.line([(x - math.cos(a) * r * .5, y - math.sin(a) * r * .5), (x + math.cos(a) * r * .5, y + math.sin(a) * r * .5)], INK, 4)

def wagon(c, cx, w, text, k, t, kind="", lift=0., num=None, na=1.):
    h = WH * k; y1 = RY - 26 * k - lift; y0 = y1 - h
    fill = {"verb": YEL, "weil": CORAL}.get(kind, WHITE)
    c.rrect((cx - w / 2 - 5, y0 - 5, cx + w / 2 + 5, y1 + 5), 20 * k, INK); c.rrect((cx - w / 2, y0, cx + w / 2, y1), 16 * k, fill)
    c.text((cx, (y0 + y1) / 2), text, SIZE * k, INK)
    for dx in (-.28, .28): wheel(c, cx + w * dx, RY - 14 * k - lift, 18 * k, t)
    if num and na > 0:
        col = K.mix(GROUND, INK if kind != "verb" else RED, na)
        c.text((cx, RY + 62), num, 46 if kind != "verb" else 56, col)

def loco(c, k, t, dx):
    x0 = 40 + dx; w = LOCO * k; y1 = RY - 26 * k; h = WH * k
    c.rrect((x0 - 5, y1 - h * .7 - 5, x0 + w + 5, y1 + 5), 18 * k, INK); c.rrect((x0, y1 - h * .7, x0 + w, y1), 14 * k, BLUE)
    c.rrect((x0 + w * .5 - 5, y1 - h * 1.15 - 5, x0 + w + 5, y1 - h * .4), 14 * k, INK); c.rrect((x0 + w * .5, y1 - h * 1.15, x0 + w, y1 - h * .4), 10 * k, BLUE)
    c.rrect((x0 + w * .6, y1 - h * 1.02, x0 + w * .9, y1 - h * .66), 6 * k, (220, 240, 255))
    c.rect((x0 + w * .14, y1 - h * 1.0, x0 + w * .34, y1 - h * .7), INK)
    for i in range(3):                                                # calm smoke puffs
        p = (t * .6 + i / 3) % 1
        c.circ(x0 + w * .24 - p * 30, y1 - h * 1.05 - p * 150, (10 + 22 * p) * k, K.mix((250, 250, 252), SKY, p))
    for fx in (.25, .75): wheel(c, x0 + w * fx, RY - 16 * k, 22 * k, t)

def card(c, cy, lines, p, fill=WHITE, border=INK):
    if p <= 0: return
    s = .85 + .15 * back(min(1, p)); off = (1 - out3(min(1, p))) * 60
    hs = [sz * 1.25 for _, sz, _, _ in lines]; h = sum(hs) + 60
    c.rrect((70, cy - h / 2 + off, 1010, cy + h / 2 + off), 34, border); c.rrect((76, cy - h / 2 + 6 + off, 1004, cy + h / 2 - 6 + off), 30, fill)
    y = cy - h / 2 + 30 + off
    for (tx, sz, col, w), hh in zip(lines, hs):
        sz = c.fit(tx, sz * s, 880, w); c.text((540, y + hh / 2), tx, sz, col, w); y += hh

def render(t):
    c = K.Canvas(SKY, S=2)
    for i, (cx, r) in enumerate(((200, 330), (620, 420), (980, 300))): c.circ(cx, 1010 + r * .45, r, HILL if i != 1 else HILL2)
    for i in range(3):                                                # clouds drift slowly
        x = (i * 430 + t * 14) % 1300 - 110; y = 470 + i * 70
        for dx, r in ((0, 44), (48, 58), (104, 40)): c.circ(x + dx, y - r * .3, r, WHITE)
    c.rect((0, 1250, 1080, 1920), (196, 228, 178)); c.rect((0, RY, 1080, 1250), GROUND)
    for x in range(-40, 1100, 72): c.rect((x, RY + 6, x + 22, RY + 26), (170, 140, 104))
    c.rect((0, RY - 2, 1080, RY + 8), RAIL)
    # --- train state ---
    if t < T_R: A, B, p = L1, L1, 0
    elif t < T_W: A, B, p = L1, L2, ease(seg(t, T_R, T_R + .8))
    else: A, B, p = L2, L3, ease(seg(t, T_W + .1, T_W + 1.1))
    k = lerp(A[1], B[1], p); dx = (1 - out3(seg(t, 0, .9))) * 1150
    bob = math.sin(t * 9) * 1.5
    loco(c, k, t, dx)
    order = [w.lower() for w in (S1["words"] if t < T_R else S2["words"])]
    num_a = 1 - seg(t, T_W, T_W + .2) if t >= T_W else seg(t, T_R + .8, T_R + 1.1) if t >= T_R else seg(t, .9, 1.3)
    for key, (bx, bw, btxt) in B[0].items():
        if key in A[0]: ax, aw, atxt = A[0][key]
        else: ax, aw, atxt = bx, bw, btxt                              # new wagon ('weil') drops in from above
        cx = lerp(ax, bx, p) + dx; w = lerp(aw, bw, p); txt = btxt if p > .5 else atxt
        lift = 0
        if key == VERB and A is not B and t >= T_W: lift = math.sin(math.pi * p) * 190      # verb flies over to the tail
        elif A is not B and abs(ax - bx) > 5 and key != VERB: lift = math.sin(math.pi * p) * (40 if t < T_W else 0)
        if key not in A[0]:
            q = seg(t, T_W + .6, T_W + 1.1); lift = (1 - out3(q)) * 330 if q > 0 else 3000
        kind = "verb" if key == VERB else ("weil" if key not in L1[0] else "")
        num = None
        if key in order and t < T_W + .2: num = "№%d" % (order.index(key) + 1) if key == VERB else str(order.index(key) + 1)
        wagon(c, cx, w, txt, k, t, kind, lift + (bob if lift == 0 else 0), num, num_a)
    if t >= T_W + 1.2:
        vx = L3[0][VERB][0]; q = back(seg(t, T_W + 1.2, T_W + 1.55))
        if q > 0: c.text((min(vx, 950), RY + 64), "хвіст", 52 * q, RED)
    # --- header ---
    c.text((540, 168), CFG["header"], c.fit(CFG["header"], 78, 960), INK)
    c.text((540, 248), CFG["sub"], c.fit(CFG["sub"], 44, 960, "SemiBold"), GREY, "SemiBold")
    # --- captions ---
    if t < T_Q:
        card(c, 1440, [(" ".join(S1["words"]) + ".", 70, INK, "Black"), (S1["ua"], 46, GREY, "SemiBold"), (S1["note"], 46, RED, "Bold")], seg(t, .9, 1.2), fill=(255, 248, 220))
    elif t < T_R:
        left = T_R - t
        card(c, 1420, [(QZ["ask"], 46, GREY, "SemiBold"), (QZ["q"], 70, INK, "Black"), ("A: %s      B: %s" % tuple(QZ["opts"]), 56, BLUE, "Black")], seg(t, T_Q, T_Q + .3), fill=(255, 248, 220))
        cx, cy, r = 540, 1660, 58; c.circ(cx, cy, r + 8, INK); c.circ(cx, cy, r, WHITE)
        c.d.pieslice([(cx - r) * 2, (cy - r) * 2, (cx + r) * 2, (cy + r) * 2], -90, -90 + 360 * min(1, left / 3), fill=YEL)
        c.text((cx, cy), str(min(3, math.ceil(left))), 60, INK)
    elif t < T_W:
        card(c, 1440, [(" ".join(S2["words"]) + ".", 70, GREEN, "Black"), (S2["ua"], 46, GREY, "SemiBold"), (S2["note"], 46, INK, "Bold")], seg(t, T_R, T_R + .3), fill=(232, 248, 238), border=GREEN)
    else:
        card(c, 1440, [(S3["pre"] + " " + " ".join(S3["words"]) + ".", 70, INK, "Black"), (S3["ua"], 46, GREY, "SemiBold"), (S3["note"], 46, RED, "Bold")], seg(t, T_W, T_W + .3), fill=(255, 236, 232), border=CORAL)
    fr = c.done().convert("RGBA")
    fr.alpha_composite(TAG, ((K.W - TAG.width) // 2, 286))
    if t >= T_END:
        fr.alpha_composite(Image.new("RGBA", fr.size, (20, 22, 30, int(150 * seg(t, T_END, T_END + .4)))))
        FC.draw_end(fr, t, T_END, CARDS, y=1050)
    return fr

def audio(path):
    import numpy as np
    tr = K.Track(DUR); m = CA.music(DUR, 100); env = np.ones(len(m))
    i0, i1 = int(T_Q * K.SR), int(T_R * K.SR); env[i0:i1] = .15; env[i1:i1 + int(.4 * K.SR)] = np.linspace(.15, 1, int(.4 * K.SR))
    tr.add(m * env * 1.6, 0)
    for i in range(6): tr.add(K.tri(196, .09, 30), .05 + i * .14, .28 * (1 - i / 8))          # train rolls in (soft tonal chug)
    tr.add(K.tone(587, .3, 8, ((1, 1), (1.26, .8))), .9, .3)                                      # two-tone whistle
    tr.add(K.ding(), 1.3, .3)
    for k in range(3): tr.add(CA.tick(k == 2), T_R - 3 + k + .02, .6)
    tr.add(K.ding(), T_R, .5); tr.add(K.ding(1318.5), T_R + .12, .35)
    tr.add(K.tone(330, .3, 9, ((1, 1), (2, .4))), T_W, .6)                                        # 'weil' drops
    for i, f in enumerate((392, 494, 587, 784)): tr.add(K.pulse(f, .12, 16), T_W + .2 + i * .22, .2)   # verb flies
    tr.add(K.ding(), T_W + 1.2, .5); tr.add(K.ding(), T_END + 1.3, .35)
    tr.save(path)

if __name__ == "__main__": K.main(render, DUR, audio)
