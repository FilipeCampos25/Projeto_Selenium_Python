"""
context_manager.py

Módulo para gerenciar o contexto do Selenium (janelas/abas e frames),
implementando a regra de ouro do Item 7 da migracao.txt.
"""
import logging
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import NoSuchWindowException

logger = logging.getLogger(__name__)

def reset_context(driver: WebDriver):
    """
    Implementa a regra de ouro do Item 7: Resetar contexto e garantir aba correta.
    Antes de QUALQUER leitura ou clique:
        - Resetar contexto: default_content
        - Garantir aba correta: última aba ativa
    """
    # 1. Resetar contexto para o conteúdo principal (default_content)
    try:
        driver.switch_to.default_content()
        logger.debug("Contexto resetado para default_content.")
    except Exception as e:
        logger.warning(f"Falha ao resetar para default_content: {e}")
        # A falha aqui pode ser ignorada se o driver já estiver no default_content

    # 2. Garantir aba correta: última aba ativa
    # Isso é crucial para sistemas que abrem novas janelas/abas (como o PGC)
    try:
        window_handles = driver.window_handles
        if len(window_handles) > 0:
            # A última handle é geralmente a mais recente ou a que o driver está usando
            last_handle = window_handles[-1]
            driver.switch_to.window(last_handle)
            logger.debug(f"Mudou para a última janela/aba ativa: {driver.title}")
        else:
            logger.error("Nenhuma janela/aba encontrada. O driver pode estar em um estado inválido.")
    except NoSuchWindowException:
        logger.error("Falha ao mudar para a última janela/aba. A janela pode ter sido fechada.")
        # Se a janela principal for perdida, o fluxo deve falhar, mas tentamos continuar
        # para imitar o comportamento "ignora erros" do VBA (Item 10)
    except Exception as e:
        logger.error(f"Erro inesperado ao gerenciar janelas: {e}")

def switch_to_window_by_title(driver: WebDriver, title_part: str):
    """
    Função auxiliar para a etapa 9 do login (A_Loga_Acessa_PGC),
    que procura a janela pelo título.
    """
    original_handle = driver.current_window_handle
    found = False
    
    for handle in driver.window_handles:
        try:
            driver.switch_to.window(handle)
            if title_part in driver.title:
                logger.info(f"Janela do PGC encontrada: {driver.title}")
                found = True
                break
        except NoSuchWindowException:
            logger.warning(f"Handle de janela {handle} não existe mais.")
            continue
        except Exception as e:
            logger.error(f"Erro ao tentar inspecionar janela {handle}: {e}")
            continue
            
    if not found:
        logger.error(f"Janela com título '{title_part}' não encontrada. Voltando para a original.")
        try:
            driver.switch_to.window(original_handle)
        except NoSuchWindowException:
            logger.error("Janela original também não existe mais.")
            
    return found
