# Rapport de qualité des données — Fichier "MRE PAR SITE ENTREE"

- **Fichier source** : `data/raw/stage_data_3.pdf`
- **Période couverte** : 01/12/2019 au 31/12/2019
- **Script d'extraction** : `extract_mre.py`
- **Lignes extraites** : 31

## Correction automatique appliquée

La ligne **CSPA RABAT-SALE** contenait une cellule corrompue (`##30` au lieu d'un nombre), artefact classique d'un export Excel → PDF (colonne trop étroite). Reconstituée automatiquement à partir de la relation `total = femmes + hommes + mineurs` :

`hommes_marocain = 15852 (total) − 7208 (femmes) − 914 (mineurs) = 7730`

## Anomalies détectées (non corrigées automatiquement)

| Poste-frontière | TOTAUX imprimé | TOTAUX recalculé | Écart | Nature probable |
|---|---|---|---|---|
| CPM AL HOUC-EIMA | 1563 | 1562 | 1 | Coquille mineure sur le sous-total "marocain" (1094 imprimé vs 1093 calculé) |
| CSPA ESSA-OUIRA MOGADOR | 1354 | 1353 | 1 | Idem (456 imprimé vs 455 calculé) |
| PF BIR GUENDOUZ | 1790 | 1790 | 0 (mais sous-total incohérent) | Le sous-total "étranger" imprimé (422) ne correspond pas à femmes+hommes+mineurs (442), mais le TOTAUX final est resté cohérent avec la valeur correcte (442) — l'erreur ne s'est pas propagée |
| CSPA FES-SAISS | 48998 | 37498 | 11500 | Écart important, cause non identifiable avec certitude à partir des seules données disponibles |

Malgré ces anomalies, **la somme totale des `TOTAUX` (630187) correspond exactement au total officiel imprimé en bas du PDF** — contrairement au fichier MAROCAINS, ces coquilles s'annulent globalement ou n'affectent pas le total général.

## Traitement retenu

Comme pour le fichier MAROCAINS : les valeurs sources sont conservées telles quelles en base, avec une colonne `totaux_calcule` et un indicateur `anomalie` pour signalement — sans correction silencieuse, sauf pour la cellule `##30` où la correction est sans ambiguïté (un seul chiffre manquant, déductible avec certitude).

## Recommandation

Signaler ces 4 lignes, en particulier CSPA FES-SAISS (écart le plus important), au service responsable de la publication des statistiques APF.
