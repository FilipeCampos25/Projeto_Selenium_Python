"""
pgc_service.py
Service layer para orquestrar a coleta do PGC e o tratamento de dados (Item 9).
"""
import logging
from typing import Dict, Any, List
from ..rpa.pgc_scraper_vba_logic import run_pgc_scraper_vba
from ..db.repositories import ColetasRepository

logger = logging.getLogger(__name__)

def coleta_pgc(username: str, password: str, ano_ref: str) -> List[Dict[str, Any]]:
    """
    Orquestra a coleta do PGC e salva os dados brutos.
    """
    if not username or not password or not ano_ref:
        raise ValueError("username, password e ano_ref são obrigatórios.")

    logger.info("Iniciando coleta PGC (Lógica VBA)")
    
    # 1. Coletar tudo (inclusive sujo)
    dados_brutos = run_pgc_scraper_vba(username=username, password=password, ano_ref=ano_ref)
    
    if not dados_brutos:
        logger.warning("Coleta PGC não retornou dados.")
        return []

    # 2. Armazenar com flags (salvar_bruto já faz isso)
    repo = ColetasRepository()
    repo.salvar_bruto(fonte="PGC", dados=dados_brutos)
    
    # Retorna os dados brutos para visualização imediata, se necessário
    return dados_brutos

def processar_dados_brutos_pgc():
    """
    Orquestra o processamento dos dados brutos do PGC.
    Etapas 3 a 6 do Item 9: Normalizar, Deduplicar, Validar e Consolidar.
    """
    repo = ColetasRepository()
    # TODO: Implementar a lógica de busca, processamento e consolidação
    # Por enquanto, apenas chama o stub no repositório
    repo.consolidar_dados()
    logger.info("Processamento de dados brutos PGC iniciado (stub).")
    # A implementação completa do processamento será feita na próxima iteração
    # para manter o foco na arquitetura de dados brutos/consolidados.
    pass
