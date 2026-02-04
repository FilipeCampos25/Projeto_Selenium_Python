"""
pgc_scraper_vba_logic.py
=======================
Adaptação para suportar a Opção 1 (Docker com Chrome externo sem WebDriver).

Mudança chave:
- Se LOGIN_MODE=docker_attach:
    - NÃO abre Chrome via Selenium e NÃO abre Chrome via subprocess.
    - Apenas:
        1) (opcional) pede ao DevTools para abrir a URL do login
        2) aguarda usuário logar via noVNC (monitorando /json)
        3) anexa WebDriver via debuggerAddress="chrome-login:9222"
    - Depois disso, segue a lógica VBA normal do PGC.
"""

import json
import logging
import os
from typing import Dict, List, Optional, Any

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException

from .vba_compat import VBACompat, CheckpointFailureError
from .driver_factory import create_attached_driver
from .chrome_attach import (
    start_manual_login_session_local,
    wait_until_logged_in,
    open_url_via_devtools,
)

logger = logging.getLogger(__name__)

XPATHS_FILE = os.path.join(os.path.dirname(__file__), "pgc_xpaths.json")
with open(XPATHS_FILE, "r", encoding="utf-8") as f:
    XPATHS = json.load(f)


class PGCScraperVBA:
    def __init__(self, driver: WebDriver, ano_ref: str = "2025"):
        self.driver = driver
        self.ano_ref = ano_ref
        self.compat = VBACompat(driver)
        self.data_collected = []

    def A_Loga_Acessa_PGC(self) -> bool:
        """
        Ponto de transição igual ao VBA:
        - aqui assumimos que o login manual já ocorreu,
          e o WebDriver já está anexado na instância de Chrome.
        """
        logger.info("=== PONTO DE TRANSIÇÃO (VBA) - Selenium assume APÓS login manual ===")

        try:
            self.compat.wait_for_checkpoint(
                XPATHS["login"]["span_pgc_title"],
                "Planejamento e Gerenciamento de Contratações",
                timeout=45,
            )
        except CheckpointFailureError:
            logger.error(
                "Não detectei a tela pós-login do portal. "
                "Garanta que o login manual foi concluído antes de iniciar a coleta."
            )
            return False
        except WebDriverException as e:
            logger.error(f"Conexão com o Chrome/Driver foi perdida: {e}")
            return False
        except Exception as e:
            logger.error(f"Falha inesperada validando pós-login: {e}")
            return False

        self.compat.safe_click(XPATHS["login"]["div_pgc_access"])

        original_handles = set(self.driver.window_handles)
        if not self.compat.wait_for_new_window(original_handles):
            logger.error("Falha ao esperar pela nova janela do PGC.")
            return False

        for handle in self.driver.window_handles:
            self.driver.switch_to.window(handle)
            if XPATHS["login"]["window_title"] in (self.driver.title or ""):
                self.compat.last_handle = handle
                break
        else:
            logger.error("Não encontrou a janela do PGC.")
            return False

        logger.info("PGC acessado com sucesso (Selenium anexado pós-login).")
        return True

    def A1_Demandas_DFD_PCA(self) -> List[Dict[str, Any]]:
        logger.info("=== INICIANDO COLETA DE DFDs (Lógica VBA) ===")

        try:
            self.compat.validate_table_context(
                "Planejamento e Gerenciamento de Contratações",
                ["DFD", "Requisitante", "Valor"],
            )
        except CheckpointFailureError as e:
            logger.error(f"Contexto da tabela inválido. Abortando coleta: {e}")
            return []

        self.compat.safe_click(XPATHS["pca_selection"]["dropdown_pca"])
        li_pca_xpath = XPATHS["pca_selection"]["li_pca_ano_template"].replace("{ano}", self.ano_ref)
        self.compat.safe_click(li_pca_xpath)

        self.compat.safe_click(f"//*[@id='{XPATHS['pca_selection']['radio_minha_uasg_id']}']")

        try:
            self.compat.wait_for_checkpoint(XPATHS["table"]["rows"], timeout=15)
        except CheckpointFailureError:
            logger.error("Falha no checkpoint da tabela de DFDs após seleção de PCA/UASG.")
            return []

        self.compat.testa_spinner()

        all_data = []
        pos = 1
        posM = self._count_total_pages()
        logger.info(f"Total de páginas detectadas (VBA): {posM}")
        self._go_to_first_page()

        while True:
            logger.info(f"Coletando página {pos}/{posM}")
            page_data = self._collect_current_page_rows()
            all_data.extend(page_data)

            if not self._has_next_page():
                break

            self._go_next_page()
            pos += 1

        logger.info(f"Coleta concluída. Total de registros: {len(all_data)}")
        return all_data

    def _count_total_pages(self) -> int:
        count = 1
        while self._has_next_page():
            self._go_next_page()
            count += 1
        return count

    def _go_to_first_page(self) -> None:
        first_xpath = XPATHS["pagination"].get("btn_first")
        if first_xpath:
            try:
                self.compat.safe_click(first_xpath)
                self.compat.testa_spinner()
                return
            except Exception:
                pass

        prev_xpath = XPATHS["pagination"].get("btn_prev")
        if prev_xpath:
            for _ in range(10):
                if not self._has_prev_page():
                    break
                self.compat.safe_click(prev_xpath)
                self.compat.testa_spinner()

    def _has_prev_page(self) -> bool:
        prev_xpath = XPATHS["pagination"].get("btn_prev")
        if not prev_xpath:
            return False
        try:
            el = self.driver.find_element(By.XPATH, prev_xpath)
            return el.is_enabled()
        except Exception:
            return False

    def _has_next_page(self) -> bool:
        next_xpath = XPATHS["pagination"].get("btn_next")
        if not next_xpath:
            return False
        try:
            el = self.driver.find_element(By.XPATH, next_xpath)
            return el.is_enabled()
        except Exception:
            return False

    def _go_next_page(self) -> None:
        next_xpath = XPATHS["pagination"].get("btn_next")
        if not next_xpath:
            raise RuntimeError("XPath de próxima página não configurado em pgc_xpaths.json")
        self.compat.safe_click(next_xpath)
        self.compat.testa_spinner()

    def _collect_current_page_rows(self) -> List[Dict[str, Any]]:
        rows_xpath = XPATHS["table"]["rows"]
        rows = self.driver.find_elements(By.XPATH, rows_xpath)
        data = []
        for r in rows:
            try:
                cols = r.find_elements(By.TAG_NAME, "td")
                if not cols:
                    continue
                row_dict = {
                    "DFD": cols[0].text.strip() if len(cols) > 0 else "",
                    "Requisitante": cols[1].text.strip() if len(cols) > 1 else "",
                    "Valor": cols[2].text.strip() if len(cols) > 2 else "",
                }
                data.append(row_dict)
            except Exception:
                continue
        return data


def run_pgc_scraper_vba(
    ano_ref: Optional[str] = None,
    ano: Optional[int] = None,
    mes: Optional[int] = None,
    driver=None,
    close_driver: bool = True,
):
    """
    Wrapper PGC com suporte a:
    - LOGIN_MODE=local_attach: abre Chrome local via subprocess e anexa depois
    - LOGIN_MODE=docker_attach: Chrome já está em outro serviço (chrome-login); só espera login e anexa
    - driver externo: quando a coleta unificada já forneceu driver anexado
    """
    local_driver = None
    try:
        if not ano_ref and ano is not None:
            ano_ref = str(ano)
        if not ano_ref:
            raise ValueError("ano_ref é obrigatório.")

        login_mode = os.getenv("LOGIN_MODE", "local_attach").lower()

        if driver is None:
            start_url = os.getenv("PGC_URL") or XPATHS["login"]["url"]

            if login_mode == "docker_attach":
                # Opção 1: Chrome está no serviço "chrome-login"
                host = os.getenv("CHROME_DEBUG_HOST", "chrome-login")
                port = int(os.getenv("CHROME_DEBUG_PORT", "9222"))

                # (opcional) tenta abrir a URL de login automaticamente no Chrome do container
                open_url_via_devtools(host, port, start_url)

                # aguarda login manual via noVNC monitorando /json
                wait_until_logged_in(
                    host=host,
                    port=port,
                    timeout_s=int(os.getenv("LOGIN_TIMEOUT_S", "600")),
                )

                # anexa Selenium no Chrome do container
                debugger_address = f"{host}:{port}"
                local_driver = create_attached_driver(debugger_address=debugger_address)
                driver = local_driver

            else:
                # padrão: local_attach (seu método atual)
                session = start_manual_login_session_local(start_url=start_url)
                wait_until_logged_in(
                    host="127.0.0.1",
                    port=session.port,
                    timeout_s=int(os.getenv("LOGIN_TIMEOUT_S", "600")),
                )
                debugger_address = f"127.0.0.1:{session.port}"
                local_driver = create_attached_driver(debugger_address=debugger_address)
                driver = local_driver

        else:
            close_driver = False

        scraper = PGCScraperVBA(driver, ano_ref=ano_ref)
        if not scraper.A_Loga_Acessa_PGC():
            logger.error("[PGC] Pós-login não validado / PGC não acessado. Abortando coleta.")
            return []

        dados = scraper.A1_Demandas_DFD_PCA()
        return dados

    except Exception as e:
        logger.exception(f"[PGC] Erro: {e}")
        raise

    finally:
        if close_driver and driver is not None:
            try:
                driver.quit()
            except Exception:
                pass
