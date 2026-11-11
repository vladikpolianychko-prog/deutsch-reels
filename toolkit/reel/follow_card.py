"""Series tag + follow end card for paper reels (owner request 11.11: every reel must give a reason to like & follow).
series_tag(text)            -> small dark pill shown under the header for the whole reel ("Тест №1 · щодня новий")
follow_card(line1, line2, pressed) -> white card: avatar, @name, blue «Підписатися» button (grey «Ви підписані» when pressed),
                               heart row "♥ лайк, якщо …"
draw_end(fr, t, t0, cfg)    -> composites the follow card (pops in at t0, button 'pressed' at t0+1.3)
"""
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FD = "/usr/share/fonts/opentype/inter/"
F = lambda n, w="Bold": ImageFont.truetype(f"{FD}InterDisplay-{w}.otf", n)
INK = (28, 30, 38)

def _shadow(im, r=14, off=10, a=110):
    sh = Image.new("RGBA", (im.width + 60, im.height + 60), (0, 0, 0, 0))
    sh.paste((0, 0, 0, a), (30, 30 + off), im.getchannel("A")); sh = sh.filter(ImageFilter.GaussianBlur(r)); sh.alpha_composite(im, (30, 30)); return sh

def series_tag(text):
    f = F(40, "Black"); w = int(f.getlength(text)) + 56
    im = Image.new("RGBA", (w, 66), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, 65), 33, fill=(28, 30, 38, 235)); d.text((28, 9), text, font=f, fill=(255, 214, 70))
    return _shadow(im, 8, 4, 80)

def heart(d, cx, cy, s, col):
    d.ellipse((cx - s, cy - s * .75, cx, cy + s * .25), fill=col); d.ellipse((cx, cy - s * .75, cx + s, cy + s * .25), fill=col)
    d.polygon([(cx - s * .97, cy - s * .12), (cx + s * .97, cy - s * .12), (cx, cy + s * 1.05)], fill=col)

def follow_card(line1, line2, like, handle="deutsch_v_zoshity", pressed=False):
    W, H = 900, 470
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W - 1, H - 1), 40, fill=(255, 255, 255, 250))
    f1, f2 = F(54, "Black"), F(40, "SemiBold")
    d.text(((W - f1.getlength(line1)) / 2, 34), line1, font=f1, fill=INK)
    d.text(((W - f2.getlength(line2)) / 2, 104), line2, font=f2, fill=(90, 96, 110))
    # profile row
    y = 184; d.ellipse((56, y, 156, y + 100), fill=(255, 214, 70)); fz = F(40, "Black"); d.text((106 - fz.getlength("DZ") / 2, y + 26), "DZ", font=fz, fill=INK)
    d.text((178, y + 26), handle, font=F(42, "Bold"), fill=INK)
    bx0, by0, bx1, by1 = W - 330, y + 14, W - 50, y + 86
    if pressed:
        d.rounded_rectangle((bx0, by0, bx1, by1), 18, fill=(219, 222, 228)); t, c = "Ви підписані", INK
    else:
        d.rounded_rectangle((bx0, by0, bx1, by1), 18, fill=(0, 149, 246)); t, c = "Підписатися", (255, 255, 255)
    fb = F(38, "Bold"); d.text(((bx0 + bx1 - fb.getlength(t)) / 2, by0 + 14), t, font=fb, fill=c)
    # like row
    y2 = 340; heart(d, 96, y2 + 46, 34, (237, 73, 86))
    fl = F(44, "Bold"); d.text((150, y2 + 18), like, font=fl, fill=INK)
    return _shadow(im)

def make(cfg):
    fc = cfg.get("follow", {})
    l1 = fc.get("line1", "Завтра — новий тест"); l2 = fc.get("line2", "щодня одна сторінка зошита")
    like = fc.get("like", "лайк, якщо набрав(-ла) 5/5")
    return follow_card(l1, l2, like), follow_card(l1, l2, like, pressed=True)

def back(p): return 1 + 2.7 * (p - 1) ** 3 + 1.7 * (p - 1) ** 2

def draw_end(fr, t, t0, cards, y=1260):
    if t < t0: return
    p = min(1, (t - t0) / .4); s = .6 + .4 * back(p)
    c = cards[1] if t >= t0 + 1.3 else cards[0]
    if t0 + 1.2 <= t < t0 + 1.4: s *= .96                          # tiny 'tap' on the button
    o = c.resize((max(1, int(c.width * s)), max(1, int(c.height * s))), Image.BICUBIC)
    fr.alpha_composite(o, ((fr.width - o.width) // 2, y - o.height // 2))
