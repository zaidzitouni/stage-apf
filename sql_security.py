"""
Extraction du schéma de la base + exécution sécurisée des requêtes SQL
générées par le LLM.
------------------------------------------------------------------------
Principe de sécurité : le LLM ne reçoit JAMAIS les données, seulement la
structure des tables (noms de colonnes). Et la requête qu'il génère est
systématiquement vérifiée avant exécution : uniquement des SELECT,
sur une connexion SQLite en lecture seule (double protection).
"""
import re
import sqlite3

import pandas as pd

MOTS_INTERDITS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE",
    "ATTACH", "DETACH", "PRAGMA", "REPLACE", "TRUNCATE",
    "VACUUM", "REINDEX", "EXEC",
]


def extraire_schema(chemin_db):
    """
    Construit une description textuelle des tables et colonnes de la base,
    à fournir au LLM comme contexte. Pour les colonnes texte, on ajoute
    quelques valeurs réelles en exemple (pas les données elles-mêmes,
    juste la convention d'écriture -> évite que le LLM invente une
    orthographe/casse plausible mais fausse, ex. 'Espagnol' au lieu de
    'ESPAGNOLE'). Une colonne par ligne : plus lisible pour le LLM qu'une
    longue ligne compacte par table.
    """
    blocs = []
    with sqlite3.connect(chemin_db) as conn:
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )]
        for table in tables:
            colonnes = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
            lignes_colonnes = []
            for c in colonnes:
                nom, type_sql = c[1], c[2]
                ligne = f"  - {nom} ({type_sql})"
                if type_sql == "TEXT" and nom != "fichier_source":
                    exemples = conn.execute(
                        f'SELECT DISTINCT "{nom}" FROM "{table}" LIMIT 5'
                    ).fetchall()
                    valeurs = ", ".join(repr(v[0]) for v in exemples)
                    ligne += f" -- exemples : {valeurs}"
                lignes_colonnes.append(ligne)
            blocs.append(f"Table {table} :\n" + "\n".join(lignes_colonnes))
    return "\n\n".join(blocs)


class RequeteNonAutorisee(Exception):
    pass


def valider_sql(sql):
    """
    N'autorise qu'une unique requête SELECT. Lève RequeteNonAutorisee sinon.
    """
    nettoyee = sql.strip().rstrip(";").strip()

    if not re.match(r"^\s*SELECT\b", nettoyee, re.IGNORECASE):
        raise RequeteNonAutorisee("Seules les requêtes SELECT sont autorisées.")

    if ";" in nettoyee:
        raise RequeteNonAutorisee("Une seule instruction SQL est autorisée.")

    for mot in MOTS_INTERDITS:
        if re.search(rf"\b{mot}\b", nettoyee, re.IGNORECASE):
            raise RequeteNonAutorisee(f"Mot-clé interdit détecté : {mot}")

    return nettoyee


def executer_sql(sql, chemin_db):
    """
    Valide puis exécute la requête sur une connexion SQLite EN LECTURE SEULE
    (mode=ro) : même si le filtre ci-dessus laissait passer quelque chose
    d'inattendu, la base elle-même refuserait toute écriture.
    """
    sql_valide = valider_sql(sql)
    uri = f"file:{chemin_db}?mode=ro"
    with sqlite3.connect(uri, uri=True) as conn:
        return pd.read_sql_query(sql_valide, conn)
