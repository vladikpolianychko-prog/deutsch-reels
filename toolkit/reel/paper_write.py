"""Paper-write reel: top-down notebook sheet with printed lines; after a short countdown the pencil
strikes the wrong part (optional) and handwrites the answer under each line. One engine, two formats:
 - "red pen" (find the mistake): rows[{print, strike, write}]
 - "A2 -> B2" (say it stronger): rows[{print, write}] with tag_print/tag_write pills
usage: CFG=cfg.json python3 paper_write.py out.mp4   |   CFG=cfg.json python3 paper_write.py preview dir t1 t2 ...
cfg: header, sub, rows[], outro[], think (s), write (s), hold (s), ink ("red"|"blue"|"green"), tag_print, tag_write
"""
import json, math, os, subprocess, sys, tempfile, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS, SR = 1080, 1920, 30, 44100
CFG = json.load(open(os.environ["CFG"], encoding="utf-8"))
ROWS = CFG["rows"]
THINK, WRITE, HOLD = CFG.get("think", 3.0), CFG.get("write", 1.3), CFG.get("hold", 1.0)
RD = THINK + WRITE + HOLD
INTRO = CFG.get("intro", 0.4)
OUTRO = CFG.get("outro_dur", 2.6)
DUR = INTRO + len(ROWS) * RD + OUTRO
FD = "/usr/share/fonts/opentype/inter/"
HAND = str(Path(__file__).resolve().parent / "bg/fonts/ComicRelief-Regular.ttf")
F = lambda n, w="Bold": ImageFont.truetype(f"{FD}InterDisplay-{w}.otf", n)
INK, RED, GREEN, BLUE = (28, 30, 38), (214, 48, 49), (34, 160, 90), (150, 190, 235)
PEN = {"red": RED, "blue": (38, 78, 168), "green": (30, 140, 80)}[CFG.get("ink", "red")]

def clamp(x, a=0., b=1.): return max(a, min(b, x))
def seg(t, a, b): return clamp((t - a) / (b - a))
def ease(p): return 4 * p ** 3 if p < .5 else 1 - (-2 * p + 2) ** 3 / 2

rng = np.random.default_rng(4)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
desk = np.zeros((H, W, 3), np.float32); desk[:] = (92, 64, 44)
desk += (np.sin(xx * .012 + np.sin(yy * .003) * 4) * 9 + np.sin(xx * .09) * 3 + rng.normal(0, 2.5, (H, W)))[..., None]
DESK = Image.fromarray(np.clip(desk, 0, 255).astype(np.uint8)).convert("RGBA")

# ---------------------------------------------------------------- paper (fixed, all rows visible)
PW, PH, PX, PY, MX = 980, 1660, 50, 230, 104
TOP = CFG.get("top", 110)
BLOCK = CFG.get("block", min(255, (PH - TOP - 60) // len(ROWS)))
paper = Image.new("RGBA", (PW, PH), (253, 252, 247, 255)); d = ImageDraw.Draw(paper)
for y in range(0, PH, 48): d.line((0, y, PW, y), fill=BLUE + (120,), width=2)
for x in range(0, PW, 48): d.line((x, 0, x, PH), fill=BLUE + (120,), width=2)
d.line((70, 0, 70, PH), fill=(230, 90, 90, 200), width=4)

def pill(dd, x, y, txt, fill):
    f = F(34, "Black"); w = f.getlength(txt) + 28
    dd.rounded_rectangle((x, y, x + w, y + 50), 14, fill=fill); dd.text((x + 14, y + 5), txt, font=f, fill=(255, 255, 255)); return w + 16

def hand(txt, size, col, maxw):
    f = ImageFont.truetype(HAND, size)
    while f.getlength(txt) > maxw and size > 36: size -= 2; f = ImageFont.truetype(HAND, size)
    im = Image.new("RGBA", (int(f.getlength(txt)) + 24, int(size * 1.5)), (0, 0, 0, 0)); dd = ImageDraw.Draw(im)
    dd.text((8, 4), txt, font=f, fill=col + (255,), stroke_width=1, stroke_fill=col + (255,)); return im

LAY = []
TP, TW = CFG.get("tag_print"), CFG.get("tag_write")
for i, r in enumerate(ROWS):
    y = TOP + i * BLOCK; x = MX
    num = f"{i + 1})"; fn = F(54, "Black"); d.text((x, y + 4), num, font=fn, fill=(120, 126, 140)); x += int(fn.getlength(num)) + 22
    if TP: x += int(pill(d, x, y + 10, TP, (120, 126, 140)))
    size = 58; fp = F(size, "ExtraBold")
    while fp.getlength(r["print"]) > PW - x - 30 and size > 36: size -= 2; fp = F(size, "ExtraBold")
    d.text((x, y), r["print"], font=fp, fill=INK)
    strike = None
    if r.get("strike"):
        k = r["print"].index(r["strike"]); x0 = x + fp.getlength(r["print"][:k]); strike = (x0 - 6, y + size * .62, x0 + fp.getlength(r["strike"]) + 6)
    wx = MX + int(fn.getlength(num)) + 22; wy = y + 104
    if TW: tagw = int(F(34, "Black").getlength(TW)) + 44
    else: tagw = 0
    sp = hand(r["write"], CFG.get("hand_size", 68), PEN, PW - wx - tagw - 30)
    LAY.append(dict(strike=strike, sp=sp, wx=wx + tagw, wy=wy, tagx=wx, y=y, rest=(PW - 150, y + 250)))
PAPER = paper

def make_pencil():
    L, T = 620, 44; S = 3
    im = Image.new("RGBA", ((L + 80) * S, (T + 40) * S), (0, 0, 0, 0)); dd = ImageDraw.Draw(im)
    y0, y1 = 20 * S, (20 + T) * S; x0 = 10 * S
    body = {"red": (206, 52, 52), "blue": (52, 96, 190), "green": (40, 150, 90)}[CFG.get("ink", "red")]
    hi = tuple(min(255, c + 40) for c in body); lo = tuple(max(0, c - 40) for c in body)
    dd.polygon([(x0, (y0 + y1) // 2), (x0 + 70 * S, y0), (x0 + 70 * S, y1)], fill=(232, 196, 150))
    dd.polygon([(x0, (y0 + y1) // 2), (x0 + 22 * S, y0 + 15 * S), (x0 + 22 * S, y1 - 15 * S)], fill=PEN)
    dd.rectangle((x0 + 70 * S, y0, x0 + (L - 70) * S, y1), fill=body)
    dd.rectangle((x0 + 70 * S, y0, x0 + (L - 70) * S, y0 + 12 * S), fill=hi)
    dd.rectangle((x0 + 70 * S, y1 - 10 * S, x0 + (L - 70) * S, y1), fill=lo)
    dd.rectangle((x0 + (L - 70) * S, y0, x0 + (L - 30) * S, y1), fill=(190, 194, 204))
    dd.rounded_rectangle((x0 + (L - 30) * S, y0, x0 + (L + 20) * S, y1), 10 * S, fill=(236, 130, 140))
    im = im.resize((im.width // S, im.height // S), Image.LANCZOS)
    ang = -52; rot = im.rotate(ang, expand=True, resample=Image.BICUBIC)
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
HEAD = sticker([(CFG["header"], 60, "Black"), (CFG["sub"], 44, "SemiBold")], (255, 214, 70), rot=-1.5)
OUT = sticker([(l, 62, "Black") for l in CFG["outro"]], (255, 214, 70), rot=2)
SW = .35 if any(r.get("strike") for r in ROWS) else 0.0          # time used by the strike inside WRITE

def render(t):
    fr = DESK.copy(); tt = t - INTRO
    i = int(clamp(tt // RD, 0, len(ROWS) - 1)); tq = tt - i * RD; outro = tt >= len(ROWS) * RD
    if outro: tq = RD
    if tt < 0: tq = 0
    pg = PAPER.copy(); dd = ImageDraw.Draw(pg); tip = None
    for j in range(i + 1):
        L = LAY[j]; tj = RD if j < i else tq
        if L["strike"]:
            p = seg(tj, THINK, THINK + SW)
            if p > 0:
                x0, ys, x1 = L["strike"]; xe = x0 + (x1 - x0) * p
                dd.line((x0, ys + 5, xe, ys - 5), fill=RED + (255,), width=8)
                if j == i and p < 1: tip = (xe, ys)
        p = seg(tj, THINK + SW + .08, THINK + WRITE)
        if p > 0:
            sp = L["sp"]; w = max(1, int(sp.width * p))
            if TW: pill(dd, L["tagx"], L["wy"] + 22, TW, PEN)
            pg.alpha_composite(sp.crop((0, 0, w, sp.height)), (L["wx"], L["wy"]))
            if j == i and p < 1: tip = (L["wx"] + w, L["wy"] + sp.height * .62)
    L = LAY[i]
    if tip is None:
        rest = L["rest"]; start = (L["strike"][0], L["strike"][1]) if L["strike"] else (L["wx"], L["wy"] + 60)
        end = (L["wx"] + L["sp"].width, L["wy"] + L["sp"].height * .62)
        if tq < THINK - .45: tip = rest
        elif tq < THINK: p = ease(seg(tq, THINK - .45, THINK)); tip = (rest[0] + (start[0] - rest[0]) * p, rest[1] + (start[1] - rest[1]) * p)
        elif tq < THINK + WRITE: tip = (L["wx"], L["wy"] + 60)
        else: p = ease(seg(tq, THINK + WRITE, THINK + WRITE + .45)); tip = (end[0] + (rest[0] - end[0]) * p, end[1] + (rest[1] - end[1]) * p)
    shadow = Image.new("RGBA", (PW + 60, PH + 60), (0, 0, 0, 0)); shadow.paste((0, 0, 0, 110), (30, 36, 30 + PW, 36 + PH))
    fr.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(16)), (PX - 30, PY - 30)); fr.alpha_composite(pg, (PX, PY))
    if not outro and 0 <= tq < THINK + .2 and tt >= 0:                      # countdown next to the active row
        left = THINK - tq; cx, cy, r = PX + PW - 96, PY + L["y"] + 40, 62
        dd2 = ImageDraw.Draw(fr); rr = r * (1 + .06 * (1 - (left % 1)) if left > 0 else 1.1)
        dd2.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=(255, 255, 255, 255), outline=INK + (255,), width=6)
        dd2.arc((cx - rr + 10, cy - rr + 10, cx + rr - 10, cy + rr - 10), -90, -90 + 360 * clamp(left / THINK), fill=(RED if left <= 1 else GREEN) + (255,), width=10)
        num = str(max(0, math.ceil(left))); f = F(66, "Black"); dd2.text((cx - f.getlength(num) / 2, cy - 42), num, font=f, fill=INK)
    sx, sy = PX + tip[0], PY + tip[1]
    fr.alpha_composite(PSH, (int(sx - PTIP[0] + 26), int(sy - PTIP[1] + 30))); fr.alpha_composite(PENCIL, (int(sx - PTIP[0]), int(sy - PTIP[1])))
    fr.alpha_composite(HEAD, ((W - HEAD.width) // 2, 36))
    if outro:
        t0 = INTRO + len(ROWS) * RD; p = seg(t, t0 + .1, t0 + .5); s = .6 + .4 * (1 + 2.7 * (p - 1) ** 3 + 1.7 * (p - 1) ** 2)
        o = OUT.resize((max(1, int(OUT.width * s)), max(1, int(OUT.height * s))), Image.BICUBIC); fr.alpha_composite(o, ((W - o.width) // 2, CFG.get("outro_y", 1745) - o.height // 2))
    return fr.convert("RGB")

def audio(path):
    import clean_audio as CA
    ticks, dings = [], []
    for i in range(len(ROWS)):
        t0 = INTRO + i * RD; off = THINK - int(THINK)
        for k in range(int(THINK)): ticks.append((t0 + off + k, k == int(THINK) - 1))
        dings.append(t0 + THINK + WRITE)
    dings.append(INTRO + len(ROWS) * RD + .1)
    CA.build(path, DUR, ticks, dings)

if __name__ == "__main__":
    if sys.argv[1] == "audio": audio(sys.argv[2]); print("ok audio"); sys.exit()
    if sys.argv[1] == "preview":
        out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
        for s in sys.argv[3:]: render(float(s)).save(out / f"pw_{float(s):06.2f}.jpg", quality=88)
        print("ok", DUR)
    else:
        work = Path(tempfile.mkdtemp()); (work / "f").mkdir()
        for k in range(int(DUR * FPS)): render(k / FPS).save(work / "f" / f"{k:05d}.jpg", quality=92)
        audio(str(work / "a.wav"))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", str(work / "f" / "%05d.jpg"), "-i", str(work / "a.wav"), "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", f"{DUR:.2f}", sys.argv[1]], check=True)
        subprocess.run(["rm", "-rf", str(work)]); print("ok", sys.argv[1], DUR)
