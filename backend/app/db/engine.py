"""
engine.py
Configuração do engine SQLAlchemy com suporte a inicialização robusta.
"""

import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

def get_database_url():
    """Resolve a URL do banco de dados priorizando variáveis de ambiente."""
    url = (
        os.getenv("DATABASE_URL")
        or os.getenv("DATABASE_URI")
        or os.getenv("DB_URL")
    )
    
    # ============================================================
    # 🔴 INÍCIO MODIFICAÇÃO LOCAL - REMOVER QUANDO VOLTAR DOCKER
    # ============================================================
    # Se a URL for "disabled", retorna None (modo local sem Postgres)
    if url == "disabled":
        logger.warning("⚠️  Modo LOCAL: Database desabilitado (DATABASE_URL=disabled)")
        return None
    # ============================================================
    # 🔴 FIM MODIFICAÇÃO LOCAL
    # ============================================================
    
    if not url:
        # Fallback para Docker Compose padrão
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "postgres")
        host = os.getenv("POSTGRES_HOST", "db")
        port = os.getenv("POSTGRES_PORT", "5432")
        db = os.getenv("POSTGRES_DB", "projeto")
        url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
        logger.warning(f"DATABASE_URL não definida. Usando fallback: {url}")
    
    # Garante que use o driver psycopg2 se for postgres
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
        
    return url

DATABASE_URL = get_database_url()

# ============================================================
# 🔴 INÍCIO MODIFICAÇÃO LOCAL - REMOVER QUANDO VOLTAR DOCKER
# ============================================================
# Cria engine global apenas se DATABASE_URL estiver definida
if DATABASE_URL:
    engine: Engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
        max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
        future=True,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
else:
    # Modo local: engine e SessionLocal são None
    engine: Engine = None
    SessionLocal = None
    logger.warning("⚠️  Engine SQLAlchemy não inicializado (modo local)")
# ============================================================
# 🔴 FIM MODIFICAÇÃO LOCAL
# ============================================================

def get_engine() -> Engine:
    """Retorna o engine compartilhado."""
    if engine is None:
        raise RuntimeError("Database engine não está inicializado. Você está em modo LOCAL?")
    return engine

def get_db_session():
    """Dependency para FastAPI."""
    if SessionLocal is None:
        raise RuntimeError("Database session não está disponível. Você está em modo LOCAL?")
