import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.database import engine
from sqlalchemy import text

# Testar a query diretamente com o value correto
with engine.connect() as conn:
    # Testa com string literal minuscula (correto)
    result = conn.execute(text(
        "SELECT COUNT(*) FROM appointments WHERE status = :s"
    ), {"s": "realizado"})
    print("Query com 'realizado':", result.scalar())

    # Testa com string literal maiuscula (errado - deve dar erro)
    try:
        result2 = conn.execute(text(
            "SELECT COUNT(*) FROM appointments WHERE status = :s"
        ), {"s": "REALIZADO"})
        print("Query com 'REALIZADO':", result2.scalar())
    except Exception as e:
        print("Erro esperado com 'REALIZADO':", type(e).__name__)
