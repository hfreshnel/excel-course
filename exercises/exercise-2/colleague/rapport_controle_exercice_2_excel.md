# Rapport de contrôle — Exercice 2 Excel

## Conclusion

Le script a été contrôlé à partir des classeurs fournis et corrigé. Une feuille de démonstration prête à filmer a été créée : `Exercice2_demo_Q1_pret_a_filmer.xlsx`. Elle reprend les 18 lignes complètes de la feuille `SOL` et place les dix formules de contrôle dans une zone dédiée. Le classeur d’origine reste intact.

## Contrôles effectués

- Feuilles du classeur de départ : `QS`, `Q1`, `S2`, `S3`, `S5`, `SOL` et graphique `CC`. Aucune feuille `S4` n'existe.
- `Q1` contient 18 personnes sur les lignes 2 à 19. Les lignes 22 à 31 servent aux réponses des questions 1 à 9.
- Les colonnes `Salaries`, `Classes`, `Pay`, `Expectations` et `Affected` sont vides dans `Q1`. La feuille `SOL` du classeur de correction contient les valeurs complétées des 18 personnes.
- Les années des enseignants sont en `S2!B1:Z1`, leurs salaires en `S2!B2:Z2`.
- La table Universities est dans `S2!A34:D50` : en-têtes ligne 34, données lignes 35 à 50.
- La table structurée de produits est illustrée dans la correction `SOL!B202:J217`; la conversion de prix est en `SOL!B222:F236`.
- Les formules dans la correction sont en anglais et plusieurs plages nommées n'existent que dans le classeur solution. Le script corrigé utilise des références explicites dans les exemples concernés.

## Résultats de contrôle calculés à partir des 18 lignes complétées de `02-sol.xlsx`, feuille `SOL`

| Question | Calcul demandé | Résultat attendu |
|---|---|---:|
| 1 | NB sur les âges | 18 |
| 1 | NBVAL sur les noms | 18 |
| 2 | Salaires strictement supérieurs à 4 000 | 8 |
| 3 | Salaire > 4 000 et augmentation > 25 % | 3 |
| 4 | Somme des salaires > 4 000 | 48 654 |
| 5 | Somme des salaires > 4 000 et objectifs > 33 % | 6 066 |
| 6 | Moyenne des salaires <= 4 000 | 2 770,90 |
| 7 | Moyenne des salaires <= 4 000 et âge < 22 | 2 897 |
| 8 | Maximum de Pay si âge > 33 et Goals > 25 % | 4 532,88 |
| 9 | Minimum de Goals si classe `Upper Class` et âge < 33 | 17 % |

Ces résultats ont été calculés indépendamment à partir des données du classeur de correction, pas en ouvrant Excel et en exécutant les formules localisées. Ils servent de valeurs de contrôle lors de la captation.

## Écarts dans les fichiers d'origine

1. La formule de correction de la question 5 (`SUMIFS(Salaries,Goals,">33%")`) ne vérifie pas le salaire supérieur à 4 000. Le script applique les deux conditions de l'énoncé.
2. La formule de correction de la question 7 (`AVERAGEIFS(Salaries,Ages,"<22")`) ne vérifie pas le salaire inférieur ou égal à 4 000. Le script applique les deux conditions de l'énoncé.
3. L'énoncé dit `Upper Classes`, tandis que les données utilisent `Upper Class`. Le script retient la valeur effectivement présente dans la table.
4. Les questions 10 à 13 et 20 à 25 s'appuient en partie sur des zones d'exemple du classeur solution. Les cellules de démonstration et les limites entre fichier de départ et fichier de correction sont précisées dans le script.
5. Le fichier de correction contient certaines formules modernes/anglaises (`XLOOKUP`, `MAXIFS`, `MINIFS`) que les versions d'Excel plus anciennes ou localisées peuvent traiter différemment. La captation doit utiliser Excel Microsoft 365 en français comme prévu.

## Consigne de production indispensable

Pour filmer les questions 1 à 9, ouvrir `Exercice2_demo_Q1_pret_a_filmer.xlsx` : les données complètes et les dix formules sont déjà en place. Pour les autres vidéos, suivre les feuilles et plages explicites du script et faire les manipulations destructives (tri, sous-totaux, TCD) sur une copie. Les fichiers d’origine ne sont pas modifiés.
