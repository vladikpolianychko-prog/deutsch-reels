"""v5 prototype: the notebook opens, pen-doodle characters come alive and act out a situation (12 s, seamless loop).
cfg keys: sticky, hook1, hook2, say1, say2, klaus1, heard, fix, gloss_de, gloss_ua, cta   (see examples/kita_v5.json)
python3 compose_v5.py [preview t1 t2 ...]  -> FRAMES_DIR/NNNN.jpg (or preview/v5_T.jpg)"""
import math, sys, json, os
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "sheet"))
import make_sheet as M
W, H, FPS, DUR = 1080, 1920, 30, 12.0
M.W, M.H, M.SC = W, H, 1.0
CFG = json.load(open(os.environ["CFG"], encoding="utf-8"))
FRAMES = Path(os.environ.get("FRAMES_DIR", str(ROOT / "frames_v5")))
C = M.COL; INK = C["ink"]; RED = C["red"]; BLUE = C["blue"]; ORANGE = C["orange"]; GREEN = C["green"]
PINK, LIME, YEL, PAPER, GOLD, SKIN = (246, 176, 170), (205, 228, 110), (255, 224, 122), (253, 251, 244), (236, 186, 60), (253, 236, 220)

def clamp(x, a=0., b=1.): return max(a, min(b, x))
def seg(t, a, b): return clamp((t - a) / (b - a))
def ease(p): return 4 * p ** 3 if p < .5 else 1 - (-2 * p + 2) ** 3 / 2
def eout(p): return 1 - (1 - p) ** 3
def back(p, c=1.7): return 1 + (c + 1) * (p - 1) ** 3 + c * (p - 1) ** 2

# ------------------------------------------------------------------ static layers
PAGE = M.paper(3)                                     # grid paper, red margin
COVER = Image.open(ROOT / "bg_hi.jpg").convert("RGB")
cw, ch = COVER.size; z = 1.3
COVER = COVER.resize((W, H), Image.LANCZOS, box=(cw / 2 - cw / z / 2, ch * .47 - ch / z / 2, cw / 2 + cw / z / 2, ch * .47 + ch / z / 2)).convert("RGBA")

def sp(segs, size, bold=True, maxw=900): return M.sprite([(t, c) for t, c in segs], size, bold, maxw)
def hl_sprite(segs, size, color, seed, bold=True, maxw=900, alpha=240):
    t = sp(segs, size, bold, maxw); b = M.blob(t.width + 10, t.height - 20, color, seed, alpha)
    im = Image.new("RGBA", (b.width, b.height), (0, 0, 0, 0)); im.alpha_composite(b); im.alpha_composite(t, (20, 10)); return im

def sticky(text):
    t = sp([(text, "ink")], 44); st = Image.new("RGBA", (t.width + 50, t.height + 26), YEL + (250,)); st.alpha_composite(t, (25, 13))
    return st.rotate(2.5, expand=True, resample=Image.BICUBIC)

STICKY = sticky(CFG["sticky"])
HOOK1 = hl_sprite([(CFG["hook1"], "ink")], 74, YEL, 5, maxw=880, alpha=252)
HOOK2 = hl_sprite([(CFG["hook2"], "ink")], 84, (191, 227, 245), 11, maxw=940)
FIX = hl_sprite([("Правильно: ", "green"), (CFG["fix"], "ink")], 64, LIME, 31, maxw=960, alpha=250)
GLOSS = hl_sprite([(CFG["gloss_de"], "orange"), (" = " + CFG["gloss_ua"], "ink")], 62, PAPER, 34, maxw=900)
CTA = hl_sprite([(CFG["cta"], "ink")], 54, YEL, 35, maxw=900, alpha=252)
HEARD = hl_sprite([(CFG["heard"], "red")], 50, PINK, 21, bold=False, maxw=900, alpha=235)

def bubble(lines, size, tail_x, tail_down=True, color="ink"):
    rows = [sp([(l, color)], size, True, 560) for l in lines]
    w = max(r.width for r in rows) + 60; h = sum(r.height for r in rows) + 40
    im = Image.new("RGBA", (w + 20, h + 70), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((8, 8, w + 8, h + 8), 40, fill=PAPER + (250,), outline=INK + (255,), width=6)
    tx = int(clamp(tail_x, .15, .85) * w)
    d.polygon([(tx - 26, h + 4), (tx + 26, h + 4), (tx - 10, h + 62)], fill=PAPER + (250,))
    d.line([(tx - 26, h + 8), (tx - 10, h + 62), (tx + 26, h + 8)], fill=INK + (255,), width=6, joint="curve")
    y = 28
    for r in rows: im.alpha_composite(r, ((w + 16 - r.width) // 2, y)); y += r.height
    return im

B_OKS = bubble([CFG["say1"], CFG["say2"]], 58, .40)
B_KLA = bubble([CFG["klaus1"]], 60, .62)

# ------------------------------------------------------------------ doodle geometry
def circle(cx, cy, r, n=28, start=-1.9, k=1.06):
    return [(cx + math.cos(start + i / n * 2 * math.pi * k) * r, cy + math.sin(start + i / n * 2 * math.pi * k) * r) for i in range(n + 1)]
def arc(cx, cy, rx, ry, a0, a1, n=14):
    return [(cx + math.cos(a0 + (a1 - a0) * i / n) * rx, cy + math.sin(a0 + (a1 - a0) * i / n) * ry) for i in range(n + 1)]
def lerp2(a, b, p): return (a[0] + (b[0] - a[0]) * p, a[1] + (b[1] - a[1]) * p)

def boil(pts, seed, amp=1.8):
    r = np.random.default_rng(seed); return [(x + r.uniform(-amp, amp), y + r.uniform(-amp, amp)) for x, y in pts]

def draw_polys(img, polys, reveal, seed, width=7):
    """polys: list of (pts, stroke_color, fill_color|None). reveal 0..1 draws the first share of total length (pen draw-on)."""
    lens = [sum(math.dist(p[0][i], p[0][i + 1]) for i in range(len(p[0]) - 1)) for p in polys]
    budget = sum(lens) * reveal; d = ImageDraw.Draw(img)
    for (pts, col, fill), L in zip(polys, lens):
        if budget <= 0: break
        pts = boil(pts, seed + len(pts))
        if fill and budget >= L: d.polygon(pts, fill=fill + (255,))
        if budget >= L: d.line(pts, fill=col + (255,), width=width, joint="curve"); budget -= L; continue
        acc, out = 0, [pts[0]]
        for i in range(len(pts) - 1):
            s = math.dist(pts[i], pts[i + 1])
            if acc + s >= budget: out.append(lerp2(pts[i], pts[i + 1], (budget - acc) / max(s, 1e-6))); break
            acc += s; out.append(pts[i + 1])
        if len(out) > 1: d.line(out, fill=col + (255,), width=width, joint="curve")
        budget = 0

def oksana(x, y, t, shock=0., bob=0.):
    """Ukrainian mum: hair curlers, gold hoops, leopard tracksuit, red boxing gloves."""
    y = y - bob; hx, hy = x, y - 360; P = []
    P.append((circle(hx, hy, 72), INK, SKIN))
    for i, a in enumerate((-2.6, -2.0, -1.4, -0.8)):                          # curlers
        P.append((circle(hx + math.cos(a) * 78, hy + math.sin(a) * 74, 20, 14), INK, PINK))
    P.append((circle(hx - 74, hy + 30, 14, 12), GOLD, None)); P.append((circle(hx + 74, hy + 30, 14, 12), GOLD, None))
    blink = (t % 3.1) < .12
    er = 9 + 9 * shock
    for ex in (-26, 26):
        if blink and shock < .5: P.append(([(hx + ex - 12, hy - 8), (hx + ex + 12, hy - 8)], INK, None))
        else: P.append((circle(hx + ex, hy - 8, er, 12), INK, INK if shock < .5 else None))
    if shock > .5: P.append((circle(hx, hy + 36, 16, 14), INK, None))         # "O" mouth
    else: P.append((arc(hx, hy + 22, 28, 18, .25, 2.9), INK, None))
    torso = [(x - 70, y - 285), (x + 70, y - 285), (x + 85, y - 120), (x - 85, y - 120), (x - 70, y - 285)]
    P.append((torso, INK, (232, 196, 140)))
    for (sx, sy) in ((-40, -250), (20, -230), (-10, -180), (45, -165), (-55, -150), (35, -270)):
        P.append((circle(x + sx, y + sy, 8, 8), ORANGE, ORANGE))
    P.append(([(x - 50, y - 120), (x - 60, y)], INK, None)); P.append(([(x + 50, y - 120), (x + 60, y)], INK, None))
    P.append(([(x - 60, y), (x - 100, y)], INK, None)); P.append(([(x + 60, y), (x + 100, y)], INK, None))
    up = .55 * shock + .12 * math.sin(t * 6) * (1 - shock)                         # shadow-boxing jab when calm
    for side in (-1, 1):
        sh = (x + side * 70, y - 270); hand = (x + side * (150 - 40 * up), y - 200 - 160 * up)
        P.append(([sh, lerp2(sh, hand, .5), hand], INK, None)); P.append((circle(hand[0], hand[1], 30, 16), INK, RED))
    return P

def klaus(x, y, t, lift=0.):
    """German official: side-parted hair, round glasses, moustache, shirt and blue tie."""
    hx, hy = x, y - 400; P = []
    P.append((circle(hx, hy, 66), INK, SKIN))
    P.append((arc(hx, hy - 8, 66, 62, math.pi * 1.05, math.pi * 1.95), INK, None))
    P.append(([(hx - 20, hy - 66), (hx - 10, hy - 30)], INK, None))
    for ex in (-26, 26): P.append((circle(hx + ex, hy - 6, 19, 14), INK, None))
    P.append(([(hx - 7, hy - 6), (hx + 7, hy - 6)], INK, None))
    blink = ((t + 1.3) % 2.7) < .12
    for ex in (-26, 26):
        P.append(([(hx + ex - 6, hy - 6), (hx + ex + 6, hy - 6)], INK, None) if blink else (circle(hx + ex, hy - 6, 6, 8), INK, INK))
    P.append((arc(hx - 22, hy + 26, 22, 12, 0, math.pi), INK, None)); P.append((arc(hx + 22, hy + 26, 22, 12, 0, math.pi), INK, None))
    torso = [(x - 75, y - 330), (x + 75, y - 330), (x + 70, y - 130), (x - 70, y - 130), (x - 75, y - 330)]
    P.append((torso, INK, (236, 242, 250)))
    P.append(([(x, y - 330), (x - 16, y - 290), (x, y - 180), (x + 16, y - 290), (x, y - 330)], INK, BLUE))
    P.append(([(x - 45, y - 130), (x - 50, y)], INK, None)); P.append(([(x + 45, y - 130), (x + 50, y)], INK, None))
    P.append(([(x - 50, y), (x - 90, y)], INK, None)); P.append(([(x + 50, y), (x + 90, y)], INK, None))
    for side in (-1, 1):
        sh = (x + side * 75, y - 315)
        rest = (x + side * 120, y - 150); upp = (x + side * 60, y - 560)
        hand = lerp2(rest, upp, ease(lift))
        elbow = lerp2(lerp2(sh, rest, .5), (x + side * 140, y - 420), ease(lift))
        P.append(([sh, elbow, hand], INK, None))
    return P

def kid(x, y):
    P = [(circle(x, y - 150, 34, 20), INK, SKIN)]
    P.append((arc(x, y - 145, 14, 8, .3, 2.8), INK, None))
    for ex in (-12, 12): P.append((circle(x + ex, y - 156, 4, 6), INK, INK))
    P.append(([(x - 34, y - 112), (x + 34, y - 112), (x + 40, y - 40), (x - 40, y - 40), (x - 34, y - 112)], INK, (255, 214, 120)))
    P.append(([(x - 18, y - 40), (x - 20, y)], INK, None)); P.append(([(x + 18, y - 40), (x + 20, y)], INK, None))
    P.append(([(x - 34, y - 100), (x - 70, y - 70)], INK, None)); P.append(([(x + 34, y - 100), (x + 70, y - 70)], INK, None))
    return P

# ------------------------------------------------------------------ timeline
OPEN = (0.9, 1.6); CLOSE = (10.6, 11.4)
DRAW = (1.6, 2.6)
T_OKS = 2.8; T_LIFT = (4.4, 5.2); T_KLA = 5.0; T_SHOCK = 5.9; T_STRIKE = 6.9; T_FIX = 7.3; T_GLOSS = 8.0; T_CTA = 8.7
FLOOR = 1360; OX, KX, KIDX = 330, 770, 560; SCL = 1.25          # characters drawn at 1x, then scaled about (W/2, FLOOR)

def put(frame, im, cx, cy, alpha=1., scale=1.):
    if alpha <= .01: return
    if abs(scale - 1) > .005: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if alpha < .999: im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    frame.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

def pop(frame, im, cx, cy, t0, t, out=None):
    p = seg(t, t0, t0 + .28)
    if p <= 0: return
    a = clamp(p * 3)
    if out: a *= 1 - seg(t, *out)
    put(frame, im, cx, cy, a, .6 + .4 * back(p) if p < 1 else 1)

def cover_layer(frame, t):
    """closed notebook = frame 0; it swings open to the left and closes again for the loop"""
    o = ease(seg(t, *OPEN)) * (1 - ease(seg(t, *CLOSE)))
    if o >= .999: return
    w = int(W * (1 - o))
    if w < 4: return
    cov = COVER.resize((w, H), Image.BICUBIC)
    shade = Image.new("RGBA", cov.size, (0, 0, 0, int(110 * o))); cov.alpha_composite(shade)
    frame.alpha_composite(cov, (0, 0))
    # hook printed on the cover (visible on frame 0)
    if o < .35:
        a = 1 - o / .35
        put(frame, STICKY, 120 + STICKY.width / 2, 330, a)
        put(frame, HOOK1, W / 2, 560, a); put(frame, HOOK2, W / 2, 700, a)
    if o > 0.02:                                                # page edge shadow
        d = ImageDraw.Draw(frame); d.rectangle((w, 0, w + 14, H), fill=(0, 0, 0, int(60 * (1 - o))))

def scene(frame, t):
    seed = int(t * 7)                                           # line boil ~7 fps, like hand-drawn animation
    rev = eout(seg(t, *DRAW))
    shock = ease(seg(t, T_SHOCK, T_SHOCK + .3))
    lift = seg(t, *T_LIFT)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_polys(layer, oksana(OX, FLOOR, t, shock, bob=abs(math.sin(t * 3)) * 8 * (1 - shock)), rev, seed)
    draw_polys(layer, klaus(KX, FLOOR, t, lift), rev, seed + 50)
    kx = KIDX + (KX - KIDX) * ease(lift); ky = FLOOR - 470 * ease(lift)
    draw_polys(layer, kid(kx, ky), rev, seed + 90, 6)
    if shock > .5:
        d = ImageDraw.Draw(layer)
        for i, (dx, dy) in enumerate(((-150, -520), (-110, -560))):
            im = sp([("?!"[i], "red")], 90); layer.alpha_composite(im, (int(OX + dx + i * 230), int(FLOOR + dy)))
    big = layer.resize((int(W * SCL), int(H * SCL)), Image.BICUBIC)
    ox, oy = int(W / 2 * SCL - W / 2), int(FLOOR * SCL - FLOOR)
    frame.alpha_composite(big.crop((ox, oy, ox + W, oy + H)))
    hook_on_page = hl_small
    put(frame, hook_on_page, W / 2, 300, seg(t, 1.5, 1.8) * (1 - seg(t, *CLOSE)))
    pop(frame, B_OKS, 340, 650, T_OKS, t, CLOSE)
    if t >= T_STRIKE:                                           # red scribble over Mum's bubble
        p = seg(t, T_STRIKE, T_STRIKE + .3) * (1 - seg(t, *CLOSE)); d = ImageDraw.Draw(frame)
        x0, x1 = 340 - B_OKS.width / 2 + 40, 340 + B_OKS.width / 2 - 50
        pts = [(x0 + (x1 - x0) * i / 14, 640 + (12 if i % 2 else -12)) for i in range(int(14 * p) + 1)]
        if len(pts) > 1 and p > 0: d.line(pts, fill=RED + (255,), width=9, joint="curve")
    pop(frame, B_KLA, 700, 440, T_KLA, t, (T_FIX - .3, T_FIX))
    pop(frame, HEARD, W / 2, 1470, T_KLA + .4, t, (T_FIX - .3, T_FIX))
    pop(frame, FIX, W / 2, 1470, T_FIX, t, CLOSE)
    pop(frame, GLOSS, W / 2, 1565, T_GLOSS, t, CLOSE)
    pop(frame, CTA, W / 2, 1655, T_CTA, t, CLOSE)

hl_small = hl_sprite([(CFG["hook1"] + " " + CFG["hook2"], "ink")], 52, (191, 227, 245), 12, maxw=900)

GRAIN = [np.random.default_rng(i).normal(0, 3.0, (H, W, 1)).astype(np.float32) for i in range(4)]
def render(t):
    frame = PAGE.copy()
    if t > OPEN[0] - .05: scene(frame, t)
    cover_layer(frame, t)
    out = np.asarray(frame.convert("RGB"), np.float32) + GRAIN[int(t * FPS) % 4]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        (ROOT / "preview").mkdir(exist_ok=True)
        for a in sys.argv[2:]: render(float(a)).save(ROOT / f"preview/v5_{float(a):05.2f}.jpg", quality=90)
        print("ok")
    else:
        FRAMES.mkdir(parents=True, exist_ok=True)
        for i in range(int(DUR * FPS)):
            render(i / FPS).save(FRAMES / f"{i:04d}.jpg", quality=93)
            if i % 90 == 0: print("frame", i, flush=True)
        print("done")
