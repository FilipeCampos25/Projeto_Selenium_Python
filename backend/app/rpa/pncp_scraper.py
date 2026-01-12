"""
pncp_scraper.py
Refatorado para remover sleeps estáticos e usar esperas dinâmicas.
"""
import os
import json
import time
import logging
from typing import Dict, Any, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from backend.app.core.base_scraper import (
    BasePortalScraper,
    LoginFailedError,
    ElementNotFoundError,
    ScraperError
)
from backend.app.db.repositories import ColetasRepository

logger = logging.getLogger(__name__)

SELECTORS_PATH = os.path.join(os.path.dirname(__file__), "selectors.json")

def load_selectors(path: str = SELECTORS_PATH) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            selectors = json.load(f)
    except Exception as e:
        logger.error(f"Erro ao carregar seletores: {e}")
        raise
    return selectors

class PNCPScraperRefactored(BasePortalScraper):
    def __init__(
        self,
        driver: Optional[WebDriver] = None,
        selectors: Optional[Dict[str, Any]] = None,
        wait_short: int = 10,
        wait_long: int = 60,
        headless: bool = False,
        remote_url: Optional[str] = None
    ):
        if selectors is None:
            selectors = load_selectors()

        super().__init__(
            driver=driver,
            selectors=selectors,
            wait_short=wait_short,
            wait_long=wait_long,
            headless=headless,
            remote_url=remote_url
        )
        self.ano_referencia: Optional[str] = None
        self.repo = ColetasRepository()

    def open_portal(self):
        # Removido sleep(2) fixo
        logger.info("Portal PNCP aberto. Aguardando estabilização.")
        WebDriverWait(self.driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

    def wait_manual_login(self, timeout: int = 300) -> bool:
        logger.info("Aguardando login manual...")
        start = time.time()
        login_marker = self.selectors.get("login_success_marker")

        while time.time() - start < timeout:
            try:
                if login_marker:
                    if self.driver.find_elements(By.XPATH, login_marker):
                        return True

                current = self.driver.current_url
                if current and "login" not in current.lower():
                    return True
            except:
                pass
            time.sleep(0.5) # Polling rate aceitável para login manual
        
        raise LoginFailedError("Timeout no login manual.")

    def apply_login_context(self, ano_ref: str):
        s = self.selectors

        def resolve_selector(entry):
            if isinstance(entry, dict):
                by = entry.get("by", "xpath").lower()
                val = entry.get("value")
                mapping = {"id": By.ID, "css": By.CSS_SELECTOR, "xpath": By.XPATH}
                return mapping.get(by, By.XPATH), val
            return By.XPATH, entry

        def dynamic_click(key):
            entry = s.get(key)
            if not entry: return False
            by, val = resolve_selector(entry)
            try:
                el = WebDriverWait(self.driver, 15).until(EC.element_to_be_clickable((by, val)))
                el.click()
                return True
            except:
                return False

        def wait_spinner(timeout=15):
            entry = s.get("spinner")
            if not entry: return
            by, val = resolve_selector(entry)
            try:
                WebDriverWait(self.driver, timeout).until(EC.invisibility_of_element_located((by, val)))
            except:
                pass

        # Fluxo sem sleeps fixos
        dynamic_click("link_pgc")
        wait_spinner()
        dynamic_click("button_formacao_pca")
        wait_spinner()
        dynamic_click("pca_dropdown_toggle")
        
        opt_tmpl = s.get("pca_option_template")
        if opt_tmpl:
            by, val = resolve_selector(opt_tmpl)
            try:
                el = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((by, val)))
                el.click()
            except:
                logger.warning(f"Não encontrou opção PCA para ano {ano_ref}")

        wait_spinner()
        dynamic_click("buscar_button")
        wait_spinner()
        logger.info("Contexto aplicado com sucesso.")
