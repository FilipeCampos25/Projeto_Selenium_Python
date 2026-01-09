"""
Arquivo: base_scraper.py
Descrição: Este arquivo faz parte do projeto e foi comentado para explicar a função de cada bloco de código.
"""

# backend/app/core/base_scraper.py
import time
import logging
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
)

from backend.app.rpa.driver_factory import create_driver
from backend.app.rpa.driver_global import get_driver, set_driver

logger = logging.getLogger(__name__)


# ============================================================
# EXCEÇÕES
# ============================================================
class ScraperError(Exception):
    pass


class LoginFailedError(ScraperError):
    """Erro lançado quando o login falha no scraper."""
    pass


class ElementNotFoundError(ScraperError):
    """Elemento não encontrado no scraper."""
    pass


class PaginationError(ScraperError):
    """Erro de paginação."""
    pass


# ============================================================
# BASE
# ============================================================
class BasePortalScraper(ABC):
    """
    Base class with common helpers for portal scrapers.
    The driver creation is delegated to driver_factory.create_driver.
    """

    def __init__(
        #Função __init__:
        #Executa a lógica principal definida nesta função.
        
        self,
        driver: Optional[WebDriver] = None,
        selectors: Optional[Dict[str, Dict[str, Any]]] = None,
        wait_short: int = 2,
        wait_long: int = 10,
        headless: bool = True,
        remote_url: Optional[str] = None,
    ):
        self.selectors = selectors or {}
        self.wait_short = wait_short
        self.wait_long = wait_long
        self.headless = headless
        self.remote_url = remote_url

        # PATCH 1 — permitir driver externo
        self._driver: Optional[WebDriver] = driver
        if self._driver is None:
            self._init_driver()

    @property
    def driver(self) -> WebDriver:
        if self._driver:
            return self._driver
        return get_driver()

    @driver.setter
    def driver(self, value: WebDriver):
        self._driver = value

    # --------------------------------------------------------
    # Driver
    # --------------------------------------------------------
    def _init_driver(self) -> None:
        """
        Função _init_driver:
        Executa a lógica principal definida nesta função.
        """
        if self._driver is None:
            self._driver = self._build_driver(self.headless, self.remote_url)
            # Define como global se for o driver principal criado
            set_driver(self._driver)

    def _build_driver(self, headless: bool, remote_url: Optional[str]) -> WebDriver:
        """
        Função _build_driver:
        Executa a lógica principal definida nesta função.
        """
        """
        Constrói o WebDriver usando a factory central.
        """
        try:
            driver = create_driver(headless=headless, remote_url=remote_url)
            driver.set_page_load_timeout(60)
            driver.implicitly_wait(2)
            return driver
        except Exception as e:
            logger.exception(f"Erro ao criar WebDriver: {e}")
            raise ScraperError(f"Falha ao inicializar navegador: {e}")

    # --------------------------------------------------------
    # Selectors
    # --------------------------------------------------------
    @staticmethod
    def _by_from_selector(selector: Dict[str, Any]):
        """
        Função _by_from_selector:
        Executa a lógica principal definida nesta função.
        """
        by_type = selector.get("by", "xpath").lower()
        mapping = {
            "id": By.ID,
            "name": By.NAME,
            "xpath": By.XPATH,
            "css": By.CSS_SELECTOR,
            "class": By.CLASS_NAME,
            "tag": By.TAG_NAME,
            "link": By.LINK_TEXT,
            "partial": By.PARTIAL_LINK_TEXT,
        }
        return mapping.get(by_type, By.XPATH)

    # --------------------------------------------------------
    # PATCH 3 — compatibilidade com XPATH puro (string)
    # --------------------------------------------------------
    def _extract_by_and_value(self, selector):
        """
        Função _extract_by_and_value:
        Executa a lógica principal definida nesta função.
        """
        """Retorna (By, value) para selectors string ou dict."""
        if isinstance(selector, str):
            return By.XPATH, selector

        if "value" not in selector:
            raise ScraperError(f"Selector inválido: {selector}")

        by = self._by_from_selector(selector)
        return by, selector["value"]

    # --------------------------------------------------------
    # Wait helpers
    # --------------------------------------------------------
    def wait_presence(self, selector_key: str, timeout: Optional[int] = None):
        """
        Função wait_presence:
        Executa a lógica principal definida nesta função.
        """
        timeout = timeout or self.wait_short
        selector = self.selectors.get(selector_key)
        if not selector:
            raise ScraperError(f"Selector '{selector_key}' não encontrado")

        by, value = self._extract_by_and_value(selector)

        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
        except TimeoutException:
            raise ElementNotFoundError(f"Timeout esperando presença de '{selector_key}'")

    def wait_clickable(self, selector_key: str, timeout: Optional[int] = None):
        """
        Função wait_clickable:
        Executa a lógica principal definida nesta função.
        """
        timeout = timeout or self.wait_short
        selector = self.selectors.get(selector_key)
        if not selector:
            raise ScraperError(f"Selector '{selector_key}' não encontrado")

        by, value = self._extract_by_and_value(selector)

        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
        except TimeoutException:
            raise ElementNotFoundError(f"Timeout esperando elemento clicável '{selector_key}'")

    # --------------------------------------------------------
    # Element finders
    # --------------------------------------------------------
    def find_element(self, selector_key: str):
        """
        Função find_element:
        Executa a lógica principal definida nesta função.
        """
        selector = self.selectors.get(selector_key)
        if not selector:
            raise ScraperError(f"Selector '{selector_key}' não encontrado")

        by, value = self._extract_by_and_value(selector)

        try:
            return self.driver.find_element(by, value)
        except NoSuchElementException:
            raise ElementNotFoundError(f"Elemento não encontrado '{selector_key}'")

    # --------------------------------------------------------
    # Click helpers
    # --------------------------------------------------------
    def click(self, selector_key: str):
        """
        Função click:
        Executa a lógica principal definida nesta função.
        """
        try:
            el = self.wait_clickable(selector_key, timeout=self.wait_long)
            el.click()
            time.sleep(0.3)
        except Exception as e:
            raise ScraperError(f"Erro ao clicar em '{selector_key}': {e}")

    # --------------------------------------------------------
    # Navigation
    # --------------------------------------------------------
    def get(self, url: str):
        """
        Função get:
        Executa a lógica principal definida nesta função.
        """
        try:
            self.driver.get(url)
        except Exception as e:
            raise ScraperError(f"Falha ao carregar URL {url}: {e}")

    def quit(self):
        """
        Função quit:
        Executa a lógica principal definida nesta função.
        """
        try:
            if self._driver:
                self._driver.quit()
                self._driver = None
                # Opcional: Limpar global se este for o driver global
                from backend.app.rpa.driver_global import close_driver
                close_driver()
        except Exception as e:
            logger.warning(f"Erro ao fechar driver: {e}")

    # --------------------------------------------------------
    # PATCH 2 — método go_next_page ausente
    # --------------------------------------------------------
    def go_next_page(self, next_button_key: str = "pagination_next") -> bool:
        """
        Função go_next_page:
        Executa a lógica principal definida nesta função.
        """
        selector = self.selectors.get(next_button_key)
        if not selector:
            return False

        try:
            # XPATH puro
            if isinstance(selector, str):
                btn = self.driver.find_element(By.XPATH, selector)
            else:
                by = self._by_from_selector(selector)
                btn = self.driver.find_element(by, selector["value"])

            if not btn.is_enabled():
                return False

            btn.click()
            time.sleep(1.2)
            return True

        except Exception:
            return False

    # --------------------------------------------------------
    # Abstract
    # --------------------------------------------------------
    @abstractmethod
    def run(self, *args, **kwargs):
        """
        Função run:
        Executa a lógica principal definida nesta função.
        """
        raise NotImplementedError
