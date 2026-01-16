"""
pgc_service.py
Service layer para orquestrar a coleta do PGC e o tratamento de dados.
"""
import logging
import os
from typing import Dict, Any, List
from ..rpa.pgc_scraper_vba_logic import run_pgc_scraper_vba
from ..db.repositories import ColetasRepository
from .excel_persistence import ExcelPersistence

logger = logging.getLogger(__name__)

def coleta_pgc(ano_ref: str) -> List[Dict[str, Any]]:
    """
    Orquestra a coleta do PGC e salva os dados brutos no Banco e no Excel.
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
    try:
        repo = ColetasRepository()
        repo.salvar_bruto(fonte="PGC", dados=dados_brutos)
        
        # Consolidar dados imediatamente após a coleta no banco
        logger.info("Iniciando consolidação automática dos dados coletados no banco...")
        repo.consolidar_dados()
        logger.info("Consolidação no banco concluída com sucesso.")
    except Exception as e:
        logger.error(f"Erro na persistência ou consolidação no banco: {e}")

    # 3. Armazenar no Excel (Nova funcionalidade seguindo lógica VBA)
    try:
        logger.info("Iniciando persistência no Excel seguindo lógica VBA...")
        # Usar diretório /app/outputs mapeado via volume do Docker
        outputs_dir = "/app/outputs"
        os.makedirs(outputs_dir, exist_ok=True)
        filename = f"PGC_{ano_ref}.xlsx"
        excel_path = os.path.join(outputs_dir, filename)

        excel = ExcelPersistence(excel_path)
        excel.update_pgc_sheet(dados_brutos)
        excel.sync_to_geral()
        logger.info(f"✅ Persistência no Excel concluída com sucesso!")
        logger.info(f"📁 Arquivo salvo em: {excel_path}")
        logger.info(f"📂 Acesse em: ./outputs/{filename}")
    except Exception as e:
        logger.error(f"Erro na persistência Excel: {e}")

    return dados_brutos

def processar_dados_brutos_pgc():
    """
    Orquestra o processamento manual dos dados brutos do PGC.
    """
    repo = ColetasRepository()
    repo.consolidar_dados()
    logger.info("Processamento manual de dados brutos PGC concluído.")
