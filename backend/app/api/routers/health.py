"""
Arquivo: health.py
Descrição: Este arquivo faz parte do projeto e foi comentado para explicar a função de cada bloco de código.
"""

from fastapi import APIRouter
router = APIRouter()
@router.get("/ready")
def ready():
    """
    Função ready:
    Executa a lógica principal definida nesta função.
    """
    return {"status":"ok"}
