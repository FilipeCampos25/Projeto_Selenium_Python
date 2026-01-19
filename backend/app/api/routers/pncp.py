"""
Arquivo: pncp.py
Router para PNCP scraping seguindo a lógica VBA.
Implementação do Passo 11: Rota para execução real da coleta com paginação.
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from backend.app.services.pncp_service import coleta_pncp
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pncp", tags=["pncp"])

class PNCPRequest(BaseModel):
    ano_ref: int
    # username e password podem ser opcionais se o login for totalmente manual
    username: str = "59494964691"
    password: str = "01etpdigital"
    use_mock: bool = False # Por padrão, usar a lógica real no Passo 11

@router.post("/iniciar")
async def iniciar_coleta(request: PNCPRequest, background_tasks: BackgroundTasks):
    """
    Inicia a coleta do PNCP seguindo a lógica fiel ao VBA.
    A coleta é executada em background para não travar a API.
    """
    try:
        logger.info(f"Recebida requisição para iniciar coleta PNCP {request.ano_ref} (Mock: {request.use_mock})")
        
        # Executa em background
        background_tasks.add_task(
            coleta_pncp,
            request.username,
            request.password,
            str(request.ano_ref),
            use_mock=request.use_mock
        )
        
        return {
            "status": "started",
            "ano_ref": request.ano_ref,
            "use_mock": request.use_mock,
            "message": "Coleta PNCP iniciada com sucesso. Acompanhe pelo VNC em http://localhost:7900 (Lógica VBA Fiel)"
        }
    except Exception as e:
        logger.error(f"Erro ao iniciar coleta PNCP: {e}")
        raise HTTPException(status_code=500, detail=str(e))
