"""Shared helpers for the 'kino' reels (12.11: mascot cartoon, pixel game, lyric beat).
Canvas (1080-space coords, optional supersampling), easing, clean synth (pure tones only, no noise), encode/preview.
Usage in an engine:  K.main(render, DUR, audio)   ->   python engine.py out.mp4 | preview <dir> t1 t2 ... | audio out.wav
"""
import os, subprocess, sys, tempfile, wave
from multiprocessing import Pool
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, SR = 1080, 1920, 30, 44100
FD = "/usr/share/fonts/opentype/inter/"
_fc = {}
def F(n, w="Black"):
    k = (int(n), w)
    if k not in _fc: _fc[k] = ImageFont.truetype(f"{FD}InterDisplay-{w}.otf", int(n))
    return _fc[k]

INK = (28, 30, 38); YEL = (255, 214, 70); WHITE = (255, 255, 255)
def clamp(x, a=0., b=1.): return max(a, min(b, x))
def seg(t, a, b): return clamp((t - a) / (b - a))
def ease(p): return 4 * p ** 3 if p < .5 else 1 - (-2 * p + 2) ** 3 / 2
def out3(p): return 1 - (1 - p) ** 3
def back(p): return 1 + 2.7 * (p - 1) ** 3 + 1.7 * (p - 1) ** 2
def lerp(a, b, p): return a + (b - a) * p
def mix(c1, c2, p): return tuple(int(round(lerp(a, b, p))) for a, b in zip(c1, c2))

class Canvas:
    """Draw in 1080x1920 coordinates; S = supersampling factor (shapes get smooth edges after downscale)."""
    def __init__(self, bg, S=1):
        self.S = S; self.im = Image.new("RGB", (int(W * S), int(H * S)), bg); self.d = ImageDraw.Draw(self.im)
    def _b(self, b): return [v * self.S for v in b]
    def rect(self, b, fill): self.d.rectangle(self._b(b), fill=fill)
    def rrect(self, b, r, fill, outline=None, width=0): self.d.rounded_rectangle(self._b(b), r * self.S, fill=fill, outline=outline, width=int(width * self.S))
    def ell(self, b, fill, outline=None, width=0): self.d.ellipse(self._b(b), fill=fill, outline=outline, width=int(width * self.S))
    def circ(self, cx, cy, r, fill, outline=None, width=0): self.ell((cx - r, cy - r, cx + r, cy + r), fill, outline, width)
    def poly(self, pts, fill): self.d.polygon([(x * self.S, y * self.S) for x, y in pts], fill=fill)
    def line(self, pts, fill, width): self.d.line([(x * self.S, y * self.S) for x, y in pts], fill=fill, width=int(width * self.S), joint="curve")
    def arc(self, b, a0, a1, fill, width): self.d.arc(self._b(b), a0, a1, fill=fill, width=int(width * self.S))
    def chord(self, b, a0, a1, fill): self.d.chord(self._b(b), a0, a1, fill=fill)
    def text(self, xy, s, size, fill, w="Black", anchor="mm"):
        self.d.text((xy[0] * self.S, xy[1] * self.S), s, font=F(size * self.S, w), fill=fill, anchor=anchor)
    def tw(self, s, size, w="Black"): return F(size, w).getlength(s)
    def fit(self, s, size, maxw, w="Black"):
        while self.tw(s, size, w) > maxw and size > 20: size -= 2
        return size
    def done(self):
        return self.im if self.S == 1 else self.im.resize((W, H), Image.LANCZOS)

# ---------- clean synth (pure tones, no noise) ----------
def _t(d): return np.arange(int(d * SR)) / SR
def tone(f, d, decay=0, harm=((1, 1.0),), att=.003):
    t = _t(d); x = sum(g * np.sin(2 * np.pi * f * k * t) for k, g in harm)
    if decay: x = x * np.exp(-t * decay)
    n = len(x); a = max(1, int(att * SR)); x[:a] *= np.linspace(0, 1, a); r = max(1, int(.012 * SR)); x[-r:] *= np.linspace(1, 0, r)
    return x
def kick(): t = _t(.22); return np.sin(2 * np.pi * (48 * t + 70 * (1 - np.exp(-t * 28)) / 28)) * np.exp(-t * 14)
def clap(): return tone(880, .09, 55, ((1, 1), (1.5, .5), (2.02, .3)))            # tonal 'snap' instead of noisy snare
def hat(): return tone(6200, .03, 160, ((1, 1), (1.34, .5)))
def tri(f, d, decay=0): return tone(f, d, decay, ((1, 1), (3, 1 / 9), (5, 1 / 25), (7, 1 / 49)))
def pulse(f, d, decay=0): return tone(f, d, decay, ((1, 1), (3, .33), (5, .2), (7, .12)))      # soft square (4 harmonics only)
def ding(f=1046.5): return tone(f, 1.0, 5, ((1, 1), (2, .35), (3.01, .12)))

class Track:
    def __init__(self, dur): self.n = int(dur * SR); self.a = np.zeros(self.n + SR * 2)
    def add(self, sig, t, g=1.0):
        i = int(t * SR)
        if 0 <= i < len(self.a): m = min(len(sig), len(self.a) - i); self.a[i:i + m] += sig[:m] * g
    def save(self, path, peak=.89):
        a = self.a[:self.n]; a = a - a.mean(); a = a / max(np.abs(a).max(), 1e-6) * peak
        n = self.n; a *= np.minimum(1, np.arange(n) / (.03 * SR)) * np.minimum(1, (n - np.arange(n)) / (.5 * SR))
        st = np.stack([a, a], 1)
        with wave.open(path, "w") as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype(np.int16).tobytes())

# ---------- encode / preview ----------
_R = None; _DIR = None
def _job(i):
    _R(i / FPS).convert("RGB").save(f"{_DIR}/{i:05d}.jpg", quality=93)
def main(render, dur, audio):
    global _R, _DIR
    _R = render
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        d = Path(sys.argv[2]); d.mkdir(parents=True, exist_ok=True)
        for s in sys.argv[3:]: render(float(s)).convert("RGB").save(d / f"t{float(s):05.2f}.jpg", quality=90)
        return
    if len(sys.argv) > 1 and sys.argv[1] == "audio": audio(sys.argv[2]); return
    with tempfile.TemporaryDirectory() as tmp:
        _DIR = tmp; audio(f"{tmp}/a.wav")
        with Pool(os.cpu_count()) as p: p.map(_job, range(int(dur * FPS)), chunksize=8)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", f"{tmp}/%05d.jpg", "-i", f"{tmp}/a.wav", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", f"{dur:.2f}", sys.argv[1]], check=True)
