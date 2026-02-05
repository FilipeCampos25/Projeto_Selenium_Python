"""
coleta_unificada.py
===================
Implementa a Opção 1 (Docker attach pós-login) mantendo o front-end igual:

- Usuário clica "iniciar coleta" e informa ano.
- Backend prepara o fluxo e retorna mensagem para o usuário abrir o noVNC e logar.
- Backend monitora /json do DevTools até detectar pós-login (igual VBA).
- Só então anexa Selenium e inicia PGC -> PNCP reaproveitando o driver.

AJUSTE (LOCAL):
- Agora também suporta LOGIN_MODE=local_attach:
  - Abre um Chrome LOCAL (sem WebDriver) com DevTools ativo.
  - Usuário faz login manualmente na janela local.
  - Backend monitora /json até detectar pós-login.
  - Só então anexa Selenium e executa PGC -> PNCP reaproveitando o driver.

Importante:
- Essa abordagem evita webdriver DURANTE o login, reduzindo chance de CAPTCHA.
"""

from __future__ import annotations

import logging
import os

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from backend.app.services.pgc_service import coleta_pgc
from backend.app.services.pncp_service import coleta_pncp
from backend.app.rpa.chrome_attach import (
    open_url_via_devtools,
    start_manual_login_session_local,
    wait_until_logged_in,
)
from backend.app.rpa.driver_factory import create_attached_driver

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/coleta", tags=["coleta"])


class ColetaRequest(BaseModel):
    ano_ref: int


def executar_coletas_sequenciais(
    ano_ref: int,
    preopened_session: ManualLoginSession | None = None,
) -> None:
    """
    Fluxo "attach pós-login" (docker_attach ou local_attach):
    - Um Chrome é iniciado SEM WebDriver.
    - Usuário faz login manualmente.
    - Backend detecta pós-login via DevTools (/json).
    - Só então anexa Selenium e executa PGC -> PNCP reaproveitando o driver.
    """
    ano_str = str(ano_ref)

    driver = None
    try:
        login_mode = os.getenv("LOGIN_MODE", "local_attach").lower().strip()
        start_url = os.getenv("PGC_URL", "https://www.comprasnet.gov.br/seguro/loginPortalUASG.asp")

        host: str
        port: int

        if login_mode == "docker_attach":
            # Chrome no container (via docker-compose) com DevTools exposto
            host = os.getenv("CHROME_DEBUG_HOST", "chrome-login")
            port = int(os.getenv("CHROME_DEBUG_PORT", "9222"))

            # (Opcional) manda abrir a URL de login na instância do Chrome do container
            open_url_via_devtools(host, port, start_url)

            logger.info(
                "LOGIN_MODE=docker_attach ativo. Aguardando login manual via noVNC "
                "antes de anexar o Selenium..."
            )

        elif login_mode == "local_attach":
            # Chrome LOCAL (Windows) sem Selenium até terminar login
            session = preopened_session or start_manual_login_session_local(start_url=start_url)
            host = "127.0.0.1"
            port = int(session.port)

            logger.info(
                "LOGIN_MODE=local_attach ativo. Um Chrome LOCAL foi aberto. "
                "Faça o login manualmente nessa janela e mantenha-a aberta "
                "para o Selenium anexar depois."
            )

        else:
            raise RuntimeError(
                f"LOGIN_MODE inválido: {login_mode}. "
                "Use 'docker_attach' (Opção 1) ou 'local_attach' (modo local)."
            )

        # Aguarda login manual detectando mudança de URL em /json (VBA-like)
        wait_until_logged_in(
            host=host,
            port=port,
            timeout_s=int(os.getenv("LOGIN_TIMEOUT_S", "600")),
        )

        # Após login: Selenium "assume"
        debugger_address = f"{host}:{port}"
        driver = create_attached_driver(debugger_address=debugger_address)

        # Coleta PGC
        logger.info(f"Iniciando sequência de coleta para o ano {ano_ref}")
        logger.info("Passo 1/2: Iniciando coleta PGC...")
        coleta_pgc(ano_str, driver=driver, close_driver=False)
        logger.info("Passo 1/2: Coleta PGC finalizada com sucesso.")

        # Coleta PNCP reaproveitando driver
        logger.info("Passo 2/2: Iniciando coleta PNCP...")
        coleta_pncp(
            username="",
            password="",
            ano_ref=ano_str,
            driver=driver,
            close_driver=False,
            reuse_driver=True,
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
    Dispara em background.

    Resposta orienta o usuário dependendo do LOGIN_MODE:
    - docker_attach: abrir noVNC e logar no Chrome do container
    - local_attach: usar a janela do Chrome LOCAL que será aberta automaticamente
    """
    try:
        login_mode = os.getenv("LOGIN_MODE", "local_attach").lower().strip()
        vnc_url = os.getenv("CHROME_VNC_URL", "")  # opcional: para o front mostrar link
        preopened_session: ManualLoginSession | None = None

        if login_mode == "docker_attach":
            msg = (
                "Sequência de coleta (PGC -> PNCP) iniciada em modo docker_attach. "
                "Faça o login MANUALMENTE no Chrome do servidor (via noVNC). "
                "Após o login, o Selenium irá anexar e continuar a coleta."
            )
            if vnc_url:
                msg += f" noVNC: {vnc_url}"

        elif login_mode == "local_attach":
            start_url = os.getenv("PGC_URL", "https://www.comprasnet.gov.br/seguro/loginPortalUASG.asp")
            preopened_session = start_manual_login_session_local(start_url=start_url)
            devtools_url = f"http://127.0.0.1:{preopened_session.port}/json"
            msg = (
                "Sequência de coleta (PGC -> PNCP) iniciada em modo local_attach. "
                "Um Chrome LOCAL será aberto: faça o login manualmente e mantenha a janela aberta. "
                "Após o login, o Selenium irá anexar e continuar a coleta. "
                f"DevTools: {devtools_url}"
            )

        else:
            msg = (
                f"Sequência de coleta iniciada, porém LOGIN_MODE inválido: {login_mode}. "
                "Ajuste para 'docker_attach' ou 'local_attach'."
            )

        background_tasks.add_task(executar_coletas_sequenciais, request.ano_ref, preopened_session)
        return {"status": "started", "ano_ref": request.ano_ref, "message": msg}

    except Exception as e:
        logger.error(f"Erro ao iniciar coleta unificada: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
