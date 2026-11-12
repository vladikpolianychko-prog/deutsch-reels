"""«Dativ-біт»: kinetic-typography reel on a code-made beat (120 BPM). Every word lands exactly on a beat.
A: words slam one per beat -> B: '= DATIV, завжди' -> C: examples with the Dativ form highlighted -> D: 2-s quiz -> E: fast replay -> follow card.
CFG=examples/beat01.json python3 dativ_beat.py out.mp4 | preview <dir> t.. | audio out.wav
"""
import json, math, os, sys
from pathlib import Path
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kino as K, follow_card as FC
from kino import seg, ease, back, out3, clamp, INK, YEL, WHITE

CFG = json.load(open(os.environ["CFG"], encoding="utf-8"))
WORDS, EX, QZ = CFG["words"], CFG["examples"], CFG["quiz"]
BPM = 120; B = 60 / BPM
NA = len(WORDS)                         # beats 0..NA-1 slam words
TB = (NA + 1) * B                       # phase B start
TC = TB + 4 * B                         # examples, 3 beats each
TD = TC + 3 * B * len(EX)               # quiz: 4 beats think, reveal
TR = TD + 4 * B
TE = TR + 3 * B                         # fast replay
T_END = TE + 3 * B
DUR = T_END + 3.7
BG = (16, 16, 22); CORAL, CYAN, GREEN, GREY = (255, 110, 90), (90, 210, 255), (60, 210, 120), (140, 146, 160)
PAL = [YEL, WHITE, CORAL, CYAN, YEL, WHITE, CORAL, CYAN]
CARDS = FC.make(CFG); TAG = FC.series_tag(CFG["series"])

def slam(c, xy, s, size, col, p, w="Black"):
    if p <= 0: return
    k = 1 + .55 * (1 - out3(min(1, p / .25)))
    size = c.fit(s, size, 940, w); c.text(xy, s, size * k, col, w)

def chip(c, cx, cy, s, size, fill, fg, p=1):
    if p <= 0: return
    k = .6 + .4 * back(min(1, p)); size *= k
    w = c.tw(s, size); c.rrect((cx - w / 2 - 22, cy - size * .72, cx + w / 2 + 22, cy + size * .72), 18, fill); c.text((cx, cy), s, size, fg)

def render(t):
    beat = t / B; bi = int(beat); fb = beat - bi
    pulse = (1 - min(1, fb / .35)) if t < T_END else 0
    c = K.Canvas(K.mix(BG, (40, 40, 56), .55 * pulse * (t < TD or t >= TR)))
    c.text((540, 150), CFG["header"], c.fit(CFG["header"], 66, 960), WHITE)
    c.text((540, 332), "Увімкни звук: слова йдуть у біт", 34, GREY, "SemiBold")
    # beat counter
    if t < T_END:
        for i in range(4):
            on = (bi % 4) == i; c.circ(408 + i * 88, 1480, 16 if on else 11, YEL if on else (60, 60, 76))
    if t < TB:                                                       # A: slam one word per beat
        k = min(bi, NA - 1)
        slam(c, (540, 860), WORDS[k].upper(), 300, PAL[k % len(PAL)], t - k * B)
        for i in range(k):                                            # trail of previous words
            c.text((540 - (k - 1) * 70 + i * 140, 1180), WORDS[i], 40, GREY, "Bold")
    elif t < TC:                                                      # B: list + '= DATIV'
        for i, w in enumerate(WORDS):
            c.text((300, 520 + i * 96), w, 72, PAL[i % len(PAL)], "Black")
        c.line([(430, 490), (470, 490), (470, 1170), (430, 1170)], GREY, 8)
        slam(c, (760, 790), "DATIV", 150, YEL, t - TB)
        if t >= TB + 2 * B: slam(c, (760, 930), "завжди", 80, WHITE, t - TB - 2 * B)
    elif t < TD:                                                      # C: examples
        k = min(int((t - TC) / (3 * B)), len(EX) - 1); lt = t - TC - k * 3 * B
        e = EX[k]; pre, art, noun = e["de"]
        size = 104
        for _ in range(12):
            tot = c.tw(pre + " ", size) + c.tw(art, size) + 44 + c.tw(" " + noun, size)
            if tot <= 960: break
            size -= 6
        x = 540 - tot / 2; y = 860
        slam(c, (x + c.tw(pre, size) / 2, y), pre, size, WHITE, lt)
        x2 = x + c.tw(pre + " ", size) + 22
        if lt >= B * .5:
            q = lt - B * .5; aw = c.tw(art, size)
            c.rrect((x2 - 22, y - size * .7, x2 + aw + 22, y + size * .7), 20, YEL); slam(c, (x2 + aw / 2, y), art, size, INK, q)
        if lt >= B:
            slam(c, (x2 + c.tw(art, size) + 22 + c.tw(" " + noun, size) / 2, y), " " + noun, size, WHITE, lt - B)
            c.text((540, 1010), e["ua"], 58, GREY, "Bold")
        c.text((540, 1180), e["note"], 44, CYAN, "Bold")
        c.text((540, 420), f"{k + 1}/{len(EX)}", 40, GREY, "Bold")
    elif t < TE:                                                      # D: quiz
        c.text((540, 600), "Встигнеш за 2 секунди?", 56, YEL)
        c.text((540, 760), QZ["q"], c.fit(QZ["q"], 96, 960), WHITE)
        rev = t >= TR
        for i, o in enumerate(QZ["opts"]):
            ok = o == QZ["a"]
            fill = (GREEN if ok else (50, 50, 64)) if rev else (50, 50, 64)
            chip(c, 300 + i * 240, 980, o, 80, fill, WHITE if (not rev or ok) else (110, 110, 126), seg(t, TD + i * .12, TD + i * .12 + .3))
        if not rev:
            left = TR - t; c.text((540, 1180), str(math.ceil(left)), 110, WHITE)
        else:
            c.text((540, 1170), QZ["ua"], 56, GREY, "Bold")
            c.text((540, 1260), QZ["why"], 44, CYAN, "Bold")
    else:                                                             # E: fast replay + loop hint
        k = min(int((t - TE) / (3 * B / NA)), NA - 1)
        c.text((540, 700), "Ще раз, швидко:", 52, GREY, "Bold")
        slam(c, (540, 900), WORDS[k].upper(), 220, PAL[k % len(PAL)], (t - TE) - k * (3 * B / NA))
        if t >= T_END - 0.2 or k == NA - 1: c.text((540, 1100), "+ DATIV", 90, YEL)
    fr = c.done().convert("RGBA")
    fr.alpha_composite(TAG, ((K.W - TAG.width) // 2, 200))
    if t >= T_END:
        dim = Image.new("RGBA", fr.size, (10, 10, 16, int(170 * seg(t, T_END, T_END + .3)))); fr.alpha_composite(dim)
        FC.draw_end(fr, t, T_END, CARDS, y=1250)
    return fr

def audio(path):
    tr = K.Track(DUR)
    bass = [110, 110, 130.81, 98]
    nb = int(T_END / B) + 1
    for i in range(nb):
        t = i * B; quiet = TD <= t < TR
        if not quiet: tr.add(K.kick(), t, .6)
        if i % 2 == 1 and not quiet: tr.add(K.clap(), t, .28)
        tr.add(K.hat(), t + B / 2, .12); tr.add(K.hat(), t, .07)
        f = bass[(i // 4) % 4]
        tr.add(K.tri(f, B * .9, 2.5), t, .32 if not quiet else .15)
        if i % 4 == 2: tr.add(K.tri(f * 2, B * .5, 6), t + B / 2, .12)
    for i in range(NA): tr.add(K.pulse([440, 523.25, 659.25, 587.33][i % 4], .22, 10), i * B, .2)
    tr.add(K.pulse(880, .5, 4), TB, .25); tr.add(K.pulse(659.25, .5, 4), TB, .2)
    for k in range(len(EX)): tr.add(K.pulse(783.99, .12, 16), TC + k * 3 * B + B * .5, .18)
    for k in range(4): tr.add(K.tone(1500, .05, 60), TD + k * B, .2)
    tr.add(K.ding(), TR, .45); tr.add(K.ding(1318.5), TR + .1, .3)
    for k in range(NA): tr.add(K.pulse(659.25, .08, 20), TE + k * 3 * B / NA, .15)
    tr.add(K.ding(), T_END + 1.3, .3)
    tr.save(path)

if __name__ == "__main__": K.main(render, DUR, audio)
