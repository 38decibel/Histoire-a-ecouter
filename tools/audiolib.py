"""Petite boîte à outils audio (numpy) : chargement, découpe, fondus, synthèse de sons magiques."""
import subprocess, numpy as np
from scipy.signal import butter, sosfilt

SR = 24000
import os
RAW = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'build', 'sfx_raw') + '/'
rng = np.random.default_rng(7)


def load(f, start=0.0, dur=None, sr=SR):
    args = ['ffmpeg', '-v', 'error', '-ss', str(start)]
    if dur:
        args += ['-t', str(dur)]
    args += ['-i', f if '/' in f else RAW + f + '.mp3', '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-']
    b = subprocess.run(args, capture_output=True).stdout
    return np.frombuffer(b, np.float32).astype(np.float64)


def save_wav(x, path, sr=SR):
    x = np.clip(x, -1, 1).astype(np.float32)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(sr), '-ac', '1', '-i', '-', path],
                   input=x.tobytes(), check=True)


def save_mp3(x, path, br='64k', sr=SR):
    x = np.clip(x, -1, 1).astype(np.float32)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(sr), '-ac', '1', '-i', '-',
                    '-codec:a', 'libmp3lame', '-b:a', br, path], input=x.tobytes(), check=True)


def fade(x, fin=0.01, fout=0.05):
    x = x.copy()
    a, b = int(fin * SR), int(fout * SR)
    if a: x[:a] *= np.linspace(0, 1, a)
    if b: x[-b:] *= np.linspace(1, 0, b) ** 2
    return x


def norm(x, peak_db=-3.0):
    p = np.abs(x).max() + 1e-9
    return x / p * 10 ** (peak_db / 20)


def rms_norm(x, db=-20.0):
    r = np.sqrt((x ** 2).mean()) + 1e-9
    return x / r * 10 ** (db / 20)


def lp(x, f, order=4):
    return sosfilt(butter(order, f, 'low', fs=SR, output='sos'), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, 'high', fs=SR, output='sos'), x)


def silence(d):
    return np.zeros(int(d * SR))


def mix(*parts):
    """parts = (signal, offset_seconds, gain)"""
    end = max(int(o * SR) + len(s) for s, o, g in parts)
    out = np.zeros(end)
    for s, o, g in parts:
        i = int(o * SR)
        out[i:i + len(s)] += s * g
    return out


def trim(x, thr_db=-45):
    a = np.abs(x)
    thr = a.max() * 10 ** (thr_db / 20)
    idx = np.where(a > thr)[0]
    if len(idx) == 0:
        return x
    return x[max(0, idx[0] - int(0.005 * SR)): idx[-1] + int(0.02 * SR)]


def reverb(x, wet=0.3, length=1.6, seed=1):
    r = np.random.default_rng(seed)
    n = int(length * SR)
    ir = r.standard_normal(n) * np.exp(-np.linspace(0, 7, n))
    ir = lp(ir, 6000)
    ir /= np.sqrt((ir ** 2).sum())
    y = np.convolve(x, ir)[:len(x) + n]
    out = np.zeros(len(y)); out[:len(x)] = x
    return out * (1 - wet) + y * wet


def echo(x, delay=0.28, fb=0.45, n=4):
    out = np.zeros(len(x) + int(delay * SR * n))
    for k in range(n + 1):
        i = int(k * delay * SR)
        out[i:i + len(x)] += x * fb ** k
    return out


def repeat(x, n, gap):
    return mix(*[(x, k * gap, 1.0) for k in range(n)])


# ---------- synthèse ----------
def note_freq(n):
    """n : nom style 'C6', 'G#5'"""
    names = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
    s = names[n[0]] + (1 if '#' in n else 0)
    o = int(n[-1])
    return 440 * 2 ** ((s + 12 * (o + 1) - 69) / 12)


def bell(f, dur=1.5, decay=3.0, partials=((1, 1), (2.76, .45), (5.40, .25), (8.93, .1))):
    t = np.arange(int(dur * SR)) / SR
    y = np.zeros_like(t)
    for m, a in partials:
        if f * m < SR / 2 - 500:
            y += a * np.sin(2 * np.pi * f * m * t) * np.exp(-t * decay * (1 + 0.6 * m ** 0.5))
    att = int(0.002 * SR)
    y[:att] *= np.linspace(0, 1, att)
    return y


def glock(f, dur=1.6):
    return bell(f, dur, decay=2.2, partials=((1, 1), (2.0, .18), (3.0, .12), (4.1, .08)))


def musicbox(f, dur=1.8):
    return bell(f, dur, decay=1.8, partials=((1, 1), (2.0, .25), (3.97, .2), (6.1, .05)))


def sparkle(dur=1.0, n=14, lo=2000, hi=6000, rising=False, density_up=False, seed=3):
    r = np.random.default_rng(seed)
    parts = []
    for k in range(n):
        u = r.random()
        if density_up:
            u = u ** 0.6
        t0 = u * dur
        frac = t0 / dur if rising else r.random()
        f = lo + (hi - lo) * (frac if rising else r.random())
        parts.append((bell(f, 0.5, decay=9), t0, 0.25 + 0.35 * r.random()))
    return reverb(mix(*parts), wet=0.35, length=1.2)


def gliss(f0, f1, dur, seed=5):
    """arpège pentatonique ascendant rapide (effet harpe magique)"""
    penta = [0, 2, 4, 7, 9]
    notes = []
    m0, m1 = 12 * np.log2(f0 / 440) + 69, 12 * np.log2(f1 / 440) + 69
    m = int(m0)
    while m <= m1:
        if m % 12 in penta:
            notes.append(m)
        m += 1
    parts = []
    for i, mm in enumerate(notes):
        parts.append((glock(440 * 2 ** ((mm - 69) / 12), 0.9), i * dur / max(1, len(notes)), 0.5))
    return reverb(mix(*parts), wet=0.3)


def loopify(x, xf=2.0):
    """rend une boucle sans couture par fondu enchaîné fin→début"""
    n = int(xf * SR)
    body = x[:-n].copy()
    tail = x[-n:]
    w = np.linspace(0, 1, n)
    body[:n] = body[:n] * np.sqrt(w) + tail * np.sqrt(1 - w)
    return body
