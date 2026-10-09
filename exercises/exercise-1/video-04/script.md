# VIDÉO 4 — TTC, HT et contrôle

**Durée estimée :** environ 2 min 55 s (texte parlé à 140 mots/min, à recaler sur le rendu audio)

| TC | À l'écran | Texte prononcé | Action Excel |
|---|---|---|---|
|00:00|Bandeau « Étape 4 sur 9 — TTC, HT et contrôle ».|Quatrième étape sur neuf. Nos formules calculent seules, mais calculent-elles juste ? La TVA va nous donner le moyen de le prouver.|Ouvrir l'état de fin d'étape 3, feuille D1.|
|00:10|Formules de l'énoncé surlignées. F21 surlignée.|L'énoncé fournit deux formules, l'une pour passer du HT au TTC, l'autre pour revenir. Prix TTC égale prix HT multiplié par, entre parenthèses, un plus le taux de TVA. Et prix HT égale prix TTC divisé par un plus le taux de TVA. Notre TVA, en F21, vaut cinq virgule cinq pour cent.|Aucune.|
|00:30|Encadré « 100 % + 5,5 % = 1,055 ».|Pourquoi un plus la TVA ? Parce que le prix TTC, c'est le prix HT, plus la TVA. Cent pour cent du prix, plus cinq virgule cinq pour cent : nous multiplions donc par un virgule zéro cinq cinq.|Aucune.|
|00:50|J2 active, puis J2 à J13 propagées.|L'aller d'abord. En J2, saisissez égal, prix hors taxes multiplié par, entre parenthèses, 1 plus TVA. Validez avec Entrée : la formule se propage jusqu'à J13. Pour janvier, 95 euros hors taxes donnent 100 euros 23 TTC.|J2 : =Prix_HT*(1+TVA)|
|01:05|J2 et K2 reliées par une flèche « TTC → HT ».|Un résultat qui a l'air juste n'est encore qu'une hypothèse. Mettons-le à l'épreuve en remontant le calcul : si notre formule est juste, en repartant du prix TTC, nous devons retrouver exactement le prix HT de départ.|Aucune.|
|01:20|K2 active, puis K2 à K13 propagées.|La seconde formule de l'énoncé fait ce trajet retour. En K2, saisissez égal, prix TTC divisé par, entre parenthèses, 1 plus TVA. Puis Entrée.|K2 : =Prix_TTC/(1+TVA)|
|01:30|D2 à D13 et K2 à K13 comparées ligne par ligne.|Comparez les colonnes D et K : les valeurs sont identiques, ligne par ligne. Notre calcul est cohérent dans les deux sens. C'est tout le rôle de cette colonne Prix HT vérif : un contrôle. Elle fait la différence entre un tableau qu'on espère juste et un tableau qu'on sait juste.|Aucune.|
|01:55|Encadré « Piège : #PROPAGATION! ». K5 surlignée, K2 en erreur.|Ce contrôle a tenu. Mais une formule propagée peut aussi refuser de se déployer, et l'erreur qu'elle affiche alors, vous la croiserez tôt ou tard. Imaginons qu'une valeur traîne dans la colonne, en K5. Excel ne peut plus remplir la zone : la formule de K2 affiche dièse PROPAGATION, point d'exclamation.|K5 = 0 (K2 affiche #PROPAGATION!).|
|02:15|K2 sélectionnée, zone en pointillés, K5 surlignée.|Excel n'écrase jamais une cellule occupée. Il préfère afficher cette erreur, et vous montre par un cadre en pointillés la zone qu'il voulait remplir. Cherchez la cellule qui gêne : ici, K5.|Sélectionner K2.|
|02:30|K5 effacée, K2 à K13 de nouveau propagées.|Sélectionnez K5 et appuyez sur la touche Suppr. La zone est libre : Excel propage aussitôt la formule. À mémoriser : dièse PROPAGATION signifie qu'une cellule bloque le passage.|Effacer K5.|
|02:40|Bandeau « Étape 4 sur 9 terminée ».|Nos prix TTC sont calculés, et prouvés. Ils ne disent pourtant rien de ce que les ventes rapportent. À l'étape cinq, prix et quantités se rejoignent dans le chiffre d'affaires, et le tableau livre ses premières synthèses.|Enregistrer l'état de fin d'étape 4.|
