"""
Módulo de banco de dados.
"""
from .engine import engine, SessionLocal, get_db_session

# ============================================================
# 🔴 INÍCIO MODIFICAÇÃO LOCAL - REMOVER QUANDO VOLTAR DOCKER
# ============================================================
# ColetasRepository só é importado se o engine estiver ativo
try:
    from .repositories import ColetasRepository
    __all__ = ["engine", "SessionLocal", "get_db_session", "ColetasRepository"]
except Exception as e:
    # Modo local: repositories não pode ser importado sem engine
    __all__ = ["engine", "SessionLocal", "get_db_session"]
# ============================================================
# 🔴 FIM MODIFICAÇÃO LOCAL
# ============================================================
