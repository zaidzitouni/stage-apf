"""
Chargement des données validées du fichier MAROCAINS dans une base SQLite.
---------------------------------------------------------------------------
Étape 2 du pipeline : réutilise les fonctions d'extraction/validation de
extract_marocains.py, puis charge le résultat dans une table SQL.
"""
import sqlite3
from pathlib import Path

from extract_marocains import CHEMIN_PDF, construire_dataframe, extraire_periode, valider

DOSSIER_SCRIPT = Path(__file__).parent
CHEMIN_DB = DOSSIER_SCRIPT / "data" / "db" / "apf.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS marocains_controles (
    annee INTEGER NOT NULL,
    mois INTEGER NOT NULL,
    poste_frontiere TEXT NOT NULL,
    femmes_entree INTEGER,
    hommes_entree INTEGER,
    mineurs_entree INTEGER,
    total_entree INTEGER,
    femmes_sortie INTEGER,
    hommes_sortie INTEGER,
    mineurs_sortie INTEGER,
    total_sortie INTEGER,
    totaux INTEGER,
    totaux_calcule INTEGER,
    anomalie INTEGER,
    fichier_source TEXT,
    PRIMARY KEY (annee, mois, poste_frontiere)
);
"""


def charger(df, annee, mois, fichier_source, chemin_db=CHEMIN_DB):
    """
    Charge le DataFrame dans la table SQLite.
    Utilise INSERT OR REPLACE (clé = annee/mois/poste) : relancer le script
    sur le même mois met simplement à jour les lignes au lieu de les dupliquer.
    """
    chemin_db.parent.mkdir(parents=True, exist_ok=True)
    df = df.copy()
    df["annee"] = annee
    df["mois"] = mois
    df["fichier_source"] = fichier_source
    df["anomalie"] = df["anomalie"].astype(int)  # SQLite n'a pas de type booléen natif

    colonnes_table = [
        "annee", "mois", "poste_frontiere",
        "femmes_entree", "hommes_entree", "mineurs_entree", "total_entree",
        "femmes_sortie", "hommes_sortie", "mineurs_sortie", "total_sortie",
        "totaux", "totaux_calcule", "anomalie", "fichier_source",
    ]

    with sqlite3.connect(chemin_db) as conn:
        conn.execute(SCHEMA)
        conn.executemany(
            f"INSERT OR REPLACE INTO marocains_controles "
            f"({', '.join(colonnes_table)}) VALUES ({', '.join(['?'] * len(colonnes_table))})",
            df[colonnes_table].itertuples(index=False, name=None),
        )
        conn.commit()


def verifier(chemin_db=CHEMIN_DB):
    """Petite vérification post-chargement : nombre de lignes + somme des TOTAUX."""
    with sqlite3.connect(chemin_db) as conn:
        nb_lignes = conn.execute("SELECT COUNT(*) FROM marocains_controles").fetchone()[0]
        somme_totaux = conn.execute("SELECT SUM(totaux) FROM marocains_controles").fetchone()[0]
        nb_anomalies = conn.execute(
            "SELECT COUNT(*) FROM marocains_controles WHERE anomalie = 1"
        ).fetchone()[0]
    print(f"Lignes en base       : {nb_lignes}")
    print(f"Somme des TOTAUX     : {somme_totaux}")
    print(f"Lignes marquées 'anomalie' : {nb_anomalies}")


if __name__ == "__main__":
    annee, mois = extraire_periode(CHEMIN_PDF)
    df, ligne_totaux = construire_dataframe(CHEMIN_PDF)
    df = valider(df, ligne_totaux)

    print(f"\nChargement en base : {CHEMIN_DB}")
    charger(df, annee, mois, fichier_source=CHEMIN_PDF.name)
    print("Chargement terminé.\n")

    verifier()
