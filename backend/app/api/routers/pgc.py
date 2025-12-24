"""
Arquivo: pgc.py
Router para PGC scraping.
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from backend.app.config import settings
from backend.app.services.pgc_service import coleta_pgc

router = APIRouter(prefix="/api/pgc", tags=["pgc"])

class PGCRequest(BaseModel):
    ano_ref: int

@router.post("/iniciar")
async def iniciar_coleta_pgc(request: PGCRequest, background_tasks: BackgroundTasks):
    try:
        # Executa em background
        background_tasks.add_task(
            coleta_pgc,
            str(request.ano_ref)
        )

        return {
            "status": "started",
            "ano_ref": request.ano_ref,
            "message": "Abra o VNC em http://localhost:7900 para fazer login manual"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))