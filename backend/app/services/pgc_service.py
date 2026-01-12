"""
pgc_service.py
Service layer para orquestrar a coleta do PGC e o tratamento de dados.
"""
import logging
from typing import Dict, Any, List
from ..rpa.pgc_scraper_vba_logic import run_pgc_scraper_vba
from ..db.repositories import ColetasRepository

logger = logging.getLogger(__name__)

def coleta_pgc(ano_ref: str) -> List[Dict[str, Any]]:
    """
    Orquestra a coleta do PGC e salva os dados brutos.
    """
    if not ano_ref:
        raise ValueError("ano_ref é obrigatório.")

    logger.info(f"Iniciando coleta PGC para o ano {ano_ref}")
    
    # 1. Coletar dados via Scraper (Lógica VBA)
    dados_brutos = run_pgc_scraper_vba(ano_ref=ano_ref)
    
    if not dados_brutos:
        logger.warning("Coleta PGC não retornou dados.")
        return []

    # 2. Armazenar no banco de dados
    repo = ColetasRepository()
    repo.salvar_bruto(fonte="PGC", dados=dados_brutos)
    
    # 3. Consolidar dados imediatamente após a coleta
    try:
        logger.info("Iniciando consolidação automática dos dados coletados...")
        repo.consolidar_dados()
        logger.info("Consolidação concluída com sucesso.")
    except Exception as e:
        logger.error(f"Erro na consolidação automática pós-coleta: {e}")

    return dados_brutos

def processar_dados_brutos_pgc():
    """
    Orquestra o processamento manual dos dados brutos do PGC.
    """
    repo = ColetasRepository()
    repo.consolidar_dados()
    logger.info("Processamento manual de dados brutos PGC concluído.")
