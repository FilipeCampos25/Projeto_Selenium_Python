"""
vba_compat.py
Consolida o Modo Compatibilidade VBA com esperas dinâmicas e micro-estabilidade.
"""
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchWindowException, 
    ElementClickInterceptedException,
    StaleElementReferenceException
)
from .driver_global import get_driver
from .config_vba import VBAConfig

class CheckpointFailureError(Exception):
    """Exceção levantada quando um Checkpoint Semântico falha."""
    pass

logger = logging.getLogger(__name__)

class VBACompat:
    def __init__(self, driver=None):
        self._driver = driver
        self.last_handle = None

    @property
    def driver(self):
        if self._driver:
            return self._driver
        return get_driver()

    def slow_down(self):
        """Aplica micro-espera de estabilidade apenas se necessário."""
        wait_time = VBAConfig.get_wait_time()
        if wait_time > 0:
            # Reduzido para o mínimo necessário para estabilidade de rede/JS
            time.sleep(min(wait_time, 0.1))

    def wait_for_new_window(self, original_handles: set, timeout: int = 10):
        logger.info("Validando estabilização da página.")
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            # Removido sleep(0.5) redundante, testa_spinner já lida com a espera necessária
            self.testa_spinner(timeout=5)
            return True
        except TimeoutException:
            logger.error("Timeout aguardando estabilização da página.")
            return False

    def reset_context(self):
        try:
            self.driver.switch_to.default_content()
            if not self.last_handle:
                self.last_handle = self.driver.window_handles[-1]
            
            if self.driver.current_window_handle != self.last_handle:
                self.driver.switch_to.window(self.last_handle)
        except Exception as e:
            logger.warning(f"Erro ao resetar contexto: {e}")

    def testa_spinner(self, timeout=60):
        spinner_xpath = "//div[@id='spinner']"
        try:
            # Verifica se o spinner aparece em 1.5s (tempo para o JS disparar a requisição)
            WebDriverWait(self.driver, 1.5).until(EC.presence_of_element_located((By.XPATH, spinner_xpath)))
            # Se apareceu, espera sumir
            WebDriverWait(self.driver, timeout).until(EC.invisibility_of_element_located((By.XPATH, spinner_xpath)))
            # Removido sleep(0.2) redundante pós-spinner
        except:
            pass

    def wait_for_checkpoint(self, xpath, text=None, timeout=30):
        self.reset_context()
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((By.XPATH, xpath))
            )
            if text and text.lower() not in element.text.lower():
                try:
                    WebDriverWait(self.driver, 5).until(
                        lambda d: text.lower() in d.find_element(By.XPATH, xpath).text.lower()
                    )
                except TimeoutException:
                    logger.error(f"Checkpoint falhou: Texto esperado '{text}' não encontrado.")
                    raise CheckpointFailureError(f"Texto não corresponde: Esperado='{text}'")
            
            logger.info(f"Checkpoint bem-sucedido: {xpath}")
            return True
        except TimeoutException:
            logger.error(f"Checkpoint falhou: Elemento {xpath} não encontrado.")
            raise CheckpointFailureError(f"Elemento não encontrado: {xpath}")

    def safe_click(self, xpath, scroll=True):
        """Clique seguro com tratamento de interceptação."""
        self.reset_context()
        try:
            element = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            if scroll:
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                # Removido sleep(0.3) pós-scroll, WebDriverWait já garante que o elemento está clicável
            
            try:
                element.click()
            except (ElementClickInterceptedException, StaleElementReferenceException):
                # Mantido sleep(0.8) apenas em caso de erro real de interceptação (overlay)
                time.sleep(0.8)
                element = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                element.click()
                
            self.testa_spinner()
            return True
        except Exception as e:
            logger.error(f"Erro ao clicar em {xpath}: {e}")
            return False

    def validate_table_context(self, expected_title, expected_headers):
        title_xpath = "//span[text()='Planejamento e Gerenciamento de Contratações']"
        try:
            self.wait_for_checkpoint(title_xpath, expected_title)
        except CheckpointFailureError:
            return False
        
        try:
            WebDriverWait(self.driver, 10).until(
                lambda d: len(d.find_elements(By.XPATH, "//thead//th")) > 0
            )
            table_headers = self.driver.find_elements(By.XPATH, "//thead//th")
            headers_text = [th.text.strip() for th in table_headers if th.text.strip()]
            return all(h in headers_text for h in expected_headers)
        except Exception:
            return False
