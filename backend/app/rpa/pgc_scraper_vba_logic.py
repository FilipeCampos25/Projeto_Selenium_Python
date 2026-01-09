"""
pgc_scraper_vba_logic.py
Scraper do PGC replicando FIELMENTE a lógica do VBA.
Integrado com VBACompat para garantir equivalência e estabilidade.
"""
import json
import time
import logging
import os
from typing import Dict, List, Optional, Any
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from .vba_compat import VBACompat, CheckpointFailureError
from .driver_global import get_driver, set_driver, close_driver

logger = logging.getLogger(__name__)

# Carregar XPaths do arquivo JSON
XPATHS_FILE = os.path.join(os.path.dirname(__file__), "pgc_xpaths.json")
with open(XPATHS_FILE, 'r', encoding='utf-8') as f:
    XPATHS = json.load(f)

class PGCScraperVBA:
    def __init__(self, driver: Optional[WebDriver] = None, ano_ref: str = "2025"):
        # Se o driver não for passado, ele tentará usar o global via VBACompat
        self._driver = driver
        self.ano_ref = ano_ref
        self.compat = VBACompat(driver)
        self.data_collected = []

    @property
    def driver(self):
        if self._driver:
            return self._driver
        return get_driver()

    def A_Loga_Acessa_PGC(self) -> bool:
        """Replica Sub A_Loga_Acessa_PGC() do VBA - Login manual via noVNC."""
        logger.info("=== ABRINDO LOGIN NO PGC - AGUARDE LOGIN MANUAL VIA VNC ===")
        
        self.driver.get(XPATHS["login"]["url"])
        self.driver.maximize_window()
        
        # Checkpoint: Portal aberto
        try:
            self.compat.wait_for_checkpoint(XPATHS["login"]["btn_expand_governo"])
        except CheckpointFailureError:
            logger.error("Falha no checkpoint inicial (btn_expand_governo). Abortando.")
            return False
        self.compat.safe_click(XPATHS["login"]["btn_expand_governo"])
        
        # Scroll down (VBA)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        # Aguarda login manual do usuário via noVNC
        logger.info("Aguardando login manual... Abra o VNC em http://localhost:7900 e faça o login.")
        try:
            self.compat.wait_for_checkpoint(XPATHS["login"]["span_pgc_title"], "Planejamento e Gerenciamento de Contratações")
        except CheckpointFailureError:
            logger.error("Falha no checkpoint pós-login (Título PGC). Verifique se o login foi feito.")
            return False
        
        # Clica no PGC
        self.compat.safe_click(XPATHS["login"]["div_pgc_access"])
        
        # Troca de janela (Item 7)
        original_handles = set(self.driver.window_handles)
        if not self.compat.wait_for_new_window(original_handles):
            logger.error("Falha ao esperar pela nova janela do PGC.")
            return False
            
        for handle in self.driver.window_handles:
            self.driver.switch_to.window(handle)
            if XPATHS["login"]["window_title"] in self.driver.title:
                self.compat.last_handle = handle
                break
        else:
            logger.error("Não encontrou a janela do PGC.")
            return False
        
        logger.info("Login manual concluído e PGC acessado com sucesso.")
        return True

    def A1_Demandas_DFD_PCA(self) -> List[Dict[str, Any]]:
        """Replica Sub A1_Demandas_DFD_PCA() do VBA."""
        logger.info("=== INICIANDO COLETA DE DFDs (Lógica VBA) ===")
        
        # Validação de Contexto (Item 8 e 11)
        try:
            self.compat.validate_table_context("Planejamento e Gerenciamento de Contratações", ["DFD", "Requisitante", "Valor"])
        except CheckpointFailureError as e:
            logger.error(f"Contexto da tabela inválido. Abortando coleta: {e}")
            return []

        # Seleção de PCA
        self.compat.safe_click(XPATHS["pca_selection"]["dropdown_pca"])
        li_pca_xpath = XPATHS["pca_selection"]["li_pca_ano_template"].replace("{ano}", self.ano_ref)
        self.compat.safe_click(li_pca_xpath)
        
        # Seleção UASG
        self.compat.safe_click(f"//*[@id='{XPATHS['pca_selection']['radio_minha_uasg_id']}']")
        
        # Aguarda o carregamento da tabela de DFDs (Substitui o time.sleep(5) do VBA)
        # Usamos um checkpoint semântico para garantir que a tela está pronta para coleta.
        try:
            self.compat.wait_for_checkpoint(XPATHS["table"]["rows"], timeout=15)
        except CheckpointFailureError:
            logger.error("Falha no checkpoint da tabela de DFDs após seleção de PCA/UASG.")
            return []
        self.compat.testa_spinner()

        # Coleta de dados com paginação
        all_data = []
        pos = 1
        posM = self._get_total_pages()
        
        while pos <= posM:
            logger.info(f"Coletando página {pos} de {posM}...")
            page_data = self._read_current_table()
            all_data.extend(page_data)
            
            if pos < posM:
                if not self._go_to_next_page(pos + 1):
                    break
            pos += 1
            
        self.data_collected = all_data
        return all_data

    def _get_total_pages(self) -> int:
        try:
            btns = self.driver.find_elements(By.XPATH, XPATHS["pagination"]["btns_pages"])
            pages = [int(b.text.strip()) for b in btns if b.text.strip().isdigit()]
            return max(pages) if pages else 1
        except Exception as e:
            logger.warning(f"Erro ao calcular total de páginas, assumindo 1: {e}")
            return 1

    def _read_current_table(self) -> List[Dict[str, Any]]:
        """Lê a tabela atual validando cada linha (Item 8)."""
        rows_data = []
        rows = self.driver.find_elements(By.XPATH, XPATHS["table"]["rows"])
        
        for row in rows:
            try:
                cols = row.find_elements(By.XPATH, "./td")
                if len(cols) < 10: continue
                
                # Índices baseados no pgc_xpaths.json (mapeados do VBA)
                idx = XPATHS["table_columns"]
                item = {
                    "dfd": cols[idx["index_dfd"]-1].text.strip(),
                    "requisitante": cols[idx["index_requisitante"]-1].text.strip(),
                    "descricao": cols[idx["index_descricao"]-1].text.strip(),
                    "valor": self._parse_currency(cols[idx["index_valor"]-1].text.strip()),
                    "situacao": cols[idx["index_situacao"]-1].text.strip(),
                    "coletado_em": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                rows_data.append(item)
            except Exception as e:
                logger.warning(f"Erro ao ler linha da tabela: {e}")
                
        return rows_data

    def _go_to_next_page(self, target_page: int) -> bool:
        try:
            btn_next = self.driver.find_element(By.XPATH, XPATHS["pagination"]["btn_next"])
            self.compat.safe_click(XPATHS["pagination"]["btn_next"])
            # Valida se mudou de página (Item 4.2)
            checkpoint_page = f"//button[contains(@class, 'p-highlight') and text()='{target_page}']"
            # O wait_for_checkpoint agora lança exceção, o que garante o bloqueio real
            self.compat.wait_for_checkpoint(checkpoint_page, timeout=10)
            return True
        except CheckpointFailureError as e:
            logger.error(f"Falha ao avançar para a página {target_page}. Abortando paginação: {e}")
            return False
        except Exception as e:
            logger.error(f"Erro inesperado ao avançar para a página {target_page}: {e}")
            return False

    def _parse_currency(self, value_str: str) -> float:
        try:
            # Remove "R$", pontos de milhar e troca vírgula por ponto
            clean_value = value_str.replace("R$", "").replace(".", "").replace(",", ".").strip()
            return float(clean_value)
        except Exception as e:
            logger.warning(f"Erro ao converter valor monetário '{value_str}', retornando 0.0: {e}")
            return 0.0

def run_pgc_scraper_vba(ano_ref: str = "2025") -> List[Dict[str, Any]]:
    """
    Executa o scraper do PGC e retorna a lista de dados brutos coletados.
    Login é feito manualmente via noVNC.
    """
    from .driver_factory import create_driver
    
    # Inicializa o driver e define como global
    driver = create_driver(headless=False)
    set_driver(driver)
    
    try:
        scraper = PGCScraperVBA(driver, ano_ref)
        if scraper.A_Loga_Acessa_PGC():
            return scraper.A1_Demandas_DFD_PCA()
        else:
            return []
    finally:
        close_driver()
