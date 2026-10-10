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
- Structure de chaque exercice : **vidéo 0** (présentation de la consigne et feuille de route de la résolution), puis un **rappel d'une phrase en tête de chaque vidéo suivante** (« étape X sur N »). Depuis le 2026-10-09, la tournure de ce rappel varie d'une vidéo à l'autre (l'information « étape X sur N » reste dans la première phrase).
- **Transitions (décision du 2026-10-09)** : chaque paragraphe découle du précédent (conséquence, question soulevée) plutôt que d'être annoncé (« Passons à », « Voyons »…). Pas de formules toutes faites ni de tournures répétées d'une vidéo à l'autre. Chaque fin de vidéo pose la question que la suivante résout, avec un **poids proportionné à l'importance de la vidéo suivante** (courte avant les vidéos 2, 8 ; développée avant 1, 3, 5, 6, 9). Pas de fil rouge narratif inventé : les liens viennent des données et des calculs.
- **Exercice 2 : données brutes reçues le 2026-10-10** (voir section 5). Découpage en vidéos, choix de résolution et scripts : rien n'est décidé, ne rien supposer.

**Production (décisions du 2026-10-10)**
- **Validation vidéo par vidéo** : chaque vidéo est rendue puis jugée par Wilfried avant de passer à la suivante. Ne pas enchaîner plusieurs vidéos sans son accord.
- **Manipulations hors cellules (option A)** : ruban, menus contextuels, boîtes de dialogue, zone Nom déroulée… ne sont **pas** pilotés dans l'interface. Excel exécute le résultat par COM (instantané, comme les formules) et le montage Remotion **affiche le chemin suivi** en incrustation (ex. « Insertion › Graphiques › Histogramme groupé »). Écartées : piloter la vraie interface (UI Automation, clics simulés : fragile, toute erreur oblige à refaire la prise) et le mélange des deux. Conséquence : vérifier, vidéo par vidéo, que le texte parlé reste juste sans l'interface visible.

**Format des scripts vidéo**
- Uniquement le **texte parlé** + les **indications de ce qui s'affiche à l'écran**.
- **Ne jamais mentionner l'avatar** dans les scripts.
- **Lecture humaine des formules et des noms (décision du 2026-10-09)** : rien n'est épelé. On dit « égal, prix hors taxes multiplié par le taux de solde », pas « égal, Prix tiret bas H T, astérisque, Solde ». La syntaxe exacte (`=Prix_HT*Solde`) est montrée par la carte de saisie en incrustation. Les phrases qui expliquent un symbole du clavier (astérisque, barre oblique, règle du tiret bas en vidéo 2) sont conservées.
- **Pas de pointage à la souris** : le montage illumine dynamiquement les colonnes, lignes, cellules ou plages citées à l'oral.
- **Pas d'énumération à l'oral (décision du 2026-10-10)** : ce que l'écran montre (liste de noms, colonnes une à une) n'est pas récité, ça sonne mécanique. L'oral explique le geste et l'enjeu ; l'affichage (surbrillances, encadré qui se remplit) porte la liste, calé sur des marqueurs répartis dans les phrases.

**Avatar**
- Homme, noir, nommé « Professeur Ex ». Préciser « homme » dans les prompts d'image : les générateurs produisent souvent une femme par défaut.
- **Style retenu (décision du 2026-10-08) : chibi 2D.** Le photoréalisme et les niveaux de réalisme intermédiaires sont abandonnés.
- **Pas d'animation fluide** : l'avatar s'anime par une bibliothèque de **poses clés et d'expressions du visage** (images fixes), choisies pour souligner le discours et enchaînées au compositing.
- **Bouche fixe pour commencer** : pas de synchronisation labiale (piste ultérieure : Rhubarb Lip Sync, mode phonétique, non testé en français).
- **Images générées avec GPT.** Générateurs déjà testés : GPT, Gemini, Midjourney, Hedra.
- Apparence (portrait de référence du 2026-10-08) : peau brun foncé, cheveux noirs courts très frisés, lunettes rondes à monture fine noire, barbe courte reliée à la moustache, cardigan bleu marine ouvert sur une chemise blanche à col. Images complètes (pas de calques), **cadrage à mi-corps** (tête à la taille, bras et mains visibles), fond transparent. Le corps n'est pas animé : Remotion change d'image au bon mot et ajoute un mouvement d'ensemble léger (respiration, balancement).
- **Placement : en bas à droite (décision du 2026-10-10, remplace le bas à gauche)** pendant les manipulations Excel : le contenu Excel est à gauche, et les onglets de feuilles (bas à gauche) restent visibles. La pose `point`, dessinée vers le haut et la droite, est **affichée en miroir** (`mirroredPoses` dans la composition, `AVATAR_RIGHT_SIDE_MIRRORED_POSES` dans `render_lesson.py`) pour désigner le contenu ; les autres poses ne sont pas retournées (`explain` désigne déjà la gauche, les autres sont de face). Déplacements ponctuels envisagés par Wilfried (non tranché).
- Poses : ids en anglais (`assets/avatar/prompts.md`). **Lot 1 généré le 2026-10-08** : `neutral`, `welcome`, `explain`, `point`, `warning`, `cheer`.
- **Normalisation (option A, validée le 2026-10-08)** : cadrage de GPT conservé tel quel ; seuls la transparence (opacité pleine, voile et lueur du fond supprimés) et le format (1024×1536, ancré en bas) sont unifiés. Le décalage de tête de `point` (corps tourné) est accepté.
- **Changement de pose : coupe franche + petit rebond** (spring, échelle 0,93 → 1). Le fondu enchaîné a été écarté : il dédoublait la tête quand le corps tourne. Mouvement continu : respiration (±1,2 % en hauteur, 3,6 s) et balancement (±0,6°, 5,3 s). Entrée par glissement depuis le bas au début de la vidéo. Hauteur à l'écran 420 px, 24 px du bord droit (`side`, `margin`).
**Voix** (décision du 2026-10-10, remplace l'enregistrement par Wilfried)
- **Voix de synthèse clonée avec Chatterbox Multilingual** (Resemble AI, licence MIT, local sur la RTX 3060, `language_id="fr"`). Wilfried n'enregistre plus : sa diction ne convenait pas, et la conversion de voix (ElevenLabs Voice Changer, testée) ne change que le timbre.
- **Voix de Professeur Ex** : celle d'un ami de Wilfried (accord donné pour un extrait ; **accord écrit pour le clonage et la publication à obtenir**). Référence : `assets/voice/reference.wav` = 13 s brutes (sans Demucs) de `assets/voice/reference-stream.weba` (stream sans musique), de 4:25,1 à 4:38,1, en mono, volume normalisé à −20 LUFS. Choisie à l'écoute contre une variante passée par Demucs (petits bruits et « humm » ajoutés), un premier extrait YouTube avec musique (isolé par Demucs) et la voix du collègue (`video_01.wav`, générée avec Chatterbox, tatouage Perth détecté, voix aiguë autour de 370 à 440 Hz, incompatible avec un personnage masculin). Candidats conservés dans `assets/voice/candidates/` (non versionné).
- Réglages testés et retenus pour l'instant : `exaggeration` 0,5, `cfg_weight` 0,5. Chatterbox copie aussi l'énergie et le débit de la référence : préférer un passage posé.
- **Débit homogène (décision du 2026-10-10)** : Chatterbox change de vitesse d'une phrase à l'autre (−60 % à +60 % autour de la médiane, mesuré sur les vidéos 2 et 3) ; une phrase normale paraît alors lente après une rapide. `synthesize_voice.py` mesure le débit d'articulation de chaque prise (syllabes du texte envoyé au modèle, comptées approximativement, par seconde de parole, écarts entre mots plafonnés à 0,25 s) et le ramène vers une **cible unique pour tout le cours : 5,5 syllabes/s** : rien sous ±6 %, au-delà étirement par **Rubber Band** (filtre `rubberband` de ffmpeg, hauteur et formants conservés) limité à ±15 %, et au-delà de ±20 % les autres graines sont essayées d'abord (la plus proche de la cible parmi celles qui passent le contrôle Whisper). Mots horodatés recalés sur l'étirement ; débit et tempo dans le rapport et dans `markers.json` (`sentences`). Une vidéo synthétisée avant ce réglage (vidéo 3) est à régénérer.
- **Défauts de Chatterbox constatés et parades** : (1) le modèle continue parfois après le dernier mot (jusqu'à 2,5 s de souffle ou de marmonnement, avertissement « forcing EOS, long_tail ») → couper chaque phrase à la retombée réelle de la voix après le dernier mot (recherche d'un silence sur 0,35 s au plus), puis fondu en cosinus de 150 ms qui commence une fois la voix retombée ; (2) ses silences contiennent une note de vocodeur (~430 Hz) qui tinte si on les recopie → pauses remplies d'un **bruit rose synthétique à −70 dBFS** en fondu enchaîné (le silence numérique sonne comme un trou) ; (3) mélodie de fin parfois montante sur une affirmation (« toutes les autres » : remontée de +8 demi-tons sur la dernière syllabe voisée) → mesurée avec **Praat** (`praat-parselmouth`, `to_pitch_ac`, 70 à 300 Hz ; librosa pyin trouvait trop peu de trames voisées) sur la dernière plage voisée jusqu'au dernier mot du script : **la dernière phrase de chaque vidéo** (sauf question) doit finir au plus à +1 demi-ton de la médiane de la phrase et remonter d'au plus 3 demi-tons, sinon 10 graines sont essayées (vidéo 3 : graine 1234 rejetée avec une remontée de 12 demi-tons) ; ailleurs, correction à l'oreille par la graine. La dernière phrase finit aussi sur un **fondu de volume de 1,2 s** (au lieu de 150 ms), prolongé de 0,25 s après la retombée de la voix ; (4) mots mal lus (« TVA » → « l'atva » ; lettres isolées « D » lu « deux » et « H » lu « a », constaté le 2026-10-10) → texte converti pour la synthèse (sigles épelés, nombres en toutes lettres, lettres isolées D et H écrites « dé » et « ache » par `LETTER_NAMES` dans `tts_text.py`, à compléter si d'autres lettres sont mal lues).
- **Outil `tools/synthesize_voice.py` (plan validé le 2026-10-10)** : phrases découpées par `video_script.readSentences` (ids `<ligne>.<phrase>`, phrases de moins de 4 mots fusionnées avec une voisine de la même ligne, « s'en » comptant pour un mot et la ponctuation précédée d'une espace pour zéro) ; texte envoyé au modèle converti par `tools/tts_text.py` (lexique `exercises/exercise-N/tts-lexicon.json` pour les sigles épelés et les cas particuliers, puis cellules épelées « E treize », nombres en toutes lettres avec `num2words`, **traits d'union partout** (orthographe de 1990 : « quarante et un » était lu « 40 et 1 »), milliers séparés par un espace recollés, mots restants en majuscules lus comme des mots : SOMME, MOYENNE) ; une phrase par appel, graines essayées dans l'ordre 1234, 1, 2, 3 jusqu'à **90 % de ressemblance** (clés normalisées, transcription prise d'un bloc car Whisper coupe « 41,80 € » en deux mots, « 41,80 € » équivalant à « 41 euros 80 », « CTRL » à « Contrôle ») entre la transcription Whisper (processeur, le GPU est pris par Chatterbox) et le script, meilleur essai gardé sinon ; chaque essai est mis en cache dans `recordings/voice-tts/` (clé : modèle, empreinte de la référence, réglages, texte envoyé, graine) ; fins de phrase et pauses traitées comme ci-dessus, la coupe se calant sur le dernier mot **appartenant au script** (le marmonnement transcrit, « bon ? », « Ah ! », reste dehors) ; pauses de 0,6 s entre phrases, 0,9 s entre lignes, 0,5 s au début ; volume final à −16 LUFS (gain fixe + limiteur), WAV 48 kHz 16 bits dans `recordings/voice/audio.wav` ; `markers.json` calculé directement à partir des mots horodatés de chaque phrase (pas de second passage Whisper), avec en plus `sentences` (id, graine, début, ressemblance) ; rapport `recordings/voice/voice.report.md`. **Corrections à l'oreille** dans `video-XX/voice.json` (versionné) : `{"seeds": {"<id>": <graine>}, "text": {"<id>": "<texte envoyé au modèle>"}}` ; une graine imposée est utilisée seule, sans contrôle de ressemblance. Toute modification (texte, graine, réglages, référence) régénère seulement les phrases concernées.
- Ancienne voie (enregistrement par Wilfried, décision du 2026-10-08, conservée pour mémoire et réutilisable) : chaîne enregistrement → montage automatique (`tools/edit_voice.py`) → nettoyage (`tools/clean_voice.py`, ou Adobe Enhance Speech puis `--no-denoise`) → [modificateur de voix] → alignement Whisper (`tools/align_voice.py`) → `recordings/voice/` (`audio.wav` + `markers.json`). L'alignement se fait sur l'audio **final**.
- **Rangement (décision du 2026-10-09)** : le rush est renommé `video-XX/recordings/narration/rush-<aaaammjj>-<hhmm>.<ext>` (date et heure de l'enregistrement) ; les fichiers dérivés restent à côté (`-edit.wav`, `-edit-clean.wav`, rapports, transcriptions `.whisper-<modèle>.json`). La voix finale remplace la voix provisoire dans `recordings/voice/` ; la voix SAPI est déplacée dans `recordings/voice-placeholder/` (automatiquement par `align_voice.py`).
- **Montage automatique (décision du 2026-10-09)** : Whisper transcrit le rush, chaque phrase du script y est cherchée (alignement semi-global sur des clés normalisées : sans accents, nombres en chiffres, `%` et `€` en toutes lettres). En partant de la fin, chaque phrase garde sa **dernière prise complète** (couvrant au moins 85 % de la phrase) qui précède la prise gardée pour la phrase suivante : un score bas vient le plus souvent d'un mot mal entendu par Whisper, alors qu'une prise abandonnée s'arrête avant la fin. Les faux départs internes (mots répétés juste avant leur reprise) et les « euh » sont coupés ; les coupes sont calées sur les silences ; les pauses sont ramenées à 0,6 s entre phrases et 0,9 s entre lignes du script ; 2,5 s de silence de début sont conservées pour le profil de bruit. Validation par Wilfried **à l'écoute** du `-edit.wav` et du rapport `-edit.report.md` ; correction éventuelle dans Audacity (repères `-edit.labels.txt`, réappliqués avec `--labels`).
- Consignes d'enregistrement : **2 s de silence au début** de chaque prise (le profil de bruit y est appris), pièce petite et garnie de tissus, téléphone à 15-20 cm, format sans perte si l'application le permet.
- **Transfert de performance abandonné** (2026-10-08) au profit de l'avatar en poses clés.

## 3. Architecture cible du pipeline

```
script (texte + indications écran)
   → voix enregistrée par Wilfried (nettoyée)
   → timestamps mot-à-mot (Whisper)
   → timeline (fichier de pilotage)
   → automatisation Excel + capture d'écran (Windows)
   → compositing (Remotion) : surbrillances, avatar en poses clés, titres d'étape
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
- **Poses de l'avatar dans le texte prononcé (décision du 2026-10-08)** : `{pose:id}` change de pose au début du mot qui suit ; la pose dure **jusqu'à la fin de la phrase** (`.`, `!`, `?`, `…`, ou fin de ligne), puis retour à `neutral`. Pour la prolonger, la répéter sur la phrase suivante. Ajustements automatiques : pose maintenue 0,3 s après le dernier mot (sans chevaucher le mot suivant), même pose répétée à moins de 1,5 s fusionnée, retour à `neutral` de moins de 1 s supprimé. Un id inconnu ou mal formé arrête le rendu avec une erreur explicite ; `stripMarkers` retire tout `{pose:…}`, même mal formé.
- Les scripts de l'exercice 1 étaient **figés** (texte prononcé, seuls des marqueurs ajoutés). **Exception validée le 2026-10-09** : réécriture des transitions. **Exception validée le 2026-10-10** : vidéo 2, ligne 5, énumération des douze noms remplacée par l'explication du geste (marqueurs `nA`… `nM` répartis dans les phrases). Toute autre modification du texte prononcé reste à valider par Wilfried. Contraintes de toute réécriture : ne pas modifier les phrases de dictée de formule (« saisissez : égal, … »), garder tous les marqueurs `{@…}` et `{pose:…}` devant les mêmes mots, garder le nombre et l'ordre des lignes (marqueurs implicites `r1`, `r2`… utilisés par les timelines), puis recalculer les TC et régénérer le prompteur.
- **Zoom Excel des prises : 90 %** (colonnes A à P visibles en 1920×1020).
- **Saisies en incrustation** (rendu en post, Excel reste en saisie instantanée) :
  - périmètre : **formules** et **noms de plages** (zone Nom). Pas les valeurs ponctuelles ni la saisie de données en masse ;
  - apparition **jeton par jeton**, chaque jeton (`=`, `Prix_HT`, `*`, `Solde`) au moment où la voix le dicte, calé sur les timestamps des mots, **sans marqueur supplémentaire** dans les scripts ;
  - **grille floutée légèrement, sauf la cellule cible** qui reste nette et surlignée ;
  - **carte centrée** à l'écran.
- Thème Office : **pas de changement pour l'instant** (ruban sombre, cellules claires via la surcharge temporaire du registre).

**Schéma provisoire (prototype vidéo 3, à faire évoluer avec Wilfried)**
- `video-XX/timeline.json` : `startState`, `endState`, `sheet`, `view` (zoom, défilement, cellule active) et `events`. Chaque événement : `at` (marqueur), `offset` facultatif (s), `type` (`select`, `formula`, `value`, `highlight`), `target` (adresse, unions avec `,` acceptées). `formula` porte la formule en syntaxe française ; `value` porte la valeur. Un `highlight` se termine à `to` (marqueur) ou après `duration`.
- **Ajouts du 2026-10-10 (vidéo 2)** :
  - `name` : `target` + `name`, crée le nom par `Range.Name` ; carte de saisie visant la zone Nom (dictée après « saisissez » ou depuis `dictationFrom`), sauf `"card": false` ;
  - un `highlight` peut viser un élément de l'interface (`"ui": "nameBox"`, `"formulaBar"`, ou un AutomationId comme `"TabFormulas"`) au lieu d'une plage. Rectangles lus par UI Automation **une fois, avant la capture** (`log.json` → `uiRects`) ;
  - éléments de montage, **ignorés par `run_timeline.py`** et calculés par `render_lesson.py` depuis les marqueurs de la voix (les modifier ne demande pas de nouvelle prise) : `banner` (`step`, `title`, `done`), `callout` (`title`, `position` `right` | `rightColumn` | `center`, `lines` : `text`, `detail`, `kind` `text` | `formula`, `at` facultatif pour une apparition ligne à ligne), `menuPath` (`steps` : `text`, `at` facultatif), le chemin suivi dans le ruban ou un menu (option A). Fin à `to`, après `duration`, sinon à la fin de la vidéo.
- `recordings/voice/markers.json` : `{source, audio, duration, markers: {nom: secondes}, words: [{text, start, end}]}`. Produit par `align_voice.py` pour une voix enregistrée (`source` = `whisper-<modèle>`, mots tels que transcrits, `audio.wav` en 48 kHz 16 bits ; un marqueur suivi d'un mot de la même ligne tombe au début de ce mot, un marqueur de fin de ligne à la fin du dernier mot). `run_timeline.py` prend `voice/` s'il existe, sinon `voice-placeholder/`. `render_lesson.py` lit les marqueurs de la voix utilisée par la prise (dossier de `log.audio`) et refuse une prise jouée sur une autre voix (source ou durée différente). Voix provisoire (`voice-placeholder/`) produite par SAPI (`System.Speech`, voix Hortense, **16 kHz obligatoire** : `AudioPosition` est calculé à la fréquence native de la voix, toute autre fréquence de sortie fausse les positions des mots). Les événements SAPI ne parviennent pas à pywin32, d'où le passage par `tools/sapi_synthesize.ps1`.
- `recordings/take-*/log.json` : instant prévu et réel de chaque événement (`plannedTime`, `actualTime`, `jitter`), `plannedEnd` des surbrillances et `rects` en pixels relatifs à la zone capturée, avec une auto-vérification `check` par `RangeFromPoint`. Base de temps : secondes depuis le début de l'audio ; temps vidéo = temps audio + `leadIn`.
- `render_preview.py` produit un **aperçu de contrôle** ffmpeg (capture + voix + rectangles, contours cyan des actions), pas le rendu final.
- `tools/render_lesson.py` construit `take-*/composition.json` (surbrillances et cartes de saisie, temps en secondes vidéo, rectangles en pixels de capture) puis lance le rendu Remotion (`compositing/`, composition `ExcelLesson`, `--public-dir` = dossier de prise). Les mots du script sont alignés sur les mots horodatés par `difflib.SequenceMatcher` (tolérant aux écarts de transcription) ; les mots non appariés sont interpolés. Dictée d'une formule : texte après le dernier « saisissez » (ou « tapez ») qui précède le marqueur de l'événement, jusqu'à la fin de phrase ou « , puis ». Depuis le 2026-10-09, les jetons y sont retrouvés par **alignement sur un lexique** (programmation dynamique, ordre conservé, mots intermédiaires ignorés, comparaison sans accents ni casse) : formes parlées des symboles dans le code (`=` « égal », `*` « multiplié par » ou « fois », `/` « divisé par », `(` « entre parenthèses », `)` « le tout »…), formes parlées des noms dans `exercises/exercise-N/dictation-lexicon.json` (sinon le nom lui-même, `_` lu comme un espace). Un symbole non prononcé apparaît avec le jeton dicté suivant ; un nom, un nombre ou un texte introuvable arrête le rendu avec une erreur explicite. Champ facultatif `dictationFrom` (marqueur) pour les dictées sans « saisissez ». L'avatar est ajouté si `assets/avatar/normalized/manifest.json` existe (poses copiées dans `take-*/avatar/`, bloc `avatar` : poses, hauteur, position, `defaultPose`, `cues` `{pose, start}` construits depuis les marqueurs `{pose:id}` et les fins de mots horodatées).

## 4. Environnement

- **Repo sous Windows** (`D:\dev\git\excel-course`). Wilfried utilise aussi WSL pour ce projet : ne pas accéder aux fichiers du repo depuis WSL via `/mnt/d` pour des traitements lourds (lent). Décider et documenter où tourne chaque outil.
- Outils constatés côté Windows (2026-10-05) : Python 3.14.3 (gestionnaire d'installation Python, lanceur `py` ; `python` dans Git Bash résout d'abord l'alias Microsoft Store), Node 24.11.1, Git 2.52, Git LFS 3.7.1. `uv` non installé.
- **`.venv-tts` (2026-10-10)** : venv séparé pour la synthèse vocale (Python 3.14, PyTorch 2.11.0+cu128 installé depuis `https://download.pytorch.org/whl/cu128`, `chatterbox-tts` 0.1.7 installé **sans dépendances** puis ses dépendances utiles, `demucs` 4.1.0). Écartés : `spacy-pkuseg` (chinois, à compiler) et `gradio` (démo). Chatterbox Multilingual : 3,9 Go de VRAM au maximum, environ 1,3 × le temps réel. Le PyTorch de PyPI sous Windows est sans CUDA : toujours passer par l'index PyTorch.
- Ajoutés le 2026-10-06 : **ffmpeg 9.0.2** (`winget install Gyan.FFmpeg` ; le PATH n'est à jour que dans les nouveaux shells, `automation/ffmpeg_tools.py` le trouve aussi via le dossier winget ou `FFMPEG_PATH`) ; venv Python **`.venv` à la racine** (`requirements.txt` : `pywin32` 312, `Pillow` 12.3 depuis le 2026-10-08, `comtypes` 1.4.17 depuis le 2026-10-10 pour UI Automation, que pywin32 ne sait pas piloter).
- **Automatisation Excel : côté Windows uniquement** (COM). Excel de bureau M365 requis, pas Excel Online. Bibliothèque retenue : **`pywin32`** (liaison dynamique).
- Excel constaté : M365 build 20430, interface en français (1036), séparateur de liste `;`, décimal `,`, milliers U+202F. Écran 1920×1080 physiques à **125 %** (DPI 120) ; zone de travail capturée 1920×1020 (barre des tâches exclue).
- Thème Office de Wilfried : « Utiliser le paramètre système » (Windows en sombre). Pour les prises, `ExcelSession` force temporairement `UI Theme = 0` dans le registre puis restaure la valeur : les **cellules passent en clair** mais le **ruban reste sombre** (le thème M365 synchronisé par le compte l'emporte). Thème des enregistrements à trancher par Wilfried (Fichier > Compte > Thème Office).
- Matériel : portable **RTX 3060 Laptop, 6 Go de VRAM**. Garder en tête cette limite pour tout modèle local (génération vidéo, transfert de performance).
- **Whisper (2026-10-09)** : `faster-whisper` 1.2.1 (CTranslate2 4.8.2), modèle `medium`, **sur le processeur en int8** : environ 0,6 × la durée de l'audio (245 s pour 7 min). Le GPU est détecté mais les DLL cuBLAS 12 et cuDNN 9 manquent ; `whisper_tools.py` bascule seul sur CUDA si elles deviennent chargeables (paquets pip `nvidia-cublas-cu12` et `nvidia-cudnn-cu12`, plus d'1 Go, non installés). L'audio est décodé par ffmpeg (le décodeur PyAV de faster-whisper 1.2.1 est cassé avec PyAV 19 : argument `metadata_errors` inconnu), ce qui donne aussi la même base de temps que le montage. **Pas d'invite initiale (`initial_prompt`)** : Whisper la traite comme du texte déjà prononcé et saute les phrases du script qui ouvrent l'audio (constaté : phrase 1 de la vidéo 3 absente de la transcription). Transcriptions mises en cache à côté de l'audio (`<nom>.whisper-<modèle>.json`, clé : taille, date, modèle).
- Capture d'écran : prototype avec **ffmpeg `gdigrab`** (`-draw_mouse 0` pour ne pas capturer le curseur), migration possible vers **OBS + obs-websocket** si la capture est instable. Wilfried n'a pas encore tranché définitivement. gdigrab capture bien en pixels physiques ; l'instant de début de capture est ancré sur le premier `out_time_us` de `-progress`. gdigrab horodate sur l'horloge réelle : les images perdues laissent des **trous (fréquence variable)**, sans dérive mais refusés par le compositeur Remotion (« No frame found at position »). La prise enregistre donc `capture.raw.mp4` puis le normalise en `capture.mp4` à 30 im/s constants, une image clé par seconde (`normalizeCapture`).
- Compositing : **Remotion** (React/TypeScript). **Licence vérifiée le 2026-10-06** ([LICENSE.md](https://github.com/remotion-dev/remotion/blob/main/LICENSE.md)) : gratuite pour un particulier, même en usage commercial. Wilfried porte le projet seul, sans rémunération ni vocation commerciale (le « client » est un porteur de projet qui ne le paie pas). À revérifier si ce statut change ou au passage à Remotion 5.0 (conditions annoncées comme modifiées).
- Outils gratuits/open source privilégiés. Dépendances externes acceptées si elles font bien le travail.

## 5. Arborescence du repo (proposition de départ, à ajuster)

```
/
├── CLAUDE.md
├── assets/
│   ├── client/        # originaux du client, jamais modifiés ni renommés (03-wall.jpg)
│   ├── avatar/        # Professeur Ex : prompts.md (prompts GPT, liste des poses), poses/<id>.png (originaux GPT, ids en anglais), normalized/ (généré, non versionné)
│   ├── voice/         # voix de Professeur Ex (non versionné) : reference.wav (référence de clonage), sources reçues (.weba), candidates/
│   └── charts-background.jpg   # copie de travail de 03-wall.jpg
├── exercises/
│   ├── exercise-1/
│   │   ├── data/      # 01-data.xlsx
│   │   ├── solution/  # 02-solution.xlsx, 02-sol.xlsx
│   │   ├── states/    # classeurs de fin d'étape générés (non versionnés)
│   │   └── video-00 … video-09/   # script.md (+ timeline.json pour video-03) ; recordings/ (narration/, voice/, voice-placeholder/, take-*/) et renders/ non versionnés
│   └── exercise-2/
│       ├── data/      # 01-data.xlsx, CSV 02 et 04 à 08 ; old/01-data.xlsx (version 2024)
│       ├── solution/  # 02-sol.xlsx ; old/02-sol.xlsx (version 2024)
│       └── colleague/ # pack du collègue (2026-10-10) : premier jet des scripts, rapport de contrôle, classeur de démo
├── requirements.txt   # dépendances Python (venv .venv à la racine)
├── automation/        # Python : pilotage Excel, capture, journal, aperçu de contrôle
├── compositing/       # Remotion 4.0.533 + @remotion/media (TypeScript, React 19) : ExcelLesson, HighlightBox, FocusBlur, TypingCard, ProfessorEx, StepBanner, CalloutBox, MenuPathStrip ; composition AvatarPreview
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
| `exercises/exercise-2/data/01-data.xlsx` | Énoncé de l'exercice 2 (2025-12-03). Feuille `QS` : **25 questions** (NB, NB.SI(.ENS), SOMME.SI(.ENS), MOYENNE.SI(.ENS), MAX/MIN.SI.ENS, RECHERCHEV, ESTVIDE, ABS, graphique dynamique, sous-totaux, TCD et graphique croisé dynamique, fichier CSV, tableaux avancés, références de cellules, SI imbriqués, ET/OU/NON, TRANSPOSE, RECHERCHEH/X, INDEX/EQUIV). Feuilles `Q1`, `S2`, `S3`, `S5`, `SOL`, `CC` (feuille graphique), un TCD, `03-wall.jpg` intégrée. **La feuille `SOL` contient déjà des formules de solution** (120). Fautes dans la consigne (« peronnes », « Valeure ») |
| `exercises/exercise-2/data/02-data.csv` | 210 établissements d'enseignement américains (2023) (`schoolid`, `schoolname`, `CalendarYear`…). Probablement la question 19 (« Gestion d'un fichier CSV »), à confirmer |
| `exercises/exercise-2/data/04-data.csv` à `08-data.csv` | Livrés dans un sous-dossier `00-data/`. 04 : classement mondial des universités (2 200 lignes, 2012 à 2015) ; 05 : statuts d'emploi ; 06 : codes et symboles de devises (UTF-8) ; 07 : niveaux d'études ; 08 : secteurs d'activité. Usage non précisé par le client (listes de validation ? tableaux avancés ?) |
| `exercises/exercise-2/solution/02-sol.xlsx` | Solution (2025-12-03). Feuilles `QS`, `S1`, `S2`, `S3`, `S5`, `SOL`, `CC` ; 35 noms définis, mêlant anglais et français (`Salaries` sur `SOL`, `Salaires` sur `S1`…) ; **`Dates` pointe sur `#REF!`** |
| `exercises/exercise-2/data/old/01-data.xlsx`, `solution/old/02-sol.xlsx` | Versions d'août 2024 livrées dans `00-data/old/`. L'ancien énoncé a d'autres feuilles (`Q1` à `Q5`, `ALL`) et 3 images PNG (absentes de la nouvelle version) ; l'ancienne solution a une feuille `S4` et `Jobs` sur `#REF!` |
| `exercises/exercise-2/colleague/` | Pack du collègue (2026-10-10), qui écrit les scripts de l'exercice 2 : scripts de 11 vidéos (0 à 10) en un seul fichier, rapport de contrôle, classeur `Exercice2_demo_Q1_pret_a_filmer.xlsx`. **Premier jet, pas des scripts de production.** Valeurs de contrôle des questions 1 à 9 justes (Q5 = 6 066, Q7 = 2 897 : la solution du client oublie la condition sur le salaire). Classeur de démo inutilisable (`#NOM?` en `L30:L31` : openpyxl sans préfixe `_xlfn.` ; colonnes calculées vides). Retour préparé pour lui le 2026-10-10 : Q10-11 = liste déroulante (validation `SOL!E22`, source `Clients`) + RECHERCHEV, pas UNIQUE ; Q13 = ABS sur une plage ; Q14-15 = liste déroulante des métiers (`SOL!A56`, `Jobs`) qui pilote le graphique ; bug client en `SOL!C56` (recherche par le salaire 2000, Doctor et Accountant à 9 733 tous les deux) ; conventions de script non respectées (formules préremplies, lecture épelée, pointage, transitions annoncées) |
| `exercises/exercise-1/video-00 … 09/script.md` | Scripts de production. Version du collègue (2026-10-06) **réécrite le 2026-10-06** selon les recommandations validées par Wilfried. Tableau `TC \| À l'écran \| Texte prononcé \| Action Excel`. Seule la colonne « Texte prononcé » va à la génération audio. Les TC sont estimés par `tools/estimate_timecodes.py`, le timing réel viendra de Whisper |

Les solutions du client peuvent contenir des erreurs (voir section 2). Les lire avec esprit critique.

### Gestion des fichiers binaires

- **Git LFS** suit `*.xlsx`, `*.xlsm`, `*.jpg`, `*.jpeg`, `*.png` (voir `.gitattributes`). Tout nouveau type binaire versionné doit y être ajouté **avant** son premier commit.
- **CSV gardés à l'identique** (`*.csv -text` dans `.gitattributes`, depuis le 2026-10-10) : les fichiers du client sont versionnés octet pour octet, sans normalisation des fins de ligne (ceux de l'exercice 2 sont en LF).
- Les fichiers reçus du client gardent leur nom ; seul leur emplacement change (`data/`, `solution/`, `old/` pour les versions antérieures). Livraison de l'exercice 2 : dossier `02-part-02/` (chemin d'origine du client : `24-02-00-excel\01-td\02-part-02\`), son `03-wall.jpg` identique à `assets/client/03-wall.jpg` (même SHA-256) n'a pas été dupliqué.
- Les enregistrements, rendus et états régénérables (`recordings/`, `renders/`, `states/`) ne sont pas versionnés (voir `.gitignore`).
- **Décision du 2026-10-09 : aucune vidéo ni aucun audio sur le git** (trop volumineux, régénérables). Les dossiers restent en place sur le disque. Constat à cette date : aucun média suivi, tous dans `video-XX/recordings/` et `video-XX/renders/`, déjà ignorés. Filet de sécurité : `.gitignore` exclut les extensions audio et vidéo **partout** dans le repo (`mp4`, `mov`, `webm`, `mkv`, `avi`, `wav`, `mp3`, `m4a`, `aac`, `flac`, `ogg`, `opus`), et ces types ne sont plus suivis par LFS.

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
- **Zone Nom (constaté le 2026-10-10)** : après `Range.Name`, elle affiche le nouveau nom d'elle-même. **Ne pas resélectionner** la plage juste après : pour une cellule seule (F20), la zone Nom devient vide. Une plage choisie par son nom (`sheet.Range("CA_TTC")`) s'y affiche aussi par son nom.
- **UI Automation** (`comtypes`, `ExcelSession.uiRects`) : zone Nom = `ComboBox` « Zone Nom » (11, 233, 125 × 29 px), onglets du ruban par AutomationId (`TabFormulas`…), barre de formule `FormulaBar`. Juste après une requête, Excel rejette brièvement les appels COM (`RPC_E_CALL_REJECTED`, environ 0,15 s) : reprises obligatoires.
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
- **Avatar chibi en poses clés** (voir section 2). Restent ouverts : liste des poses et expressions (proposition du 2026-10-08 à valider), déclenchement des poses depuis les scripts, cohérence du personnage d'une image générée à l'autre. Onglets de feuilles masqués en bas à gauche : **résolu le 2026-10-10** par le passage en bas à droite.
- **Relation entre `02-solution.xlsx` et `02-sol.xlsx`** non clarifiée.
- **Scripts de l'exercice 1** : réécrits (environ 35 min de texte parlé au total depuis l'ajout des transitions du 2026-10-09, contre 32 avant), à relire par Wilfried et le collègue. Restent à vérifier dans un vrai Excel : affichage de 100,23 € pour le Prix TTC de janvier, comportement des années (colonne numérique) lors de la création des graphiques en barres et combiné. À confirmer côté client : les élèves reçoivent-ils l'image de fond `03-wall.jpg` ?
- **Barre de juillet en orange** dans l'histogramme de l'énoncé : raison inconnue, non reprise dans les scripts.
- **Titres de graphiques en anglais** dans l'énoncé (« Sales », « Evolution », « Years », « Prices ») : conservés, sauf « Périodes » → « Années » (vidéo 8).
- **Exercice 2** (reçu le 2026-10-10) : 25 questions, soit bien plus de matière que l'exercice 1. Scripts écrits par le collègue (premier jet dans `colleague/`, réécriture demandée). À demander au client : colonne Salaries vide dans `Q1` de l'énoncé (remplie dans l'ancienne version et dans `SOL`), rôle des CSV 04 à 08. À trancher avec Wilfried : découpage en vidéos (11 proposées par le collègue), version des données de travail (l'énoncé contient déjà la feuille `SOL` remplie), noms définis à retenir (anglais ou français), Excel M365 attendu pour RECHERCHEX et la propagation dynamique.
- **Voix de synthèse** : `tools/synthesize_voice.py` écrit le 2026-10-10, premier essai sur la vidéo 3. Mélodie de fin montante contrôlée automatiquement sur la dernière phrase seulement : écoute complète nécessaire pour les autres. Accord écrit de l'ami pour le clonage et la publication à obtenir. Les fichiers de `assets/voice/` ne sont pas versionnés : **Wilfried les sauvegarde lui-même** (la source reçue ne se régénère pas).
- **Montage automatique** : Whisper fusionne volontiers une répétition immédiate (« en F2 saisissez… en F2 saisissez ») en une seule occurrence ; elle reste alors dans la prise gardée. Filets : `edit_voice.py` signale la parole non transcrite dans les prises gardées, `align_voice.py` signale les mots hors script sur l'audio final. L'écoute reste indispensable.
- **Dérive de synchronisation** sur les longues manipulations : d'où l'enregistrement par étape.
- **Qualité « masterclass »** : prévoir une passe de contrôle visuel sur chaque vidéo, un pipeline automatisé produit un rendu propre mais standardisé.
- **Liaison externe dans `01-data.xlsx`** : les élèves verront l'avertissement « liaisons externes » à l'ouverture. À signaler au client (fichier à nettoyer).
- **Thème Excel des enregistrements** : reporté par Wilfried (ruban sombre actuellement).
- **Surbrillances hors grille** : zone Nom, barre de formule et onglets du ruban résolus par UI Automation (2026-10-10). Restent les éléments qui n'existent qu'une fois un menu ouvert (boîtes de dialogue, menus contextuels) : sans objet en option A, le montage les décrit par `menuPath` et `callout`.
- **Vidéo 3 sans bandeaux ni encadrés** : à rendre de nouveau (sans nouvelle prise) une fois les éléments de montage ajoutés à sa timeline.
- Temps de rendu Remotion à surveiller sur 9 vidéos et plus. Mesuré le 2026-10-06 : environ 8 min pour la vidéo 3 (3 min 54 s, 7 030 images, concurrence 6). Portable **sur secteur** obligatoire (une coupure de batterie a interrompu un rendu).
- **`OffthreadVideo` abandonné** : sur la capture plein écran de 4 min, son cache d'images débordait (« No frame found at position », cause mémoire documentée). Remplacé par `<Video>` / `<Audio>` de `@remotion/media`, recommandés par la doc : https://www.remotion.dev/docs/troubleshooting/no-frame-found-at-position
- Flou de la grille pendant les saisies : 3 px + voile léger (`FocusBlur.tsx`). À ajuster à l'œil par Wilfried.

## 11. Commandes utiles

À compléter par Claude Code au fil du projet (installation des dépendances, lancement par étape, rendu d'une vidéo, génération des timestamps). Ne pas inventer de commandes avant qu'elles existent.

- Après un clone : `git lfs install` puis `git lfs pull` pour récupérer les binaires.
- Vérifier qu'un fichier est bien suivi par LFS : `git lfs ls-files`.
- Environnement Python (une fois) : `py -m venv .venv` puis `.venv\Scripts\python.exe -m pip install -r requirements.txt`.
- Générer les états de départ de l'exercice 1 : `.venv\Scripts\python.exe automation\exercise_1_states.py`.
- Voix provisoire + marqueurs d'une vidéo (écrits dans `recordings/voice-placeholder/`) : `.venv\Scripts\python.exe tools\synthesize_placeholder_voice.py exercises\exercise-1\video-03\script.md`.
- Prise Excel + capture (ne pas toucher souris ni clavier) : `.venv\Scripts\python.exe automation\run_timeline.py exercises\exercise-1\video-03\timeline.json` (affiche le dossier de prise).
- Aperçu de contrôle : `.venv\Scripts\python.exe automation\render_preview.py exercises\exercise-1\video-03\recordings\take-<horodatage>`.
- Compositing (une fois) : `cd compositing` puis `npm install`. Vérification des types : `npm run typecheck`. Studio interactif : `npm run studio`.
- Vidéo finale d'une prise : `.venv\Scripts\python.exe tools\render_lesson.py exercises\exercise-1\video-03\recordings\take-<horodatage>` (`--data-only` pour ne produire que `composition.json`, `--concurrency N`). Sortie : `video-03\renders\lesson-take-<horodatage>.mp4`.
- Environnement de synthèse vocale (une fois) : `py -3.14 -m venv .venv-tts`, puis `.venv-tts\Scripts\python.exe -m pip install torch==2.11.0 torchaudio==2.11.0 --index-url https://download.pytorch.org/whl/cu128`, puis `.venv-tts\Scripts\python.exe -m pip install --no-deps chatterbox-tts==0.1.7`, puis `.venv-tts\Scripts\python.exe -m pip install "numpy>=2" librosa==0.11.0 s3tokenizer transformers==5.2.0 diffusers==0.29.0 resemble-perth conformer==0.3.2 safetensors==0.5.3 pykakasi==2.3.0 pyloudnorm omegaconf demucs==4.1.0 num2words praat-parselmouth "faster-whisper>=1.2.1" torch==2.11.0 torchaudio==2.11.0 --extra-index-url https://download.pytorch.org/whl/cu128`. Les avertissements de pip sur `gradio` et `spacy-pkuseg` manquants sont attendus.
- **Voix de synthèse d'une vidéo** (remplace `recordings/voice/`, la voix SAPI passe dans `voice-placeholder/`) : `.venv-tts\Scripts\python.exe tools\synthesize_voice.py exercises\exercise-1\video-03\script.md` (`--force` pour ignorer le cache, `--reference` pour une autre voix). Rapport : `recordings\voice\voice.report.md`. Ensuite, nouvelle prise Excel (`run_timeline.py`) puis rendu.
- Isoler une voix d'une musique de fond : `.venv-tts\Scripts\python.exe -m demucs --two-stems=vocals -n htdemucs -o <dossier> <fichier.wav>` (à éviter si la source n'a pas de musique : artefacts audibles après clonage).
- Normaliser les poses de l'avatar (après tout ajout ou remplacement dans `assets/avatar/poses/`) : `.venv\Scripts\python.exe tools\normalize_avatar.py`. Sortie : `assets/avatar/normalized/` (`<id>.png` + `manifest.json`). À relancer avant `render_lesson.py`.
- Aperçu animé des poses (sans prise) : `cd compositing` puis `npm run studio:avatar`, composition `AvatarPreview`.
- Diagnostic d'un enregistrement de voix (format, niveaux, bruit de fond, saturation) : `.venv\Scripts\python.exe tools\clean_voice.py <enregistrement> --analyze-only`.
- Nettoyage d'une voix (coupe-bas 80 Hz, débruitage `afftdn` appris sur le silence de début, coupe des silences de bord, de-esser, compression, gain fixe + limiteur, −16 LUFS, WAV 48 kHz 24 bits) : `.venv\Scripts\python.exe tools\clean_voice.py <enregistrement>`. Sortie : `<nom>-clean.wav` et `<nom>-clean.report.json`. Options : `--no-denoise` (entrée déjà nettoyée par Adobe), `--noise-sample 0.2-1.8`, `--denoise-strength 12`, `--no-trim`.
- Prompteur pour l'enregistrement de la voix (page HTML autonome, toutes les vidéos, marqueurs retirés, défilement automatique en mots/min avec pauses de ponctuation, compte à rebours puis 3 s de silence avant le texte) : `.venv\Scripts\python.exe tools\build_teleprompter.py --open`. Sortie : `exercises\exercise-1\renders\teleprompter.html` (non versionnée, à régénérer après toute modification des scripts). Gabarit : `tools/teleprompter_template.html`. Raccourcis : touche `?` dans la page.
- Montage automatique d'un rush (transcription Whisper mise en cache, puis `-edit.wav`, `-edit.report.md`, `-edit.labels.txt`, `-edit.json` à côté du rush) : `.venv\Scripts\python.exe tools\edit_voice.py exercises\exercise-1\video-03\recordings\narration\rush-<date>-<heure>.m4a`. Options : `--sentence-pause 0.6`, `--row-pause 0.9`, `--labels <repères Audacity corrigés>` (seuls les repères `keep…` et `room tone` sont gardés), `--model`, `--device cpu|cuda`. Puis nettoyage avec `clean_voice.py` sur le `-edit.wav`.
- Alignement de la voix finale et remplacement de la voix de la vidéo : `.venv\Scripts\python.exe tools\align_voice.py exercises\exercise-1\video-03\recordings\narration\rush-<date>-<heure>-edit-clean.wav` (écrit `recordings/voice/audio.wav` et `markers.json`, déplace la voix SAPI dans `voice-placeholder/`). Une nouvelle prise Excel (`run_timeline.py`) est ensuite nécessaire.
- Recalculer les TC et la durée estimée des scripts (après toute modification du texte prononcé) : `py tools/estimate_timecodes.py exercises/exercise-1/video-*/script.md`. Dans Git Bash, préfixer par `PYTHONIOENCODING=utf-8` si la console affiche mal les accents.