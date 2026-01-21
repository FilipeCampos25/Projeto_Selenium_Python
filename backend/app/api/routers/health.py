"""
Arquivo: health.py
Descrição: Este arquivo faz parte do projeto e foi comentado para explicar a função de cada bloco de código.
"""

import os
from fastapi import APIRouter

router = APIRouter()

@router.get("/ready")
def ready():
    """
    Função ready:
    Executa a lógica principal definida nesta função.
    """
    # ============================================================
    # 🔴 INÍCIO MODIFICAÇÃO LOCAL - REMOVER QUANDO VOLTAR DOCKER
    # ============================================================
    # Retornar informação de modo (local ou docker)
    modo = "local" if os.getenv("SELENIUM_MODE") == "local" else "docker"
    return {"status": "ok", "mode": modo}
    # ============================================================
    # 🔴 FIM MODIFICAÇÃO LOCAL
    # ============================================================
