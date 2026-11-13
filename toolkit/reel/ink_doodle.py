"""/ink-doodle reel: hand-drawn stick-figure story, thick black ink outlines, flat pastel colours, 'boiling' lines
(every outline is re-jittered ~8x per second), a sign label at the top, captions on notebook-paper scraps.
Story (cfg-free, Friday the 13th): Pech gehabt! -> So ein Pech! -> Schwein gehabt! -> Ich drücke dir die Daumen!
usage: python3 ink_doodle.py out.mp4 | preview dir t1 t2 ...
"""
import math, os, subprocess, sys, tempfile, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import clean_audio as CA, follow_card as FC

W, H, FPS = 1080, 1920, 30
INK = (24, 24, 28); SKY = (168, 220, 235); HILL = (160, 210, 140); GRASS = (124, 190, 104)
WALK = (218, 214, 206); ROAD = (126, 133, 140); WOOD = (176, 120, 70); TREE = (92, 170, 84); TRUNK = (128, 84, 48)
HAIR = (120, 72, 38); SKIN = (255, 255, 255); BUS = (246, 196, 52); PIG = (246, 168, 180); PIGD = (226, 130, 148)
HF = str(HERE / "bg/fonts/ComicRelief-Bold.ttf"); HR = str(HERE / "bg/fonts/ComicRelief-Regular.ttf")
FI = lambda n, w="Black": ImageFont.truetype(f"/usr/share/fonts/opentype/inter/InterDisplay-{w}.otf", n)
FH = lambda n: ImageFont.truetype(HF, n)

def clamp(x, a=0., b=1.): return max(a, min(b, x))
def seg(t, a, b): return clamp((t - a) / (b - a))
def ease(p): return 4 * p ** 3 if p < .5 else 1 - (-2 * p + 2) ** 3 / 2
def back(p): return 1 + 2.7 * (p - 1) ** 3 + 1.7 * (p - 1) ** 2

class Pen:
    """jittered ink drawing; the seed changes every 4 frames -> boiling lines"""
    def __init__(self, d, seed): self.d = d; self.r = np.random.default_rng(seed)
    def j(self, pts, a=2.2): return [(x + self.r.uniform(-a, a), y + self.r.uniform(-a, a)) for x, y in pts]
    def line(self, pts, w=7, col=INK, a=2.0):
        p = self.j(pts, a); self.d.line(p, fill=col, width=w, joint="curve")
        for x, y in (p[0], p[-1]): self.d.ellipse((x - w / 2, y - w / 2, x + w / 2, y + w / 2), fill=col)
    def poly(self, pts, fill, w=7, a=2.0):
        p = self.j(pts, a); self.d.polygon(p, fill=fill); self.d.line(p + [p[0]], fill=INK, width=w, joint="curve")
    def ell(self, cx, cy, rx, ry, fill, w=7, n=44, a=1.8, rot=0):
        pts = []
        for i in range(n):
            t = i / n * 2 * math.pi; x, y = rx * math.cos(t), ry * math.sin(t)
            pts.append((cx + x * math.cos(rot) - y * math.sin(rot), cy + x * math.sin(rot) + y * math.cos(rot)))
        if fill is None:
            p = self.j(pts, a); self.d.line(p + [p[0]], fill=INK, width=w, joint="curve")
        else: self.poly(pts, fill, w, a)
    def rect(self, x0, y0, x1, y1, fill, w=7): self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], fill, w)

def cloud(P, cx, cy, s=1, fill=(255, 255, 255)):
    pts = []
    for i in range(60):
        t = i / 60 * 2 * math.pi; r = 1 + .18 * max(0, math.sin(t * 5)) if math.sin(t) < .2 else 1
        pts.append((cx + math.cos(t) * 110 * s * r, cy + math.sin(t) * 42 * s * (r if math.sin(t) < 0 else .8)))
    P.poly(pts, fill, 6)

# ------------------------------------------------------------------ scene timing
T_HOOK, T_CAT, T_BUS, C1 = 0.0, 2.6, 4.2, 5.9      # Pech gehabt card at C1
T_RAIN, C2 = 8.6, 9.9                               # So ein Pech
T_PIG, C3 = 12.6, 14.9                              # Schwein gehabt
T_THUMB, C4 = 18.2, 18.7                            # Ich drücke dir die Daumen
BODY = 22.6; DUR = BODY + 4.8

def background(P, t):
    d = P.d
    d.rectangle((0, 0, W, 1100), fill=SKY)
    sun = seg(t, T_PIG + 1.2, T_PIG + 2.2)
    if sun > 0:
        r = 70 * back(sun); P.ell(900, 200, r, r, (255, 214, 70), 6)
        for k in range(10):
            a = k / 10 * 2 * math.pi + t * .4; P.line([(900 + math.cos(a) * (r + 18), 200 + math.sin(a) * (r + 18)), (900 + math.cos(a) * (r + 48), 200 + math.sin(a) * (r + 48))], 6)
    for cx, cy, s, sp in ((170, 330, 1, 9), (860, 420, .8, 6)):
        cloud(P, (cx + t * sp) % (W + 300) - 150, cy, s)
    pts = [(0, 1000)] + [(x, 960 + 30 * math.sin(x / 170)) for x in range(0, W + 1, 40)] + [(W, 1100), (0, 1100)]
    P.poly(pts, HILL, 6, 1.2)
    d.rectangle((0, 1040, W, 1120), fill=GRASS); P.line([(0, 1040), (W, 1040)], 6, a=1)
    P.rect(-10, 1120, W + 10, 1420, WALK, 6)
    for x in range(0, W, 180): P.line([(x, 1120), (x, 1420)], 4, (150, 146, 140), 1.2)
    P.line([(0, 1270), (W, 1270)], 4, (150, 146, 140), 1.2)
    P.rect(-10, 1420, W + 10, 1460, (236, 234, 228), 6)
    d.rectangle((0, 1460, W, H), fill=ROAD)
    for x in range(-60, W, 200): P.rect(x + 40, 1640, x + 150, 1656, (245, 245, 245), 3)
    # tree (left) and bus-stop sign (right)
    P.rect(108, 760, 148, 1150, TRUNK, 6)
    tp = [(128 + math.cos(a) * (150 + 14 * math.sin(a * 7)), 640 + math.sin(a) * (150 + 14 * math.sin(a * 7))) for a in np.linspace(0, 2 * math.pi, 50, endpoint=False)]
    P.poly(tp, TREE, 7)
    P.line([(940, 760), (940, 1330)], 9, (110, 114, 120)); P.rect(870, 640, 1010, 770, (255, 255, 255), 6)
    P.rect(895, 680, 985, 728, BUS, 4); P.ell(915, 734, 8, 8, INK, 3); P.ell(965, 734, 8, 8, INK, 3)
    P.rect(905, 800, 975, 880, (255, 255, 255), 5)
    for k in range(3): P.line([(918, 822 + k * 18), (962, 822 + k * 18)], 3)

def hair(P, cx, cy, r):
    pts = []
    n = 26
    for i in range(n + 1):
        a = math.pi + i / n * math.pi
        rr = r * (1.12 if i % 2 else 1.32)
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr * .95 + 6))
    pts += [(cx + r * .95, cy + 18), (cx + r * .55, cy - r * .55), (cx, cy - r * .62), (cx - r * .55, cy - r * .5), (cx - r * .95, cy + 18)]
    P.poly(pts, HAIR, 6)

def person(P, x, y, t, pose="idle", face="smile", run=0.0):
    """x,y = feet centre on ground"""
    hip = (x, y - 170); neck = (x, y - 330); head = (x, y - 430); r = 92
    sw = math.sin(t * 14) * run
    P.line([hip, (x - 40 - 30 * sw, y)], 8); P.line([hip, (x + 40 + 30 * sw, y)], 8)
    for fx in (x - 40 - 30 * sw, x + 40 + 30 * sw): P.ell(fx, y + 4, 24, 12, INK, 3)
    P.line([neck, hip], 8)
    sh = (x, y - 300)
    if pose == "idle": A = [((x - 70, y - 220), (x - 90, y - 160)), ((x + 70, y - 220), (x + 90, y - 160))]
    elif pose == "run": A = [((x - 70, y - 250 - 40 * sw), (x - 140, y - 330 - 60 * sw)), ((x + 80, y - 240 + 40 * sw), (x + 150, y - 300))]
    elif pose == "reach": A = [((x - 70, y - 220), (x - 90, y - 160)), ((x + 90, y - 360), (x + 150, y - 470))]
    elif pose == "sad": A = [((x - 50, y - 210), (x - 60, y - 150)), ((x + 50, y - 210), (x + 60, y - 150))]
    elif pose == "happy": A = [((x - 110, y - 380), (x - 150, y - 480)), ((x + 110, y - 380), (x + 150, y - 480))]
    else: A = [((x - 120, y - 230), (x - 70, y - 300)), ((x + 120, y - 230), (x + 70, y - 300))]       # thumbs
    for el, hand in A:
        P.line([sh, el, hand], 8)
        if pose == "thumbs":
            P.ell(hand[0], hand[1], 22, 20, SKIN, 5); P.ell(hand[0], hand[1] - 18, 9, 9, SKIN, 4)
        else: P.ell(hand[0], hand[1], 14, 14, SKIN, 5)
    P.ell(head[0], head[1], r, r * 1.02, SKIN, 7)
    hair(P, head[0], head[1], r)
    ex, ey = head[0], head[1] + 8
    if face in ("smile", "happy", "neutral"):
        for k in (-1, 1): P.ell(ex + k * 32, ey, 9, 11, INK, 2)
    if face == "shock":
        for k in (-1, 1): P.ell(ex + k * 32, ey - 4, 15, 17, (255, 255, 255), 5); P.ell(ex + k * 32, ey - 2, 6, 6, INK, 2)
        P.ell(ex, ey + 50, 16, 20, INK, 3)
    elif face == "sad":
        for k in (-1, 1): P.line([(ex + k * 32 - 14, ey - 4 - k * 4), (ex + k * 32 + 14, ey - 4 + k * 4)], 6)
        P.line([(ex - 28, ey + 58), (ex, ey + 44), (ex + 28, ey + 58)], 6)
        tear = (t * 1.6) % 1; P.ell(ex - 40, ey + 20 + tear * 40, 7, 10, (90, 160, 230), 3)
    elif face == "happy":
        P.line([(ex - 38, ey + 38), (ex - 18, ey + 60), (ex + 18, ey + 60), (ex + 38, ey + 38)], 6)
        for k in (-1, 1): P.ell(ex + k * 58, ey + 30, 14, 9, (250, 170, 170), 0)
    elif face == "smile": P.line([(ex - 26, ey + 42), (ex, ey + 54), (ex + 26, ey + 42)], 6)
    else: P.line([(ex - 20, ey + 50), (ex + 20, ey + 50)], 6)

def cat(P, x, y, t):
    s = math.sin(t * 16)
    P.ell(x, y - 70, 70, 36, INK, 5)
    for k, ph in ((-45, 1), (-20, -1), (25, 1), (50, -1)): P.line([(x + k, y - 50), (x + k + 12 * s * ph, y)], 9)
    P.ell(x + 78, y - 108, 32, 30, INK, 5)
    P.poly([(x + 58, y - 128), (x + 66, y - 160), (x + 80, y - 132)], INK, 4); P.poly([(x + 84, y - 132), (x + 98, y - 160), (x + 104, y - 126)], INK, 4)
    for k in (-1, 1): P.ell(x + 78 + k * 12, y - 112, 5, 6, (240, 220, 80), 0)
    P.line([(x - 66, y - 80), (x - 110, y - 130 + 10 * s), (x - 96, y - 170)], 9)

def bus(P, x, y):
    P.rect(x, y - 300, x + 620, y - 40, BUS, 8)
    for k in range(4): P.rect(x + 40 + k * 140, y - 260, x + 150 + k * 140, y - 170, (190, 228, 245), 6)
    P.rect(x + 560, y - 260, x + 610, y - 120, (190, 228, 245), 6)
    P.line([(x, y - 140), (x + 620, y - 140)], 5)
    for wx in (x + 120, x + 490): P.ell(wx, y - 40, 46, 46, (60, 60, 66), 6); P.ell(wx, y - 40, 16, 16, (200, 200, 200), 4)
    f = FI(46); P.d.text((x + 230, y - 128), "BUS", font=f, fill=INK)
    for k in range(4): P.line([(x - 40 - k * 30, y - 250 + k * 50), (x - 160 - k * 30, y - 250 + k * 50)], 5)

def rain_cloud(P, cx, cy, t):
    cloud(P, cx, cy, 1.25, (120, 126, 140))
    for k in range(9):
        dx = -90 + k * 22; ph = (t * 2.4 + k * .37) % 1
        y0 = cy + 45 + ph * 150; P.line([(cx + dx * 1.2, y0), (cx + dx * 1.2 - 8, y0 + 34)], 5, (70, 140, 220), 1)

def pig(P, x, y, t, clover=True):
    s = math.sin(t * 12)
    for k, ph in ((-55, 1), (-25, -1), (35, 1), (65, -1)): P.line([(x + k, y - 60), (x + k + 10 * s * ph, y)], 12, PIGD)
    P.ell(x, y - 110, 110, 72, PIG, 7)
    P.line([(x - 108, y - 120), (x - 135, y - 140), (x - 128, y - 160), (x - 112, y - 148)], 5)
    P.ell(x + 110, y - 160, 62, 58, PIG, 7)
    P.poly([(x + 72, y - 205), (x + 70, y - 250), (x + 104, y - 214)], PIGD, 5); P.poly([(x + 120, y - 214), (x + 150, y - 248), (x + 152, y - 204)], PIGD, 5)
    P.ell(x + 160, y - 148, 26, 20, PIGD, 5)
    for k in (-1, 1): P.ell(x + 160 + k * 9, y - 148, 4, 6, INK, 0)
    for k in (-1, 1): P.ell(x + 108 + k * 22, y - 176, 7, 9, INK, 2)
    if clover:
        cx, cy = x + 196, y - 196
        P.line([(x + 168, y - 126), (cx, cy)], 6, (40, 130, 60))
        for a in range(4):
            ang = a * math.pi / 2 + math.pi / 4; P.ell(cx + math.cos(ang) * 22, cy + math.sin(ang) * 22, 20, 20, (70, 180, 90), 5)

def paper_scrap(lines, w=900, rot=0.0):
    """notebook-paper caption card: squared paper, red margin, torn top edge, ink border"""
    fonts = [(FI(l[1], l[2]) if l[3] == "inter" else FH(l[1]), l) for l in lines]
    rows = []
    for f, (txt, size, weight, kind, col) in fonts:
        words, cur = txt.split(), ""
        for wd in words:
            tt = (cur + " " + wd).strip()
            if f.getlength(tt) <= w - 110 or not cur: cur = tt
            else: rows.append((f, cur, col)); cur = wd
        rows.append((f, cur, col))
    h = sum(f.size + 18 for f, _, _ in rows) + 70
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    r = np.random.default_rng(7)
    top = [(x, 14 + r.uniform(-6, 6)) for x in range(0, w + 1, 30)]
    poly = top + [(w, h), (0, h)]
    d.polygon(poly, fill=(253, 252, 247))
    mask = Image.new("L", (w, h), 0); ImageDraw.Draw(mask).polygon(poly, fill=255)
    grid = Image.new("RGBA", (w, h), (0, 0, 0, 0)); g = ImageDraw.Draw(grid)
    for y in range(0, h, 40): g.line((0, y, w, y), fill=(150, 190, 235, 110), width=2)
    for x in range(0, w, 40): g.line((x, 0, x, h), fill=(150, 190, 235, 110), width=2)
    g.line((60, 0, 60, h), fill=(230, 90, 90, 190), width=3)
    im.paste(grid, (0, 0), Image.composite(grid, Image.new("RGBA", (w, h)), mask).getchannel("A"))
    d.line(poly + [poly[0]], fill=INK, width=6, joint="curve")
    y = 44
    for f, txt, col in rows:
        d.text(((w - f.getlength(txt)) / 2 + 20, y), txt, font=f, fill=col); y += f.size + 18
    if rot: im = im.rotate(rot, expand=True, resample=Image.BICUBIC)
    sh = Image.new("RGBA", (im.width + 40, im.height + 40), (0, 0, 0, 0)); sh.paste((0, 0, 0, 90), (20, 30), im.getchannel("A"))
    sh = sh.filter(ImageFilter.GaussianBlur(10)); sh.alpha_composite(im, (20, 16)); return sh

RED, BLUE = (200, 40, 45), (34, 74, 160)
SIGN = paper_scrap([("ПʼЯТНИЦЯ, 13-ТЕ", 64, "Black", "inter", INK)], 640, -1.5)
CARDS = {
    "hook": (0.35, C1 - .25, paper_scrap([("Як німці кажуть,", 58, "Black", "inter", INK), ("коли не щастить?", 58, "Black", "inter", RED)], 900, 1)),
    "c1": (C1, T_RAIN + .9, paper_scrap([("Pech gehabt!", 96, "", "hand", BLUE), ("Не пощастило!", 54, "Black", "inter", INK), ("das Pech — це ще й «смола»", 40, "SemiBold", "inter", (95, 100, 115))], 900, -1)),
    "c2": (C2, T_PIG + .8, paper_scrap([("So ein Pech!", 96, "", "hand", BLUE), ("Ну й невезіння!", 54, "Black", "inter", INK)], 900, 1)),
    "c3": (C3, T_THUMB - .1, paper_scrap([("Schwein gehabt!", 96, "", "hand", BLUE), ("Пощастило!", 58, "Black", "inter", INK), ("дослівно: «мав свиню»", 40, "SemiBold", "inter", (95, 100, 115))], 900, -1)),
    "c4": (C4, BODY, paper_scrap([("Ich drücke dir", 84, "", "hand", BLUE), ("die Daumen!", 84, "", "hand", BLUE), ("Тримаю за тебе кулаки!", 52, "Black", "inter", INK), ("німці «тиснуть великі пальці»", 38, "SemiBold", "inter", (95, 100, 115))], 900, 1)),
}
SERIES = FC.series_tag("Мультик у зошиті · №1")
FOLLOW = FC.make({"follow": {"line1": "Завтра — мультик №2", "line2": "нова історія німецькою в зошиті", "like": "лайк, якщо тобі сьогодні пощастило"}})

def person_state(t):
    if t < T_BUS: return 470, "idle", ("smile" if t < T_CAT + .3 else "shock"), 0
    if t < C1 + .6: return 470 + 150 * ease(seg(t, T_BUS + .2, T_BUS + 1.2)), "run", "shock", 1
    if t < T_RAIN: return 620, "sad", "sad", 0
    if t < T_PIG + 1.4: return 620 - 150 * ease(seg(t, T_RAIN - .6, T_RAIN + .2)), "sad", "sad", 0
    if t < T_THUMB: return 470, "happy", "happy", 0
    return 470, "thumbs", "smile", 0

def render(t):
    im = Image.new("RGB", (W, H), SKY); d = ImageDraw.Draw(im)
    P = Pen(d, int(t * FPS) // 4)
    background(P, t)
    if T_RAIN - .2 <= t < T_PIG + 1.5:                                  # rain cloud follows only him
        k = seg(t, T_RAIN - .2, T_RAIN + .5); out = seg(t, T_PIG + .8, T_PIG + 1.5)
        rain_cloud(P, 470 - 700 * (1 - ease(k)) + 800 * ease(out), 640, t)
    x, pose, face, run = person_state(t)
    person(P, x, 1300, t, pose, face, run)
    if T_CAT <= t < T_BUS + .4:                                         # black cat crosses
        p = seg(t, T_CAT, T_BUS + .4); cat(P, -160 + p * (W + 340), 1400, t)
    if T_BUS <= t < C1 + .3:
        p = seg(t, T_BUS, C1 + .3); bus(P, -700 + p * (W + 900), 1440)
    if T_PIG <= t:
        p = ease(seg(t, T_PIG, T_PIG + 1.6)); pig(P, -260 + p * 470, 1410, t, clover=t < T_THUMB + .2)
    frame = im.convert("RGBA")
    s = .6 + .4 * back(seg(t, .05, .4)); sg = SIGN.resize((int(SIGN.width * s), int(SIGN.height * s)), Image.BICUBIC)
    frame.alpha_composite(sg, ((W - sg.width) // 2, 36))
    frame.alpha_composite(SERIES, ((W - SERIES.width) // 2, 36 + SIGN.height - 20))
    for key, (a, b, card) in CARDS.items():
        if a <= t < b:
            p = seg(t, a, a + .35); s = .55 + .45 * back(p); c = card.resize((max(1, int(card.width * s)), max(1, int(card.height * s))), Image.BICUBIC)
            frame.alpha_composite(c, ((W - c.width) // 2, 1690 - c.height // 2 if key != "c4" else 1660 - c.height // 2))
    if t >= BODY:
        dim = Image.new("RGBA", (W, H), (0, 0, 0, int(110 * seg(t, BODY, BODY + .4)))); frame.alpha_composite(dim)
        FC.draw_end(frame, t, BODY + .3, FOLLOW, 1050)
    return frame.convert("RGB")

def audio(path):
    CA.build(path, DUR, ticks=[], dings=[C1, C2, C3, C4, BODY + .3])

if __name__ == "__main__":
    if sys.argv[1] == "preview":
        out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
        for s in sys.argv[3:]: render(float(s)).save(out / f"ink_{float(s):06.2f}.jpg", quality=88)
        print("ok", DUR)
    else:
        work = Path(tempfile.mkdtemp()); (work / "f").mkdir()
        for k in range(int(DUR * FPS)): render(k / FPS).save(work / "f" / f"{k:05d}.jpg", quality=92)
        audio(str(work / "a.wav"))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", str(work / "f" / "%05d.jpg"), "-i", str(work / "a.wav"), "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", f"{DUR:.2f}", sys.argv[1]], check=True)
        subprocess.run(["rm", "-rf", str(work)]); print("ok", sys.argv[1], DUR)
