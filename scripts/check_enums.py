import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text(
        "SELECT t.typname, e.enumlabel "
        "FROM pg_type t JOIN pg_enum e ON t.oid = e.enumtypid "
        "ORDER BY t.typname, e.enumsortorder"
    ))
    rows = result.fetchall()
    current = None
    for typname, label in rows:
        if typname != current:
            print(f"\n{typname}:")
            current = typname
        print(f"  - '{label}'")
