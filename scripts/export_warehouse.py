import pathlib

from google.cloud import bigquery

PROJECT = "project-119b887b-87ca-43ee-bf0"
client = bigquery.Client(project=PROJECT)
out = pathlib.Path("data")
out.mkdir(exist_ok=True)

for t in ["fct_ventes", "dim_commune", "dim_date"]:
    df = client.query(f"SELECT * FROM `{PROJECT}.dvf_marts.{t}`").to_dataframe()
    df.to_parquet(out / f"{t}.parquet", index=False)
    print(t, len(df))
