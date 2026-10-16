"""Notebook-style A4 cheat sheet (2 pages) as a PDF.
usage: python3 make_sheet.py spec.json out.pdf [preview_dir]
spec: see nach.json (colors: ink, red, blue, orange, grey, green).  Needs pillow + numpy."""
import json, math, os, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = Path(__file__).resolve().parent
FONT = str(HERE.parent / "reel/bg/fonts/ComicRelief-Regular.ttf")
W, H = 1240, 1754                              # A4 @ 150 dpi
SC = 0.64                                      # global text scale
X0, X1 = 200, 1150                             # text column (red margin line at x=150)
COL = {"ink": (27, 35, 51), "red": (214, 69, 69), "blue": (38, 78, 168), "orange": (232, 132, 50),
       "grey": (74, 88, 120), "green": (62, 154, 58)}
BLUE_HL, YEL, WHITE = (191, 227, 245), (255, 224, 122), (253, 251, 244)
_f = {}
def font(s):
    if s not in _f: _f[s] = ImageFont.truetype(FONT, s)
    return _f[s]

def sprite(segs, size, bold=True, maxw=X1 - X0):
    """segs [[text,color]] on one line -> RGBA (the Bold cut of the font has a broken 'ю', so bold = stroke)."""
    size = round(size * SC)
    while True:
        f = font(size); sw = max(1, round(size * .028)) if bold else 0
        widths = [f.getlength(t) + sw * 2 / max(1, len(segs)) for t, _ in segs]
        if sum(widths) <= maxw or size < 20: break
        size -= 2
    asc, desc = f.getmetrics()
    im = Image.new("RGBA", (int(math.ceil(sum(widths))) + 12, asc + desc + 12), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x = 6
    for (t, c), w in zip(segs, widths):
        col = COL[c] + (255,)
        d.text((x, 6), t, font=f, fill=col, stroke_width=sw, stroke_fill=col); x += w
    return im

def segs_of(lst): return [(t, c) for t, c in lst]

def paper(seed=1):
    r = np.random.default_rng(seed)
    a = np.zeros((H, W, 3), np.float32); a[:] = (248, 244, 232)
    for y in range(30, H, 40): a[y:y + 2] = a[y:y + 2] * .72 + np.array([176, 206, 232]) * .28
    for x in range(30, W, 40): a[:, x:x + 2] = a[:, x:x + 2] * .72 + np.array([176, 206, 232]) * .28
    a[:, 148:151] = a[:, 148:151] * .35 + np.array([226, 120, 128]) * .65
    a += r.normal(0, 2.0, (H, W, 1)).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    a *= (1 - .07 * np.clip(((xx - W / 2) / (W * .8)) ** 2 + ((yy - H / 2) / (H * .8)) ** 2, 0, 1))[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")

def blob(w, h, color, seed=1, alpha=235):
    r = np.random.default_rng(seed)
    im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    pts = []; n = 14
    for i in range(n + 1): pts.append((38 + (w - 36) * i / n + r.uniform(-3, 3), 20 + r.uniform(-5, 4)))
    for i in range(1, 8): a = -math.pi / 2 + i / 8 * math.pi; pts.append((20 + w - 18 + math.cos(a) * 20, 20 + h / 2 + math.sin(a) * h / 2))
    for i in range(n, -1, -1): pts.append((38 + (w - 36) * i / n + r.uniform(-3, 3), 20 + h + r.uniform(-4, 5)))
    for i in range(1, 8): a = math.pi / 2 + i / 8 * math.pi; pts.append((38 + math.cos(a) * 20, 20 + h / 2 + math.sin(a) * h / 2))
    d.polygon(pts, fill=color + (alpha,))
    return im.filter(ImageFilter.GaussianBlur(.8))

def wobbly_line(x0, y0, x1, y1, color, width=7, seed=1, amp=3):
    r = np.random.default_rng(seed); n = max(8, int(math.hypot(x1 - x0, y1 - y0) / 14))
    return [(x0 + (x1 - x0) * i / n + r.uniform(-amp, amp), y0 + (y1 - y0) * i / n + r.uniform(-amp, amp)) for i in range(n + 1)]

def stroke(img, pts, color, width):
    d = ImageDraw.Draw(img); d.line(pts, fill=color + (255,), width=width, joint="curve")
    for (x, y) in (pts[0], pts[-1]): d.ellipse((x - width / 2, y - width / 2, x + width / 2, y + width / 2), fill=color + (255,))

def frame(img, x, y, w, h, color, seed=2):
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    d.rounded_rectangle((x, y, x + w, y + h), radius=22, fill=WHITE + (232,))
    img.alpha_composite(ov)
    for i, (a, b) in enumerate([((x, y), (x + w, y)), ((x + w, y), (x + w, y + h)), ((x + w, y + h), (x, y + h)), ((x, y + h), (x, y - 6))]):
        stroke(img, wobbly_line(a[0], a[1], b[0], b[1], color, 7, seed + i, 2.5), color, 7)

def put(img, im, x, y): img.alpha_composite(im, (int(x), int(y)))

def sticky(img, text, x, y):
    t = sprite([(text, "ink")], 40)
    st = Image.new("RGBA", (t.width + 50, t.height + 26), YEL + (250,)); st.alpha_composite(t, (25, 13))
    st = st.rotate(1.5, expand=True, resample=Image.BICUBIC); put(img, st, x, y); return st.height

def check_overflow(y, page):
    if y > H - 50: raise SystemExit(f"page {page}: content overflows (y={y}), reduce sizes/spacing")

def page1(S):
    img = paper(1); y = 60
    y += sticky(img, S["sticky"], X0, y) + 14
    t = sprite([(S["title"], "blue")], 160); put(img, blob(t.width + 10, t.height - 40, BLUE_HL, 7), X0 - 14, y); put(img, t, X0, y)
    m = sprite([(S["meaning"], "ink")], 46, bold=False, maxw=X1 - X0 - t.width - 30); put(img, m, X0 + t.width + 24, y + t.height - 78)
    y += t.height + 30
    # rule frame
    items = []
    for ln in S["rule"]:
        im = sprite(segs_of(ln["segs"]), ln["size"], ln.get("bold", False), X1 - X0 - 80); items.append((im, ln.get("gap", 6)))
    head = sprite([(S["rule_head"], "red")], 52)
    fh = 30 + head.height + sum(i.height + g for i, g in items) + 24
    frame(img, X0 - 20, y, X1 - X0 + 40, fh, COL["red"], 11)
    yy = y + 22; put(img, head, X0 + 10, yy); yy += head.height + 4
    for im, g in items: put(img, im, X0 + 20, yy + g / 2); yy += im.height + g
    y += fh + 44
    vt = sprite([(S["verbs_title"], "ink")], 58); put(img, vt, X0, y)
    stroke(img, wobbly_line(X0 + 4, y + vt.height + 2, X0 + vt.width - 4, y + vt.height + 2, COL["red"], 8, 5, 3), COL["red"], 8)
    y += vt.height + 26
    for i, v in enumerate(S["verbs"], 1):
        a = sprite([(f"{i}  ", "orange"), (v["de"], "blue")], 50); put(img, a, X0, y)
        b = sprite([(" — " + v["ua"], "ink")], 40, bold=False, maxw=X1 - X0 - a.width); put(img, b, X0 + a.width, y + 8)
        y += a.height - 2
        e = sprite(segs_of(v["ex"]), 40, False); put(img, e, X0 + 52, y); y += e.height - 4
        t2 = sprite([(v["tr"] + "  ·  ", "grey"), (v["perfekt"], "green")], 32, False, X1 - X0 - 52); put(img, t2, X0 + 52, y); y += t2.height + 14
    check_overflow(y, 1)
    return img.convert("RGB")

def page2(S):
    img = paper(2); y = 60
    y += sticky(img, S["sticky"], X0, y) + 20
    tt = sprite([(S["test_title"], "ink")], 60); put(img, blob(tt.width + 6, tt.height - 26, YEL, 9, 250), X0 - 14, y - 7); put(img, tt, X0, y)
    y += tt.height + 36
    for i, q in enumerate(S["test"], 1):
        a = sprite([(f"{i}  ", "orange")] + segs_of(q["q"]), 58); put(img, a, X0, y)
        h = sprite([(q["hint"], "grey")], 34, False); put(img, h, X0 + 52, y + a.height - 6)
        y += a.height + h.height + 18
    y += 10
    f = sprite([(S["friend"], "ink")], 38, False)
    put(img, blob(f.width + 6, f.height - 14, BLUE_HL, 13, 235), X0 - 12, y - 13); put(img, f, X0, y); y += f.height + 46
    # fold line
    d = ImageDraw.Draw(img)
    for x in range(X0 - 40, X1 + 60, 36): d.line((x, y, x + 20, y), fill=COL["grey"] + (255,), width=4)
    y += 26
    at = sprite([(S["answers_title"], "red")], 50); put(img, at, X0, y)
    stroke(img, wobbly_line(X0 + 4, y + at.height + 2, X0 + at.width - 4, y + at.height + 2, COL["red"], 7, 3, 3), COL["red"], 7)
    y += at.height + 22
    box_top = y - 10; rows = []
    for ans in S["answers"]:
        im = sprite(segs_of(ans), 52); rows.append(im)
    bh = sum(r.height + 12 for r in rows) + 30
    frame(img, X0 - 20, box_top, X1 - X0 + 40, bh, COL["green"], 21)
    yy = box_top + 18
    for r in rows: put(img, r, X0 + 20, yy); yy += r.height + 12
    y = box_top + bh + 56
    if S.get("recap"):
        rt = sprite([(S["recap_title"], "orange")], 50)
        lines = [sprite(segs_of(l), 38, False, X1 - X0 - 60) for l in S["recap"]]
        rh = 24 + rt.height + sum(l.height + 8 for l in lines) + 16
        frame(img, X0 - 20, y, X1 - X0 + 40, rh, COL["orange"], 31)
        yy = y + 18; put(img, rt, X0 + 10, yy); yy += rt.height + 4
        for l in lines: put(img, l, X0 + 20, yy); yy += l.height + 8
        y += rh + 40
    ft = sprite([(S["footer"], "ink")], 40, False); put(img, ft, X0, max(y, H - 150))
    check_overflow(max(y, H - 150) + ft.height, 2)
    return img.convert("RGB")

def main():
    spec = json.load(open(sys.argv[1], encoding="utf-8")); out = sys.argv[2]
    pages = [page1(spec), page2(spec)]
    pages[0].save(out, "PDF", resolution=150, save_all=True, append_images=pages[1:], quality=92)
    if len(sys.argv) > 3:
        os.makedirs(sys.argv[3], exist_ok=True)
        for i, p in enumerate(pages, 1): p.save(os.path.join(sys.argv[3], f"p{i}.png"))
    print("ok", out)

if __name__ == "__main__": main()
