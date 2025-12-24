"""
Arquivo: pncp.py
Descrição: Este arquivo faz parte do projeto e foi comentado para explicar a função de cada bloco de código.
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from backend.app.config import settings
from backend.app.rpa.pncp_scraper import PNCPScraperRefactored

router = APIRouter(prefix="/api/pncp", tags=["pncp"])

class PNCPRequest(BaseModel):
    ano_ref: int
    max_pages: int = 10
    headless: bool = True

@router.post("/iniciar")
async def iniciar_coleta(request: PNCPRequest, background_tasks: BackgroundTasks):
    try:
        scraper = PNCPScraperRefactored(
            headless=request.headless,
            remote_url=settings.SELENIUM_REMOTE_URL
        )

        background_tasks.add_task(
            scraper.run,
            request.ano_ref,
            request.max_pages
        )

        return {
            "status": "started",
            "ano_ref": request.ano_ref,
            "headless": request.headless
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
