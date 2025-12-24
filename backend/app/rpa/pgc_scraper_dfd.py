"""
pgc_scraper_item.py

Abrir item e extrair header, tabelas e DFD (apenas coleta; OCR em outro módulo).
"""

import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)

def wait_visible(driver, by, sel, timeout=30):
    """
    Função wait_visible:
    Executa a lógica principal definida nesta função.
    """
    return WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located((by, sel))
    )

def wait_el(driver, by, sel, timeout=30):
    """
    Função wait_el:
    Executa a lógica principal definida nesta função.
    """
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, sel))
    )

def js_click(driver, el):
    """
    Função js_click:
    Executa a lógica principal definida nesta função.
    """
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    driver.execute_script("arguments[0].click();", el)

def open_item_details(driver, action_xpath: str):
    """
    Função open_item_details:
    Executa a lógica principal definida nesta função.
    """
    logger.info(f"Abrindo item via action_xpath: {action_xpath}")
    el = wait_el(driver, By.XPATH, action_xpath)
    js_click(driver, el)
    time.sleep(1)
    DETAIL_HEADER = "//h1 | //h2 | //div[contains(@class,'titulo')]"
    wait_visible(driver, By.XPATH, DETAIL_HEADER, timeout=20)
    return True

def extract_header_fields(driver):
    """
    Função extract_header_fields:
    Executa a lógica principal definida nesta função.
    """
    data = {}
    candidates = {
        "numero": "//span[@id='lblNumero'] | //div[@id='campo-numero']",
        "titulo": "//span[@id='lblTitulo'] | //h1[contains(@class,'titulo')]",
        "unidade": "//span[@id='lblUnidade']",
        "situacao": "//span[@id='lblSituacao']",
        "responsavel": "//span[@id='lblResponsavel'] | //div[@class='responsavel']",
        "data_inicio": "//span[@id='lblDataInicio']",
        "data_fim": "//span[@id='lblDataFim']",
    }
    for key, xpath in candidates.items():
        try:
            el = driver.find_element(By.XPATH, xpath)
            text = el.text.strip()
            if text:
                data[key] = text
        except:
            pass
    logger.info("Campos gerais extraídos.")
    return data

def extract_tables(driver):
    """
    Função extract_tables:
    Executa a lógica principal definida nesta função.
    """
    logger.info("Extraindo tabelas internas...")
    tables_data = {}
    tables = driver.find_elements(By.XPATH, "//table")
    for idx, table in enumerate(tables, start=1):
        try:
            rows = table.find_elements(By.XPATH, ".//tbody/tr")
            header_cols = table.find_elements(By.XPATH, ".//thead//th")
            headers = [h.text.strip() for h in header_cols]
            table_name = f"table_{idx}"
            tables_data[table_name] = {
                "headers": headers,
                "rows": []
            }
            for row in rows:
                cols = row.find_elements(By.XPATH, "./td")
                tables_data[table_name]["rows"].append([
                    c.text.strip() for c in cols
                ])
        except Exception as e:
            logger.error(f"Erro extraindo tabela {idx}: {e}")
    return tables_data

def extract_dfd_image(driver):
    """
    Função extract_dfd_image:
    Executa a lógica principal definida nesta função.
    """
    selectors = [
        "//div[@id='dfd']",
        "//canvas[contains(@class,'dfd') or contains(@id,'dfd')]",
        "//img[contains(@src,'dfd')]",
    ]
    for sel in selectors:
        try:
            el = driver.find_element(By.XPATH, sel)
            path = f"/tmp/dfd_{int(time.time())}.png"
            el.screenshot(path)
            logger.info(f"Imagem DFD salva em: {path}")
            return path
        except:
            continue
    logger.warning("Nenhum DFD encontrado.")
    return None

def return_to_table(driver):
    """
    Função return_to_table:
    Executa a lógica principal definida nesta função.
    """
    selectors = [
        "//button[contains(., 'Voltar')]",
        "//a[contains(., 'Voltar')]",
        "//button[@id='btnVoltar']",
    ]
    for sel in selectors:
        try:
            btn = driver.find_element(By.XPATH, sel)
            js_click(driver, btn)
            time.sleep(1)
            return True
        except:
            continue
    logger.warning("Botão VOLTAR não encontrado.")
    return False

def process_item(driver: WebDriver, item: dict):
    """
    Função process_item:
    Executa a lógica principal definida nesta função.
    """
    logger.info(f"--- PROCESSANDO ITEM {item.get('numero')} ---")
    open_item_details(driver, item["action_xpath"])
    header = extract_header_fields(driver)
    tables = extract_tables(driver)
    dfd_image = extract_dfd_image(driver)
    return_to_table(driver)
    logger.info(f"Item {item.get('numero')} coletado com sucesso.")
    return {
        "header": header,
        "tables": tables,
        "dfd_image": dfd_image
    }
