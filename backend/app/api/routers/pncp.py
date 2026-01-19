"""
Arquivo: pncp.py
Router para PNCP scraping seguindo a lógica VBA.
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from backend.app.services.pncp_service import coleta_pncp

router = APIRouter(prefix="/api/pncp", tags=["pncp"])

class PNCPRequest(BaseModel):
    ano_ref: int
    # username e password podem ser opcionais se o login for totalmente manual
    username: str = "59494964691"
    password: str = "01etpdigital"

@router.post("/iniciar")
async def iniciar_coleta(request: PNCPRequest, background_tasks: BackgroundTasks):
    try:
        # Executa em background
        background_tasks.add_task(
            coleta_pncp,
            request.username,
            request.password,
            str(request.ano_ref)
        )
        return {
            "status": "started",
            "ano_ref": request.ano_ref,
            "message": "Abra o VNC em http://localhost:7900 para acompanhar a coleta (Lógica VBA)"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
