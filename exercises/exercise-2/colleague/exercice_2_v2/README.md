# Exercice 2 — Vidéos 00 à 02, version révisée

- Les scripts sont séparés par vidéo.
- Les formules sont dictées dans le texte prononcé et saisies via des actions déterministes.
- Les noms de plages sont créés en vidéo 1 sur les colonnes de Q1.
- La colonne Salaries est reprise depuis la feuille SOL du classeur de départ de référence pour la démonstration, sous réserve de validation client.
- Pay et Classes sont calculés avant les questions 8 et 9.
- La question 9 utilise `Upper Class`, libellé présent dans les données.
- La liste déroulante est construite dans `Q1!E22`, et RECHERCHEV est réalisée dans le classeur de départ.
- Les exemples ESTVIDE et ABS sont recréés dans des cellules de Q1.

## Point nécessitant une décision client
La question 8 est ambiguë : la feuille SOL calcule le maximum de `Pay` (salaire après augmentation), tandis qu'une autre partie de la correction semble traiter Pay comme le taux d'augmentation. Ce script suit SOL et présente `Pay` comme le salaire après augmentation, avec un résultat attendu de 4 532,88. Faire confirmer l'intitulé avant publication.

## Autre point à confirmer
Confirmer que les salaires de `SOL!D2:D19` doivent être repris dans `Q1!D2:D19`.
