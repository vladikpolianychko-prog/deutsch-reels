"""Deterministic notebook-style carousel (6 slides, 1080x1350 PNG). No AI-generated text: every letter comes from the spec.
usage: python3 make_carousel.py spec.json out_dir        (spec: see bei.json)  needs pillow + numpy."""
import json, math, os, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sheet"))
import make_sheet as M
M.W, M.H, M.SC = 1080, 1350, 1.0
W, H = 1080, 1350
X0, X1 = 200, 1020
CX = (X0 + X1) // 2
COL = M.COL; BLUE_HL, YEL, WHITE = M.BLUE_HL, M.YEL, M.WHITE
LIME, PINK = (205, 228, 110), (246, 176, 170)

def sp(segs, size, bold=True, maxw=X1 - X0): return M.sprite([(t, c) for t, c in segs], size, bold, maxw)
def hl(img, x, y, w, h, color, seed=1, alpha=235): M.put(img, M.blob(int(w), int(h), color, seed, alpha), x - 20, y - 20)
def cput(img, im, y, cx=CX): M.put(img, im, cx - im.width // 2, y)
def segs(lst): return [(t, c) for t, c in lst]

def sticky(img, text, y=70):
    t = sp([(text, "ink")], 44); st = Image.new("RGBA", (t.width + 56, t.height + 28), YEL + (250,)); st.alpha_composite(t, (28, 14))
    st = st.rotate(1.5, expand=True, resample=Image.BICUBIC); M.put(img, st, X0 - 20, y); return y + st.height

def heading(img, text, y, color=BLUE_HL, size=70, seed=3):
    t = sp([(text, "ink")], size, True, X1 - X0 - 40); hl(img, CX - t.width // 2 - 10, y + 10, t.width + 20, t.height - 24, color, seed)
    cput(img, t, y); return y + t.height

def sad_face(img, cx, cy, r=46):
    d = ImageDraw.Draw(img); ink = COL["ink"] + (255,)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=ink, width=6, fill=WHITE + (255,))
    for dx in (-16, 16): d.ellipse((cx + dx - 5, cy - 14, cx + dx + 5, cy - 4), fill=ink)
    d.arc((cx - 20, cy + 10, cx + 20, cy + 40), 200, 340, fill=ink, width=6)

def arrow(img, x, y0, y1, color):
    M.stroke(img, M.wobbly_line(x, y0, x, y1, color, 8, 3, 3), color, 9)
    M.stroke(img, [(x - 28, y1 - 30), (x, y1), (x + 28, y1 - 30)], color, 9)

def uniform(rows, size, bold, maxw):
    """largest common font size (<= size) at which every row fits maxw, so all rows look the same"""
    while size > 24 and max(sp(r, size, bold, 10 ** 6).width for r in rows) > maxw: size -= 2
    return size

def s1(S, top, fin):
    img = M.paper(1); y = top; y = sticky(img, S.get("sticky", f"Префікси №{S['no']}"), y) + 50
    t = sp([(S.get("big", S["prefix"] + "-"), "blue")], 330, True, X1 - X0)
    hl(img, CX - t.width // 2 - 20, y + 55, t.width + 40, t.height - 110, BLUE_HL, 7); cput(img, t, y); y += t.height + 40
    h = sp([(S["hook_de"], "ink")], 78, True, X1 - X0 - 30); hl(img, CX - h.width // 2 - 15, y + 8, h.width + 30, h.height - 22, BLUE_HL, 5); cput(img, h, y); y += h.height + 60
    w = sp([(S["wrong_ua"], "red")], 60, False, X1 - X0 - 30); hl(img, CX - w.width // 2 - 15, y + 8, w.width + 30, w.height - 22, PINK, 8); cput(img, w, y)
    ly = y + w.height // 2 + 4; M.stroke(img, M.wobbly_line(CX - w.width // 2 - 5, ly, CX + w.width // 2 + 5, ly, COL["red"], 7, 4, 3), COL["red"], 7)
    y += w.height + 80
    l = sp([("це НЕ так", "ink")], 70, True, 400); hl(img, CX - 210 - 20, y + 10, l.width + 30, l.height - 26, LIME, 9); M.put(img, l, CX - 210, y)
    sad_face(img, CX + 210 + 70, y + l.height // 2, 54); y += l.height
    return img, y

def s2(S, top, fin):
    img = M.paper(2); y = top; y = heading(img, S.get("t2", f"Як працює {S['prefix']}-"), y, BLUE_HL, 84) + 70
    rsz = uniform([segs(r) for r in S["rule"]], 60, False, X1 - X0 - 70)
    rows = [sp(segs(r), rsz, False, 10 ** 6) for r in S["rule"]]
    rh = sum(i.height + 10 for i in rows) + 70; M.frame(img, X0 - 10, y, X1 - X0 + 20, rh, COL["red"], 11)
    yy = y + 35
    for im in rows: cput(img, im, yy); yy += im.height + 10
    y += rh + 110
    e = sp(segs(S["example"]), 80, True, X1 - X0); cput(img, e, y); y += e.height + 8
    u = sp([(S["example_ua"], "grey")], 52, False, X1 - X0); cput(img, u, y); y += u.height + 90
    p = sp(segs(S["perfekt"]), 62, False, X1 - X0 + 30); cput(img, p, y); y += p.height
    if S.get("note"): y += 50; n = sp(segs(S["note"]), 48, False, X1 - X0); cput(img, n, y); y += n.height
    return img, y

def s3(S, top, fin):
    img = M.paper(3); y = top; y = heading(img, S.get("t3", f"5 дієслів з {S['prefix']}-"), y, LIME, 84, 4) + 90
    aw = max(sp([(d, "blue")], 66, True, 10 ** 6).width for d, _ in S["verbs"])
    us = uniform([[("— " + ua, "ink")] for _, ua in S["verbs"]], 50, False, X1 - X0 - 100 - aw - 8)
    two = us < 42                       # long words: translation goes on its own line under the word
    if two: us = uniform([[("— " + ua, "ink")] for _, ua in S["verbs"]], 46, False, X1 - X0 - 100)
    for i, (de, ua) in enumerate(S["verbs"], 1):
        hl(img, X0 - 4, y + 14, 76, 76, LIME, 20 + i); n = sp([(str(i), "ink")], 62, True, 70); M.put(img, n, X0 + 34 - n.width // 2, y + 8)
        a = sp([(de, "blue")], 66, True, 470); M.put(img, a, X0 + 100, y)
        b = sp([("— " + ua, "ink")], us, False, 10 ** 6)
        if two: M.put(img, b, X0 + 100, y + a.height - 14); y += 185
        else: M.put(img, b, X0 + 100 + a.width + 8, y + 14); y += 170
    return img, y - 40

def s4(S, top, fin):
    img = M.paper(4); y = top; y = heading(img, S.get("t4", f"Тест: встав дієслово з {S['prefix']}-"), y, BLUE_HL, 66, 5) + 110
    qs = uniform([[(f"{i}  ", "orange")] + segs(q["q"]) for i, q in enumerate(S["test"], 1)], 66, True, X1 - X0 - 20)
    for i, q in enumerate(S["test"], 1):
        s = sp([(f"{i}  ", "orange")] + segs(q["q"]), qs, True, 10 ** 6)
        hl(img, X0 - 5, y + 14, X1 - X0 + 10, s.height - 22, BLUE_HL if i % 2 else LIME, 30 + i, 200); M.put(img, s, X0 + 10, y)
        y += s.height + 6; h = sp([(f"({q['hint']})", "orange")], 52, False, X1 - X0); cput(img, h, y); y += h.height + 100
    return img, y - 60

def s5(S, top, fin):
    img = M.paper(5); y = sticky(img, "Відповіді до тесту", top) + 80
    rs = uniform([[(f"{i}  ", "orange")] + segs(a) for i, a in enumerate(S["answers"], 1)], 58, True, X1 - X0 - 40)
    rows = [sp([(f"{i}  ", "orange")] + segs(a), rs, True, 10 ** 6) for i, a in enumerate(S["answers"], 1)]
    bh = sum(r.height + 56 for r in rows) + 70; M.frame(img, X0 - 10, y, X1 - X0 + 20, bh, COL["green"], 21)
    yy = y + 50
    for r in rows: M.put(img, r, X0 + 20, yy); yy += r.height + 56
    y += bh + 110
    f = sp([("Перевір друга: хто швидше?", "ink")], 64, True, X1 - X0 - 30); hl(img, CX - f.width // 2 - 15, y + 8, f.width + 30, f.height - 22, BLUE_HL, 13); cput(img, f, y); y += f.height
    return img, y

def s6(S, top, fin):
    img = M.paper(6); y = top
    a = sp([("Напиши", "ink")], 112, True, X1 - X0); hl(img, CX - a.width // 2 - 20, y + 20, a.width + 40, a.height - 50, BLUE_HL, 6); cput(img, a, y); y += a.height + 30
    k = sp([(S["keyword"], "blue")], 210, True, X1 - X0); cput(img, k, y); y += k.height + 10
    arrow(img, CX, y, y + 110, COL["ink"]); y += 170
    b = sp([(S.get("cta2", "надішлю PDF-шпаргалку"), "ink")], 68, True, X1 - X0 - 30); hl(img, CX - b.width // 2 - 15, y + 10, b.width + 30, b.height - 26, LIME, 8); cput(img, b, y); y += b.height + 80
    c = sp([(S["next"], "ink")], 56, True, X1 - X0 - 30); hl(img, CX - c.width // 2 - 15, y + 8, c.width + 30, c.height - 22, YEL, 9); cput(img, c, y); y += c.height + 60
    h = sp([("@deutsch_v_zoshity", "grey")], 50, False, 560); cput(img, h, y); y += h.height
    return img, y

def build(f, S):
    _, y_end = f(S, 90, False); h = y_end - 90
    top = max(70, (H - h) // 2 - 10)
    img, y_end = f(S, top, True)
    M.check_overflow(y_end, f.__name__)
    return img.convert("RGB")

def main():
    S = json.load(open(sys.argv[1], encoding="utf-8")); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
    assert len(S["verbs"]) == 5 and len(S["test"]) == 3 and len(S["answers"]) == 3
    for i, f in enumerate((s1, s2, s3, s4, s5, s6), 1): build(f, S).save(os.path.join(out, f"slide{i}.png"))
    print("ok", out)
if __name__ == "__main__": main()
