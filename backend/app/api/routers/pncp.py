"""
Arquivo: pncp.py
Router para PNCP scraping seguindo a lógica VBA.
Implementação do Passo 16: Suporte a Feature Flags na rota da API.
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.app.services.pncp_service import coleta_pncp
from backend.app.rpa.config_vba import is_pncp_real_enabled
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pncp", tags=["pncp"])

class PNCPRequest(BaseModel):
    ano_ref: int
    # username e password são tratados internamente ou via login manual no VNC

@router.post("/iniciar")
async def iniciar_coleta(request: PNCPRequest, background_tasks: BackgroundTasks):
    """
    Inicia a coleta do PNCP seguindo a lógica fiel ao VBA.
    Passo 1.1: Mock desativado definitivamente.
    """
    try:
        logger.info(f"Recebida requisição PNCP Real para o ano {request.ano_ref}")
        
        # Executa em background
        background_tasks.add_task(
            coleta_pncp,
            "", # username (login manual)
            "", # password (login manual)
            str(request.ano_ref)
        )
        
        return {
            "status": "started",
            "ano_ref": request.ano_ref,
            "modo_execucao": "REAL",
            "message": f"Coleta PNCP REAL iniciada para o ano {request.ano_ref}. Acompanhe pelo VNC em http://localhost:7900"
        }
    except Exception as e:
        logger.error(f"Erro ao iniciar coleta PNCP: {e}")
        raise HTTPException(status_code=500, detail=str(e))
