"""Paper-quiz reel: top-down notebook sheet, printed questions, a pencil underlines the question,
5-second timer with ticks, green check on the right answer, paper slides up to the next question.
Based on the Oct-Nov 2026 outlier format (paper quiz with pen + countdown).
usage: CFG=cfg.json python3 paper_quiz.py out.mp4   |   CFG=cfg.json python3 paper_quiz.py preview dir t1 t2 ...
cfg: header, sub, questions[{q:[lines], options:[3], answer:idx}], outro, read (s), count (s), reveal (s)
"""
import json, math, os, subprocess, sys, tempfile, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS, SR = 1080, 1920, 30, 44100
CFG = json.load(open(os.environ["CFG"], encoding="utf-8"))
QS = CFG["questions"]
READ, COUNT, REVEAL = CFG.get("read", 2.2), CFG.get("count", 5.0), CFG.get("reveal", 1.9)
QD = READ + COUNT + REVEAL
OUTRO = CFG.get("outro_dur", 2.6)
DUR = len(QS) * QD + OUTRO
FD = "/usr/share/fonts/opentype/inter/"
F = lambda n, w="Bold": ImageFont.truetype(f"{FD}InterDisplay-{w}.otf", n)
INK, RED, GREEN, BLUE = (28, 30, 38), (214, 48, 49), (34, 160, 90), (150, 190, 235)

def clamp(x, a=0., b=1.): return max(a, min(b, x))
def seg(t, a, b): return clamp((t - a) / (b - a))
def ease(p): return 4 * p ** 3 if p < .5 else 1 - (-2 * p + 2) ** 3 / 2

# ---------------------------------------------------------------- desk
rng = np.random.default_rng(4)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
desk = np.zeros((H, W, 3), np.float32); desk[:] = (92, 64, 44)
desk += (np.sin(xx * .012 + np.sin(yy * .003) * 4) * 9 + np.sin(xx * .09) * 3 + rng.normal(0, 2.5, (H, W)))[..., None]
DESK = Image.fromarray(np.clip(desk, 0, 255).astype(np.uint8)).convert("RGBA")

# ---------------------------------------------------------------- paper (notebook sheet, taller than the screen)
PW, MX = 980, 96                       # paper width, left text margin
BLOCK = 600                            # vertical space per question
TOP = 300                              # first question top inside the paper
PH = TOP + BLOCK * len(QS) + 900
paper = Image.new("RGBA", (PW, PH), (253, 252, 247, 255)); d = ImageDraw.Draw(paper)
for y in range(0, PH, 48): d.line((0, y, PW, y), fill=BLUE + (120,), width=2)
for x in range(0, PW, 48): d.line((x, 0, x, PH), fill=BLUE + (120,), width=2)
d.line((70, 0, 70, PH), fill=(230, 90, 90, 200), width=4)
LAY = []                               # per question: underline segments, option rows
for i, q in enumerate(QS):
    y = TOP + i * BLOCK; fq = F(60, "ExtraBold"); under = []
    for li, line in enumerate(q["q"]):
        txt = (f"{i + 1}) " if li == 0 else "    ") + line
        d.text((MX, y), txt, font=fq, fill=INK); w = d.textlength(txt, font=fq)
        under.append((MX, y + 76, MX + w)); y += 84
    y += 34; rows = []
    for oi, o in enumerate(q["options"]):
        txt = "ABC"[oi] + ")  " + o; fo = F(58, "SemiBold")
        d.text((MX + 40, y), txt, font=fo, fill=INK); rows.append((MX + 40, y, d.textlength(txt, font=fo))); y += 96
    LAY.append(dict(under=under, rows=rows, top=TOP + i * BLOCK))
PAPER = paper
PX = (W - PW) // 2
def scroll_at(t):
    """paper y so that the active question sits at screen y=430"""
    i = min(int(t // QD), len(QS) - 1); cur = 430 - LAY[i]["top"]
    if i > 0:
        prev = 430 - LAY[i - 1]["top"]; p = ease(seg(t, i * QD - .15, i * QD + .45)); return prev + (cur - prev) * p
    return cur

# ---------------------------------------------------------------- pencil sprite (tip at origin, pointing up-left)
def make_pencil():
    L, T = 620, 44; S = 3
    im = Image.new("RGBA", ((L + 80) * S, (T + 40) * S), (0, 0, 0, 0)); dd = ImageDraw.Draw(im)
    y0, y1 = 20 * S, (20 + T) * S; x0 = 10 * S
    dd.polygon([(x0, (y0 + y1) // 2), (x0 + 70 * S, y0), (x0 + 70 * S, y1)], fill=(232, 196, 150))
    dd.polygon([(x0, (y0 + y1) // 2), (x0 + 22 * S, y0 + 15 * S), (x0 + 22 * S, y1 - 15 * S)], fill=(40, 40, 46))
    dd.rectangle((x0 + 70 * S, y0, x0 + (L - 70) * S, y1), fill=(245, 150, 40))
    dd.rectangle((x0 + 70 * S, y0, x0 + (L - 70) * S, y0 + 12 * S), fill=(255, 184, 84))
    dd.rectangle((x0 + 70 * S, y1 - 10 * S, x0 + (L - 70) * S, y1), fill=(210, 118, 24))
    dd.rectangle((x0 + (L - 70) * S, y0, x0 + (L - 30) * S, y1), fill=(190, 194, 204))
    dd.rounded_rectangle((x0 + (L - 30) * S, y0, x0 + (L + 20) * S, y1), 10 * S, fill=(236, 130, 140))
    im = im.resize((im.width // S, im.height // S), Image.LANCZOS)
    ang = -52; rot = im.rotate(ang, expand=True, resample=Image.BICUBIC)
    # tip position after rotation
    cx, cy = im.width / 2, im.height / 2; tx, ty = 10 - cx, (20 + T / 2) - cy; a = math.radians(-ang)
    rx = tx * math.cos(a) - ty * math.sin(a) + rot.width / 2; ry = tx * math.sin(a) + ty * math.cos(a) + rot.height / 2
    sh = Image.new("RGBA", rot.size, (0, 0, 0, 0)); sh.putalpha(rot.getchannel("A").filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * .38)))
    return rot, sh, (rx, ry)
PENCIL, PSH, PTIP = make_pencil()

def sticker(lines, fill, fg=INK, pad=(34, 20), rot=0):
    fs = [F(s, w) for _, s, w in lines]; ws = [f.getlength(t) for (t, _, _), f in zip(lines, fs)]
    w = int(max(ws)) + pad[0] * 2; h = sum(f.size + 14 for f in fs) + pad[1] * 2 - 14
    im = Image.new("RGBA", (w, h), fill + (255,)); dd = ImageDraw.Draw(im); y = pad[1]
    for (t, _, _), f, tw in zip(lines, fs, ws): dd.text(((w - tw) / 2, y), t, font=f, fill=fg); y += f.size + 14
    if rot: im = im.rotate(rot, expand=True, resample=Image.BICUBIC)
    sh = Image.new("RGBA", (im.width + 40, im.height + 40), (0, 0, 0, 0))
    sh.paste((0, 0, 0, 90), (20, 26), im.getchannel("A")); sh = sh.filter(ImageFilter.GaussianBlur(10)); sh.alpha_composite(im, (20, 16)); return sh
HEAD = sticker([(CFG["header"], 62, "Black"), (CFG["sub"], 46, "SemiBold")], (255, 214, 70), rot=-1.5)
OUT = sticker([(l, 64, "Black") for l in CFG["outro"]], (255, 214, 70), rot=2)

def render(t):
    fr = DESK.copy(); sy = scroll_at(t)
    i = min(int(t // QD), len(QS) - 1); tq = t - i * QD; outro = t >= len(QS) * QD
    if outro: tq = QD
    pg = PAPER.copy(); d = ImageDraw.Draw(pg)
    tip = None
    for j in range(i + 1):                                   # marks: past questions complete, current animated
        L = LAY[j]; tt = QD if j < i else tq
        n = len(L["under"])                                  # red underline while "reading"
        for k, (x0, yu, x1) in enumerate(L["under"]):
            p = seg(tt, .15 + k * (READ - .3) / n, .15 + (k + 1) * (READ - .3) / n)
            if p > 0:
                d.line((x0, yu, x0 + (x1 - x0) * p, yu), fill=RED + (255,), width=7)
                if j == i and 0 < p < 1: tip = (x0 + (x1 - x0) * p, yu)
        a = QS[j]["answer"]; x, y, w = L["rows"][a]
        p = seg(tt, READ + COUNT + .05, READ + COUNT + .5)   # reveal: highlight + check
        if p > 0:
            hl = Image.new("RGBA", pg.size, (0, 0, 0, 0)); ImageDraw.Draw(hl).rounded_rectangle((x - 14, y - 4, x - 14 + (w + 28) * p, y + 78), 14, fill=(120, 230, 150, 110)); pg.alpha_composite(hl); d = ImageDraw.Draw(pg)
            pts = [(x - 92, y + 38), (x - 70, y + 62), (x - 30, y + 6)]; q = p * 2
            if q <= 1: e = (pts[0][0] + (pts[1][0] - pts[0][0]) * q, pts[0][1] + (pts[1][1] - pts[0][1]) * q); d.line([pts[0], e], fill=GREEN + (255,), width=12)
            else:
                e = (pts[1][0] + (pts[2][0] - pts[1][0]) * (q - 1), pts[1][1] + (pts[2][1] - pts[1][1]) * (q - 1)); d.line([pts[0], pts[1], e], fill=GREEN + (255,), width=12, joint="curve")
            if j == i and p < 1: tip = e
    L = LAY[i]
    if tip is None:                                          # resting / moving pencil
        rest = (L["rows"][1][0] + 620, L["rows"][1][1] + 150)
        a = QS[i]["answer"]; x, y, w = L["rows"][a]
        if tq < .15: tip = rest
        elif tq < READ + COUNT - .5: tip = rest
        elif tq < READ + COUNT + .05:
            p = ease(seg(tq, READ + COUNT - .5, READ + COUNT + .05)); tip = (rest[0] + (x - 92 - rest[0]) * p, rest[1] + (y + 38 - rest[1]) * p)
        else:
            p = ease(seg(tq, READ + COUNT + .5, READ + COUNT + 1.0)); tip = (x - 30 + (rest[0] - (x - 30)) * p, y + 6 + (rest[1] - (y + 6)) * p)
    # paper with shadow
    vis = pg.crop((0, int(-sy) if sy < 0 else 0, PW, int(-sy) + H if sy < 0 else H - int(sy)))
    py = max(0, int(sy)); shadow = Image.new("RGBA", (PW + 60, vis.height + 60), (0, 0, 0, 0)); shadow.paste((0, 0, 0, 110), (30, 36, 30 + PW, 36 + vis.height)); fr.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(16)), (PX - 30, py - 30)); fr.alpha_composite(vis, (PX, py))
    # timer
    if not outro and READ <= tq < READ + COUNT + .25:
        left = COUNT - (tq - READ); cx, cy, r = 905, 300 + 0 * 0, 92
        dd = ImageDraw.Draw(fr); pulse = 1 + .06 * (1 - (left % 1)) if left > 0 else 1.1
        rr = r * pulse; dd.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=(255, 255, 255, 255), outline=INK + (255,), width=8)
        dd.arc((cx - rr + 14, cy - rr + 14, cx + rr - 14, cy + rr - 14), -90, -90 + 360 * clamp(left / COUNT), fill=(RED if left <= 2 else GREEN) + (255,), width=14)
        num = str(max(0, math.ceil(left))); f = F(96, "Black"); tw = f.getlength(num); dd.text((cx - tw / 2, cy - 60), num, font=f, fill=INK)
    # pencil
    sx, sy2 = PX + tip[0], sy + tip[1]
    fr.alpha_composite(PSH, (int(sx - PTIP[0] + 26), int(sy2 - PTIP[1] + 30))); fr.alpha_composite(PENCIL, (int(sx - PTIP[0]), int(sy2 - PTIP[1])))
    fr.alpha_composite(HEAD, ((W - HEAD.width) // 2, 40))
    if outro:
        p = seg(t, len(QS) * QD + .1, len(QS) * QD + .5); s = .6 + .4 * (1 + 2.7 * (p - 1) ** 3 + 1.7 * (p - 1) ** 2)
        o = OUT.resize((max(1, int(OUT.width * s)), max(1, int(OUT.height * s))), Image.BICUBIC); fr.alpha_composite(o, ((W - o.width) // 2, 1180 - o.height // 2))
    return fr.convert("RGB")

# ---------------------------------------------------------------- audio: ticks, ding, pencil scratch, soft bed
def audio(path):
    n = int(DUR * SR); a = np.zeros(n + SR); r = np.random.default_rng(2)
    def add(sig, t, g=1.):
        i = int(t * SR); j = min(len(a), i + len(sig)); a[i:j] += sig[: j - i] * g
    tt = np.arange(int(.06 * SR)) / SR; tick = np.sin(2 * np.pi * 1900 * tt) * np.exp(-tt * 90) + .5 * np.sin(2 * np.pi * 950 * tt) * np.exp(-tt * 70)
    td = np.arange(int(.9 * SR)) / SR; ding = (np.sin(2 * np.pi * 1046 * td) + .6 * np.sin(2 * np.pi * 1568 * td) + .3 * np.sin(2 * np.pi * 2093 * td)) * np.exp(-td * 5)
    def scratch(dur):
        m = int(dur * SR); x = r.normal(0, 1, m); x = np.convolve(x, np.ones(6) / 6, "same") - np.convolve(x, np.ones(60) / 60, "same")
        env = (.6 + .4 * np.sin(np.arange(m) / SR * 2 * np.pi * 9)) * np.minimum(1, np.arange(m) / (.03 * SR)) * np.minimum(1, (m - np.arange(m)) / (.05 * SR)); return x * env
    def whoosh(dur=.5):
        m = int(dur * SR); x = np.convolve(r.normal(0, 1, m), np.ones(40) / 40, "same"); return x * np.sin(np.linspace(0, np.pi, m)) ** 2
    for i in range(len(QS)):
        t0 = i * QD
        if i: add(whoosh(), t0 - .15, .5)
        add(scratch(READ - .3), t0 + .15, .16)
        for k in range(int(COUNT)): add(tick, t0 + READ + k, .5 if k < COUNT - 2 else .75)
        add(ding, t0 + READ + COUNT, .34); add(scratch(.42), t0 + READ + COUNT + .05, .2)
    add(ding, len(QS) * QD + .1, .25)
    # soft bed: two-note pulse so the video is not silent between ticks
    tb = np.arange(len(a)) / SR; bed = .05 * np.sin(2 * np.pi * 110 * tb) * (0.6 + .4 * np.sin(2 * np.pi * .5 * tb)) + .03 * np.sin(2 * np.pi * 164.8 * tb)
    a = (a + bed)[:n]; a = a / max(1e-6, np.abs(a).max()) * .85
    fade = np.minimum(1, (n - np.arange(n)) / (.25 * SR)); a *= fade
    with wave.open(path, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((a * 32767).astype(np.int16).tobytes())

if __name__ == "__main__":
    if sys.argv[1] == "preview":
        out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
        for s in sys.argv[3:]: render(float(s)).save(out / f"pq_{float(s):06.2f}.jpg", quality=88)
        print("ok", DUR)
    else:
        work = Path(tempfile.mkdtemp()); (work / "f").mkdir()
        for k in range(int(DUR * FPS)): render(k / FPS).save(work / "f" / f"{k:05d}.jpg", quality=92)
        audio(str(work / "a.wav"))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", str(work / "f" / "%05d.jpg"), "-i", str(work / "a.wav"), "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", "-t", f"{DUR:.2f}", sys.argv[1]], check=True)
        subprocess.run(["rm", "-rf", str(work)]); print("ok", sys.argv[1], DUR)
