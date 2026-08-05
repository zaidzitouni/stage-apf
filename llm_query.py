"""
Traduction d'une question en français en requête SQL, via l'API OpenAI.
--------------------------------------------------------------------------
Important : seul le SCHÉMA (noms de tables/colonnes) est envoyé au LLM,
jamais les données elles-mêmes. La requête générée est ensuite validée par
sql_security.py avant toute exécution.
"""
import os

from openai import OpenAI

PROMPT_SYSTEME = """Tu es un traducteur de questions en français vers des requêtes SQL SQLite.

Contexte métier (à connaître impérativement avant de répondre) :
- marocains_controles : contrôles de ressortissants marocains, à l'entrée ET à la sortie.
- mre_controles : contrôles de Marocains Résidant à l'Étranger (MRE), à l'entrée uniquement.
- touristes_pa : arrivées de touristes étrangers par voie AÉRIENNE (aéroports) uniquement.
- touristes_pm_pt : arrivées de touristes étrangers par voie MARITIME et TERRESTRE uniquement.

touristes_pa et touristes_pm_pt sont deux morceaux d'une même notion ("touristes
étrangers"), simplement séparés par mode de transport. Une question sur le total
des touristes SANS précision de mode de transport (avion, bateau, poste terrestre)
doit combiner les deux tables (UNION ALL). Une question qui précise explicitement
un mode de transport ne doit interroger que la table correspondante.

Schéma de la base de données (tables et colonnes disponibles) :
{schema}

Règles strictes :
- Réponds UNIQUEMENT avec la requête SQL, sans aucune explication, sans balises markdown (pas de ```sql).
- Une seule requête SELECT. Jamais d'INSERT, UPDATE, DELETE, DROP, ou toute autre modification.
- Utilise uniquement les tables et colonnes listées ci-dessus.
- Pour toute comparaison sur une colonne texte (nom, nationalité, poste...), utilise
  UPPER(colonne) = UPPER('valeur') plutôt que colonne = 'valeur', pour rester
  insensible à la casse même si l'orthographe exacte de la valeur est incertaine.
- Si la question porte sur une notion absente du schéma, réponds exactement :
  SELECT 'Question hors du périmètre des données disponibles' AS message
"""


def generer_sql(question, schema):
    """Appelle l'API OpenAI pour traduire la question en requête SQL."""
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    modele = os.environ.get("OPENAI_MODEL", "gpt-5.4-mini")

    reponse = client.chat.completions.create(
        model=modele,
        messages=[
            {"role": "system", "content": PROMPT_SYSTEME.format(schema=schema)},
            {"role": "user", "content": question},
        ],
        temperature=0,
    )
    sql = reponse.choices[0].message.content.strip()

    # Filet de sécurité si le modèle ajoute quand même des balises markdown
    sql = sql.removeprefix("```sql").removeprefix("```").removesuffix("```").strip()
    return sql
