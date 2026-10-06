# VIDÉO 4 — TTC, HT et contrôle

**Durée estimée :** environ 2 min 30 s (texte parlé à 140 mots/min, à recaler sur le rendu audio)

| TC | À l'écran | Texte prononcé | Action Excel |
|---|---|---|---|
|00:00|Bandeau « Étape 4 sur 9 — TTC, HT et contrôle ».|Étape quatre sur neuf : la TVA, et une habitude précieuse, contrôler ses calculs.|Ouvrir l'état de fin d'étape 3, feuille D1.|
|00:05|Formules de l'énoncé surlignées. F21 surlignée.|L'énoncé nous donne deux formules. Prix TTC égale prix HT multiplié par, entre parenthèses, un plus le taux de TVA. Et dans l'autre sens, prix HT égale prix TTC divisé par un plus le taux de TVA. Notre TVA, en F21, vaut cinq virgule cinq pour cent.|Aucune.|
|00:25|Encadré « 100 % + 5,5 % = 1,055 ».|Pourquoi un plus la TVA ? Parce que le prix TTC, c'est le prix HT, plus la TVA. Cent pour cent du prix, plus cinq virgule cinq pour cent : nous multiplions donc par un virgule zéro cinq cinq.|Aucune.|
|00:45|J2 active, puis J2 à J13 propagées.|En J2, saisissez : égal, Prix tiret bas H T, astérisque, parenthèse ouvrante, 1, plus, TVA, parenthèse fermante. Validez avec Entrée : la formule se propage jusqu'à J13. Pour janvier, 95 euros hors taxes donnent 100 euros 23 TTC.|J2 : =Prix_HT*(1+TVA)|
|01:00|J2 et K2 reliées par une flèche « TTC → HT ».|Faisons maintenant le chemin inverse. Si notre calcul est juste, en repartant du prix TTC, nous devons retrouver exactement le prix HT de départ.|Aucune.|
|01:10|K2 active, puis K2 à K13 propagées.|En K2, saisissez : égal, Prix tiret bas TTC, barre oblique, parenthèse ouvrante, 1, plus, TVA, parenthèse fermante. Puis Entrée.|K2 : =Prix_TTC/(1+TVA)|
|01:20|D2 à D13 et K2 à K13 comparées ligne par ligne.|Comparez les colonnes D et K : les valeurs sont identiques, ligne par ligne. Notre calcul est cohérent dans les deux sens. C'est tout le rôle de cette colonne Prix HT vérif : un contrôle. Un professionnel ne se contente pas d'un résultat ; il vérifie qu'il est juste.|Aucune.|
|01:40|Encadré « Piège : #PROPAGATION! ». K5 surlignée, K2 en erreur.|Voyons une erreur que vous rencontrerez forcément. Imaginons qu'une valeur traîne dans la colonne, en K5. Excel ne peut plus remplir la zone : la formule de K2 affiche dièse PROPAGATION, point d'exclamation.|K5 = 0 (K2 affiche #PROPAGATION!).|
|01:55|K2 sélectionnée, zone en pointillés, K5 surlignée.|Excel n'écrase jamais une cellule occupée. Il préfère afficher cette erreur, et vous montre par un cadre en pointillés la zone qu'il voulait remplir. Cherchez la cellule qui gêne : ici, K5.|Sélectionner K2.|
|02:05|K5 effacée, K2 à K13 de nouveau propagées.|Sélectionnez K5 et appuyez sur la touche Suppr. La zone est libre : Excel propage aussitôt la formule. Retenez ce réflexe : dièse PROPAGATION signifie qu'une cellule bloque le passage.|Effacer K5.|
|02:20|Bandeau « Étape 4 sur 9 terminée ».|Nos prix TTC sont calculés et contrôlés. À l'étape cinq, nous calculerons le chiffre d'affaires et nos indicateurs de synthèse.|Enregistrer l'état de fin d'étape 4.|
