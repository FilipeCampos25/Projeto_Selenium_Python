"""
pgc_service.py
Service layer para orquestrar a coleta do PGC e o tratamento de dados.
MODIFICADO PARA EXECUÇÃO LOCAL.
"""
import logging
import os
from typing import Dict, Any, List
from ..rpa.pgc_scraper_vba_logic import run_pgc_scraper_vba

# ============================================================
# 🔴 INÍCIO MODIFICAÇÃO LOCAL - REMOVER QUANDO VOLTAR DOCKER
# ============================================================
# Importar ColetasRepository de forma segura (pode falhar em modo local)
try:
    from ..db.repositories import ColetasRepository
    POSTGRES_AVAILABLE = True
except Exception:
    ColetasRepository = None
    POSTGRES_AVAILABLE = False
# ============================================================
# 🔴 FIM MODIFICAÇÃO LOCAL
# ============================================================

from .excel_persistence import ExcelPersistence

logger = logging.getLogger(__name__)

def coleta_pgc(ano_ref: str, driver=None, close_driver: bool = True) -> List[Dict[str, Any]]:
    """
    Orquestra a coleta do PGC e salva os dados no Excel.
    MODIFICADO PARA EXECUÇÃO LOCAL - Postgres desabilitado.
    """
    if not ano_ref:
        raise ValueError("ano_ref é obrigatório.")

    logger.info(f"[LOCAL] Iniciando coleta PGC para o ano {ano_ref}")
    
    # 1. Coletar dados via Scraper (Lógica VBA)
    dados_brutos = run_pgc_scraper_vba(ano_ref=ano_ref, driver=driver, close_driver=close_driver)
    
    if not dados_brutos:
        logger.warning("[LOCAL] Coleta PGC não retornou dados.")
        return []

    # ============================================================
    # 🔴 INÍCIO MODIFICAÇÃO LOCAL - REMOVER QUANDO VOLTAR DOCKER
    # ============================================================
    
    # 2. Armazenar em JSON temporário (Postgres desabilitado)
    try:
        repo = ColetasRepository()
        repo.salvar_bruto(fonte="PGC", dados=dados_brutos)
        logger.info("[LOCAL] ✅ Dados salvos em JSON temporário")
        
        # Consolidação desabilitada em modo local
        # repo.consolidar_dados()
        
    except Exception as e:
        logger.error(f"[LOCAL] ❌ Erro na persistência JSON: {e}")

    # 3. Armazenar no Excel (MODIFICADO - caminho local)
    try:
        logger.info("[LOCAL] Iniciando persistência no Excel...")
        
        # Usar diretório local
        outputs_dir = os.path.join(os.getcwd(), "outputs_local")
        os.makedirs(outputs_dir, exist_ok=True)
        filename = f"PGC_{ano_ref}.xlsx"
        excel_path = os.path.join(outputs_dir, filename)

        excel = ExcelPersistence(excel_path)
        excel.update_pgc_sheet(dados_brutos)
        excel.sync_to_geral()
        
        logger.info(f"[LOCAL] ✅ Excel salvo com sucesso!")
        logger.info(f"[LOCAL] 📁 Arquivo: {excel_path}")
        logger.info(f"[LOCAL] 📂 Abra a pasta: {outputs_dir}")
        
    except Exception as e:
        logger.error(f"[LOCAL] ❌ Erro na persistência Excel: {e}")
    
    # ============================================================
    # 🔴 FIM MODIFICAÇÃO LOCAL
    # ============================================================
    
    # CÓDIGO ORIGINAL DOCKER (DESCOMENTAR QUANDO VOLTAR):
    # try:
    #     repo = ColetasRepository()
    #     repo.salvar_bruto(fonte="PGC", dados=dados_brutos)
    #     logger.info("Iniciando consolidação automática...")
    #     repo.consolidar_dados()
    #     logger.info("Consolidação no banco concluída.")
    # except Exception as e:
    #     logger.error(f"Erro na persistência ou consolidação: {e}")
    #
    # try:
    #     outputs_dir = "/app/outputs"
    #     os.makedirs(outputs_dir, exist_ok=True)
    #     filename = f"PGC_{ano_ref}.xlsx"
    #     excel_path = os.path.join(outputs_dir, filename)
    #     excel = ExcelPersistence(excel_path)
    #     excel.update_pgc_sheet(dados_brutos)
    #     excel.sync_to_geral()
    # except Exception as e:
    #     logger.error(f"Erro na persistência Excel: {e}")

    return dados_brutos

def processar_dados_brutos_pgc():
    """
    Orquestra o processamento manual dos dados brutos do PGC.
    DESABILITADO EM MODO LOCAL.
    """
    # ============================================================
    # 🔴 INÍCIO MODIFICAÇÃO LOCAL
    # ============================================================
    
    logger.warning("[LOCAL] Processamento manual desabilitado (sem Postgres)")
    return
    
    # ============================================================
    # 🔴 FIM MODIFICAÇÃO LOCAL
    # ============================================================
    
    # CÓDIGO ORIGINAL (DESCOMENTAR QUANDO VOLTAR DOCKER):
    # repo = ColetasRepository()
    # repo.consolidar_dados()
    # logger.info("Processamento manual de dados brutos PGC concluído.")
