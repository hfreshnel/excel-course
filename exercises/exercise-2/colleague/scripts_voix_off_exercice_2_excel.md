# Exercice 2 — Excel : Culture numérique
## Scripts de voix off pour débutants — Microsoft 365

**Base de travail :** `02-part-02/01-data.xlsx`  
**Classeur de correction fourni :** `02-part-02/02-sol.xlsx`  
**Public :** débutants, Excel en français. Les noms de fonctions et séparateurs peuvent différer de ceux du classeur source, qui contient plusieurs formules en anglais. Dans les vidéos, on utilise les noms français de Microsoft 365 et le séparateur `;`.

> **Consigne de production :** pour les questions 1 à 9, ouvrir `Exercice2_demo_Q1_pret_a_filmer.xlsx`. Les 18 lignes de données sont complètes et les dix formules sont déjà placées en `L22:L31` ; clique sur chaque cellule pendant la voix off pour montrer la formule et son résultat. Pour les vidéos suivantes, utiliser le classeur d'origine `02-part-02/01-data.xlsx` et suivre les feuilles/plages ci-dessous. Les fichiers d'origine restent intacts.

---

## Audit de concordance avec les classeurs fournis — version contrôlée

- Le classeur de départ `02-part-02/01-data.xlsx` contient les feuilles `QS`, `Q1`, `S2`, `S3`, `S5`, `SOL` et le graphique `CC`. Il n'existe pas de feuille `S4`.
- **Attention au tableau Q1 :** il contient 18 personnes, de la ligne 2 à la ligne 19. Les lignes 22 à 31 sont les emplacements des résultats des questions 1 à 9, et non des personnes. Les formules doivent donc utiliser les lignes 2 à 19, pas 2 à 31.
- **Données manquantes dans Q1 :** les colonnes `Salaries`, `Classes`, `Pay`, `Expectations` et `Affected` sont vides dans le classeur d'origine. Le fichier séparé `Exercice2_demo_Q1_pret_a_filmer.xlsx` résout ce problème pour la vidéo 1 : il contient les données complètes, les formules et les résultats de contrôle, sans modifier le classeur d'origine.
- Les données des enseignants sont dans `S2` : années en `B1:Z1`, salaires de Teacher en `B2:Z2`. La table Universities commence dans `S2` à la ligne 33 ; ses en-têtes sont à la ligne 34 et les données vont des lignes 35 à 50. Les sous-totaux déjà préparés sont dans la correction `SOL`, lignes 100 à 121.
- La table de produits et prix se trouve dans `S3`, lignes 4 à 18. La table des conversions de devises est dans `S3`, lignes 24 à 38. Les exemples d'étudiants et de recherches sont également présents dans `S3` (les numéros de lignes diffèrent de ceux de `SOL`). Pour les références ci-dessous, le script indique explicitement quelle feuille utiliser.
- Les formules de `02-sol.xlsx` sont en anglais et les noms définis (par exemple `Ages`, `Salaries`, `Rises`, `Goals`, `Pay`, `Classes`, `Matrix` et `Truth`) ne sont pas présents dans le classeur de départ. Les formules de ce script utilisent donc des plages explicites en français pour éviter les références nommées non définies.
- **Divergence confirmée dans la correction :** la formule de correction pour la question 5 n'applique pas le critère de salaire supérieur à 4 000 ; celle de la question 7 n'applique pas le critère de salaire inférieur ou égal à 4 000. Les formules du script suivent les deux conditions formulées dans l'énoncé.
- **Question 9 :** l'énoncé écrit « Upper Classes », mais les données et la correction utilisent `Upper Class`. La formule ci-dessous utilise donc la valeur réellement présente dans les données : `Upper Class`.
- Les manipulations de sous-totaux classiques ne sont pas proposées dans toutes les versions d'Excel pour une plage convertie en tableau structuré. Pour cette partie, utiliser une plage normale triée par indicateur ; pour les TCD et graphiques croisés dynamiques, créer une nouvelle feuille de démonstration à partir de la table Universities.

---

# VIDÉO 0 — Introduction générale
**Durée estimée :** 2 min 30  
**Objectif :** présenter les 25 questions et le parcours.

| TC | À l'écran | Texte prononcé | Action Excel |
|---|---|---|---|
| 00:00 | Titre « Excel — Culture numérique : exercice 2 » | Bonjour et bienvenue dans cette nouvelle série consacrée à Excel. Dans cet exercice, nous allons apprendre à compter, additionner et calculer des moyennes sous conditions, à rechercher des informations, à construire des graphiques et à manipuler des tableaux et des fichiers CSV. | Afficher le titre. |
| 00:20 | Feuille QS, questions 1 à 25 | L'exercice comporte vingt-cinq questions. Certaines portent sur un même thème : nous allons donc les regrouper en vidéos pour apprendre progressivement, sans répéter les mêmes explications à chaque question. | Afficher la feuille QS et surligner les questions. |
| 00:40 | Feuille Q1 avec les colonnes Clients, Ages, Countries, Salaries… | Nous commencerons par un tableau de personnes, avec leur âge, leur pays, leur salaire, leur augmentation et leurs objectifs. Il servira à comprendre les fonctions de comptage, les sommes et les moyennes conditionnelles. | Ouvrir Q1. |
| 01:00 | Aperçu des feuilles S2, S3, S5 et SOL | Ensuite, nous travaillerons sur plusieurs cas : l'évolution des salaires des enseignants, des données d'universités, des prix de produits, des tableaux structurés et des résultats d'étudiants. Chaque exemple sert à illustrer une fonctionnalité précise. | Montrer brièvement les feuilles S2, S3, S5 et SOL. |
| 01:25 | Bandeau « On comprend avant de mémoriser » | Le but n'est pas de recopier des formules sans les comprendre. Pour chaque fonction, nous verrons la question à résoudre, la logique de la formule, puis les erreurs les plus fréquentes. Vous pourrez ensuite adapter la méthode à vos propres tableaux. | Afficher le bandeau. |
| 01:50 | Feuille QS, questions 1 à 9 | Nous allons commencer par les fonctions statistiques avec critères. Gardez à l'esprit une règle essentielle : une condition sert à sélectionner les lignes qui doivent être prises en compte dans le calcul. | Sélectionner Q1. |
| 02:10 | Titre « Vidéo 1 — Compter et calculer sous conditions » | Ouvrez le classeur de départ, puis cliquez sur la feuille Q1. Nous allons examiner les données avant d'écrire nos premières formules. | Ouvrir `Exercice2_demo_Q1_pret_a_filmer.xlsx`, afficher la table complète, puis montrer les formules préremplies dans `L22:L31`. |

---

# VIDÉO 1 — Compter, additionner et calculer sous conditions
**Questions :** 1 à 9  
**Durée estimée :** 6 à 7 min  
**Objectifs :** NB, NBVAL, NB.SI, NB.SI.ENS, SOMME.SI, SOMME.SI.ENS, MOYENNE.SI, MOYENNE.SI.ENS, MAX.SI.ENS et MIN.SI.ENS.

| TC | À l'écran | Texte prononcé | Action Excel |
|---|---|---|---|
| 00:00 | Feuille Q1, tableau des personnes | Dans cette première vidéo, nous allons apprendre à répondre à des questions comme : combien de personnes sont dans le tableau ? Combien gagnent plus de quatre mille dollars ? Et quel est le salaire moyen d'un groupe défini par plusieurs critères ? | Montrer les colonnes A à J. |
| 00:20 | En-têtes Clients et Ages | Avant les formules, repérons les colonnes. La colonne Clients contient des noms, Ages contient les âges, Salaries les salaires, Pay Rise le taux d'augmentation, Pay le salaire après augmentation, et Goals le taux d'objectif. Les critères doivent toujours être appliqués à la bonne colonne. | Pointer chaque en-tête. |
| 00:45 | Cellule de résultat de NB | La question 1 demande de compter les personnes avec la fonction NB. NB compte uniquement les cellules qui contiennent des nombres. Il ne compte donc pas directement les noms. Pour compter les âges numériques, on utilise la plage des âges. En Excel français, la formule est de la forme égal NB, puis la plage entre parenthèses. | Dans `Q1_Demo`, cliquer sur `L22` : la formule `=NB(B2:B19)` est déjà saisie et renvoie 18. |
| 01:15 | Comparaison NB et NBVAL | Attention à la différence avec NBVAL. NBVAL compte les cellules non vides, qu'elles contiennent du texte ou un nombre. Pour compter les personnes à partir de leur nom, NBVAL est donc généralement plus adapté. La fonction NB répond à la question « combien de valeurs numériques ? », tandis que NBVAL répond à « combien de cellules remplies ? ». | Dans `Q1_Demo`, cliquer sur `L22` puis `L23` pour afficher `=NB(B2:B19)` et `=NBVAL(A2:A19)`. Les deux résultats attendus sont 18. |
| 01:50 | Question 2, salaires supérieurs à 4000 | Pour compter les salaires supérieurs à quatre mille, on utilise NB.SI. La fonction reçoit deux informations : la plage à examiner, puis le critère. Le critère doit être écrit entre guillemets : supérieur à quatre mille. Le signe supérieur est important : un salaire égal à quatre mille ne sera pas compté. | Dans `Q1_Demo`, cliquer sur `L24` pour afficher `=NB.SI(D2:D19;">4000")`. Le résultat attendu est 8. |
| 02:20 | Question 3, salaire et augmentation | La question suivante ajoute une deuxième condition : le salaire doit dépasser quatre mille et l'augmentation doit dépasser vingt-cinq pour cent. Dès que plusieurs conditions doivent être vraies en même temps, on utilise NB.SI.ENS. Chaque plage de critères doit correspondre aux mêmes lignes. | Dans `Q1_Demo`, cliquer sur `L25` pour afficher `=NB.SI.ENS(D2:D19;">4000";F2:F19;">25%")`. Le résultat attendu est 3. |
| 02:55 | Question 4, somme des salaires | Pour additionner les salaires supérieurs à quatre mille, on utilise SOMME.SI. La première plage sert à tester la condition ; la somme est calculée sur les valeurs qui répondent à ce critère. Si la plage à additionner est la même que la plage testée, le troisième argument peut être omis. | Dans `Q1_Demo`, cliquer sur `L26` pour afficher `=SOMME.SI(D2:D19;">4000")`. Le résultat attendu est 48 654. |
| 03:25 | Question 5, objectifs supérieurs à 33 % | Avec plusieurs critères, la fonction devient SOMME.SI.ENS. Elle commence par la plage à additionner, puis reçoit les plages et les critères à respecter. Ici, l'énoncé demande deux conditions simultanées : le salaire doit dépasser quatre mille dollars et l'objectif doit dépasser trente-trois pour cent. Nous utilisons donc deux plages de critères. Attention : la formule présente dans le classeur de correction semble ne tester que l'objectif. Nous suivons ici le texte de la question et signalons cette divergence. | Dans `Q1_Demo`, cliquer sur `L27` pour afficher `=SOMME.SI.ENS(D2:D19;D2:D19;">4000";H2:H19;">33%")`. Le résultat attendu est 6 066. |
| 03:55 | Questions 6 et 7 | Pour calculer une moyenne avec une condition, on utilise MOYENNE.SI. La question 6 demande la moyenne des salaires inférieurs ou égaux à quatre mille. La question 7 ajoute deux conditions à la moyenne : le salaire doit être inférieur ou égal à quatre mille dollars et l'âge doit être inférieur à vingt-deux ans. Pour appliquer ces deux conditions simultanément, utilisez MOYENNE.SI.ENS. | Dans `Q1_Demo`, cliquer sur `L28` puis `L29` pour afficher les formules `=MOYENNE.SI(D2:D19;"<=4000")` et `=MOYENNE.SI.ENS(D2:D19;D2:D19;"<=4000";B2:B19;"<22")`. Les résultats attendus sont 2 770,90 et 2 897. |
| 04:35 | Questions 8 et 9 | Les fonctions MAX.SI.ENS et MIN.SI.ENS permettent de trouver un maximum ou un minimum en respectant plusieurs critères. La question 8 cherche le maximum de Pay pour les personnes de plus de trente-trois ans dont l'objectif dépasse vingt-cinq pour cent. La question 9 cherche le minimum de Goals parmi les personnes de la classe Upper Class âgées de moins de trente-trois ans. | Dans `Q1_Demo`, cliquer sur `L30` puis `L31` pour afficher les formules `=MAX.SI.ENS(G2:G19;B2:B19;">33";H2:H19;">25%")` et `=MIN.SI.ENS(H2:H19;E2:E19;"Upper Class";B2:B19;"<33")`. Les résultats attendus sont 4 532,88 et 17 %. Les colonnes utilisées sont Pay (G), Ages (B), Goals (H) et Classes (E). |
| 05:15 | Schéma « Plage + critère » | Retenons la logique. NB.SI compte, SOMME.SI additionne, MOYENNE.SI calcule une moyenne. La version avec « .ENS » accepte plusieurs conditions. MAX.SI.ENS et MIN.SI.ENS recherchent respectivement une valeur maximale ou minimale après filtrage. | Afficher le récapitulatif. |
| 05:40 | Erreur fréquente : critère sans guillemets | Une erreur fréquente consiste à écrire un critère comme supérieur à quatre mille sans guillemets. Dans ces fonctions, les opérateurs associés à une valeur sont généralement fournis sous forme de texte, par exemple entre guillemets. Vérifiez aussi les pourcentages : vingt-cinq pour cent doit être comparé à une valeur de vingt-cinq pour cent, et non au nombre vingt-cinq. | Montrer une formule correcte et une formule incorrecte. |
| 06:05 | Transition vers question 10 | Vous savez maintenant compter et calculer sur des sous-ensembles de données. Dans la prochaine vidéo, nous allons créer des listes automatiques, effectuer une recherche et tester les cellules vides ou les valeurs absolues. | Afficher Q10 à Q13. |

---

# VIDÉO 2 — Listes automatiques, recherche, cellules vides et valeurs absolues
**Questions :** 10 à 13  
**Durée estimée :** 4 à 5 min

| TC | À l'écran | Texte prononcé | Action Excel |
|---|---|---|---|
| 00:00 | Q1, question 10 | Dans cette vidéo, nous allons découvrir quatre outils pratiques : générer une liste automatiquement, retrouver un salaire à partir d'un nom, vérifier si une cellule est vide et calculer une valeur absolue. | Afficher les questions 10 à 13. |
| 00:20 | Liste des noms de la colonne Clients | Une liste automatique peut être obtenue avec une fonction dynamique comme UNIQUE dans les versions récentes d'Excel. Elle renvoie les valeurs distinctes d'une plage et peut se déployer automatiquement dans les cellules voisines. Cette zone de résultat s'appelle une plage déversée. | Montrer `=UNIQUE(A2:A19)` dans une zone libre si la version le permet. |
| 00:55 | Recherche d'un salarié et de son salaire | La question suivante demande d'afficher automatiquement le salaire correspondant à un salarié. Avec RECHERCHEV, on indique la valeur recherchée, le tableau qui contient le nom et le salaire, le numéro de la colonne à renvoyer, puis FAUX pour exiger une correspondance exacte. Le nom recherché doit se trouver dans la première colonne de la zone de recherche. | Montrer un petit tableau avec nom et salaire, puis la structure de RECHERCHEV. |
| 01:35 | Formule mise en évidence | La structure générale est : égal RECHERCHEV, parenthèse, valeur recherchée, point-virgule, matrice, point-virgule, numéro de colonne, point-virgule, FAUX. Il faut adapter la matrice et le numéro de colonne à l'emplacement réel des données. Si le nom n'existe pas, Excel peut renvoyer une erreur de recherche. | Décomposer les quatre arguments à l'écran. |
| 02:05 | Question 12, cellule vide | Pour savoir si une cellule est vide, on peut utiliser ESTVIDE. La fonction renvoie VRAI si la cellule ne contient rien, et FAUX si elle contient une valeur ou une formule. Attention : une cellule qui affiche une chaîne vide produite par une formule n'est pas nécessairement considérée comme vide par ESTVIDE. | Dans la feuille `SOL` du classeur de correction, la correction teste `F25` avec `=ESTVIDE(F25)`. Pour filmer clairement, placer cette formule dans une cellule libre, puis comparer le résultat avec une cellule réellement vide et une cellule contenant une formule qui renvoie `""`. |
| 02:40 | Question 13, nombres positifs et négatifs | La valeur absolue mesure la distance à zéro : elle est toujours positive ou nulle. La fonction ABS transforme moins huit en huit, et moins quarante en quarante. Elle est utile lorsqu'on veut comparer une grandeur sans tenir compte de son signe. | Montrer `=ABS(-8)` puis `=ABS(-40)`. |
| 03:10 | Récapitulatif des quatre fonctions | À retenir : UNIQUE produit une liste sans doublons, RECHERCHEV récupère une information dans un tableau, ESTVIDE teste le contenu d'une cellule, et ABS renvoie la valeur absolue d'un nombre. | Afficher les quatre noms. |
| 03:35 | Transition vers S2 | Nous allons maintenant étudier des séries de salaires sur plusieurs années, puis construire des graphiques et des synthèses. | Ouvrir la feuille S2. |

---

# VIDÉO 3 — Évolution des salaires et graphique dynamique
**Questions :** 14 et 15  
**Durée estimée :** 4 à 5 min

| TC | À l'écran | Texte prononcé | Action Excel |
|---|---|---|---|
| 00:00 | Feuille S2, tableau des métiers et années | La feuille S2 présente plusieurs métiers en lignes et les années en colonnes. Chaque cellule contient le salaire associé à un métier et à une année. L'objectif est de préparer une liste des enseignants avec l'évolution de leur salaire, puis de représenter cette évolution dans un graphique dynamique. | Montrer les années B1:Z1 et les salaires de Teacher en B2:Z2. |
| 00:25 | Ligne Teacher sur plusieurs années | Pour extraire l'évolution du salaire des enseignants, repérez d'abord la ligne Teacher, puis les colonnes correspondant aux années. Il faut conserver l'association entre chaque année et sa valeur : si l'on copie uniquement les salaires, le graphique ne saura plus à quelle année correspond chaque point. | Sélectionner la ligne Teacher et les en-têtes d'années. |
| 00:55 | Tableau de synthèse | Créez une petite zone de synthèse avec deux colonnes : Année et Salaire des enseignants. Reprenez les années de `S2!B1:Z1` et associez les salaires de `S2!B2:Z2` dans le même ordre. Cette zone intermédiaire simplifie la création et la mise à jour du graphique. | Construire ou montrer la zone de synthèse. |
| 01:30 | Insertion d'un graphique en courbes | Sélectionnez les deux colonnes, puis ouvrez Insertion et choisissez un graphique en courbes. Les années doivent être sur l'axe horizontal et les salaires sur l'axe vertical. Ajoutez un titre explicite, par exemple « Évolution du salaire des enseignants ». | Insérer le graphique et modifier le titre. |
| 02:05 | Graphique et tableau sélectionnés | Un graphique dynamique est lié à ses données sources. Lorsque les valeurs de la plage changent, le graphique se met à jour. Pour que cela fonctionne correctement, il faut que la série du graphique pointe vers la bonne plage et que les années soient reconnues comme étiquettes de l'axe horizontal. | Montrer Sélectionner des données. |
| 02:40 | Erreur fréquente : axes inversés | Si les années apparaissent comme plusieurs séries ou si le graphique affiche les métiers sur l'axe horizontal, vérifiez l'orientation des données et la commande Intervertir ligne et colonne. Un graphique correct doit permettre de lire immédiatement comment le salaire évolue au fil du temps. | Montrer la commande si nécessaire. |
| 03:10 | Résultat final | Nous avons transformé une ligne de données en une représentation lisible. Le tableau donne les valeurs exactes ; le graphique, lui, fait ressortir la tendance. Ces deux vues sont complémentaires. | Montrer le tableau et le graphique. |
| 03:35 | Transition vers la table Universities | Dans la prochaine vidéo, nous allons découvrir les sous-totaux et les tableaux croisés dynamiques, deux outils utiles pour résumer beaucoup de données. | Ouvrir S2. La table Universities se trouve plus bas dans la même feuille ; ne pas chercher une feuille S4. |

---

# VIDÉO 4 — Sous-totaux, tableau de bord et tableau croisé dynamique
**Questions :** 16 à 18  
**Durée estimée :** 6 min

| TC | À l'écran | Texte prononcé | Action Excel |
|---|---|---|---|
| 00:00 | Feuille S2, table Universities (à partir de la ligne 33) | La table Universities de la feuille S2 contient des indicateurs, des districts, des objectifs et des résultats. Lorsqu'un tableau comporte plusieurs catégories, les sous-totaux et les tableaux croisés dynamiques permettent de résumer les informations sans additionner manuellement chaque ligne. | Montrer les colonnes Indicators, Districts, Goals et Results dans S2 (en-têtes ligne 34). |
| 00:30 | Regrouper les lignes par indicateur | Avant d'utiliser les sous-totaux classiques, les données doivent être triées selon le champ qui définit les groupes. Ici, on regroupe les lignes par indicateur : Enrollment, Graduation, Retention ou Faculty. Le tri permet à Excel de repérer où chaque groupe commence et se termine. | Dans S2, sélectionner toute la table Universities (A34:D50), puis trier par Indicators en conservant toutes les colonnes ensemble. |
| 01:00 | Données triées | La commande Sous-total se trouve dans l'onglet Données, selon la version d'Excel. On choisit le champ de regroupement, la fonction à appliquer et les colonnes à résumer. Par exemple, on peut calculer la somme des objectifs et la somme des résultats pour chaque indicateur. | Montrer la boîte de dialogue Sous-total. |
| 01:35 | Plan avec niveaux 1, 2 et 3 | Excel ajoute des lignes de sous-total et affiche des niveaux de plan. Le niveau le plus détaillé montre toutes les lignes ; un niveau intermédiaire affiche les sous-totaux ; le niveau le plus synthétique permet de comparer les totaux des groupes. Les sous-totaux ne remplacent pas les données : ils ajoutent une lecture résumée. | Cliquer sur les niveaux de plan. |
| 02:10 | Graphique de tableau de bord | Pour créer un tableau de bord simple, choisissez les indicateurs importants et représentez les totaux dans un graphique. Un graphique en colonnes permet, par exemple, de comparer les objectifs aux résultats. Le titre, la légende et les axes doivent être explicites pour éviter les interprétations ambiguës. | Montrer une zone de synthèse et un graphique. |
| 02:45 | Insertion d'un tableau croisé dynamique | Un tableau croisé dynamique, ou TCD, est un outil de synthèse interactif. Sélectionnez la plage de données, puis choisissez Insertion, Tableau croisé dynamique. Excel demande où placer le résultat. Choisissez une nouvelle feuille si vous souhaitez séparer la synthèse des données sources. | Créer un TCD à partir de S2!A34:D50 (en-têtes ligne 34, données lignes 35 à 50). |
| 03:20 | Liste des champs du TCD | Dans la liste des champs, faites glisser une catégorie dans Lignes, une autre dans Colonnes si nécessaire, et une valeur numérique dans Valeurs. Excel choisit souvent Somme ou Nombre selon le type de données. Vérifiez toujours le calcul proposé : un champ de résultats doit généralement être résumé par une somme ou une moyenne, pas par un comptage inattendu. | Montrer le volet Champs de tableau croisé dynamique. |
| 04:00 | TCD par indicateur et district | Par exemple, placez Indicators dans Lignes, Districts dans Colonnes et Results dans Valeurs. Vous obtenez une synthèse qui compare les résultats par indicateur et par district. Les champs peuvent être déplacés pour répondre à une autre question sans modifier les données sources. | Organiser le TCD. |
| 04:35 | Graphique croisé dynamique | Un graphique croisé dynamique représente les données du TCD. Sélectionnez le TCD, puis insérez un graphique croisé dynamique. Les filtres du TCD et les champs associés peuvent piloter le graphique. C'est pratique pour explorer les résultats selon différents indicateurs ou districts. | Insérer le graphique croisé dynamique. |
| 05:05 | Bouton Actualiser | Si les données sources sont modifiées ou complétées, un TCD ne se met pas toujours à jour immédiatement. Utilisez Actualiser. Si de nouvelles lignes ont été ajoutées en dehors de la plage source, il peut être nécessaire de modifier la source du TCD. | Montrer Actualiser et la source de données. |
| 05:30 | Récapitulatif | Retenons la différence : les sous-totaux ajoutent des lignes de synthèse dans une liste triée ; le tableau croisé dynamique construit une synthèse flexible ; le graphique croisé dynamique visualise cette synthèse. | Afficher les trois outils. |

---

# VIDÉO 5 — Importer et gérer un fichier CSV
**Question :** 19  
**Durée estimée :** 4 min

| TC | À l'écran | Texte prononcé | Action Excel |
|---|---|---|---|
| 00:00 | Fichiers CSV du dossier 00-data | Un fichier CSV est un fichier texte qui stocke des données sous forme de lignes et de colonnes. Les colonnes sont séparées par un caractère, souvent une virgule ou un point-virgule. Le CSV ne conserve pas la mise en forme avancée d'un classeur Excel. | Montrer les fichiers CSV du dossier. |
| 00:25 | Aperçu de 02-data.csv dans un éditeur texte | Avant d'importer un CSV, regardez sa première ligne. Elle contient souvent les noms des champs, comme l'identifiant de l'école, son nom, l'année, la ville ou le statut. Il faut aussi vérifier le séparateur utilisé, car une mauvaise détection peut placer toute la ligne dans une seule colonne. | Ouvrir un aperçu du CSV. |
| 00:55 | Excel, onglet Données | Dans Excel, la méthode recommandée consiste à utiliser Données, puis À partir d'un fichier texte ou CSV. Sélectionnez le fichier et contrôlez l'aperçu avant de charger les données. Choisissez le bon séparateur et l'encodage afin de préserver les accents et les caractères particuliers. | Dans le dossier fourni `02-part-02`, sélectionner le fichier `02-data.csv` (ne pas le chercher dans le classeur Excel). |
| 01:35 | Aperçu des colonnes séparées | Vérifiez les colonnes une à une. Les codes d'établissement peuvent contenir des zéros au début : si Excel les convertit en nombres, ces zéros risquent de disparaître. Pour un identifiant, il est souvent préférable de conserver le type Texte. Les codes postaux peuvent également nécessiter une attention particulière. | Contrôler les types de colonnes dans l'importation. |
| 02:10 | Bouton Charger | Une fois les paramètres vérifiés, cliquez sur Charger. Les données apparaissent dans une feuille Excel. Si vous utilisez Power Query, l'importation peut être actualisée lorsque le fichier source change, selon la façon dont la connexion a été créée. | Charger les données. |
| 02:40 | Enregistrement au format Excel | Si vous souhaitez ajouter des formules, des graphiques ou de la mise en forme, enregistrez une copie au format classeur Excel, c'est-à-dire XLSX. Gardez le CSV original si vous devez conserver la source brute. N'enregistrez pas par-dessus le fichier d'origine sans raison. | Enregistrer sous XLSX. |
| 03:10 | Récapitulatif | Les étapes essentielles sont donc : inspecter le CSV, importer avec le bon séparateur, vérifier l'encodage et les types de données, puis charger et enregistrer une copie Excel si nécessaire. | Afficher le récapitulatif. |

---

# VIDÉO 6 — Tableaux structurés et références de cellules
**Questions :** 20 et 21  
**Durée estimée :** 5 à 6 min

| TC | À l'écran | Texte prononcé | Action Excel |
|---|---|---|---|
| 00:00 | Feuille S3, tableau de produits et prix | Dans cette vidéo, nous allons découvrir deux notions qui rendent les classeurs plus fiables : les tableaux structurés et les références relatives ou absolues. Nous allons utiliser un exemple de produits et de prix, puis convertir des prix avec différents taux. | Ouvrir la feuille S3 pour les prix, puis montrer la zone correspondante dans SOL pour le tableau structuré. |
| 00:25 | Tableau de données | Un tableau structuré se crée en sélectionnant les données, puis en choisissant Insertion, Tableau, ou en utilisant le raccourci Contrôle T. Vérifiez que l'option indiquant que le tableau comporte des en-têtes est cochée si la première ligne contient les titres. | Créer ou montrer le tableau structuré. |
| 00:55 | Onglet Création de tableau | Donnez au tableau un nom explicite, par exemple TableauPrix. Les tableaux structurés utilisent les noms des colonnes dans les formules. Au lieu de référencer une cellule par son adresse, on peut utiliser le nom du tableau et celui de la colonne. Cela rend les formules plus lisibles et facilite l'extension lorsque de nouvelles lignes sont ajoutées. | Renommer le tableau et montrer une référence structurée. |
| 01:30 | Colonnes Price 1 à Price 4 | Dans l'exemple, on peut calculer une moyenne, une somme, un minimum et un maximum pour chaque produit à partir des quatre prix. Dans un tableau structuré, une formule saisie dans une colonne calculée se propage généralement à toutes les lignes de cette colonne. | Montrer les colonnes calculées. |
| 02:00 | Ligne Total | La ligne des totaux permet de résumer les colonnes numériques. Selon la configuration, on peut y choisir Somme, Moyenne, Minimum ou Maximum. La fonction SOUS.TOTAL est utile lorsque le tableau est filtré, car elle peut ignorer les lignes masquées par un filtre selon le numéro de fonction utilisé. | Activer la ligne des totaux et afficher les choix. |
| 02:35 | Tableau de prix US, UK, EU et JP | Passons aux références de cellules. Une référence relative, comme C3, change lorsqu'on copie la formule. Une référence absolue, comme C dollar 3, garde la colonne et la ligne fixes. Une référence mixte, comme C dollar 3 ou dollar C3, ne bloque qu'une partie de la référence. | Montrer les références dans une formule. |
| 03:05 | Formule de conversion | Ici, le prix de départ est dans la colonne C et les taux de conversion sont sur une ligne distincte. Pour recopier la formule vers le bas tout en gardant la cellule du taux sur la même ligne, on bloque la ligne du taux. Par exemple, C3 multiplié par D dollar 16 garde la ligne 16 fixe, mais permet à C3 de devenir C4, C5, puis C6. | Montrer `=C3*D$16`, puis recopier vers le bas. |
| 03:45 | Recopie vers la droite | Si l'on recopie aussi la formule vers la droite, la colonne du taux doit pouvoir passer de D à E puis à F. C'est pourquoi la référence D dollar 16 est mixte : la ligne reste fixe, mais la colonne évolue. À l'inverse, dollar C3 fixe la colonne C tout en laissant le numéro de ligne évoluer. | Montrer la recopie vers la droite. |
| 04:20 | Erreur fréquente | Une erreur classique consiste à bloquer toute la référence alors qu'on souhaite laisser une partie changer, ou à ne rien bloquer alors qu'un taux doit rester fixe. Avant de recopier une formule, demandez-vous : quelle cellule doit suivre le déplacement, et quelle cellule doit rester ancrée ? | Comparer C3, `$C$3`, `C$3` et `$C3`. |
| 04:50 | Récapitulatif | Les tableaux structurés rendent les données extensibles et les formules lisibles. Les références relatives et absolues contrôlent, elles, le comportement des formules lors de la recopie. Ces deux outils deviennent particulièrement utiles dans les classeurs contenant de nombreuses lignes et colonnes. | Afficher les notions. |

---

# VIDÉO 7 — SI imbriquées : attribuer une mention
**Question :** 22  
**Durée estimée :** 4 à 5 min

| TC | À l'écran | Texte prononcé | Action Excel |
|---|---|---|---|
| 00:00 | Feuille S5, tableau Students | Nous allons maintenant attribuer une mention à des étudiants à partir de leur note finale. Les notes sont calculées à partir de plusieurs scores, puis une catégorie est attribuée selon des seuils. C'est un cas classique pour la fonction SI. | Ouvrir la feuille SOL et repérer la zone des étudiants autour des lignes 240 à 266. |
| 00:25 | Colonnes Score 1 à Score 4 | La première étape consiste à calculer la moyenne des quatre notes. La fonction MOYENNE reçoit les cellules contenant les scores. Pour la première ligne, la formule prend les quatre cellules de score de cette ligne. On recopie ensuite la formule vers le bas pour calculer la moyenne de chaque étudiant. | Montrer `=MOYENNE(C240:F240)` ou la ligne correspondante dans le classeur. |
| 01:00 | Seuils Excellent, Good, Bad | Nous avons trois catégories : Excellent, Good et Bad, avec des seuils indiqués dans le tableau. Il est préférable de faire référence aux cellules qui contiennent ces seuils plutôt que de les retaper dans chaque formule. Ainsi, si un seuil change, les résultats se recalculent automatiquement. | Montrer les seuils et leurs cellules. |
| 01:35 | Structure d'un SI | La fonction SI vérifie une condition. Si elle est vraie, elle renvoie un résultat ; si elle est fausse, elle en renvoie un autre. Pour trois catégories, on peut placer un deuxième SI dans le résultat « si faux » du premier. On appelle cela un SI imbriqué. | Afficher `=SI(condition;résultat_si_vrai;résultat_si_faux)`. |
| 02:10 | Formule imbriquée en couleurs | La logique est la suivante : si la moyenne atteint le seuil Excellent, afficher Excellent. Sinon, tester si elle dépasse le seuil Good. Si oui, afficher Good ; sinon, afficher Bad. L'ordre des tests compte : on vérifie d'abord le seuil le plus élevé. | Décomposer la formule par blocs. |
| 02:45 | Résultats sur plusieurs étudiants | Les textes affichés doivent être entre guillemets lorsqu'ils sont écrits directement dans la formule. Les références aux seuils, elles, pointent vers les cellules concernées. Vérifiez aussi si le seuil doit être strictement supérieur ou supérieur ou égal : cette différence change le résultat pour une note exactement égale au seuil. | Montrer les comparateurs `>` et `>=`. |
| 03:20 | Recopie et vérification | Une fois la formule correcte sur la première ligne, recopiez-la sur les autres étudiants. Contrôlez quelques cas : une moyenne au-dessus du premier seuil, une moyenne entre les deux seuils, puis une moyenne sous le deuxième seuil. Ces trois cas permettent de vérifier la logique. | Vérifier trois lignes. |
| 03:50 | Récapitulatif | Un SI imbriqué permet de choisir parmi plusieurs résultats. Pour rester lisible, utilisez des seuils bien identifiés, testez d'abord la catégorie la plus élevée et vérifiez soigneusement les opérateurs de comparaison. | Afficher le schéma logique. |

---

# VIDÉO 8 — Fonctions logiques ET, OU et NON
**Question :** 23  
**Durée estimée :** 5 min

| TC | À l'écran | Texte prononcé | Action Excel |
|---|---|---|---|
| 00:00 | Tableau de critères : âge, pays, revenus | Les fonctions logiques permettent de combiner plusieurs conditions. Nous allons voir ET, OU et NON, puis les utiliser avec SI pour obtenir un résultat compréhensible, par exemple « Sélectionné » ou « Non sélectionné ». | Afficher les données d'exemple. |
| 00:25 | Schéma ET | ET renvoie VRAI uniquement si toutes les conditions sont vraies. Si une seule condition est fausse, ET renvoie FAUX. On l'utilise lorsque toutes les exigences doivent être respectées en même temps. | Afficher deux ou trois conditions reliées par ET. |
| 00:55 | Schéma OU | OU renvoie VRAI dès qu'au moins une des conditions est vraie. Dans notre exemple, une personne est sélectionnée si son âge dépasse quarante-quatre ans, ou si son pays est les États-Unis, ou si ses revenus dépassent deux cent vingt mille. Une seule de ces conditions suffit. | Montrer les trois conditions. |
| 01:35 | Formule OU dans une cellule | On peut d'abord afficher directement le résultat logique de OU. La formule renvoie VRAI ou FAUX. Ensuite, on peut placer OU à l'intérieur de SI pour remplacer ces valeurs par des messages plus clairs. | Montrer `=OU(C275>44;D275="USA";E275>220000)` en adaptant les cellules. |
| 02:10 | Formule SI avec OU | La structure est : SI, puis OU avec les conditions, puis le texte à afficher si la condition est vraie, et enfin celui à afficher si elle est fausse. Les textes écrits directement doivent être entourés de guillemets. | Montrer une formule SI avec OU. |
| 02:45 | NON | NON inverse une valeur logique : VRAI devient FAUX et FAUX devient VRAI. On l'utilise quand on veut tester l'inverse d'une condition. Par exemple, NON d'une condition indiquant qu'une cellule est vide permet de vérifier qu'elle ne l'est pas. | Montrer `=NON(ESTVIDE(A1))` comme exemple pédagogique. |
| 03:15 | Exemple ET avec client Oui | On peut aussi combiner les fonctions. Dans le tableau suivant, il faut satisfaire une condition composée avec OU, mais également être client. On utilise OU pour vérifier les critères d'âge, de pays ou de revenus, puis ET pour exiger en plus que la colonne Client contienne Oui. | Montrer la formule combinant ET et OU. |
| 03:55 | Décomposition de la formule | Lisons la formule de l'intérieur vers l'extérieur. D'abord, OU vérifie si au moins un critère est vrai. Ensuite, ET vérifie que ce résultat est vrai et que la personne est bien cliente. Enfin, SI traduit le résultat en un message lisible. | Colorer les parties OU, ET et SI. |
| 04:30 | Tableau de résultats | Pour contrôler la formule, testez une ligne qui satisfait le critère de pays, une ligne qui satisfait le critère de revenus et une ligne qui ne satisfait aucun critère. Dans le deuxième tableau, vérifiez également la colonne Client : même si OU est vrai, une personne qui n'est pas cliente ne doit pas être sélectionnée. | Vérifier plusieurs cas. |
| 04:55 | Récapitulatif | À retenir : ET signifie « toutes les conditions », OU signifie « au moins une condition », et NON inverse le résultat logique. Associées à SI, ces fonctions permettent de transformer une règle métier en décision automatique. | Afficher le récapitulatif. |

---

# VIDÉO 9 — TRANSPOSE, RECHERCHEH et RECHERCHEX
**Question :** 24  
**Durée estimée :** 5 à 6 min

| TC | À l'écran | Texte prononcé | Action Excel |
|---|---|---|---|
| 00:00 | Zone de recherche horizontale | Jusqu'ici, nous avons surtout recherché des valeurs dans des tableaux organisés verticalement. Dans cette vidéo, nous allons transposer un tableau, utiliser RECHERCHEH pour une recherche horizontale et découvrir RECHERCHEX, une fonction plus flexible. | Montrer l'exemple des produits et des prix. |
| 00:25 | Tableau vertical Produit / Prix | TRANSPOSE permet de changer l'orientation d'une plage : les lignes deviennent des colonnes et les colonnes deviennent des lignes. Dans les versions récentes d'Excel, la formule peut se déployer automatiquement dans la zone de destination. | Montrer un tableau vertical et le résultat horizontal avec `=TRANSPOSE(plage)`. |
| 01:05 | Tableau horizontal | Après transposition, les produits sont placés sur la première ligne et les prix sur la deuxième. Cette disposition permet de rechercher une valeur dans la première ligne et de renvoyer la valeur correspondante située plus bas. | Pointer la première ligne et la deuxième ligne. |
| 01:35 | RECHERCHEH | RECHERCHEH cherche une valeur dans la première ligne d'une matrice. On indique la valeur recherchée, la matrice, le numéro de ligne à renvoyer et FAUX pour une correspondance exacte. Dans notre exemple, nous cherchons Orange dans la première ligne et renvoyons le prix de la deuxième ligne. | Dans le support de démonstration `SOL`, cellule H315, utiliser `=RECHERCHEH(H312;B311:F312;2;FAUX)`. Le résultat attendu pour Orange est 5. |
| 02:15 | Limites de RECHERCHEV et RECHERCHEH | RECHERCHEV travaille verticalement : la valeur cherchée est dans la première colonne. RECHERCHEH travaille horizontalement : la valeur cherchée est dans la première ligne. Ces fonctions exigent donc que le tableau soit organisé dans le bon sens. | Afficher les deux orientations. |
| 02:45 | Tableau produit, code et prix | RECHERCHEX offre davantage de souplesse. On lui donne la valeur recherchée, la plage où la trouver, puis la plage qui contient le résultat à renvoyer. Les deux plages peuvent être séparées : la colonne du résultat n'a pas besoin d'être à droite de la colonne recherchée. | Montrer le tableau de produits, codes et prix. |
| 03:20 | Formule RECHERCHEX | Pour trouver le prix du produit Kiwi, on recherche Kiwi dans la colonne Produit et on renvoie la valeur de la colonne Prix. La formule est plus simple à lire parce qu'on désigne directement la plage de recherche et la plage de résultat. | Dans le support de démonstration `SOL`, cellule F322, utiliser `=RECHERCHEX(F319;B320:B323;D320:D323)`. Le résultat attendu pour Kiwi est 2. |
| 03:55 | Résultat et cas absent | RECHERCHEX peut également définir le message à afficher si aucune correspondance n'est trouvée. C'est utile pour éviter une erreur peu explicite. Attention toutefois : cette fonction n'est pas disponible dans certaines anciennes versions d'Excel. | Montrer l'argument facultatif si_non_trouvé. |
| 04:25 | Comparaison des trois fonctions | Retenons : TRANSPOSE change l'orientation d'une plage ; RECHERCHEH recherche dans la première ligne ; RECHERCHEX recherche dans une plage et renvoie le résultat depuis une autre plage. Si votre version d'Excel le permet, RECHERCHEX est souvent plus flexible. | Afficher le tableau comparatif. |
| 04:55 | Transition vers INDEX et EQUIV | Il nous reste une dernière méthode de recherche. INDEX et EQUIV peuvent travailler ensemble pour retrouver une valeur à partir de sa position. C'est le sujet de la dernière vidéo. | Afficher Q25. |

---

# VIDÉO 10 — INDEX et EQUIV : retrouver une valeur par sa position
**Question :** 25  
**Durée estimée :** 4 à 5 min

| TC | À l'écran | Texte prononcé | Action Excel |
|---|---|---|---|
| 00:00 | Tableau des étudiants et des notes | Pour terminer, nous allons combiner INDEX et EQUIV. Cette combinaison permet de rechercher une valeur sans imposer la même organisation que RECHERCHEV. Nous allons d'abord comprendre chaque fonction séparément, puis les associer. | Afficher le tableau des étudiants et des notes. |
| 00:25 | Fonction EQUIV | EQUIV recherche une valeur dans une plage et renvoie sa position. Elle ne renvoie pas directement la valeur trouvée, mais son rang dans la plage. Par exemple, si P4 est le quatrième élément de la liste P1, P2, P3, P4, EQUIV renvoie quatre. | Montrer la liste P1 à P4 et la position de P4. |
| 01:00 | Fonction INDEX | INDEX fait l'opération complémentaire : à partir d'une plage et d'une position, elle renvoie la valeur située à cet emplacement. Dans un tableau à deux dimensions, on peut indiquer le numéro de ligne et le numéro de colonne. | Montrer la matrice des notes. |
| 01:35 | Exemple de note d'anglais de James | Dans le tableau des étudiants, les étudiants sont sur les lignes et les matières sur les colonnes. Pour récupérer la note d'anglais de James, il faut identifier la ligne de James et la colonne de l'anglais. Dans l'exemple de correction, les positions sont données directement à INDEX ; on peut ensuite les rendre dynamiques avec EQUIV. | Montrer la ligne James et la colonne Anglais. |
| 02:10 | INDEX + EQUIV | La combinaison fonctionne en deux temps. EQUIV trouve la position de l'étudiant dans la colonne des noms. Une deuxième fonction EQUIV peut trouver la position de la matière dans les en-têtes. INDEX utilise ensuite ces deux positions pour renvoyer la note située à leur intersection. | Afficher une formule INDEX avec deux EQUIV, adaptée à la plage réelle. |
| 02:50 | Tableau Produit, Prix et Référence | EQUIV peut aussi retrouver la position d'un produit, d'un prix ou d'une référence dans une liste. Le troisième argument, zéro dans la syntaxe classique, demande une correspondance exacte. Sans cette précision, la fonction peut appliquer un mode de recherche différent. | Montrer les trois exemples de recherche de la correction. |
| 03:25 | Erreurs fréquentes | Vérifiez que la plage utilisée par EQUIV correspond bien à la liste où se trouve la valeur recherchée. Pour INDEX, vérifiez que les positions renvoyées correspondent aux lignes et colonnes de la matrice choisie. Une erreur de décalage d'une ligne ou d'une colonne suffit à renvoyer une mauvaise donnée. | Montrer une formule puis les plages surlignées. |
| 03:55 | Récapitulatif général des 25 questions | Nous avons terminé les vingt-cinq questions de cet exercice. Vous avez appris à compter et calculer sous conditions, à rechercher des valeurs, à travailler avec les références, à utiliser des fonctions logiques, à gérer des fichiers CSV et à construire des synthèses et des graphiques. | Afficher les grands thèmes. |
| 04:20 | Écran final « Comprendre, tester, vérifier » | Pour progresser, ne mémorisez pas uniquement les formules. Reprenez chaque exemple, modifiez un critère et observez comment le résultat change. C'est en testant les formules sur plusieurs cas que vous apprendrez à les utiliser de manière autonome. Merci d'avoir suivi cette série, et à bientôt pour un nouvel exercice Excel. | Afficher l'écran final. |

---

## Notes de vérification avant génération des voix

1. Le fichier de départ contient des libellés et des formules partiellement en anglais. Adapter les noms de fonctions à Excel français si le poste cible utilise Microsoft 365 en français.
2. La feuille Q1 contient 18 personnes en lignes 2 à 19, mais plusieurs colonnes y sont vides. Le fichier `Exercice2_demo_Q1_pret_a_filmer.xlsx` a été créé séparément avec les données complètes et les dix formules de démonstration préremplies.
3. Pour la question 5, le texte de l'énoncé demande la somme des salaires supérieurs à 4 000 dollars **et** des objectifs supérieurs à 33 %. La formule doit donc contenir les deux critères conformément au texte de l’énoncé : `=SOMME.SI.ENS(D2:D19;D2:D19;">4000";H2:H19;">33%")`. La correction fournie semble n'utiliser que le critère Goals dans sa formule, il faut donc vérifier et expliquer cette divergence au lieu de la masquer.
4. Pour la question 7, la formule doit respecter les deux conditions de l'énoncé : salaires `<=4000` et âges `<22`. Formule : `=MOYENNE.SI.ENS(D2:D19;D2:D19;"<=4000";B2:B19;"<22")`.
5. Les questions 10 à 13 et 20 à 25 contiennent des exemples d'apprentissage. Vérifier les noms définis et les cellules d'exemple dans `02-sol.xlsx` avant d'afficher une formule définitive à l'écran.
6. Pour les sous-totaux et TCD, partir de la table Universities dans `S2!A34:D50`. Effectuer les manipulations dans une copie du classeur pour préserver le fichier d'origine.
