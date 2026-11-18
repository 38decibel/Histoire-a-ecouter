"""Construit la banque de bruitages (build/sfx/*.wav) et les ambiances en boucle (app/audio/amb/*.mp3).
Sources : BigSoundBank.com (Joseph Sardin, libres de droits) + sons magiques synthétisés."""
import os
from audiolib import *

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = ROOT + '/build/sfx/'
AMB = ROOT + '/docs/audio/amb/'
os.makedirs(OUT, exist_ok=True); os.makedirs(AMB, exist_ok=True); os.makedirs(RAW, exist_ok=True)
import re, subprocess
# téléchargement des sons BigSoundBank manquants
for i in sorted(set(re.findall(r"load\('(\d{4})'", open(__file__).read()))):
    if not os.path.exists(RAW + i + '.mp3'):
        subprocess.run(['curl', '-s', '-o', RAW + i + '.mp3', f'https://bigsoundbank.com/UPLOAD/mp3/{i}.mp3'], check=True)
N = note_freq
S = {}

# ---- sons magiques (synthèse) ----
S['carillon'] = reverb(mix((glock(N('E6')), 0, .6), (glock(N('G6')), .18, .6), (glock(N('C7')), .36, .7)), .3)
S['jingle etoile'] = mix((gliss(N('C6'), N('C7'), .45), 0, .8),
                         (mix((glock(N('C6'), 2.2), 0, .5), (glock(N('E6'), 2.2), 0, .4), (glock(N('G6'), 2.2), 0, .4),
                              (glock(N('C7'), 2.2), 0, .5)), .5, .8),
                         (sparkle(1.6, 18, 3000, 7000, seed=11), .5, .6))
S['jingle etoile doux'] = lp(S['jingle etoile'], 3500) * .6
S['scintillement'] = sparkle(0.9, 12, 2500, 6500, seed=4)
S['ding'] = reverb(mix((glock(N('C6'), 1.2), 0, .7), (glock(N('G6'), 1.4), .12, .8)), .25)
S['tintement'] = reverb(bell(N('A6'), 1.6, decay=2.0), .3) * .8
S['tintement3'] = reverb(mix((bell(N('E6'), 1.5, 2), 0, .7), (bell(N('G6'), 1.5, 2), .38, .7), (bell(N('C7'), 1.8, 2), .76, .8)), .3)
S['reveil lucioles'] = mix((sparkle(2.2, 40, 1500, 7500, rising=True, density_up=True, seed=8), 0, 1),
                           (gliss(N('C5'), N('C7'), 1.6), .4, .5))
S['envol'] = mix((gliss(N('G4'), N('E7'), 1.4, seed=2), 0, .8), (hp(load('1796', .15, .5), 300), .1, .5),
                 (sparkle(1.8, 20, 3000, 7500, rising=True, seed=9), .3, .6))
S['pop'] = fade(np.sin(2 * np.pi * np.cumsum(np.linspace(900, 250, int(.06 * SR))) / SR) * np.exp(-np.linspace(0, 6, int(.06 * SR))), .002, .01)
S['fee long'] = mix((hp(load('2090', 0, 5.5), 400), 0, .7), (gliss(N('C5'), N('C7'), 1.2, seed=3), .2, .5),
                    (sparkle(2.5, 26, 2500, 7000, seed=12), .4, .5))
S['fee court'] = mix((hp(load('2088', 0, 2.6), 400), 0, .7), (sparkle(1.4, 14, 2500, 7000, seed=13), .1, .5))
S['fee depart'] = mix((hp(load('2090', 0, 5.5), 400), 0, .6), (sparkle(3.0, 26, 2000, 6500, seed=14), .2, .45))
S['fee depart'] *= np.linspace(1, 0, len(S['fee depart'])) ** 1.5
S['carillon leger'] = hp(load('2081', 0, 2.4), 300)
S['boing'] = load('2278', .15, .9)

# ---- bruitages réels (BigSoundBank) ----
S['zip'] = load('0270', 0, .7)
S['croc'] = load('1114', .15, .75)
S['abeille'] = load('1000', 1.0, 2.8)
S['pas feuilles'] = load('0137', 2.0, 3.0)
S['bruissement'] = lp(load('2889', 10.0, 2.2), 6000)
S['buisson'] = mix((load('2889', 30.0, 1.4), 0, 1), (load('1299', .5, .8), .3, .8))
S['reniflement'] = load('0784', 1.35, 1.6)
S['grattement'] = load('1305', 2.9, 1.2)
S['roulade'] = load('0137', 20.0, 2.2)
S['vent'] = lp(load('0146', 5.0, 3.0), 4000)
S['voix lointaine'] = lp(echo(hp(load('3255', 0.5, 2.0), 500), .32, .5, 5), 2500) * .6
S['ruisseau loin'] = lp(load('1354', 0, 4.5), 2500) * np.linspace(0.05, 1, int(4.5 * SR)) ** 1.5
S['tintements cristallins'] = mix(*[(glock(N(n), .9), i * .22, .5) for i, n in enumerate(['E7', 'G6', 'C7', 'A6', 'D7'])])
S['oiseau'] = load('1667', .15, 1.9)
S['grincement'] = load('3211', .15, 1.8)
S['clapotis'] = load('1514', 6.0, 2.5)
S['plouf'] = load('1529', 0, 1.6)
S['canards'] = load('0276', 7.4, 2.0)
S['grenouille'] = load('0819', 5.3, 1.6)
S['bulles'] = load('0150', 2.0, 2.0)
S['pas herbe'] = load('1253', 1.0, 2.5)
S['hibou'] = load('1764', 0, 1.3)
S['hibou joyeux'] = mix((load('3459', .25, 1.0), 0, 1), (load('3459', .25, 1.0), .7, .8))
S['gouttes'] = mix((load('1384', 1.4, .6), 0, 1), (load('1384', 4.3, .6), .7, .8), (load('1384', 7.2, .6), 1.5, .7))
S['gouttes'] = reverb(S['gouttes'], .4, 1.8)
S['miaou'] = load('1890', .05, 2.0)
S['meuh'] = load('2383', 1.0, 1.7)
S['cocorico'] = load('0283', .3, 2.0)
S['ailes'] = load('2893', .2, 1.2)

LEAD = {}  # temps (s) après lequel la voix peut reprendre (le reste du son passe sous la voix)
for k, x in S.items():
    x = trim(x) if k not in ('ruisseau loin',) else x
    x = fade(x, .005, min(.25, len(x) / SR * .3))
    peak = {'ruisseau loin': -10, 'abeille': -8, 'vent': -9, 'pas feuilles': -8, 'pas herbe': -8, 'bruissement': -9,
            'clapotis': -9, 'voix lointaine': -10, 'gouttes': -6, 'fee depart': -6, 'jingle etoile doux': -9}.get(k, -4)
    x = norm(x, peak)
    save_wav(x, OUT + k.replace(' ', '_') + '.wav')
    print(f'{k:24s} {len(x) / SR:4.1f}s')

# ---- ambiances en boucle ----
def amb(name, x, db=-22):
    x = loopify(fade(x, .5, .01), 3.0)
    save_mp3(rms_norm(x, db), AMB + name + '.mp3', '48k')
    print('amb', name, f'{len(x) / SR:.0f}s')

amb('foret', lp(load('0100', 0, 54), 9000), -24)
amb('riviere', load('1354', 0, 60), -24)
amb('soir', load('3203', 0, 60), -24)
amb('nuit', load('0110', 0, 60), -25)
amb('grotte', load('2135', 0, 60), -24)
amb('accueil', reverb(load('0195', 0, 17.3), .25), -24)

# berceuse originale (boîte à musique synthétique, 3/4)
mel = [('A4', 1), ('C5', 1), ('A4', 1), ('G4', 2), ('F4', 1), ('G4', 1), ('A4', 1), ('F4', 1), ('D4', 3),
       ('A4', 1), ('C5', 1), ('D5', 1), ('C5', 2), ('A4', 1), ('G4', 1), ('A4', 1), ('G4', 1), ('F4', 3)]
beat = .62
parts, t = [], 0
for n, b in mel:
    parts.append((musicbox(N(n) * 2, 2.5), t, .5)); t += b * beat
bars = int(t / (3 * beat))
for i in range(bars):
    parts.append((musicbox(N(['F3', 'C4', 'D4', 'C4', 'F3', 'A3', 'C4', 'F3'][i % 8]) * 2, 2.5), i * 3 * beat, .25))
loop_len = t
x = reverb(mix(*parts), .35, 2.0)
# repli de la queue sur le début pour une boucle parfaite
n = int(loop_len * SR); y = x[:n].copy(); tail = x[n:]; y[:len(tail)] += tail
save_mp3(rms_norm(y, -24), AMB + 'berceuse.mp3', '48k'); print('amb berceuse', f'{loop_len:.0f}s')

# ambiance féerique : nappe douce + clochettes
dur = 16.0; tt = np.arange(int(dur * SR)) / SR
pad = np.zeros_like(tt)
chords = [['C4', 'E4', 'G4', 'B4'], ['A3', 'C4', 'E4', 'A4'], ['F3', 'A3', 'C4', 'E4'], ['G3', 'B3', 'D4', 'G4']]
for ci, ch in enumerate(chords):
    env = np.clip(1 - np.abs((tt - (ci * 4 + 2)) / 2.6), 0, 1) ** 1.2
    env += np.clip(1 - np.abs((tt - (ci * 4 + 2 - dur)) / 2.6), 0, 1) ** 1.2  # bouclage
    env += np.clip(1 - np.abs((tt - (ci * 4 + 2 + dur)) / 2.6), 0, 1) ** 1.2
    for n in ch:
        f = N(n)
        pad += env * (np.sin(2 * np.pi * f * tt + .3 * np.sin(2 * np.pi * 4.5 * tt)) + .2 * np.sin(4 * np.pi * f * tt))
pad = lp(pad, 2500)
bells = mix(*[(glock(N(n) , 1.5), t0, .25) for t0, n in
              [(1, 'E6'), (3.5, 'G6'), (5, 'C7'), (7.5, 'A6'), (9, 'E6'), (11.5, 'D7'), (13, 'G6'), (14.5, 'C7')]])
y = pad / np.abs(pad).max() * .5
y[:len(bells[:len(y)])] += reverb(bells, .4)[:len(y)]
save_mp3(rms_norm(y, -24), AMB + 'feerique.mp3', '48k'); print('amb feerique')

# musique d'attente pendant les choix (kalimba douce, 4 temps)
pat = ['C5', 'E5', 'G5', 'A5', 'G5', 'E5', 'D5', 'E5']
step = .5
parts = [(musicbox(N(n), 2.0), i * step, .45) for i, n in enumerate(pat)]
x = reverb(mix(*parts), .3)
n = int(len(pat) * step * SR); y = x[:n].copy(); tail = x[n:]; y[:len(tail)] += tail
save_mp3(rms_norm(y, -26), AMB + 'attente.mp3', '48k'); print('amb attente')
