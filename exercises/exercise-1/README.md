# EXERCICE 1 — SCRIPTS

Version production avec **texte prononcé + indications écran + actions Excel**.

## Structure

- **Vidéo 0** : présentation de l'énoncé et feuille de route. Elle ne compte pas dans les étapes.
- **Vidéos 1 à 9** : les neuf étapes de la résolution. Chacune s'ouvre sur le bandeau « Étape X sur 9 — titre » et sur une phrase de rappel prononcée qui situe l'étape (« troisième étape sur neuf », « Neuvième et dernière étape »…), formulée différemment à chaque vidéo et rattachée à la précédente.

| Étape | Vidéo | Consigne de l'énoncé |
|---|---|---|
| 1 | Construire le tableau | 1 (feuille D1, Cambria) et couleur d'onglet (3) |
| 2 | Nommer ses plages | 2 |
| 3 | Prix soldé, économie et évolution | 3 |
| 4 | TTC, HT et contrôle | 3 |
| 5 | CA, % CA et synthèses | 3 |
| 6 | Histogramme « CV Ventes » (feuille G1) | 4 |
| 7 | Secteurs 3D « Répartition du CA TTC » (feuille G2) | 4 |
| 8 | Barres « Sales » (feuille G3) | 4 |
| 9 | Graphique combiné « Evolution » (feuille G4) | 4 |

## Convention

Chaque script utilise le format :

`TC | À l'écran | Texte prononcé | Action Excel`

- **Texte prononcé** : seule colonne envoyée au générateur de voix. Les nombres y sont écrits comme ils doivent être dits (« cinq virgule cinq pour cent »). Formules et noms se lisent comme un humain les dit, sans rien épeler : « saisissez égal, prix hors taxes multiplié par le taux de solde ». La syntaxe exacte s'affiche dans la carte de saisie. Pour que le rendu retrouve chaque jeton, la dictée suit « saisissez » et s'arrête à la fin de phrase ou à « , puis ». Les noms qui ne se disent pas comme ils s'écrivent sont déclarés dans `dictation-lexicon.json`.
- **À l'écran** : ce que le montage affiche ou met en surbrillance (bandeaux, encadrés, plages citées).
- **Action Excel** : ce que l'automatisation exécute. Les formules y sont écrites **en version française d'Excel**, telles que l'élève les tape. L'automatisation devra les écrire avec `Range.Formula2Local`, ou les traduire en anglais pour `Range.Formula2`. Une formule n'est saisie que dans sa première cellule : la propagation remplit le reste.
- **TC** : estimation calculée par `tools/estimate_timecodes.py` à partir du nombre de mots prononcés (140 mots/min). Le timing réel viendra des timestamps de l'audio.
- **Marqueurs** `{@nom}` dans le texte prononcé : ils ne sont pas prononcés et ne changent pas le texte. Ils indiquent le mot auquel une action ou une surbrillance de `timeline.json` se déclenche (au début du mot qui suit le marqueur). Chaque ligne a en plus un marqueur implicite `r1`, `r2`… Avant d'envoyer le texte à un générateur de voix, il faut retirer les marqueurs (`tools/video_script.py`, fonction `readCleanSpokenText`). Vidéo annotée à ce jour : **vidéo 3**.
- **Poses de l'avatar** `{pose:id}` dans le texte prononcé : même règle de déclenchement, jamais prononcées. La pose dure jusqu'à la fin de la phrase, puis l'avatar revient en `neutral`. Ids disponibles : voir `assets/avatar/prompts.md` (lot 1 : `neutral`, `welcome`, `explain`, `point`, `warning`, `cheer`). Vidéo annotée à ce jour : **vidéo 3** (24 poses).

## Choix de résolution

- **Feuilles** : tableau sur `D1` (consigne), graphiques sur les feuilles graphiques `G1` à `G4`.
- **Noms de plages** (15, sans accents) : `Periode`, `Annee`, `Produits`, `Prix_HT`, `Prix_Solde`, `Economie`, `Prix_Haut`, `Evo`, `Quantite`, `Prix_TTC`, `Prix_HT_C`, `CA_TTC`, `PCA`, `Solde` (F20), `TVA` (F21).
- **Prix soldé** : `=Prix_HT*Solde`. Le taux de 44 % est présenté comme « le prix soldé représente 44 % du prix HT », pour coller aux valeurs de l'énoncé sans laisser croire à une remise de 44 %.
- **% CA** : `=CA_TTC/SOMME(CA_TTC)`, sans nom dédié pour le total. Total en L14 (`=SOMME(CA_TTC)`), contrôle à 100 % en M14 (`=SOMME(PCA)`).
- **Habillage des graphiques** : fond de mur (`assets/charts-background.jpg`), titres et étiquettes « Maximum » comme dans l'énoncé.

## Erreurs de l'énoncé corrigées en vidéo

| Vidéo | Erreur | Correction |
|---|---|---|
| 1 | En-tête K1 écrit `Prix_HT`, doublon de la colonne D | `Prix HT vérif` |
| 7 | Graphique en secteurs titré « Prix HT » alors qu'il représente le % CA | Données % CA conservées, titre « Répartition du CA TTC » |
| 8 | Axe des catégories titré « Périodes » alors qu'il porte des années | « Années » |
| 9 | Courbes empilées : le Prix TTC s'affiche à environ 195 € au lieu de 100,23 € | Courbes simples |

## Valeurs de contrôle

CA TTC total 34 965,87 € · moyenne TTC 61,89 € · maximum de CA 6 013,50 € (novembre) · minimum du % CA 1,12 % (août) · Prix TTC de janvier 100,23 €. Ces valeurs correspondent à `solution/02-solution.xlsx` et au tableau de l'énoncé.
