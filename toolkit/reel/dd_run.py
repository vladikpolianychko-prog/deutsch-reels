"""«Der · Die · Das Run»: 8-bit runner. A word appears, three gates (der/die/das) roll in, 2 s to choose,
pixel-Ü runs through the right gate. Scene is drawn at 270x480 and upscaled x4 (nearest) for real pixel look; HUD is full-res.
CFG=examples/run01.json python3 dd_run.py out.mp4 | preview <dir> t.. | audio out.wav
"""
import json, math, os, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kino as K, follow_card as FC
from kino import seg, ease, back, out3, clamp, INK, YEL, WHITE

CFG = json.load(open(os.environ["CFG"], encoding="utf-8")); WORDS = CFG["items"]
T0, R, THINK = 0.0, 3.2, 2.0
T_RES = T0 + R * len(WORDS); T_END = T_RES + 1.6; DUR = T_END + 3.7
LW, LH, SC = 270, 480, 4
HOR, HERO_Y = 196, 356                      # low-res horizon and hero feet line
COL = {"der": (64, 140, 255), "die": (240, 72, 84), "das": (52, 200, 110)}
LANE = {"der": -1, "die": 0, "das": 1}
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
_mf = {}
def M(n):
    n = int(n)
    if n not in _mf: _mf[n] = ImageFont.truetype(MONO, n)
    return _mf[n]
CARDS = FC.make(CFG); TAG = FC.series_tag(CFG["series"])

# static sky (low-res)
SKY = Image.new("RGB", (LW, LH)); sd = ImageDraw.Draw(SKY)
for y in range(LH):
    p = min(1, y / HOR); sd.line([(0, y), (LW, y)], fill=K.mix((18, 14, 48), (92, 52, 140), p))
import random
rnd = random.Random(3)
STARS = [(rnd.randrange(LW), rnd.randrange(20, HOR - 40), rnd.random()) for _ in range(46)]
MOUNT = [(0, HOR)] + [(x, HOR - 18 - int(14 * math.sin(x / 17) + 9 * math.sin(x / 7.3))) for x in range(0, LW + 1, 6)] + [(LW, HOR)]
sd.polygon(MOUNT, fill=(40, 26, 84))
sd.rectangle((0, HOR - 34, LW, HOR - 30), fill=(255, 130, 90))
sd.ellipse((LW // 2 - 26, HOR - 70, LW // 2 + 26, HOR - 18), fill=(255, 170, 80)); sd.rectangle((0, HOR - 34, LW, HOR), fill=(40, 26, 84))
sd.polygon(MOUNT, fill=(40, 26, 84))

SPRITE = ["..WWW...WWW..",
          ".WWKW...WKWW.",
          "..WWW...WWW..",
          ".............",
          ".YY.......YY.",
          ".YY.......YY.",
          ".YY.......YY.",
          ".YY.......YY.",
          ".YYY.....YYY.",
          "..YYYYYYYYY..",
          "...YYYYYYY..."]
PAL = {"W": (255, 255, 255), "K": (20, 20, 30), "Y": (255, 214, 70), "L": (255, 160, 50)}

def road_hw(y): return 10 + (LW * .78) * (y - HOR) / (LH - HOR)          # half width at low-res row y

def gate_y(p): return HOR + (HERO_Y - HOR) * (p ** 1.6)

def scene(t, lane_x, gate_p, flash_lane, flash):
    im = SKY.copy(); d = ImageDraw.Draw(im)
    for x, y, ph in STARS:
        if math.sin(t * 3 + ph * 9) > -.3: d.point((x, y), fill=(255, 255, 230))
    scroll = t * 9
    for y in range(HOR, LH):
        hw = road_hw(y); z = 60 / (y - HOR + 2)
        band = int(z + scroll) % 2
        d.line([(0, y), (LW, y)], fill=(30, 110, 70) if band else (26, 96, 62))
        d.line([(LW / 2 - hw, y), (LW / 2 + hw, y)], fill=(70, 70, 92) if band else (62, 62, 84))
        for k in (-1, 1):
            x = LW / 2 + k * hw / 3
            if band: d.line([(x - max(.5, hw / 60), y), (x + max(.5, hw / 60), y)], fill=(236, 236, 240))
        d.point((LW / 2 - hw, y), fill=(255, 255, 255)); d.point((LW / 2 + hw, y), fill=(255, 255, 255))
    gates = []
    if gate_p is not None and 0 <= gate_p <= 1.08:
        gy = gate_y(min(gate_p, 1.0)) + max(0, gate_p - 1) * 300; hw = road_hw(gy); lw = 2 * hw / 3; gh = lw * .95
        for art, k in LANE.items():
            cx = LW / 2 + k * lw; x0, x1 = cx - lw * .44, cx + lw * .44; th = max(1, lw * .07)
            col = COL[art]
            if flash_lane == art and flash > 0: col = K.mix(col, (255, 255, 255), flash)
            d.rectangle((x0, gy - gh, x0 + th, gy), fill=col); d.rectangle((x1 - th, gy - gh, x1, gy), fill=col)
            d.rectangle((x0, gy - gh, x1, gy - gh + th * 2.2), fill=col)
            gates.append((art, cx * SC, (gy - gh * .55) * SC, lw * SC))
    # hero
    s = 3; hx = lane_x - len(SPRITE[0]) * s / 2; hy = HERO_Y - (len(SPRITE) + 2) * s - abs(math.sin(t * 14)) * 3
    for r, row in enumerate(SPRITE):
        for c_, ch in enumerate(row):
            if ch != ".": d.rectangle((hx + c_ * s, hy + r * s, hx + c_ * s + s - 1, hy + r * s + s - 1), fill=PAL[ch])
    leg = int(t * 10) % 2
    for i, lx in enumerate((3, 9)):
        dy = 0 if (i == leg) else 2
        d.rectangle((hx + lx * s, hy + 11 * s, hx + lx * s + s - 1, hy + 11 * s + (2 - dy // 2) * s), fill=PAL["L"])
    d.ellipse((lane_x - 18, HERO_Y + 1, lane_x + 18, HERO_Y + 6), fill=(20, 60, 40))
    return im.resize((K.W, K.H), Image.NEAREST), gates

def ctext(d, xy, s, f, fill, stroke=0, sfill=INK):
    d.text(xy, s, font=f, fill=fill, anchor="mm", stroke_width=stroke, stroke_fill=sfill)

def render(t):
    k = int((t - T0) // R) if t >= T0 else 0; k = min(k, len(WORDS) - 1)
    lt = t - T0 - k * R
    w = WORDS[k]; art = w["art"]
    decided = lt >= THINK + .25
    tx = LW / 2 + LANE[art] * (2 * road_hw(HERO_Y) / 3)
    lane_x = LW / 2 + (tx - LW / 2) * ease(seg(lt, THINK + .25, THINK + .5)) if t < T_RES else LW / 2
    gp = None if t >= T_RES else seg(lt, .25, THINK + .62) * 1.08
    flash = 1 - seg(lt, THINK + .6, THINK + .95) if lt >= THINK + .6 else 0
    fr, gates = scene(t, lane_x, gp, art, flash)
    fr = fr.convert("RGBA"); d = ImageDraw.Draw(fr)
    for a, x, y, lw in gates:
        if lw * .30 >= 22: ctext(d, (x, y), a.upper(), M(max(14, lw * .30)), WHITE, max(2, int(lw * .025)), INK)
    # top HUD
    d.rectangle((0, 0, K.W, 300), fill=(14, 10, 36, 255))
    ctext(d, (540, 92), "DER · DIE · DAS  RUN", M(64), YEL, 4, (120, 40, 20))
    fr.alpha_composite(TAG, ((K.W - TAG.width) // 2, 140))
    hud = f"СЛОВО {min(k + 1, len(WORDS)) if t < T_RES else len(WORDS)}/{len(WORDS)}"
    d.text((70, 250), CFG["level"], font=M(38), fill=WHITE, anchor="lm"); d.text((1010, 250), hud, font=M(38), fill=WHITE, anchor="rm")
    if t < T_RES:
        # word card
        p = back(seg(lt, 0, .25)); y0 = 340
        if p > 0:
            cw, ch = 860 * (0.7 + .3 * p), 250
            d.rounded_rectangle((540 - cw / 2 - 8, y0 - 8, 540 + cw / 2 + 8, y0 + ch + 8), 22, fill=INK)
            d.rounded_rectangle((540 - cw / 2, y0, 540 + cw / 2, y0 + ch), 18, fill=(250, 246, 232))
            if decided:
                ctext(d, (540, y0 + 92), f"{art} {w['de']}", M(96), COL[art], 3, INK)
            else:
                ctext(d, (540, y0 + 92), f"___ {w['de']}", M(96), INK)
            ctext(d, (540, y0 + 190), w["ua"], K.F(52, "Bold"), (90, 96, 110))
        # timer bar
        left = clamp(1 - lt / THINK) if lt >= 0 else 1
        if lt < THINK + .2:
            bw = 860 * left; col = K.mix((255, 214, 70), (240, 72, 84), 1 - left)
            d.rounded_rectangle((110, 616, 970, 648), 16, fill=(40, 34, 70));
            if bw > 8: d.rounded_rectangle((110, 616, 110 + bw, 648), 16, fill=col)
            sec = math.ceil(max(0, THINK - lt))
            if sec: ctext(d, (540, 720), str(sec), M(110), WHITE, 5, INK)
        if THINK + .55 <= lt < THINK + 1.2:
            q = seg(lt, THINK + .55, THINK + 1.2); ctext(d, (lane_x * SC, 1200 - 120 * q), "+1", M(80), YEL, 4, INK)
        if t < 2.2:
            q = 1 - seg(t, 1.9, 2.2); ctext(d, (540, 850), CFG["hook"], K.F(58, "Black"), (255, 214, 70, int(255 * q)), 5, INK)
    else:
        q = seg(t, T_RES, T_RES + .35)
        ov = Image.new("RGBA", fr.size, (10, 8, 30, int(200 * q))); fr.alpha_composite(ov); d = ImageDraw.Draw(fr)
        if q > 0:
            ctext(d, (540, 520), "LEVEL CLEAR!", M(100 * (.6 + .4 * back(q))), YEL, 5, INK)
            for i, ww in enumerate(WORDS):
                ctext(d, (540, 660 + i * 84), f"{ww['art']} {ww['de']}", M(64), COL[ww["art"]], 3, INK)
            if t < T_END: ctext(d, (540, 1140), "Скільки вгадав(-ла)? Пиши ?/5", K.F(52, "Black"), WHITE)
        if t >= T_END: FC.draw_end(fr, t, T_END, CARDS, y=1310)
    return fr

def audio(path):
    tr = K.Track(DUR); bpm = 150; b = 60 / bpm
    bass = [110, 110, 130.81, 98]; arp = [(440, 523.25, 659.25), (440, 523.25, 659.25), (523.25, 659.25, 783.99), (392, 493.88, 587.33)]
    n_bars = int(T_RES / (b * 4)) + 1
    for bar in range(n_bars):
        for e in range(8):
            t = bar * b * 4 + e * b / 2
            if t >= T_RES: break
            tr.add(K.tri(bass[bar % 4] if e % 2 == 0 else bass[bar % 4] * 2, b / 2 * .9, 3), t, .35)
            tr.add(K.pulse(arp[bar % 4][e % 3] * 2, b / 2 * .8, 9), t, .07)
            if e % 2 == 0: tr.add(K.kick(), t, .45)
            else: tr.add(K.hat(), t, .12)
    for i in range(len(WORDS)):
        s = T0 + i * R
        tr.add(K.pulse(660, .07, 25), s, .2)
        tr.add(K.tone(1500, .06, 60), s + THINK - 1, .18); tr.add(K.tone(1800, .06, 60), s + THINK, .25)
        tr.add(K.pulse(987.8, .07, 20), s + THINK + .6, .3); tr.add(K.pulse(1318.5, .28, 9), s + THINK + .67, .3)
    for j, f in enumerate((523.25, 659.25, 783.99, 1046.5)): tr.add(K.pulse(f, .16 if j < 3 else .5, 6), T_RES + .05 + j * .12, .3)
    for j, f in enumerate((523.25, 659.25, 783.99)): tr.add(K.tri(f, 1.4, 1.5), T_RES + .6, .15)
    tr.add(K.ding(), T_END + 1.3, .35)
    tr.save(path)

if __name__ == "__main__": K.main(render, DUR, audio)
