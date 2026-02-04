"""
Arquivo: coleta_unificada.py
Router para orquestrar as coletas PGC e PNCP em sequência.

MUDANÇA PRINCIPAL (fidelidade ao VBA antigo):
- Não criamos WebDriver no início.
- Abrimos o Chrome fora do Selenium, usuário faz login manual, monitoramos /json.
- Só então anexamos o Selenium e iniciamos a coleta PGC -> PNCP reaproveitando o driver.

Isso garante que o Selenium "assume" somente após o login manual, exatamente como o VBA.
"""

from __future__ import annotations

import logging
import os

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from backend.app.services.pgc_service import coleta_pgc
from backend.app.services.pncp_service import coleta_pncp
from backend.app.rpa.chrome_attach import start_manual_login_session, wait_until_logged_in
from backend.app.rpa.driver_factory import create_attached_driver

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/coleta", tags=["coleta"])


class ColetaRequest(BaseModel):
    ano_ref: int


def executar_coletas_sequenciais(ano_ref: int) -> None:
    """
    Executa a coleta do PGC e, após a finalização, executa a do PNCP.

    Fluxo:
    1) Abre Chrome fora do Selenium na URL de login (PGC_URL).
    2) Usuário loga manualmente.
    3) Detecta pós-login via DevTools (/json).
    4) Anexa Selenium e roda PGC, depois PNCP com reuse_driver=True.
    """
    ano_str = str(ano_ref)

    driver = None
    try:
        # 1) Abrir Chrome fora do Selenium (VBA-style)
        start_url = os.getenv("PGC_URL") or "http://www.comprasnet.gov.br/seguro/loginPortal.asp"
        session = start_manual_login_session(start_url=start_url)

        # 2) Aguardar login manual (monitorando /json)
        wait_until_logged_in(
            port=session.port,
            timeout_s=int(os.getenv("LOGIN_TIMEOUT_S", "600"))
        )

        # 3) Anexar Selenium SOMENTE AGORA
        debugger_address = f"127.0.0.1:{session.port}"
        driver = create_attached_driver(debugger_address=debugger_address, headless=False)

        # 4) Coleta PGC
        logger.info(f"Iniciando sequência de coleta para o ano {ano_ref}")
        logger.info("Passo 1/2: Iniciando coleta PGC...")
        coleta_pgc(ano_str, driver=driver, close_driver=False)
        logger.info("Passo 1/2: Coleta PGC finalizada com sucesso.")

        # 5) Coleta PNCP (reutilizando o mesmo driver)
        logger.info("Passo 2/2: Iniciando coleta PNCP...")
        coleta_pncp(
            username="",
            password="",
            ano_ref=ano_str,
            driver=driver,
            close_driver=False,
            reuse_driver=True
        )
        logger.info("Passo 2/2: Coleta PNCP finalizada com sucesso.")
        logger.info(f"Sequência de coleta para o ano {ano_ref} concluída.")

    except Exception as e:
        logger.error(f"Erro durante a sequência de coleta: {e}", exc_info=True)

    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass


@router.post("/iniciar")
async def iniciar_coleta_unificada(request: ColetaRequest, background_tasks: BackgroundTasks):
    """
    Endpoint para disparar as coletas PGC e PNCP em sequência via BackgroundTasks.
    """
    try:
        background_tasks.add_task(executar_coletas_sequenciais, request.ano_ref)

        return {
            "status": "started",
            "ano_ref": request.ano_ref,
            "message": (
                "Sequência de coleta (PGC -> PNCP) iniciada. "
                "⚠️ Abra o Chrome que será iniciado automaticamente, faça o login manual e NÃO feche a janela. "
                "Após o login, o Selenium irá anexar e continuar a coleta."
            ),
        }

    except Exception as e:
        logger.error(f"Erro ao iniciar coleta unificada: {e}")
        raise HTTPException(status_code=500, detail=str(e))
