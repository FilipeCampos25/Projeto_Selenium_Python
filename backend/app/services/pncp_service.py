"""
pncp_service.py
Service layer para orquestrar a coleta do PNCP e o tratamento de dados.
"""
from ..rpa.pncp_scraper import login_and_search
from ..db.repositories import ColetasRepository
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

def coleta_pncp(username: str, password: str, ano_ref: str, headless: bool = True, timeout: int = 20) -> Dict[str, Any]:
    """
    Orquestra a coleta do PNCP e persiste o resultado.
    """
    if not username or not password:
        raise ValueError("username and password are required")
    if not ano_ref:
        raise ValueError("ano_ref is required")

    logger.info(f"Iniciando coleta PNCP para o ano {ano_ref}")
    
    # 1. Executa o scraper
    resultado = login_and_search(
        username=username, 
        password=password, 
        ano_ref=ano_ref, 
        headless=headless, 
        timeout=timeout
    )

    # 2. Persiste no banco de dados
    try:
        repo = ColetasRepository()
        # O scraper PNCP retorna um dict com metadados e possivelmente uma lista de itens
        # Vamos salvar o resultado completo como bruto
        repo.salvar_bruto(fonte="PNCP", dados=[resultado])
        
        # 3. Tenta consolidar
        try:
            repo.consolidar_dados()
        except Exception as e:
            logger.error(f"Erro na consolidação PNCP: {e}")
            
        resultado["_status"] = "salvo"
    except Exception as e:
        logger.exception("Erro ao salvar resultado da coleta PNCP")
        resultado["_save_error"] = str(e)

    return resultado
