"""
driver_factory.py
Factory para criação de WebDriver.

Este projeto suporta DOIS modos de uso:

1) Driver "normal" (Selenium cria o Chrome):
   - Usado quando queremos Selenium controlando tudo desde o início.

2) Driver "attach" (fidelidade ao VBA antigo):
   - Primeiro abrimos o Chrome fora do Selenium com --remote-debugging-port.
   - Usuário faz login manual.
   - Só depois criamos o WebDriver anexando na instância existente via debuggerAddress.

Observação:
- O modo attach é pensado para EXECUÇÃO LOCAL (Chrome instalado na máquina).
- Em Docker/Remote Selenium, "attach" normalmente não é aplicável sem arquitetura extra.
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
    # webdriver-manager é útil em modo local; em ambientes sem internet, tentamos cache primeiro.
    from webdriver_manager.chrome import ChromeDriverManager
except Exception:  # pragma: no cover
    ChromeDriverManager = None  # type: ignore

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configurações de robustez (equivalente ao "driver settings" do VBA)
# ---------------------------------------------------------------------------

def _apply_vba_driver_settings(driver: WebDriver) -> None:
    """
    Aplica configurações de robustez exigidas pelo projeto (equivalente à disciplina do VBA).
    """
    driver.set_page_load_timeout(300)
    driver.set_script_timeout(120)
    try:
        driver.maximize_window()
    except Exception:
        pass

    # Garantir contexto base
    try:
        driver.switch_to.default_content()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Descoberta do ChromeDriver (fidelidade: "chromedriverPath" do VBA)
# ---------------------------------------------------------------------------

def _find_chromedriver_in_cache_windows() -> Optional[str]:
    """
    Procura por ChromeDriver já baixado no cache do webdriver-manager (Windows).
    Exemplo:
      C:/Users/<user>/.wdm/drivers/chromedriver/win64/<versao>/chromedriver.exe
    """
    wdm_cache = os.path.expanduser("~/.wdm/drivers/chromedriver/win64")
    if not os.path.exists(wdm_cache):
        return None

    paths = glob.glob(os.path.join(wdm_cache, "*/chromedriver.exe"))
    if paths:
        # pega o primeiro encontrado (suficiente para o cenário local)
        return paths[0]
    return None


def _build_chromedriver_service() -> Optional[Service]:
    """
    Constrói Selenium Service para o ChromeDriver, tentando (em ordem):
    1) Cache do webdriver-manager
    2) Download via webdriver-manager (se disponível)
    3) None (deixar Selenium tentar resolver via PATH)
    """
    cached = _find_chromedriver_in_cache_windows()
    if cached and os.path.exists(cached):
        logger.info(f"[driver_factory] Usando ChromeDriver do cache: {cached}")
        return Service(cached)

    if ChromeDriverManager is not None:
        try:
            logger.warning("[driver_factory] ChromeDriver não encontrado em cache, tentando baixar via webdriver-manager...")
            return Service(ChromeDriverManager().install())
        except Exception as e:
            logger.error(f"[driver_factory] Falha ao baixar ChromeDriver: {e}")

    logger.warning("[driver_factory] Usando resolução do ChromeDriver via PATH (último recurso).")
    return None


# ---------------------------------------------------------------------------
# Driver LOCAL "normal" (Selenium cria o Chrome)
# ---------------------------------------------------------------------------

def _build_local_driver(headless: bool) -> WebDriver:
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

    # Downloads locais
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
    return driver


# ---------------------------------------------------------------------------
# Driver "attach" (Selenium anexa em Chrome existente pós-login)
# ---------------------------------------------------------------------------

def create_attached_driver(debugger_address: str, headless: bool = False) -> WebDriver:
    """
    Cria um WebDriver anexado em uma instância de Chrome já aberta com:
      --remote-debugging-port=<porta>

    Fidelidade ao VBA:
    - o VBA não "cria" o Chrome via Selenium; ele abre o Chrome e depois conecta.

    Parâmetros:
    - debugger_address: "127.0.0.1:9222"
    - headless: ignorado na prática (não existe "headless attach" pós-fato), mas mantido por assinatura.
    """
    options = webdriver.ChromeOptions()

    # IMPORTANTE: ao anexar, o Chrome já está rodando; headless não se aplica.
    options.add_experimental_option("debuggerAddress", debugger_address)

    # Ainda setamos preferências para downloads (pode não surtir efeito se o perfil já estiver carregado,
    # mas mantém coerência do projeto).
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
    logger.info(f"[driver_factory] WebDriver anexado com sucesso em {debugger_address}")
    return driver


# ---------------------------------------------------------------------------
# Driver REMOTO (Docker Selenium) - manter para quando voltar Docker
# ---------------------------------------------------------------------------

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

    prefs = {
        "download.default_directory": "/home/ubuntu/projeto_trabalho/projeto_adaptado/selenium_downloads",
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
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
    """
    Cria WebDriver baseado no modo configurado.
    - SELENIUM_MODE=local -> Chrome local
    - SELENIUM_MODE=remote -> Selenium remoto (Docker)
    - SELENIUM_MODE=auto  -> remoto se SELENIUM_REMOTE_URL existir, senão local
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
    return _build_local_driver(headless)
