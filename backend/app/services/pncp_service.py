"""
pncp_service.py
Service layer para orquestrar a coleta do PNCP e o tratamento de dados.
MODIFICADO PARA EXECUÇÃO LOCAL.
"""
from ..rpa.pncp_scraper_vba_logic import run_pncp_scraper_vba
from ..db.repositories import ColetasRepository
from .excel_persistence import ExcelPersistence
from typing import Dict, Any, List
import logging
import os

logger = logging.getLogger(__name__)

def coleta_pncp(username: str, password: str, ano_ref: str, headless: bool = False, timeout: int = 20, use_mock: bool = None) -> Dict[str, Any]:
    """
    Orquestra a coleta do PNCP e persiste o resultado no Excel.
    MODIFICADO PARA EXECUÇÃO LOCAL - Postgres desabilitado.
    """
    if not ano_ref:
        raise ValueError("ano_ref is required")
    
    logger.info(f"[LOCAL] INICIANDO COLETA PNCP - ANO {ano_ref}")
    
    # Execução real
    dados_brutos = run_pncp_scraper_vba(ano_ref=ano_ref)
    
    resultado = {
        "status": "ok" if dados_brutos else "no_data",
        "total_itens": len(dados_brutos),
        "ano_referencia": ano_ref,
        "modo": "REAL_LOCAL"
    }

    # ============================================================
    # 🔴 INÍCIO MODIFICAÇÃO LOCAL - REMOVER QUANDO VOLTAR DOCKER
    # ============================================================
    
    # Persistência em JSON temporário
    if dados_brutos:
        logger.info(f"[LOCAL] Persistindo {len(dados_brutos)} itens em JSON...")
        try:
            repo = ColetasRepository()
            repo.salvar_bruto(fonte="PNCP", dados=dados_brutos)
            # repo.consolidar_dados()  # Desabilitado em modo local
            resultado["_status_db"] = "json_local"
        except Exception as e:
            logger.error(f"[LOCAL] ❌ Erro na persistência JSON: {e}")
            resultado["_status_db"] = "erro"

    # Persistência em Excel LOCAL
    if dados_brutos:
        try:
            logger.info("[LOCAL] Atualizando Excel...")
            
            outputs_dir = os.path.join(os.getcwd(), "outputs_local")
            os.makedirs(outputs_dir, exist_ok=True)
            excel_path = os.path.join(outputs_dir, f"PGC_{ano_ref}.xlsx")
            
            excel = ExcelPersistence(excel_path)
            excel.update_pncp_sheet(dados_brutos)
            
            logger.info(f"[LOCAL] ✅ Excel atualizado: {excel_path}")
            
        except Exception as e:
            logger.error(f"[LOCAL] ❌ Erro no Excel: {e}")
    
    # ============================================================
    # 🔴 FIM MODIFICAÇÃO LOCAL
    # ============================================================
    
    # CÓDIGO ORIGINAL DOCKER (DESCOMENTAR QUANDO VOLTAR):
    # if dados_brutos:
    #     try:
    #         repo = ColetasRepository()
    #         repo.salvar_bruto(fonte="PNCP", dados=dados_brutos)
    #         repo.consolidar_dados()
    #         resultado["_status_db"] = "consolidado"
    #     except Exception as e:
    #         resultado["_status_db"] = "erro"
    #
    # if dados_brutos:
    #     try:
    #         outputs_dir = "/app/outputs"
    #         excel_path = os.path.join(outputs_dir, f"PGC_{ano_ref}.xlsx")
    #         excel = ExcelPersistence(excel_path)
    #         excel.update_pncp_sheet(dados_brutos)
    #     except Exception as e:
    #         logger.error(f"[ERRO-EXCEL] Falha: {e}")

    return resultado