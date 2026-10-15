from db import TABLES, connect

con = connect()
for t in TABLES:
    print(f"-- {t}")
    print(con.execute(f"DESCRIBE {t}").df().to_string(index=False))
    print()
