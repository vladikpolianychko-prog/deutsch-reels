"""Synthesize the sound design for the reel from sfx.json (event list exported by reel.html)."""
import json
import wave
from pathlib import Path

import numpy as np
from scipy import signal

ROOT = Path(__file__).resolve().parent
SR = 44100
DUR = 25.0
rng = np.random.default_rng(7)


def env_ad(n, a=0.01, d=0.02):
    e = np.ones(n)
    na, nd = max(1, int(a * SR)), max(1, int(d * SR))
    e[:na] = np.linspace(0, 1, na)
    e[-nd:] *= np.linspace(1, 0, nd)
    return e


def bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], btype="band", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def lp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, btype="low", fs=SR, output="sos"), x)


def scribble(dur):
    """Felt marker on paper: band-limited noise shaped into quick strokes."""
    n = int(dur * SR)
    noise = rng.standard_normal(n)
    hi = bp(noise, 1800, 6500) * 0.8 + bp(noise, 350, 1100) * 0.35
    # strokes: 9-14 per second with random weight
    t = np.arange(n) / SR
    rate = rng.uniform(9, 14)
    phase = rng.uniform(0, 1)
    strokes = np.abs(np.sin(np.pi * (t * rate + phase))) ** 1.6
    weights = np.repeat(rng.uniform(.45, 1.0, int(dur * rate) + 3), int(SR / rate) + 1)[:n]
    e = strokes * weights * env_ad(n, .015, .04)
    return hi * e * 0.22


def swipe(dur):
    n = int(dur * SR)
    x = bp(rng.standard_normal(n), 700, 3200)
    e = np.sin(np.linspace(0, np.pi, n)) ** .7
    return x * e * 0.16


def pop(dur=.12):
    n = int(.12 * SR)
    t = np.arange(n) / SR
    f = 950 * np.exp(-t * 22) + 320
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t * 38)
    click = bp(rng.standard_normal(n), 2000, 7000) * np.exp(-t * 300) * .4
    return (s + click) * 0.33


def tick(dur=.06):
    n = int(.06 * SR)
    t = np.arange(n) / SR
    return bp(rng.standard_normal(n), 2500, 8000) * np.exp(-t * 160) * 0.18


def ding(dur=.8):
    n = int(1.1 * SR)
    t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * 1318.5 * t) * np.exp(-t * 5.5) * .55 +
         np.sin(2 * np.pi * 1975.5 * t) * np.exp(-t * 7) * .35 +
         np.sin(2 * np.pi * 2637 * t) * np.exp(-t * 10) * .15)
    return s * env_ad(n, .003, .2) * 0.2


def flip(dur=.7):
    """Page turn: airy rustle with falling brightness and a soft landing flap."""
    n = int(.75 * SR)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    # time-varying lowpass via crossfading three bands
    b1, b2, b3 = lp(noise, 5500), lp(noise, 2500), lp(noise, 900)
    w = np.clip(t / .55, 0, 1)
    x = b1 * (1 - w) ** 2 + b2 * 2 * w * (1 - w) + b3 * w ** 2
    rustle = np.abs(np.sin(np.pi * t * 7)) ** 2 * .5 + .5
    e = np.sin(np.clip(t / .6, 0, 1) * np.pi) ** 1.2
    flap = np.sin(2 * np.pi * 85 * t) * np.exp(-np.maximum(t - .52, 0) * 30) * (t > .52)
    return (x * e * rustle * .28 + flap * .35)


def peel(dur=.3):
    n = int(max(dur, .25) * SR)
    t = np.arange(n) / SR
    crackle = (rng.random(n) < np.linspace(.002, .02, n)) * rng.uniform(-1, 1, n)
    x = bp(crackle * 3 + rng.standard_normal(n) * .25, 1500, 7500)
    return x * env_ad(n, .02, .06) * 0.3


def whoosh(dur, big=False):
    n = int(dur * SR)
    t = np.linspace(0, 1, n)
    noise = rng.standard_normal(n)
    # sweep a resonant band up then down by blending fixed bands
    bands = [bp(noise, f * .7, f * 1.4) for f in (300, 650, 1300, 2400)]
    pos = np.sin(t * np.pi) * 3  # 0 -> 3 -> 0
    out = np.zeros(n)
    for i, b in enumerate(bands):
        out += b * np.clip(1 - np.abs(pos - i), 0, 1)
    e = np.sin(t * np.pi) ** 2
    g = .5 if big else .3
    mono = out * e * g
    pan = np.clip(t, 0, 1)  # left -> right
    return np.stack([mono * np.cos(pan * np.pi / 2), mono * np.sin(pan * np.pi / 2)], axis=1) * 1.4


def thump(dur=.25, big=False):
    n = int(.35 * SR)
    t = np.arange(n) / SR
    f = 140 * np.exp(-t * 12) + 55
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 16)
    paper = bp(rng.standard_normal(n), 600, 3500) * np.exp(-t * 60)
    return (s * (.7 if big else .45) + paper * (.35 if big else .22)) * 0.75


def slap(dur=.2):
    n = int(.25 * SR)
    t = np.arange(n) / SR
    x = bp(rng.standard_normal(n), 500, 3000) * np.exp(-t * 45) * .6
    low = np.sin(2 * np.pi * 150 * t) * np.exp(-t * 28) * .5
    return (x + low) * 0.5


def rise(dur=.5):
    n = int(dur * SR)
    t = np.linspace(0, 1, n)
    noise = rng.standard_normal(n)
    bands = [bp(noise, f * .7, f * 1.4) for f in (400, 900, 1800)]
    pos = t * 2
    out = sum(b * np.clip(1 - np.abs(pos - i), 0, 1) for i, b in enumerate(bands))
    return out * np.sin(t * np.pi) ** 1.5 * .22


def snap(dur=.1):
    n = int(.14 * SR)
    t = np.arange(n) / SR
    crack = bp(rng.standard_normal(n), 1800, 9000) * np.exp(-t * 90)
    body = np.sin(2 * np.pi * 420 * t) * np.exp(-t * 60) * .3
    return (crack * .9 + body) * .42


def glow(dur=.5):
    n = int(1.0 * SR)
    t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * t + i) * a for i, (f, a) in enumerate(((880, .4), (1318.5, .3), (1760, .2), (2637, .1))))
    trem = .75 + .25 * np.sin(2 * np.pi * 9 * t)
    return s * trem * np.minimum(t / .25, 1) * np.exp(-np.maximum(t - .25, 0) * 4) * .09


def slide(dur=.7):
    n = int(dur * SR)
    t = np.linspace(0, 1, n)
    x = bp(rng.standard_normal(n), 900, 4000)
    return x * np.sin(t * np.pi) ** .8 * .12


def chime(dur=1.0):
    n = int(1.6 * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for k, f in enumerate((1046.5, 1318.5, 1568.0, 2093.0)):
        d = int(k * .09 * SR)
        tt = t[: n - d]
        out[d:] += (np.sin(2 * np.pi * f * tt) * .6 + np.sin(2 * np.pi * f * 2 * tt) * .15) * np.exp(-tt * 3.2)
    return out * .1


def click(dur=.1, big=False):
    """Plug snapping into a socket: two plastic transients + a tiny low body."""
    n = int(.16 * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for d, g in ((0, 1.0), (.014, .7)):
        k = int(d * SR)
        tt = t[: n - k]
        out[k:] += bp(rng.standard_normal(n - k), 2500, 9000) * np.exp(-tt * 420) * g
        out[k:] += np.sin(2 * np.pi * 1900 * tt) * np.exp(-tt * 260) * .35 * g
    out += np.sin(2 * np.pi * 180 * t) * np.exp(-t * 45) * (.4 if big else .2)
    return out * (.55 if big else .4)


def ring(dur=.6):
    """Old telephone bell: two bell tones struck by a 22 Hz hammer."""
    n = int(.62 * SR)
    t = np.arange(n) / SR
    bell = sum(np.sin(2 * np.pi * f * t) * a for f, a in ((1180, .5), (1420, .4), (2360, .18), (3540, .08)))
    hammer = (np.sin(2 * np.pi * 22 * t) > 0).astype(float)
    hammer = lp(hammer, 300)
    e = np.minimum(t / .01, 1) * np.exp(-np.maximum(t - .45, 0) * 18)
    return bell * (.55 + .45 * hammer) * e * .13


def boing(dur=.4, small=False):
    """Coiled cord springing: a wobbling low tone with a metallic twang."""
    n = int(.5 * SR)
    t = np.arange(n) / SR
    f = (210 if not small else 330) * (1 + .3 * np.sin(2 * np.pi * 11 * t) * np.exp(-t * 5))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)
    tw = np.sin(2 * np.pi * np.cumsum(f * 4.1) / SR) * np.exp(-t * 14) * .25
    return (s + tw) * (.22 if small else .32)


def stretch(dur=.5):
    """Cord being pulled longer: rising wobble + faint creak."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 160 + 260 * (t / dur) + 25 * np.sin(2 * np.pi * 17 * t)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / dur) ** .8
    creak = bp(rng.standard_normal(n), 1200, 3800) * (np.abs(np.sin(2 * np.pi * 34 * t)) ** 6)
    return (s * .2 + creak * .1)


GEN = {"scribble": scribble, "swipe": swipe, "pop": pop, "tick": tick, "ding": ding, "flip": flip,
       "peel": peel, "slap": slap, "rise": rise, "snap": snap, "glow": glow, "slide": slide, "chime": chime,
       "click": click, "ring": ring, "boing": boing, "stretch": stretch}


def main():
    events = json.loads((ROOT / "sfx.json").read_text())
    # camera moves into / out of the diorama get a soft swish
    events += []
    mix = np.zeros((int(DUR * SR) + SR, 2))
    for ev in events:
        typ, t0, dur = ev["type"], ev["t"], max(ev.get("dur", .2), .05)
        if typ == "whoosh":
            snd = whoosh(dur, ev.get("big", False))
        elif typ == "click":
            snd = click(dur, ev.get("big", False))
        elif typ == "boing":
            snd = boing(dur, ev.get("small", False))
        elif typ == "thump":
            snd = thump(dur, ev.get("big", False))
            if ev.get("big"):
                p = pop()
                snd[:len(p)] += p * .6
        else:
            snd = GEN[typ](dur)
        if snd.ndim == 1:
            pan = rng.uniform(-.25, .25)
            snd = np.stack([snd * (1 - pan), snd * (1 + pan)], axis=1) * .8
        i0 = int(t0 * SR)
        i1 = min(len(mix), i0 + len(snd))
        mix[i0:i1] += snd[: i1 - i0]
    # gentle room reverb: two short taps
    for d, g in ((.031, .18), (.057, .1)):
        k = int(d * SR)
        mix[k:] += mix[:-k] * g
    mix = mix[: int(DUR * SR)]
    peak = np.max(np.abs(mix))
    mix = np.tanh(mix / peak * 1.3) / np.tanh(1.3) * .89
    data = (mix * 32767).astype(np.int16)
    with wave.open(str(ROOT / "sfx.wav"), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
    print("events:", len(events), "peak:", float(np.max(np.abs(mix))))


if __name__ == "__main__":
    main()
