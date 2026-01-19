"""
pncp_service.py
Service layer para orquestrar a coleta do PNCP e o tratamento de dados.
"""
from ..rpa.pncp_scraper_vba_logic import run_pncp_scraper_vba
from ..db.repositories import ColetasRepository
from .excel_persistence import ExcelPersistence
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

def coleta_pncp(username: str, password: str, ano_ref: str, headless: bool = True, timeout: int = 20) -> Dict[str, Any]:
    """
    Orquestra a coleta do PNCP e persiste o resultado no Banco e no Excel.
    """
    # username e password são mantidos na assinatura para compatibilidade, 
    # mas o login é manual via noVNC seguindo a lógica VBA.
    if not ano_ref:
        raise ValueError("ano_ref is required")
    
    logger.info(f"Iniciando coleta PNCP para o ano {ano_ref} (Lógica VBA)")
    
    # 1. Executa o scraper (Lógica VBA fiel)
    dados_brutos = run_pncp_scraper_vba(ano_ref=ano_ref)
    
    resultado = {
        "status": "ok" if dados_brutos else "no_data",
        "collected_data": dados_brutos,
        "ano_referencia": ano_ref
    }

    # 2. Persiste no banco de dados
    try:
        repo = ColetasRepository()
        # Salva os dados brutos coletados
        if dados_brutos:
            repo.salvar_bruto(fonte="PNCP", dados=dados_brutos)
            
            # Tenta consolidar no banco
            try:
                repo.consolidar_dados()
            except Exception as e:
                logger.error(f"Erro na consolidação PNCP no banco: {e}")
            
        resultado["_status"] = "salvo"
    except Exception as e:
        logger.exception("Erro ao salvar resultado da coleta PNCP no banco")
        resultado["_save_error"] = str(e)

    # 3. Persiste no Excel (Nova funcionalidade seguindo lógica VBA)
    try:
        logger.info("Iniciando persistência PNCP no Excel seguindo lógica VBA...")
        # Usar diretório /app/outputs mapeado via volume do Docker
        outputs_dir = "/app/outputs"
        import os
        os.makedirs(outputs_dir, exist_ok=True)
        filename = f"PGC_{ano_ref}.xlsx"
        excel_path = os.path.join(outputs_dir, filename)
        
        excel = ExcelPersistence(excel_path)
        excel.update_pncp_sheet(dados_brutos)
        logger.info("Persistência PNCP no Excel concluída com sucesso.")
    except Exception as e:
        logger.error(f"Erro na persistência PNCP no Excel: {e}")

    return resultado
