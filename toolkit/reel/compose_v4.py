"""v4: 9-second relatable situation skit (Ти / Вихователь чує / Правильно). cfg: sticky,label1,q1,q2,label2,h1,h2,fix1,fix2,gloss_de,gloss_ua,cta
python3 compose.py [preview t1 t2 ...]   -> frames/NNNN.jpg (or preview/p_T.jpg)"""
import math, sys, json, os
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent
FRAMES = Path(os.environ.get("FRAMES_DIR", str(ROOT / "frames_v4")))
W, H, FPS, DUR = 1080, 1920, 30, 9.0
FB = str(ROOT / "bg/fonts/ComicRelief-Bold.ttf")
FR = str(ROOT / "bg/fonts/ComicRelief-Regular.ttf")
INK, RED, ORANGE, GREEN, GREY = (27, 35, 51), (214, 69, 69), (232, 132, 50), (62, 154, 58), (74, 88, 120)
BLUE, LIME, YEL = (191, 227, 245), (211, 234, 126), (255, 224, 122)

BG = Image.open(ROOT / "bg_hi.jpg").convert("RGB")
BW, BH = BG.size

# ------------------------------------------------------------------ easing & helpers
def clamp(x, a=0., b=1.): return max(a, min(b, x))
def seg(t, a, b): return clamp((t - a) / (b - a))
def ease(p): return 4 * p ** 3 if p < .5 else 1 - (-2 * p + 2) ** 3 / 2
def ease_out(p): return 1 - (1 - p) ** 3
def back(p, c=1.7): return 1 + (c + 1) * (p - 1) ** 3 + c * (p - 1) ** 2
def lerp(a, b, p): return a + (b - a) * p
_fonts = {}
def font(size, bold=True):
    k = (size, bold)
    if k not in _fonts: _fonts[k] = ImageFont.truetype(FR, size)   # the Bold cut has a broken "ю"; weight comes from a stroke instead
    return _fonts[k]

def text_sprite(segs, size, bold=True, maxw=920):
    """segs: [(text, color)] drawn on one line; shrinks to fit maxw. Returns RGBA + per-segment x spans."""
    while True:
        f = font(size, bold)
        widths = [f.getlength(s) + (round(size * .028) * 2 if bold else 0) / max(1, len(segs)) for s, _ in segs]
        if sum(widths) <= maxw or size < 30: break
        size -= 2
    asc, desc = f.getmetrics()
    w, h = int(math.ceil(sum(widths))) + 16, asc + desc + 16
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x, spans = 8, []
    for (s, col), sw in zip(segs, widths):
        d.text((x, 8), s, font=f, fill=col + (255,), stroke_width=max(1, round(size * .028)) if bold else 0, stroke_fill=col + (255,))
        spans.append((x, x + sw)); x += sw
    return im, spans, asc

def blob(w, h, color, seed=1, alpha=235):
    """marker-highlighter strip with slightly ragged edges"""
    r = np.random.default_rng(seed)
    im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    pts = []
    n = 14
    for i in range(n + 1): pts.append((20 + 18 + (w - 36) * i / n + r.uniform(-3, 3), 20 + r.uniform(-6, 5)))
    for i in range(1, 8):
        a = -math.pi / 2 + i / 8 * math.pi; pts.append((20 + w - 18 + math.cos(a) * 22 + r.uniform(-2, 2), 20 + h / 2 + math.sin(a) * h / 2))
    for i in range(n, -1, -1): pts.append((20 + 18 + (w - 36) * i / n + r.uniform(-3, 3), 20 + h + r.uniform(-5, 6)))
    for i in range(1, 8):
        a = math.pi / 2 + i / 8 * math.pi; pts.append((20 + 18 + math.cos(a) * 22 + r.uniform(-2, 2), 20 + h / 2 + math.sin(a) * h / 2))
    d.polygon(pts, fill=color + (alpha,))
    return im.filter(ImageFilter.GaussianBlur(.8))

def strokes_sprite(polys, w, h, color, width):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for p in polys: d.line(p, fill=color + (255,), width=width, joint="curve")
    for p in polys:
        for (x, y) in (p[0], p[-1]): d.ellipse((x - width / 2, y - width / 2, x + width / 2, y + width / 2), fill=color + (255,))
    return im

# ------------------------------------------------------------------ scene elements
EL = []   # each: dict(img, cx, cy, kind, t0, t1, out0, out1, layer)
def add(img, cx, cy, kind, t0, t1=None, out=None, layer=1, dy_out=-70):
    EL.append(dict(img=img, cx=cx, cy=cy, kind=kind, t0=t0, t1=t1 if t1 is not None else t0 + .3, out=out, layer=layer, dy_out=dy_out))

def line(segs, size, cx, cy, kind, t0, t1=None, out=None, bold=True, strip=None, strip_t=None, seed=1, layer=2, maxw=920, strip_alpha=235):
    im, spans, asc = text_sprite(segs, size, bold, maxw)
    if strip:
        b = blob(im.width + 40, int(size * 1.12), strip, seed, strip_alpha)
        st0, st1 = strip_t if strip_t else (t0 - .08, t0 + .12)
        add(b, cx, cy + size * .06, "swipe", st0, st1, out, layer=1)
    add(im, cx, cy, kind, t0, t1, out, layer)
    return im, spans

def circle_around(w, h, color, width=7, seed=3):
    r = np.random.default_rng(seed); pts = []
    for i in range(49):
        a = -2.3 + i / 48 * math.pi * 2 * 1.07; k = 1 + r.uniform(-.02, .02) + i / 48 * .05
        pts.append((w / 2 + math.cos(a) * (w / 2 - 8) * k, h / 2 + math.sin(a) * (h / 2 - 8) * k))
    return strokes_sprite([pts], w + 20, h + 20, color, width)


CFG = json.load(open(os.environ["CFG"], encoding="utf-8"))
END = (8.3, 8.7)          # everything added later fades here, so the last frame == frame 0 (seamless loop)
PAPER = (250, 248, 240); PINK = (246, 176, 170)
sticky_txt, _, _ = text_sprite([(CFG["sticky"], INK)], 44)
sticky = Image.new("RGBA", (sticky_txt.width + 50, sticky_txt.height + 26), YEL + (250,)); sticky.alpha_composite(sticky_txt, (25, 13))
sticky = sticky.rotate(3, expand=True, resample=Image.BICUBIC)
add(sticky, 100 + sticky.width // 2, 310, "static", 0, out=None, layer=3)
# frame 0 holds the hook: who speaks + the (wrong) phrase
line([(CFG["label1"], INK)], 78, 540, 520, "rise", -1, 0, None, strip=YEL, strip_t=(-1, 0), seed=5, strip_alpha=252)
line([(CFG["q1"], INK)], 104, 540, 690, "rise", -1, 0, None, strip=BLUE, strip_t=(-1, 0), seed=11)
line([(CFG["q2"], INK)], 104, 540, 830, "rise", -1, 0, None, strip=BLUE, strip_t=(-1, 0), seed=12)
# beat 2: what the German actually hears
line([(CFG["label2"], INK)], 70, 540, 1010, "pop", 1.8, 2.05, (4.3, 4.5), strip=PINK, strip_t=(1.75, 1.95), seed=21, strip_alpha=250)
line([(CFG["h1"], RED)], 92, 540, 1150, "pop", 2.4, 2.65, (4.3, 4.5), strip=PAPER, strip_t=(2.35, 2.5), seed=22, strip_alpha=245)
line([(CFG["h2"], RED)], 92, 540, 1280, "pop", 2.9, 3.15, (4.3, 4.5), strip=PAPER, strip_t=(2.85, 3.0), seed=23, strip_alpha=245)
# beat 3: strike the wrong phrase, show the right one
for i, (cy, key) in enumerate(((690, "q1"), (830, "q2"))):
    im, _, _ = text_sprite([(CFG[key], INK)], 104, True, 920)
    sw = im.width
    strike = strokes_sprite([[(10 + j * (sw - 20) / 14, 40 + (10 if j % 2 else -10)) for j in range(15)]], sw + 20, 80, RED, 9)
    add(strike, 540, cy + 8, "draw", 4.2 + i * .12, 4.5 + i * .12, END, layer=3)
line([("Правильно:", INK)], 70, 540, 1010, "pop", 4.7, 4.95, END, strip=LIME, strip_t=(4.65, 4.85), seed=31, strip_alpha=250)
line([(CFG["fix1"], INK)], 92, 540, 1150, "pop", 5.0, 5.25, END, strip=LIME, strip_t=(4.95, 5.15), seed=32, strip_alpha=250)
if CFG.get("fix2"):
    line([(CFG["fix2"], INK)], 96, 540, 1280, "pop", 5.2, 5.45, END, strip=LIME, strip_t=(5.15, 5.35), seed=33, strip_alpha=250)
check = strokes_sprite([[(10, 60), (45, 100), (120, 12)]], 130, 115, GREEN, 14)
add(check, 880, 1000, "draw", 5.5, 5.7, END, layer=4)
line([(CFG["gloss_de"], ORANGE), (" = " + CFG["gloss_ua"], INK)], 64, 540, 1440, "pop", 6.0, 6.25, END, strip=PAPER, strip_t=(5.95, 6.1), seed=34, strip_alpha=245, maxw=960)
line([(CFG["cta"], INK)], 56, 540, 1570, "pop", 6.9, 7.15, END, strip=YEL, strip_t=(6.85, 7.0), seed=35, strip_alpha=252, maxw=900)
# ------------------------------------------------------------------ atmosphere layers
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = (1 - .38 * np.clip(((xx - W / 2) / (W * .75)) ** 2 + ((yy - H * .46) / (H * .62)) ** 2, 0, 1) ** 1.3)[..., None]
LEAK = np.clip(1 - np.hypot(xx + 120, yy - 260) / 1250, 0, 1) ** 2
LEAK = (LEAK[..., None] * np.array([255, 196, 130], np.float32)[None, None, :])
GRAIN = [np.random.default_rng(i).normal(0, 3.2, (H, W, 1)).astype(np.float32) for i in range(6)]
rd = np.random.default_rng(7)
DUST = [dict(x=rd.uniform(0, W), y=rd.uniform(0, H), vy=-rd.uniform(8, 26), vx=rd.uniform(-6, 6), s=rd.uniform(1.6, 5.2), a=rd.uniform(.18, .5), ph=rd.uniform(0, 6.3)) for _ in range(48)]
DOT = {}
def dot(s):
    k = round(s * 2) / 2
    if k not in DOT:
        n = int(k * 6) + 4; im = Image.new("L", (n, n), 0); ImageDraw.Draw(im).ellipse((n / 2 - k, n / 2 - k, n / 2 + k, n / 2 + k), fill=255)
        DOT[k] = im.filter(ImageFilter.GaussianBlur(k * .7))
    return DOT[k]

ZK = [(0, 1.30), (4.4, 1.38), (8.3, 1.42), (9.0, 1.30)]
def zoom(t):
    for (ta, za), (tb, zb) in zip(ZK, ZK[1:]):
        if t <= tb: return lerp(za, zb, ease(seg(t, ta, tb)))
    return ZK[-1][1]

def background(t):
    z = zoom(t)
    cw, ch = BW / z, BH / z
    cx = BW / 2 + math.sin(t * .35) * 18; cy = BH * .47 + math.cos(t * .3) * 14
    cx = min(max(cx, cw / 2), BW - cw / 2); cy = min(max(cy, ch / 2), BH - ch / 2)
    box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
    return BG.resize((W, H), Image.LANCZOS, box=box)

def place(frame, img, cx, cy, alpha=1., scale=1., dy=0., clip=None):
    if alpha <= 0.01: return
    im = img
    if clip is not None:
        im = im.copy(); w = int(im.width * clip)
        if w <= 0: return
        mask = Image.new("L", im.size, 0); ImageDraw.Draw(mask).rectangle((0, 0, w, im.height), fill=255)
        a = im.getchannel("A"); im.putalpha(Image.fromarray(np.minimum(np.array(a), np.array(mask))))
    if abs(scale - 1) > .005:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if alpha < .999:
        a = im.getchannel("A").point(lambda v: int(v * alpha)); im = im.copy(); im.putalpha(a)
    frame.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2 + dy)))

def draw_elements(frame, t):
    for e in sorted(EL, key=lambda e: e["layer"]):
        k, t0, t1 = e["kind"], e["t0"], e["t1"]
        if k != "static" and t < t0 - 1e-6 and k not in ("rise",): continue
        alpha, scale, dy, clip = 1., 1., 0., None
        p = seg(t, t0, t1)
        if k == "pop": scale = .6 + .4 * back(p) if p < 1 else 1; alpha = clamp(p * 3)
        elif k == "fade": alpha = ease_out(p); dy = (1 - ease_out(p)) * 24
        elif k in ("type", "draw", "swipe"): clip = ease_out(p) if k == "swipe" else p; alpha = 1 if p > 0 else 0
        elif k == "rise": scale = 1 + .04 * (1 - ease_out(seg(t, 0, .45)))   # present on frame 0, settles
        elif k == "loopin": alpha = ease_out(p); scale = 1 + .04 * (1 - ease_out(p))
        if e["out"]:
            q = seg(t, *e["out"])
            if q >= 1: continue
            alpha *= 1 - q; dy += e["dy_out"] * ease(q)
        
        place(frame, e["img"], e["cx"], e["cy"], alpha, scale, dy, clip if (clip is not None and clip < .999) else None)

def countdown(frame, t):
    p = seg(t, *COUNT)
    if p <= 0 or t > OUT2[1]: return
    fade = 1 - seg(t, *OUT2)
    d = ImageDraw.Draw(frame); cx, cy, r = 540, 1385, 62
    d.ellipse((cx - r - 16, cy - r - 16, cx + r + 16, cy + r + 16), fill=(250, 248, 240, int(235 * fade)))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(27, 35, 51, int(50 * fade)), width=12)
    end = -90 + 360 * p
    d.arc((cx - r, cy - r, cx + r, cy + r), -90, end, fill=(47, 111, 214, int(255 * fade)), width=13)
    n = "3" if p < 1 / 3 else "2" if p < 2 / 3 else "1"
    local = (p * 3) % 1; s = 1 + .3 * (1 - ease_out(min(1, local * 4)))
    im, _, _ = text_sprite([(n, INK)], 96)
    place(frame, im, cx, cy - 6, fade, s)

def dust(frame, t):
    layer = Image.new("L", (W, H), 0)
    for q in DUST:
        x = (q["x"] + q["vx"] * t + math.sin(t * .9 + q["ph"]) * 14) % W
        y = (q["y"] + q["vy"] * t) % H
        tw = .6 + .4 * math.sin(t * 1.7 + q["ph"] * 2)
        d = dot(q["s"]); layer.paste(Image.eval(d, lambda v, a=q["a"] * tw: int(v * a)), (int(x), int(y)), Image.eval(d, lambda v, a=q["a"] * tw: int(v * a)))
    warm = Image.new("RGBA", (W, H), (255, 236, 205, 0)); warm.putalpha(layer)
    frame.alpha_composite(warm)

def render(t):
    bg = background(t)
    arr = np.asarray(bg, np.float32)
    leak = .16 + .04 * math.sin(t * .8)
    arr = arr + (255 - arr) * (LEAK / 255) * leak          # screen-like warm light leak
    arr = arr * VIG
    frame = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    dust(frame, t)
    draw_elements(frame, t)
    out = np.asarray(frame.convert("RGB"), np.float32) + GRAIN[int(t * FPS) % len(GRAIN)]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        (ROOT / "preview").mkdir(exist_ok=True)
        for a in sys.argv[2:]:
            render(float(a)).save(ROOT / f"preview/v4_{float(a):05.2f}.jpg", quality=90)
        print("ok")
    else:
        FRAMES.mkdir(parents=True, exist_ok=True)
        for i in range(int(DUR * FPS)):
            render(i / FPS).save(FRAMES / f"{i:04d}.jpg", quality=93)
            if i % 60 == 0: print("frame", i, flush=True)
        print("done")
