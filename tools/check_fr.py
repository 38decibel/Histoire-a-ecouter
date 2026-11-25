"""Vérifie la prononciation de chaque morceau de voix : on le fait transcrire par Whisper (reconnaissance
vocale, forcée en français) et on compare au texte attendu. Un écart signale un mot mal prononcé
(accent anglais ou espagnol, mot lu de travers…).

Usage : python3 tools/check_fr.py [seuil]      (pip install faster-whisper)
"""
import difflib, hashlib, json, os, re, subprocess, sys, unicodedata
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import gen_clips as g
from faster_whisper import WhisperModel

SEUIL = float(sys.argv[1]) if len(sys.argv) > 1 else 0.88


def a16(path):
    b = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'],
                       capture_output=True).stdout
    return np.frombuffer(b, np.float32)


def norm(t):
    t = unicodedata.normalize('NFD', t.lower())
    t = ''.join(c for c in t if unicodedata.category(c) != 'Mn')
    t = t.replace('œ', 'oe')
    return re.sub(r'[^a-z0-9]+', ' ', t).strip()


model = WhisperModel('small', device='cpu', compute_type='int8')
import asyncio
clips = g.parse()
seen, bad = set(), []
sem = asyncio.Semaphore(1)
for cid, clip in clips.items():
    for spk, line in clip['lines']:
        for r in g.runs(g.tokens(cid, spk, line)).values():
            k = g.run_key(r)
            if k in seen:
                continue
            seen.add(k)
            path, _ = asyncio.run(g.tts(k, sem))
            text = ' '.join(k[1])
            segs, info = model.transcribe(a16(path), beam_size=5, language='fr')
            heard = ''.join(s.text for s in segs).strip()
            ratio = difflib.SequenceMatcher(None, norm(text), norm(heard)).ratio()
            if ratio < SEUIL:
                bad.append((ratio, cid, k[0], text, heard))
for r, cid, v, t, h in sorted(bad):
    print(f'{r:.2f} {cid} [{v}]\n   texte : {t}\n   entendu : {h}')
print(len(bad), 'groupes suspects sur', len(seen))
