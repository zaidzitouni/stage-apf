"""
Interface conversationnelle Text-to-SQL pour interroger les données APF
en français.
Lancement : uv run streamlit run app.py
"""
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from llm_query import generer_sql
from sql_security import RequeteNonAutorisee, executer_sql, extraire_schema

load_dotenv()

CHEMIN_DB = Path(__file__).parent / "data" / "db" / "apf.db"

st.set_page_config(page_title="APF — Interrogation en langage naturel", page_icon="🛂")
st.title("Interrogation des données APF")
st.caption("Pose une question en français sur les arrivées (touristes, MRE, marocains).")

question = st.text_input(
    "Ta question",
    placeholder="Ex : Combien d'Espagnols sont arrivés par voie aérienne en décembre 2019 ?",
)

if st.button("Interroger", type="primary") and question:
    schema = extraire_schema(CHEMIN_DB)

    with st.spinner("Traduction de la question en SQL..."):
        try:
            sql = generer_sql(question, schema)
        except Exception as e:
            st.error(f"Erreur lors de l'appel au LLM : {e}")
            st.stop()

    with st.expander("Requête SQL générée", expanded=False):
        st.code(sql, language="sql")

    try:
        resultats = executer_sql(sql, CHEMIN_DB)
    except RequeteNonAutorisee as e:
        st.error(f"Requête refusée par le filtre de sécurité : {e}")
        st.stop()
    except Exception as e:
        st.error(f"Erreur lors de l'exécution de la requête : {e}")
        st.stop()

    if resultats.empty:
        st.warning("Aucun résultat pour cette question.")
    else:
        st.dataframe(resultats, width="stretch")

        # Graphique automatique seulement quand la forme du résultat s'y prête :
        # 1 colonne catégorielle (texte) + 1 colonne numérique, plusieurs lignes.
        colonnes_texte = resultats.select_dtypes(include=["object", "str"]).columns
        colonnes_nombres = resultats.select_dtypes(include="number").columns

        if len(resultats) > 1 and len(colonnes_texte) == 1 and len(colonnes_nombres) >= 1:
            st.bar_chart(resultats.set_index(colonnes_texte[0])[colonnes_nombres[0]])
