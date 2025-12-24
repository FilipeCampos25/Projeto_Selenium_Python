"""
Arquivo: chromedriver_manager.py
Descrição: Este arquivo faz parte do projeto e foi comentado para explicar a função de cada bloco de código.
"""

# projetoSeleniumPython/backend/app/rpa/chromedriver_manager.py
"""
Gerenciamento do ChromeDriver para uso em containers e desenvolvimento local.

Funções principais:
 - get_webdriver(): retorna um webdriver.Chrome() pronto para uso (headless / container).
 - Ao inicializar, tenta:
    1) encontrar o binário do Google Chrome,
    2) descobrir a versão principal do Chrome,
    3) verificar se existe chromedriver compatível no PATH (/usr/local/bin),
    4) se não existir, baixa o chromedriver compatível para /usr/local/bin ou ./drivers,
    5) configura opções recomendadas para rodar dentro de container (headless, no-sandbox, disable-dev-shm-usage).
"""

from __future__ import annotations
import os
import platform
import stat
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Optional
import requests

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Local onde o chromedriver será colocado se precisarmos baixar
DEFAULT_DRIVER_DIR = Path("/usr/local/bin") if os.access("/usr/local/bin", os.W_OK) else Path.cwd() / "drivers"
DEFAULT_DRIVER_DIR.mkdir(parents=True, exist_ok=True)


def _which_binary(names: list[str]) -> Optional[Path]:
    """
    Função _which_binary:
    Executa a lógica principal definida nesta função.
    """
    """Procura um binário entre vários nomes (ex: ['google-chrome', 'google-chrome-stable', 'chromium'])"""
    for n in names:
        p = shutil.which(n)
        if p:
            return Path(p)
    return None


def find_chrome_binary() -> Optional[Path]:
    """
    Função find_chrome_binary:
    Executa a lógica principal definida nesta função.
    """
    """Tenta localizar o binário do Google Chrome / Chromium no sistema."""
    system = platform.system().lower()
    # nomes comuns
    linux_names = ["google-chrome-stable", "google-chrome", "chromium-browser", "chromium"]
    mac_names = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "google-chrome"]
    win_names = ["chrome.exe"]

    if system == "linux":
        return _which_binary(linux_names)
    elif system == "darwin":
        # mac: ver se caminho absoluto existe, senão tentativa de which
        for p in mac_names:
            if Path(p).exists():
                return Path(p)
        return _which_binary(mac_names)
    elif system == "windows":
        return _which_binary(win_names)
    else:
        return _which_binary(linux_names + mac_names + win_names)


def get_chrome_version(chrome_path: Path) -> Optional[str]:
    """
    Função get_chrome_version:
    Executa a lógica principal definida nesta função.
    """
    """Retorna a versão completa do chrome (ex: '120.0.6096.119') ou None."""
    try:
        # Executa o binário com --version
        res = subprocess.run([str(chrome_path), "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
        out = res.stdout.strip() or res.stderr.strip()
        # Saída geralmente: "Google Chrome 120.0.6096.119"
        parts = out.split()
        for part in parts:
            if part[0].isdigit():
                return part.strip()
        return None
    except Exception:
        return None


def _platform_for_chromedriver() -> str:
    """
    Função _platform_for_chromedriver:
    Executa a lógica principal definida nesta função.
    """
    """Retorna o sufixo usado pelos chromedriver zips no storage (linux64, win32/win64, mac64, mac_arm64)."""
    system = platform.system().lower()
    machine = platform.machine().lower()
    if system == "linux":
        return "linux64"
    if system == "windows":
        # historically chromedriver had win32/win64 naming; use win32 for wide compatibility
        return "win32"
    if system == "darwin":
        # mac intel vs m1/arm
        if "arm" in machine or "aarch64" in machine:
            return "mac_arm64"
        return "mac64"
    return "linux64"


def chromedriver_download_url_for_version(version: str) -> str:
    """
    Função chromedriver_download_url_for_version:
    Executa a lógica principal definida nesta função.
    """
    """Monta a URL do chromedriver zip para a versão informada."""
    plat = _platform_for_chromedriver()
    return f"https://chromedriver.storage.googleapis.com/{version}/chromedriver_{plat}.zip"


def get_compatible_chromedriver_version(chrome_version: str) -> Optional[str]:
    """
    Função get_compatible_chromedriver_version:
    Executa a lógica principal definida nesta função.
    """
    """
    Consulta a API pública do Google para descobrir uma versão do chromedriver compatível com a versão principal do Chrome.
    Ex.: Chrome 120.x -> buscar chromedriver versão para 120: https://chromedriver.storage.googleapis.com/LATEST_RELEASE_120
    """
    try:
        major = chrome_version.split(".")[0]
        url = f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{major}"
        r = requests.get(url, timeout=10)
        if r.ok:
            return r.text.strip()
    except Exception:
        pass
    return None


def download_and_extract_chromedriver(version: str, target_dir: Path) -> Optional[Path]:
    """
    Função download_and_extract_chromedriver:
    Executa a lógica principal definida nesta função.
    """
    """
    Baixa chromedriver para a versão exata e descompacta em target_dir, retornando o path do executável.
    """
    url = chromedriver_download_url_for_version(version)
    try:
        r = requests.get(url, stream=True, timeout=20)
        r.raise_for_status()
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    tmp.write(chunk)
            tmp_path = Path(tmp.name)
        with zipfile.ZipFile(tmp_path, "r") as zf:
            # extrair executável para target_dir
            members = zf.namelist()
            # chromedriver zip costuma ter um único arquivo chamado 'chromedriver' ou 'chromedriver.exe'
            extracted = None
            for member in members:
                name = Path(member).name
                if "chromedriver" in name:
                    zf.extract(member, path=target_dir)
                    extracted = target_dir / member
                    # se extraiu dentro de subdir, corrija o path
                    extracted = extracted.resolve()
                    final_path = target_dir / name
                    # move para target dir raiz
                    if extracted != final_path:
                        shutil.move(str(extracted), str(final_path))
                    # permissões executáveis
                    final_path.chmod(final_path.stat().st_mode | stat.S_IEXEC)
                    # remove zip temp
                    try:
                        tmp_path.unlink()
                    except Exception:
                        pass
                    return final_path
    except Exception as e:
        # não interromper o app por falha de download; retorna None para o caller lidar
        print(f"[chromedriver_manager] Falha ao baixar chromedriver {version}: {e}")
        return None
    return None


def ensure_chromedriver(chrome_version: Optional[str] = None) -> Optional[Path]:
    """
    Função ensure_chromedriver:
    Executa a lógica principal definida nesta função.
    """
    """
    Garante que exista um chromedriver compatível no PATH ou em DEFAULT_DRIVER_DIR.
    Retorna o Path para o chromedriver ou None se não foi possível garantir.
    """
    # 1) tenta localizar chromedriver já presente (prioriza /usr/local/bin e PATH)
    existing = shutil.which("chromedriver")
    if existing:
        return Path(existing)

    # 2) se temos versão do chrome, tenta descobrir versão compatível e baixar
    if chrome_version:
        drv_version = get_compatible_chromedriver_version(chrome_version)
        if drv_version:
            print(f"[chromedriver_manager] Baixando chromedriver versão {drv_version} para a plataforma {_platform_for_chromedriver()}...")
            target = DEFAULT_DRIVER_DIR
            target.mkdir(parents=True, exist_ok=True)
            driver_path = download_and_extract_chromedriver(drv_version, target)
            if driver_path:
                # Move para /usr/local/bin se possível (preferível)
                try:
                    if target.resolve() != Path("/usr/local/bin").resolve() and os.access("/usr/local/bin", os.W_OK):
                        dest = Path("/usr/local/bin") / driver_path.name
                        shutil.move(str(driver_path), str(dest))
                        dest.chmod(dest.stat().st_mode | stat.S_IEXEC)
                        return dest
                    else:
                        # já em DEFAULT_DRIVER_DIR
                        return driver_path
                except Exception:
                    # fallback: garantir executável em target
                    driver_path.chmod(driver_path.stat().st_mode | stat.S_IEXEC)
                    return driver_path

    # 3) falha: retorna None
    return None


def get_webdriver(headless: bool = True, extra_args: Optional[list[str]] = None) -> webdriver.Chrome:
    """
    Função get_webdriver:
    Executa a lógica principal definida nesta função.
    """
    """
    Retorna um objeto webdriver.Chrome pronto para uso.
    - headless: se True adiciona argumentos de headless (recomendado em containers).
    - extra_args: lista com argumentos adicionais para o Chrome.
    """

    extra_args = extra_args or []
    chrome_bin = find_chrome_binary()
    chrome_version = None
    if chrome_bin:
        chrome_version = get_chrome_version(chrome_bin)

    # Tenta encontrar chromedriver já instalado no PATH
    driver_path = shutil.which("chromedriver")
    if not driver_path:
        # tenta baixar compatível com chrome detectado
        driver_path_obj = ensure_chromedriver(chrome_version)
        if driver_path_obj:
            driver_path = str(driver_path_obj)
        else:
            # última tentativa: procurar em DEFAULT_DRIVER_DIR
            possible = next(DEFAULT_DRIVER_DIR.glob("chromedriver*"), None)
            if possible:
                driver_path = str(possible)

    chrome_options = Options()
    # Opções úteis para container
    if headless:
        # Selenium 4 mudou a flag --headless=new (Chromium v109+), mas usar compatível:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-background-networking")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-client-side-phishing-detection")
    chrome_options.add_argument("--disable-popup-blocking")
    for a in extra_args:
        chrome_options.add_argument(a)

    # Se foi detectado o binário do chrome, configura explicitamente (ajuda em ambientes não-standrd)
    if chrome_bin:
        try:
            chrome_options.binary_location = str(chrome_bin)
        except Exception:
            pass

    # Prepara o Service do chromedriver (Selenium 4+)
    service = None
    if driver_path:
        service = Service(driver_path)
    else:
        # sem driver_path, confiar no webdriver detectar chromedriver no PATH
        service = Service()

    # Cria o webdriver
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        # Em caso de erro, tenta forçar baixar de novo (retry simples)
        print("[chromedriver_manager] Erro ao iniciar ChromeDriver:", e)
        print("[chromedriver_manager] Tentando baixar/instalar chromedriver compatível e reiniciar...")
        new_driver = ensure_chromedriver(chrome_version)
        if new_driver:
            service = Service(str(new_driver))
            driver = webdriver.Chrome(service=service, options=chrome_options)
            return driver
        # se ainda falhar, re-raise para o chamador lidar
        raise
