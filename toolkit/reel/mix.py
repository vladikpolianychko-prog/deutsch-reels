"""Mix the synthesized music bed with UI sound effects for the 12 s aus- reel."""
import sys, wave
import numpy as np
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sfx as S

import os, json
SR, DUR = 44100, float(os.environ.get("DUR", "12"))
def load(p):
    w = wave.open(p); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2) / 32767; return x
import os
SRC = os.environ.get("MUSIC", "music.wav")
OFF = int(float(os.environ.get("OFFSET", "0")) * SR)
music = load(SRC)[OFF: OFF + int(DUR * SR)].copy()
if SRC != "music.wav":                      # mastered AI track: tame it under the voice-less UI sounds, soft tail for the loop
    music *= .42 / max(1e-9, np.sqrt(np.mean(music ** 2))) * .2
    n = int(.45 * SR); music[-n:] *= np.linspace(1, .35, n)[:, None]
    m = int(.05 * SR); music[:m] *= np.linspace(.6, 1, m)[:, None]
ev = json.load(open(os.environ["EV"]))
fx = np.zeros((int(DUR * SR) + SR, 2))
rng = np.random.default_rng(4)
for typ, t0, dur in ev:
    snd = S.whoosh(dur, False) if typ == "whoosh" else S.GEN[typ](dur)
    if snd.ndim == 1:
        pan = rng.uniform(-.2, .2); snd = np.stack([snd * (1 - pan), snd * (1 + pan)], axis=1)
    i0 = int(t0 * SR); i1 = min(len(fx), i0 + len(snd)); fx[i0:i1] += snd[: i1 - i0] * .85
fx = fx[: int(DUR * SR)]
fx /= max(1e-9, np.max(np.abs(fx))); fx *= .7
mix = music * (.55 if SRC == "music.wav" else 1.0) + fx * .6
mix = np.tanh(mix * 1.15) / np.tanh(1.15)
mix *= .89 / np.max(np.abs(mix))
with wave.open("mix.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("mix.wav ok", float(np.sqrt(np.mean(mix ** 2))))
