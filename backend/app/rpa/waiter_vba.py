"""
Arquivo: waiter_vba.py
Descrição: Este arquivo faz parte do projeto e foi otimizado para remover sleeps redundantes herdados do VBA.
"""

# backend/app/rpa/waiter_vba.py
"""
Funções de espera replicando a lógica do VBA, mas otimizadas para Python/Selenium.
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException

DEFAULT_TIMEOUT = 30
POLL = 0.1  # 0.1 segundo


def wait_spinner(driver, spinner_xpath, timeout=DEFAULT_TIMEOUT):
    """
    Espera spinner sumir.
    """
    end_time = time.time() + timeout
    
    while time.time() < end_time:
        try:
            # Tenta encontrar o spinner
            spinner = driver.find_element(By.XPATH, spinner_xpath)
            
            # Se encontrou, verifica se está visível
            if spinner.is_displayed():
                # Spinner visível, aguarda o próximo poll
                time.sleep(POLL)
                continue
            else:
                # Spinner não visível, pode prosseguir
                return True
                
        except (NoSuchElementException, StaleElementReferenceException):
            # Spinner não existe ou foi removido do DOM, pode prosseguir
            return True
        except Exception:
            # Qualquer outro erro, considera que spinner sumiu
            return True
        
        # Removido sleep(POLL) extra no final do loop, já existe um dentro do if is_displayed
    
    return True


def wait_element_present(driver, xpath, timeout=DEFAULT_TIMEOUT):
    """
    Aguarda elemento estar presente no DOM.
    """
    try:
        WebDriverWait(driver, timeout, poll_frequency=POLL).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        return True
    except TimeoutException:
        return False


def wait_element_visible(driver, xpath, timeout=DEFAULT_TIMEOUT):
    """
    Aguarda elemento estar visível.
    """
    try:
        WebDriverWait(driver, timeout, poll_frequency=POLL).until(
            EC.visibility_of_element_located((By.XPATH, xpath))
        )
        return True
    except TimeoutException:
        return False


def wait_element_clickable(driver, xpath, timeout=DEFAULT_TIMEOUT):
    """
    Aguarda elemento estar clicável.
    """
    try:
        element = WebDriverWait(driver, timeout, poll_frequency=POLL).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        return element
    except TimeoutException:
        return None


def wait_element_invisible(driver, xpath, timeout=DEFAULT_TIMEOUT):
    """
    Aguarda elemento ficar invisível ou ser removido do DOM.
    """
    try:
        WebDriverWait(driver, timeout, poll_frequency=POLL).until(
            EC.invisibility_of_element_located((By.XPATH, xpath))
        )
        return True
    except TimeoutException:
        return False


def wait_ready(driver, timeout=DEFAULT_TIMEOUT):
    """
    Espera o documento carregar completamente.
    """
    try:
        WebDriverWait(driver, timeout, poll_frequency=POLL).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        return True
    except TimeoutException:
        raise TimeoutException("Página não carregou completamente.")


def wait_table_ready(driver, table_xpath, timeout=DEFAULT_TIMEOUT):
    """
    Espera tabela existir E conter linhas.
    """
    try:
        WebDriverWait(driver, timeout, poll_frequency=POLL).until(
            lambda d: len(d.find_elements(By.XPATH, f"{table_xpath}//tbody/tr")) > 0
        )
        return True
    except TimeoutException:
        raise TimeoutException("Tabela não ficou pronta.")


def wait_text_present(driver, xpath, text, timeout=DEFAULT_TIMEOUT):
    """
    Aguarda texto específico estar presente em elemento.
    """
    try:
        WebDriverWait(driver, timeout, poll_frequency=POLL).until(
            EC.text_to_be_present_in_element((By.XPATH, xpath), text)
        )
        return True
    except TimeoutException:
        return False


def wait_current_page(driver, page_xpath, expected_page, timeout=DEFAULT_TIMEOUT):
    """
    Aguarda até que a página atual seja a esperada.
    """
    try:
        WebDriverWait(driver, timeout, poll_frequency=POLL).until(
            lambda d: d.find_element(By.XPATH, page_xpath).text.strip() == str(expected_page)
        )
        return True
    except TimeoutException:
        return False
