# Masterclass vidéo Excel

Production automatisée de cours vidéo Excel (Microsoft 365, en français, public débutant). Un professeur incarné par un avatar chibi 2D, « Professeur Ex », résout pas à pas des exercices fournis par un client.

> La source de vérité du projet est [CLAUDE.md](CLAUDE.md) (décisions, conventions, constats techniques). Ce fichier n'est qu'une porte d'entrée.

## Principe

Pour chaque vidéo, un script (texte parlé + marqueurs) pilote toute la chaîne :

```
script.md → voix de synthèse (Chatterbox, clonée) → timestamps mot à mot (Whisper)
          → timeline.json → Excel piloté par COM + capture d'écran (ffmpeg)
          → compositing Remotion (surbrillances, cartes de saisie, avatar en poses clés, bandeaux)
          → vidéo finale
```

Les formules sont saisies instantanément dans Excel, les surbrillances et incrustations sont rendues en post, calées sur la voix.

## Contenu du dépôt

| Dossier | Rôle |
|---|---|
| `exercises/exercise-N/` | Données du client, solutions, `README.md` de l'exercice, `video-XX/` (script, timeline, voix) |
| `automation/` | Python : pilotage Excel (COM), capture, journal des prises, aperçu de contrôle |
| `tools/` | Python : synthèse vocale, alignement Whisper, rendu final, prompteur, estimation des TC |
| `compositing/` | Remotion (TypeScript, React) : composition `ExcelLesson` |
| `assets/` | Originaux du client, poses de l'avatar, fond des graphiques |

État : exercice 1 (10 vidéos) et exercice 2 (13 vidéos) rendus, en attente de validation vidéo par vidéo.

## Prérequis

- **Windows** (automatisation Excel par COM) avec **Excel de bureau Microsoft 365** en français
- Python 3.14 (lanceur `py`), Node 24, Git, **Git LFS**
- ffmpeg : `winget install Gyan.FFmpeg`
- GPU NVIDIA conseillé pour la voix (testé sur RTX 3060, 6 Go de VRAM)

## Installation

```powershell
git clone <url> excel-course
cd excel-course
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

Le script récupère les fichiers LFS, crée `.venv` et `.venv-tts` (environ 5 Go), installe `compositing/` et normalise les poses de l'avatar. Options : `-SkipTts`, `-SkipNode`, `-SkipAvatar`.

Les modèles (Chatterbox, Whisper medium, Demucs, environ 7 Go) se téléchargent au premier usage.

## À restaurer hors git

Non versionnés, à récupérer de la sauvegarde :

- `assets/voice/` : référence de clonage de la voix, **non régénérable**
- `video-XX/recordings/` et `renders/` : régénérables, mais la synthèse vocale d'un exercice prend plusieurs heures
- `exercises/*/states/` : `automation\exercise_1_states.py` et `automation\exercise_2_states.py` les régénèrent

Aucun fichier audio ou vidéo n'est jamais versionné.

## Produire une vidéo

Exemple pour la vidéo 3 de l'exercice 1, depuis la racine :

```powershell
# 1. Voix de synthèse
.venv-tts\Scripts\python.exe tools\synthesize_voice.py exercises\exercise-1\video-03\script.md

# 2. Prise Excel + capture (ne toucher ni souris ni clavier)
.venv\Scripts\python.exe automation\run_timeline.py exercises\exercise-1\video-03\timeline.json

# 3. Rendu final
.venv\Scripts\python.exe tools\render_lesson.py exercises\exercise-1\video-03\recordings\take-<horodatage>
```

Sortie : `video-03\renders\lesson-take-<horodatage>.mp4`. D'autres commandes (essai à blanc, prompteur, studio Remotion, aperçu des poses) sont listées dans la section 11 de [CLAUDE.md](CLAUDE.md).

## Conventions

- Code en **anglais**, contexte et documentation en **français**
- Indentation par **tabulations** (`.editorconfig`)
- Pas de docstrings, commentaires seulement sur les parties complexes
- Un portable **sur secteur** est nécessaire pour les rendus (plusieurs minutes par vidéo)
