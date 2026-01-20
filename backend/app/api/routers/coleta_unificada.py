"""
Arquivo: coleta_unificada.py
Router para orquestrar as coletas PGC e PNCP em sequência.
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
import logging
from backend.app.services.pgc_service import coleta_pgc
from backend.app.services.pncp_service import coleta_pncp

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/coleta", tags=["coleta"])

class ColetaRequest(BaseModel):
    ano_ref: int

def executar_coletas_sequenciais(ano_ref: int):
    """
    Executa a coleta do PGC e, após a finalização, executa a do PNCP.
    """
    ano_str = str(ano_ref)
    
    try:
        # 1. Iniciar Coleta PGC
        logger.info(f"Iniciando sequência de coleta para o ano {ano_ref}")
        logger.info("Passo 1/2: Iniciando coleta PGC...")
        coleta_pgc(ano_str)
        logger.info("Passo 1/2: Coleta PGC finalizada com sucesso.")
        
        # 2. Iniciar Coleta PNCP (apenas após o término do PGC)
        logger.info("Passo 2/2: Iniciando coleta PNCP...")
        coleta_pncp(
            username="", 
            password="", 
            ano_ref=ano_str
        )
        logger.info("Passo 2/2: Coleta PNCP finalizada com sucesso.")
        logger.info(f"Sequência de coleta para o ano {ano_ref} concluída.")
        
    except Exception as e:
        logger.error(f"Erro durante a sequência de coleta: {e}")

@router.post("/iniciar")
async def iniciar_coleta_unificada(request: ColetaRequest, background_tasks: BackgroundTasks):
    """
    Endpoint para disparar as coletas PGC e PNCP em sequência via BackgroundTasks.
    """
    try:
        background_tasks.add_task(
            executar_coletas_sequenciais,
            request.ano_ref
        )

        return {
            "status": "started",
            "ano_ref": request.ano_ref,
            "message": "Sequência de coleta (PGC -> PNCP) iniciada. Acompanhe pelo VNC em http://localhost:7900"
        }

    except Exception as e:
        logger.error(f"Erro ao iniciar coleta unificada: {e}")
        raise HTTPException(status_code=500, detail=str(e))
