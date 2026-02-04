"""
driver_factory.py
=================
Adaptação para a Opção 1 (Docker com Chrome externo sem WebDriver):
- Cria WebDriver ANEXADO (attach) em um Chrome que já está rodando em outro serviço/container
  com remote debugging.

Ponto chave:
- debuggerAddress precisa ser alcançável pelo chromedriver que está executando aqui.
  Em Docker: normalmente "chrome-login:9222" (nome do serviço na rede docker).
"""

from __future__ import annotations

import glob
import logging
import os
import time
from typing import Optional

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.remote.webdriver import WebDriver

try:
    from webdriver_manager.chrome import ChromeDriverManager
except Exception:  # pragma: no cover
    ChromeDriverManager = None  # type: ignore

logger = logging.getLogger(__name__)


def _apply_vba_driver_settings(driver: WebDriver) -> None:
    driver.set_page_load_timeout(300)
    driver.set_script_timeout(120)
    try:
        driver.maximize_window()
    except Exception:
        pass
    try:
        driver.switch_to.default_content()
    except Exception:
        pass


def _find_chromedriver_in_cache() -> Optional[str]:
    """
    Procura chromedriver já baixado no cache do webdriver-manager.
    Útil para ambientes sem internet.
    """
    # Windows cache
    wdm_cache_win = os.path.expanduser("~/.wdm/drivers/chromedriver/win64")
    if os.path.exists(wdm_cache_win):
        paths = glob.glob(os.path.join(wdm_cache_win, "*/chromedriver.exe"))
        if paths:
            return paths[0]

    # Linux cache
    wdm_cache_linux = os.path.expanduser("~/.wdm/drivers/chromedriver/linux64")
    if os.path.exists(wdm_cache_linux):
        paths = glob.glob(os.path.join(wdm_cache_linux, "*/chromedriver"))
        if paths:
            return paths[0]

    return None


def _build_chromedriver_service() -> Optional[Service]:
    cached = _find_chromedriver_in_cache()
    if cached and os.path.exists(cached):
        logger.info(f"[driver_factory] Usando ChromeDriver do cache: {cached}")
        return Service(cached)

    if ChromeDriverManager is not None:
        try:
            logger.warning("[driver_factory] ChromeDriver não encontrado em cache; tentando baixar via webdriver-manager...")
            return Service(ChromeDriverManager().install())
        except Exception as e:
            logger.error(f"[driver_factory] Falha ao baixar ChromeDriver: {e}")

    logger.warning("[driver_factory] Usando resolução do ChromeDriver via PATH (último recurso).")
    return None


def create_attached_driver(debugger_address: str) -> WebDriver:
    """
    Cria WebDriver anexado em um Chrome já rodando com:
      --remote-debugging-port=9222

    Exemplo debugger_address:
      - LOCAL: "127.0.0.1:9222"
      - DOCKER Opção 1: "chrome-login:9222"
    """
    options = webdriver.ChromeOptions()
    options.add_experimental_option("debuggerAddress", debugger_address)

    # downloads (não é crítico no attach, mas mantém coerência)
    downloads_path = os.path.join(os.getcwd(), "downloads_local")
    os.makedirs(downloads_path, exist_ok=True)
    prefs = {
        "download.default_directory": downloads_path,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    options.add_experimental_option("prefs", prefs)

    service = _build_chromedriver_service()
    if service:
        driver = webdriver.Chrome(service=service, options=options)
    else:
        driver = webdriver.Chrome(options=options)

    _apply_vba_driver_settings(driver)
    logger.info(f"[driver_factory] WebDriver anexado em {debugger_address}")
    return driver


def _build_remote_driver(remote_url: str, headless: bool) -> WebDriver:
    """
    Mantém suporte ao Selenium remoto tradicional (Grid), mas NÃO é o foco da Opção 1.
    """
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")

    options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    for attempt in range(1, 6):
        try:
            driver = webdriver.Remote(command_executor=remote_url, options=options)
            _apply_vba_driver_settings(driver)
            logger.info(f"[driver_factory] Conexão remota OK (tentativa {attempt})")
            return driver
        except WebDriverException as e:
            logger.warning(f"[driver_factory] Falha tentativa {attempt}: {e}")
            time.sleep(attempt * 2)

    raise RuntimeError("Falha ao conectar ao Selenium remoto.")


def create_driver(headless: bool = False, remote_url: Optional[str] = None) -> WebDriver:
    """
    Driver padrão do projeto. Mantido para compatibilidade.
    """
    mode = os.getenv("SELENIUM_MODE", "auto").lower()
    env_remote_url = os.getenv("SELENIUM_REMOTE_URL")
    effective_remote_url = remote_url or env_remote_url

    if mode == "remote" or (mode == "auto" and effective_remote_url):
        if not effective_remote_url:
            raise RuntimeError("SELENIUM_REMOTE_URL não definido para modo remote/auto.")
        return _build_remote_driver(effective_remote_url, headless)

    # default: local
    logger.info("[driver_factory] Usando WebDriver LOCAL (Chrome da máquina).")
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")

    options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    service = _build_chromedriver_service()
    if service:
        driver = webdriver.Chrome(service=service, options=options)
    else:
        driver = webdriver.Chrome(options=options)

    _apply_vba_driver_settings(driver)
    return driver
