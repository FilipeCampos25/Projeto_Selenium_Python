"""
vba_compat.py
Consolida o Modo Compatibilidade VBA com esperas dinâmicas.
Removidos sleeps estáticos baseados em comentários do VBA original.
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

    def slow_down(self):
        """
        Aplica espera dinâmica apenas se necessário.
        Reduzido ou removido conforme orientação de evitar sleeps sem contexto.
        """
        wait_time = VBAConfig.get_wait_time()
        if wait_time > 0.1:
            time.sleep(wait_time)

    def wait_for_new_window(self, original_handles: set, timeout: int = 10):
        """
        Valida que a navegação ocorreu esperando um estado estável.
        Substituído sleep(2) por verificação de readyState.
        """
        logger.info("Validando estabilização da página.")
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            # Em vez de sleep(2), verificamos se o spinner (se existir) sumiu
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
        """
        Emula o 'testa_spinner' do VBA com espera dinâmica.
        """
        spinner_xpath = "//div[@id='spinner']"
        # Curta espera para ver se o spinner aparece
        try:
            WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, spinner_xpath)))
        except:
            return # Se não apareceu em 1s, assume que não virá ou já passou

        # Se apareceu, espera sumir
        try:
            WebDriverWait(self.driver, timeout).until(EC.invisibility_of_element_located((By.XPATH, spinner_xpath)))
        except TimeoutException:
            logger.warning(f"Spinner ainda visível após {timeout}s")

    def wait_for_checkpoint(self, xpath, text=None, timeout=30):
        """Checkpoints Semânticos com espera dinâmica."""
        self.reset_context()
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((By.XPATH, xpath))
            )
            if text and text.lower() not in element.text.lower():
                # Tenta esperar o texto mudar dinamicamente (timeout curto)
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
        """Clique seguro sem sleeps desnecessários."""
        self.reset_context()
        try:
            element = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            if scroll:
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            
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
            # Espera dinâmica pelos cabeçalhos
            WebDriverWait(self.driver, 10).until(
                lambda d: len(d.find_elements(By.XPATH, "//thead//th")) > 0
            )
            table_headers = self.driver.find_elements(By.XPATH, "//thead//th")
            headers_text = [th.text.strip() for th in table_headers if th.text.strip()]
            return all(h in headers_text for h in expected_headers)
        except Exception:
            return False
