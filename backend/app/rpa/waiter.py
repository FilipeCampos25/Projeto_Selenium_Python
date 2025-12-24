"""
waiter.py
Refatorado para incluir Checkpoints Semânticos e Separação de Coleta (Itens 4 e 5).
Garante que a navegação seja validada antes de qualquer extração de dados.
"""
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30
POLL = 0.5 # Aumentado levemente para emular VBA

def wait_ready(driver, timeout=DEFAULT_TIMEOUT):
    """Espera o documento carregar completamente."""
    for _ in range(int(timeout / POLL)):
        try:
            state = driver.execute_script("return document.readyState")
            if state == "complete":
                return True
        except Exception:
            pass
        time.sleep(POLL)
    raise TimeoutException("Página não carregou completamente.")

def wait_spinner(driver, spinner_xpath, timeout=DEFAULT_TIMEOUT):
    """Espera spinner sumir (Item 4.1 - Não confiar apenas no spinner)."""
    end = time.time() + timeout
    # Primeiro espera o spinner aparecer (se for rápido demais pode perder)
    try:
        WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.XPATH, spinner_xpath)))
    except:
        pass
        
    while time.time() < end:
        try:
            spinner = driver.find_element(By.XPATH, spinner_xpath)
            if not spinner.is_displayed():
                return True
        except Exception:
            return True
        time.sleep(POLL)
    return True

def validate_checkpoint(driver, xpath, expected_text=None, timeout=DEFAULT_TIMEOUT):
    """
    Item 4.2: Checkpoint Semântico.
    Valida se a tela está correta antes de prosseguir.
    """
    try:
        element = WebDriverWait(driver, timeout, POLL).until(
            EC.visibility_of_element_located((By.XPATH, xpath))
        )
        if expected_text:
            actual_text = element.text.strip()
            if expected_text.lower() not in actual_text.lower():
                logger.error(f"Checkpoint falhou: Esperado '{expected_text}', obtido '{actual_text}'")
                return False
        logger.info(f"Checkpoint validado: {xpath}")
        return True
    except TimeoutException:
        logger.error(f"Checkpoint falhou: Elemento {xpath} não visível após {timeout}s")
        return False

def confirm_navigation_before_collection(driver, checkpoint_xpath, expected_text=None):
    """
    Item 5: Separação Obrigatória entre Navegação e Coleta.
    """
    wait_ready(driver)
    if not validate_checkpoint(driver, checkpoint_xpath, expected_text):
        raise RuntimeError(f"Navegação não confirmada para o checkpoint: {checkpoint_xpath}")
    
    # Pequena espera adicional após confirmação (Modo Compatibilidade)
    time.sleep(1)
    return True

def wait_visible(driver, xpath, timeout=DEFAULT_TIMEOUT):
    return WebDriverWait(driver, timeout, POLL, ignored_exceptions=(StaleElementReferenceException,)).until(
        EC.visibility_of_element_located((By.XPATH, xpath))
    )

def wait_clickable(driver, xpath, timeout=DEFAULT_TIMEOUT):
    return WebDriverWait(driver, timeout, POLL, ignored_exceptions=(StaleElementReferenceException,)).until(
        EC.element_to_be_clickable((By.XPATH, xpath))
    )

def wait_table_ready(driver, table_xpath, expected_headers=None, timeout=DEFAULT_TIMEOUT):
    """
    Item 8: Valida se a tabela está pronta E se os cabeçalhos batem.
    """
    end = time.time() + timeout
    while time.time() < end:
        try:
            table = driver.find_element(By.XPATH, table_xpath)
            rows = table.find_elements(By.XPATH, ".//tbody/tr")
            if rows:
                if expected_headers:
                    headers = [th.text.strip() for th in table.find_elements(By.XPATH, ".//thead//th") if th.text.strip()]
                    if all(h in headers for h in expected_headers):
                        return True
                    else:
                        logger.warning(f"Cabeçalhos não batem. Esperado: {expected_headers}, Obtido: {headers}")
                else:
                    return True
        except Exception:
            pass
        time.sleep(POLL)
    raise TimeoutException("Tabela não ficou pronta ou cabeçalhos inválidos.")
