"""
pgc_service.py
Service layer para orquestrar a coleta do PGC e o tratamento de dados (Item 9).
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

    logger.info("Iniciando coleta PGC (Lógica VBA - Login Manual)")
    
    # 1. Coletar tudo (inclusive sujo)
    dados_brutos = run_pgc_scraper_vba(ano_ref=ano_ref)
    
    if not dados_brutos:
        logger.warning("Coleta PGC não retornou dados.")
        return []

    # 2. Armazenar com flags (salvar_bruto já faz isso)
    repo = ColetasRepository()
    repo.salvar_bruto(fonte="PGC", dados=dados_brutos)
    
    # 3. Inicia processamento automático após coleta (Opcional, mas recomendado pelo fluxo)
    try:
        repo.consolidar_dados()
    except Exception as e:
        logger.error(f"Erro na consolidação automática pós-coleta: {e}")

    # Retorna os dados brutos para visualização imediata, se necessário
    return dados_brutos

def processar_dados_brutos_pgc():
    """
    Orquestra o processamento dos dados brutos do PGC.
    Etapas 3 a 6 do Item 9: Normalizar, Deduplicar, Validar e Consolidar.
    """
    repo = ColetasRepository()
    # Chama a consolidação no repositório
    repo.consolidar_dados()
    logger.info("Processamento de dados brutos PGC concluído.")
