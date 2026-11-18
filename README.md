# L'histoire à écouter — « Les trois étoiles de la fée Lumina »

Livre audio interactif pour enfants de 3 à 6 ans (~12 min). L'enfant est le héros ou l'héroïne : au son du carillon,
il dit sa réponse à voix haute et le parent touche le bouton correspondant sur le téléphone.
Choix, tirages au sort et récompenses donnent **38 880 parcours** différents.

## Écouter
L'application est dans `docs/` : un site statique (HTML/JS, sans serveur) installable sur l'écran d'accueil
du téléphone (PWA) et utilisable hors connexion une fois chargé.

- **GitHub Pages** : Settings → Pages → *Deploy from a branch* → `main` / `/docs`.
  ⚠️ Sur un dépôt **privé**, GitHub Pages demande un compte GitHub Pro (sinon : rendre le dépôt public,
  ou brancher le dépôt sur Netlify / Cloudflare Pages, gratuits même en privé, dossier de publication `docs`).
- **En local** : `cd docs && python3 -m http.server` puis ouvrir http://localhost:8000.

## Organisation
| Chemin | Rôle |
|---|---|
| `source/histoire.txt` | Texte de tous les clips, avec les balises de bruitages, pauses et ambiances |
| `docs/scenario.json` | L'arbre de l'histoire : choix, tirages au sort, variables (couleur du sac, animal…), étoiles, délai de réponse (`choiceTimeout`, 30 s : ensuite le hasard choisit) |
| `docs/index.html` | Le lecteur (Web Audio : voix + ambiance en boucle + musique d'attente pendant les choix) |
| `docs/audio/clips/` | Les 68 clips MP3 générés (voix + bruitages mixés) |
| `docs/audio/amb/` | Ambiances en boucle (forêt, rivière, soir, nuit, grotte, accueil, féerique, berceuse, attente) |
| `docs/clips.json` | Généré : durée de chaque clip et changements d'ambiance en cours de clip |
| `tools/build_sfx.py` | Prépare les bruitages et les ambiances (télécharge les sons sources, synthétise les sons magiques) |
| `tools/gen_clips.py` | Génère les clips : synthèse vocale + insertion des bruitages + normalisation |

## Modifier l'histoire
1. Corriger le texte dans `source/histoire.txt` (et si besoin les choix dans `docs/scenario.json`).
2. Régénérer : `pip install edge-tts numpy scipy` (+ ffmpeg), puis
   `python3 tools/build_sfx.py` (une fois) et `python3 tools/gen_clips.py` (ou `gen_clips.py P01 E1-A` pour quelques clips).
3. Changer `CACHE` dans `docs/sw.js` (`lumina-v2`…) pour que les téléphones rechargent les nouveaux sons.

Voix : narrateur **Henri**, Lumina **Éloïse** (voix neuronales Microsoft via `edge-tts`) ; les paroles entre « » des
animaux et du hibou utilisent la voix du narrateur plus aiguë / plus grave (réglages `VOICES` et `QUOTE_STYLE`).

## Crédits sonores
- Bruitages et ambiances naturelles : [BigSoundBank.com](https://bigsoundbank.com) — Joseph Sardin, sons libres de droits.
- Sons magiques (carillon, étoile, fée, scintillements), berceuse, musique d'attente : synthétisés pour ce projet.
- La boîte à musique de l'accueil joue *Le Temps des cerises* (1866, domaine public), enregistrement BigSoundBank.
