"""
pgc_scraper_vba_logic.py
Scraper do PGC com lógica otimizada, removendo sleeps estáticos.
"""
import json
import time
import logging
import os
from typing import Dict, List, Optional, Any
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .vba_compat import VBACompat, CheckpointFailureError

logger = logging.getLogger(__name__)

# Carregar XPaths do arquivo JSON
XPATHS_FILE = os.path.join(os.path.dirname(__file__), "pgc_xpaths.json")
with open(XPATHS_FILE, 'r', encoding='utf-8') as f:
    XPATHS = json.load(f)

class PGCScraperVBA:
    def __init__(self, driver: WebDriver, ano_ref: str = "2025"):
        self.driver = driver
        self.ano_ref = ano_ref
        self.compat = VBACompat(driver)
        self.data_collected = []

    def A_Loga_Acessa_PGC(self) -> bool:
        """Replica Sub A_Loga_Acessa_PGC() do VBA sem sleeps fixos."""
        logger.info("=== ABRINDO LOGIN NO PGC ===")
        
        self.driver.get(XPATHS["login"]["url"])
        self.driver.maximize_window()
        
        try:
            self.compat.wait_for_checkpoint(XPATHS["login"]["btn_expand_governo"])
        except CheckpointFailureError:
            return False
            
        self.compat.safe_click(XPATHS["login"]["btn_expand_governo"])
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        logger.info("Aguardando login manual...")
        try:
            # Espera dinâmica pelo título do PGC após login
            self.compat.wait_for_checkpoint(XPATHS["login"]["span_pgc_title"], "Planejamento e Gerenciamento de Contratações", timeout=300)
        except CheckpointFailureError:
            return False
        
        self.compat.safe_click(XPATHS["login"]["div_pgc_access"])
        
        # Validação de navegação
        if not self.compat.wait_for_new_window(set()):
            return False
            
        logger.info("PGC acessado com sucesso.")
        return True

    def A1_Demandas_DFD_PCA(self) -> List[Dict[str, Any]]:
        """Replica Sub A1_Demandas_DFD_PCA() com esperas dinâmicas."""
        logger.info("=== INICIANDO COLETA DE DFDs ===")
        
        try:
            self.compat.validate_table_context("Planejamento e Gerenciamento de Contratações", ["DFD", "Requisitante", "Valor"])
        except CheckpointFailureError:
            return []

        self.compat.safe_click(XPATHS["pca_selection"]["dropdown_pca"])
        li_pca_xpath = XPATHS["pca_selection"]["li_pca_ano_template"].replace("{ano}", self.ano_ref)
        self.compat.safe_click(li_pca_xpath)
        
        self.compat.safe_click(f"//*[@id='{XPATHS['pca_selection']['radio_minha_uasg_id']}']")
        
        # Espera dinâmica pela tabela
        try:
            self.compat.wait_for_checkpoint(XPATHS["table"]["rows"], timeout=20)
        except CheckpointFailureError:
            return []
        
        self.compat.testa_spinner()

        all_data = []
        pos = 1
        posM = self._count_total_pages()
        logger.info(f"Total de páginas: {posM}")
        
        while pos <= posM:
            logger.info(f"Coletando página {pos} de {posM}...")
            page_data = self._read_current_table()
            all_data.extend(page_data)
            
            if pos < posM:
                if not self._go_to_next_page():
                    break
            pos += 1
            
        self.data_collected = all_data
        return all_data

    def _count_total_pages(self) -> int:
        """Conta páginas usando lógica de timeout em vez de sleeps."""
        contador = 1
        while True:
            try:
                # Espera curta para ver se o botão existe e está habilitado
                btn_next = WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located((By.XPATH, XPATHS["pagination"]["btn_next"]))
                )
                if 'p-disabled' in btn_next.get_attribute('class'):
                    break
                
                self.compat.safe_click(XPATHS["pagination"]["btn_next"])
                # Espera a tabela mudar (pode validar pelo número da página se disponível)
                self.compat.testa_spinner()
                contador += 1
            except:
                break
        
        # Volta para página 1
        try:
            self.compat.safe_click(XPATHS["pagination"]["btn_first"])
            self.compat.testa_spinner()
        except:
            pass
        
        return contador

    def _read_current_table(self) -> List[Dict[str, Any]]:
        rows_data = []
        # Garante que as linhas estão presentes
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, XPATHS["table"]["rows"]))
            )
            rows = self.driver.find_elements(By.XPATH, XPATHS["table"]["rows"])
            
            for row in rows:
                try:
                    cols = row.find_elements(By.XPATH, "./td")
                    if len(cols) < 10: continue
                    
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
                except:
                    continue
        except:
            pass
                
        return rows_data

    def _go_to_next_page(self) -> bool:
        """Avança página com validação dinâmica."""
        try:
            if not self.compat.safe_click(XPATHS["pagination"]["btn_next"]):
                return False
            
            # Espera dinâmica pela recarga
            self.compat.wait_for_checkpoint(XPATHS["table"]["rows"], timeout=15)
            self.compat.testa_spinner()
            return True
        except:
            return False

    def _parse_currency(self, value_str: str) -> float:
        try:
            clean_value = value_str.replace("R$", "").replace(".", "").replace(",", ".").strip()
            return float(clean_value)
        except:
            return 0.0

def run_pgc_scraper_vba(ano_ref: str = "2025") -> List[Dict[str, Any]]:
    from .driver_factory import create_driver
    driver = create_driver(headless=False)
    try:
        scraper = PGCScraperVBA(driver, ano_ref)
        if scraper.A_Loga_Acessa_PGC():
            return scraper.A1_Demandas_DFD_PCA()
        return []
    finally:
        driver.quit()
