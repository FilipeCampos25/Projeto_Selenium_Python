"""
Arquivo: pgc_scraper_item.py
Descrição: Este arquivo faz parte do projeto e foi comentado para explicar a função de cada bloco de código.
"""

# backend/app/rpa/pgc_scraper_item.py
"""
Abrir item PGC e extrair header, tabelas e DFD (imagem).
Feito para ser chamado pelo serviço orquestrador.
"""

import os
import time
import logging
import base64
from typing import Dict, Any, List, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logger = logging.getLogger(__name__)

def _wait_visible(driver: WebDriver, xpath: str, timeout: int = 10):
    """
    Função _wait_visible:
    Executa a lógica principal definida nesta função.
    """
    return WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.XPATH, xpath)))

def extract_header_fields(driver: WebDriver) -> Dict[str, Any]:
    """
    Função extract_header_fields:
    Executa a lógica principal definida nesta função.
    """
    """
    Extrai campos do header com base em XPaths conhecidos.
    Retorna dict com chaves comuns (numero, data, objeto, orgao, etc) quando encontrados.
    """
    header = {}
    mapping = {
        "numero": "//div[@class='header']//span[contains(@class,'numero')]|//h1",
        "objeto": "//label[text()='Objeto']/following-sibling::div|//div[contains(@class,'objeto')]",
        # adicione outros campos conforme necessário
    }
    for k, xp in mapping.items():
        try:
            el = driver.find_element(By.XPATH, xp)
            header[k] = el.text.strip()
        except Exception:
            header[k] = None
    # fallback: tentar extrair número por outro xpath usado no VBA
    try:
        if not header.get("numero"):
            el = driver.find_element(By.XPATH, "//div[contains(@class,'cabecalho')]/div[1]")
            header["numero"] = el.text.strip()
    except Exception:
        pass
    return header

def extract_tables(driver: WebDriver) -> List[Dict[str, Any]]:
    """
    Função extract_tables:
    Executa a lógica principal definida nesta função.
    """
    """
    Retorna lista de tabelas: cada tabela como dict {head:[...], rows:[{col:val}]}
    Usa xpath para localizar a tabela principal na listagem de andamentos/registro.
    """
    results = []
    try:
        # xpath que captura tabela de resultados na página (extraído do VBA)
        table_xpath = "//div[@id='minhauasg']//p-table//table | //div[@id='minhauasg']//table"
        table_el = driver.find_element(By.XPATH, table_xpath)
        # pegar headers
        headers = []
        try:
            ths = table_el.find_elements(By.XPATH, ".//thead//th")
            headers = [th.text.strip() for th in ths]
        except Exception:
            pass
        rows = []
        try:
            trs = table_el.find_elements(By.XPATH, ".//tbody//tr")
            for tr in trs:
                cells = tr.find_elements(By.XPATH, ".//td")
                values = [c.text.strip() for c in cells]
                # mapear por índice
                row = {headers[i] if i < len(headers) and headers[i] else str(i): values[i] if i < len(values) else "" for i in range(max(len(values), len(headers)))}
                rows.append(row)
        except Exception:
            pass
        results.append({"headers": headers, "rows": rows})
    except Exception as e:
        logger.debug("Nenhuma tabela encontrada: %s", e)
    return results

def extract_dfd_image(driver: WebDriver, save_dir: Optional[str] = None) -> Optional[str]:
    """
    Função extract_dfd_image:
    Executa a lógica principal definida nesta função.
    """
    """
    Localiza o DFD (se existir) e captura screenshot do elemento.
    Retorna path do arquivo salvo ou base64 string se preferir.
    """
    save_dir = save_dir or "/tmp"
    try:
        # no VBA o DFD era acessado por uma aba / conjunto de dfds; tentamos localizar canvas/img
        dfd_candidates = [
            "//div[contains(@class,'dfd') or contains(@class,'diagrama')]/img",
            "//app-dfd//img",
            "//div[contains(@class,'dfd-preview')]//canvas",
            "//div[contains(@class,'dfd-preview')]//img"
        ]
        for xp in dfd_candidates:
            try:
                el = driver.find_element(By.XPATH, xp)
                # scroll into view
                driver.execute_script("arguments[0].scrollIntoView(true);", el)
                time.sleep(0.2)
                # capturar screenshot do elemento
                png = el.screenshot_as_png
                fname = os.path.join(save_dir, f"dfd_{int(time.time()*1000)}.png")
                with open(fname, "wb") as f:
                    f.write(png)
                # opcional: retornar base64 para armazenamento em JSON/DB
                b64 = base64.b64encode(png).decode("ascii")
                return {"path": fname, "b64": b64}
            except Exception:
                continue
    except Exception as e:
        logger.exception("Erro extraindo DFD: %s", e)
    return None

def return_to_table(driver: WebDriver):
    """
    Função return_to_table:
    Executa a lógica principal definida nesta função.
    """
    """
    Tenta voltar para a listagem principal (fechar modal ou clicar 'Fechar')
    """
    try:
        close_xpaths = [
            "//span/button[text()='Fechar']",
            "//button[contains(.,'Fechar') or contains(.,'Voltar')]",
            "//button[@aria-label='Fechar']"
        ]
        for xp in close_xpaths:
            try:
                el = driver.find_element(By.XPATH, xp)
                el.click()
                time.sleep(0.2)
                return
            except Exception:
                continue
        # fallback: voltar no histórico
        driver.back()
        time.sleep(0.4)
    except Exception:
        pass

def collect_item(driver: WebDriver, item_open_xpath: str = None) -> Dict[str, Any]:
    """
    Função collect_item:
    Executa a lógica principal definida nesta função.
    """
    """
    Abre um item (já fornecendo o xpath do link/btn que abre o item), extrai header/tabelas/dfd e retorna dict.
    """
    item = {"header": None, "tables": [], "dfd": None}
    try:
        if item_open_xpath:
            try:
                el = driver.find_element(By.XPATH, item_open_xpath)
                el.click()
            except Exception:
                driver.execute_script("arguments[0].click();", el)
            # aguardar modal ou detalhe carregar
            time.sleep(0.6)
        # extrair
        item["header"] = extract_header_fields(driver)
        item["tables"] = extract_tables(driver)
        item["dfd"] = extract_dfd_image(driver)
        # tentar fechar e voltar
        return_to_table(driver)
    except Exception as e:
        logger.exception("Erro ao coletar item: %s", e)
    return item
