"""
semantic_waiter.py

Implementa os Checkpoints Semânticos (Item 4) para garantir que a navegação
esteja no estado lógico correto antes de prosseguir.
"""
import logging
from typing import Dict, Any
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

logger = logging.getLogger(__name__)

def wait_for_semantic_checkpoint(
    driver: WebDriver,
    checkpoint_name: str,
    xpaths_to_check: Dict[str, str],
    timeout: int = 30
) -> bool:
    """
    Função genérica para esperar por um ou mais elementos semânticos.
    O checkpoint é considerado bem-sucedido se TODOS os XPATHs forem encontrados.
    """
    logger.info(f"Aguardando Checkpoint Semântico: {checkpoint_name}...")
    
    # A espera é feita em um loop para garantir que todos os elementos sejam encontrados
    # dentro do timeout total.
    
    all_found = True
    for key, xpath in xpaths_to_check.items():
        try:
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            logger.debug(f"Elemento semântico '{key}' encontrado.")
        except TimeoutException:
            logger.error(f"Checkpoint FALHOU: Elemento semântico '{key}' não encontrado em {timeout}s.")
            all_found = False
            break
        except Exception as e:
            logger.error(f"Erro inesperado ao checar '{key}': {e}")
            all_found = False
            break

    if all_found:
        logger.info(f"Checkpoint Semântico '{checkpoint_name}' CONCLUÍDO com sucesso.")
    else:
        logger.error(f"Checkpoint Semântico '{checkpoint_name}' FALHOU.")
        
    return all_found

def checkpoint_pgc_main_page(driver: WebDriver, XPATHS: Dict[str, Any]) -> bool:
    """
    Checkpoint para a página principal do PGC (após login e troca de janela).
    Baseado no Item 11 da migracao.txt.
    """
    xpaths_to_check = {
        "titulo_pgc": XPATHS["login"]["span_pgc_title"], # Texto “Planejamento e Gerenciamento de Contratações”
        "menu_pca": XPATHS["pca_selection"]["dropdown_pca"], # Presença do menu PCA
        "container_principal": XPATHS["pca_selection"]["main_container"], # Presença do container principal
    }
    return wait_for_semantic_checkpoint(driver, "Página Principal PGC", xpaths_to_check)

def checkpoint_dfd_list_page(driver: WebDriver, XPATHS: Dict[str, Any]) -> bool:
    """
    Checkpoint para a página de listagem de DFDs (após seleção de PCA e UASG).
    """
    xpaths_to_check = {
        "titulo_pgc": XPATHS["login"]["span_pgc_title"], # Confirma que ainda está no PGC
        "tabela_principal": XPATHS["table"]["main_table"], # Presença da tabela principal
        "paginacao": XPATHS["pagination"]["btns_pages"], # Presença dos botões de paginação
    }
    return wait_for_semantic_checkpoint(driver, "Página de Listagem de DFDs", xpaths_to_check)
