"""Clean soundtrack for paper reels: soft music bed (pure tones, no noise), clock ticks, answer chime.
No noise-based sounds at all (the old pencil 'scratch' and 110 Hz hum were heard as interference).
build(path, dur, ticks=[(t, loud)], dings=[t], bpm=88)
"""
import wave
import numpy as np

SR = 44100

def _env(n, a, r):
    e = np.ones(n); ai = int(a * SR); ri = int(r * SR)
    if ai: e[:ai] = np.linspace(0, 1, ai)
    if ri: e[-ri:] *= np.linspace(1, 0, ri)
    return e

def _tone(f, dur, decay=None, harm=((1, 1.0),)):
    t = np.arange(int(dur * SR)) / SR
    x = sum(g * np.sin(2 * np.pi * f * k * t) for k, g in harm)
    if decay: x = x * np.exp(-t * decay)
    return x

def music(dur, bpm=88, seed=1):
    """C - G - Am - F, warm pad + soft plucked arpeggio + sine bass."""
    n = int(dur * SR); out = np.zeros(n + SR * 2)
    beat = 60 / bpm; bar = beat * 4
    chords = [(261.63, 329.63, 392.00), (196.00, 246.94, 293.66), (220.00, 261.63, 329.63), (174.61, 220.00, 261.63)]
    bass = [130.81, 98.00, 110.00, 87.31]
    t0, k = 0.0, 0
    while t0 < dur + bar:
        ch = chords[k % 4]; i = int(t0 * SR); L = int((bar + .6) * SR)
        if i >= len(out): break
        pad = sum(_tone(f, bar + .6, harm=((1, 1), (2, .18))) + _tone(f * 1.003, bar + .6) * .6 for f in ch) * _env(L, .5, .6)
        m = min(L, len(out) - i); out[i:i + m] += pad[:m] * .05
        b = _tone(bass[k % 4], bar, harm=((1, 1), (2, .25))) * _env(int(bar * SR), .03, .4)
        m = min(len(b), len(out) - i); out[i:i + m] += b[:m] * .09
        for s in range(8):                                   # eighth-note arpeggio, soft and decaying
            f = ch[[0, 1, 2, 1, 0, 2, 1, 2][s]] * 2
            p = _tone(f, beat * 1.4, decay=6, harm=((1, 1), (2, .3), (3, .08))) * _env(int(beat * 1.4 * SR), .004, .05)
            j = int((t0 + s * beat / 2) * SR)
            if j < len(out): m = min(len(p), len(out) - j); out[j:j + m] += p[:m] * (.05 if s % 2 else .07)
        t0 += bar; k += 1
    return out[:n]

def tick(loud=False):
    f = 1500 if loud else 1150
    x = _tone(f, .07, decay=70, harm=((1, 1), (2.01, .25)))
    return x * _env(len(x), .001, .01)

def ding():
    return _tone(1046.5, 1.1, decay=4.5, harm=((1, 1), (2.0, .35), (3.01, .12))) * _env(int(1.1 * SR), .002, .1)

def build(path, dur, ticks=(), dings=(), bpm=88):
    n = int(dur * SR); a = np.zeros(n + SR * 2)
    def add(sig, t, g):
        i = int(t * SR)
        if 0 <= i < len(a): m = min(len(sig), len(a) - i); a[i:i + m] += sig[:m] * g
    a[:n] += music(dur, bpm)
    for t, loud in ticks: add(tick(loud), t, .32 if loud else .24)
    for t in dings: add(ding(), t, .26)
    a = a[:n]
    a -= a.mean()
    peak = np.abs(a).max(); a = a / max(peak, 1e-6) * .89
    a *= np.minimum(1, np.arange(n) / (.08 * SR)) * np.minimum(1, (n - np.arange(n)) / (.6 * SR))
    st = np.stack([a, a], 1)
    with wave.open(path, "w") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype(np.int16).tobytes())
