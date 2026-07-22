"""
Extraction du fichier APF "MAROCAINS PAR SITE" (stage_data_2.pdf)
------------------------------------------------------------------
Étape 1 du pipeline : extraction + nettoyage + validation.
"""
from pathlib import Path

import pdfplumber
import pandas as pd

DOSSIER_SCRIPT = Path(__file__).parent
CHEMIN_PDF = DOSSIER_SCRIPT / "data" / "raw" / "stage_data_2.pdf"

COLONNES = [
    "poste_frontiere",
    "femmes_entree", "hommes_entree", "mineurs_entree", "total_entree",
    "femmes_sortie", "hommes_sortie", "mineurs_sortie", "total_sortie",
    "totaux",
]

def extraire_lignes_brutes(chemin_pdf):
    """Extrait toutes les lignes de tous les tableaux détectés sur toutes les pages."""
    lignes = []
    with pdfplumber.open(chemin_pdf) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                lignes.extend(table)
    return lignes


def est_ligne_entete(row):
    """Repère les lignes d'en-tête répétées (à ignorer)."""
    if not row or row[0] in ("", None):
        return len(row) > 1 and row[1] == "ENTREE"
    return "POSTES FRONTIERES" in str(row[0]).upper()


def nettoyer_cellule(val):
    """Remplace None par '', enlève les retours à la ligne internes, strip les espaces."""
    if val is None:
        return ""
    return str(val).replace("\n", " ").strip()


def reparer_ligne_clairsemee(row):
    """
    pdfplumber ajoute parfois des colonnes fantômes vides en fin de ligne
    (artefact de mise en page) : on les retire d'abord, sans toucher au
    reste de la ligne.

    Cas plus rare (ex. PA GUELMIM) : sur une ligne presque entièrement vide,
    la toute dernière valeur (TOTAUX) peut glisser d'une case vers la
    droite. Une fois les colonnes fantômes retirées, s'il reste un
    excédent, on retire la case vide la plus proche de cette valeur pour
    la remettre à sa vraie place.
    """
    row = list(row)
    largeur = len(COLONNES)

    # 1) Colonnes fantômes vides en fin de ligne
    while len(row) > largeur and row[-1] == "":
        row.pop()

    # 2) Cas résiduel : une valeur a glissé d'une case
    while len(row) > largeur:
        for i in range(len(row) - 2, 0, -1):
            if row[i] == "":
                row.pop(i)
                break
        else:
            row.pop()  # sécurité, ne devrait pas arriver

    while len(row) < largeur:
        row.append("")
    return row


def construire_dataframe(chemin_pdf):
    brutes = extraire_lignes_brutes(chemin_pdf)
    lignes_donnees = []
    for row in brutes:
        row = [nettoyer_cellule(c) for c in row]
        if est_ligne_entete(row):
            continue
        if row[0] == "TOTAUX":
            ligne_totaux_officielle = row
            continue
        if len(row) != len(COLONNES):
            row = reparer_ligne_clairsemee(row)
        lignes_donnees.append(row)

    df = pd.DataFrame(lignes_donnees, columns=COLONNES)

    # Conversion en nombres (case vide -> 0)
    for col in COLONNES[1:]:
        df[col] = pd.to_numeric(df[col].replace("", "0"), errors="coerce").fillna(0).astype(int)

    return df, ligne_totaux_officielle


def valider(df, ligne_totaux_officielle):
    """Vérifie les règles arithmétiques + le total officiel imprimé sur le PDF."""
    anomalies = df[
        (df.total_entree != df.femmes_entree + df.hommes_entree + df.mineurs_entree) |
        (df.total_sortie != df.femmes_sortie + df.hommes_sortie + df.mineurs_sortie) |
        (df.totaux != df.total_entree + df.total_sortie)
    ]
    print(f"Lignes extraites : {len(df)}")
    print(f"Anomalies arithmétiques restantes : {len(anomalies)}")
    if len(anomalies):
        print(anomalies)

    somme_calculee = df.totaux.sum()
    somme_officielle = int(ligne_totaux_officielle[-1])
    print(f"Somme calculée des TOTAUX      : {somme_calculee}")
    print(f"Total officiel imprimé sur PDF : {somme_officielle}")
    print("-> Validation OK" if somme_calculee == somme_officielle else "-> ECART DETECTE")


if __name__ == "__main__":
    df, ligne_totaux = construire_dataframe(CHEMIN_PDF)
    valider(df, ligne_totaux)
    print("\nAperçu des 5 premières lignes :")
    print(df.head())
    print("\nLigne PA GUELMIM après correction :")
    print(df[df.poste_frontiere == "PA GUELMIM"])