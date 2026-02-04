"""
chrome_attach.py
Utilitários para reproduzir fielmente o fluxo do VBA:

1) Abrir o Google Chrome "por fora" (sem Selenium) com:
   - --remote-debugging-port=<porta>
   - --user-data-dir=<perfil persistente>
2) Usuário realiza login MANUALMENTE.
3) Código monitora a porta /json (DevTools) até detectar que o usuário já saiu do login.
4) Somente então criamos o Selenium WebDriver anexando na instância existente
   via ChromeOptions(debuggerAddress=...).

Importante:
- Este fluxo é equivalente ao VBA antigo que controlava apenas a porta/instância,
  e só inicializava o Selenium após o login manual.
- Funciona em execução LOCAL (Windows) onde o Chrome está instalado na máquina.
- Em ambiente Docker/Remote Selenium, anexar em um Chrome externo geralmente não é viável.
"""

from __future__ import annotations

import json
import logging
import os
import socket
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Sequence

import urllib.request

logger = logging.getLogger(__name__)


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/110.0.0.0 Safari/537.36"
)

# ---------------------------------------------------------------------------
# Helpers de porta / HTTP
# ---------------------------------------------------------------------------

def _is_port_open(host: str, port: int, timeout_s: float = 0.25) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout_s)
        try:
            sock.connect((host, port))
            return True
        except OSError:
            return False


def _find_free_port(start: int = 9222, end: int = 9250) -> int:
    """
    Procura uma porta livre para o remote debugging do Chrome.
    Fidelidade: VBA usava uma "porta monitorada" (variável porta).
    """
    host = "127.0.0.1"
    for p in range(start, end + 1):
        if not _is_port_open(host, p):
            return p
    raise RuntimeError(f"Nenhuma porta livre encontrada entre {start} e {end}.")


def _http_get_text(url: str, timeout_s: float = 1.5) -> str:
    with urllib.request.urlopen(url, timeout=timeout_s) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _read_devtools_json(port: int) -> list[dict]:
    """
    Emula o VBA:
      GET http://localhost:<porta>/json
    """
    raw = _http_get_text(f"http://127.0.0.1:{port}/json", timeout_s=1.5)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return []


# ---------------------------------------------------------------------------
# Localização do Chrome + perfil
# ---------------------------------------------------------------------------

def _default_chrome_candidates_windows() -> Sequence[str]:
    """
    Locais comuns do Chrome no Windows.
    Se necessário, permita override via env CHROME_PATH.
    """
    candidates = []
    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    local_appdata = os.environ.get("LOCALAPPDATA", "")

    candidates.append(os.path.join(program_files, "Google", "Chrome", "Application", "chrome.exe"))
    candidates.append(os.path.join(program_files_x86, "Google", "Chrome", "Application", "chrome.exe"))

    # Instalações "user-level" raras, mas acontecem
    if local_appdata:
        candidates.append(os.path.join(local_appdata, "Google", "Chrome", "Application", "chrome.exe"))

    return [c for c in candidates if c and os.path.exists(c)]


def resolve_chrome_path() -> str:
    """
    Resolve caminho do Chrome.
    Fidelidade: o VBA chamava explicitamente o chrome.exe.
    """
    env_path = os.getenv("CHROME_PATH")
    if env_path and os.path.exists(env_path):
        return env_path

    candidates = _default_chrome_candidates_windows()
    if candidates:
        return candidates[0]

    raise RuntimeError(
        "Não foi possível localizar o Google Chrome. "
        "Defina a variável de ambiente CHROME_PATH apontando para chrome.exe."
    )


def resolve_selenium_profile_dir() -> str:
    """
    Equivalente ao VBA:
      C:/Users/<User>/AppData/Local/Selenium_Profile

    Usamos LOCALAPPDATA para evitar hardcode de user.
    """
    local_appdata = os.environ.get("LOCALAPPDATA")
    if not local_appdata:
        # Fallback: pasta atual
        base = Path.cwd() / "Selenium_Profile"
    else:
        base = Path(local_appdata) / "Selenium_Profile"

    base.mkdir(parents=True, exist_ok=True)
    return str(base)


# ---------------------------------------------------------------------------
# API principal
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ManualLoginSession:
    """
    Representa uma sessão de login manual do Chrome com remote debugging.
    """
    port: int
    chrome_path: str
    user_data_dir: str
    start_url: str


def start_manual_login_session(
    start_url: str,
    port: Optional[int] = None,
    user_data_dir: Optional[str] = None,
    user_agent: str = DEFAULT_USER_AGENT,
) -> ManualLoginSession:
    """
    Inicia o Chrome fora do Selenium, com remote debugging.
    Retorna dados necessários para anexar depois.

    - start_url: URL de login (ex: portal comprasnet)
    - port: porta fixa (se None, escolhe livre)
    - user_data_dir: diretório do perfil (se None, usa Selenium_Profile)
    """
    chrome_path = resolve_chrome_path()
    chosen_port = port or int(os.getenv("CHROME_DEBUG_PORT", "0") or 0) or _find_free_port()
    profile_dir = user_data_dir or resolve_selenium_profile_dir()

    # Comando fiel ao VBA
    cmd = [
        chrome_path,
        f"--remote-debugging-port={chosen_port}",
        f"--user-data-dir={profile_dir}",
        "--profile-directory=Default",
        f"--user-agent={user_agent}",
        "--no-first-run",
        "--no-default-browser-check",
        "--new-tab",
        start_url,
    ]

    logger.info(f"[LOGIN] Abrindo Chrome com remote debugging na porta {chosen_port}...")
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False)

    # Aguardar porta abrir (sem sleep bruto, com polling controlado)
    deadline = time.time() + 15
    while time.time() < deadline:
        if _is_port_open("127.0.0.1", chosen_port):
            logger.info("[LOGIN] Porta do DevTools aberta. Aguardando login manual do usuário...")
            return ManualLoginSession(
                port=chosen_port,
                chrome_path=chrome_path,
                user_data_dir=profile_dir,
                start_url=start_url,
            )
        time.sleep(0.2)

    raise RuntimeError(
        f"[LOGIN] Falha ao abrir Chrome na porta {chosen_port}. "
        "Verifique se o Chrome iniciou corretamente."
    )


def wait_until_logged_in(
    port: int,
    timeout_s: int = 600,
    poll_s: float = 0.5,
    expected_url: Optional[str] = None,
    predicate: Optional[Callable[[str], bool]] = None,
) -> str:
    """
    Monitora http://localhost:<porta>/json e retorna a URL atual quando
    for detectado "pós-login".

    Fidelidade:
    - No VBA, ele fazia parsing do JSON e comparava urlAtual com um valor exato.

    Estratégia:
    - Se expected_url for definido, tentamos igualdade direta.
    - Caso contrário, usamos heurística (url contém '/inicio' ou saiu do loginPortal).
    - Você pode fornecer predicate custom para sua realidade.
    """
    expected_url = expected_url or os.getenv("PGC_POST_LOGIN_URL")

    def default_pred(url: str) -> bool:
        if expected_url:
            return url.strip().lower() == expected_url.strip().lower()

        # Heurística segura: saiu do login e entrou em uma área "interna"
        u = url.lower()
        if "/inicio" in u:
            return True
        if "loginportal" in u:
            return False
        if "seguro/login" in u and "comprasnet" in u:
            return False
        # qualquer página comprasnet/contratos fora de login
        if "comprasnet.gov.br" in u or "contratos.comprasnet.gov.br" in u:
            return True
        return False

    pred = predicate or default_pred

    deadline = time.time() + timeout_s
    last_urls: list[str] = []

    while time.time() < deadline:
        try:
            targets = _read_devtools_json(port)
            urls = [t.get("url", "") for t in targets if isinstance(t, dict)]
            urls = [u for u in urls if u]
            if urls:
                last_urls = urls

            for u in urls:
                if pred(u):
                    logger.info(f"[LOGIN] Detectado pós-login via DevTools: {u}")
                    return u

        except Exception:
            # silencioso: o Chrome pode estar inicializando a interface DevTools
            pass

        time.sleep(poll_s)

    raise RuntimeError(
        "[LOGIN] Timeout aguardando login manual. "
        f"Últimas URLs observadas: {last_urls[-5:]}"
    )
