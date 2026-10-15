SCHEMA = """fct_ventes(id_mutation VARCHAR, date_id DATE, commune_id VARCHAR, prix DOUBLE,
           surface_bati DOUBLE, surface_terrain DOUBLE, nb_pieces BIGINT, nb_lots BIGINT,
           type_bien VARCHAR, prix_m2 DOUBLE)
dim_commune(commune_id VARCHAR, nom_commune VARCHAR, code_postal VARCHAR)
dim_date(date_id DATE, annee BIGINT, trimestre BIGINT, mois BIGINT, nom_mois VARCHAR, jour_semaine BIGINT)

fct_ventes.commune_id -> dim_commune.commune_id
fct_ventes.date_id    -> dim_date.date_id"""

INSTRUCTION = (
    "Écris une requête SQL DuckDB qui répond à la question. "
    "Réponds uniquement par la requête, sans explication."
)


def build_prompt(question):
    return f"{INSTRUCTION}\n\n### Schéma\n{SCHEMA}\n\n### Question\n{question}\n\n### SQL\n"
