"""New playful bed for v6: plucked (Karplus-Strong) melody + soft bass + brushed shaker, 104 BPM, writes music_v6.wav."""
import os, wave
import numpy as np
SR = 44100; DUR = float(os.environ.get("DUR", "16")); BPM = 104; B = 60 / BPM
rng = np.random.default_rng(11)
def ks(freq, dur, bright=.5):
    n = int(dur * SR); p = max(2, int(SR / freq)); buf = rng.uniform(-1, 1, p); out = np.zeros(n)
    for i in range(n):
        out[i] = buf[i % p]; buf[i % p] = .996 * (bright * buf[i % p] + (1 - bright) * buf[(i + 1) % p]) if True else 0
    return out * np.exp(-np.arange(n) / SR * 2.2)
def note(m): return 440 * 2 ** ((m - 69) / 12)
mix = np.zeros((int(DUR * SR) + SR, 2))
def add(sig, t, pan=0., g=1.):
    i = int(t * SR); j = min(len(mix), i + len(sig)); mix[i:j, 0] += sig[: j - i] * g * (1 - pan); mix[i:j, 1] += sig[: j - i] * g * (1 + pan)
chords = [(60, 64, 67), (57, 60, 64), (53, 57, 60), (55, 59, 62)]          # C Am F G
mel = [76, 74, 72, 74, 76, 79, 76, None, 72, 74, 76, 72, 69, 72, 74, None]
t, k = 0.0, 0
cache = {}
def pl(m, d, br):
    key = (m, round(d, 2), br)
    if key not in cache: cache[key] = ks(note(m), d, br)
    return cache[key]
while t < DUR:
    ch = chords[(k // 8) % 4]
    if k % 2 == 0: add(pl(ch[0] - 12, B * 1.8, .5), t, 0, .55)                                   # bass on beats
    if k % 2 == 1: add(pl(ch[(k // 2) % 3], B * .9, .35), t, -.3, .28)                            # off-beat chord pluck
    m = mel[k % 16]
    if m and (k // 16) % 2 == 0 or (m and k % 4 == 0): add(pl(m, B * 1.2, .3), t, .3, .32)       # melody
    sh = rng.standard_normal(int(.06 * SR)) * np.exp(-np.arange(int(.06 * SR)) / SR * 70)            # shaker
    add(np.convolve(sh, [1, -1], "same") * (.10 if k % 2 else .05), t, .1)
    t += B / 2; k += 1
mix = mix[: int(DUR * SR)]
mix /= np.max(np.abs(mix)) + 1e-9; mix *= .8
n = int(.6 * SR); mix[-n:] *= np.linspace(1, .4, n)[:, None]
with wave.open("music_v6.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("music ok")
