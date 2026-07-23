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


import re


def extraire_periode(chemin_pdf):
    """
    Repère la période couverte par le fichier depuis son texte
    (ex. 'DU 01/12/2019 AU 31/12/2019') pour l'utiliser comme métadonnée
    lors du chargement en base -> évite de coder la date en dur.
    """
    with pdfplumber.open(chemin_pdf) as pdf:
        texte = pdf.pages[0].extract_text()
    match = re.search(r"DU (\d{2})/(\d{2})/(\d{4}) AU", texte)
    if not match:
        return None
    jour, mois, annee = match.groups()
    return int(annee), int(mois)


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
    """
    Ajoute des colonnes de contrôle (totaux recalculés) et un indicateur
    booléen d'anomalie, SANS modifier les valeurs sources extraites du PDF
    (on ne réécrit jamais une donnée source silencieusement).
    """
    df = df.copy()
    df["total_entree_calcule"] = df.femmes_entree + df.hommes_entree + df.mineurs_entree
    df["total_sortie_calcule"] = df.femmes_sortie + df.hommes_sortie + df.mineurs_sortie
    df["totaux_calcule"] = df.total_entree_calcule + df.total_sortie_calcule
    df["anomalie"] = (
        (df.total_entree != df.total_entree_calcule)
        | (df.total_sortie != df.total_sortie_calcule)
        | (df.totaux != df.totaux_calcule)
    )

    anomalies = df[df.anomalie]
    print(f"Lignes extraites : {len(df)}")
    print(f"Anomalies arithmétiques détectées : {len(anomalies)}")
    if len(anomalies):
        print(anomalies[["poste_frontiere", "totaux", "totaux_calcule"]].to_string(index=False))

    somme_imprimee = df.totaux.sum()
    somme_officielle = int(ligne_totaux_officielle[-1])
    print(f"\nSomme des TOTAUX imprimés sur le PDF (tels quels) : {somme_imprimee}")
    print(f"Total officiel imprimé en bas du PDF              : {somme_officielle}")
    print("-> Cohérent" if somme_imprimee == somme_officielle else "-> Écart (voir anomalies ci-dessus)")

    return df


if __name__ == "__main__":
    annee, mois = extraire_periode(CHEMIN_PDF)
    print(f"Période détectée dans le PDF : {mois:02d}/{annee}\n")

    df, ligne_totaux = construire_dataframe(CHEMIN_PDF)
    df = valider(df, ligne_totaux)
    print("\nAperçu des 5 premières lignes :")
    print(df.head())
    print("\nLigne PA GUELMIM après correction :")
    print(df[df.poste_frontiere == "PA GUELMIM"])