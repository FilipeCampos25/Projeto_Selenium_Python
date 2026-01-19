"""
pncp_service.py
Service layer para orquestrar a coleta do PNCP e o tratamento de dados.

HISTÓRICO DE ADAPTAÇÃO:
- Passo 11 a 19: Implementação de fidelidade, erros, logs, persistência e documentação.
- Passo 20: Desativação definitiva do mock e ativação total da implementação real.
"""
from ..rpa.pncp_scraper_vba_logic import run_pncp_scraper_vba
from ..db.repositories import ColetasRepository
from .excel_persistence import ExcelPersistence
from ..rpa.config_vba import is_pncp_real_enabled
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

def coleta_pncp(username: str, password: str, ano_ref: str, headless: bool = True, timeout: int = 20, use_mock: bool = None) -> Dict[str, Any]:
    """
    Orquestra a coleta do PNCP e persiste o resultado no Banco e no Excel.
    Implementação do Passo 20: Foco total na implementação real validada.
    """
    if not ano_ref:
        raise ValueError("ano_ref is required")
    
    # Passo 1.1: Remoção definitiva do mock.
    # A implementação real agora é a única via de execução.
    
    logger.info(f"=== [SERVICE] INICIANDO COLETA PNCP REAL - ANO {ano_ref} ===")
    
    # IMPLEMENTAÇÃO REAL VALIDADA (Lógica VBA Fiel)
    logger.info("[LOG-VBA] Executando implementação real (Passo 1.1).")
    dados_brutos = run_pncp_scraper_vba(ano_ref=ano_ref)
    
    resultado = {
        "status": "ok" if dados_brutos else "no_data",
        "total_itens": len(dados_brutos),
        "ano_referencia": ano_ref,
        "modo": "REAL"
    }

    # --- PERSISTÊNCIA NO BANCO (Passo 14) ---
    if dados_brutos:
        logger.info(f"[LOG-VBA] Persistindo {len(dados_brutos)} itens no Postgres...")
        try:
            repo = ColetasRepository()
            repo.salvar_bruto(fonte="PNCP", dados=dados_brutos)
            repo.consolidar_dados()
            resultado["_status_db"] = "consolidado"
        except Exception as e:
            logger.error(f"[ERRO-DB] Falha na persistência: {e}")
            resultado["_status_db"] = "erro"

    # --- PERSISTÊNCIA NO EXCEL (Passo 15) ---
    if dados_brutos:
        try:
            logger.info("[LOG-VBA] Atualizando Excel PGC_2025.xlsx...")
            outputs_dir = "/app/outputs"
            import os
            os.makedirs(outputs_dir, exist_ok=True)
            excel_path = os.path.join(outputs_dir, f"PGC_{ano_ref}.xlsx")
            
            excel = ExcelPersistence(excel_path)
            excel.update_pncp_sheet(dados_brutos)
            logger.info("[LOG-VBA] Excel atualizado.")
        except Exception as e:
            logger.error(f"[ERRO-EXCEL] Falha no Excel: {e}")

    return resultado
