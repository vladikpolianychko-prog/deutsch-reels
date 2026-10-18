"""v6: "night sketchbook" — a terracotta spiral sketchbook on a dark desk under a warm lamp; the cover flips up and
cartoon characters (Oksana, Klaus, a kid) act out a situation.  Everything is new vs v1-v5: fonts (Inter Display + Lora
Italic), colours, paper (dot grid), characters (cel-shaded, 2x supersampled, rigged limbs), music (music_v6.py).
cfg: series, hook_ua, hook_de, say (list of lines), klaus (list of lines), heard, fix, gloss_de, gloss_ua, cta
python3 compose_v6.py [preview t1 t2 ...]"""
import math, sys, json, os
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent
W, H, FPS, DUR = 1080, 1920, 30, 16.0
CFG = json.load(open(os.environ["CFG"], encoding="utf-8"))
FRAMES = Path(os.environ.get("FRAMES_DIR", str(ROOT / "frames_v6")))

# ------------------------------------------------------------------ palette & fonts
OUT = (31, 36, 58); CREAM = (251, 248, 241); CORAL = (255, 107, 91); MINT = (61, 196, 160); SUN = (255, 201, 60)
SKY = (90, 169, 230); NAVY = (24, 33, 56); TERRA = (190, 84, 58); WHITE = (255, 255, 255)
SKIN, SKIN_SH = (255, 219, 190), (236, 184, 150)
FD = "/usr/share/fonts/opentype/inter/"
_fc = {}
def font(kind, size):
    k = (kind, size)
    if k in _fc: return _fc[k]
    if kind == "de":
        f = ImageFont.truetype("/usr/share/fonts/truetype/google-fonts/Lora-Italic-Variable.ttf", size)
        f.set_variation_by_axes([700])
    else:
        f = ImageFont.truetype(FD + {"black": "InterDisplay-Black.otf", "bold": "InterDisplay-Bold.otf", "semi": "InterDisplay-SemiBold.otf"}[kind], size)
    _fc[k] = f; return f

def clamp(x, a=0., b=1.): return max(a, min(b, x))
def seg(t, a, b): return clamp((t - a) / (b - a))
def ease(p): return 4 * p ** 3 if p < .5 else 1 - (-2 * p + 2) ** 3 / 2
def eout(p): return 1 - (1 - p) ** 3
def back(p, c=1.9): return 1 + (c + 1) * (p - 1) ** 3 + c * (p - 1) ** 2
def lerp(a, b, p): return a + (b - a) * p

# ------------------------------------------------------------------ text sprites
def line_sprite(segs, maxw):
    """segs: [(text, kind, size, color)] on one line; scales all sizes down together until it fits maxw"""
    k = 1.0
    while True:
        fs = [font(kd, max(18, int(sz * k))) for _, kd, sz, _ in segs]
        ws = [f.getlength(t) for (t, *_), f in zip(segs, fs)]
        if sum(ws) <= maxw or k < .5: break
        k -= .03
    asc = max(f.getmetrics()[0] for f in fs); desc = max(f.getmetrics()[1] for f in fs)
    im = Image.new("RGBA", (int(sum(ws)) + 8, asc + desc + 8), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 4
    for (t, kd, sz, col), f, w in zip(segs, fs, ws):
        d.text((x, 4 + asc - f.getmetrics()[0]), t, font=f, fill=col + (255,)); x += w
    return im

def shadow_of(im, blur=14, alpha=110, dy=10):
    a = im.getchannel("A").filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * alpha / 255))
    sh = Image.new("RGBA", im.size, OUT + (0,)); sh.putalpha(a)
    out = Image.new("RGBA", (im.width, im.height + dy), (0, 0, 0, 0)); out.alpha_composite(sh, (0, dy)); out.alpha_composite(im, (0, 0)); return out

def card(rows, fill, pad=(44, 30), radius=36, border=None, maxw=940, gap=6):
    """rows: list of segs lists -> rounded card sprite with soft shadow"""
    sps = [line_sprite(r, maxw - 2 * pad[0]) for r in rows]
    w = max(s.width for s in sps) + 2 * pad[0]; h = sum(s.height for s in sps) + gap * (len(sps) - 1) + 2 * pad[1]
    im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, 20 + w, 20 + h), radius, fill=fill + (255,), outline=(border + (255,)) if border else None, width=6 if border else 0)
    y = 20 + pad[1]
    for s in sps: im.alpha_composite(s, (20 + (w - s.width) // 2, y)); y += s.height + gap
    return shadow_of(im)

def bubble(rows, tail_frac, maxw=600):
    sps = [line_sprite(r, maxw - 70) for r in rows]
    w = max(s.width for s in sps) + 70; h = sum(s.height for s in sps) + 46
    im = Image.new("RGBA", (w + 40, h + 100), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    tx = 20 + int(clamp(tail_frac, .18, .82) * w)
    d.polygon([(tx - 34, 20 + h - 12), (tx + 30, 20 + h - 12), (tx - 22, 20 + h + 64)], fill=WHITE + (255,), outline=OUT + (255,), width=7)
    d.rounded_rectangle((20, 20, 20 + w, 20 + h), 44, fill=WHITE + (255,), outline=OUT + (255,), width=7)
    d.polygon([(tx - 26, 20 + h - 16), (tx + 22, 20 + h - 16), (tx - 18, 20 + h + 50)], fill=WHITE + (255,))
    y = 20 + 23
    for s in sps: im.alpha_composite(s, (20 + (w - s.width) // 2, y)); y += s.height
    return shadow_of(im, 12, 90, 8)

DE = lambda t, sz=68, c=OUT: (t, "de", sz, c)
UA = lambda t, sz=60, c=OUT, k="black": (t, k, sz, c)

SERIES = card([[UA(CFG["series"], 40, WHITE, "bold")]], NAVY, pad=(30, 16), radius=28)
HOOK_UA = line_sprite([UA(CFG["hook_ua"], 100, WHITE)], 940)
HOOK_DE = card([[DE(l, 84)] for l in (CFG.get("hook_de_lines") or [CFG["hook_de"]])], CREAM, pad=(44, 30), radius=30, maxw=960)
BF = CFG.get("bubble_font", 70)
B_OKS = bubble([[DE(l, BF)] for l in CFG["say"]], .45, 620)
_rh = B_OKS.height - 100 - 8; OKS_ROWS = [480 - B_OKS.height / 2 + 20 + 23 + (k + .55) * (_rh - 46) / len(CFG["say"]) for k in range(len(CFG["say"]))]
B_KLA = bubble([[DE(l, BF)] for l in CFG["klaus"]], .62, 640)
HEARD = card([[UA(CFG.get("heard_label", "Він почув:"), 50, CORAL, "bold")], [UA(CFG["heard"], 66, OUT)]], CREAM, border=CORAL, maxw=980)
FIX = card([[UA("ПРАВИЛЬНО", 44, WHITE, "black")], [DE(CFG["fix"], 92, WHITE)], [UA(CFG["gloss_de"], 62, SUN, "black"), UA(" = " + CFG["gloss_ua"], 62, WHITE, "bold")]], (35, 150, 118), pad=(46, 30), maxw=1000, gap=10)
CTA = card([[UA(CFG["cta"], 66, OUT)]], SUN, pad=(44, 28), maxw=1000)
QM = line_sprite([UA("?!", 150, CORAL)], 400)

# ------------------------------------------------------------------ static backdrop: desk + lamp + sketchbook page
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
def backdrop():
    r = np.random.default_rng(3)
    desk = np.zeros((H, W, 3), np.float32); desk[:] = (30, 42, 66)
    grain = (np.sin(xx * .045 + np.sin(yy * .004) * 3) * 6 + r.normal(0, 3, (H, W)))[..., None]
    desk += grain
    lamp = np.clip(1 - np.hypot(xx - W * .85, yy + 120) / 1500, 0, 1)[..., None] ** 1.6
    desk = desk * (1 + 1.6 * lamp) + np.array([70, 45, 10]) * lamp
    img = Image.fromarray(np.clip(desk, 0, 255).astype(np.uint8)).convert("RGBA")
    # page with shadow
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((52, 150, W - 28, H - 40), 26, fill=(0, 0, 0, 150))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(22)))
    page = np.zeros((H, W, 3), np.float32); page[:] = CREAM
    page += r.normal(0, 2.2, (H, W, 1))
    page *= (1 - .10 * np.clip(((xx - W * .8) / W) ** 2 + ((yy + 100) / (H * 1.2)) ** 2, 0, 1))[..., None]
    pim = Image.fromarray(np.clip(page, 0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(pim)
    for y in range(230, H - 60, 46):
        for x in range(86, W - 50, 46): d.ellipse((x - 2.6, y - 2.6, x + 2.6, y + 2.6), fill=(176, 186, 205, 255))
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rounded_rectangle((40, 140, W - 40, H - 52), 26, fill=255)
    img.paste(pim, (0, 0), m)
    return img

BASE = backdrop()

def spiral(img):
    d = ImageDraw.Draw(img)
    for x in range(92, W - 60, 52):
        d.ellipse((x - 12, 128, x + 12, 152), fill=(20, 26, 44, 255))
        d.rounded_rectangle((x - 7, 96, x + 7, 150), 7, fill=(150, 158, 175, 255), outline=(70, 78, 98, 255), width=3)
        d.line((x - 2, 102, x - 2, 140), fill=(230, 234, 242, 255), width=3)

# ------------------------------------------------------------------ cover (terracotta hard cover, elastic band, label)
def make_cover():
    r = np.random.default_rng(5)
    a = np.zeros((H - 192, W - 80, 3), np.float32); a[:] = TERRA
    hh, ww = a.shape[:2]; y2, x2 = np.mgrid[0:hh, 0:ww].astype(np.float32)
    a += (np.sin(x2 * 1.3) * 3 + np.sin(y2 * 1.1) * 3 + r.normal(0, 4, (hh, ww)))[..., None]       # linen weave
    a *= (1 + .35 * np.clip(1 - np.hypot(x2 - ww * .85, y2 + 100) / 1400, 0, 1) ** 1.5)[..., None]
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, ww - 1, hh - 1), 26, fill=255); im.putalpha(m)
    d = ImageDraw.Draw(im)
    d.rectangle((ww - 120, 0, ww - 92, hh), fill=(40, 30, 32, 255))                                  # elastic band
    s = SERIES; im.alpha_composite(s, (40, 70))
    hy = 470
    hu = shadow_of(HOOK_UA, 10, 120, 6); im.alpha_composite(hu, ((ww - hu.width) // 2, hy))
    im.alpha_composite(HOOK_DE, ((ww - HOOK_DE.width) // 2, hy + hu.height + 20))
    tip = line_sprite([UA("А що почув німець?", 62, (255, 226, 200), "bold")], 900)
    im.alpha_composite(tip, ((ww - tip.width) // 2, hy + hu.height + HOOK_DE.height + 50))
    return im

COVER = make_cover(); COVER_BACK = Image.new("RGBA", COVER.size, (150, 66, 46, 255)); COVER_BACK.putalpha(COVER.getchannel("A"))

def draw_cover(frame, o):
    """o = 0 closed ... 1 flipped up around the top spiral"""
    if o >= .999: return
    hcov = COVER.height; ang = o * math.pi
    sc = math.cos(ang)
    if sc > 0.01:
        h = max(2, int(hcov * sc)); c = COVER.resize((COVER.width, h), Image.BICUBIC)
        shade = Image.new("RGBA", c.size, (0, 0, 0, int(150 * (1 - sc)))); shade.putalpha(Image.eval(c.getchannel("A"), lambda v: int(v * (1 - sc) * .6)))
        c.alpha_composite(shade); frame.alpha_composite(c, (40, 140))
    elif sc < -0.01:
        h = max(2, int(hcov * -sc * .18)); c = COVER_BACK.resize((COVER.width, h), Image.BICUBIC); frame.alpha_composite(c, (40, 140 - h))

# ------------------------------------------------------------------ 2x supersampled character layer
S = 2; RX0, RY0, RW, RH = 0, 260, W, 1180
def P(x, y): return ((x - RX0) * S, (y - RY0) * S)

class Pen:
    def __init__(self, d): self.d = d
    def ell(self, cx, cy, rx, ry, fill, w=6, ol=OUT):
        d = self.d
        if w: d.ellipse([*P(cx - rx - w, cy - ry - w), *P(cx + rx + w, cy + ry + w)], fill=ol + (255,))
        d.ellipse([*P(cx - rx, cy - ry), *P(cx + rx, cy + ry)], fill=fill + (255,))
    def shaded_ell(self, cx, cy, rx, ry, fill, shade, w=6):
        self.ell(cx, cy, rx, ry, shade, w)
        self.d.ellipse([*P(cx - rx * .92 - 5, cy - ry * .92 - 6), *P(cx + rx * .86 - 5, cy + ry * .86 - 6)], fill=fill + (255,))
    def poly(self, pts, fill, w=6):
        self.d.polygon([P(*p) for p in pts], fill=fill + (255,), outline=OUT + (255,), width=w * S)
    def cap(self, a, b, r, fill, w=6):
        d = self.d
        for rr, col in ((r + w, OUT), (r, fill)):
            d.line([P(*a), P(*b)], fill=col + (255,), width=int(rr * 2 * S))
            for (x, y) in (a, b): d.ellipse([*P(x - rr, y - rr), *P(x + rr, y + rr)], fill=col + (255,))
    def line(self, pts, col=OUT, w=6): self.d.line([P(*p) for p in pts], fill=col + (255,), width=w * S, joint="curve")
    def arc(self, cx, cy, rx, ry, a0, a1, col=OUT, w=6, n=16):
        self.line([(cx + math.cos(a0 + (a1 - a0) * i / n) * rx, cy + math.sin(a0 + (a1 - a0) * i / n) * ry) for i in range(n + 1)], col, w)

def limb(sh, a1, l1, a2, l2):
    el = (sh[0] + math.cos(a1) * l1, sh[1] + math.sin(a1) * l1)
    return el, (el[0] + math.cos(a1 + a2) * l2, el[1] + math.sin(a1 + a2) * l2)

LEO, LEO_SH, LEO_SP = (236, 186, 106), (214, 160, 84), (92, 58, 30)
def oksana(pen, x, y, t, st):
    """st: talk 0..1, shock 0..1, blink 0..1, jab (L,R) 0..1, guard 0..1, lookx"""
    br = math.sin(t * 2.4) * 3; y -= st.get("jump", 0)
    # shadow
    pen.d.ellipse([*P(x - 110, y - 14), *P(x + 110, y + 14)], fill=(0, 0, 0, 40))
    for sx in (-1, 1):                                                    # legs + sneakers
        pen.cap((x + sx * 34, y - 210), (x + sx * 40, y - 40), 26, LEO)
        pen.ell(x + sx * 52, y - 20, 46, 22, WHITE); pen.line([(x + sx * 30, y - 24), (x + sx * 74, y - 24)], (210, 214, 225), 4)
    top = y - 420 + br
    pen.poly([(x - 86, top + 20), (x + 86, top + 20), (x + 104, y - 190), (x - 104, y - 190)], LEO)
    pen.d.polygon([P(x + 30, top + 24), P(x + 86, top + 24), P(x + 100, y - 196), P(x + 50, y - 196)], fill=LEO_SH + (255,))
    for (sx, sy, rr) in ((-50, 80, 12), (20, 60, 10), (-20, 140, 13), (55, 130, 11), (-62, 180, 10), (10, 190, 12), (60, 200, 9), (-30, 30, 9)):
        pen.ell(x + sx, top + sy, rr, rr * .8, LEO_SH, 0); pen.arc(x + sx, top + sy, rr, rr * .8, .3, 4.4, LEO_SP, 4)
    pen.line([(x, top + 26), (x, y - 196)], WHITE, 5)
    pen.d.rectangle([*P(x - 104, y - 206), *P(x + 104, y - 190)], fill=(196, 140, 70, 255))
    hx, hy = x + st.get("tilt", 0) * 10, top - 92
    pen.cap((x, top + 20), (x, top - 20), 24, SKIN)                       # neck
    # arms (behind gloves); shoulder angles
    for side, jab in ((-1, st.get("jabL", 0)), (1, st.get("jabR", 0))):
        sh = (x + side * 86, top + 40)
        guard = st.get("guard", 0)
        a1 = math.pi / 2 + side * (-.55) ; a2 = side * -1.2
        a1 = lerp(a1, math.pi / 2 - side * (math.pi / 2 + .9) * 0 + (-math.pi / 2 if False else 0), 0) if False else a1
        # rest: hands at hips; guard: gloves near cheeks; jab: arm forward (towards +x for right)
        rest = (math.pi / 2 - side * .35, -side * .9 * -1)
        g = (-math.pi / 2 - side * 1.0, side * -2.3) if side < 0 else (-math.pi / 2 + 1.0, -2.3 * 1)
        g = ((-math.pi / 2 - .9) if side < 0 else (-math.pi / 2 + .9), (2.4 if side < 0 else -2.4))
        j = ((math.pi + .15) if side < 0 else -.15, 0.0)
        r_a1, r_a2 = (math.pi / 2 + .45, -.6) if side < 0 else (math.pi / 2 - .45, .6)
        A1 = lerp(lerp(r_a1, g[0], guard), j[0], jab); A2 = lerp(lerp(r_a2, g[1], guard), j[1], jab)
        el, hand = limb(sh, A1, 92, A2, 84)
        pen.cap(sh, el, 22, LEO); pen.cap(el, hand, 20, LEO)
        pen.d.rectangle([*P(hand[0] - 22, hand[1] - 22), *P(hand[0] + 22, hand[1] - 8)], fill=(200, 140, 70, 255))   # sleeve cuff
        pen.shaded_ell(hand[0], hand[1] + 6, 20, 22, SKIN, SKIN_SH, 5)
        pen.ell(hand[0] - side * 16, hand[1] + 2, 8, 12, SKIN, 4)                                             # thumb
    # hair back, head, hair front, curlers
    pen.ell(hx, hy - 6, 112, 104, (250, 222, 150))
    for ex in (-1, 1): pen.ell(hx + ex * 84, hy + 10, 18, 22, SKIN)
    pen.shaded_ell(hx, hy + 6, 86, 92, SKIN, SKIN_SH)
    pen.d.polygon([P(hx - 98, hy - 20), P(hx - 70, hy - 92), P(hx, hy - 104), P(hx + 72, hy - 92), P(hx + 98, hy - 20), P(hx + 60, hy - 52), P(hx + 10, hy - 40), P(hx - 40, hy - 56)], fill=(250, 222, 150, 255), outline=OUT + (255,), width=6 * S)
    for i, a in enumerate((-2.55, -2.05, -1.55, -1.05, -.55)):
        cx, cy = hx + math.cos(a) * 104, hy - 10 + math.sin(a) * 100
        pen.cap((cx - 14, cy + 3), (cx + 14, cy - 3), 17, (255, 150, 190), 5)
        pen.line([(cx - 4, cy - 14), (cx - 2, cy + 14)], (230, 100, 150), 4)
    # earrings swing
    sw = math.sin(t * 5) * 6
    for ex in (-1, 1): pen.d.ellipse([*P(hx + ex * 88 - 22 + sw, hy + 30), *P(hx + ex * 88 + 22 + sw, hy + 74)], outline=(222, 170, 40, 255), width=8 * S)
    # face
    shock = st.get("shock", 0); lx = st.get("lookx", 4)
    for ex in (-1, 1):
        ex0 = hx + ex * 32; ey = hy - 4
        ry = 24 + 10 * shock
        pen.ell(ex0, ey, 20 + 4 * shock, ry, WHITE, 5)
        pen.ell(ex0 + lx, ey + 4, 11, 13, (60, 90, 150), 0); pen.ell(ex0 + lx, ey + 4, 6, 7, (20, 24, 40), 0)
        pen.ell(ex0 + lx - 4, ey - 2, 4, 4, WHITE, 0)
        b = st.get("blink", 0)
        if b > 0: pen.d.rectangle([*P(ex0 - 26, ey - ry - 6), *P(ex0 + 26, ey - ry - 6 + (2 * ry + 8) * b)], fill=SKIN + (255,)); pen.line([(ex0 - 22, ey - ry - 6 + (2 * ry + 8) * b), (ex0 + 22, ey - ry - 6 + (2 * ry + 8) * b)], OUT, 5)
        by = ey - 40 - 16 * shock
        pen.line([(ex0 - 20, by + 6 - ex * 0), (ex0, by - 4), (ex0 + 20, by + 4)], OUT, 7)
        pen.ell(ex0 + ex * 14, hy + 40, 18, 10, (255, 170, 160), 0)
    pen.arc(hx + 2, hy + 24, 8, 6, .2, 2.9, SKIN_SH, 5)
    talk = st.get("talk", 0)
    if shock > .5: pen.ell(hx, hy + 60, 18, 26, (150, 30, 50), 6)
    elif talk > .05:
        pen.ell(hx, hy + 56, 26, 6 + 16 * talk, (150, 30, 50), 6); pen.ell(hx, hy + 60 + 8 * talk, 12, 5 * talk + 1, (240, 110, 120), 0)
    else: pen.arc(hx, hy + 46, 28, 16, .25, 2.9, (200, 50, 70), 7)

KL_HAIR, SHIRT, SHIRT_SH, TROU = (120, 78, 50), (182, 218, 242), (150, 190, 222), (84, 92, 112)
def klaus(pen, x, y, t, st):
    br = math.sin(t * 2.1 + 1) * 3; sq = st.get("squat", 0) * 18
    pen.d.ellipse([*P(x - 105, y - 14), *P(x + 105, y + 14)], fill=(0, 0, 0, 40))
    for sx in (-1, 1):
        pen.cap((x + sx * 32, y - 240 + sq), (x + sx * 36, y - 40), 26, TROU)
        pen.ell(x + sx * 50, y - 20, 44, 20, (70, 46, 34))
    top = y - 500 + br + sq
    pen.poly([(x - 88, top + 22), (x + 88, top + 22), (x + 80, y - 228 + sq), (x - 80, y - 228 + sq)], SHIRT)
    pen.d.polygon([P(x + 32, top + 26), P(x + 86, top + 26), P(x + 78, y - 232 + sq), P(x + 46, y - 232 + sq)], fill=SHIRT_SH + (255,))
    pen.d.rectangle([*P(x - 80, y - 250 + sq), *P(x + 80, y - 228 + sq)], fill=(60, 44, 36, 255)); pen.d.rectangle([*P(x - 14, y - 252 + sq), *P(x + 14, y - 226 + sq)], fill=(210, 180, 90, 255))
    pen.poly([(x, top + 30), (x - 18, top + 70), (x, top + 200), (x + 18, top + 70)], NAVY, 5)
    pen.poly([(x - 40, top + 18), (x, top + 34), (x - 30, top + 56)], WHITE, 5); pen.poly([(x + 40, top + 18), (x, top + 34), (x + 30, top + 56)], WHITE, 5)
    pen.line([(x - 36, top + 30), (x + 40, top + 150), (x + 36, top + 30)], CORAL, 5)                   # lanyard
    pen.d.rounded_rectangle([*P(x + 18, top + 146), *P(x + 72, top + 214)], 6 * S, fill=WHITE + (255,), outline=OUT + (255,), width=4 * S)
    pen.d.rectangle([*P(x + 24, top + 152), *P(x + 66, top + 166)], fill=MINT + (255,))
    lift = st.get("lift", 0)
    for side in (-1, 1):
        sh = (x + side * 88, top + 40)
        r_a1, r_a2 = (math.pi / 2 + .25, -.35) if side < 0 else (math.pi / 2 - .25, .35)
        u_a1, u_a2 = (-math.pi / 2 - .32, .42) if side < 0 else (-math.pi / 2 + .32, -.42)
        A1, A2 = lerp(r_a1, u_a1, lift), lerp(r_a2, u_a2, lift)
        el, hand = limb(sh, A1, 96, A2, 88)
        pen.cap(sh, el, 22, SHIRT); pen.cap(el, hand, 20, SHIRT); pen.shaded_ell(hand[0], hand[1], 20, 20, SKIN, SKIN_SH, 5)
        st.setdefault("hands", []).append(hand)
    hx, hy = x, top - 96
    pen.cap((x, top + 20), (x, top - 20), 24, SKIN)
    for ex in (-1, 1): pen.ell(hx + ex * 76, hy + 8, 16, 22, SKIN)
    pen.shaded_ell(hx, hy, 76, 90, SKIN, SKIN_SH)
    pen.d.polygon([P(hx - 80, hy - 20), P(hx - 70, hy - 80), P(hx - 10, hy - 104), P(hx + 60, hy - 92), P(hx + 82, hy - 30), P(hx + 60, hy - 60), P(hx - 30, hy - 66), P(hx - 66, hy - 36)], fill=KL_HAIR + (255,), outline=OUT + (255,), width=6 * S)
    pen.line([(hx - 30, hy - 66), (hx - 14, hy - 100)], OUT, 4)
    b = st.get("blink", 0); talk = st.get("talk", 0)
    for ex in (-1, 1):
        ex0, ey = hx + ex * 30, hy - 6
        pen.d.ellipse([*P(ex0 - 27, ey - 27), *P(ex0 + 27, ey + 27)], fill=(235, 246, 255, 255), outline=OUT + (255,), width=6 * S)
        if b < .5: pen.ell(ex0 + 3, ey + 2, 8, 9, (20, 24, 40), 0); pen.ell(ex0, ey - 2, 3, 3, WHITE, 0)
        else: pen.line([(ex0 - 12, ey + 2), (ex0 + 12, ey + 2)], OUT, 5)
        pen.line([(ex0 - 14, ey - 18), (ex0 + 2, ey - 22)], WHITE, 4)
        pen.line([(ex0 - 22, ey - 44 - 6 * st.get("brow", 0)), (ex0 + 22, ey - 40 - 6 * st.get("brow", 0))], KL_HAIR, 9)
    pen.line([(hx - 3, hy - 6), (hx + 3, hy - 6)], OUT, 5)
    mo = 6 + 14 * talk
    if talk > .05: pen.ell(hx, hy + 58, 18, mo * .7, (150, 30, 50), 5)
    else: pen.arc(hx, hy + 54, 16, 8, .3, 2.8, OUT, 5)
    pen.d.polygon([P(hx - 4, hy + 26), P(hx - 40, hy + 30), P(hx - 66, hy + 18), P(hx - 52, hy + 48), P(hx - 10, hy + 46), P(hx, hy + 38), P(hx + 10, hy + 46), P(hx + 52, hy + 48), P(hx + 66, hy + 18), P(hx + 40, hy + 30), P(hx + 4, hy + 26)], fill=(110, 70, 44, 255), outline=OUT + (255,), width=5 * S)

def kid(pen, x, y, t, st):
    kick = st.get("kick", 0)
    if st.get("ground", True): pen.d.ellipse([*P(x - 60, y - 9), *P(x + 60, y + 9)], fill=(0, 0, 0, 40))
    for sx in (-1, 1):
        a = math.pi / 2 + sx * (.15 + kick * .5 * math.sin(t * 16 + sx))
        knee = (x + sx * 18 + math.cos(a) * 36, y - 80 + math.sin(a) * 36)
        pen.cap((x + sx * 18, y - 86), knee, 14, (90, 120, 200)); pen.ell(knee[0] + sx * 6, knee[1] + 14, 20, 12, CORAL, 5)
    pen.poly([(x - 46, y - 190), (x + 46, y - 190), (x + 58, y - 80), (x - 58, y - 80)], SUN)
    pen.line([(x, y - 186), (x, y - 86)], (225, 160, 30), 4)
    up = st.get("armsup", .7)
    for side in (-1, 1):
        sh = (x + side * 46, y - 176)
        a = lerp(math.pi / 2 - side * .6, -math.pi / 2 - side * .5, up) if side > 0 else lerp(math.pi / 2 + .6, -math.pi / 2 - .5 * -1 * -1, up)
        a = (lerp(math.pi / 2 + .6, -math.pi / 2 - .5, up)) if side < 0 else (lerp(math.pi / 2 - .6, -math.pi / 2 + .5, up))
        hand = (sh[0] + math.cos(a) * 60, sh[1] + math.sin(a) * 60)
        pen.cap(sh, hand, 13, SUN); pen.ell(hand[0], hand[1], 12, 12, SKIN, 5)
    hx, hy = x, y - 252
    pen.shaded_ell(hx, hy, 58, 56, SKIN, SKIN_SH)
    pen.d.polygon([P(hx - 50, hy - 26), P(hx - 30, hy - 60), P(hx + 10, hy - 66), P(hx + 48, hy - 34), P(hx + 14, hy - 44), P(hx + 20, hy - 76), P(hx - 6, hy - 50)], fill=(150, 96, 60, 255), outline=OUT + (255,), width=5 * S)
    for ex in (-1, 1):
        pen.ell(hx + ex * 20, hy + 4, 9, 11, (20, 24, 40), 0); pen.ell(hx + ex * 20 - 3, hy, 3, 3, WHITE, 0)
        pen.ell(hx + ex * 34, hy + 22, 11, 7, (255, 160, 150), 0)
    if st.get("laugh", 0) > .5: pen.d.chord([*P(hx - 22, hy + 6), *P(hx + 22, hy + 42)], 0, 180, fill=(150, 30, 50, 255), outline=OUT + (255,), width=4 * S)
    else: pen.arc(hx, hy + 24, 14, 9, .3, 2.8, OUT, 5)

# ------------------------------------------------------------------ timeline (s)
OPEN = (0.9, 1.7); CLOSE = (15.0, 15.8)
FLOOR = 1300; OX, KX, KIDX = 290, 800, 560
def blink_at(t, period, ph): q = (t + ph) % period; return 1 - abs(q - .09) / .09 if q < .18 else 0

# ---- lip sync: per-speaker loudness envelope from the voice files (cfg "voices"), else a simple talk cycle
import subprocess
ENV = {}
def _load_env():
    for v in CFG.get("voices", []):
        path = v["file"] if os.path.isabs(v["file"]) else str(ROOT / v["file"])
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", "8000", "-f", "s16le", "-"], capture_output=True, check=True).stdout
        x = np.frombuffer(raw, np.int16) / 32768.
        hop = 8000 // FPS; n = len(x) // hop
        e = np.array([np.sqrt(np.mean(x[i * hop:(i + 1) * hop] ** 2)) for i in range(n)])
        e = np.clip(e / (np.percentile(e, 90) + 1e-6), 0, 1.2)
        ENV.setdefault(v["who"], []).append((v["t"], e))
_load_env()
def voice_talk(who, t):
    for t0, e in ENV.get(who, []):
        i = int(round((t - t0) * FPS))
        if 0 <= i < len(e): return float(clamp(e[i] * 1.1))
    return None

def scene_chars(t):
    lay = Image.new("RGBA", (RW * S, RH * S), (0, 0, 0, 0)); pen = Pen(ImageDraw.Draw(lay))
    def appear(t0): p = seg(t, t0, t0 + .5); return p
    # --- Oksana state
    vt = voice_talk("oksana", t)
    talk = vt if vt is not None else ((abs(math.sin(t * 13)) * .9 + .1) if 2.9 <= t <= 4.9 and not ENV else 0)
    shock = ease(seg(t, 8.6, 8.8)) * (1 - seg(t, 14.6, 14.9))
    jump = max(0, math.sin(seg(t, 8.6, 9.1) * math.pi)) * 46
    jab = 0
    os_ = dict(talk=talk, shock=shock, jump=jump, jabR=jab, guard=shock * .9, blink=blink_at(t, 3.3, .4) if shock < .5 else 0, lookx=6 if t > 5 else 3)
    # --- Klaus state
    sq = max(0, math.sin(seg(t, 5.0, 5.45) * math.pi))
    lift = (back(seg(t, 5.3, 5.9), 1.4) if t >= 5.3 else 0) * (1 - ease(seg(t, 12.0, 12.6)))
    vk = voice_talk("klaus", t)
    ktalk = vk if vk is not None else ((abs(math.sin(t * 11 + 1)) * .9 + .1) if 6.2 <= t <= 8.1 and not ENV else 0)
    ks = dict(squat=sq, lift=min(lift, 1.08), talk=ktalk, blink=blink_at(t, 2.9, 1.2), brow=1 if 6.2 <= t <= 8.1 else 0)
    def scaled(fn, x, st, t0):
        p = appear(t0)
        if p <= 0: return
        if p >= 1: fn(pen, x, FLOOR, t, st); return
        sub = Image.new("RGBA", lay.size, (0, 0, 0, 0)); fn(Pen(ImageDraw.Draw(sub)), x, FLOOR, t, st)
        k = .2 + .8 * back(p)
        fx, fy = P(x, FLOOR)
        sw, sh = max(1, int(sub.width * k)), max(1, int(sub.height * k)); s2 = sub.resize((sw, sh), Image.BILINEAR)
        lay.alpha_composite(s2, (int(fx - fx * k), int(fy - fy * k)))
    scaled(oksana, OX, os_, 1.9)
    ks["hands"] = []
    scaled(klaus, KX, ks, 2.1)
    # kid: stands next to Klaus, then is carried by Klaus's hands
    if appear(2.3) > 0:
        if t < 5.3 or not ks["hands"]:
            hop = abs(math.sin(t * 6)) * 10 if 3.0 < t < 5.0 else 0
            kst = dict(armsup=.85, kick=0)
            scaled(kid, KIDX, kst, 2.3) if t < 2.8 else kid(pen, KIDX, FLOOR - hop, t, kst)
        else:
            hl, hr = ks["hands"][0], ks["hands"][1]; mx, my = (hl[0] + hr[0]) / 2, (hl[1] + hr[1]) / 2
            p = ease(seg(t, 5.3, 5.9)) * (1 - ease(seg(t, 12.0, 12.6))); kx = lerp(KIDX, mx, p); ky = lerp(FLOOR, my + 10, p)
            kid(pen, kx, ky, t, dict(armsup=1, kick=1 if 5.9 < t < 12.0 else 0, ground=t > 12.6, laugh=1 if t > 6.0 else 0))
            # Klaus's hands drawn again on top so he visibly holds the kid
            if t < 12.6:
                for h in (hl, hr): pen.shaded_ell(h[0], h[1], 20, 20, SKIN, SKIN_SH, 5)
    return lay.resize((RW, RH), Image.LANCZOS)

def put(frame, im, cx, cy, a=1., s=1.):
    if a <= .01: return
    if abs(s - 1) > .005: im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BICUBIC)
    if a < .999: im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    frame.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

def pop(frame, im, cx, cy, t, t0, t_out=None, dur=.35):
    p = seg(t, t0, t0 + dur)
    if p <= 0: return
    a = clamp(p * 2.5) * (1 - seg(t, *t_out) if t_out else 1)
    put(frame, im, cx, cy, a, (.5 + .5 * back(p)) if p < 1 else 1)

def slide_up(frame, im, cx, cy, t, t0, t_out):
    p = eout(seg(t, t0, t0 + .45))
    if p <= 0: return
    a = (1 - seg(t, *t_out)); put(frame, im, cx, cy + (1 - p) * 300, a * clamp(p * 2))

def render(t):
    frame = BASE.copy()
    o = ease(seg(t, *OPEN)) * (1 - ease(seg(t, *CLOSE)))
    if o > .02:
        frame.alpha_composite(scene_chars(t), (RX0, RY0))
        END = (14.6, 14.95)
        put(frame, SERIES, 40 + SERIES.width / 2 + 30, 205, seg(t, 1.6, 1.9) * (1 - seg(t, 5.9, 6.15)))
        pop(frame, B_OKS, 320, 480, t, 2.85, (12.3, 12.6))
        if t >= 9.5:                                                   # coral strike-through over Mum's phrase
            p = seg(t, 9.5, 9.85) * (1 - seg(t, 12.3, 12.6)); d = ImageDraw.Draw(frame)
            x0, x1 = 320 - B_OKS.width / 2 + 60, 320 + B_OKS.width / 2 - 60
            for k, yy0 in enumerate(OKS_ROWS):
                pk = clamp(p * 2 - k * .6)
                if pk > 0: d.line([(x0, yy0 + 10), (x0 + (x1 - x0) * pk, yy0 - 10)], fill=CORAL + (255,), width=12)
        pop(frame, B_KLA, min(780, W - 64 - B_KLA.width / 2), 290, t, 6.15, (12.3, 12.6))
        pop(frame, QM, 140, 760, t, 8.7, END)
        slide_up(frame, HEARD, W / 2, 1490, t, 6.6, (9.6, 9.9))
        slide_up(frame, FIX, W / 2, 1530, t, 9.9, END)
        pop(frame, CTA, W / 2, 410, t, 12.7, END, .45)
    spiral(frame)
    draw_cover(frame, o)
    if o <= .02: spiral(frame)
    return frame.convert("RGB")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        (ROOT / "preview").mkdir(exist_ok=True)
        for a in sys.argv[2:]: render(float(a)).save(ROOT / f"preview/v6_{float(a):05.2f}.jpg", quality=92)
        print("ok")
    else:
        FRAMES.mkdir(parents=True, exist_ok=True)
        for i in range(int(DUR * FPS)):
            render(i / FPS).save(FRAMES / f"{i:04d}.jpg", quality=93)
            if i % 90 == 0: print("frame", i, flush=True)
        print("done")
