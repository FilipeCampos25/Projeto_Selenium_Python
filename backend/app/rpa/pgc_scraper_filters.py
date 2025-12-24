"""
pgc_scraper_filters.py

Funções para selecionar filtros: ano, unidade, pta.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging

logger = logging.getLogger(__name__)

def wait_el(driver: WebDriver, by, selector, timeout=30):
    """
    Função wait_el:
    Executa a lógica principal definida nesta função.
    """
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, selector))
    )

def wait_visible(driver: WebDriver, by, selector, timeout=30):
    """
    Função wait_visible:
    Executa a lógica principal definida nesta função.
    """
    return WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located((by, selector))
    )

def js_click(driver, element):
    """
    Função js_click:
    Executa a lógica principal definida nesta função.
    """
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
    driver.execute_script("arguments[0].click();", element)

def open_and_select_option(driver: WebDriver, dropdown_xpath: str, item_text: str, timeout=30):
    """
    Função open_and_select_option:
    Executa a lógica principal definida nesta função.
    """
    logger.info(f"Abrindo dropdown: {dropdown_xpath}")
    dd = wait_visible(driver, By.XPATH, dropdown_xpath, timeout)
    js_click(driver, dd)
    time.sleep(0.8)

    logger.info(f"Selecionando opção: {item_text}")
    item_xpath = f".//*[normalize-space(text())='{item_text}']"

    try:
        item = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, item_xpath))
        )
        js_click(driver, item)
        time.sleep(0.5)
        return True
    except Exception:
        pass

    try:
        item = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, f"//{item_xpath}"))
        )
        js_click(driver, item)
        time.sleep(0.5)
        return True
    except Exception as e:
        logger.error(f"Não foi possível selecionar '{item_text}': {e}")
        return False

def select_year(driver: WebDriver, ano: str):
    """
    Função select_year:
    Executa a lógica principal definida nesta função.
    """
    DROPDOWN_ANO = "//div[@id='filtro-ano']"
    logger.info(f"Selecionando ANO = {ano}")
    ok = open_and_select_option(driver, DROPDOWN_ANO, ano)
    if not ok:
        raise Exception(f"Falha ao selecionar ano {ano}")
    time.sleep(1)
    return True

def select_unit(driver: WebDriver, unidade: str):
    """
    Função select_unit:
    Executa a lógica principal definida nesta função.
    """
    DROPDOWN_UG = "//div[@id='filtro-ug']"
    logger.info(f"Selecionando UNIDADE = {unidade}")
    ok = open_and_select_option(driver, DROPDOWN_UG, unidade)
    if not ok:
        raise Exception(f"Falha ao selecionar unidade {unidade}")
    time.sleep(1)
    return True

def select_pta(driver: WebDriver, pta: str):
    """
    Função select_pta:
    Executa a lógica principal definida nesta função.
    """
    DROPDOWN_PTA = "//div[@id='filtro-pta']"
    logger.info(f"Selecionando PTA = {pta}")
    ok = open_and_select_option(driver, DROPDOWN_PTA, pta)
    if not ok:
        raise Exception(f"Falha ao selecionar PTA {pta}")
    time.sleep(1)
    return True

def select_filters(driver: WebDriver, ano: str, unidade: str, pta: str):
    """
    Função select_filters:
    Executa a lógica principal definida nesta função.
    """
    logger.info("---- Iniciando seleção de filtros PGC ----")
    select_year(driver, ano)
    select_unit(driver, unidade)
    select_pta(driver, pta)
    logger.info("---- Seleção de filtros concluída ----")
    return True
