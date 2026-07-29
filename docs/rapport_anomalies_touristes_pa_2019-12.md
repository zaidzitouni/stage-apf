# Rapport de qualité des données — Fichier "TOURISTE PA ENTREE" (aéroports)

- **Fichier source** : `data/raw/stage_data_1.pdf`
- **Période couverte** : 01/12/2019 au 31/12/2019
- **Script d'extraction** : `extract_touristes.py`
- **Format** : matrice nationalité (185) × poste-frontière (18), transformée en format long

## Constat

Contrairement aux fichiers précédents, ce fichier présente des écarts **sur les 18 postes-frontières** entre la somme calculée à partir des lignes individuelles et le total officiel imprimé en bas du tableau — alors que le total général (765410 vs 765412) et 183 des 185 totaux par nationalité sont, eux, cohérents.

## Démarche d'investigation

Avant de conclure, 4 vérifications indépendantes ont été menées :

1. **Extraction automatique (pdfplumber, réglages par défaut)** — écarts constatés.
2. **Extraction positionnelle** (coordonnées x/y réelles des cellules détectées) — mêmes valeurs, mêmes positions.
3. **Grille de colonnes forcée manuellement** (bornes verticales imposées depuis l'en-tête) — mêmes valeurs.
4. **camelot-py** (bibliothèque indépendante, moteur Ghostscript + OpenCV, algorithme totalement différent de pdfplumber) — **résultat identique** sur les lignes vérifiées (ex. PORTUGAISE : `'', '312'` sur les 2 premières colonnes de postes, dans les 4 méthodes).
5. **Inspection visuelle** de la grille détectée superposée à l'image du PDF — confirme que les valeurs sont physiquement positionnées à l'endroit extrait.

## Conclusion

**Il ne s'agit pas d'un bug d'extraction.** Les 4 méthodes, dont 2 bibliothèques indépendantes, convergent vers les mêmes valeurs aux mêmes positions. Le tableau détaillé par nationalité est fidèlement extrait.

L'incohérence provient donc du **document source lui-même** : les totaux par poste-frontière imprimés en bas du tableau ne se reconcilient pas avec le détail par nationalité, sur la totalité des 18 colonnes. Il est probable que ce total officiel ait été calculé à partir d'une extraction différente (système source, ou export intermédiaire) que celle utilisée pour le détail par nationalité — un problème de cohérence interne du rapport ministériel, plus large que les coquilles isolées observées sur les fichiers MAROCAINS et MRE.

À noter : un premier test faisait suspecter un artefact d'extraction (débordement de libellés multi-lignes avalant des chiffres, comme identifié et corrigé sur le fichier PM/PT). Ce même correctif appliqué au fichier PA n'a changé aucun résultat, confirmant que la cause est différente ici.

## Fiabilité par niveau d'agrégation

| Niveau | Fiabilité |
|---|---|
| Nationalité (toutes postes confondus) | ✅ Fiable (183/185 lignes exactement cohérentes) |
| Poste-frontière (toutes nationalités confondues) | ⚠️ Non réconcilié avec le total officiel — à utiliser avec prudence |
| Grand total général | ✅ Quasi-exact (écart de 2 sur 765412) |

## Recommandation

- Le KPI "arrivées par nationalité" (dashboard Power BI) peut s'appuyer sur ces données en confiance.
- Le KPI "arrivées par poste-frontière" pour ce fichier spécifique doit être présenté avec une réserve, ou complété par une vérification manuelle du PDF source auprès du Ministère.
- Signaler cette incohérence de reconciliation au service responsable de la publication des statistiques APF.
