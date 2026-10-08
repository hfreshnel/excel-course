# CLAUDE.md — Masterclass vidéo Excel

> Ce fichier est la source de vérité du projet. **Le mettre à jour dès qu'une décision change** (outil abandonné, schéma modifié, convention ajustée). Un CLAUDE.md obsolète est pire que pas de CLAUDE.md.

## 1. Contexte et objectif

Commande client : produire des **masterclass vidéo de cours Excel**. Un professeur incarné par un **avatar IA** (« Professeur Ex ») détaille, étape par étape, la résolution d'exercices fournis par le client.

- Exigence client : qualité « digne de masterclass.com ». Le client a dit « dessin animé acceptable ».
- Équipe : 2 ingénieurs (Wilfried + un collègue). Le collègue a généré les scripts HeyGen de l'exercice 1.
- Wilfried est ingénieur junior ambitieux, profil fullstack indépendant. Tu agis comme un ingénieur senior qui l'assiste (voir section 9).

## 2. Décisions figées

Ne pas les remettre en cause sans validation explicite de Wilfried.

**Pédagogie**
- Excel **Microsoft 365, en français**. Public **débutant**.
- Formules enseignées en **propagation dynamique M365** (formules matricielles dynamiques). **Jamais** de matrices héritées `{=…}`.
- Les **erreurs de l'énoncé client sont corrigées et expliquées en vidéo**.
- Plusieurs vidéos par exercice. **Exercice 1 : 9 vidéos** + une vidéo 0.
- Structure de chaque exercice : **vidéo 0** (présentation de la consigne et feuille de route de la résolution), puis un **rappel d'une phrase en tête de chaque vidéo suivante** (« étape X sur N »).
- **Exercice 2 : pas encore reçu.** Ne rien supposer à son sujet.

**Format des scripts vidéo**
- Uniquement le **texte parlé** + les **indications de ce qui s'affiche à l'écran**.
- **Ne jamais mentionner l'avatar** dans les scripts.
- **Pas de pointage à la souris** : le montage illumine dynamiquement les colonnes, lignes, cellules ou plages citées à l'oral.

**Avatar**
- Homme, noir, nommé « Professeur Ex ». Préciser « homme » dans les prompts d'image : les générateurs produisent souvent une femme par défaut.
- Piste initiale : tête de chibi 2D. Wilfried teste maintenant plusieurs niveaux de réalisme (du chibi au photoréalisme) pour retenir **le plus simple à qualité maximale**. Le chibi n'est pas acquis.
- Générateurs d'images testés : GPT, Gemini, Midjourney, Hedra. **Pas de plan HeyGen actuellement** (à tester d'abord comme outil d'animation).
- Piste explorée : **transfert de performance** (Wilfried performeur, personnage généré par IA, voix remplacée si pas assez impactante) plutôt qu'avatar piloté par l'audio. Outils gratuits/open source en self-build acceptés.

## 3. Architecture cible du pipeline

```
script (texte + indications écran)
   → audio / vidéo avatar (HeyGen ou alternative)
   → timestamps mot-à-mot (Whisper)
   → timeline (fichier de pilotage)
   → automatisation Excel + capture d'écran (Windows)
   → compositing (Remotion) : surbrillances, avatar, titres d'étape
   → export final
```

**Principes de conception (le schéma exact est à concevoir avec Wilfried, ne pas l'imposer)**
- **Une timeline par vidéo**, pilotant à la fois le script Excel et le compositing.
- Chaque entrée est une **action horodatée** avec un type, une cible et une charge utile (saisie de formule, défilement, sélection, surbrillance…).
- Le script Excel **exporte un log** des instants réels d'exécution et des **rectangles en pixels** des plages. Il ne dessine pas les surbrillances dans Excel.
- **Les surbrillances sont rendues en post (Remotion)**, calées sur les timestamps de la parole, pour absorber la gigue d'Excel et permettre de corriger le timing sans réenregistrer.
- Enregistrer **par étape**, pas en un bloc continu, pour faciliter le recalage sur l'audio.
- Valider le schéma avec Wilfried avant toute implémentation lourde.

**Décisions du 2026-10-06** (validées par Wilfried)
- Formules saisies de façon **instantanée** (`Range.Formula2Local` d'un coup), pas de frappe simulée.
- Ancrage des actions par **marqueurs dans le texte prononcé** : `{@nom}` déclenche l'action au début du mot qui suit. Chaque ligne du tableau porte aussi un marqueur implicite `r1`, `r2`… Les marqueurs ne sont jamais prononcés (`tools/video_script.py` les retire).
- Les scripts de l'exercice 1 sont **figés** (texte prononcé). Seuls des marqueurs y sont ajoutés.
- **Zoom Excel des prises : 90 %** (colonnes A à P visibles en 1920×1020).
- **Saisies en incrustation** (rendu en post, Excel reste en saisie instantanée) :
  - périmètre : **formules** et **noms de plages** (zone Nom). Pas les valeurs ponctuelles ni la saisie de données en masse ;
  - apparition **jeton par jeton**, chaque jeton (`=`, `Prix_HT`, `*`, `Solde`) au moment où la voix le dicte, calé sur les timestamps des mots, **sans marqueur supplémentaire** dans les scripts ;
  - **grille floutée légèrement, sauf la cellule cible** qui reste nette et surlignée ;
  - **carte centrée** à l'écran.
- Thème Office : **pas de changement pour l'instant** (ruban sombre, cellules claires via la surcharge temporaire du registre).

**Schéma provisoire (prototype vidéo 3, à faire évoluer avec Wilfried)**
- `video-XX/timeline.json` : `startState`, `endState`, `sheet`, `view` (zoom, défilement, cellule active) et `events`. Chaque événement : `at` (marqueur), `offset` facultatif (s), `type` (`select`, `formula`, `value`, `highlight`), `target` (adresse, unions avec `,` acceptées). `formula` porte la formule en syntaxe française ; `value` porte la valeur. Un `highlight` se termine à `to` (marqueur) ou après `duration`.
- `recordings/voice/markers.json` : `{source, audio, duration, markers: {nom: secondes}, words: [{text, start, end}]}`. Produit aujourd'hui par la voix provisoire (`System.Speech`, voix Hortense, **16 kHz obligatoire** : `AudioPosition` est calculé à la fréquence native de la voix, toute autre fréquence de sortie fausse les positions des mots). Les événements SAPI ne parviennent pas à pywin32, d'où le passage par `tools/sapi_synthesize.ps1`. L'alignement Whisper produira le même format.
- `recordings/take-*/log.json` : instant prévu et réel de chaque événement (`plannedTime`, `actualTime`, `jitter`), `plannedEnd` des surbrillances et `rects` en pixels relatifs à la zone capturée, avec une auto-vérification `check` par `RangeFromPoint`. Base de temps : secondes depuis le début de l'audio ; temps vidéo = temps audio + `leadIn`.
- `render_preview.py` produit un **aperçu de contrôle** ffmpeg (capture + voix + rectangles, contours cyan des actions), pas le rendu final.
- `tools/render_lesson.py` construit `take-*/composition.json` (surbrillances et cartes de saisie, temps en secondes vidéo, rectangles en pixels de capture) puis lance le rendu Remotion (`compositing/`, composition `ExcelLesson`, `--public-dir` = dossier de prise). Les mots du script sont alignés sur les mots horodatés par `difflib.SequenceMatcher` (tolérant aux écarts de transcription) ; les mots non appariés sont interpolés. Dictée d'une formule : texte après le dernier « saisissez » qui précède le marqueur de l'événement, jusqu'à la fin de phrase ou « , puis », découpé aux virgules ; le nombre de morceaux doit égaler le nombre de jetons de la formule, sinon erreur explicite. Champ facultatif `dictationFrom` (marqueur) pour les dictées sans « saisissez ».

## 4. Environnement

- **Repo sous Windows** (`D:\dev\git\excel-course`). Wilfried utilise aussi WSL pour ce projet : ne pas accéder aux fichiers du repo depuis WSL via `/mnt/d` pour des traitements lourds (lent). Décider et documenter où tourne chaque outil.
- Outils constatés côté Windows (2026-10-05) : Python 3.14.3 (gestionnaire d'installation Python, lanceur `py` ; `python` dans Git Bash résout d'abord l'alias Microsoft Store), Node 24.11.1, Git 2.52, Git LFS 3.7.1. `uv` non installé.
- Ajoutés le 2026-10-06 : **ffmpeg 9.0.2** (`winget install Gyan.FFmpeg` ; le PATH n'est à jour que dans les nouveaux shells, `automation/ffmpeg_tools.py` le trouve aussi via le dossier winget ou `FFMPEG_PATH`) ; venv Python **`.venv` à la racine** (`requirements.txt` : `pywin32` 312).
- **Automatisation Excel : côté Windows uniquement** (COM). Excel de bureau M365 requis, pas Excel Online. Bibliothèque retenue : **`pywin32`** (liaison dynamique).
- Excel constaté : M365 build 20430, interface en français (1036), séparateur de liste `;`, décimal `,`, milliers U+202F. Écran 1920×1080 physiques à **125 %** (DPI 120) ; zone de travail capturée 1920×1020 (barre des tâches exclue).
- Thème Office de Wilfried : « Utiliser le paramètre système » (Windows en sombre). Pour les prises, `ExcelSession` force temporairement `UI Theme = 0` dans le registre puis restaure la valeur : les **cellules passent en clair** mais le **ruban reste sombre** (le thème M365 synchronisé par le compte l'emporte). Thème des enregistrements à trancher par Wilfried (Fichier > Compte > Thème Office).
- Matériel : portable **RTX 3060 Laptop, 6 Go de VRAM**. Whisper (`faster-whisper`) en modèle `small` ou `medium` est réaliste. Garder en tête cette limite pour tout modèle local (génération vidéo, transfert de performance).
- Capture d'écran : prototype avec **ffmpeg `gdigrab`** (`-draw_mouse 0` pour ne pas capturer le curseur), migration possible vers **OBS + obs-websocket** si la capture est instable. Wilfried n'a pas encore tranché définitivement. gdigrab capture bien en pixels physiques ; l'instant de début de capture est ancré sur le premier `out_time_us` de `-progress`. gdigrab horodate sur l'horloge réelle : les images perdues laissent des **trous (fréquence variable)**, sans dérive mais refusés par le compositeur Remotion (« No frame found at position »). La prise enregistre donc `capture.raw.mp4` puis le normalise en `capture.mp4` à 30 im/s constants, une image clé par seconde (`normalizeCapture`).
- Compositing : **Remotion** (React/TypeScript). **Licence vérifiée le 2026-10-06** ([LICENSE.md](https://github.com/remotion-dev/remotion/blob/main/LICENSE.md)) : gratuite pour un particulier, même en usage commercial. Wilfried porte le projet seul, sans rémunération ni vocation commerciale (le « client » est un porteur de projet qui ne le paie pas). À revérifier si ce statut change ou au passage à Remotion 5.0 (conditions annoncées comme modifiées).
- Outils gratuits/open source privilégiés. Dépendances externes acceptées si elles font bien le travail.

## 5. Arborescence du repo (proposition de départ, à ajuster)

```
/
├── CLAUDE.md
├── assets/
│   ├── client/        # originaux du client, jamais modifiés ni renommés (03-wall.jpg)
│   └── charts-background.jpg   # copie de travail de 03-wall.jpg
├── exercises/
│   ├── exercise-1/
│   │   ├── data/      # 01-data.xlsx
│   │   ├── solution/  # 02-solution.xlsx, 02-sol.xlsx
│   │   ├── states/    # classeurs de fin d'étape générés (non versionnés)
│   │   └── video-00 … video-09/   # script.md (+ timeline.json pour video-03) ; recordings/, renders/ non versionnés
│   └── exercise-2/    # vide tant que non reçu
├── requirements.txt   # dépendances Python (venv .venv à la racine)
├── automation/        # Python : pilotage Excel, capture, journal, aperçu de contrôle
├── compositing/       # Remotion 4.0.533 + @remotion/media (TypeScript, React 19) : ExcelLesson, HighlightBox, FocusBlur, TypingCard
└── tools/             # scripts utilitaires (timestamps, recalage…)
```

### Fichiers fournis par le client / le projet

| Fichier (emplacement actuel) | Rôle |
|---|---|
| `exercises/exercise-1/data/01-data.xlsx` | Énoncé de l'exercice 1 (feuille unique `QQ` : consigne et images des tableaux/diagrammes attendus) |
| `exercises/exercise-1/solution/02-solution.xlsx` | Solution. Tableau sur la feuille `DD` (et non `D1` comme le demande la consigne), graphiques sur les feuilles graphiques `D1`–`D4`. **Ses valeurs correspondent exactement à celles du tableau de l'énoncé** (Prix Haut 96 €, somme CA TTC 34 965,87 €). Contient `03-wall.jpg` en image intégrée (même hash SHA-256) |
| `exercises/exercise-1/solution/02-sol.xlsx` | Solution plus ancienne ou erronée : mois en anglais, Prix Haut 96,26 €, colonne `TTC` = montant de TVA, CA = Quantité × montant de TVA (somme 1 822,86 € au lieu de 34 965,87 €), graphique combiné en courbe non empilée. Le README des scripts parle de « solution B corrigée » : **probablement `02-solution.xlsx`, à confirmer avec Wilfried** |
| `assets/client/03-wall.jpg` | Original du client, conservé intact. **Fond des graphiques** (pas un décor de studio) |
| `assets/charts-background.jpg` | Copie de travail renommée de `03-wall.jpg` (contenu identique). C'est elle que le code référence |
| `exercises/exercise-1/README.md` | **Référence des scripts** : structure en 9 étapes, convention des colonnes, choix de résolution (feuilles, noms, formules), erreurs de l'énoncé corrigées, valeurs de contrôle. À tenir à jour avec les scripts |
| `exercises/exercise-1/video-00 … 09/script.md` | Scripts de production. Version du collègue (2026-10-06) **réécrite le 2026-10-06** selon les recommandations validées par Wilfried. Tableau `TC \| À l'écran \| Texte prononcé \| Action Excel`. Seule la colonne « Texte prononcé » va à la génération audio. Les TC sont estimés par `tools/estimate_timecodes.py`, le timing réel viendra de Whisper |

Les solutions du client peuvent contenir des erreurs (voir section 2). Les lire avec esprit critique.

### Gestion des fichiers binaires

- **Git LFS** suit `*.xlsx`, `*.xlsm`, `*.jpg`, `*.jpeg`, `*.png`, `*.mp4`, `*.mov`, `*.webm`, `*.wav`, `*.mp3` (voir `.gitattributes`). Tout nouveau type binaire doit y être ajouté **avant** son premier commit.
- Les enregistrements, rendus et états régénérables (`recordings/`, `renders/`, `states/`) ne sont pas versionnés (voir `.gitignore`).

## 6. Règles techniques Excel (COM)

- Utiliser **`Range.Formula2`**, jamais `Formula`. Avec `Formula`, Excel insère des `@` d'intersection implicite et casse la propagation dynamique. Doc : https://learn.microsoft.com/en-us/office/vba/api/excel.range.formula2
- Excel en **mode édition** rejette les appels COM (`RPC_E_CALL_REJECTED`). Écrire les formules d'un coup via COM, ou, si la frappe visible est voulue, la simuler avec reprise de focus avant chaque action.
- **Fenêtre, zoom, police, résolution et thème figés** pour tous les enregistrements. Sinon les coordonnées en pixels dérivent. Conversion des plages via `Range.Left/Top/Width/Height` et `ActiveWindow.PointsToScreenPixelsX/Y`.
- **Repartir d'un classeur propre** (copie du fichier d'exercice) à chaque prise.
- `ScreenUpdating` désactivé pendant les opérations lourdes, réactivé avant la capture. Prévoir un court délai avant les surbrillances pour un affichage stable.
- Nettoyage garanti (fermeture d'Excel, arrêt de l'enregistrement) même en cas d'exception.
- **Locale et pywin32** : pywin32 appelle Excel avec la locale utilisateur (fr-FR). Conséquences constatées : `Range("A1,B2")` échoue (Excel attend `;`), d'où `resolveRange` (union via `Application.Union`) ; `NumberFormat` est interprété à la française, d'où **`NumberFormatLocal`** avec les séparateurs lus dans Excel (`ExcelSession.localFormats`) ; les formules sont écrites avec **`Formula2Local`** (syntaxe française des scripts).
- **Pixels** : `ActiveWindow.ActivePane.PointsToScreenPixelsX/Y` (et non la version `Window`), processus DPI-aware par moniteur. Validé au pixel près au zoom 130 % (contrôle `RangeFromPoint` = ok).
- **`01-data.xlsx` contient une liaison externe** vers `C:\Users\baoucmoh\Documents\DO.xlsx` (poste du client). Ouverture avec `UpdateLinks=0`, liaison rompue dans les états générés. En Excel visible, la boîte « liaisons externes » bloque `Workbooks.Open` sans erreur.
- Toujours ouvrir une copie placée dans le repo (`recordings/`), pas dans `%TEMP%`.
- Bulle « Formule propagée » (`DynamicArrayFirstSpillCallout`) : affichage unique par profil, qui masquait la grille dans la première prise. `ExcelSession` la marque comme vue (registre `TeachingCallouts`, valeur 2) avant chaque prise visible.
- Au zoom 90 %, le texte de la grille fait environ 13 px de haut en 1080p : lisible en plein écran, petit sur mobile. Piste : recadrage dynamique (zoom sur la zone utile) au compositing.
- Les états de départ sont générés par `automation/exercise_1_states.py` (étapes 1 et 2 rejouées par code, plus un ajustement automatique des largeurs de colonnes que le script de la vidéo 1 ne mentionne pas).

## 7. Conventions de code

- **Tout le code est en anglais** : variables, fonctions, classes, commentaires, messages de commit.
- Nommage : variables et fonctions en `camelCase` (tous langages) ; classes en `PascalCase` ; constantes en `UPPER_SNAKE_CASE`.
- Fichiers : TypeScript/React en `kebab-case` ; Python en `snake_case` ; composants React en `PascalCase` (fichier et nom).
- Indentation : **tabulations** partout (largeur d'affichage 4), imposée par `.editorconfig`. Seule exception : YAML en 2 espaces (la spécification YAML interdit les tabulations). Configurer les formateurs (Prettier `useTabs: true`, Ruff `indent-style = "tab"`) en conséquence.
- Commentaires : uniquement sur les parties complexes. **Pas de docstrings ni de JSDoc.**
- Gestion d'erreurs **défensive** : `try/catch` systématique, journalisation de chaque échec.
- Priorité à la **performance** sur la lisibilité pure. Paradigme pragmatique selon le contexte.
- **Tests uniquement sur demande.**
- Le code produit doit être **complet, fonctionnel et prêt à l'exécution**.

## 8. Documents et livrables

- Tout document produit est en **Markdown**, sauf demande contraire. Si un autre format s'impose (docx, pdf…), le signaler et attendre validation.
- Avant tout document, rapport ou livrable structuré : **proposer un plan et attendre validation**, puis seulement générer.
- Contexte et décisions en **français**, code en **anglais**.

## 9. Règles de travail avec Wilfried

- Adopter la posture d'un **ingénieur senior qui assiste un ingénieur junior** : expliquer les mécanismes, pas seulement les résultats, sans simplifier à l'excès.
- **Analyser avant de répondre.** Quand plusieurs solutions existent : présenter les options, comparer, recommander, justifier.
- Pour les réponses impliquant un choix, une architecture ou un risque, utiliser la structure : Résumé, Analyse, Solution, Optimisations, Risques.
- **Ne jamais faire d'hypothèse sans validation.** Poser les questions en cas d'information manquante.
- Signaler explicitement le niveau d'incertitude et ce qui manque pour atteindre 100 % de certitude. Si la certitude est inférieure à 90 %, demander clarification avant de répondre.
- Fonder les affirmations techniques sur la **documentation officielle** et fournir le lien. Si aucune source fiable n'existe, le dire.
- **Contredire Wilfried si nécessaire**, de façon directe et factuelle. Quand il se trompe : corriger, expliquer pourquoi, fournir la version correcte.
- **Plan validé avant tout gros développement.** Une fois le plan validé, produire des blocs de code complets sans explications ligne par ligne.
- Anticiper les besoins, proposer optimisations et alternatives.

## 10. Points ouverts et risques

- **Format d'export de l'avatar** (fond uni, vert, canal alpha ?) : conditionne l'incrustation. À vérifier en premier.
- **Style final de l'avatar** et outil d'animation non tranchés (voir section 2).
- **Relation entre `02-solution.xlsx` et `02-sol.xlsx`** non clarifiée.
- **Scripts de l'exercice 1** : réécrits (environ 32 min de texte parlé au total), à relire par Wilfried et le collègue. Restent à vérifier dans un vrai Excel : affichage de 100,23 € pour le Prix TTC de janvier, comportement des années (colonne numérique) lors de la création des graphiques en barres et combiné. À confirmer côté client : les élèves reçoivent-ils l'image de fond `03-wall.jpg` ?
- **Barre de juillet en orange** dans l'histogramme de l'énoncé : raison inconnue, non reprise dans les scripts.
- **Titres de graphiques en anglais** dans l'énoncé (« Sales », « Evolution », « Years », « Prices ») : conservés, sauf « Périodes » → « Années » (vidéo 8).
- **Exercice 2** pas encore reçu.
- **Dérive de synchronisation** sur les longues manipulations : d'où l'enregistrement par étape.
- **Qualité « masterclass »** : prévoir une passe de contrôle visuel sur chaque vidéo, un pipeline automatisé produit un rendu propre mais standardisé.
- **Liaison externe dans `01-data.xlsx`** : les élèves verront l'avertissement « liaisons externes » à l'ouverture. À signaler au client (fichier à nettoyer).
- **Thème Excel des enregistrements** : reporté par Wilfried (ruban sombre actuellement).
- **Surbrillances hors grille** (barre de formule, zone Nom, ruban) : non calculables via `Range`. Les saisies passant en incrustation, le besoin restant concerne surtout le ruban et les boîtes de dialogue (coordonnées fixes mesurées ou UI Automation).
- Temps de rendu Remotion à surveiller sur 9 vidéos et plus. Mesuré le 2026-10-06 : environ 8 min pour la vidéo 3 (3 min 54 s, 7 030 images, concurrence 6). Portable **sur secteur** obligatoire (une coupure de batterie a interrompu un rendu).
- **`OffthreadVideo` abandonné** : sur la capture plein écran de 4 min, son cache d'images débordait (« No frame found at position », cause mémoire documentée). Remplacé par `<Video>` / `<Audio>` de `@remotion/media`, recommandés par la doc : https://www.remotion.dev/docs/troubleshooting/no-frame-found-at-position
- Flou de la grille pendant les saisies : 3 px + voile léger (`FocusBlur.tsx`). À ajuster à l'œil par Wilfried.

## 11. Commandes utiles

À compléter par Claude Code au fil du projet (installation des dépendances, lancement par étape, rendu d'une vidéo, génération des timestamps). Ne pas inventer de commandes avant qu'elles existent.

- Après un clone : `git lfs install` puis `git lfs pull` pour récupérer les binaires.
- Vérifier qu'un fichier est bien suivi par LFS : `git lfs ls-files`.
- Environnement Python (une fois) : `py -m venv .venv` puis `.venv\Scripts\python.exe -m pip install -r requirements.txt`.
- Générer les états de départ de l'exercice 1 : `.venv\Scripts\python.exe automation\exercise_1_states.py`.
- Voix provisoire + marqueurs d'une vidéo : `.venv\Scripts\python.exe tools\synthesize_placeholder_voice.py exercises\exercise-1\video-03\script.md`.
- Prise Excel + capture (ne pas toucher souris ni clavier) : `.venv\Scripts\python.exe automation\run_timeline.py exercises\exercise-1\video-03\timeline.json` (affiche le dossier de prise).
- Aperçu de contrôle : `.venv\Scripts\python.exe automation\render_preview.py exercises\exercise-1\video-03\recordings\take-<horodatage>`.
- Compositing (une fois) : `cd compositing` puis `npm install`. Vérification des types : `npm run typecheck`. Studio interactif : `npm run studio`.
- Vidéo finale d'une prise : `.venv\Scripts\python.exe tools\render_lesson.py exercises\exercise-1\video-03\recordings\take-<horodatage>` (`--data-only` pour ne produire que `composition.json`, `--concurrency N`). Sortie : `video-03\renders\lesson-take-<horodatage>.mp4`.
- Recalculer les TC et la durée estimée des scripts (après toute modification du texte prononcé) : `py tools/estimate_timecodes.py exercises/exercise-1/video-*/script.md`. Dans Git Bash, préfixer par `PYTHONIOENCODING=utf-8` si la console affiche mal les accents.