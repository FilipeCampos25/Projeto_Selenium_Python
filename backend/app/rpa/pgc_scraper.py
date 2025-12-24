"""
Arquivo: pgc_scraper.py
Descrição: Este arquivo faz parte do projeto e foi comentado para explicar a função de cada bloco de código.
"""

# backend/app/rpa/pnpc_scraper.py
"""
PNCP Scraper (Selenium) - versão 'completa' pronta para uso.
Objetivos:
- Fazer login (usuário + senha)
- Aceitar ano de referência após login
- Navegar pelo sistema (usando XPATHs configuráveis)
- Coletar resultados por página / linha
- Salvar JSON com estrutura para posterior gravação no Postgres

INSTRUÇÕES RÁPIDAS:
- Preencha o dicionário XPATHS abaixo com os XPATHs reais usados no seu VBA
  ou crie um arquivo backend/app/rpa/pnpc_xpaths.json com as mesmas chaves.
- Chame main() ou use a função run_scraper(...) a partir do seu serviço/backend.
"""

from __future__ import annotations
import json
import time
import logging
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    ElementClickInterceptedException,
    WebDriverException,
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

LOG = logging.getLogger("pncp_scraper")
LOG.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
LOG.addHandler(handler)

# ---------------------------
# --- CONFIGURABLE XPATHS ---
# ---------------------------
# Prefer loading from JSON file. If not present, edit this dict to match VBA XPATHs.
DEFAULT_XPATHS = {
    # Login page
    "login_username": "//input[@id='username']",
    "login_password": "//input[@id='password']",
    "login_submit": "//button[@id='loginBtn']",

    # After login - input year prompt (if modal or page element)
    "year_input": "//input[@id='anoReferencia']",
    "year_submit": "//button[@id='applyYearBtn']",

    # Navigation to search / consulta
    "menu_consulta": "//a[@id='menuConsulta']",
    "filtro_ano": "//select[@id='filterAno']",
    "buscar_btn": "//button[@id='buscarBtn']",

    # Results area
    "results_table": "//table[@id='resultsTable']/tbody",
    "results_rows": "//table[@id='resultsTable']/tbody/tr",
    "row_cols": "./td",

    # Pagination
    "pagination_next": "//a[contains(@class,'page-next')]",
    "pagination_disabled_next": "//a[contains(@class,'page-next') and contains(@class,'disabled')]",

    # Download or expand if necessary
    "row_expand_btn": ".//button[contains(@class,'expand-row')]",

    # Any other action used by VBA - add keys here...
}

XPATHS_FILE = os.path.join(os.path.dirname(__file__), "pncp_xpaths.json")


# ---------------------------
# --- DATA STRUCTURES -------
# ---------------------------
@dataclass
class ScrapeRow:
    index: int
    cells: Dict[str, Any]
    extra: Dict[str, Any] = None


# ---------------------------
# --- UTIL / HELPERS -------
# ---------------------------
def load_xpaths() -> Dict[str, str]:
    """
    Função load_xpaths:
    Executa a lógica principal definida nesta função.
    """
    """Load XPATHS from JSON file if present, otherwise return DEFAULT_XPATHS."""
    try:
        if os.path.exists(XPATHS_FILE):
            with open(XPATHS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                LOG.info("Loaded XPATHs from %s", XPATHS_FILE)
                # merge: keys from default not present in file will remain
                merged = DEFAULT_XPATHS.copy()
                merged.update(data)
                return merged
    except Exception as e:
        LOG.warning("Could not load XPATHS file: %s", e)
    return DEFAULT_XPATHS.copy()


def build_driver(
    
    # Função build_driver:
    # Executa a lógica principal definida nesta função.
    
    headless: bool = False,
    remote_url: Optional[str] = None,
    window_size: str = "1920,1080",
    options_extra: Optional[List[str]] = None,
) -> WebDriver:
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument(f"--window-size={window_size}")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    if options_extra:
        for o in options_extra:
            opts.add_argument(o)
    try:
        if remote_url:
            LOG.info("Connecting to remote Selenium at %s", remote_url)
            driver = webdriver.Remote(remote_url, options=opts)
        else:
            LOG.info("Starting local Chrome driver")
            driver = webdriver.Chrome(options=opts)
    except WebDriverException as e:
        LOG.exception("Error creating WebDriver: %s", e)
        raise
    driver.implicitly_wait(2)  # short implicit wait; explicit waits used elsewhere
    return driver


def safe_find(driver: WebDriver, by: By, selector: str, timeout: int = 12):
    """
    Função safe_find:
    Executa a lógica principal definida nesta função.
    """
    """Explicit wait for element presence."""
    try:
        wait = WebDriverWait(driver, timeout)
        return wait.until(EC.presence_of_element_located((by, selector)))
    except TimeoutException:
        LOG.debug("Element not found (timeout): %s %s", by, selector)
        return None


def safe_find_all(parent, by: By, selector: str, timeout: float = 2.0):
    """
    Função safe_find_all:
    Executa a lógica principal definida nesta função.
    """
    """Try to find elements, return empty list if none."""
    try:
        return parent.find_elements(by, selector)
    except Exception:
        return []


def click_element(driver: WebDriver, by: By, selector: str, timeout: int = 8) -> bool:
    """
    Função click_element:
    Executa a lógica principal definida nesta função.
    """
    """Wait then click, with retries."""
    try:
        el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, selector)))
        el.click()
        return True
    except (TimeoutException, ElementClickInterceptedException) as e:
        LOG.debug("Could not click element %s %s: %s", by, selector, e)
        return False


# ---------------------------
# --- SCRAPING LOGIC -------
# ---------------------------
class PNCPScraper:
    def __init__(
        
        #Função __init__:
        #Executa a lógica principal definida nesta função.
        
        self,
        base_url: str,
        username: str,
        password: str,
        year: str,
        driver: Optional[WebDriver] = None,
        headless: bool = False,
        remote_selenium_url: Optional[str] = None,
        xpaths: Optional[Dict[str, str]] = None,
    ):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.year = str(year)
        self.driver_provided = driver is not None
        self.driver = driver or build_driver(headless=headless, remote_url=remote_selenium_url)
        self.xpaths = xpaths or load_xpaths()
        self.wait = WebDriverWait(self.driver, 12)

    def open_base(self):
        """
        Função open_base:
        Executa a lógica principal definida nesta função.
        """
        LOG.info("Opening base URL: %s", self.base_url)
        self.driver.get(self.base_url)

    def do_login(self) -> bool:
        """
        Função do_login:
        Executa a lógica principal definida nesta função.
        """
        LOG.info("Performing login for user %s", self.username)
        # username
        try:
            el_user = safe_find(self.driver, By.XPATH, self.xpaths["login_username"], timeout=12)
            el_pass = safe_find(self.driver, By.XPATH, self.xpaths["login_password"], timeout=12)
            el_submit = safe_find(self.driver, By.XPATH, self.xpaths["login_submit"], timeout=12)
            if el_user is None or el_pass is None or el_submit is None:
                LOG.error("Login elements not found. Check XPATHs.")
                return False
            el_user.clear()
            el_user.send_keys(self.username)
            el_pass.clear()
            el_pass.send_keys(self.password)
            # some sites require pressing ENTER instead of clicking
            try:
                el_submit.click()
            except Exception:
                el_pass.send_keys("\n")
            # wait for post-login indicator: either menu_consulta or any known element
            post_login_indicator = self.xpaths.get("menu_consulta") or self.xpaths.get("buscar_btn")
            if post_login_indicator:
                found = WebDriverWait(self.driver, 12).until(
                    EC.presence_of_element_located((By.XPATH, post_login_indicator))
                )
                LOG.debug("Post-login element found: %s", post_login_indicator)
            time.sleep(1)
            return True
        except TimeoutException as e:
            LOG.exception("Timeout during login: %s", e)
            return False
        except Exception as e:
            LOG.exception("Exception during login: %s", e)
            return False

    def apply_year(self) -> bool:
        """
        Função apply_year:
        Executa a lógica principal definida nesta função.
        """
        LOG.info("Applying year reference: %s", self.year)
        # Try a few strategies: modal input, filter select, or a separate page input
        # 1) year_input
        yi = self.xpaths.get("year_input")
        if yi:
            el = safe_find(self.driver, By.XPATH, yi, timeout=6)
            if el:
                try:
                    el.clear()
                    el.send_keys(self.year)
                    submit = self.xpaths.get("year_submit")
                    if submit:
                        click_element(self.driver, By.XPATH, submit)
                    LOG.debug("Year applied via year_input")
                    time.sleep(0.8)
                    return True
                except Exception as e:
                    LOG.debug("Failed to set year via year_input: %s", e)

        # 2) filtro_ano select dropdown
        fa = self.xpaths.get("filtro_ano")
        if fa:
            el = safe_find(self.driver, By.XPATH, fa, timeout=4)
            if el:
                try:
                    from selenium.webdriver.support.ui import Select
                    sel = Select(el)
                    # try to select by visible text first
                    try:
                        sel.select_by_visible_text(self.year)
                        LOG.debug("Year selected by visible text")
                        click_element(self.driver, By.XPATH, self.xpaths.get("buscar_btn", ""))
                        return True
                    except Exception:
                        try:
                            sel.select_by_value(self.year)
                            click_element(self.driver, By.XPATH, self.xpaths.get("buscar_btn", ""))
                            return True
                        except Exception:
                            LOG.debug("Couldn't select year in filtro_ano")
                except Exception as e:
                    LOG.debug("Select widget issue: %s", e)

        LOG.warning("Year reference not applied — verify XPATHs and page flow.")
        return False

    def open_consulta(self) -> bool:
        """
        Função open_consulta:
        Executa a lógica principal definida nesta função.
        """
        LOG.info("Opening consulta / search section")
        menu = self.xpaths.get("menu_consulta")
        if menu:
            return click_element(self.driver, By.XPATH, menu, timeout=8)
        # fallback: maybe buscar_btn is visible directly
        buscar = self.xpaths.get("buscar_btn")
        if buscar:
            el = safe_find(self.driver, By.XPATH, buscar, timeout=6)
            return el is not None
        LOG.debug("No menu_consulta or buscar_btn configured.")
        return False

    def parse_row(self, row_element, index: int) -> ScrapeRow:
        """
        Função parse_row:
        Executa a lógica principal definida nesta função.
        """
        """Parse single table row into ScrapeRow dataclass."""
        cells = {}
        try:
            cols = safe_find_all(row_element, By.XPATH, "./td")
            # If the table has headers we may want to map names; we just number them here.
            for i, td in enumerate(cols):
                text = td.text.strip()
                cells[f"col_{i}"] = text
            # optional: try to expand row to get detail
            # if expand button exists
            exp_xpath = self.xpaths.get("row_expand_btn")
            if exp_xpath:
                try:
                    btns = row_element.find_elements(By.XPATH, exp_xpath)
                    if btns:
                        try:
                            btns[0].click()
                            time.sleep(0.4)  # allow expansion
                            # attempt to read expanded content
                            extra_el = row_element.find_element(By.XPATH, ".//div[contains(@class,'row-details')]")
                            cells["expanded"] = extra_el.text.strip()
                        except Exception:
                            LOG.debug("Could not click expand on row %s", index)
                except Exception:
                    pass
        except Exception as e:
            LOG.exception("Error parsing row: %s", e)
        return ScrapeRow(index=index, cells=cells, extra={})

    def collect_current_page(self) -> List[ScrapeRow]:
        """
        Função collect_current_page:
        Executa a lógica principal definida nesta função.
        """
        LOG.info("Collecting rows from current page")
        results = []
        table_xpath = self.xpaths.get("results_table")
        row_xpath = self.xpaths.get("results_rows")
        if not row_xpath:
            LOG.error("No results_rows XPATH configured.")
            return results
        try:
            # wait until at least the table presence
            safe_find(self.driver, By.XPATH, table_xpath or row_xpath, timeout=8)
            rows = self.driver.find_elements(By.XPATH, row_xpath)
            LOG.info("Found %d rows on page", len(rows))
            for i, r in enumerate(rows):
                sr = self.parse_row(r, i)
                results.append(sr)
        except Exception as e:
            LOG.exception("Error collecting page rows: %s", e)
        return results

    def go_next_page(self) -> bool:
        """
        Função go_next_page:
        Executa a lógica principal definida nesta função.
        """
        """Click next page if available. Return True if navigated, False if no more pages."""
        nx_disabled = self.xpaths.get("pagination_disabled_next")
        nx = self.xpaths.get("pagination_next")
        try:
            # if disabled next exists -> return False
            if nx_disabled:
                el = safe_find(self.driver, By.XPATH, nx_disabled, timeout=1)
                if el:
                    LOG.debug("Next page disabled (pagination end).")
                    return False
            if not nx:
                LOG.debug("No pagination_next XPATH configured.")
                return False
            clicked = click_element(self.driver, By.XPATH, nx, timeout=6)
            if clicked:
                time.sleep(1.0)
                LOG.debug("Navigated to next page.")
                return True
            else:
                LOG.debug("Could not click next page.")
                return False
        except Exception as e:
            LOG.debug("Pagination next failed: %s", e)
            return False

    def scrape_all(self, max_pages: Optional[int] = None) -> List[ScrapeRow]:
        """
        Função scrape_all:
        Executa a lógica principal definida nesta função.
        """
        LOG.info("Beginning full scrape (max_pages=%s)", max_pages)
        collected: List[ScrapeRow] = []
        page = 0
        while True:
            LOG.info("Collecting page %d", page + 1)
            rows = self.collect_current_page()
            collected.extend(rows)
            page += 1
            if max_pages and page >= max_pages:
                LOG.info("Reached max_pages limit: %s", max_pages)
                break
            next_exists = self.go_next_page()
            if not next_exists:
                LOG.info("No further pages.")
                break
        LOG.info("Scraping complete. Total rows: %d", len(collected))
        return collected

    def save_json(self, output_path: str, rows: List[ScrapeRow]):
        """
        Função save_json:
        Executa a lógica principal definida nesta função.
        """
        LOG.info("Saving output to %s", output_path)
        payload = {"metadata": {"source": self.base_url, "year": self.year, "fetched_at": time.time()},
                   "rows": [asdict(r) for r in rows]}
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        LOG.info("Saved %d rows.", len(rows))

    def close(self):
        """
        Função close:
        Executa a lógica principal definida nesta função.
        """
        if self.driver:
            if not self.driver_provided:
                try:
                    self.driver.quit()
                except Exception:
                    pass
            self.driver = None

    def run(self, output_path: str = "pncp_output.json", max_pages: Optional[int] = None) -> Dict[str, Any]:
        """
        Função run:
        Executa a lógica principal definida nesta função.
        """
        try:
            self.open_base()
            if not self.do_login():
                raise RuntimeError("Login step failed. Check credentials and XPATHs.")
            # optionally open consulta
            self.open_consulta()
            # apply year after login
            self.apply_year()
            # wait a bit for results to become available
            time.sleep(1.0)
            # trigger buscar if necessary
            buscar = self.xpaths.get("buscar_btn")
            if buscar:
                click_element(self.driver, By.XPATH, buscar)
                time.sleep(1.0)
            rows = self.scrape_all(max_pages=max_pages)
            self.save_json(output_path, rows)
            return {"status": "ok", "rows": len(rows), "output": output_path}
        except Exception as e:
            LOG.exception("Error during scraping run: %s", e)
            return {"status": "error", "message": str(e)}
        finally:
            self.close()


# ---------------------------
# --- EXAMPLE RUN ----------
# ---------------------------
def run_scraper_from_env():
    """
    Função run_scraper_from_env:
    Executa a lógica principal definida nesta função.
    """
    """
    Convenience function to run scraper using env vars (good for Docker / CI).
    Required env vars:
      PNCP_BASE_URL, PNCP_USER, PNCP_PASS, PNCP_YEAR
    Optional:
      PNCP_HEADLESS, PNCP_SELENIUM_REMOTE, PNCP_OUTPUT
    """
    base_url = os.environ.get("PNCP_BASE_URL", "https://example.com/login")
    user = os.environ.get("PNCP_USER", "")
    passwd = os.environ.get("PNCP_PASS", "")
    year = os.environ.get("PNCP_YEAR", "")
    if not (user and passwd and year):
        LOG.error("Missing PNCP_USER / PNCP_PASS / PNCP_YEAR environment variables")
        return

    headless = os.environ.get("PNCP_HEADLESS", "1") in ("1", "true", "True")
    remote = os.environ.get("PNCP_SELENIUM_REMOTE", None)
    output = os.environ.get("PNCP_OUTPUT", "/tmp/pncp_output.json")

    scraper = PNCPScraper(
        base_url=base_url,
        username=user,
        password=passwd,
        year=year,
        headless=headless,
        remote_selenium_url=remote,
    )
    res = scraper.run(output_path=output)
    LOG.info("Run result: %s", res)


if __name__ == "__main__":
    # For quick local tests:
    # export PNCP_BASE_URL=... PNCP_USER=... PNCP_PASS=... PNCP_YEAR=2024
    # python backend/app/rpa/pnpc_scraper.py
    run_scraper_from_env()
