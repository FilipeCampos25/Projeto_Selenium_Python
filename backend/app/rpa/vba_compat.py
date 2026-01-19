"""
vba_compat.py
Consolida o Modo Compatibilidade VBA (Itens 2, 3, 7 e 13).
Integrado com config_vba para permitir otimização futura.
"""
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchWindowException
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

    def wait(self, seconds: float):
        """
        Emula Application.Wait do VBA (Passo 2.2).
        """
        logger.debug(f"[LOG-VBA] Aguardando {seconds}s (Application.Wait)")
        time.sleep(seconds)

    def wait_for_new_window(self, original_handles: set, timeout: int = 10):
        logger.warning(
            "wait_for_new_window: nenhuma nova janela esperada. "
            "Validando navegação na mesma aba."
        )
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            time.sleep(2)
            logger.info("Navegação confirmada na mesma aba (sem nova janela).")
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
        """
        Emula o 'testa_spinner' do VBA (Passo 2.2).
        Fidelidade total ao loop: Do ... Loop While IsPresent.
        """
        spinner_xpath = "//body/app-root/ng-http-loader/div[@id='spinner']"
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # No VBA, IsPresent verifica a existência. find_elements é o equivalente que não levanta exceção.
                spinners = self.driver.find_elements(By.XPATH, spinner_xpath)
                if not spinners:
                    break # Sai do loop se o spinner não existe
                
                # Se o spinner existe, espera 0.1s como no VBA
                self.wait(0.1)
            except Exception:
                break # Sai do loop em caso de erro inesperado

    def wait_for_checkpoint(self, xpath, text=None, timeout=30):
        self.reset_context()
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((By.XPATH, xpath))
            )
            if text and text.lower() not in element.text.lower():
                logger.error(f"Checkpoint falhou: Texto esperado '{text}' não encontrado no elemento {xpath}.")
                raise CheckpointFailureError(f"Texto do checkpoint não corresponde: Esperado='{text}', Encontrado='{element.text}'")
            logger.info(f"Checkpoint bem-sucedido: {xpath}")
            return True
        except TimeoutException:
            logger.error(f"Checkpoint falhou: Elemento {xpath} não encontrado no tempo limite.")
            raise CheckpointFailureError(f"Elemento de checkpoint não encontrado: {xpath}")

    def safe_click(self, xpath, scroll=True):
        self.reset_context()
        try:
            self.testa_spinner(timeout=10)
            element = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            if scroll:
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(0.2)
            try:
                element.click()
            except Exception as e_click:
                logger.debug(f"Regular click failed ({e_click}), trying JS click for {xpath}")
                self.driver.execute_script("arguments[0].click();", element)
            return True
        except Exception as e:
            logger.error(f"Erro ao clicar em {xpath}: {e}")
            return False

    def validate_table_context(self, expected_title, expected_headers):
        title_xpath = "//span[text()='Planejamento e Gerenciamento de Contratações']"
        try:
            self.wait_for_checkpoint(title_xpath, expected_title)
        except CheckpointFailureError as e:
            logger.error(f"Falha na validação do título da página: {e}")
            return False
        
        try:
            table_headers = self.driver.find_elements(By.XPATH, "//thead//th")
            headers_text = [th.text.strip() for th in table_headers if th.text.strip()]
            return all(h in headers_text for h in expected_headers)
        except Exception as e:
            logger.error(f"Erro ao validar cabeçalhos da tabela: {e}")
            return False
