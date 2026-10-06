# VIDÉO 5 — CA, % CA et synthèses

**Durée estimée :** environ 3 min 15 s (texte parlé à 140 mots/min, à recaler sur le rendu audio)

| TC | À l'écran | Texte prononcé | Action Excel |
|---|---|---|---|
|00:00|Bandeau « Étape 5 sur 9 — CA, % CA et synthèses ». L à P surlignées.|Étape cinq sur neuf : le chiffre d'affaires et les synthèses. Nous connaissons nos prix ; nous voulons maintenant savoir combien nous avons vendu.|Ouvrir l'état de fin d'étape 4, feuille D1.|
|00:10|I2, J2 et L2 reliées.|Le chiffre d'affaires TTC, c'est la quantité vendue multipliée par le prix TTC. Pour janvier : 28 unités à 100 euros 23, soit 2 806 euros 30.|Aucune.|
|00:20|L2 active, puis L2 à L13 propagées.|En L2, saisissez : égal, Quantite, astérisque, Prix tiret bas TTC, puis Entrée. Les douze chiffres d'affaires apparaissent d'un coup.|L2 : =Quantite*Prix_TTC|
|00:30|K14, puis L14 actives.|Calculons le total. En K14, saisissez le libellé Somme TTC. En L14, saisissez : égal, SOMME, parenthèse ouvrante, C A tiret bas TTC, parenthèse fermante. La fonction SOMME additionne toutes les valeurs de la plage. Résultat : 34 965 euros 87.|K14 = Somme TTC. L14 : =SOMME(CA_TTC)|
|00:50|Encadré « Fonction = NOM(ce sur quoi elle travaille) ».|Remarquez la forme d'une fonction : son nom, puis, entre parenthèses, ce sur quoi elle travaille. Nous allons en utiliser trois autres dans un instant, sur le même modèle.|Aucune.|
|01:00|M2 active, puis M2 à M13 propagées.|Le pourcentage du chiffre d'affaires indique la part de chaque mois dans le total. En M2, saisissez : égal, C A tiret bas TTC, barre oblique, SOMME, parenthèse ouvrante, C A tiret bas TTC, parenthèse fermante. Chaque chiffre d'affaires est divisé par le total. Pour janvier : huit virgule zéro trois pour cent.|M2 : =CA_TTC/SOMME(CA_TTC)|
|01:25|M14 active.|Contrôle immédiat : en M14, additionnons les pourcentages, avec égal, SOMME de P C A. Nous devons obtenir exactement 100 pour cent. C'est le cas : aucune part ne manque.|M14 : =SOMME(PCA)|
|01:35|N2 active.|Passons aux synthèses. En N2, la moyenne des prix TTC : égal, MOYENNE, parenthèse ouvrante, Prix tiret bas TTC, parenthèse fermante. Résultat : 61 euros 89.|N2 : =MOYENNE(Prix_TTC)|
|01:45|O2 active. M9 surlignée.|En O2, la plus petite part du chiffre d'affaires : égal, MIN, parenthèse ouvrante, P C A, parenthèse fermante. Résultat : un virgule douze pour cent. C'est le mois d'août.|O2 : =MIN(PCA)|
|02:00|P2 active. L12 surlignée.|Et en P2, le plus gros chiffre d'affaires : égal, MAX, parenthèse ouvrante, C A tiret bas TTC, parenthèse fermante. Résultat : 6 013 euros 50, en novembre.|P2 : =MAX(CA_TTC)|
|02:10|F18, puis F19 actives.|Terminons avec les deux dates. En F18, saisissez : égal, AUJOURDHUI, parenthèse ouvrante, parenthèse fermante. En F19 : égal, MAINTENANT, et les deux parenthèses. AUJOURDHUI donne la date du jour ; MAINTENANT, la date et l'heure. Ces fonctions n'ont besoin d'aucune information : les parenthèses restent vides, mais elles sont obligatoires.|F18 : =AUJOURDHUI(). F19 : =MAINTENANT()|
|02:35|Encadré « Vos dates seront différentes : c'est normal ».|Vos dates seront différentes des nôtres : c'est normal. Elles se mettent à jour à chaque ouverture du classeur.|Aucune.|
|02:40|Valeurs de contrôle en incrustation.|Vérifiez vos résultats. Total du chiffre d'affaires : 34 965 euros 87. Moyenne TTC : 61 euros 89. Plus petite part : un virgule douze pour cent. Plus gros chiffre d'affaires : 6 013 euros 50. Si un chiffre diffère, revenez aux formules de l'étape concernée.|Aucune.|
|03:00|Tableau complet. Bandeau « Étape 5 sur 9 terminée ».|Notre tableau est terminé : il calcule tout seul, et il est contrôlé. Les trois premières consignes sont remplies. Place à la quatrième : les graphiques. À l'étape six, nous créerons un histogramme des ventes.|Enregistrer l'état de fin d'étape 5.|
