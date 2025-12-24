"""
Arquivo: engine.py
Descrição: Este arquivo faz parte do projeto e foi comentado para explicar a função de cada bloco de código.
"""

# backend/app/db/engine.py
# Robust engine factory: aceita DATABASE_URL via env; se não existir, usa fallback
# e não levanta exceção durante import (evita break no startup do uvicorn).

import os
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
import logging

logger = logging.getLogger(__name__)

# Tentativas em ordem: env padrão, env alternativa, fallback igual ao session.py
DATABASE_URL = (
    os.getenv("DATABASE_URL")
    or os.getenv("DATABASE_URI")
    or os.getenv("DB_URL")
    or os.getenv("DATABASE_URL_FALLBACK")
)

if not DATABASE_URL:
    # Fallback (desenvolvimento/compose): mantido igual ao session.py para compatibilidade.
    # Ajuste este valor se seu docker-compose usar outro usuário/senha/db.
    DATABASE_URL = "postgresql+psycopg2://user:password@db:5432/projeto"
    logger.warning(
        "DATABASE_URL não definida — usando fallback de desenvolvimento. "
        "Defina a variável DATABASE_URL em produção."
    )

# Cria engine global (pool de conexões do SQLAlchemy)
# Configurações conservadoras para evitar exaustão de conexões
_engine: Engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
    future=True,
)

engine = _engine

# Session maker opcional
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine, future=True)

def get_engine() -> Engine:
    """
    Função get_engine:
    Executa a lógica principal definida nesta função.
    """
    """Retorna o engine compartilhado do projeto."""
    return _engine

def get_db_session():
    """
    Função get_db_session:
    Executa a lógica principal definida nesta função.
    """
    """Yield a session (use em dependências FastAPI se precisar)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        