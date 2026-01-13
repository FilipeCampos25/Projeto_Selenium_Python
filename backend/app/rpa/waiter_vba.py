"""
Arquivo: waiter_vba.py
Descrição: Este arquivo faz parte do projeto e foi comentado para explicar a função de cada bloco de código.
"""

# backend/app/rpa/waiter_vba.py
"""
Funções de espera replicando a lógica do VBA.
Baseado na análise do testa_spinner() e outros padrões de espera do VBA.
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException

DEFAULT_TIMEOUT = 30
POLL = 0.1  # 0.1 segundo = TimeValue("00:00:01") / 10 do VBA


def wait_spinner(driver, spinner_xpath, timeout=DEFAULT_TIMEOUT):
    """
    Função wait_spinner:
    Executa a lógica principal definida nesta função.
    """
    """
    Espera spinner sumir - EXATAMENTE como o VBA.
    
    VBA original:
    Sub testa_spinner()
        caminho = "//body/app-root/ng-http-loader/div[@id='spinner']"
        Do
            Application.Wait Now + (TimeValue("00:00:01") / 10)
        Loop While driver.FindElementByXPath(caminho, timeout:=1, Raise:=False).IsPresent
    End Sub
    
    Python equivalente:
    - Verifica a cada 0.1 segundo (POLL)
    - Continua enquanto spinner estiver presente E visível
    - Retorna True quando spinner desaparece ou não está visível
    """
    end_time = time.time() + timeout
    
    while time.time() < end_time:
        try:
            # Tenta encontrar o spinner
            spinner = driver.find_element(By.XPATH, spinner_xpath)
            
            # Se encontrou, verifica se está visível
            if spinner.is_displayed():
                # Spinner visível, aguarda
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
        
        time.sleep(POLL)
    
    # Timeout atingido, mas não é erro crítico
    return True


def wait_element_present(driver, xpath, timeout=DEFAULT_TIMEOUT):
    """
    Função wait_element_present:
    Executa a lógica principal definida nesta função.
    """
    """
    Aguarda elemento estar presente no DOM.
    
    VBA original:
    Do While Not driver.IsElementPresent(By.XPath("..."))
    Loop
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
    Função wait_element_visible:
    Executa a lógica principal definida nesta função.
    """
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
    Função wait_element_clickable:
    Executa a lógica principal definida nesta função.
    """
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
    Função wait_element_invisible:
    Executa a lógica principal definida nesta função.
    """
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
    Função wait_ready:
    Executa a lógica principal definida nesta função.
    """
    """
    Espera o documento carregar completamente.
    """
    end_time = time.time() + timeout
    
    while time.time() < end_time:
        try:
            state = driver.execute_script("return document.readyState")
            if state == "complete":
                return True
        except Exception:
            pass
        time.sleep(POLL)
    
    raise TimeoutException("Página não carregou completamente.")


def wait_table_ready(driver, table_xpath, timeout=DEFAULT_TIMEOUT):
    """
    Função wait_table_ready:
    Executa a lógica principal definida nesta função.
    """
    """
    Espera tabela existir E conter linhas.
    """
    end_time = time.time() + timeout
    
    while time.time() < end_time:
        try:
            table = driver.find_element(By.XPATH, table_xpath)
            rows = table.find_elements(By.XPATH, ".//tbody/tr")
            if rows and len(rows) > 0:
                return True
        except Exception:
            pass
        time.sleep(POLL)
    
    raise TimeoutException("Tabela não ficou pronta.")


def wait_text_present(driver, xpath, text, timeout=DEFAULT_TIMEOUT):
    """
    Função wait_text_present:
    Executa a lógica principal definida nesta função.
    """
    """
    Aguarda texto específico estar presente em elemento.
    """
    end_time = time.time() + timeout
    
    while time.time() < end_time:
        try:
            element = driver.find_element(By.XPATH, xpath)
            if text in element.text:
                return True
        except Exception:
            pass
        time.sleep(POLL)
    
    return False


def wait_current_page(driver, page_xpath, expected_page, timeout=DEFAULT_TIMEOUT):
    """
    Função wait_current_page:
    Executa a lógica principal definida nesta função.
    """
    """
    Aguarda até que a página atual seja a esperada.
    
    VBA original:
    Do Until CInt(Trim(driver.FindElementByXPath("...").Text)) = pos
        pos = pos
    Loop
    """
    end_time = time.time() + timeout
    
    while time.time() < end_time:
        try:
            element = driver.find_element(By.XPATH, page_xpath)
            current_text = element.text.strip()
            if current_text and int(current_text) == expected_page:
                return True
        except Exception:
            pass
        time.sleep(POLL)
    
    return False
