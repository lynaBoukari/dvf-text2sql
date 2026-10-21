import json

from db import connect

con = connect()
ok = err = vide = 0

for i, line in enumerate(open("data/eval.jsonl", encoding="utf-8"), 1):
    row = json.loads(line)
    tag = " [ambigu]" if row.get("ambigu") else ""
    print(f"--- {i}{tag}  {row['question']}")
    try:
        df = con.execute(row["sql"]).df()
    except Exception as e:
        print(f"    ERREUR  {type(e).__name__}: {e}\n")
        err += 1
        continue
    if len(df) == 0:
        print("    VIDE\n")
        vide += 1
        continue
    print(df.head(5).to_string(index=False), "\n")
    ok += 1

print(f"{ok} ok, {vide} vides, {err} erreurs")
