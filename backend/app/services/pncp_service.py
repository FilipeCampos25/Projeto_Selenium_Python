"""
pncp_service.py
Service layer para orquestrar a coleta do PNCP e o tratamento de dados.

HISTÓRICO DE ADAPTAÇÃO:
- Passo 11: Ativação da lógica real com paginação fiel ao VBA.
- Passo 14: Ativação controlada da persistência no banco após validação.
"""
from ..rpa.pncp_scraper_vba_logic import run_pncp_scraper_vba
from ..db.repositories import ColetasRepository
from .excel_persistence import ExcelPersistence
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

def coleta_pncp(username: str, password: str, ano_ref: str, headless: bool = True, timeout: int = 20, use_mock: bool = False) -> Dict[str, Any]:
    """
    Orquestra a coleta do PNCP e persiste o resultado no Banco e no Excel.
    Implementação do Passo 14: Ativação controlada da persistência no banco.
    """
    if not ano_ref:
        raise ValueError("ano_ref is required")
    
    logger.info(f"=== [SERVICE] INICIANDO ORQUESTRAÇÃO PNCP - ANO {ano_ref} ===")
    
    dados_brutos: List[Dict[str, Any]] = []
    
    # --- ESCOLHA DA FONTE DE DADOS ---
    if use_mock:
        logger.info("[LOG-VBA] Utilizando MOCK para coleta PNCP (Modo de Teste)")
        dados_brutos = [
            {
                "col_a_contratacao": "MOCK-001/2025",
                "col_b_descricao": "ITEM MOCK PARA TESTE DE FLUXO",
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
        # IMPLEMENTAÇÃO REAL (Lógica VBA fiel com Paginação do Passo 11 e Erros do Passo 12)
        logger.info("[LOG-VBA] Iniciando implementação real (Lógica VBA Fiel - Passo 11/12/13)")
        dados_brutos = run_pncp_scraper_vba(ano_ref=ano_ref)
    
    resultado = {
        "status": "ok" if dados_brutos else "no_data",
        "total_itens": len(dados_brutos),
        "ano_referencia": ano_ref,
        "is_mock": use_mock
    }

    # --- PASSO 14: ATIVAÇÃO CONTROLADA DA PERSISTÊNCIA NO BANCO ---
    # Só habilitar o salvamento definitivo no Postgres após todos os campos estarem coletados e validados.
    if dados_brutos:
        logger.info(f"[LOG-VBA] Iniciando persistência controlada de {len(dados_brutos)} itens no Banco de Dados...")
        try:
            repo = ColetasRepository()
            
            # 1. Salva os dados brutos (Histórico de Coleta)
            # VBA: Equivalente ao armazenamento temporário antes do processamento
            repo.salvar_bruto(fonte="PNCP", dados=dados_brutos)
            
            # 2. Consolidação e Upsert na tabela PNCP (Mapeamento Passo 4)
            # O método consolidar_dados() em repositories.py já trata o mapeamento fiel.
            try:
                logger.info("[LOG-VBA] Consolidando dados na tabela PNCP (Mapeamento VBA x Postgres)...")
                repo.consolidar_dados()
                resultado["_status_db"] = "consolidado"
            except Exception as e:
                logger.error(f"[ERRO-DB] Falha na consolidação PNCP no banco: {e}")
                resultado["_status_db"] = "erro_consolidacao"
            
        except Exception as e:
            logger.exception("[ERRO-DB] Erro crítico ao salvar resultado da coleta PNCP no banco")
            resultado["_status_db"] = "erro_persistência"
            resultado["_db_error"] = str(e)
    else:
        logger.warning("[AVISO-VBA] Nenhum dado coletado para persistir no banco.")

    # --- PERSISTÊNCIA NO EXCEL (Mantendo lógica VBA) ---
    # Implementado conforme Passo 15 (será refinado no próximo passo, mas já funcional)
    try:
        if dados_brutos:
            logger.info("[LOG-VBA] Iniciando persistência PNCP no Excel (PGC_2025.xlsx)...")
            outputs_dir = "/app/outputs"
            import os
            os.makedirs(outputs_dir, exist_ok=True)
            filename = f"PGC_{ano_ref}.xlsx"
            excel_path = os.path.join(outputs_dir, filename)
            
            excel = ExcelPersistence(excel_path)
            excel.update_pncp_sheet(dados_brutos)
            logger.info(f"[LOG-VBA] Persistência Excel concluída: {filename}")
    except Exception as e:
        logger.error(f"[ERRO-EXCEL] Falha na persistência PNCP no Excel: {e}")

    return resultado
