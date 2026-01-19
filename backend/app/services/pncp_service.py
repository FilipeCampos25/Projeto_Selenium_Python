"""
pncp_service.py
Service layer para orquestrar a coleta do PNCP e o tratamento de dados.

HISTÓRICO DE ADAPTAÇÃO:
- Passo 11: Ativação da lógica real com paginação fiel ao VBA.
- Passo 14: Ativação controlada da persistência no banco após validação.
- Passo 16: Implementação de Feature Flag para alternar entre Mock e Real.
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
    Implementação do Passo 16: Respeita a Feature Flag FEATURE_PNCP_REAL.
    """
    if not ano_ref:
        raise ValueError("ano_ref is required")
    
    # Lógica da Feature Flag (Passo 16)
    # Se use_mock for passado explicitamente na chamada (ex: via API), ele tem precedência.
    # Caso contrário, usa o valor da Feature Flag global.
    real_enabled = is_pncp_real_enabled()
    
    # Se use_mock for True, força mock. Se for False, força real. 
    # Se for None, segue a Feature Flag (Se real_enabled=True -> use_mock=False)
    final_use_mock = use_mock if use_mock is not None else (not real_enabled)
    
    logger.info(f"=== [SERVICE] INICIANDO ORQUESTRAÇÃO PNCP - ANO {ano_ref} ===")
    logger.info(f"[LOG-VBA] Feature Flag PNCP_REAL: {real_enabled} | Modo Final Mock: {final_use_mock}")
    
    dados_brutos: List[Dict[str, Any]] = []
    
    # --- ESCOLHA DA FONTE DE DADOS ---
    if final_use_mock:
        logger.info("[LOG-VBA] Utilizando MOCK para coleta PNCP (Modo de Teste/Segurança)")
        dados_brutos = [
            {
                "col_a_contratacao": "MOCK-001/2025",
                "col_b_descricao": "ITEM MOCK PARA TESTE DE FLUXO (FEATURE FLAG ATIVA)",
                "col_c_categoria": "Serviços",
                "col_d_valor": 1000.00,
                "col_e_inicio": "2025-01-01",
                "col_f_fim": "2025-12-31",
                "col_g_status": "MOCK",
                "col_h_status_tipo": "MOCK",
                "col_i_dfd": "000/2025"
            }
        ]
    else:
        # IMPLEMENTAÇÃO REAL (Lógica VBA fiel com Passos 11, 12 e 13)
        logger.info("[LOG-VBA] Iniciando implementação real (Lógica VBA Fiel - Passo 16)")
        dados_brutos = run_pncp_scraper_vba(ano_ref=ano_ref)
    
    resultado = {
        "status": "ok" if dados_brutos else "no_data",
        "total_itens": len(dados_brutos),
        "ano_referencia": ano_ref,
        "is_mock": final_use_mock,
        "feature_flag_real": real_enabled
    }

    # --- PERSISTÊNCIA CONTROLADA (Passo 14) ---
    if dados_brutos:
        logger.info(f"[LOG-VBA] Iniciando persistência controlada de {len(dados_brutos)} itens...")
        try:
            repo = ColetasRepository()
            repo.salvar_bruto(fonte="PNCP", dados=dados_brutos)
            
            try:
                logger.info("[LOG-VBA] Consolidando dados na tabela PNCP...")
                repo.consolidar_dados()
                resultado["_status_db"] = "consolidado"
            except Exception as e:
                logger.error(f"[ERRO-DB] Falha na consolidação: {e}")
                resultado["_status_db"] = "erro_consolidacao"
            
        except Exception as e:
            logger.exception("[ERRO-DB] Erro crítico na persistência")
            resultado["_status_db"] = "erro_persistência"

    # --- PERSISTÊNCIA NO EXCEL (Passo 15) ---
    try:
        if dados_brutos:
            logger.info("[LOG-VBA] Atualizando Excel (PGC_2025.xlsx)...")
            outputs_dir = "/app/outputs"
            import os
            os.makedirs(outputs_dir, exist_ok=True)
            filename = f"PGC_{ano_ref}.xlsx"
            excel_path = os.path.join(outputs_dir, filename)
            
            excel = ExcelPersistence(excel_path)
            excel.update_pncp_sheet(dados_brutos)
            logger.info(f"[LOG-VBA] Excel atualizado com sucesso.")
    except Exception as e:
        logger.error(f"[ERRO-EXCEL] Falha no Excel: {e}")

    return resultado
