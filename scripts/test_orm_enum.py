import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.database import engine
from sqlalchemy import text
from sqlalchemy.orm import Session
from models.dentist import Dentist, DentistStatus

with engine.connect() as conn:
    # Check current dentist_status labels
    res = conn.execute(text("""
        SELECT e.enumlabel
        FROM pg_type t
        JOIN pg_enum e ON t.oid = e.enumtypid
        WHERE t.typname = 'dentist_status'
        ORDER BY e.enumsortorder;
    """)).fetchall()
    print("Postgres dentist_status labels:", [r[0] for r in res])

with Session(engine) as db:
    try:
        count = db.query(Dentist).filter(Dentist.status == DentistStatus.ATIVO).count()
        print("Query with DentistStatus.ATIVO:", count)
    except Exception as e:
        print("Query with DentistStatus.ATIVO error:", e)

    try:
        count = db.query(Dentist).filter(Dentist.status == DentistStatus.ATIVO.value).count()
        print("Query with DentistStatus.ATIVO.value:", count)
    except Exception as e:
        print("Query with DentistStatus.ATIVO.value error:", e)
