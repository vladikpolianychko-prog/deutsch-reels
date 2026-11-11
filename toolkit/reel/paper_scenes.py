"""Paper-scenes reel: three new faceless notebook formats in one engine (cfg["mode"]):
 - "read":  read-aloud challenge (tongue twisters): 3-2-1, words get highlighted at reading pace, translation appears
 - "build": word builder: compound pieces with glosses appear, 3-s guess timer, pencil writes the word + meaning
 - "chat":  real-life dialogue: cashier bubble (DE + UA), 3-s 'what do you answer?', your bubble appears
Shared: wooden desk, squared notebook page that scrolls to the active block, header sticker, series tag,
follow end card (follow_card.py), clean soundtrack (clean_audio.py).
usage: CFG=cfg.json python3 paper_scenes.py out.mp4 | preview dir t1 t2 ... | audio out.wav
"""
import json, math, os, subprocess, sys, tempfile
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import follow_card as FC, clean_audio as CA

W, H, FPS = 1080, 1920, 30
CFG = json.load(open(os.environ["CFG"], encoding="utf-8")); MODE = CFG["mode"]; ITEMS = CFG["items"]
THINK = CFG.get("think", 3.0)
FD = "/usr/share/fonts/opentype/inter/"
HAND = str(Path(__file__).resolve().parent / "bg/fonts/ComicRelief-Regular.ttf")
F = lambda n, w="Bold": ImageFont.truetype(f"{FD}InterDisplay-{w}.otf", n)
HF = lambda n: ImageFont.truetype(HAND, n)
INK, RED, GREEN, BLUE, GREY = (28, 30, 38), (214, 48, 49), (34, 160, 90), (150, 190, 235), (110, 116, 130)
PEN = (38, 78, 168)

def clamp(x, a=0., b=1.): return max(a, min(b, x))
def seg(t, a, b): return clamp((t - a) / (b - a))
def ease(p): return 4 * p ** 3 if p < .5 else 1 - (-2 * p + 2) ** 3 / 2
def back(p): return 1 + 2.7 * (p - 1) ** 3 + 1.7 * (p - 1) ** 2

rng = np.random.default_rng(4); yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
desk = np.zeros((H, W, 3), np.float32); desk[:] = (92, 64, 44)
desk += (np.sin(xx * .012 + np.sin(yy * .003) * 4) * 9 + np.sin(xx * .09) * 3 + rng.normal(0, 2.5, (H, W)))[..., None]
DESK = Image.fromarray(np.clip(desk, 0, 255).astype(np.uint8)).convert("RGBA")

PW, MX, X1 = 980, 104, 940
def wrap(text, font, maxw):
    lines, cur = [], ""
    for w_ in text.split():
        t = (cur + " " + w_).strip()
        if font.getlength(t) <= maxw or not cur: cur = t
        else: lines.append(cur); cur = w_
    return lines + [cur]

# ---------------------------------------------------------------- layout per mode (static ink on paper + timings)
BLOCKS = []; t = .4
if MODE == "read":
    fr_, ft = F(84, "ExtraBold"), HF(54)
    for it in ITEMS:
        words, y = [], 0
        for line in wrap(it["de"], fr_, X1 - MX):
            x = MX
            for w_ in line.split():
                ww = fr_.getlength(w_); words.append((x, y, ww)); x += ww + fr_.getlength(" ")
            y += 118
        tr = wrap(it["ua"], ft, X1 - MX)
        pace = it.get("pace", CFG.get("pace", .42)); rd = len(words) * pace
        h = y + 40 + len(tr) * 74
        BLOCKS.append(dict(it=it, words=words, tr=tr, h=h, t0=t, read=(t + THINK, t + THINK + rd), end=t + THINK + rd + 1.7)); t = BLOCKS[-1]["end"]
elif MODE == "build":
    fp, fg = F(70, "ExtraBold"), F(34, "SemiBold")
    for it in ITEMS:
        n = len(it["parts"]); total = sum(fp.getlength(p) for p, _ in it["parts"]) + fp.getlength(" + ") * (n - 1)
        h = 560
        BLOCKS.append(dict(it=it, h=h, t0=t, think=t + 1.7, reveal=t + 1.7 + THINK, end=t + 1.7 + THINK + 1.8)); t = BLOCKS[-1]["end"]
elif MODE == "chat":
    for it in ITEMS:
        BLOCKS.append(dict(it=it, h=0, t0=t, think=t + .7, reveal=t + .7 + THINK, end=t + .7 + THINK + 1.6)); t = BLOCKS[-1]["end"]
BODY_END = t; OUTRO = CFG.get("outro_dur", 4.6); DUR = BODY_END + OUTRO
PY0 = 230; PH = H - PY0 + 40; PCY = CFG.get("center", 820)   # content centre in paper coords (~screen 990)

paper = Image.new("RGBA", (PW, PH), (253, 252, 247, 255)); d = ImageDraw.Draw(paper)
for yy_ in range(0, PH, 48): d.line((0, yy_, PW, yy_), fill=BLUE + (120,), width=2)
for xx_ in range(0, PW, 48): d.line((xx_, 0, xx_, PH), fill=BLUE + (120,), width=2)
d.line((70, 0, 70, PH), fill=(230, 90, 90, 200), width=4)
PAPER = paper

# sprites
def hand(txt, size, col):
    f = HF(size); im = Image.new("RGBA", (int(f.getlength(txt)) + 24, int(size * 1.5)), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((8, 4), txt, font=f, fill=col + (255,), stroke_width=1, stroke_fill=col + (255,)); return im

def bubble(lines, fill, fg, maxw=720, tail="left", label=None):
    fs = [(F(62, "Bold"), lines[0], fg)] + ([(F(42, "Medium"), lines[1], (95, 100, 115) if fill[0] > 200 else (220, 232, 255))] if len(lines) > 1 else [])
    rows = []
    for f, txt, c in fs:
        for l in wrap(txt, f, maxw): rows.append((f, l, c))
    w = int(max(f.getlength(l) for f, l, _ in rows)) + 64; h = sum(f.size + 16 for f, _, _ in rows) + 44
    lab_h = 56 if label else 0
    im = Image.new("RGBA", (w + 30, h + 30 + lab_h), (0, 0, 0, 0)); dd = ImageDraw.Draw(im)
    if label: dd.text((14 if tail == "left" else w - F(40, "Bold").getlength(label) + 14, 0), label, font=F(40, "Bold"), fill=GREY)
    ox = 0 if tail == "left" else 30
    dd.rounded_rectangle((ox, lab_h, ox + w, lab_h + h), 34, fill=fill + (255,))
    if tail == "left": dd.polygon([(ox + 18, lab_h + h - 40), (ox - 0, lab_h + h + 22), (ox + 70, lab_h + h - 6)], fill=fill + (255,))
    else: dd.polygon([(ox + w - 18, lab_h + h - 40), (ox + w + 26, lab_h + h + 22), (ox + w - 70, lab_h + h - 6)], fill=fill + (255,))
    yy_ = lab_h + 22
    for f, l, c in rows: dd.text((ox + 32, yy_), l, font=f, fill=c); yy_ += f.size + 16
    sh = Image.new("RGBA", (im.width + 40, im.height + 40), (0, 0, 0, 0)); sh.paste((0, 0, 0, 60), (20, 28), im.getchannel("A"))
    sh = sh.filter(ImageFilter.GaussianBlur(10)); sh.alpha_composite(im, (20, 20)); return sh

for b in BLOCKS:
    it = b["it"]
    if MODE == "build":
        fp, fg = F(100, "ExtraBold"), F(44, "SemiBold"); parts = it["parts"]
        widths = [fp.getlength(p) for p, _ in parts]; plus = fp.getlength(" + ")
        total = sum(widths) + plus * (len(parts) - 1); sc = min(1, (X1 - MX) / total)
        fp = F(int(100 * sc), "ExtraBold"); widths = [fp.getlength(p) for p, _ in parts]; plus = fp.getlength(" + ")
        x = MX + ((X1 - MX) - (sum(widths) + plus * (len(parts) - 1))) / 2; pos = []
        for (p, gl), wd in zip(parts, widths): pos.append((x, p, gl, wd)); x += wd + plus
        b["pos"] = pos; b["fp"] = fp
        b["ans"] = hand(it["word"], 100, PEN); b["mean"] = hand("= " + it["ua"], 74, RED)
    if MODE == "chat":
        b["q"] = bubble([it["q"], it["q_ua"]], (255, 255, 255), INK, label=CFG.get("who", "Касирка"))
        b["a"] = bubble([it["a"], it.get("a_ua", "")] if it.get("a_ua") else [it["a"]], (0, 132, 255), (255, 255, 255), tail="right", label="Ти")
        b["dots"] = bubble(["…"], (0, 132, 255), (255, 255, 255), tail="right", label="Ти")
    if MODE == "read":
        b["trs"] = [hand(l, 54, GREY) for l in b["tr"]]

for b in BLOCKS:
    if MODE == "chat": b["h"] = b["q"].height + 10 + b["a"].height
    b["top"] = int(PCY - b["h"] / 2)

def sticker(lines, fill, fg=INK, pad=(34, 20), rot=0):
    fs = [F(s, w) for _, s, w in lines]; ws = [f.getlength(t_) for (t_, _, _), f in zip(lines, fs)]
    w = int(max(ws)) + pad[0] * 2; h = sum(f.size + 14 for f in fs) + pad[1] * 2 - 14
    im = Image.new("RGBA", (w, h), fill + (255,)); dd = ImageDraw.Draw(im); y_ = pad[1]
    for (t_, _, _), f, tw in zip(lines, fs, ws): dd.text(((w - tw) / 2, y_), t_, font=f, fill=fg); y_ += f.size + 14
    if rot: im = im.rotate(rot, expand=True, resample=Image.BICUBIC)
    sh = Image.new("RGBA", (im.width + 40, im.height + 40), (0, 0, 0, 0))
    sh.paste((0, 0, 0, 90), (20, 26), im.getchannel("A")); sh = sh.filter(ImageFilter.GaussianBlur(10)); sh.alpha_composite(im, (20, 16)); return sh
HEAD = sticker([(CFG["header"], 60, "Black"), (CFG["sub"], 44, "SemiBold")], (255, 214, 70), rot=-1.5)
OUT = sticker([(l, 62, "Black") for l in CFG["outro"]], (255, 214, 70), rot=2)
SERIES = FC.series_tag(CFG["series"]) if CFG.get("series") else None
CARDS = FC.make(CFG)

def make_pencil():
    L, T, S = 620, 44, 3
    im = Image.new("RGBA", ((L + 80) * S, (T + 40) * S), (0, 0, 0, 0)); dd = ImageDraw.Draw(im)
    y0, y1, x0 = 20 * S, (20 + T) * S, 10 * S; body = (52, 96, 190)
    dd.polygon([(x0, (y0 + y1) // 2), (x0 + 70 * S, y0), (x0 + 70 * S, y1)], fill=(232, 196, 150))
    dd.polygon([(x0, (y0 + y1) // 2), (x0 + 22 * S, y0 + 15 * S), (x0 + 22 * S, y1 - 15 * S)], fill=PEN)
    dd.rectangle((x0 + 70 * S, y0, x0 + (L - 70) * S, y1), fill=body); dd.rectangle((x0 + 70 * S, y0, x0 + (L - 70) * S, y0 + 12 * S), fill=(92, 136, 230))
    dd.rectangle((x0 + (L - 70) * S, y0, x0 + (L - 30) * S, y1), fill=(190, 194, 204)); dd.rounded_rectangle((x0 + (L - 30) * S, y0, x0 + (L + 20) * S, y1), 10 * S, fill=(236, 130, 140))
    im = im.resize((im.width // S, im.height // S), Image.LANCZOS); ang = -52; rot = im.rotate(ang, expand=True, resample=Image.BICUBIC)
    cx, cy = im.width / 2, im.height / 2; tx, ty = 10 - cx, (20 + T / 2) - cy; a = math.radians(-ang)
    return rot, (tx * math.cos(a) - ty * math.sin(a) + rot.width / 2, tx * math.sin(a) + ty * math.cos(a) + rot.height / 2)
PENCIL, PTIP = make_pencil()

def timer(fr, cx, cy, left, total, r=70):
    dd = ImageDraw.Draw(fr); rr = r * (1 + .06 * (1 - (left % 1)) if left > 0 else 1.1)
    dd.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=(255, 255, 255, 255), outline=INK + (255,), width=6)
    dd.arc((cx - rr + 10, cy - rr + 10, cx + rr - 10, cy + rr - 10), -90, -90 + 360 * clamp(left / total), fill=(RED if left <= 1 else GREEN) + (255,), width=10)
    num = str(max(0, math.ceil(left))); f = F(72, "Black"); dd.text((cx - f.getlength(num) / 2, cy - 46), num, font=f, fill=INK)

def active(t):
    for i, b in enumerate(BLOCKS):
        if t < b["end"]: return i
    return len(BLOCKS) - 1

def scroll(t): return PY0

def render(t):
    fr = DESK.copy(); sy = scroll(t); ia = active(t); outro = t >= BODY_END
    pg = PAPER.copy(); dd = ImageDraw.Draw(pg); tip = None; overlays = []
    for i, b in ([] if outro else [(ia, BLOCKS[ia])]):
        it, top = b["it"], b["top"]; tt = t
        if MODE == "read":
            fr_ = F(84, "ExtraBold"); n = len(b["words"]); r0, r1 = b["read"]; k = (tt - r0) / max(1e-6, r1 - r0) * n
            for j, (x, y, ww) in enumerate(b["words"]):
                if j < k: dd.rounded_rectangle((x - 8, top + y + 6, x + ww + 8, top + y + 102), 12, fill=(255, 226, 92))
            for j, (x, y, ww) in enumerate(b["words"]):
                w_ = it["de"].split()[j]; dd.text((x, top + y), w_, font=fr_, fill=INK)
            p = seg(tt, r1 + .1, r1 + .9); yy_ = top + b["words"][-1][1] + 140
            for s in b["trs"]:
                if p > 0: pg.alpha_composite(s.crop((0, 0, max(1, int(s.width * p)), s.height)), (MX, int(yy_)))
                yy_ += 74
            if i == ia and not outro and tt < r0: overlays.append(("count", r0 - tt, top, 0))
        if MODE == "build":
            fp, fg = b["fp"], F(44, "SemiBold"); n = len(b["pos"])
            for j, (x, p_, gl, wd) in enumerate(b["pos"]):
                a = seg(tt, b["t0"] + .1 + j * 1.4 / n, b["t0"] + .4 + j * 1.4 / n)
                if a <= 0: continue
                col = tuple(int(253 + (c - 253) * a) for c in INK)
                dd.text((x, top + 30), p_, font=fp, fill=col)
                gw = fg.getlength(gl); dd.text((x + (wd - gw) / 2, top + 30 + fp.size + 16), gl, font=fg, fill=tuple(int(253 + (c - 253) * a) for c in GREY))
                if j < n - 1: dd.text((x + wd + fp.getlength(" ") * .5, top + 30), "+", font=fp, fill=RED)
            p = seg(tt, b["reveal"] + .05, b["reveal"] + .9)
            if p > 0:
                s = b["ans"]; w_ = max(1, int(s.width * p)); xa = (PW - b["ans"].width) // 2; ya = top + 250
                pg.alpha_composite(s.crop((0, 0, w_, s.height)), (xa, ya))
                if i == ia and p < 1: tip = (xa + w_, ya + s.height * .62)
            p2 = seg(tt, b["reveal"] + .95, b["reveal"] + 1.5)
            if p2 > 0:
                s = b["mean"]; pg.alpha_composite(s.crop((0, 0, max(1, int(s.width * p2)), s.height)), ((PW - b["mean"].width) // 2, top + 390))
            if i == ia and not outro and b["think"] <= tt < b["reveal"]: overlays.append(("timer", b["reveal"] - tt, top + 300, PW - 110))
        if MODE == "chat":
            p = seg(tt, b["t0"] + .05, b["t0"] + .4)
            if p > 0:
                q = b["q"]; s = .7 + .3 * back(p); qi = q.resize((max(1, int(q.width * s)), max(1, int(q.height * s))), Image.BICUBIC); pg.alpha_composite(qi, (MX - 30, top))
            qh = b["q"].height
            if b["think"] <= tt < b["reveal"]:
                dt = b["dots"]; pg.alpha_composite(dt, (PW - 60 - dt.width, top + qh + 10))
                if i == ia and not outro: overlays.append(("timer", b["reveal"] - tt, top + qh + 70, PW - 60 - b["dots"].width - 150))
            p = seg(tt, b["reveal"], b["reveal"] + .35)
            if p > 0:
                a_ = b["a"]; s = .7 + .3 * back(p); ai = a_.resize((max(1, int(a_.width * s)), max(1, int(a_.height * s))), Image.BICUBIC)
                pg.alpha_composite(ai, (PW - 60 - ai.width, top + qh + 10))
                if p >= 1:
                    cx, cy = PW - 60 - a_.width - 40, top + qh + 10 + a_.height // 2
                    dd.line([(cx - 26, cy), (cx - 8, cy + 20), (cx + 24, cy - 22)], fill=GREEN + (255,), width=12, joint="curve")
    # paper
    top_y = int(sy); vis = pg.crop((0, max(0, -top_y), PW, max(0, -top_y) + H - max(0, top_y))); py = max(0, top_y); px = (W - PW) // 2
    shadow = Image.new("RGBA", (PW + 60, vis.height + 60), (0, 0, 0, 0)); shadow.paste((0, 0, 0, 110), (30, 36, 30 + PW, 36 + vis.height))
    fr.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(16)), (px - 30, py - 30)); fr.alpha_composite(vis, (px, py))
    for kind, left, yy_, ox in overlays:
        if kind == "timer": timer(fr, px + ox, int(sy + yy_), left, THINK)
        if kind == "count":
            n = max(1, math.ceil(left)); f = F(64, "Black"); txt = CFG.get("count_text", "Читай уголос через") + f" {n}…"
            w_ = f.getlength(txt) + 60; cx = W / 2; cy = int(sy + yy_ - 70)
            ImageDraw.Draw(fr).rounded_rectangle((cx - w_ / 2, cy - 48, cx + w_ / 2, cy + 48), 30, fill=RED + (255,)); ImageDraw.Draw(fr).text((cx - w_ / 2 + 30, cy - 38), txt, font=f, fill=(255, 255, 255))
    if tip:
        sx, sy2 = px + tip[0], sy + tip[1]; fr.alpha_composite(PENCIL, (int(sx - PTIP[0]), int(sy2 - PTIP[1])))
    fr.alpha_composite(HEAD, ((W - HEAD.width) // 2, 36))
    if SERIES is not None: fr.alpha_composite(SERIES, ((W - SERIES.width) // 2, 36 + HEAD.height - 34))
    if outro:
        p = seg(t, BODY_END + .1, BODY_END + .5); s = .6 + .4 * back(p)
        o = OUT.resize((max(1, int(OUT.width * s)), max(1, int(OUT.height * s))), Image.BICUBIC); fr.alpha_composite(o, ((W - o.width) // 2, CFG.get("outro_y", 820) - o.height // 2))
        FC.draw_end(fr, t, BODY_END + 1.1, CARDS, CFG.get("card_y", 1380))
    return fr.convert("RGB")

def audio(path):
    ticks, dings = [], []
    for b in BLOCKS:
        if MODE == "read":
            r0 = b["read"][0]
            for k in range(int(THINK)): ticks.append((r0 - THINK + k, k == int(THINK) - 1))
            dings.append(b["read"][1])
        else:
            for k in range(int(THINK)): ticks.append((b["think"] + k, k == int(THINK) - 1))
            dings.append(b["reveal"])
    dings.append(BODY_END + .1); CA.build(path, DUR, ticks, dings)

if __name__ == "__main__":
    if sys.argv[1] == "audio": audio(sys.argv[2]); print("ok audio"); sys.exit()
    if sys.argv[1] == "preview":
        out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
        for s in sys.argv[3:]: render(float(s)).save(out / f"ps_{float(s):06.2f}.jpg", quality=88)
        print("ok", round(DUR, 2), [round(b["end"], 2) for b in BLOCKS])
    else:
        work = Path(tempfile.mkdtemp()); (work / "f").mkdir()
        for k in range(int(DUR * FPS)): render(k / FPS).save(work / "f" / f"{k:05d}.jpg", quality=92)
        audio(str(work / "a.wav"))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", str(work / "f" / "%05d.jpg"), "-i", str(work / "a.wav"), "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", f"{DUR:.2f}", sys.argv[1]], check=True)
        subprocess.run(["rm", "-rf", str(work)]); print("ok", sys.argv[1], round(DUR, 2))
