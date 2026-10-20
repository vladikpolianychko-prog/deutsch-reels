"""Trend reel (Oct 2026): a crumpled notebook page unfolds on a dark desk and the answer is handwritten on it.
cfg: hook_small, hook_lines[], lines[{t, segs:[[text,color]], size}], clock{t, h, m, x, y}, sticky{t, text}, sub{t, text}
python3 compose_crumple.py [preview t1 t2 ...]"""
import math, sys, json, os
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "sheet"))
import make_sheet as M
W, H, FPS = 1080, 1920, 30
CFG = json.load(open(os.environ["CFG"], encoding="utf-8")); DUR = float(CFG.get("dur", 10))
FRAMES = Path(os.environ.get("FRAMES_DIR", str(ROOT / "frames_cr")))
C = M.COL
PW, PH = 920, 1240; PCX, PCY = W // 2, 1150
UNF = tuple(CFG.get("unfold", [0.35, 1.9]))

def clamp(x, a=0., b=1.): return max(a, min(b, x))
def seg(t, a, b): return clamp((t - a) / (b - a))
def ease(p): return 4 * p ** 3 if p < .5 else 1 - (-2 * p + 2) ** 3 / 2
def eout(p): return 1 - (1 - p) ** 3
def back(p, c=1.7): return 1 + (c + 1) * (p - 1) ** 3 + c * (p - 1) ** 2

# ---- desk
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); r = np.random.default_rng(3)
desk = np.zeros((H, W, 3), np.float32); desk[:] = (30, 40, 62)
desk += (np.sin(xx * .045 + np.sin(yy * .004) * 3) * 6 + r.normal(0, 3, (H, W)))[..., None]
lamp = np.clip(1 - np.hypot(xx - W * .8, yy + 100) / 1600, 0, 1)[..., None] ** 1.6
DESK = Image.fromarray(np.clip(desk * (1 + 1.5 * lamp) + np.array([70, 45, 10]) * lamp, 0, 255).astype(np.uint8)).convert("RGBA")

# ---- flat page (grid + margin), facet shading field for the crumple
M.W, M.H, M.SC = PW, PH, 1.0
PAGE = M.paper(4)
PAGE.putalpha(255)
g = np.random.default_rng(11); pts = np.c_[g.uniform(0, PW, 70), g.uniform(0, PH, 70)]
sy, sx = np.mgrid[0:PH // 4, 0:PW // 4].astype(np.float32) * 4
d2 = (sx[..., None] - pts[:, 0]) ** 2 + (sy[..., None] - pts[:, 1]) ** 2
o = np.sort(d2, axis=2); idx = np.argmin(d2, axis=2)
shade_v = g.uniform(-1, 1, len(pts))[idx]
edge = np.clip(1 - (np.sqrt(o[..., 1]) - np.sqrt(o[..., 0])) / 7, 0, 1)
SHADE = np.array(Image.fromarray(((shade_v + 1) * 127.5).astype(np.uint8)).resize((PW, PH), Image.BILINEAR), np.float32) / 127.5 - 1
EDGE = np.array(Image.fromarray((edge * 255).astype(np.uint8)).resize((PW, PH), Image.BILINEAR), np.float32) / 255

FD = "/usr/share/fonts/opentype/inter/"
def ui(t, size, col=(255, 255, 255), bold=True, maxw=980):
    f = ImageFont.truetype(FD + ("InterDisplay-Black.otf" if bold else "InterDisplay-SemiBold.otf"), size)
    while f.getlength(t) > maxw and size > 30: size -= 2; f = ImageFont.truetype(f.path, size)
    im = Image.new("RGBA", (int(f.getlength(t)) + 20, size + 30), (0, 0, 0, 0)); ImageDraw.Draw(im).text((10, 6), t, font=f, fill=col + (255,))
    sh = im.getchannel("A").filter(ImageFilter.GaussianBlur(8)); s = Image.new("RGBA", im.size, (0, 0, 0, 0)); s.putalpha(sh.point(lambda v: v * .55))
    out = Image.new("RGBA", (im.width, im.height + 6), (0, 0, 0, 0)); out.alpha_composite(s, (0, 6)); out.alpha_composite(im); return out

HOOK_S = ui(CFG["hook_small"], 54, (255, 214, 170), False)
HOOK = [ui(l, 84) for l in CFG["hook_lines"]]
LINES = [dict(l, sprite=M.sprite([(a, b) for a, b in l["segs"]], l.get("size", 64), l.get("bold", True), PW - 200)) for l in CFG["lines"]]

def clock(d, cx, cy, rr, hh, mm, p):
    k = back(p) if p < 1 else 1; rr = rr * k
    if rr < 4: return
    d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=C["ink"] + (255,), width=7, fill=(255, 255, 255, 230))
    for i in range(12):
        a = i * math.pi / 6; d.line((cx + math.cos(a) * rr * .78, cy + math.sin(a) * rr * .78, cx + math.cos(a) * rr * .9, cy + math.sin(a) * rr * .9), fill=C["ink"] + (255,), width=4)
    ah = ((hh % 12) + mm / 60) / 12 * 2 * math.pi - math.pi / 2; am = mm / 60 * 2 * math.pi - math.pi / 2
    d.line((cx, cy, cx + math.cos(ah) * rr * .5, cy + math.sin(ah) * rr * .5), fill=C["ink"] + (255,), width=9)
    d.line((cx, cy, cx + math.cos(am) * rr * .75, cy + math.sin(am) * rr * .75), fill=C["red"] + (255,), width=6)
    d.ellipse((cx - 7, cy - 7, cx + 7, cy + 7), fill=C["ink"] + (255,))

def page_at(t):
    pg = PAGE.copy(); d = ImageDraw.Draw(pg)
    for L in LINES:                                   # handwriting reveal: sprite clipped left-to-right
        p = seg(t, L["t"], L["t"] + L.get("dur", .55))
        if p <= 0: continue
        sp = L["sprite"]; w = max(1, int(sp.width * eout(p)))
        x = L.get("x", (PW - sp.width) // 2 + 30)
        pg.alpha_composite(sp.crop((0, 0, w, sp.height)), (int(x), int(L["y"])))
        if L.get("hl") and p >= 1: pass
    ck = CFG.get("clock")
    if ck and t >= ck["t"]: clock(d, ck["x"], ck["y"], ck.get("r", 95), ck["h"], ck["m"], seg(t, ck["t"], ck["t"] + .4))
    return pg

def crumple(pg, c):
    a = np.array(pg, np.float32)
    k = (1 + (.38 * c + .025) * SHADE)[..., None]; a[..., :3] *= k
    a[..., :3] *= (1 - (.5 * c + .06) * EDGE)[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")

def render(t):
    fr = DESK.copy()
    u = ease(seg(t, *UNF)); c = 1 - u
    pg = crumple(page_at(t), c)
    k = .26 + .74 * u; ang = 28 * c - 1.5 * u
    if c > .02:                                       # irregular silhouette while still crumpled
        m = Image.new("L", (PW, PH), 0); dm = ImageDraw.Draw(m); n = 40; rr = np.random.default_rng(5)
        jit = rr.uniform(-1, 1, n)
        poly = []
        for i in range(n):
            a = i / n * 2 * math.pi; ex, ey = math.cos(a), math.sin(a)
            sq = 1 / max(abs(ex) / (PW / 2), abs(ey) / (PH / 2))           # rectangle radius
            ci = min(PW, PH) / 2 * .95                                     # circle radius (ball)
            rad = lerp(sq, ci, c) * (1 + .12 * c * jit[i])
            poly.append((PW / 2 + ex * rad, PH / 2 + ey * rad))
        dm.polygon(poly, fill=255); pg.putalpha(Image.fromarray(np.minimum(np.array(m), np.array(pg.getchannel("A")))))
    pw, ph = max(2, int(PW * k)), max(2, int(PH * k))
    im = pg.resize((pw, ph), Image.BICUBIC).rotate(ang, expand=True, resample=Image.BICUBIC)
    sh = im.getchannel("A").filter(ImageFilter.GaussianBlur(24)); shadow = Image.new("RGBA", im.size, (0, 0, 0, 0)); shadow.putalpha(sh.point(lambda v: v * .6))
    bob = math.sin(t * 9) * 6 * c
    fr.alpha_composite(shadow, (int(PCX - im.width / 2 + 10), int(PCY - im.height / 2 + 26 + bob)))
    fr.alpha_composite(im, (int(PCX - im.width / 2), int(PCY - im.height / 2 + bob)))
    # hook on the desk (always)
    y = 90; fr.alpha_composite(HOOK_S, ((W - HOOK_S.width) // 2, y)); y += HOOK_S.height + 6
    for h in HOOK: fr.alpha_composite(h, ((W - h.width) // 2, y)); y += h.height - 6
    st = CFG.get("sticky")
    if st and t >= st["t"]:
        p = seg(t, st["t"], st["t"] + .35); sp = M.sprite([(st["text"], "ink")], 54, True, 860)
        card = Image.new("RGBA", (sp.width + 60, sp.height + 30), (255, 224, 122, 250)); card.alpha_composite(sp, (30, 15))
        card = card.rotate(-2, expand=True, resample=Image.BICUBIC); s = .6 + .4 * back(p)
        card = card.resize((max(1, int(card.width * s)), max(1, int(card.height * s))), Image.BICUBIC)
        fr.alpha_composite(card, ((W - card.width) // 2, st.get("y", 1640) - card.height // 2))
    return fr.convert("RGB")

def lerp(a, b, p): return a + (b - a) * p

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        out = Path(os.environ.get("PREVIEW_DIR", str(ROOT / "preview"))); out.mkdir(parents=True, exist_ok=True)
        for a in sys.argv[2:]: render(float(a)).save(out / f"cr_{float(a):05.2f}.jpg", quality=90)
        print("ok")
    else:
        FRAMES.mkdir(parents=True, exist_ok=True)
        for i in range(int(DUR * FPS)):
            render(i / FPS).save(FRAMES / f"{i:04d}.jpg", quality=93)
        print("done")
