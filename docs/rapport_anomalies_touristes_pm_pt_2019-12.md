# Rapport de qualité des données — Fichier "TOURISTE PM PT ENTREE" (maritime/terrestre)

- **Fichier source** : `data/raw/stage_data_4.pdf`
- **Période couverte** : 01/12/2019 au 31/12/2019
- **Script d'extraction** : `extract_touristes.py`
- **Format** : matrice nationalité (133) × poste-frontière (19), transformée en format long

## Constat initial

Une anomalie a été détectée sur la ligne "GUINEENNE EQUATORIALE" : total imprimé = 14, somme calculée = 0.

## Cause identifiée

Le libellé de cette nationalité s'enroule sur 2 lignes dans le PDF ("GUINEENNE" / "EQUATORIALE"), et la fin du mot ("ORIALE") déborde dans la première cellule numérique, entraînant l'extraction de `'ORIALE 14'` au lieu de `'14'` — la valeur numérique était donc bien présente mais noyée dans du texte parasite.

## Correction appliquée

Ajout d'une règle de nettoyage générale : toute cellule numérique se terminant par une séquence de chiffres, précédée de texte parasite, est nettoyée pour ne garder que ces chiffres (`re.match(r"^\D*(\d+)$", texte)`). Cette règle est sans risque pour les libellés de nationalité (colonne 0), qui ne se terminent jamais par des chiffres.

## Résultat après correction

- **0 anomalie par nationalité** (133/133 lignes cohérentes)
- **0 anomalie par poste-frontière** (19/19 postes cohérents)
- **Total général exact** : 137375 = 137375

Ce fichier est entièrement validé, sans réserve.
