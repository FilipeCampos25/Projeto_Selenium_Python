"""
driver_factory.py
Factory para criação de WebDriver.

✅ OBJETIVO DESTA ADAPTAÇÃO (FIDELIDADE AO VBA):
- Replicar o padrão do VBA antigo:
  1) Abrir o Google Chrome "normal" (fora do Selenium) com:
     - --remote-debugging-port=<porta>
     - --user-data-dir=<perfil>
     - abrir uma URL inicial (ex.: tela de login)
  2) Usuário faz login MANUALMENTE.
  3) O sistema detecta a troca de URL (ou uma URL de sucesso específica).
  4) Só então o Selenium "assume" anexando (attach) nessa instância/porta.

✅ COMO ATIVAR O MODO "VBA ATTACH"
Defina o env:
  SELENIUM_MODE=attach

E (opcional) configure:
  CHROME_DEBUG_PORT=9222
  CHROME_USER_DATA_DIR=C:\Users\<USER>\AppData\Local\Selenium_Profile
  CHROME_PROFILE_DIRECTORY=Default
  CHROME_BINARY=C:\Program Files\Google\Chrome\Application\chrome.exe
  CHROME_USER_AGENT=Mozilla/5.0 (...)
  CHROME_START_URL=https://contratos.comprasnet.gov.br/login
  CHROME_LOGIN_SUCCESS_URLS=https://contratos.comprasnet.gov.br/inicio|https://<outra_url_ok>
  CHROME_ATTACH_TIMEOUT_SECONDS=300

Observação:
- Mesmo que sua coleta final seja em outros portais (PGC/PNCP), você pode
  usar uma página "gatilho" de login aqui. O que importa é:
  -> login manual com perfil persistente + Selenium anexa depois do sucesso.
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import time
import urllib.request
from typing import Optional, Sequence

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.remote.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)


# =============================================================================
# Configs gerais (timeouts e robustez estilo VBA)
# =============================================================================
def _apply_vba_driver_settings(driver: WebDriver) -> None:
    """
    Aplica configurações de robustez exigidas pelo padrão "VBA-like".
    """
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


# =============================================================================
# Utilitários (porta / Chrome DevTools / polling)
# =============================================================================
def _is_tcp_port_open(host: str, port: int, timeout: float = 0.2) -> bool:
    """
    Verifica rapidamente se uma porta TCP está aberta.
    """
    import socket
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


def _http_get_json(url: str, timeout: float = 1.5):
    """
    Faz GET simples e retorna JSON parseado.
    Usamos urllib para evitar dependências extras.
    """
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    return json.loads(raw)


def _devtools_current_urls(debug_port: int) -> Sequence[str]:
    """
    Lê http://localhost:<port>/json e retorna uma lista de URLs abertas.
    (Equivalente ao VBA que lê o campo "url" no JSON.)
    """
    data = _http_get_json(f"http://127.0.0.1:{debug_port}/json", timeout=1.5)
    urls: list[str] = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and "url" in item:
                u = str(item.get("url") or "")
                if u:
                    urls.append(u)
    return urls


def _wait_until_port_is_ready(debug_port: int, timeout_seconds: int = 30) -> None:
    """
    Aguarda a porta de depuração do Chrome ficar disponível.
    """
    start = time.time()
    while True:
        if _is_tcp_port_open("127.0.0.1", debug_port):
            # Porta abriu; mas ainda pode demorar /json responder.
            try:
                _ = _devtools_current_urls(debug_port)
                return
            except Exception:
                pass

        if time.time() - start > timeout_seconds:
            raise RuntimeError(
                f"Falha ao iniciar/atingir Chrome DevTools na porta {debug_port} em {timeout_seconds}s."
            )
        time.sleep(0.25)


def _wait_for_login_success_by_url(
    debug_port: int,
    success_urls: Sequence[str],
    timeout_seconds: int = 300,
) -> str:
    """
    Espera o usuário concluir o login manual detectando a URL atual via DevTools.

    - O VBA original fazia um loop lendo /json e pegando a URL
      até bater com "https://contratos.comprasnet.gov.br/inicio".
    - Aqui suportamos múltiplas URLs possíveis (separadas por | no env).
    """
    success_urls_norm = [u.strip() for u in success_urls if u.strip()]
    start = time.time()

    while True:
        if time.time() - start > timeout_seconds:
            raise RuntimeError(
                "Timeout aguardando login manual. "
                "Nenhuma URL de sucesso foi detectada via DevTools."
            )

        try:
            urls = _devtools_current_urls(debug_port)
            # match exato OU por prefixo (alguns portais adicionam querystring)
            for current in urls:
                for ok in success_urls_norm:
                    if current == ok or current.startswith(ok):
                        return current
        except Exception:
            # DevTools pode oscilar nos primeiros segundos
            pass

        time.sleep(0.5)


# =============================================================================
# Modo LOCAL (cria um Chrome NOVO via Selenium)
# =============================================================================
def _find_chromedriver_in_cache() -> Optional[str]:
    """
    Procura por ChromeDriver já baixado no cache do webdriver-manager.
    Retorna o caminho do executável se encontrar.
    """
    import glob

    wdm_cache = os.path.expanduser("~/.wdm/drivers/chromedriver/win64")
    if not os.path.exists(wdm_cache):
        return None

    chromedriver_paths = glob.glob(os.path.join(wdm_cache, "*/chromedriver.exe"))
    if chromedriver_paths:
        logger.info(f"[LOCAL] ChromeDriver encontrado em cache: {chromedriver_paths[0]}")
        return chromedriver_paths[0]
    return None


def _build_local_driver(headless: bool) -> WebDriver:
    """
    Constrói WebDriver LOCAL usando Chrome instalado na máquina.
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

    logger.info("[LOCAL] Criando WebDriver Chrome local...")

    chromedriver_path = _find_chromedriver_in_cache()
    service = None

    if chromedriver_path and os.path.exists(chromedriver_path):
        logger.info(f"[LOCAL] Usando ChromeDriver do cache: {chromedriver_path}")
        service = Service(chromedriver_path)
    else:
        logger.warning("[LOCAL] ChromeDriver não encontrado em cache, tentando baixar via webdriver-manager...")
        try:
            service = Service(ChromeDriverManager().install())
        except Exception as download_err:
            logger.error(f"[LOCAL] Falha ao baixar ChromeDriver: {download_err}")
            logger.info("[LOCAL] Tentando usar ChromeDriver do PATH do sistema (service=None).")
            service = None

    if service:
        driver = webdriver.Chrome(service=service, options=options)
    else:
        driver = webdriver.Chrome(options=options)

    _apply_vba_driver_settings(driver)
    logger.info("[LOCAL] WebDriver Chrome local criado com sucesso!")
    return driver


# =============================================================================
# Modo DOCKER (RemoteWebDriver)
# =============================================================================
def _build_remote_driver(remote_url: str, headless: bool) -> WebDriver:
    """
    Constrói WebDriver remoto (container Selenium).
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


# =============================================================================
# Modo VBA ATTACH (o que você pediu: Chrome abre, login manual, depois Selenium anexa)
# =============================================================================
def _detect_default_chrome_binary_windows() -> Optional[str]:
    """
    Tenta localizar chrome.exe em caminhos padrão do Windows.
    """
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


def _start_chrome_with_remote_debugging(
    *,
    chrome_binary: str,
    debug_port: int,
    user_data_dir: str,
    profile_directory: str,
    user_agent: Optional[str],
    start_url: str,
) -> None:
    """
    Inicia o Chrome como processo "normal", com perfil dedicado e DevTools ativado.
    Espelha o cmd do VBA.

    Importante:
    - não bloqueia (Popen)
    - não mata processos existentes
    """
    os.makedirs(user_data_dir, exist_ok=True)

    args = [
        chrome_binary,
        f"--remote-debugging-port={debug_port}",
        f'--user-data-dir={user_data_dir}',
        f"--profile-directory={profile_directory}",
        "--new-tab",
        start_url,
    ]
    if user_agent:
        args.insert(-2, f'--user-agent={user_agent}')

    logger.info("[ATTACH] Iniciando Chrome fora do Selenium...")
    logger.info(f"[ATTACH] Chrome args: {' '.join(args)}")

    # Em Windows, evita abrir uma janela extra do cmd.
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]

    subprocess.Popen(args, creationflags=creationflags)  # noqa: S603,S607


def _build_attached_driver(
    *,
    debug_port: int,
    attach_timeout_seconds: int,
    user_data_dir: str,
    profile_directory: str,
    chrome_binary: Optional[str],
    user_agent: Optional[str],
    start_url: str,
    success_urls: Sequence[str],
    headless: bool,
) -> WebDriver:
    """
    1) Garante que o Chrome está rodando com DevTools na porta.
    2) Aguarda login manual (detectando URLs via /json)
    3) Anexa o Selenium nessa instância (debuggerAddress)
    """
    if headless:
        # No fluxo VBA, headless não faz sentido pois há login manual.
        logger.warning("[ATTACH] headless=True foi solicitado, mas será ignorado (login manual requer UI).")

    # 1) Chrome binary
    chrome_bin = chrome_binary or os.getenv("CHROME_BINARY") or _detect_default_chrome_binary_windows()
    if not chrome_bin or not os.path.exists(chrome_bin):
        raise RuntimeError(
            "Chrome binary não encontrado. Defina CHROME_BINARY com o caminho completo do chrome.exe."
        )

    # 2) Sobe Chrome se porta não estiver aberta
    if not _is_tcp_port_open("127.0.0.1", debug_port):
        _start_chrome_with_remote_debugging(
            chrome_binary=chrome_bin,
            debug_port=debug_port,
            user_data_dir=user_data_dir,
            profile_directory=profile_directory,
            user_agent=user_agent,
            start_url=start_url,
        )

    # 3) Aguarda DevTools pronto
    _wait_until_port_is_ready(debug_port, timeout_seconds=30)

    # 4) Aguarda login manual por mudança de URL via DevTools (/json)
    ok_url = _wait_for_login_success_by_url(
        debug_port=debug_port,
        success_urls=success_urls,
        timeout_seconds=attach_timeout_seconds,
    )
    logger.info(f"[ATTACH] Login detectado via DevTools. URL OK: {ok_url}")

    # 5) Anexa Selenium nessa instância
    options = webdriver.ChromeOptions()
    options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")

    # OBS: Não setamos user-data-dir aqui! Quem manda é o processo do Chrome que já está rodando.
    # Também evitamos flags anti-automation aqui: em attach, elas não fazem muita diferença e podem conflitar.

    chromedriver_path = _find_chromedriver_in_cache()
    service = None
    if chromedriver_path and os.path.exists(chromedriver_path):
        logger.info(f"[ATTACH] Usando ChromeDriver do cache: {chromedriver_path}")
        service = Service(chromedriver_path)
    else:
        logger.info("[ATTACH] Obtendo ChromeDriver via webdriver-manager...")
        service = Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(service=service, options=options)
    _apply_vba_driver_settings(driver)
    logger.info("[ATTACH] Selenium anexado com sucesso ao Chrome existente.")
    return driver


# =============================================================================
# API pública
# =============================================================================
def create_driver(headless: bool = False, remote_url: Optional[str] = None) -> WebDriver:
    """
    Cria WebDriver baseado no modo configurado.

    Modos suportados:
    - SELENIUM_MODE=attach  -> fluxo VBA: abre Chrome, login manual, Selenium anexa depois
    - SELENIUM_MODE=remote  -> docker/selenium grid
    - SELENIUM_MODE=local   -> Chrome novo controlado pelo Selenium
    - SELENIUM_MODE=auto    -> se tiver SELENIUM_REMOTE_URL usa remote, senão local
    """
    mode = (os.getenv("SELENIUM_MODE") or "auto").strip().lower()
    env_remote_url = os.getenv("SELENIUM_REMOTE_URL")
    effective_remote_url = remote_url or env_remote_url

    if mode == "attach":
        debug_port = int(os.getenv("CHROME_DEBUG_PORT", "9222"))
        user_data_dir = os.getenv(
            "CHROME_USER_DATA_DIR",
            os.path.join(os.path.expanduser("~"), "AppData", "Local", "Selenium_Profile")
            if os.name == "nt"
            else os.path.join(os.path.expanduser("~"), ".selenium_profile"),
        )
        profile_directory = os.getenv("CHROME_PROFILE_DIRECTORY", "Default")
        chrome_binary = os.getenv("CHROME_BINARY")
        user_agent = os.getenv("CHROME_USER_AGENT")
        start_url = os.getenv("CHROME_START_URL", "https://contratos.comprasnet.gov.br/login")

        # URLs de sucesso (padrão espelha o VBA).
        # Separe múltiplas por "|".
        success_urls_env = os.getenv(
            "CHROME_LOGIN_SUCCESS_URLS",
            "https://contratos.comprasnet.gov.br/inicio",
        )
        success_urls = [u.strip() for u in success_urls_env.split("|") if u.strip()]

        attach_timeout = int(os.getenv("CHROME_ATTACH_TIMEOUT_SECONDS", "300"))

        logger.info("[driver_factory] SELENIUM_MODE=attach (fluxo VBA) ativo.")
        return _build_attached_driver(
            debug_port=debug_port,
            attach_timeout_seconds=attach_timeout,
            user_data_dir=user_data_dir,
            profile_directory=profile_directory,
            chrome_binary=chrome_binary,
            user_agent=user_agent,
            start_url=start_url,
            success_urls=success_urls,
            headless=headless,
        )

    # Remote
    if mode == "remote" or (mode == "auto" and effective_remote_url):
        if not effective_remote_url:
            raise RuntimeError("SELENIUM_MODE=remote, mas SELENIUM_REMOTE_URL não foi definido.")
        logger.info("[driver_factory] SELENIUM_MODE=remote ativo.")
        return _build_remote_driver(effective_remote_url, headless=headless)

    # Local
    logger.info("[driver_factory] SELENIUM_MODE=local/auto -> usando Chrome local.")
    return _build_local_driver(headless=headless)
