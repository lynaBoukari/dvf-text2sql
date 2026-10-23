import json
import re
from itertools import cycle

from db import connect

COMMUNES = [
    "Bordeaux",
    "Mérignac",
    "Pessac",
    "Talence",
    "Villenave-d'Ornon",
    "Bègles",
    "Arcachon",
    "La Teste-de-Buch",
    "Le Bouscat",
    "Libourne",
    "Eysines",
    "Gujan-Mestras",
    "Cenon",
    "Gradignan",
    "Saint-Médard-en-Jalles",
    "Bruges",
    "Lacanau",
    "Andernos-les-Bains",
    "Lormont",
    "Floirac",
    "Lège-Cap-Ferret",
    "Le Haillan",
    "Saint-André-de-Cubzac",
    "Ambarès-et-Lagrave",
    "Blanquefort",
]
ANNEES = [2022, 2023, 2024]
TYPES = ["Maison", "Appartement"]
NB_PIECES = [2, 3, 4, 5]
SEUILS_SURFACE = [40, 60, 80, 100, 120]
SEUILS_TERRAIN = [200, 500, 1000, 2000]
TOP_N = [3, 5, 10]


def q(valeur):
    """Échappe une valeur texte avant de l'insérer dans une chaîne SQL."""
    return str(valeur).replace("'", "''")


def combos(n, **listes):
    """n jeux de paramètres, chaque liste tournant à son propre rythme."""
    iters = {k: cycle(v) for k, v in listes.items()}
    return [{k: next(it) for k, it in iters.items()} for _ in range(n)]


TEMPLATES = [
    # ---- 1 : agrégat simple sur une commune, prix médian au m2 ----
    {
        "n": 8,
        "listes": {"commune": COMMUNES},
        "questions": [
            "Quel est le prix médian au m2 à {commune} ?",
            "Combien coûte le mètre carré à {commune} ?",
            "Prix médian au m2 sur {commune} ?",
        ],
        "sql": "SELECT median(f.prix_m2) AS prix_m2_median "
        "FROM fct_ventes f "
        "JOIN dim_commune c ON f.commune_id = c.commune_id "
        "WHERE c.nom_commune = '{commune}'",
    },
    # ---- 2 : jointure dim_date + filtre type_bien ----
    {
        "n": 8,
        "listes": {"commune": COMMUNES, "annee": ANNEES, "type_bien": TYPES},
        "questions": [
            "Combien de biens de type {type_bien} ont été vendus à {commune} en {annee} ?",
            "Nombre de ventes de type {type_bien} sur {commune} pour {annee} ?",
        ],
        "sql": "SELECT COUNT(*) AS nb_ventes "
        "FROM fct_ventes f "
        "JOIN dim_commune c ON f.commune_id = c.commune_id "
        "JOIN dim_date d ON f.date_id = d.date_id "
        "WHERE c.nom_commune = '{commune}' "
        "AND f.type_bien = '{type_bien}' AND d.annee = {annee}",
    },
    # ---- 3 : surface bâtie moyenne sur une commune ----
    {
        "n": 8,
        "listes": {"commune": COMMUNES},
        "questions": [
            "Quelle est la surface bâtie moyenne des ventes à {commune} ?",
            "Surface moyenne des biens vendus sur {commune} ?",
        ],
        "sql": "SELECT AVG(f.surface_bati) AS surface_moyenne_bati "
        "FROM fct_ventes f "
        "JOIN dim_commune c ON f.commune_id = c.commune_id "
        "WHERE c.nom_commune = '{commune}'",
    },
    # ---- 4 : prix maximum sur une commune ----
    {
        "n": 8,
        "listes": {"commune": COMMUNES},
        "questions": [
            "Quel est le prix le plus élevé observé à {commune} ?",
            "Vente la plus chère sur {commune} ?",
        ],
        "sql": "SELECT MAX(f.prix) AS prix_plus_cher "
        "FROM fct_ventes f "
        "JOIN dim_commune c ON f.commune_id = c.commune_id "
        "WHERE c.nom_commune = '{commune}'",
    },
    # ---- 5 : groupement par trimestre (dim_date) ----
    {
        "n": 3,
        "listes": {"annee": ANNEES},
        "questions": [
            "Combien de ventes par trimestre en {annee} ?",
            "Répartition des ventes par trimestre pour {annee} ?",
        ],
        "sql": "SELECT d.trimestre, COUNT(*) AS nb_ventes "
        "FROM fct_ventes f "
        "JOIN dim_date d ON f.date_id = d.date_id "
        "WHERE d.annee = {annee} "
        "GROUP BY d.trimestre ORDER BY d.trimestre",
    },
    # ---- 6 : évolution annuelle du volume sur une commune ----
    {
        "n": 8,
        "listes": {"commune": COMMUNES},
        "questions": [
            "Combien de ventes par année à {commune} ?",
            "Volume annuel des transactions sur {commune} ?",
        ],
        "sql": "SELECT d.annee, COUNT(*) AS nb_ventes "
        "FROM fct_ventes f "
        "JOIN dim_commune c ON f.commune_id = c.commune_id "
        "JOIN dim_date d ON f.date_id = d.date_id "
        "WHERE c.nom_commune = '{commune}' "
        "GROUP BY d.annee ORDER BY d.annee",
    },
    # ---- 7 : classement avec LIMIT et départage unique ----
    {
        "n": 6,
        "listes": {"n_top": TOP_N, "type_bien": TYPES},
        "questions": [
            "Quelles sont les {n_top} communes les plus chères au m2 pour le type {type_bien} ?",
            "Top {n_top} des communes où le m2 est le plus cher, type {type_bien} ?",
        ],
        "sql": "SELECT c.nom_commune, median(f.prix_m2) AS prix_m2_median "
        "FROM fct_ventes f "
        "JOIN dim_commune c ON f.commune_id = c.commune_id "
        "WHERE f.type_bien = '{type_bien}' "
        "GROUP BY c.commune_id, c.nom_commune "
        "ORDER BY prix_m2_median DESC, c.commune_id LIMIT {n_top}",
    },
    # ---- 8 : les N ventes les plus chères d'une commune ----
    {
        "n": 8,
        "listes": {"commune": COMMUNES, "n_top": TOP_N},
        "questions": [
            "Quelles sont les {n_top} ventes les plus chères à {commune} ?",
            "Top {n_top} des transactions les plus chères sur {commune} ?",
        ],
        "sql": "SELECT f.prix, f.surface_bati, f.type_bien "
        "FROM fct_ventes f "
        "JOIN dim_commune c ON f.commune_id = c.commune_id "
        "WHERE c.nom_commune = '{commune}' "
        "ORDER BY f.prix DESC, f.id_mutation "
        "LIMIT {n_top}",
    },
    # ---- 9 : comparaison d'une commune sur deux années ----
    {
        "n": 8,
        "listes": {"commune": COMMUNES},
        "questions": [
            "Quel est le prix médian au m2 à {commune} en 2023 et en 2024 ?",
            "Comment évolue le prix au m2 à {commune} entre 2023 et 2024 ?",
        ],
        "sql": "SELECT d.annee, median(f.prix_m2) AS prix_m2_median "
        "FROM fct_ventes f "
        "JOIN dim_commune c ON f.commune_id = c.commune_id "
        "JOIN dim_date d ON f.date_id = d.date_id "
        "WHERE c.nom_commune = '{commune}' AND d.annee IN (2023, 2024) "
        "GROUP BY d.annee ORDER BY d.annee",
    },
    # ---- 10 : comparaison entre deux communes sur une année ----
    {
        "n": 8,
        "listes": {
            "commune_a": COMMUNES,
            "commune_b": COMMUNES[1:] + COMMUNES[:1],
            "annee": ANNEES,
        },
        "questions": [
            "Y a-t-il plus de ventes à {commune_a} ou à {commune_b} en {annee} ?",
            "Compare le nombre de ventes entre {commune_a} et {commune_b} pour {annee}.",
        ],
        "sql": "SELECT c.nom_commune, COUNT(*) AS nb_ventes "
        "FROM fct_ventes f "
        "JOIN dim_commune c ON f.commune_id = c.commune_id "
        "JOIN dim_date d ON f.date_id = d.date_id "
        "WHERE c.nom_commune IN ('{commune_a}', '{commune_b}') "
        "AND d.annee = {annee} "
        "GROUP BY c.commune_id, c.nom_commune "
        "ORDER BY nb_ventes DESC, c.commune_id",
    },
    # ---- 11 : filtre sur nb_pieces ----
    {
        "n": 8,
        "listes": {"commune": COMMUNES, "nb_pieces": NB_PIECES, "type_bien": TYPES},
        "questions": [
            "Combien de ventes de type {type_bien} de plus de {nb_pieces} pièces à {commune} ?",
            "Nombre de biens {type_bien} à plus de {nb_pieces} pièces sur {commune} ?",
        ],
        "sql": "SELECT COUNT(*) AS nb_ventes "
        "FROM fct_ventes f "
        "JOIN dim_commune c ON f.commune_id = c.commune_id "
        "WHERE c.nom_commune = '{commune}' "
        "AND f.type_bien = '{type_bien}' AND f.nb_pieces > {nb_pieces}",
    },
    # ---- 12 : filtre sur surface_bati ----
    {
        "n": 8,
        "listes": {"commune": COMMUNES, "seuil": SEUILS_SURFACE, "type_bien": TYPES},
        "questions": [
            "Quel est le prix moyen des biens de type {type_bien} de moins de {seuil} m2 à {commune} ?",
            "Prix moyen pour un bien {type_bien} sous {seuil} m2 sur {commune} ?",
        ],
        "sql": "SELECT AVG(f.prix) AS prix_moyen "
        "FROM fct_ventes f "
        "JOIN dim_commune c ON f.commune_id = c.commune_id "
        "WHERE c.nom_commune = '{commune}' "
        "AND f.type_bien = '{type_bien}' AND f.surface_bati < {seuil}",
    },
    # ---- 13 : filtre sur surface_terrain ----
    {
        "n": 4,
        "listes": {"seuil": SEUILS_TERRAIN},
        "questions": [
            "Combien de ventes avec un terrain de plus de {seuil} m2 ?",
            "Nombre de biens vendus avec plus de {seuil} m2 de terrain ?",
        ],
        "sql": "SELECT COUNT(*) AS nb_ventes "
        "FROM fct_ventes f "
        "WHERE f.surface_terrain > {seuil}",
    },
    # ---- 14 : croisement type_bien x annee ----
    {
        "n": 6,
        "listes": {"type_bien": TYPES, "annee": ANNEES},
        "questions": [
            "Quel est le prix médian au m2 des biens de type {type_bien} en {annee} ?",
            "Médiane du prix au m2, type {type_bien}, année {annee} ?",
        ],
        "sql": "SELECT median(f.prix_m2) AS prix_m2_median "
        "FROM fct_ventes f "
        "JOIN dim_date d ON f.date_id = d.date_id "
        "WHERE f.type_bien = '{type_bien}' AND d.annee = {annee}",
    },
    # ---- 15 : croisement commune x nb_pieces ----
    {
        "n": 8,
        "listes": {"commune": COMMUNES, "nb_pieces": NB_PIECES},
        "questions": [
            "Quel est le prix moyen des biens de {nb_pieces} pièces à {commune} ?",
            "Prix moyen pour {nb_pieces} pièces sur {commune} ?",
        ],
        "sql": "SELECT AVG(f.prix) AS prix_moyen "
        "FROM fct_ventes f "
        "JOIN dim_commune c ON f.commune_id = c.commune_id "
        "WHERE c.nom_commune = '{commune}' AND f.nb_pieces = {nb_pieces}",
    },
]


def normalise(texte):
    return re.sub(r"\s+", " ", texte.strip().lower())


# 1. fabrication
paires = []
for t in TEMPLATES:
    for i, p in enumerate(combos(t["n"], **t["listes"])):
        p_sql = {k: q(v) for k, v in p.items()}
        paires.append(
            {
                "question": t["questions"][i % len(t["questions"])].format(**p),
                "sql": t["sql"].format(**p_sql),
            }
        )

# 2. validation
eval_questions = {
    normalise(json.loads(l)["question"])
    for l in open("data/eval.jsonl", encoding="utf-8")
}

con = connect()
gardees, vues = [], set()
rejets = {"erreur": 0, "vide": 0, "doublon_eval": 0, "doublon_interne": 0}

for paire in paires:
    nq = normalise(paire["question"])
    if nq in eval_questions:
        rejets["doublon_eval"] += 1
        continue
    if nq in vues:
        rejets["doublon_interne"] += 1
        continue
    try:
        df = con.execute(paire["sql"]).df()
    except Exception:
        rejets["erreur"] += 1
        continue
    if len(df) == 0:
        rejets["vide"] += 1
        continue
    vues.add(nq)
    gardees.append(paire)

# 3. écriture
with open("data/train.jsonl", "w", encoding="utf-8") as f:
    for paire in gardees:
        f.write(json.dumps(paire, ensure_ascii=False) + "\n")

print(f"{len(gardees)} paires gardées sur {len(paires)} fabriquées")
for motif, n in rejets.items():
    print(f"  rejet {motif} : {n}")
