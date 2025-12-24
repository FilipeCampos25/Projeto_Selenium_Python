"""
Arquivo: pncp_service.py
Descrição: Este arquivo faz parte do projeto e foi comentado para explicar a função de cada bloco de código.
"""

# backend/app/services/pncp_service.py
from ..rpa.pncp_scraper import login_and_search
from ..db import repositories
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

def coleta_pncp(username: str, password: str, ano_ref: str, headless: bool = True, timeout: int = 20) -> Dict[str, Any]:
    """
    Função coleta_pncp:
    Executa a lógica principal definida nesta função.
    """
    """
    Service layer: validate inputs, call the scraper and persist result (persistence is non-blocking stub).
    """
    if not username or not password:
        raise ValueError("username and password are required")
    if not ano_ref:
        raise ValueError("ano_ref is required")

    logger.info("Starting PNCP collection")
    resultado = login_and_search(username=username, password=password, ano_ref=ano_ref, headless=headless, timeout=timeout)

    # persist (stub). repositories.salvar_pncp should accept (payload: dict) and save to DB or file.
    try:
        saved_id = repositories.salvar_pncp(resultado)
        resultado["_saved_id"] = saved_id
    except Exception as e:
        logger.exception("Error saving coleta result")
        resultado["_save_error"] = str(e)

    return resultado
