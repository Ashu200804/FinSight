import pathlib
import sqlite3

for name in ("backend/local_run.db", "local_run.db"):
    db = pathlib.Path(name)
    if not db.exists():
        continue
    print("DB", db)
    con = sqlite3.connect(str(db))
    cur = con.cursor()
    print("tables", cur.execute("select name from sqlite_master where type='table' and name like 'explanation%' order by name").fetchall())
    try:
        rows = cur.execute(
            "select id, entity_id, credit_score, credit_rating, decision, created_at from explanation_models order by created_at desc limit 5"
        ).fetchall()
        print("rows", rows)
    except Exception as exc:
        print("query_err", exc)
    con.close()
