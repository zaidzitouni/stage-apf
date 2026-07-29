from pathlib import Path

from extract_mre import CHEMIN_PDF, construire_dataframe, extraire_periode, valider
from db_utils import charger_dataframe, verifier_table

CHEMIN_DB = Path(__file__).parent / "data" / "db" / "apf.db"

if __name__ == "__main__":
    annee, mois = extraire_periode(CHEMIN_PDF)
    df, ligne_totaux = construire_dataframe(CHEMIN_PDF)
    df = valider(df, ligne_totaux)

    print(f"\nChargement en base : {CHEMIN_DB}")
    charger_dataframe(
        df, "mre_controles",
        cle_primaire=["annee", "mois", "poste_frontiere"],
        chemin_db=CHEMIN_DB, annee=annee, mois=mois, fichier_source=CHEMIN_PDF.name,
    )
    print("Chargement terminé.\n")
    verifier_table("mre_controles", CHEMIN_DB)
