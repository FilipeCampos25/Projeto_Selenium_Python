"""
chrome_attach.py
================
Implementa o fluxo "VBA-like" para DOCKER (Opção 1):
- Chrome roda em um serviço separado (ex: "chrome-login"), SEM WebDriver.
- Usuário faz login manual via noVNC.
- Backend monitora DevTools /json (igual ao VBA) para detectar pós-login.
- Depois cria WebDriver anexando via debuggerAddress (Selenium só entra após login).

Também mantém compatibilidade com modo LOCAL (abrir Chrome via subprocess),
mas o foco aqui é o modo DOCKER "attach pós-login".
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
from urllib.parse import quote

import urllib.request

logger = logging.getLogger(__name__)


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/110.0.0.0 Safari/537.36"
)

# ---------------------------------------------------------------------------
# Helpers de rede/HTTP (VBA lia http://localhost:<porta>/json)
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
    host = "127.0.0.1"
    for p in range(start, end + 1):
        if not _is_port_open(host, p):
            return p
    raise RuntimeError(f"Nenhuma porta livre encontrada entre {start} e {end}.")


def _http_get_text(url: str, timeout_s: float = 2.0) -> str:
    with urllib.request.urlopen(url, timeout=timeout_s) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _http_get_json(url: str, timeout_s: float = 2.0) -> object:
    raw = _http_get_text(url, timeout_s=timeout_s)
    return json.loads(raw)


def read_devtools_targets(host: str, port: int) -> list[dict]:
    """
    Equivalente ao VBA: GET http://<host>:<port>/json
    Retorna a lista de "targets" (abas/páginas) do Chrome.
    """
    try:
        obj = _http_get_json(f"http://{host}:{port}/json", timeout_s=2.0)
        if isinstance(obj, list):
            return [t for t in obj if isinstance(t, dict)]
        return []
    except Exception:
        return []


def open_url_via_devtools(host: str, port: int, url: str) -> None:
    """
    Abre uma nova aba no Chrome via DevTools endpoint:
      GET http://<host>:<port>/json/new?<url>

    Isso é útil no DOCKER:
    - O Chrome já está rodando no serviço chrome-login.
    - O backend "manda" abrir a URL de login, sem WebDriver.
    """
    try:
        u = f"http://{host}:{port}/json/new?{quote(url, safe=':/?&=#')}"
        _ = _http_get_text(u, timeout_s=2.0)
        logger.info(f"[LOGIN] DevTools abriu nova aba: {url}")
    except Exception as e:
        # Não é fatal: usuário pode abrir manualmente pelo VNC
        logger.warning(f"[LOGIN] Não consegui abrir URL via DevTools ({url}): {e}")


# ---------------------------------------------------------------------------
# Local (manter para compatibilidade com seu fluxo atual)
# ---------------------------------------------------------------------------

def _default_chrome_candidates_windows() -> Sequence[str]:
    candidates = []
    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    local_appdata = os.environ.get("LOCALAPPDATA", "")

    candidates.append(os.path.join(program_files, "Google", "Chrome", "Application", "chrome.exe"))
    candidates.append(os.path.join(program_files_x86, "Google", "Chrome", "Application", "chrome.exe"))
    if local_appdata:
        candidates.append(os.path.join(local_appdata, "Google", "Chrome", "Application", "chrome.exe"))

    return [c for c in candidates if c and os.path.exists(c)]


def resolve_chrome_path() -> str:
    env_path = os.getenv("CHROME_PATH")
    if env_path and os.path.exists(env_path):
        return env_path

    candidates = _default_chrome_candidates_windows()
    if candidates:
        return candidates[0]

    raise RuntimeError(
        "Não foi possível localizar o Google Chrome. "
        "Defina a variável CHROME_PATH apontando para chrome.exe."
    )


def resolve_selenium_profile_dir() -> str:
    local_appdata = os.environ.get("LOCALAPPDATA")
    if not local_appdata:
        base = Path.cwd() / "Selenium_Profile"
    else:
        base = Path(local_appdata) / "Selenium_Profile"
    base.mkdir(parents=True, exist_ok=True)
    return str(base)


@dataclass(frozen=True)
class ManualLoginSession:
    port: int
    chrome_path: str
    user_data_dir: str
    start_url: str


def start_manual_login_session_local(
    start_url: str,
    port: Optional[int] = None,
    user_data_dir: Optional[str] = None,
    user_agent: str = DEFAULT_USER_AGENT,
) -> ManualLoginSession:
    """
    Modo LOCAL (igual ao seu fluxo atual): abre Chrome fora do Selenium com remote debugging.
    """
    chrome_path = resolve_chrome_path()
    chosen_port = port or int(os.getenv("CHROME_DEBUG_PORT", "0") or 0) or _find_free_port()
    profile_dir = user_data_dir or resolve_selenium_profile_dir()

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

    logger.info(f"[LOGIN] Abrindo Chrome LOCAL com DevTools na porta {chosen_port}...")
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False)

    deadline = time.time() + 15
    while time.time() < deadline:
        if _is_port_open("127.0.0.1", chosen_port):
            logger.info("[LOGIN] Porta DevTools aberta (LOCAL).")
            return ManualLoginSession(
                port=chosen_port,
                chrome_path=chrome_path,
                user_data_dir=profile_dir,
                start_url=start_url,
            )
        time.sleep(0.2)

    raise RuntimeError(
        f"[LOGIN] Falha ao abrir Chrome na porta {chosen_port} (LOCAL)."
    )


# ---------------------------------------------------------------------------
# Espera pós-login (LOCAL ou DOCKER)
# ---------------------------------------------------------------------------

def wait_until_logged_in(
    host: str,
    port: int,
    timeout_s: int = 600,
    poll_s: float = 0.5,
    expected_url: Optional[str] = None,
    predicate: Optional[Callable[[str], bool]] = None,
) -> str:
    """
    Replica fielmente a ideia do VBA:
    - Loop lendo /json
    - Extrai urlAtual
    - Compara com URL esperada (ou heurística) para definir "entrou"

    No DOCKER (Opção 1): host será "chrome-login" (ou o nome do serviço).
    """
    expected_url = expected_url or os.getenv("PGC_POST_LOGIN_URL")

    def default_pred(url: str) -> bool:
        if expected_url:
            return url.strip().lower() == expected_url.strip().lower()

        u = url.lower()

        # Heurística base: saiu do login
        if "loginportal" in u:
            return False
        if "/seguro/login" in u and "comprasnet" in u:
            return False

        # Pós-login comum
        if "/inicio" in u:
            return True

        # Qualquer página interna do domínio após login
        if "comprasnet.gov.br" in u or "contratos.comprasnet.gov.br" in u:
            return True

        return False

    pred = predicate or default_pred

    deadline = time.time() + timeout_s
    last_urls: list[str] = []

    logger.info(f"[LOGIN] Aguardando pós-login via DevTools: http://{host}:{port}/json")

    while time.time() < deadline:
        targets = read_devtools_targets(host, port)
        urls = [t.get("url", "") for t in targets if isinstance(t, dict)]
        urls = [u for u in urls if u]

        if urls:
            last_urls = urls

        for u in urls:
            if pred(u):
                logger.info(f"[LOGIN] Pós-login detectado: {u}")
                return u

        time.sleep(poll_s)

    raise RuntimeError(
        "[LOGIN] Timeout aguardando login manual. "
        f"Últimas URLs observadas: {last_urls[-5:]}"
    )
