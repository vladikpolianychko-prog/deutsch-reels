"""Extended notebook-style cheat sheet: rule page + N verb pages + exercises + answers (A4 PDF).
usage: python3 make_sheet_full.py spec.json out.pdf [preview_dir]   (spec: see nach_full.json; reuses make_sheet.py)"""
import json, os, sys
from make_sheet import *
import make_sheet as M

def head(img, S, y):
    return y + sticky(img, S["sticky"], X0, y) + 14

def page_rule(S):
    img = paper(1); y = head(img, S, 60)
    t = sprite([(S["title"], "blue")], 160); put(img, blob(t.width + 10, t.height - 40, BLUE_HL, 7), X0 - 14, y); put(img, t, X0, y)
    m = sprite([(S["meaning"], "ink")], 46, bold=False, maxw=X1 - X0 - t.width - 30); put(img, m, X0 + t.width + 24, y + t.height - 78)
    y += t.height + 30
    items = [(sprite(segs_of(l["segs"]), l["size"], l.get("bold", False), X1 - X0 - 80), l.get("gap", 6)) for l in S["rule"]]
    hd = sprite([(S["rule_head"], "red")], 52)
    fh = 30 + hd.height + sum(i.height + g for i, g in items) + 24
    frame(img, X0 - 20, y, X1 - X0 + 40, fh, COL["red"], 11)
    yy = y + 22; put(img, hd, X0 + 10, yy); yy += hd.height + 4
    for im, g in items: put(img, im, X0 + 20, yy + g / 2); yy += im.height + g
    y += fh + 50
    rt = sprite([(S["recap_title"], "orange")], 52)
    lines = [sprite(segs_of(l), 40, False, X1 - X0 - 60) for l in S["recap"]]
    rh = 24 + rt.height + sum(l.height + 14 for l in lines) + 20
    frame(img, X0 - 20, y, X1 - X0 + 40, rh, COL["orange"], 31)
    yy = y + 18; put(img, rt, X0 + 10, yy); yy += rt.height + 8
    for l in lines: put(img, l, X0 + 20, yy); yy += l.height + 14
    y += rh + 50
    pt = sprite([(S["plan_title"], "green")], 52)
    pl = [sprite(segs_of(l), 40, False, X1 - X0 - 60) for l in S["plan"]]
    ph = 24 + pt.height + sum(l.height + 14 for l in pl) + 20
    frame(img, X0 - 20, y, X1 - X0 + 40, ph, COL["green"], 41)
    yy = y + 18; put(img, pt, X0 + 10, yy); yy += pt.height + 8
    for l in pl: put(img, l, X0 + 20, yy); yy += l.height + 14
    y += ph + 20
    check_overflow(y, 1); return img.convert("RGB")

def page_verbs(S, g, start, no):
    img = paper(no); y = head(img, S, 60)
    tt = sprite([(g["title"], "ink")], 58); put(img, blob(tt.width + 6, tt.height - 26, YEL, 9 + no, 250), X0 - 14, y - 7); put(img, tt, X0, y)
    y += tt.height + 22
    for i, (de, ua, ex, pf) in enumerate(g["verbs"], start):
        a = sprite([(f"{i}  ", "orange"), (de, "blue")], 46); put(img, a, X0, y)
        pfs = sprite([(pf, "green")], 34, False, 330); put(img, pfs, X1 - pfs.width, y + 8)
        b = sprite([(" — " + ua, "ink")], 38, False, X1 - X0 - a.width - pfs.width - 20); put(img, b, X0 + a.width, y + 8)
        y += a.height - 4
        e = sprite(segs_of([(ex, "ink")]), 38, False, X1 - X0 - 52); put(img, e, X0 + 52, y); y += e.height + 8
    check_overflow(y, no); return img.convert("RGB")

def ex_block(img, y, blk, n0, S):
    h = sprite([(blk["head"], "red")], 48); put(img, h, X0, y)
    stroke(img, wobbly_line(X0 + 4, y + h.height + 2, X0 + h.width - 4, y + h.height + 2, COL["red"], 7, 3 + n0, 3), COL["red"], 7)
    y += h.height + 20
    for k, (q, hint) in enumerate(blk["items"]):
        a = sprite([(f"{n0 + k}  ", "orange"), (q, "ink")], 52); put(img, a, X0, y)
        hh = sprite([(f"({hint})", "grey")], 32, False); put(img, hh, X0 + 52, y + a.height - 6)
        y += a.height + hh.height + 12
    return y + 16

def page_ex1(S, no):
    img = paper(no); y = head(img, S, 60)
    tt = sprite([(S["ex_title"] + " · частина 1", "ink")], 60); put(img, blob(tt.width + 6, tt.height - 26, YEL, 9, 250), X0 - 14, y - 7); put(img, tt, X0, y)
    y += tt.height + 28
    n = 1
    for blk in S["ex"][:2]: y = ex_block(img, y, blk, n, S); n += len(blk["items"])
    check_overflow(y, no); return img.convert("RGB")

def page_ex2(S, no):
    img = paper(no); y = head(img, S, 60)
    tt = sprite([(S["ex_title"] + " · частина 2", "ink")], 60); put(img, blob(tt.width + 6, tt.height - 26, YEL, 9, 250), X0 - 14, y - 7); put(img, tt, X0, y)
    y += tt.height + 28
    n = 11
    for blk in S["ex"][2:]: y = ex_block(img, y, blk, n, S); n += len(blk["items"])
    f = sprite([(S["friend"], "ink")], 38, False)
    put(img, blob(f.width + 6, f.height - 14, BLUE_HL, 13, 235), X0 - 12, y - 13); put(img, f, X0, y); y += f.height + 34
    check_overflow(y, no); return img.convert("RGB")

def page_ans(S, no):
    img = paper(no); y = head(img, S, 60)
    at = sprite([(S["answers_title"], "red")], 50); put(img, at, X0, y)
    stroke(img, wobbly_line(X0 + 4, y + at.height + 2, X0 + at.width - 4, y + at.height + 2, COL["red"], 7, 3, 3), COL["red"], 7)
    y += at.height + 20; top = y - 6
    rows = [sprite(segs_of(a), 50, True, X1 - X0 - 50) for a in S["answers"]]
    bh = sum(r.height + 12 for r in rows) + 28
    frame(img, X0 - 20, top, X1 - X0 + 40, bh, COL["green"], 21)
    yy = top + 16
    for r in rows: put(img, r, X0 + 20, yy); yy += r.height + 12
    y = top + bh + 40
    ft = sprite([(S["footer"], "ink")], 38, False); put(img, ft, X0, y); y += ft.height
    check_overflow(y, no); return img.convert("RGB")

def main():
    S = json.load(open(sys.argv[1], encoding="utf-8")); out = sys.argv[2]
    n = sum(len(g["verbs"]) for g in S["groups"]); assert n == 50, n
    assert sum(len(b["items"]) for b in S["ex"]) == 15 and len(S["answers"]) == 15
    pages = [page_rule(S)]; start = 1
    for g in S["groups"]:
        pages.append(page_verbs(S, g, start, len(pages) + 1)); start += len(g["verbs"])
    pages += [page_ex1(S, len(pages) + 1), page_ex2(S, len(pages) + 2), page_ans(S, len(pages) + 3)]
    pages[0].save(out, "PDF", resolution=150, save_all=True, append_images=pages[1:], quality=92)
    if len(sys.argv) > 3:
        os.makedirs(sys.argv[3], exist_ok=True)
        for i, p in enumerate(pages, 1): p.save(os.path.join(sys.argv[3], f"f{i}.png"))
    print("ok", out, len(pages), "pages")
main()
