"""
Script para criar o schema no banco Neon (PostgreSQL).
Cria os ENUMs e tabelas a partir dos models SQLAlchemy.
Execute: python scripts/create_neon_schema.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import Base, engine
from sqlalchemy import text
import models  # noqa: F401 - carrega todos os models

# Mapeamento de todos os ENUMs usados nos models
ENUMS = [
    ("dentist_status",     ["Ativo", "Inativo", "Ferias", "Afastado"]),
    ("appointment_status", ["agendado", "confirmado", "cancelado", "realizado", "faltou"]),
    ("expensestatus",      ["pendente", "pago", "cancelado"]),
    ("receivablestatus",   ["pendente", "parcial", "pago", "cancelado"]),
    ("procedurecategory",  ["Preventivo", "Restaurador", "Cirurgico", "Estetico",
                            "Ortodontico", "Protese", "Endodontia", "Outro"]),
]

def create_enums(conn):
    for name, values in ENUMS:
        check = conn.execute(
            text("SELECT 1 FROM pg_type WHERE typname = :name"),
            {"name": name}
        ).fetchone()
        if not check:
            vals = ", ".join(f"'{v}'" for v in values)
            conn.execute(text(f"CREATE TYPE {name} AS ENUM ({vals})"))
            print(f"  [CRIADO]   ENUM: {name}")
        else:
            print(f"  [EXISTENTE] ENUM: {name}")

print("=" * 50)
print("Criando ENUMs no Neon...")
print("=" * 50)
with engine.connect() as conn:
    create_enums(conn)
    conn.commit()

print("\nCriando tabelas...")
Base.metadata.create_all(bind=engine)
print("\nSchema criado com sucesso no Neon!")

with engine.connect() as conn:
    result = conn.execute(text(
        "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
    ))
    tables = [row[0] for row in result]
    print(f"\nTabelas no banco ({len(tables)}): {tables}")
