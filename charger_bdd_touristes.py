"""
Chargement des fichiers Touristes (PA aéroports + PM/PT maritime-terrestre)
dans la base SQLite, au format long (nationalite, poste_frontiere, nombre).
"""
from pathlib import Path

from extract_touristes import construire_dataframe, valider, extraire_periode
from db_utils import charger_dataframe, verifier_table

DOSSIER_SCRIPT = Path(__file__).parent
CHEMIN_DB = DOSSIER_SCRIPT / "data" / "db" / "apf.db"

FICHIERS = [
    {"chemin": DOSSIER_SCRIPT / "data" / "raw" / "stage_data_1.pdf", "table": "touristes_pa"},
    {"chemin": DOSSIER_SCRIPT / "data" / "raw" / "stage_data_4.pdf", "table": "touristes_pm_pt"},
]

if __name__ == "__main__":
    for f in FICHIERS:
        print(f"\n===== {f['table']} =====")
        annee, mois = extraire_periode(f["chemin"])
        df_long, df_large, postes, ligne_totaux = construire_dataframe(f["chemin"])
        valider(df_long, df_large, postes, ligne_totaux)

        print(f"\nChargement en base : {f['table']}")
        charger_dataframe(
            df_long, f["table"],
            cle_primaire=["annee", "mois", "nationalite", "poste_frontiere"],
            chemin_db=CHEMIN_DB, annee=annee, mois=mois, fichier_source=f["chemin"].name,
        )
        verifier_table(f["table"], CHEMIN_DB, colonne_totaux="nombre")
