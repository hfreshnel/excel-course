# EXERCICE 2 — SCRIPTS

Version de travail du 2026-10-12 : scripts du collègue (pack final reçu le 2026-10-12, `colleague/exercice_2_scripts_final/`, vidéos 0 à 10) analysés puis réécrits avec carte blanche de Wilfried. **Non validés** : à relire par Wilfried et le collègue, puis à confirmer côté client pour les points listés en fin de document.

## Structure

- **Vidéo 0** : présentation de l'énoncé et feuille de route. Elle ne compte pas dans les étapes.
- **Vidéos 1 à 12** : les douze étapes. Chacune s'ouvre sur le bandeau « Étape X sur 12 — titre » et sur une phrase de rappel tournée différemment à chaque vidéo, et se termine sur la question que la vidéo suivante résout.

| Étape | Vidéo | Questions | Feuille | Durée estimée |
|---|---|---|---|---|
| — | Présentation | — | QS | 2 min 10 |
| 1 | Nommer les colonnes et compter | 1 à 3 (+ colonnes Classes et Pay) | Q1 | 4 min 20 |
| 2 | Additionner, moyenner, extrêmes | 4 à 9 | Q1 | 3 min 45 |
| 3 | Liste déroulante et recherche | 10 à 13 | Q1 | 2 min 45 |
| 4 | Graphique dynamique des métiers | 14 et 15 | S2 | 3 min 10 |
| 5 | Sous-totaux et tableau de bord | 16 | S2 | 2 min 55 |
| 6 | Tableau et graphique croisés dynamiques | 17 et 18 | S2, TCD | 2 min 20 |
| 7 | Importer un fichier CSV | 19 | Ecoles | 2 min 40 |
| 8 | Tableaux structurés et références | 20 et 21 | S3 | 3 min 50 |
| 9 | SI imbriqués | 22 | S3 | 2 min 30 |
| 10 | ET, OU et NON | 23 | S3 | 4 min 25 |
| 11 | TRANSPOSE, RECHERCHEH, RECHERCHEX | 24 | S3 | 3 min 10 |
| 12 | INDEX et EQUIV, bilan | 25 | S3 | 3 min 15 |

Total : environ 41 min de texte parlé (140 mots/min, à recaler sur la voix). Le collègue proposait 11 vidéos ; ses vidéos 1 (questions 1 à 9) et 4 (questions 16 à 18) dépassaient 6 à 8 minutes, contre 2 min 30 à 6 min pour l'exercice 1 : chacune est coupée en deux.

## Convention

Format et règles de l'exercice 1 (voir `exercises/exercise-1/README.md`), avec ces précisions :

- **Texte prononcé** : poses de l'avatar `{pose:id}` posées ; marqueurs d'action `{@nom}` **pas encore posés**, ils seront ajoutés avec les timelines. Aucune énumération de ce que montre l'écran (listes de noms, valeurs de contrôle, réglages de boîtes de dialogue) : un encadré la porte.
- **Dictées** : chaque formule suit « tapez » (ou « saisissez » pour la zone Nom) et s'arrête au point ; jamais de « , puis » à l'intérieur (il clôt la dictée pour `render_lesson.py`). Les critères numériques s'écrivent d'un bloc (`4000`, `220000`) pour être retrouvés dans la formule. Toutes les dictées ont été passées à l'aligneur de `render_lesson.py` le 2026-10-12 : elles passent toutes, sauf les cas listés dans « Pipeline ».
- **Diction** (`tts-lexicon.json`) : fonctions lues comme un formateur les dit (NB.SI.ENS « enne bé si ensemble », RECHERCHEV « recherche vé », EQUIV « équiv », ABS « a bé esse »), sigles épelés (USA, CSV, TCD, XLSX), mots anglais écrits phonétiquement (Upper Class « Apeur Classe », Working Class, Pay, Teacher, Good, Bad, Grades, Price, James, Mason). Les mots anglais sont évités à l'oral quand l'écran suffit (indicateurs, districts, noms de métiers autres que Teacher). Contrôle fait avec `tools/tts_text.py` : aucun sigle, chiffre ni symbole ne reste dans le texte envoyé au modèle.
- **Dictées et lexique** (`dictation-lexicon.json`) : les noms de plages se retrouvent par leur orthographe ; seules les références avec `$` y sont déclarées.
- **Option A** : validation des données, sous-totaux, plan, TCD, tableaux, import CSV, ligne des totaux sont exécutés par COM ; le montage affiche le chemin (`menuPath`) et les réglages des boîtes de dialogue (`callout`). Le texte parlé a été écrit pour rester juste sans l'interface visible (« dans l'onglet Données, choisissez… », jamais « cliquez ici »).

## Choix de résolution

- **Feuilles** : on travaille dans les feuilles visibles de l'énoncé, Q1 (questions 1 à 13), S2 (14 à 18), S3 (20 à 25), plus deux feuilles créées, `TCD` et `Ecoles`. **`S5`, `SOL` et `CC` sont masquées dans l'énoncé** : `SOL` est le corrigé, `S5` une copie corrigée des tableaux de `S3` (formules cassées, `#NOM?`), `CC` le graphique croisé du corrigé. Elles ne sont jamais montrées.
- **État de départ** (`states/state-00.xlsx`, à générer) : l'énoncé, avec les salaires de `SOL!D2:D19` recopiés en `Q1!D2:D19` (colonne vide dans l'énoncé, voir les points client).
- **Noms de plages** (Q1, en français, sans accents) : `Clients` (A, déjà attendu par la validation existante de E22), `Ages` (B), `Salaires` (D), `Classes` (E), `Augmentations` (F, Pay Rise), `Nouveaux_Salaires` (G, Pay), `Objectifs` (H). Plus `Metiers` (S2!A2:A19). Les en-têtes sont en anglais : des noms français rendent les formules lisibles comme les questions, et se prononcent sans lexique phonétique. Countries, Expectations et Affected ne servent à aucune question : ni nommées ni calculées.
- **Propagation** : une seule formule par colonne dès que possible : Pay `=Salaires*(1+Augmentations)`, Classes `=SI(Salaires>4000;"Upper Class";"Working Class")` (libellés du corrigé), ABS sur une plage, années `=B1:Z1`, salaires du métier choisi, écart des sous-totaux, mentions des SI imbriqués, SI sur la colonne OU, TRANSPOSE. Formules **recopiées**, et l'explication est donnée en vidéo : MOYENNE par élève (une propagation demanderait BYROW), ET et OU (ils résument leurs arguments en une seule réponse), la grille de conversion de la question 21 (sujet même de la question).
- **Question 8** : lecture du corrigé, `MAX.SI.ENS` sur Pay (salaire après augmentation) : 4 532,88.
- **Question 14** : `=RECHERCHEV(A23;A2:Z19;COLONNE(B1:Z1);FAUX)` en B23, propagée sur la ligne. RECHERCHEV vient d'être vue (étape 3) ; RECHERCHEX, plus simple ici (`=RECHERCHEX(A23;A2:A19;B2:Z19)`), est gardée pour l'étape 11, qui y renvoie. Zone de pilotage en lignes 22 et 23 (A22 vide pour que la ligne des années serve d'étiquettes). Graphique en courbes (le corrigé fait un graphique à bulles).
- **Question 16** : pas de tri (les lignes sont déjà groupées) ; sous-totaux Somme sur Goals et Results ; colonne Écart propagée ; histogramme tracé au niveau 2 du plan, total général exclu. Les tendances en Wingdings et le graphique combiné du corrigé ne sont pas repris.
- **Questions 17 et 18** : TCD sur `S2!A57:J93` d'abord par état (agrégation réelle), puis réorganisé comme le corrigé (filtre état = New York, universités en lignes, Revenues et Investissement) ; histogramme croisé ; la croissance (pourcentage) n'est pas tracée.
- **Question 19** : `data/02-data.csv`, import Power Query, identifiants en Texte (zéros de tête), démonstration du piège du double clic.
- **Question 20** : tableau `Produits`, colonne calculée Moyenne (référence structurée), ajout puis retrait d'une ligne, ligne des totaux en Moyenne.
- **Question 21** : erreur montrée d'abord (`=C25*D38` recopiée), puis `=$C25*D$38`, puis F4.
- **Question 22** : seuils lus dans les cellules, `>=` pour Excellent et Good (le corrigé prend `>` pour Good ; mêmes résultats avec ces données).
- **Question 23** : ET sur une plage (`ET(C59:F59>=$I$71)`, les quatre notes), OU, SI sur la colonne OU, ET combiné à OU, et un exemple de NON ajouté (colonne « Prospect » : critères remplis mais pas client), l'énoncé et le corrigé n'en ayant aucun.
- **Question 24** : RECHERCHEV en rappel, TRANSPOSE (formule propagée au lieu d'une recopie à la main), RECHERCHEH, RECHERCHEX avec recherche vers la gauche et message d'absence.
- **Question 25** : INDEX et les trois EQUIV du corrigé, puis INDEX avec deux EQUIV pilotés par des cellules.

## Erreurs corrigées et expliquées en vidéo

| Vidéo | Erreur de l'énoncé | Correction |
|---|---|---|
| 2 | Question 9 : « Upper Classes », alors que les cellules contiennent « Upper Class » | Critère « Upper Class », règle du critère texte exact |
| 4 | Question 14 : « liste des enseignants », alors que le tableau liste dix-huit métiers | Liste de tous les métiers |
| 10 | En-tête `S3!H58` « Yes/No » sur une colonne de mentions | « Grades » |
| 10 | Titre `S3!B89` « EI, OU et SI » | « ET, OU et SI » |
| 12 | `S3!B133` : « Bob » suivi d'une espace, la recherche exacte échoue | Retapé sans espace |

Non signalées à l'oral, à transmettre au client : fautes de la feuille QS (« peronnes », « Valeure », « Si imbriquées », « Gestion d'un fichiers CSV »), titre « Recherche ? » en `S3!B138`.

### Erreurs du corrigé (feuille `SOL`, masquée), évitées sans être citées

| Question | Erreur | Valeur juste |
|---|---|---|
| 5 | `SOMME.SI.ENS` sans la condition sur le salaire : 8 104 | 6 066 (le piège est expliqué en vidéo 2) |
| 7 | `MOYENNE.SI.ENS` sans la condition sur le salaire : 4 063,33 | 2 897 |
| 14 | RECHERCHEV enchaînées, chaque année cherchée par le salaire de l'année précédente : Doctor et Accountant ont 9 733 en 2000, Accountant affiche la courbe de Doctor | Recherche par le nom du métier (expliquée en vidéo 4) |
| 24 | Tableau transposé recopié à la main : `SOL!C311` vide au lieu de Pomme, `S5!C91` « Salade » | TRANSPOSE |
| 22 | Good testé avec `>` alors que les seuils se lisent « à partir de » | `>=` |

## Valeurs de contrôle

| Question | Valeur | Question | Valeur |
|---|---|---|---|
| 1 (NB, NBVAL) | 18, 18 | 11 (Olivia) | 3 756 |
| 2 | 8 | 13 | 21, 8, 40, 33 |
| 3 | 3 (Emma, Mason, Michael) | 16 | 15/14, 14/13, 13/14, 12/17, total 54/58 |
| 4 | 48 654 | 17 | Californie 23 455 510 ; New York : Columbia, Cornell, NYU |
| 5 | 6 066 | 21 | premier téléviseur : 1 688,70 £, 1 970,15 €, 314 509,55 ¥ |
| 6 | 2 770,90 | 22 | Excellent : Emily, Assia ; Bad : Noah ; Good : les sept autres |
| 7 | 2 897 | 23 | ET : Excellent Assia, Good Emily, Olivia, Mia ; OU : Alex, Olivia, Noah, Assia ; ET et OU : Alex, Olivia, Assia ; Prospect : Noah |
| 8 | 4 532,88 (Charlotte) | 24 | Pomme 6, Orange 5, Kiwi 2, code C3 → Orange |
| 9 | 17 % (William) | 25 | 18 ; EQUIV 4, 2, 3 ; Alice en math 16 ; Bob en anglais 11 |

Pay de Lili : 3 534. Valeurs recalculées le 2026-10-12 à partir de `data/01-data.xlsx` (et des salaires de `SOL`).

## Analyse du pack du collègue (2026-10-12)

Vidéos 0 à 2 identiques à la v2 du 2026-10-11 (restes déjà relevés : dictées incomplètes, Pay et Classes recopiés, « Lower Class », transitions annoncées). Vidéos 3 à 10, nouvelles :

- **Adresses fausses ou en conflit** : tableau des métiers donné en `S2!A2:Z31` (il s'arrête en Z19) ; zone de pilotage en `S2!A34:Z37`, sur le tableau des universités (A33 à D50) ; exemple de RECHERCHEH sur `J4:K5`, qui ne couvre que deux colonnes du tableau transposé, avec un résultat attendu (42) faux.
- **Mauvaise feuille de travail** : les vidéos 6 à 10 recopient des tableaux de `SOL` vers `S5` ou des zones libres de `S3`, alors que `S3` contient déjà ces tableaux, vides, aux bonnes adresses, et que `S5` (masquée) contient leurs solutions. La vidéo 0 présentait `S5` et `SOL` à l'élève.
- **TCD** : construit sur le tableau des indicateurs, alors que le corrigé le construit sur le tableau des universités (A57 à J93).
- **Conventions non respectées** : formules non dictées, transitions annoncées (« Cette quatrième étape porte sur… », « Commençons »), récapitulatifs récités, consignes d'interface qui supposent l'écran visible (option A), recopies là où la propagation suffit, exemple de NON abstrait (`NON(ESTVIDE(A1))`).
- **Repris** : le découpage par thèmes, l'explication du doublon Doctor et Accountant, la lecture de Pay en question 8, les seuils lus dans des cellules, l'ordre des tests des SI imbriqués, la mise en garde sur les zéros de tête des CSV.

## Points à valider

**Par Wilfried**
- Découpage en 13 vidéos (12 étapes) au lieu de 11.
- Noms de plages en français.
- Question 14 en RECHERCHEV et COLONNE (plutôt que RECHERCHEX).
- Tendances et graphique combiné du corrigé non repris (question 16) ; croissance absente du graphique croisé (question 18).
- Exemple de NON ajouté (colonne Prospect).
- Écoute de la diction : phrases de dictée longues en vidéo 10 (H91 et I91), à surveiller dans le rapport de voix.

**Par le client**
- Colonne Salaries vide dans Q1 : énoncé à corriger, ou salaires à fournir autrement ? Les scripts supposent un énoncé où ils sont présents.
- Question 8 : maximum de Pay (salaire après augmentation, 4 532,88, retenu) ou du taux d'augmentation (32 %) ?
- Question 14 : « enseignants » pour « métiers » ?
- Question 19 : `02-data.csv` est-il bien le fichier visé ? Rôle des CSV `04` à `08` ?
- Feuilles masquées `S5`, `SOL`, `CC` : le corrigé est livré dans le fichier de l'élève.

**Pipeline, avant les prises**
- `tokenizeFormula` (`tools/render_lesson.py`) ne reconnaît pas `$` : accepter `$` dans le motif des noms suffit, avec les entrées de `dictation-lexicon.json` (simulation faite le 2026-10-12 : vidéos 8 et 10 alignées).
- Références structurées (`Produits[@[Price 1]:[Price 4]]`, vidéo 8) : `"card": false`, ou extension du découpeur.
- Timelines et marqueurs `{@…}` à écrire. Événements à ajouter à `run_timeline.py` : validation de données (liste), sous-totaux et niveaux de plan, TCD (création, champs, filtre) et graphique croisé, tableau (création, nom, ligne ajoutée, ligne des totaux), import Power Query, ouverture d'un CSV avec `Local=True`.
- Génération de `state-00.xlsx` (énoncé + salaires).
- À vérifier dans un vrai Excel : ligne des années prise comme étiquettes avec A22 vide (vidéo 4) ; lignes masquées absentes du graphique au niveau 2 (vidéo 5) ; libellés du chemin Power Query et de « Remplacer l'étape actuelle » (vidéo 7) ; colonne calculée créée par COM dans un tableau (vidéo 8).
