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

class CheckpointFailureError(Exception):
    """Exceção levantada quando um Checkpoint Semântico falha."""
    pass
from .config_vba import VBAConfig

logger = logging.getLogger(__name__)

class VBACompat:
    def __init__(self, driver=None):
        # Se o driver não for passado, usa o global
        self._driver = driver
        self.last_handle = None

    @property
    def driver(self):
        if self._driver:
            return self._driver
        return get_driver()

    def slow_down(self):
        """Aplica espera baseada no modo de operação (Item 13)."""
        time.sleep(VBAConfig.get_wait_time())

    def wait_for_new_window(self, original_handles: set, timeout: int = 10) -> bool:
        """
        Espera por uma nova janela/aba ser aberta (Item 7).
        Corrigido para comparar handles em vez de apenas contar a quantidade.
        """
        try:
            def check_new_window(d):
                current_handles = set(d.window_handles)
                new_handles = current_handles - original_handles
                return list(new_handles)[0] if new_handles else False

            new_window_handle = WebDriverWait(self.driver, timeout).until(check_new_window)
            if new_window_handle:
                logger.info(f"Nova janela detectada: {new_window_handle}")
                return True
            return False
        except TimeoutException:
            logger.error("Timeout esperando por nova janela.")
            return False

    def reset_context(self):
        """Garante contexto correto (Item 7)."""
        try:
            self.driver.switch_to.default_content()
            if not self.last_handle:
                self.last_handle = self.driver.window_handles[-1]
            
            if self.driver.current_window_handle != self.last_handle:
                self.driver.switch_to.window(self.last_handle)
        except Exception as e:
            logger.warning(f"Erro ao resetar contexto: {e}")

    def testa_spinner(self, timeout=60):
        """Emula o 'testa_spinner' do VBA."""
        spinner_xpath = "//div[@id='spinner']"
        try:
            WebDriverWait(self.driver, 2).until(EC.presence_of_element_located((By.XPATH, spinner_xpath)))
        except:
            pass

        try:
            WebDriverWait(self.driver, timeout).until(EC.invisibility_of_element_located((By.XPATH, spinner_xpath)))
        except TimeoutException:
            pass
        
        self.slow_down()

    def wait_for_checkpoint(self, xpath, text=None, timeout=30):
        """Checkpoints Semânticos (Item 4 e 11)."""
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
        """Clique seguro seguindo as regras do VBA (Item 6)."""
        self.reset_context()
        try:
            element = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            if scroll:
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(0.5)
            
            element.click()
            self.testa_spinner()
            return True
        except Exception as e:
            logger.error(f"Erro ao clicar em {xpath}: {e}")
            return False

    def validate_table_context(self, expected_title, expected_headers):
        """Validação específica para o Item 8."""
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
