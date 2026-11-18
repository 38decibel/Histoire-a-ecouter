"""Génère les clips MP3 de l'histoire à partir de source/histoire.txt.

Voix : synthèse neuronale Microsoft (edge-tts) — narrateur Henri, Lumina Éloïse.
Bruitages : build/sfx/*.wav (voir build_sfx.py), insérés aux balises {nom}.
Sortie : docs/audio/clips/ID.mp3 + docs/clips.json (durées, ambiances).

Usage : python3 tools/gen_clips.py [ID ...]   (sans argument : tous les clips)
"""
import asyncio, hashlib, json, os, re, subprocess, sys
import numpy as np
import edge_tts

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'source', 'histoire.txt')
SFX = os.path.join(ROOT, 'build', 'sfx')
CACHE = os.path.join(ROOT, 'build', 'tts_cache')
OUT = os.path.join(ROOT, 'docs', 'audio', 'clips')
META = os.path.join(ROOT, 'docs', 'clips.json')
SR = 24000

VOICES = {
    'N': dict(voice='fr-FR-RemyMultilingualNeural', rate='-4%', pitch='+0Hz'),   # narrateur
    'L': dict(voice='fr-FR-EloiseNeural', rate='-4%', pitch='+4Hz'),             # Lumina
    # voix des animaux : voix de synthèse + effets (rubberband décale la hauteur ET le timbre → voix de dessin animé)
    'lapin': dict(voice='fr-FR-EloiseNeural', rate='+6%', pitch='+0Hz',
                  fx='rubberband=pitch=1.38:tempo=1.0'),
    'herisson': dict(voice='fr-FR-EloiseNeural', rate='+0%', pitch='+0Hz',
                     fx='rubberband=pitch=1.22,equalizer=f=3000:t=q:w=1:g=4'),
    'cane': dict(voice='fr-FR-DeniseNeural', rate='+4%', pitch='+0Hz',
                 fx='rubberband=pitch=1.28,highpass=f=450,equalizer=f=1400:t=q:w=0.8:g=10,tremolo=f=11:d=0.3'),
    'grenouille': dict(voice='fr-FR-EloiseNeural', rate='-2%', pitch='+0Hz',
                       fx='rubberband=pitch=0.82,tremolo=f=19:d=0.55,equalizer=f=700:t=q:w=1:g=5'),
    'luciole': dict(voice='fr-FR-EloiseNeural', rate='+4%', pitch='+0Hz',
                    fx='rubberband=pitch=1.55,aecho=0.8:0.6:60|120:0.25|0.15'),
    'hibou': dict(voice='fr-FR-RemyMultilingualNeural', rate='-14%', pitch='+0Hz',
                  fx='rubberband=pitch=0.74,vibrato=f=5:d=0.08,aecho=0.8:0.5:90:0.2'),
}
QUOTE_STYLE = [(r'E3-H', 'hibou'), (r'lapin', 'lapin'), (r'herisson', 'herisson'), (r'canards', 'cane'),
               (r'grenouille', 'grenouille'), (r'E3-G', 'luciole')]

GAP_LINE = 0.55     # respiration entre deux paragraphes
GAP_CHUNK = 0.12    # entre deux morceaux d'une même ligne
REPEAT_GAP = {'croc': 0.5, 'boing': 0.38}
LEAD = {'carillon': None, 'ruisseau_loin': None, 'fee_long': 2.2, 'fee_depart': 2.0, 'jingle_etoile': 1.6,
        'jingle_etoile_doux': None, 'reveil_lucioles': 1.8, 'envol': 1.8, 'voix_lointaine': 2.6, 'vent': 1.2,
        'abeille': 1.4, 'pas_feuilles': 1.6, 'pas_herbe': 1.5, 'tintement3': 1.5, 'gouttes': 1.4}
# None = on attend la fin du son ; sinon la voix reprend après LEAD secondes (le son continue dessous)


def parse():
    clips, cur = {}, None
    for raw in open(SRC, encoding='utf-8'):
        line = raw.rstrip('\n')
        if not line.strip() or line.startswith('#'):
            continue
        if line.startswith('=== '):
            cur = line[4:].strip(); clips[cur] = {'amb': None, 'lines': []}; continue
        if line.startswith('@amb '):
            clips[cur]['amb'] = line[5:].strip(); continue
        spk = 'N'
        if line.startswith('L:'):
            spk, line = 'L', line[2:].strip()
        clips[cur]['lines'].append((spk, line.strip()))
    return clips


def quote_style(cid):
    for pat, st in QUOTE_STYLE:
        if re.search(pat, cid):
            return st
    return 'N'


def tokens(cid, spk, line):
    """découpe une ligne en événements : ('say', voix, texte) / ('sfx', nom, n) / ('pause', s) / ('amb', nom)"""
    ev = []
    for part in re.split(r'(\{[^}]*\})', line):
        if not part.strip():
            continue
        if part.startswith('{'):
            tag = part[1:-1].strip()
            if tag.startswith('@amb'):
                ev.append(('amb', tag.split()[1]))
            elif tag.startswith('pause'):
                p = tag.split()
                ev.append(('pause', float(p[1]) if len(p) > 1 else 2.0))
            else:
                m = re.match(r'(\w+)(?:\s*x(\d+))?', tag)
                ev.append(('sfx', m.group(1), int(m.group(2) or 1)))
        else:
            # paroles rapportées « … » avec une voix de personnage (narrateur seulement)
            if spk == 'N' and '«' in part and quote_style(cid) != 'N':
                for sub in re.split(r'(«[^»]*»)', part):
                    if sub.strip(' ,'):
                        v = quote_style(cid) if sub.startswith('«') else 'N'
                        ev.append(('say', v, sub.strip('«» ').strip()))
            else:
                ev.append(('say', spk, part.strip()))
    return ev


def load_wav(path):
    b = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                       capture_output=True, check=True).stdout
    return np.frombuffer(b, np.float32).astype(np.float64)


def trim(x, thr=0.01):
    idx = np.where(np.abs(x) > thr * np.abs(x).max())[0]
    if not len(idx):
        return x
    return x[max(0, idx[0] - 240): idx[-1] + 480]


async def tts(voice, text, sem):
    p = VOICES[voice]
    key = hashlib.md5(json.dumps([p, text]).encode()).hexdigest()
    path = os.path.join(CACHE, key + '.mp3')
    if not os.path.exists(path):
        async with sem:
            for attempt in range(4):
                try:
                    await edge_tts.Communicate(text, p['voice'], rate=p['rate'], pitch=p['pitch']).save(path + '.tmp')
                    if p.get('fx'):
                        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', path + '.tmp', '-af', p['fx'], '-f', 'mp3', path + '.fx'], check=True)
                        os.replace(path + '.fx', path); os.remove(path + '.tmp')
                    else:
                        os.replace(path + '.tmp', path)
                    break
                except Exception as e:
                    print('  retry', attempt, text[:40], e); await asyncio.sleep(2)
    return path


def place(track, x, t):
    i = int(t * SR)
    if i + len(x) > len(track):
        track = np.concatenate([track, np.zeros(i + len(x) - len(track) + SR)])
    track[i:i + len(x)] += x
    return track


def build(cid, clip, tts_paths, sfx_cache):
    voice, fx = np.zeros(SR * 5), np.zeros(SR * 5)
    t, end, ambs = 0.25, 0.0, []
    for li, (spk, line) in enumerate(clip['lines']):
        if li:
            t += GAP_LINE
        for e in tokens(cid, spk, line):
            if e[0] == 'say':
                x = trim(load_wav(tts_paths[(e[1], e[2])]))
                voice = place(voice, x * 0.9, t); t += len(x) / SR + GAP_CHUNK
            elif e[0] == 'pause':
                t += e[1]
            elif e[0] == 'amb':
                ambs.append({'at': round(t, 2), 'amb': e[1]})
            else:
                name, n = e[1], e[2]
                x = sfx_cache.setdefault(name, load_wav(os.path.join(SFX, name + '.wav')))
                g = REPEAT_GAP.get(name, 0.45)
                for k in range(n):
                    fx = place(fx, x * 0.55, t + k * g)
                dur = (n - 1) * g + len(x) / SR
                lead = LEAD.get(name, min(dur, 1.0 + (n - 1) * g))
                end = max(end, t + dur)
                t += dur if lead is None else lead
                t += 0.08
            end = max(end, t)
    n = int((end + 0.4) * SR)
    voice, fx = np.pad(voice, (0, max(0, n - len(voice))))[:n], np.pad(fx, (0, max(0, n - len(fx))))[:n]
    # les bruitages s'effacent un peu quand la voix parle
    env = np.convolve(np.abs(voice), np.ones(1200) / 1200, 'same')
    duck = 1 - 0.55 * np.clip(env / (env.max() * 0.15 + 1e-9), 0, 1)
    duck = np.convolve(duck, np.ones(2400) / 2400, 'same')
    y = voice + fx * duck
    return y, ambs


def encode(y, path):
    y = np.clip(y / (np.abs(y).max() + 1e-9) * 0.89, -1, 1).astype(np.float32)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-',
                    '-af', 'loudnorm=I=-17:TP=-1.5:LRA=11', '-ar', str(SR),
                    '-codec:a', 'libmp3lame', '-b:a', '64k', path], input=y.tobytes(), check=True)


async def main(only):
    os.makedirs(CACHE, exist_ok=True); os.makedirs(OUT, exist_ok=True)
    clips = parse()
    ids = only or list(clips)
    sem = asyncio.Semaphore(6)
    jobs = {}
    for cid in ids:
        for spk, line in clips[cid]['lines']:
            for e in tokens(cid, spk, line):
                if e[0] == 'say':
                    jobs[(e[1], e[2])] = None
    keys = list(jobs)
    paths = await asyncio.gather(*[tts(v, txt, sem) for v, txt in keys])
    tts_paths = dict(zip(keys, paths))
    meta = json.load(open(META)) if os.path.exists(META) else {}
    sfx_cache = {}
    for cid in ids:
        y, ambs = build(cid, clips[cid], tts_paths, sfx_cache)
        encode(y, os.path.join(OUT, cid + '.mp3'))
        meta[cid] = {'dur': round(len(y) / SR, 1), 'amb': clips[cid]['amb'], 'ambAt': ambs}
        print(f'{cid:24s} {len(y) / SR:5.1f}s', clips[cid]['amb'] or '', ambs or '')
    meta = {k: meta[k] for k in clips if k in meta}
    json.dump(meta, open(META, 'w'), ensure_ascii=False, indent=1)
    print('total', round(sum(m['dur'] for m in meta.values()) / 60, 1), 'min de clips,', len(meta), 'clips')


if __name__ == '__main__':
    asyncio.run(main(sys.argv[1:]))
