"""
Extraction du fichier APF "MRE PAR SITE ENTREE" (stage_data_3.pdf)
--------------------------------------------------------------------
Structure proche du fichier MAROCAINS : poste-frontière en ligne,
mais ici la dimension est le type de passeport (étranger / marocain)
plutôt que entrée/sortie.
"""
import re
from pathlib import Path

import pandas as pd
import pdfplumber

DOSSIER_SCRIPT = Path(__file__).parent
CHEMIN_PDF = DOSSIER_SCRIPT / "data" / "raw" / "stage_data_3.pdf"

COLONNES = [
    "poste_frontiere",
    "femmes_etranger", "hommes_etranger", "mineurs_etranger", "total_etranger",
    "femmes_marocain", "hommes_marocain", "mineurs_marocain", "total_marocain",
    "totaux",
]

# Les 3 colonnes "détail" de chaque groupe (utilisées pour valider/réparer le "total")
GROUPES = [
    ("femmes_etranger", "hommes_etranger", "mineurs_etranger", "total_etranger"),
    ("femmes_marocain", "hommes_marocain", "mineurs_marocain", "total_marocain"),
]


def extraire_lignes_brutes(chemin_pdf):
    lignes = []
    with pdfplumber.open(chemin_pdf) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                lignes.extend(table)
    return lignes


def nettoyer_cellule(val):
    if val is None:
        return ""
    return str(val).replace("\n", " ").strip()


def est_ligne_ignoree(row):
    """Lignes d'en-tête répétées ou lignes 'espaceur' vides entre chaque donnée."""
    return row[0] in (None, "", "POSTES FRONTIERES")


def extraire_periode(chemin_pdf):
    with pdfplumber.open(chemin_pdf) as pdf:
        texte = pdf.pages[0].extract_text()
    match = re.search(r"DU (\d{2})/(\d{2})/(\d{4}) AU", texte)
    if not match:
        return None
    jour, mois, annee = match.groups()
    return int(annee), int(mois)


def construire_dataframe(chemin_pdf):
    brutes = [[nettoyer_cellule(c) for c in row] for row in extraire_lignes_brutes(chemin_pdf)]

    lignes_donnees = []
    ligne_totaux_officielle = None
    for row in brutes:
        if est_ligne_ignoree(row):
            continue
        if row[0] == "TOTAUX":
            ligne_totaux_officielle = row
            continue
        lignes_donnees.append(row)

    df = pd.DataFrame(lignes_donnees, columns=COLONNES)

    # Repérer les cellules corrompues (ex: "##30") avant conversion numérique
    corrections = []
    for idx, row in df.iterrows():
        for femmes_c, hommes_c, mineurs_c, total_c in GROUPES:
            valeurs = {femmes_c: row[femmes_c], hommes_c: row[hommes_c], mineurs_c: row[mineurs_c]}
            corrompues = [c for c, v in valeurs.items() if v and not v.isdigit()]
            propres = {c: int(v) for c, v in valeurs.items() if v.isdigit()}
            total_val = row[total_c]
            if len(corrompues) == 1 and total_val.isdigit():
                colonne_a_reparer = corrompues[0]
                valeur_reparee = int(total_val) - sum(propres.values())
                df.at[idx, colonne_a_reparer] = str(valeur_reparee)
                corrections.append((row["poste_frontiere"], colonne_a_reparer, valeur_reparee))

    for col in COLONNES[1:]:
        df[col] = pd.to_numeric(df[col].replace("", "0"), errors="coerce").fillna(0).astype(int)

    if corrections:
        print("Cellules corrompues reconstituées automatiquement :")
        for poste, col, val in corrections:
            print(f"  - {poste} / {col} -> {val}")

    return df, ligne_totaux_officielle


def valider(df, ligne_totaux_officielle):
    df = df.copy()
    df["total_etranger_calcule"] = df.femmes_etranger + df.hommes_etranger + df.mineurs_etranger
    df["total_marocain_calcule"] = df.femmes_marocain + df.hommes_marocain + df.mineurs_marocain
    df["totaux_calcule"] = df.total_etranger_calcule + df.total_marocain_calcule
    df["anomalie"] = (
        (df.total_etranger != df.total_etranger_calcule)
        | (df.total_marocain != df.total_marocain_calcule)
        | (df.totaux != df.totaux_calcule)
    )

    anomalies = df[df.anomalie]
    print(f"\nLignes extraites : {len(df)}")
    print(f"Anomalies arithmétiques détectées : {len(anomalies)}")
    if len(anomalies):
        print(anomalies[["poste_frontiere", "totaux", "totaux_calcule"]].to_string(index=False))

    somme_imprimee = df.totaux.sum()
    somme_officielle = int(ligne_totaux_officielle[-1])
    print(f"\nSomme des TOTAUX imprimés (tels quels) : {somme_imprimee}")
    print(f"Total officiel imprimé en bas du PDF    : {somme_officielle}")
    print("-> Cohérent" if somme_imprimee == somme_officielle else "-> Écart (voir anomalies ci-dessus)")

    return df


if __name__ == "__main__":
    annee, mois = extraire_periode(CHEMIN_PDF)
    print(f"Période détectée dans le PDF : {mois:02d}/{annee}\n")

    df, ligne_totaux = construire_dataframe(CHEMIN_PDF)
    df = valider(df, ligne_totaux)

    print("\nAperçu des 5 premières lignes :")
    print(df.head())
    print("\nLigne CSPA RABAT-SALE après reconstitution :")
    print(df[df.poste_frontiere == "CSPA RABAT-SALE"])
