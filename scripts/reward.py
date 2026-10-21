from db import connect


def normalise(df):
    """Le résultat d'une requête, comparable : lignes triées, flottants arrondis."""

    def cell(v):
        if v is None:
            return "NULL"
        if isinstance(v, float):
            return f"{v:.2f}"
        return str(v)

    return sorted(tuple(cell(v) for v in row) for row in df.itertuples(index=False))


def reward(sql_genere, sql_reference, con):
    """1.0 si la requête générée produit le même résultat que la référence, sinon 0.0."""
    attendu = normalise(con.execute(sql_reference).df())
    try:
        obtenu = normalise(con.execute(sql_genere).df())
    except Exception:
        return 0.0
    return 1.0 if obtenu == attendu else 0.0


if __name__ == "__main__":
    import json

    con = connect()
    lignes = [json.loads(l) for l in open("data/eval.jsonl", encoding="utf-8")]
    identique = sum(reward(r["sql"], r["sql"], con) for r in lignes)
    hack = sum(reward("SELECT 1", r["sql"], con) for r in lignes)
    print(
        f"reference vs elle-meme : {identique}/{len(lignes)}  (attendu {len(lignes)})"
    )
    print(f"SELECT 1 vs reference  : {hack}/{len(lignes)}  (attendu 0)")
