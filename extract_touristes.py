"""
Extraction des fichiers APF "TOURISTE PA ENTREE" (aéroports) et
"TOURISTE PM PT ENTREE" (maritime/terrestre).
---------------------------------------------------------------------------
Contrairement aux fichiers MAROCAINS/MRE (une ligne par poste-frontière),
ces fichiers sont une matrice nationalité x poste-frontière. On la
transforme en format "long" (une ligne par couple nationalité/poste) :
plus facile à valider, à charger en base, et à interroger ensuite.

Ce script est générique : il fonctionne pour les 2 fichiers, seul le
chemin change (voir charger_bdd_touristes_pa.py / _pm_pt.py).
"""
import re

import pandas as pd
import pdfplumber


import re


def nettoyer_cellule(val):
    if val is None:
        return ""
    texte = str(val).replace("\n", " ").strip()
    # Cas d'un libellé enroulé qui déborde dans la cellule numérique voisine
    # (ex: 'ORIALE 14' au lieu de '14') : on ne garde que les chiffres finaux.
    match = re.match(r"^\D*(\d+)$", texte)
    if match:
        return match.group(1)
    return texte


def est_ligne_ignoree(row):
    """Lignes d'en-tête répétées à chaque page, ou lignes 'espaceur' vides."""
    return row[0] in (None, "", "NATIONALITES")


def extraire_periode(chemin_pdf):
    with pdfplumber.open(chemin_pdf) as pdf:
        texte = pdf.pages[0].extract_text()
    match = re.search(r"DU (\d{2})/(\d{2})/(\d{4}) AU", texte)
    if not match:
        return None
    jour, mois, annee = match.groups()
    return int(annee), int(mois)


def extraire_lignes_brutes(chemin_pdf):
    lignes = []
    with pdfplumber.open(chemin_pdf) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                lignes.extend(table)
    return [[nettoyer_cellule(c) for c in row] for row in lignes]


def construire_dataframe(chemin_pdf):
    """
    Retourne :
    - df_long : format long (nationalite, poste_frontiere, nombre, totaux_nationalite)
    - df_large : format large brut (utile pour la validation par poste)
    - postes : liste ordonnée des noms de poste-frontière
    - ligne_totaux_officielle : la ligne TOTAUX imprimée en bas du PDF
    """
    lignes = extraire_lignes_brutes(chemin_pdf)

    entete = lignes[0]
    postes = entete[1:-1]  # colonne 0 = NATIONALITES, dernière colonne = TOTAUX

    lignes_donnees = []
    ligne_totaux_officielle = None
    for row in lignes:
        if est_ligne_ignoree(row):
            continue
        if row[0] == "TOTAUX":
            ligne_totaux_officielle = row
            continue
        lignes_donnees.append(row)

    colonnes = ["nationalite"] + postes + ["totaux"]
    df_large = pd.DataFrame(lignes_donnees, columns=colonnes)

    for col in colonnes[1:]:
        df_large[col] = pd.to_numeric(df_large[col].replace("", "0"), errors="coerce").fillna(0).astype(int)

    df_long = df_large.melt(
        id_vars=["nationalite", "totaux"], value_vars=postes,
        var_name="poste_frontiere", value_name="nombre",
    ).rename(columns={"totaux": "totaux_nationalite"})

    return df_long, df_large, postes, ligne_totaux_officielle


def valider(df_long, df_large, postes, ligne_totaux_officielle):
    """
    3 niveaux de validation :
    1) somme par nationalité (ligne) == totaux_nationalite imprimé
    2) somme par poste (colonne) == valeur de la ligne TOTAUX officielle pour ce poste
    3) somme générale == total officiel (intersection ligne/colonne TOTAUX)
    """
    # 1) Validation par ligne (nationalité)
    par_nat = df_long.groupby("nationalite").nombre.sum().reset_index(name="somme_calculee")
    verif_nat = df_large[["nationalite", "totaux"]].merge(par_nat, on="nationalite")
    anomalies_nat = verif_nat[verif_nat.totaux != verif_nat.somme_calculee]

    # 2) Validation par colonne (poste)
    totaux_officiels_poste = {
        p: int(v) if v else 0 for p, v in zip(postes, ligne_totaux_officielle[1:-1])
    }
    par_poste = df_long.groupby("poste_frontiere").nombre.sum()
    anomalies_poste = {
        p: (int(par_poste[p]), totaux_officiels_poste[p])
        for p in postes if int(par_poste[p]) != totaux_officiels_poste[p]
    }

    # 3) Grand total
    grand_total_calcule = int(df_long.nombre.sum())
    grand_total_officiel = int(ligne_totaux_officielle[-1])

    print(f"Nationalités : {len(df_large)} | Postes : {len(postes)} | Lignes (format long) : {len(df_long)}")
    print(f"Anomalies par nationalité : {len(anomalies_nat)}")
    if len(anomalies_nat):
        print(anomalies_nat.to_string(index=False))
    print(f"Anomalies par poste : {len(anomalies_poste)}")
    for p, (calc, off) in anomalies_poste.items():
        print(f"  - {p} : calculé={calc}, officiel={off}")
    print(f"Somme générale calculée : {grand_total_calcule}")
    print(f"Total officiel imprimé  : {grand_total_officiel}")
    print("-> Cohérent" if grand_total_calcule == grand_total_officiel else "-> Écart détecté")

    return anomalies_nat, anomalies_poste, grand_total_calcule, grand_total_officiel
