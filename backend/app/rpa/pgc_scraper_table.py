"""
pgc_scraper_table.py

Clicar em pesquisar e extrair a tabela principal.
"""

import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

logger = logging.getLogger(__name__)

def js_click(driver, el):
    """
    Função js_click:
    Executa a lógica principal definida nesta função.
    """
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    driver.execute_script("arguments[0].click();", el)

def click_search_button(driver: WebDriver):
    """
    Função click_search_button:
    Executa a lógica principal definida nesta função.
    """
    selectors = [
        "//button[contains(., 'Consultar')]",
        "//button[contains(., 'Pesquisar')]",
        "//button[contains(., 'Buscar')]",
        "//input[@type='submit']",
        "//button[@id='btnPesquisar']",
    ]
    for sel in selectors:
        try:
            btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, sel))
            )
            js_click(driver, btn)
            logger.info(f"Clique no botão de consulta realizado com sucesso ({sel}).")
            return True
        except:
            continue
    raise Exception("Botão de CONSULTAR não encontrado.")

def wait_for_table(driver: WebDriver, timeout=60):
    """
    Função wait_for_table:
    Executa a lógica principal definida nesta função.
    """
    selectors_table = [
        "//table[contains(@class,'table')]",
        "//table[contains(@class,'dataTable')]",
        "//table",
    ]
    start = time.time()
    while time.time() - start < timeout:
        for sel in selectors_table:
            try:
                table = driver.find_element(By.XPATH, sel)
                if table.is_displayed():
                    rows = table.find_elements(By.XPATH, ".//tbody/tr")
                    if len(rows) > 0:
                        logger.info(f"Tabela encontrada com {len(rows)} linhas.")
                        return table
            except:
                pass
        time.sleep(0.5)
    raise Exception("A tabela de resultados não carregou dentro do timeout.")

def get_element_xpath(driver, element):
    """
    Função get_element_xpath:
    Executa a lógica principal definida nesta função.
    """
    return driver.execute_script(
        """
        function absoluteXPath(element) {
            var comp, comps = [];
            var parent = null;
            var xpath = '';
            var getPos = function(element) {
                var position = 1, curNode;
                for (curNode = element.previousSibling; curNode; curNode = curNode.previousSibling){
                    if (curNode.nodeName == element.nodeName)
                        ++position;
                }
                return position;
            }

            if (element instanceof Document) {
                return '/';
            }

            for (; element && !(element instanceof Document); element = element.nodeType ==Node.ATTRIBUTE_NODE ? element.ownerElement : element.parentNode) {
                comp = comps[comps.length] = {};
                switch (element.nodeType) {
                    case Node.TEXT_NODE:
                        comp.name = 'text()';
                        break;
                    case Node.ATTRIBUTE_NODE:
                        comp.name = '@' + element.nodeName;
                        break;
                    case Node.ELEMENT_NODE:
                        comp.name = element.nodeName;
                        break;
                }
                comp.position = getPos(element);
            }

            for (var i = comps.length - 1; i >= 0; i--) {
                comp = comps[i];
                xpath += '/' + comp.name.toLowerCase();
                if (comp.position !== null && comp.position !== 1) {
                    xpath += '[' + comp.position + ']';
                }
            }

            return xpath;
        }
        return absoluteXPath(arguments[0]);
        """,
        element
    )

def extract_table_data(driver, table):
    """
    Função extract_table_data:
    Executa a lógica principal definida nesta função.
    """
    data = []
    rows = table.find_elements(By.XPATH, ".//tbody/tr")
    logger.info(f"Extraindo dados da tabela ({len(rows)} linhas)...")
    for index, row in enumerate(rows, start=1):
        try:
            cols = row.find_elements(By.XPATH, "./td")
            if len(cols) == 0:
                continue
            numero  = cols[0].text.strip()
            titulo  = cols[1].text.strip() if len(cols) > 1 else ""
            unidade = cols[2].text.strip() if len(cols) > 2 else ""
            situacao = cols[3].text.strip() if len(cols) > 3 else ""
            valor = cols[4].text.strip() if len(cols) > 4 else ""
            try:
                action_el = cols[-1].find_element(By.XPATH, ".//button | .//a")
                action_xpath = get_element_xpath(driver, action_el)
            except:
                action_xpath = None
            data.append({
                "index": index,
                "numero": numero,
                "titulo": titulo,
                "unidade": unidade,
                "situacao": situacao,
                "valor": valor,
                "action_xpath": action_xpath,
            })
        except Exception as e:
            logger.error(f"Erro ao extrair linha {index}: {e}")
    return data

def run_search_and_get_table(driver):
    """
    Função run_search_and_get_table:
    Executa a lógica principal definida nesta função.
    """
    logger.info("---- Iniciando CONSULTA ----")
    click_search_button(driver)
    table = wait_for_table(driver)
    extracted = extract_table_data(driver, table)
    logger.info(f"Consulta concluída. {len(extracted)} itens encontrados.")
    return extracted

def _get_paginator_buttons(driver):
    """
    Função _get_paginator_buttons:
    Executa a lógica principal definida nesta função.
    """
    """
    Retorna lista de WebElements dos botões de paginação (se existirem).
    Usa XPath comum de primeNG p-paginator. Retorna [] se não houver.
    """
    try:
        # elementos de paginação (ajuste se necessário)
        items = driver.find_elements(By.XPATH, "//div[contains(@class,'p-paginator')]//button[contains(@class,'p-paginator-element') or contains(@class,'p-paginator-pages') or contains(@class,'p-paginator-pages')]/..//button")
        if items:
            return items
    except Exception:
        pass
    # fallback: procurar botões dentro do bloco com id conhecido (minhauasg)
    try:
        items = driver.find_elements(By.XPATH, "//div[@id='minhauasg']//span[contains(@class,'p-paginator-pages')]/button")
        return items
    except Exception:
        return []

def run_search_and_get_table(driver):
    """
    Função run_search_and_get_table:
    Executa a lógica principal definida nesta função.
    """
    logger.info("---- Iniciando CONSULTA (com paginação) ----")
    click_search_button(driver)
    table = wait_for_table(driver)
    # primeira página
    extracted = extract_table_data(driver, table)

    # detectar e iterar páginas se houver
    paginator_buttons = _get_paginator_buttons(driver)
    if paginator_buttons:
        # extra precaution: collect the page buttons again inside loop because DOM can be re-rendered
        logger.info("Paginator detectado. Iterando páginas...")
        # find number of pages (try to read buttons text)
        try:
            page_btns = driver.find_elements(By.XPATH, "//div[contains(@class,'p-paginator')]//button[not(contains(@class,'p-paginator-first')) and not(contains(@class,'p-paginator-last'))]")
            page_count = len(page_btns)
        except Exception:
            page_count = 0

        # iterate through pages (starting from 2)
        for page_index in range(2, page_count+1 if page_count>0 else 1000):
            try:
                # click page button by position (re-find each time)
                btn = driver.find_element(By.XPATH, f"(//div[contains(@class,'p-paginator')]//button[not(contains(@class,'p-paginator-first')) and not(contains(@class,'p-paginator-last'))])[{page_index}]")
                driver.execute_script("arguments[0].click();", btn)
                # wait for table to refresh
                time.sleep(1)
                table = wait_for_table(driver, timeout=15)
                page_data = extract_table_data(driver, table)
                # if no new rows, break
                if not page_data:
                    break
                extracted.extend(page_data)
            except Exception:
                # if page_index beyond available pages, break
                break
    else:
        logger.info("Nenhum paginator detectado — apenas página atual coletada.")

    logger.info(f"Consulta concluída. {len(extracted)} itens encontrados (todas as páginas).")
    return extracted