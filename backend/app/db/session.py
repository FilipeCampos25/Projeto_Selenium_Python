"""
Arquivo: session.py
Descrição: Este arquivo faz parte do projeto e foi comentado para explicar a função de cada bloco de código.
"""

# backend/app/db/session.py

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from backend.app.db.engine import engine as _engine

# SessionLocal usando a engine carregada de engine.py
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=_engine,
    future=True
)

def get_session():
    """
    Função get_session:
    Executa a lógica principal definida nesta função.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
