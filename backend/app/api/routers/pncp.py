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
    #username: str = "59494964691"
    #password: str = "01etpdigital"
    # use_mock agora é opcional. Se não enviado, segue a Feature Flag global.
    use_mock: Optional[bool] = None 

@router.post("/iniciar")
async def iniciar_coleta(request: PNCPRequest, background_tasks: BackgroundTasks):
    """
    Inicia a coleta do PNCP seguindo a lógica fiel ao VBA.
    Respeita a Feature Flag FEATURE_PNCP_REAL (Passo 16).
    """
    try:
        # Verifica o estado atual da Feature Flag para informar na resposta
        real_enabled = is_pncp_real_enabled()
        
        logger.info(
            f"Recebida requisição PNCP {request.ano_ref} | "
            f"Override Mock: {request.use_mock} | "
            f"Feature Flag Real: {real_enabled}"
        )
        
        # Executa em background
        background_tasks.add_task(
            coleta_pncp,
            request.username,
            request.password,
            str(request.ano_ref),
            use_mock=request.use_mock
        )
        
        # Determina o modo que será usado para informar o usuário
        modo_final = "MOCK" if (request.use_mock is True or (request.use_mock is None and not real_enabled)) else "REAL"
        
        return {
            "status": "started",
            "ano_ref": request.ano_ref,
            "modo_execucao": modo_final,
            "feature_flag_real": real_enabled,
            "message": f"Coleta PNCP iniciada no modo {modo_final}. Acompanhe pelo VNC em http://localhost:7900"
        }
    except Exception as e:
        logger.error(f"Erro ao iniciar coleta PNCP: {e}")
        raise HTTPException(status_code=500, detail=str(e))
