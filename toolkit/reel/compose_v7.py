"""v7: "night sketchbook" with a configurable cast — every reel gets its own characters (look_spec), props (scene.kind),
poses/moods timeline and dialogue order.  Shares backdrop/cover/text helpers with v6.
cfg: series, hook_ua, hook_de_lines, heard, fix, gloss_de, gloss_ua, cta, open, cast{A,B}, scene, dialogue[], voices[], beats{}, sfx[]
python3 compose_v7.py [preview t1 t2 ...]"""
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
HOOK_DE = card([[DE(l, 84)] for l in CFG["hook_de_lines"]], CREAM, pad=(44, 30), radius=30, maxw=960)
BF = CFG.get("bubble_font", 64)
HEARD = card([[UA(CFG.get("heard_label", "Він почув:"), 50, CORAL, "bold")], [UA(CFG["heard"], 66, OUT)]], CREAM, border=CORAL, maxw=980)
FIX = card([[UA("ПРАВИЛЬНО", 44, WHITE, "black")], [DE(CFG["fix"], 92, WHITE)], [UA(CFG["gloss_de"], 62, SUN, "black"), UA(" = " + CFG["gloss_ua"], 62, WHITE, "bold")]], (35, 150, 118), pad=(46, 30), maxw=1000, gap=10)
CTA = card([[UA(CFG["cta"], 66, OUT)]], SUN, pad=(44, 28), maxw=1000)
QM = line_sprite([UA("?!", 150, CORAL)], 400)
BUBBLES = []
for b in CFG["dialogue"]:
    sp = bubble([[DE(l, BF)] for l in b["lines"]], b.get("tail", .5), b.get("maxw", 640))
    rh = sp.height - 100 - 8; cy = b["pos"][1]
    rows = [cy - sp.height / 2 + 20 + 23 + (k + .55) * (rh - 46) / len(b["lines"]) for k in range(len(b["lines"]))]
    BUBBLES.append(dict(b, sprite=sp, rows=rows))

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


# ------------------------------------------------------------------ v7: configurable cast
def ik(S0, T, l1, l2, side):
    dx, dy = T[0] - S0[0], T[1] - S0[1]; d = clamp(math.hypot(dx, dy), abs(l1 - l2) + 1, l1 + l2 - 1)
    base = math.atan2(dy, dx); a = math.acos(clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1))
    els = [(S0[0] + math.cos(base + s * a) * l1, S0[1] + math.sin(base + s * a) * l1) for s in (1, -1)]
    el = max(els, key=lambda e: side * (e[0] - S0[0]) + .3 * (e[1] - S0[1]))
    ang = math.atan2(T[1] - el[1], T[0] - el[0])
    return el, (el[0] + math.cos(ang) * l2, el[1] + math.sin(ang) * l2)

# hand targets relative to the neck base (x, top): (Lx, Ly, Rx, Ry)
POSES = {"rest": (-104, 205, 104, 205), "offer_r": (40, 125, 150, 125), "offer_l": (-150, 125, -40, 125),
         "hands_up": (-165, -85, 165, -85), "face": (-62, -66, 62, -66), "wave": (-104, 205, 150, -70),
         "finger": (-120, 175, 150, -150), "hips": (-122, 172, 122, 172), "belly": (-40, 205, 40, 205),
         "shrug": (-172, 25, 172, 25), "point_l": (-104, 205, -40, 205)}
def pose_at(timeline, t):
    """timeline [[t, pose], ...] -> blended targets"""
    cur = POSES[timeline[0][1]]; name = timeline[0][1]
    for t0, p in timeline[1:]:
        if t < t0: break
        k = ease(seg(t, t0, t0 + .28)); nxt = POSES[p]
        cur = tuple(lerp(a, b, k) for a, b in zip(cur, nxt)); name = p if k > .5 else name
    return cur, name
def mood_at(timeline, t):
    m = timeline[0][1]
    for t0, v in timeline[1:]:
        if t >= t0: m = v
    return m

def person(pen, x, y, t, sp, st):
    sk, sks = tuple(sp.get("skin", SKIN)), tuple(sp.get("skin_sh", SKIN_SH))
    leg = sp.get("leg", 210); tor = sp.get("torso", 220); sw = sp.get("shoulders", 86); hw = sp.get("hips", 100)
    oc, osh = tuple(sp["outfit_color"]), tuple(sp["outfit_shade"]); lc = tuple(sp.get("legs_color", (84, 92, 112)))
    hc = tuple(sp.get("hair_color", (120, 78, 50))); mood = st.get("mood", "neutral"); shock = 1 if mood == "shock" else 0
    br = math.sin(t * 2.3 + sp.get("ph", 0)) * 3; y -= st.get("jump", 0)
    lean = st.get("lean", 0)
    pen.d.ellipse([*P(x - 110, y - 14), *P(x + 110, y + 14)], fill=(0, 0, 0, 40))
    top = y - leg - tor + br; bot = y - leg + 20
    hx, hy = x + lean, top - 92
    kind = sp["outfit"]
    # ---- long hair behind everything
    if sp.get("hair") == "long":
        pen.poly([(hx - 104, hy - 40), (hx - 124, hy + 120), (hx - 112, hy + 200), (hx + 112, hy + 200), (hx + 124, hy + 120), (hx + 104, hy - 40)], hc)
    # ---- legs + shoes
    shoe = tuple(sp.get("shoes", (70, 46, 34)))
    if kind == "dress":
        for sx in (-1, 1): pen.cap((x + sx * 30, y - 140), (x + sx * 34, y - 40), 17, sk); pen.ell(x + sx * 44, y - 22, 36, 18, shoe)
    elif kind == "robe":
        for sx in (-1, 1):
            pen.cap((x + sx * 30, y - 150), (x + sx * 34, y - 40), 24, lc)
            for k in range(3): pen.line([(x + sx * 34 - 22, y - 130 + k * 30), (x + sx * 34 + 22, y - 130 + k * 30)], tuple(sp.get("stripe", (90, 110, 170))), 5)
            pen.ell(x + sx * 48, y - 20, 48, 20, shoe); pen.ell(x + sx * 48, y - 30, 30, 10, WHITE, 0)
    else:
        for sx in (-1, 1):
            pen.cap((x + sx * 32, bot - 20), (x + sx * 36, y - 40), 26, lc)
            pen.ell(x + sx * 50, y - 20, 46, 21, shoe)
            if kind == "hoodie": pen.line([(x + sx * 28, y - 26), (x + sx * 72, y - 26)], (210, 214, 225), 4)
    # ---- torso
    if kind == "dress":
        pen.poly([(x - sw, top + 20), (x + sw, top + 20), (x + hw * .8, bot - 30), (x - hw * .8, bot - 30)], oc)
        pen.poly([(x - hw * .8, bot - 40), (x + hw * .8, bot - 40), (x + hw + 36, y - 130), (x - hw - 36, y - 130)], oc)
        pen.d.polygon([P(x + 20, bot - 34), P(x + hw * .8, bot - 34), P(x + hw + 30, y - 136), P(x + 50, y - 136)], fill=osh + (255,))
        pen.line([(x - hw * .8, bot - 38), (x + hw * .8, bot - 38)], osh, 10)
        for k in range(5): pen.ell(x - 60 + k * 30, y - 170 + (k % 2) * 14, 6, 6, WHITE, 0)
    elif kind == "robe":
        pen.poly([(x - sw, top + 20), (x + sw, top + 20), (x + hw + 14, y - 140), (x - hw - 14, y - 140)], oc)
        pen.d.polygon([P(x + 30, top + 26), P(x + sw - 2, top + 26), P(x + hw + 8, y - 146), P(x + 50, y - 146)], fill=osh + (255,))
        pen.poly([(x - 34, top + 20), (x + 34, top + 20), (x, top + 120)], tuple(sp.get("legs_color", WHITE)), 5)
        for k in range(3): pen.line([(x - 22 + k * 4, top + 30 + k * 26), (x + 22 - k * 4, top + 30 + k * 26)], tuple(sp.get("stripe", (90, 110, 170))), 4)
        pen.line([(x - 40, top + 20), (x + 6, top + 150), (x + 30, y - 140)], OUT, 5)
        pen.line([(x + 40, top + 20), (x - 4, top + 140)], osh, 12)
        by = top + tor * .62
        pen.d.rectangle([*P(x - sw - 4, by - 12), *P(x + sw + 4, by + 12)], fill=osh + (255,), outline=OUT + (255,), width=4 * S)
        pen.cap((x + 20, by + 6), (x + 34, by + 80), 8, osh, 4); pen.cap((x + 28, by + 6), (x + 56, by + 70), 8, osh, 4)
    elif kind == "sweater":
        pen.poly([(x - sw, top + 20), (x + sw, top + 20), (x + hw, bot), (x - hw, bot)], oc)
        pen.ell(x, top + tor * .62, hw + 6, tor * .42, oc, 6)
        pen.d.ellipse([*P(x + 10, top + tor * .3), *P(x + hw, top + tor * .9)], fill=osh + (255,))
        zz = [(x - sw + 8 + k * 24, top + 70 + (k % 2) * 16) for k in range(int((2 * sw - 16) / 24) + 1)]
        pen.line(zz, tuple(sp.get("knit", WHITE)), 6)
        pen.d.rectangle([*P(x - hw + 4, bot - 22), *P(x + hw - 4, bot - 6)], fill=osh + (255,))
    else:   # hoodie
        pen.poly([(x - sw, top + 20), (x + sw, top + 20), (x + hw, bot), (x - hw, bot)], oc)
        pen.d.polygon([P(x + 30, top + 24), P(x + sw - 2, top + 24), P(x + hw - 4, bot - 4), P(x + 50, bot - 4)], fill=osh + (255,))
        pen.poly([(x - 56, top + tor * .6), (x + 56, top + tor * .6), (x + 70, bot - 8), (x - 70, bot - 8)], osh, 5)
        pen.d.rectangle([*P(x - hw, bot - 22), *P(x + hw, bot - 2)], fill=osh + (255,))
        pen.arc(x, top + 18, 74, 40, .1, 3.04, osh, 22)
        for sx in (-1, 1): pen.line([(x + sx * 20, top + 40), (x + sx * 24, top + 110)], WHITE, 5); pen.ell(x + sx * 24, top + 114, 6, 6, WHITE, 3)
    # ---- neck, head, ears
    pen.cap((x, top + 20), (hx, top - 20), 24, sk)
    if sp.get("hair") == "bun":
        pen.ell(hx + 4, hy - 138, 50, 44, hc)
        pen.ell(hx, hy - 10, 94, 96, hc)
    for ex in (-1, 1): pen.ell(hx + ex * 78, hy + 10, 17, 22, sk)
    pen.shaded_ell(hx, hy + 2, sp.get("head_rx", 80), sp.get("head_ry", 90), sk, sks)
    hs = sp.get("hair")
    if hs == "long":
        pen.d.polygon([P(hx - 98, hy - 6), P(hx - 84, hy - 80), P(hx - 10, hy - 106), P(hx + 70, hy - 92), P(hx + 98, hy - 6), P(hx + 76, hy - 40), P(hx + 20, hy - 66), P(hx - 30, hy - 50), P(hx - 70, hy - 20)], fill=hc + (255,), outline=OUT + (255,), width=6 * S)
    elif hs == "bun":
        pen.d.polygon([P(hx - 92, hy - 10), P(hx - 70, hy - 84), P(hx, hy - 104), P(hx + 74, hy - 86), P(hx + 94, hy - 12), P(hx + 50, hy - 56), P(hx - 10, hy - 62), P(hx - 56, hy - 44)], fill=hc + (255,), outline=OUT + (255,), width=6 * S)
        pen.cap((hx - 30, hy - 102), (hx + 36, hy - 100), 9, tuple(sp.get("scrunchie", CORAL)), 4)
        pen.arc(hx - 8, hy - 150, 24, 16, 3.6, 4.9, (min(255, hc[0] + 70), min(255, hc[1] + 60), min(255, hc[2] + 50)), 5)
    elif hs == "short":
        pen.d.polygon([P(hx - 82, hy - 20), P(hx - 72, hy - 80), P(hx - 10, hy - 104), P(hx + 60, hy - 92), P(hx + 84, hy - 30), P(hx + 60, hy - 60), P(hx - 30, hy - 66), P(hx - 66, hy - 36)], fill=hc + (255,), outline=OUT + (255,), width=6 * S)
    elif hs == "bald_sides":
        for ex in (-1, 1): pen.ell(hx + ex * 74, hy - 14, 22, 34, hc, 5)
        pen.arc(hx - 18, hy - 54, 30, 18, 3.5, 5.0, WHITE, 6)
    # ---- face
    lx = st.get("lookx", 4); b = st.get("blink", 0); ang = 1 if mood == "angry" else 0
    for ex in (-1, 1):
        ex0, ey = hx + ex * 30, hy - 6
        ry = 23 + 10 * shock
        pen.ell(ex0, ey, 19 + 4 * shock, ry, WHITE, 5)
        pen.ell(ex0 + lx, ey + 4, 10, 12, tuple(sp.get("eyes", (60, 90, 150))), 0); pen.ell(ex0 + lx, ey + 4, 6, 7, (20, 24, 40), 0); pen.ell(ex0 + lx - 4, ey - 2, 4, 4, WHITE, 0)
        if b > 0:
            yb = ey - ry - 6 + (2 * ry + 8) * b
            pen.d.rectangle([*P(ex0 - 25, ey - ry - 6), *P(ex0 + 25, yb)], fill=sk + (255,)); pen.line([(ex0 - 22, yb), (ex0 + 22, yb)], OUT, 5)
        by = ey - 40 - 16 * shock
        bc = tuple(sp.get("brow", OUT)); bw = sp.get("brow_w", 7)
        pen.line([(ex0 + ex * 22, by - 2 - 6 * ang), (ex0 - ex * 20, by + 2 + 12 * ang)], bc, bw)
        if sp.get("blush"): pen.ell(ex0 + ex * 14, hy + 40, 17, 9, (255, 170, 160), 0)
        if sp.get("glasses"): pen.d.ellipse([*P(ex0 - 29, ey - 29), *P(ex0 + 29, ey + 29)], outline=OUT + (255,), width=5 * S)
    if sp.get("glasses"): pen.line([(hx - 4, hy - 8), (hx + 4, hy - 8)], OUT, 5)
    pen.arc(hx + 2, hy + 22, 8, 6, .2, 2.9, sks, 5)
    if sp.get("beard"):
        bc = tuple(sp["beard"])
        pen.d.polygon([P(hx - 78, hy + 6), P(hx - 70, hy + 70), P(hx - 30, hy + 108), P(hx + 30, hy + 108), P(hx + 70, hy + 70), P(hx + 78, hy + 6), P(hx + 56, hy + 40), P(hx - 56, hy + 40)], fill=bc + (255,), outline=OUT + (255,), width=5 * S)
    talk = st.get("talk", 0); lip = tuple(sp.get("lips", (200, 50, 70)))
    my = hy + 56
    if talk > .05: pen.ell(hx, my, 22, 5 + 16 * talk, (150, 30, 50), 6); pen.ell(hx, my + 6 + 7 * talk, 11, 4 * talk + 1, (240, 110, 120), 0)
    elif shock: pen.ell(hx, my + 4, 17, 25, (150, 30, 50), 6)
    elif mood == "laugh": pen.d.chord([*P(hx - 30, my - 16), *P(hx + 30, my + 30)], 0, 180, fill=(150, 30, 50, 255), outline=OUT + (255,), width=5 * S)
    elif mood == "happy": pen.arc(hx, my - 10, 26, 16, .25, 2.9, lip, 7)
    elif mood == "angry": pen.arc(hx, my + 12, 20, 12, 3.5, 5.9, OUT, 6)
    else: pen.line([(hx - 14, my), (hx + 14, my)], OUT, 6)
    if sp.get("mustache"):
        mc = tuple(sp["mustache"])
        pen.d.polygon([P(hx - 4, hy + 28), P(hx - 40, hy + 30), P(hx - 70, hy + 18), P(hx - 56, hy + 46), P(hx - 10, hy + 44), P(hx, hy + 38), P(hx + 10, hy + 44), P(hx + 56, hy + 46), P(hx + 70, hy + 18), P(hx + 40, hy + 30), P(hx + 4, hy + 28)], fill=mc + (255,), outline=OUT + (255,), width=5 * S)
    if sp.get("earrings"):
        swg = math.sin(t * 5) * 5
        for ex in (-1, 1): pen.ell(hx + ex * 82 + swg, hy + 44, 9, 9, SUN, 4)
    # ---- hats
    hat = sp.get("hat")
    if hat == "party":
        pen.poly([(hx - 46, hy - 80), (hx + 40, hy - 92), (hx + 22, hy - 230)], CORAL, 6)
        for k in (1, 2):
            f = k / 3; pen.line([(lerp(hx - 46, hx + 22, f) + 3, lerp(hy - 80, hy - 230, f)), (lerp(hx + 40, hx + 22, f) - 3, lerp(hy - 92, hy - 230, f))], SUN, 9)
        pen.ell(hx + 22, hy - 236, 18, 18, SUN, 5)
    elif hat == "nightcap":
        sway = math.sin(t * 2.2) * 8; hcol = tuple(sp.get("hat_color", SKY))
        pen.poly([(hx + 92, hy - 56), (hx + 60, hy - 140), (hx - 30, hy - 168), (hx - 110, hy - 130), (hx - 150 + sway, hy - 40), (hx - 92, hy - 76), (hx - 92, hy - 56)], hcol)
        pen.cap((hx - 92, hy - 60), (hx + 92, hy - 60), 13, WHITE, 5)
        pen.ell(hx - 152 + sway, hy - 34, 22, 22, WHITE, 5)
    # ---- arms (drawn last so hands can touch the face)
    tg, pname = st["targets"], st["pose_name"]
    sl = tuple(sp.get("sleeve", oc)); L1, L2 = 92 * sp.get("arm", 1), 84 * sp.get("arm", 1)
    hands = []
    for side, (tx, ty) in ((-1, tg[:2]), (1, tg[2:])):
        shp = (x + side * sw, top + 40)
        if pname == "wave" and side == 1: tx += math.sin(t * 14) * 24
        el, hand = ik(shp, (x + tx + (lean if ty < 60 else 0), top + ty), L1, L2, side)
        pen.cap(shp, el, 22, sl); pen.cap(el, hand, 20, sl)
        pen.shaded_ell(hand[0], hand[1], 20, 21, sk, sks, 5)
        if pname == "finger" and side == 1: pen.cap((hand[0] + 2, hand[1] - 14), (hand[0] + 6, hand[1] - 56), 8, sk, 4)
        hands.append(hand)
    st["hands"] = hands

# ------------------------------------------------------------------ props (drawn in the supersampled layer)
def note(pen, x, y, k, col):
    pen.ell(x, y, 14 * k, 11 * k, col, 4); pen.line([(x + 12 * k, y), (x + 12 * k, y - 52 * k)], OUT, 5); pen.line([(x + 12 * k, y - 52 * k), (x + 34 * k, y - 34 * k)], OUT, 5)

def props_back(pen, t):
    sc = CFG["scene"]; kind = sc["kind"]
    if kind == "birthday":
        tx = sc.get("table_x", 545); ty = FLOOR - 200
        for i, (bx, by, col) in enumerate(((tx - 70, 660, CORAL), (tx + 10, 610, SKY), (tx + 80, 680, SUN))):
            bob = math.sin(t * 1.7 + i * 1.3) * 10; cy = by + bob
            pen.line([(bx, cy + 64), (bx + math.sin(t * 1.1 + i) * 10, cy + 160), (tx - 30 + i * 30, ty - 40)], (120, 128, 150), 3)
            pen.ell(bx, cy, 50, 62, col, 6); pen.arc(bx - 16, cy - 20, 18, 26, 3.4, 4.6, WHITE, 6)
            pen.poly([(bx - 9, cy + 64), (bx + 9, cy + 64), (bx, cy + 78)], col, 4)
        pen.d.rectangle([*P(tx - 26, ty), *P(tx + 26, FLOOR - 10)], fill=(150, 108, 76, 255), outline=OUT + (255,), width=5 * S)
        pen.poly([(tx - 110, ty - 20), (tx + 110, ty - 20), (tx + 120, ty + 30), (tx - 120, ty + 30)], WHITE)
        for k in range(5): pen.ell(tx - 88 + k * 44, ty + 30, 22, 10, (255, 150, 170), 0)
        pen.d.rectangle([*P(tx - 80, ty - 100), *P(tx + 80, ty - 22)], fill=(250, 214, 226, 255), outline=OUT + (255,), width=5 * S)
        pen.d.rectangle([*P(tx - 52, ty - 160), *P(tx + 52, ty - 100)], fill=(255, 238, 244, 255), outline=OUT + (255,), width=5 * S)
        pen.line([(tx - 80, ty - 70), (tx - 40, ty - 58), (tx, ty - 72), (tx + 40, ty - 58), (tx + 80, ty - 70)], CORAL, 6)
        for k in (-1, 0, 1):
            cx = tx + k * 30; pen.d.rectangle([*P(cx - 6, ty - 204), *P(cx + 6, ty - 160)], fill=SKY + (255,), outline=OUT + (255,), width=3 * S)
            fl = 1 + .15 * math.sin(t * 19 + k * 2)
            pen.ell(cx, ty - 220, 8 * fl, 14 * fl, SUN, 3); pen.ell(cx, ty - 216, 4, 7, (255, 250, 220), 0)
    elif kind == "night_door":
        dx0, dx1, dy0 = sc.get("door", [660, 940, 640])
        pen.d.rectangle([*P(dx0 - 22, dy0 - 22), *P(dx1 + 22, FLOOR)], fill=(150, 108, 76, 255), outline=OUT + (255,), width=6 * S)
        pen.d.rectangle([*P(dx0, dy0), *P(dx1, FLOOR)], fill=(38, 48, 78, 255), outline=OUT + (255,), width=5 * S)
        lamp = Image.new("RGBA", (1, 1)); pen.ell((dx0 + dx1) / 2, dy0 + 60, 70, 40, (255, 214, 120), 0)
        pen.ell((dx0 + dx1) / 2, dy0 + 60, 26, 16, (255, 246, 210), 0)
        pen.poly([(dx1 + 22, dy0 - 10), (dx1 + 70, dy0 + 30), (dx1 + 70, FLOOR - 30), (dx1 + 22, FLOOR)], (196, 150, 108), 5)
        pen.ell(dx1 + 58, (dy0 + FLOOR) / 2, 7, 7, SUN, 3)
        pen.d.rectangle([*P(dx0 - 10, FLOOR - 26), *P(dx1 + 10, FLOOR)], fill=(176, 120, 80, 255), outline=OUT + (255,), width=4 * S)
        cx, cy = sc.get("clock", [520, 690]); pen.ell(cx, cy, 64, 64, WHITE, 7)
        for k in range(12):
            a = k * math.pi / 6; pen.line([(cx + math.cos(a) * 50, cy + math.sin(a) * 50), (cx + math.cos(a) * 58, cy + math.sin(a) * 58)], OUT, 4)
        hh, mm = sc.get("time", [22, 30]); ah = ((hh % 12) + mm / 60) / 12 * 2 * math.pi - math.pi / 2; am = mm / 60 * 2 * math.pi - math.pi / 2
        pen.line([(cx, cy), (cx + math.cos(ah) * 30, cy + math.sin(ah) * 30)], OUT, 8); pen.line([(cx, cy), (cx + math.cos(am) * 46, cy + math.sin(am) * 46)], CORAL, 5)
        pen.ell(cx, cy, 6, 6, OUT, 0)
        mx, my2 = sc.get("moon", [150, 640])
        pen.d.rectangle([*P(mx - 80, my2 - 90), *P(mx + 80, my2 + 90)], fill=(38, 48, 88, 255), outline=(150, 108, 76, 255), width=12 * S)
        pen.ell(mx + 20, my2 - 30, 30, 30, (255, 236, 160), 0); pen.ell(mx + 34, my2 - 40, 26, 26, (38, 48, 88), 0)
        for sx, sy in ((-40, 30), (-10, 60), (40, 40), (-50, -50)): pen.ell(mx + sx, my2 + sy, 4, 4, WHITE, 0)
        pen.line([(mx, my2 - 90), (mx, my2 + 90)], (150, 108, 76), 8); pen.line([(mx - 80, my2), (mx + 80, my2)], (150, 108, 76), 8)
        # speaker with music notes until it is switched off
        spx = sc.get("speaker_x", 500); off = sc.get("music_off", 99)
        pen.d.rounded_rectangle([*P(spx - 70, FLOOR - 120), *P(spx + 70, FLOOR - 6)], 14 * S, fill=(52, 60, 84, 255), outline=OUT + (255,), width=5 * S)
        for k in (-1, 1):
            pump = 1 + (.12 * abs(math.sin(t * 9)) if t < off else 0)
            pen.ell(spx + k * 34, FLOOR - 62, 26 * pump, 26 * pump, (90, 100, 128), 4); pen.ell(spx + k * 34, FLOOR - 62, 10, 10, OUT, 0)
        pen.ell(spx, FLOOR - 104, 5, 5, MINT if t < off else CORAL, 0)
        if t < off:
            for i in range(4):
                ph = (t * .55 + i * .25) % 1; k = 1 - ph * .4
                note(pen, spx - 30 + i * 22 + math.sin(t * 3 + i) * 26, FLOOR - 140 - ph * 300, k, (MINT, SUN, CORAL, SKY)[i])

def gift_box(pen, cx, cy, ang=0):
    pts = [(-62, -46), (62, -46), (62, 50), (-62, 50)]
    rot = lambda p: (cx + p[0] * math.cos(ang) - p[1] * math.sin(ang), cy + p[0] * math.sin(ang) + p[1] * math.cos(ang))
    pen.poly([rot(p) for p in pts], SKY)
    pen.poly([rot(p) for p in [(-10, -46), (10, -46), (10, 50), (-10, 50)]], CORAL, 4)
    pen.poly([rot(p) for p in [(-68, -60), (68, -60), (68, -40), (-68, -40)]], SKY)
    for s in (-1, 1): pen.poly([rot(p) for p in [(0, -60), (s * 40, -92), (s * 46, -62)]], CORAL, 4)

# ------------------------------------------------------------------ timeline
OPEN = tuple(CFG.get("open", [0.9, 1.7])); CLOSE = (15.0, 15.8)
FLOOR = 1300
def blink_at(t, period, ph): q = (t + ph) % period; return 1 - abs(q - .09) / .09 if q < .18 else 0

import subprocess
ENV = {}
for v in CFG.get("voices", []):
    path = v["file"] if os.path.isabs(v["file"]) else str(ROOT / v["file"])
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", "8000", "-f", "s16le", "-"], capture_output=True, check=True).stdout
    xx_ = np.frombuffer(raw, np.int16) / 32768.; hop = 8000 // FPS
    e = np.array([np.sqrt(np.mean(xx_[i * hop:(i + 1) * hop] ** 2)) for i in range(len(xx_) // hop)])
    ENV.setdefault(v["who"], []).append((v["t"], np.clip(e / (np.percentile(e, 90) + 1e-6), 0, 1.2)))
def voice_talk(who, t):
    for t0, e in ENV.get(who, []):
        i = int(round((t - t0) * FPS))
        if 0 <= i < len(e): return float(clamp(e[i] * 1.1))
    return 0.

def scene_chars(t):
    lay = Image.new("RGBA", (RW * S, RH * S), (0, 0, 0, 0)); pen = Pen(ImageDraw.Draw(lay))
    props_back(pen, t)
    hands = {}
    for key in ("A", "B"):
        c = CFG["cast"][key]
        tg, pn = pose_at(c["poses"], t)
        mood = mood_at(c["moods"], t)
        st = dict(targets=tg, pose_name=pn, mood=mood, talk=voice_talk(key, t), blink=blink_at(t, 3.1 + (key == "B") * .4, .4 + (key == "B")) if mood != "shock" else 0,
                  lookx=c.get("look", 4), lean=lerp(0, c.get("lean_amt", 0), max([ease(seg(t, a, a + .3)) * (1 - ease(seg(t, b, b + .4))) for a, b in c.get("lean", [[99, 99]])])),
                  jump=max([0] + [math.sin(seg(t, a, a + .5) * math.pi) * 40 for a in c.get("jumps", [])]))
        p = seg(t, c.get("appear", 1.9), c.get("appear", 1.9) + .5)
        if p <= 0: continue
        if p >= 1: person(pen, c["x"], FLOOR, t, c["look_spec"], st)
        else:
            sub = Image.new("RGBA", lay.size, (0, 0, 0, 0)); person(Pen(ImageDraw.Draw(sub)), c["x"], FLOOR, t, c["look_spec"], st)
            k = .2 + .8 * back(p); fx, fy = P(c["x"], FLOOR)
            s2 = sub.resize((max(1, int(sub.width * k)), max(1, int(sub.height * k))), Image.BILINEAR)
            lay.alpha_composite(s2, (int(fx - fx * k), int(fy - fy * k)))
        hands[key] = st.get("hands")
    sc = CFG["scene"]
    if sc["kind"] == "birthday" and hands.get("A"):
        (l, r) = hands["A"]; drop = sc.get("box_drop", 99)
        bx, by = (l[0] + r[0]) / 2, (l[1] + r[1]) / 2 - 30
        if t >= drop:
            p = seg(t, drop, drop + .45); gx = sc.get("box_floor_x", 470)
            bx, by = lerp(bx, gx, p), lerp(by, FLOOR - 50, p * p); gift_box(pen, bx, by, p * .5)
        else: gift_box(pen, bx, by)
        a, b = sc.get("poison", [99, 99])
        if a <= t <= b + .6:
            for i in range(7):
                ph = ((t - a) * .9 + i / 7) % 1; k = 1 - seg(t, b, b + .6)
                if k > 0: pen.ell(bx - 5 + (i * 37) % 90 + math.sin(t * 4 + i) * 12, by - 70 - ph * 220, (8 + i % 3 * 5) * k, (8 + i % 3 * 5) * k, (120, 210, 80), 4)
    if sc.get("confetti") is not None:
        t0 = sc["confetti"]
        if t >= t0:
            rng = np.random.default_rng(7)
            for i in range(70):
                ang = rng.uniform(-math.pi, 0); sp0 = rng.uniform(400, 900); dt = t - t0
                cx = sc.get("confetti_x", 545) + math.cos(ang) * sp0 * dt
                cy = 760 + math.sin(ang) * sp0 * dt + 600 * dt * dt
                if cy < FLOOR:
                    col = (CORAL, SUN, MINT, SKY, (255, 150, 190))[i % 5]; w2 = 9 + 4 * math.sin(t * 10 + i)
                    pen.d.rectangle([*P(cx - w2, cy - 6), *P(cx + w2, cy + 6)], fill=col + (255,))
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

BT = CFG["beats"]
def render(t):
    frame = BASE.copy()
    o = ease(seg(t, *OPEN)) * (1 - ease(seg(t, *CLOSE)))
    if o > .02:
        frame.alpha_composite(scene_chars(t), (RX0, RY0))
        END = (14.6, 14.95)
        put(frame, SERIES, 40 + SERIES.width / 2 + 30, 205, seg(t, OPEN[1] - .1, OPEN[1] + .2) * (1 - seg(t, BT["series_out"], BT["series_out"] + .25)))
        for b in BUBBLES:
            sp = b["sprite"]; cx = min(b["pos"][0], W - 64 - sp.width / 2); cx = max(cx, 64 + sp.width / 2)
            pop(frame, sp, cx, b["pos"][1], t, b["in"], (b["out"], b["out"] + .3))
            if b.get("wrong") and t >= BT["strike"]:
                p = seg(t, BT["strike"], BT["strike"] + .35) * (1 - seg(t, b["out"], b["out"] + .3)); d = ImageDraw.Draw(frame)
                x0, x1 = cx - sp.width / 2 + 60, cx + sp.width / 2 - 60
                for k, yy0 in enumerate(b["rows"]):
                    pk = clamp(p * 2 - k * .6)
                    if pk > 0: d.line([(x0, yy0 + 10), (x0 + (x1 - x0) * pk, yy0 - 10)], fill=CORAL + (255,), width=12)
        pop(frame, QM, *BT["qm_pos"], t, BT["qm"], END)
        slide_up(frame, HEARD, W / 2, 1490, t, BT["heard"][0], (BT["heard"][1], BT["heard"][1] + .3))
        slide_up(frame, FIX, W / 2, 1530, t, BT["fix"], END)
        pop(frame, CTA, W / 2, BT.get("cta_y", 410), t, BT["cta"], END, .45)
    spiral(frame)
    draw_cover(frame, o)
    if o <= .02: spiral(frame)
    return frame.convert("RGB")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        out = Path(os.environ.get("PREVIEW_DIR", str(ROOT / "preview"))); out.mkdir(exist_ok=True, parents=True)
        for a in sys.argv[2:]: render(float(a)).save(out / f"v7_{float(a):05.2f}.jpg", quality=90)
        print("ok")
    else:
        FRAMES.mkdir(parents=True, exist_ok=True)
        for i in range(int(DUR * FPS)):
            render(i / FPS).save(FRAMES / f"{i:04d}.jpg", quality=93)
            if i % 90 == 0: print("frame", i, flush=True)
        print("done")
