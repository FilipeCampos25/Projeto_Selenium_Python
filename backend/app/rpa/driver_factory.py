"""
driver_factory.py
Ajustado para atender aos itens 3.1 e 3.2 da lista de migração:
- Múltiplas abas e window handles.
- noVNC como espelho, Selenium como fonte de verdade.
"""
from __future__ import annotations
import os
import logging
import time
from typing import Optional
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import WebDriverException

# import get_webdriver local implementation if present (chromedriver_manager)
try:
    from backend.app.rpa.chromedriver_manager import get_webdriver as get_local_webdriver
except Exception:
    get_local_webdriver = None

logger = logging.getLogger(__name__)

def _apply_vba_driver_settings(driver: WebDriver):
    """
    Aplica configurações de robustez exigidas pelo Item 3 da lista de migração.
    """
    # Item 3.1: Sempre assumir múltiplas abas e window handles
    driver.set_page_load_timeout(300)
    driver.set_script_timeout(120)
    
    # Item 3.2: Sessão visual (noVNC) é apenas espelho.
    # Garantimos que o Selenium tenha o foco e estado correto.
    driver.maximize_window()
    
    # Reset inicial de contexto
    try:
        driver.switch_to.default_content()
    except:
        pass

def _build_remote_driver(remote_url: str, headless: bool) -> WebDriver:
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")

    options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--window-size=1920,1080")
    
    # Downloads (Item 3.2 - Selenium controla, não a UI)
    prefs = {
        "download.default_directory": "/home/ubuntu/projeto_trabalho/projeto_adaptado/selenium_downloads",
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    options.add_experimental_option("prefs", prefs)

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
    mode = os.getenv("SELENIUM_MODE", "auto").lower()
    env_remote_url = os.getenv("SELENIUM_REMOTE_URL")
    effective_remote_url = remote_url or env_remote_url

    driver = None
    if mode == "remote" or (mode == "auto" and effective_remote_url):
        driver = _build_remote_driver(effective_remote_url, headless)
    elif get_local_webdriver:
        driver = get_local_webdriver(headless=headless)
        _apply_vba_driver_settings(driver)
    
    if not driver:
        raise RuntimeError("Nenhum driver pôde ser criado.")
        
    return driver
