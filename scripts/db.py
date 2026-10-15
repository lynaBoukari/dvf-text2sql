import duckdb

TABLES = ["fct_ventes", "dim_commune", "dim_date"]


def connect(prefix="data"):
    con = duckdb.connect()
    for t in TABLES:
        con.execute(
            f"CREATE TABLE {t} AS SELECT * FROM read_parquet('{prefix}/{t}.parquet')"
        )
    return con
