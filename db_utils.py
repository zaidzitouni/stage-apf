"""
Fonctions génériques de chargement en base SQLite, réutilisées par tous
les scripts extract_*.py / charger_*.py du pipeline APF.
"""
import sqlite3

TYPE_SQL = {"int64": "INTEGER", "float64": "REAL", "object": "TEXT", "bool": "INTEGER"}


def charger_dataframe(df, table_name, cle_primaire, chemin_db, annee=None, mois=None, fichier_source=None):
    """
    Charge un DataFrame dans une table SQLite (créée si besoin), avec
    INSERT OR REPLACE : relancer le script sur la même période met à jour
    les lignes existantes au lieu de les dupliquer.
    """
    df = df.copy()
    if annee is not None:
        df["annee"] = annee
    if mois is not None:
        df["mois"] = mois
    if fichier_source is not None:
        df["fichier_source"] = fichier_source

    for col in df.select_dtypes(include="bool").columns:
        df[col] = df[col].astype(int)

    colonnes_sql = ", ".join(f'"{c}" {TYPE_SQL.get(str(df[c].dtype), "TEXT")}' for c in df.columns)
    schema = (
        f'CREATE TABLE IF NOT EXISTS "{table_name}" '
        f'({colonnes_sql}, PRIMARY KEY ({", ".join(cle_primaire)}));'
    )

    chemin_db.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(chemin_db) as conn:
        conn.execute(schema)
        placeholders = ", ".join(["?"] * len(df.columns))
        conn.executemany(
            f'INSERT OR REPLACE INTO "{table_name}" ({", ".join(df.columns)}) VALUES ({placeholders})',
            df.itertuples(index=False, name=None),
        )
        conn.commit()


def verifier_table(table_name, chemin_db, colonne_totaux="totaux"):
    """Petit contrôle post-chargement : nombre de lignes + somme de contrôle."""
    with sqlite3.connect(chemin_db) as conn:
        nb = conn.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()[0]
        somme = conn.execute(f'SELECT SUM("{colonne_totaux}") FROM "{table_name}"').fetchone()[0]
    print(f"Lignes en base ({table_name}) : {nb}")
    print(f"Somme des {colonne_totaux}   : {somme}")