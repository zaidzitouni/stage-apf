# Rapport de qualité des données — Fichier "MAROCAINS PAR SITE"

- **Fichier source** : `data/raw/stage_data_2.pdf`
- **Période couverte** : 01/12/2019 au 31/12/2019
- **Script d'extraction** : `extract_marocains.py`
- **Lignes extraites** : 31 (correspond au nombre de postes-frontières du tableau original)

## Méthodologie de validation

Chaque ligne est vérifiée par deux règles arithmétiques :
1. `total_entree = femmes_entree + hommes_entree + mineurs_entree` (et l'équivalent pour la sortie)
2. `totaux = total_entree + total_sortie`

La somme des `totaux` de toutes les lignes est ensuite comparée à la ligne `TOTAUX` officielle imprimée en bas du tableau du PDF (532463), qui sert de référence indépendante.

## Anomalies détectées

3 lignes sur 31 ne respectent pas la règle 2 (le `TOTAUX` imprimé sur le PDF ne correspond pas à `total_entree + total_sortie`) :

| Poste-frontière | Total entrée | Total sortie | TOTAUX imprimé (PDF) | TOTAUX recalculé | Écart |
|---|---|---|---|---|---|
| CPM MARINA KABILA | 17 | 18 | 36 | 35 | −1 |
| CSPA CHARIF AL IDRISSI AL HOCEIMA | 139 | 193 | 237 | 332 | +95 |
| CSPA DAKHLA | 101 | 105 | 147 | 206 | +59 |

**Somme des 3 écarts : 153**, soit exactement l'écart entre la somme de toutes les valeurs `TOTAUX` imprimées (532310) et le total officiel du PDF (532463).

## Analyse

Cette correspondance exacte indique que le grand total officiel du PDF (532463) a été calculé par le Ministère à partir de la logique `entrée + sortie`, et **non** à partir de la somme des valeurs individuelles imprimées dans la colonne `TOTAUX` de ces 3 lignes précises. Il s'agit donc très probablement d'une **erreur de saisie dans le document source**, sur ces 3 cases uniquement — pas d'un problème d'extraction : les valeurs `femmes/hommes/mineurs` de ces lignes sont cohérentes entre elles, seule la colonne `TOTAUX` de la ligne diverge.

## Traitement retenu

- La valeur `TOTAUX` telle qu'imprimée sur le PDF est **conservée telle quelle** en base (fidélité à la source, on ne réécrit jamais une donnée d'origine silencieusement).
- Une colonne `totaux_calcule` (valeur recalculée) et un indicateur `anomalie` (booléen) sont ajoutés à chaque ligne, permettant à tout consommateur de la base (rapport Power BI, requête SQL, interface en langage naturel) de repérer ces 3 cas et de choisir la valeur à utiliser en connaissance de cause.

## Recommandation

Signaler ces 3 lignes au service responsable de la publication des statistiques APF pour vérification/correction à la source.
