"""Add character voices (cfg "voices") on top of mix.wav, ducking music/sfx under speech. Writes mix.wav in place."""
import json, os, subprocess, sys, wave
import numpy as np
from pathlib import Path
ROOT = Path(__file__).resolve().parent; SR = 44100
cfg = json.load(open(os.environ["CFG"], encoding="utf-8"))
w = wave.open("mix.wav"); base = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2) / 32768.; w.close()
voice = np.zeros(len(base)); duck = np.ones(len(base))
for v in cfg.get("voices", []):
    path = v["file"] if os.path.isabs(v["file"]) else str(ROOT / v["file"])
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.int16) / 32768.; x = x / (np.max(np.abs(x)) + 1e-9) * .92
    i0 = int(v["t"] * SR); i1 = min(len(base), i0 + len(x)); voice[i0:i1] += x[: i1 - i0]
    a, b = max(0, i0 - int(.12 * SR)), min(len(base), i1 + int(.2 * SR)); duck[a:b] = .38
k = int(.08 * SR); duck = np.convolve(duck, np.ones(k) / k, "same")
out = base * duck[:, None] * .9 + voice[:, None] * .95
out = np.tanh(out * 1.05) / np.tanh(1.05); out *= .92 / np.max(np.abs(out))
with wave.open("mix.wav", "wb") as o:
    o.setnchannels(2); o.setsampwidth(2); o.setframerate(SR); o.writeframes((out * 32767).astype(np.int16).tobytes())
print("voices mixed", len(cfg.get("voices", [])))
