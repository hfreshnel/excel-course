# Professeur Ex — prompts de génération (GPT)

Avatar chibi 2D, cadrage à mi-corps, animé par poses clés au compositing (voir `CLAUDE.md`, section 2). Une image fixe complète par pose, fond transparent, bouche fixe.

## Méthode

1. **Référence chibi** (une seule fois) : joindre le **portrait de référence** et le prompt de l'étape 1 dans le même message. Demander plusieurs variantes, garder la plus fidèle au portrait. Elle sert aussi de pose `neutral` : **`poses/neutral.png`** (retenue le 2026-10-08).
2. **Chaque pose** : **nouvelle conversation**, joindre la **référence chibi** `poses/neutral.png` (jamais le portrait ni la pose précédente), coller le prompt de l'étape 2 en remplaçant `<POSE LINE>`. Enregistrer le résultat sous `poses/<id>.png` (id du tableau ci-dessous).
3. Toujours le même format (**portrait 2:3**) et le bloc personnage recopié **à l'identique**.

Contrôles sur chaque image :
- **Vraie transparence** : vérifier le canal alpha. Si le générateur dessine un faux damier, demander un fond uni gris clair et détourer avec `rembg`.
- **Cohérence** avec la référence : lunettes, barbe, cardigan (côtes), nombre de boutons de chemise, couleurs.
- **Bouche fermée** sauf `welcome` et `cheer` (images brèves à l'écran).
- Gauche et droite sont toujours exprimées **par rapport à l'image** (« toward the right side of the image »), jamais par rapport au personnage.
- Personnage **symétrique** (pas de poche ni d'accessoire d'un seul côté) : Remotion peut retourner une image horizontalement si l'avatar change de coin.

Placement prévu : **en bas à gauche** de l'écran. Excel se trouve donc en haut et à droite du personnage, d'où l'orientation de `point`.

## Bloc personnage

À recopier tel quel dans chaque prompt, à la place de `[CHARACTER BLOCK]`.

```text
CHARACTER — "Professeur Ex": an adult Black man drawn as a 2D chibi character
(big head, small rounded body, short arms). Dark brown skin. Short, rounded,
very curly black afro hair. Thin round black-rimmed glasses. Short black beard
joined to a thin mustache. Dark brown eyes, thick dark eyebrows. Outfit: open
navy blue cardigan with ribbed edges over a white collared shirt.
No logo, no pattern, no text, no pockets, no accessories other than the glasses.
STYLE: clean dark line art, flat colors with soft cel shading, exactly the same
art style, colors and proportions as the reference image.
FRAMING: waist-up shot (from the top of the head to the waist), centered,
arms and hands fully visible inside the frame, same scale and framing as the
reference image. Portrait 2:3 format.
BACKGROUND: transparent (real alpha channel, no checkerboard pattern),
no props unless stated.
```

## Étape 1 — Référence chibi

Image jointe : **portrait de référence**.

```text
Using the attached portrait as the reference for the face, hair, glasses, beard,
skin tone and clothing, draw the same man as a 2D chibi character.

[CHARACTER BLOCK]

Pose: front-facing, arms relaxed, hands loosely clasped in front of his waist.
Expression: gentle smile, mouth closed.
```

## Étape 2 — Une pose

Image jointe : **référence chibi**.

```text
Using the attached image as the exact character reference (same face, hair,
glasses, beard, outfit, colors, line art, proportions and scale), draw the same
character in a new pose.

[CHARACTER BLOCK]

Pose: <POSE LINE>
```

## Poses

Moments tirés des scripts de l'exercice 1.

| Lot | Id | `<POSE LINE>` | Usage | Exemple |
|---|---|---|---|---|
| 1 | `neutral` | *Référence chibi de l'étape 1, pas de nouvelle génération* | Par défaut | — |
| 1 | `welcome` | `one hand raised at shoulder height in a friendly wave, warm open smile.` | Ouverture, au revoir | « Bonjour et bienvenue… », « À tout de suite » |
| 1 | `explain` | `one hand open at chest height, palm up, as if explaining calmly; gentle smile, mouth closed.` | Explications | « Comme Prix HT désigne douze cellules… » |
| 1 | `point` | `body slightly turned toward the right side of the image, arm extended up and toward the right side of the image, index finger pointing there, eyes looking at his hand; interested smile, mouth closed.` | Diriger le regard vers Excel | « Regardez : une seule formule… », « Voici l'énoncé » |
| 1 | `warning` | `index finger raised next to his face, eyebrows slightly frowned, serious but kind look, mouth closed.` | Pièges, mises en garde | « Attention à un piège classique » |
| 1 | `cheer` | `both thumbs up in front of his chest, big happy open smile.` | Fin d'étape, félicitations | « Notre structure est prête », « Félicitations » |
| 2 | `skeptical` | `one hand on his chin, one eyebrow raised, small doubtful pout, mouth closed.` | Erreurs de l'énoncé | « Pourtant, son titre dit Prix HT » |
| 2 | `think` | `index finger on his temple, eyes looking up, thoughtful look, mouth closed.` | Questions posées à l'élève | « Pourquoi deux types, et surtout deux axes ? » |
| 2 | `remember` | `tapping his temple with his index finger, confident knowing smile, mouth closed.` | Règles à retenir | « Règle d'or : … », « Retenez : … » |
| 2 | `tip` | `winking, index finger raised, playful smile, mouth closed.` | Astuces | « Astuce : la touche Tabulation… » |
| 2 | `excited` | `both arms open wide, bright eyes, delighted smile, mouth closed.` | Effet « waouh » | « Vous verrez, cela change tout » |
| 2 | `check` | `holding a plain clipboard with a single green check mark (no text), satisfied look, mouth closed.` | Contrôles, checklist | Vidéo 4, vidéo 9 « quatre vérifications » |
| 3 | `pause` | `one palm facing forward at shoulder height, as if saying "pause", friendly smile, mouth closed.` | Invitation à mettre en pause | « mettez la vidéo en pause » (vidéo 1) |
| 3 | `neutral-eyes-closed` | *Modification de `neutral`* : `same image, only close his eyes; change nothing else.` | Clignements automatiques | — |

Le lot 1 suffit pour une première vidéo de test.
