"""
driver_factory.py
Factory para criação de WebDriver - ADAPTADO PARA EXECUÇÃO LOCAL
"""
from __future__ import annotations
import os
import logging
import time
import glob
from typing import Optional
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

logger = logging.getLogger(__name__)

def _apply_vba_driver_settings(driver: WebDriver):
    """
    Aplica configurações de robustez exigidas pelo Item 3 da lista de migração.
    """
    driver.set_page_load_timeout(300)
    driver.set_script_timeout(120)
    driver.maximize_window()
    
    try:
        driver.switch_to.default_content()
    except:
        pass

# ============================================================
# 🔴 INÍCIO MODIFICAÇÃO LOCAL - REMOVER QUANDO VOLTAR DOCKER
# ============================================================

def _find_chromedriver_in_cache() -> str:
    """
    Procura por ChromeDriver já baixado no cache do webdriver-manager.
    Retorna o caminho do executável se encontrar.
    """
    import glob
    
    # Caminho padrão do cache do webdriver-manager
    wdm_cache = os.path.expanduser("~/.wdm/drivers/chromedriver/win64")
    
    if not os.path.exists(wdm_cache):
        return None
    
    # Procurar por qualquer versão baixada
    # Exemplo: C:\Users\username\.wdm\drivers\chromedriver\win64\143.0.7499.192\chromedriver.exe
    chromedriver_paths = glob.glob(os.path.join(wdm_cache, "*/chromedriver.exe"))
    
    if chromedriver_paths:
        logger.info(f"[LOCAL] ChromeDriver encontrado em cache: {chromedriver_paths[0]}")
        return chromedriver_paths[0]
    
    return None

def _build_local_driver(headless: bool) -> WebDriver:
    """
    Constrói WebDriver LOCAL usando Chrome instalado na máquina.
    ESTA FUNÇÃO É PARA EXECUÇÃO LOCAL - REMOVER QUANDO VOLTAR DOCKER.
    """
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
    
    # Downloads locais (ajuste o caminho conforme necessário)
    downloads_path = os.path.join(os.getcwd(), "downloads_local")
    os.makedirs(downloads_path, exist_ok=True)
    
    prefs = {
        "download.default_directory": downloads_path,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    options.add_experimental_option("prefs", prefs)
    
    try:
        logger.info("[LOCAL] Criando WebDriver Chrome local...")
        
        # Tentar encontrar ChromeDriver no cache primeiro
        chromedriver_path = _find_chromedriver_in_cache()
        
        if chromedriver_path and os.path.exists(chromedriver_path):
            logger.info(f"[LOCAL] Usando ChromeDriver do cache: {chromedriver_path}")
            service = Service(chromedriver_path)
        else:
            logger.warning("[LOCAL] ChromeDriver não encontrado em cache, tentando baixar...")
            # Se não encontrar, tenta baixar (pode falhar se sem internet)
            try:
                service = Service(ChromeDriverManager().install())
            except Exception as download_err:
                logger.error(f"[LOCAL] Falha ao baixar: {download_err}")
                logger.info("[LOCAL] Tentando usar ChromeDriver do PATH do sistema...")
                # Última tentativa: deixar Selenium procurar no PATH
                service = None
        
        if service:
            driver = webdriver.Chrome(service=service, options=options)
        else:
            driver = webdriver.Chrome(options=options)
        
        _apply_vba_driver_settings(driver)
        logger.info("[LOCAL] WebDriver Chrome local criado com sucesso!")
        return driver
    except Exception as e:
        logger.error(f"[LOCAL] Erro ao criar driver local: {e}")
        logger.error("VERIFIQUE SE:")
        logger.error("1. Google Chrome está instalado")
        logger.error("2. Há uma versão do ChromeDriver em: C:\\Users\\{user}\\.wdm\\drivers\\chromedriver\\win64\\")
        logger.error("3. Você tem permissão de leitura no cache")
        raise RuntimeError(f"Falha ao criar driver Chrome local: {e}")


# ============================================================
# 🔴 FIM MODIFICAÇÃO LOCAL
# ============================================================


# FUNÇÃO ORIGINAL _build_remote_driver (MANTER PARA QUANDO VOLTAR DOCKER)
def _build_remote_driver(remote_url: str, headless: bool) -> WebDriver:
    """
    ESTA FUNÇÃO É PARA DOCKER - NÃO SERÁ USADA EM EXECUÇÃO LOCAL.
    MANTER CÓDIGO PARA QUANDO VOLTAR A USAR DOCKER.
    """
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
    """
    Cria WebDriver baseado no modo configurado.
    
    MODIFICADO PARA EXECUÇÃO LOCAL:
    - Sempre cria driver local
    - Ignora remote_url
    - Não tenta conectar com container Docker
    """
    # ============================================================
    # 🔴 INÍCIO MODIFICAÇÃO LOCAL - REMOVER QUANDO VOLTAR DOCKER
    # ============================================================
    
    logger.info("[LOCAL] Modo LOCAL ativado - usando Chrome da máquina")
    driver = _build_local_driver(headless)
    return driver
    
    # ============================================================
    # 🔴 FIM MODIFICAÇÃO LOCAL
    # ============================================================
    
    # CÓDIGO ORIGINAL (DESCOMENTAR QUANDO VOLTAR DOCKER):
    # mode = os.getenv("SELENIUM_MODE", "auto").lower()
    # env_remote_url = os.getenv("SELENIUM_REMOTE_URL")
    # effective_remote_url = remote_url or env_remote_url
    #
    # driver = None
    # if mode == "remote" or (mode == "auto" and effective_remote_url):
    #     driver = _build_remote_driver(effective_remote_url, headless)
    # elif get_local_webdriver:
    #     driver = get_local_webdriver(headless=headless)
    #     _apply_vba_driver_settings(driver)
    # 
    # if not driver:
    #     raise RuntimeError("Nenhum driver pôde ser criado.")
    #     
    # return driver