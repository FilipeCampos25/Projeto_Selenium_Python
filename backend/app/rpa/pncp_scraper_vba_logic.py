"""
pncp_scraper_vba_logic.py
Scraper do PNCP replicando FIELMENTE a lógica do VBA (Sub Dados_PNCP).
Integrado com VBACompat para garantir equivalência e estabilidade.
"""
import json
import time
import logging
import os
import re
from typing import Dict, List, Optional, Any
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from .vba_compat import VBACompat, CheckpointFailureError

logger = logging.getLogger(__name__)

# Carregar XPaths do arquivo JSON
XPATHS_FILE = os.path.join(os.path.dirname(__file__), "pncp_xpaths.json")
with open(XPATHS_FILE, 'r', encoding='utf-8') as f:
    XPATHS = json.load(f)

def so_numero(text: str) -> str:
    """Emula a função SoNumero do VBA."""
    if not text:
        return ""
    return "".join(re.findall(r'\d+', text))

class PNCPScraperVBA:
    def __init__(self, driver: WebDriver, ano_ref: str = "2025"):
        self.driver = driver
        self.ano_ref = ano_ref
        self.compat = VBACompat(driver)
        self.data_collected = []

    def Dados_PNCP(self) -> List[Dict[str, Any]]:
        """Replica Sub Dados_PNCP() do VBA."""
        logger.info("=== INICIANDO COLETA PNCP (Lógica VBA) ===")
        
        # 1. Testa o spinner
        self.compat.testa_spinner()
        
        # 2. Aguarda a tela aparecer (Formação do PCA)
        try:
            self.compat.wait_for_checkpoint(XPATHS["pca_selection"]["button_formacao_pca"], timeout=50)
        except CheckpointFailureError:
            logger.error("Falha ao aguardar botão 'Formação do PCA'.")
            return []

        # 3. Seleciona Formação do PCA
        self.compat.safe_click(XPATHS["pca_selection"]["button_formacao_pca"])
        self.compat.testa_spinner()

        # 4. Aguarda combo de seleção de período
        try:
            self.compat.wait_for_checkpoint(XPATHS["pca_selection"]["dropdown_pca"], timeout=30)
        except CheckpointFailureError:
            logger.error("Falha ao aguardar dropdown PCA.")
            return []
        
        self.compat.testa_spinner()

        # 5. Seleciona o combo
        self.compat.safe_click(XPATHS["pca_selection"]["dropdown_pca"])
        self.compat.testa_spinner()

        # 6. Seleciona o ano do PGC pretendido
        li_pca_xpath = XPATHS["pca_selection"]["li_pca_ano_template"].replace("{ano}", self.ano_ref)
        self.compat.safe_click(li_pca_xpath)
        self.compat.testa_spinner()

        # 7. Dá um tempo (Application.Wait Now + TimeValue("00:00:01"))
        time.sleep(1)

        # 8. Inicia contador de linhas (lin = 2 no VBA)
        # No Python, apenas coletamos para uma lista.

        # --- SEÇÃO REPROVADAS ---
        self._coletar_aba("reprovadas", "REPROVADA")

        # --- SEÇÃO APROVADAS ---
        self._coletar_aba("aprovadas", "APROVADA")

        # --- SEÇÃO PENDENTES ---
        self._coletar_aba("pendentes", "EM ELABORAÇÃO")

        logger.info(f"Coleta PNCP concluída. Total de itens: {len(self.data_collected)}")
        return self.data_collected

    def _coletar_aba(self, aba_id: str, status_vba: str):
        """Lógica comum para as abas Reprovadas, Aprovadas e Pendentes."""
        logger.info(f"Coletando aba: {aba_id}")
        
        xpath_aba = XPATHS["tabs"][aba_id]
        self.compat.safe_click(xpath_aba)
        time.sleep(1)
        self.compat.testa_spinner()

        # Testa se não encontrou nada
        # No VBA, ele testa se o elemento de "nada encontrado" NÃO está presente
        xpath_vazio = f"//div[@aria-labelledby='{aba_id}']/div[@class='search-results']/div/div/div/div/div[2]/span"
        try:
            # Se o elemento de "nada encontrado" NÃO estiver presente, prossegue
            if len(self.driver.find_elements(By.XPATH, xpath_vazio)) == 0:
                
                # Obtem o total de demandas
                xpath_label_total = XPATHS["table"]["label_total_template"].replace("{aba_id}", aba_id)
                txt = ""
                start_wait = time.time()
                while txt == "" and (time.time() - start_wait < 10):
                    try:
                        txt = self.driver.find_element(By.XPATH, xpath_label_total).text
                    except:
                        time.sleep(0.5)
                
                if not txt:
                    return

                demandas = int(so_numero(txt))
                logger.info(f"Total de demandas na aba {aba_id}: {demandas}")

                # Clica na tabela
                xpath_tbody = XPATHS["table"]["tbody_template"].replace("{aba_id}", aba_id)
                self.compat.safe_click(xpath_tbody)
                self.compat.testa_spinner()

                # Rola a tabela até carregar todos os itens (Simula o Do While do VBA)
                xpath_ultimo_item = f"{xpath_tbody}[@class='p-element p-datatable-tbody']/div[{demandas}]"
                
                max_scroll_attempts = 20
                attempts = 0
                while len(self.driver.find_elements(By.XPATH, xpath_ultimo_item)) == 0 and attempts < max_scroll_attempts:
                    self.driver.execute_script("arguments[0].scrollIntoView();", self.driver.find_element(By.XPATH, xpath_tbody))
                    self.compat.testa_spinner()
                    time.sleep(0.5)
                    attempts += 1

                time.sleep(1)
                self.compat.testa_spinner()

                # Varre as demandas
                for i in range(1, demandas + 1):
                    try:
                        base_xpath = XPATHS["table"]["item_base_template"].replace("{aba_id}", aba_id).replace("{index}", str(i))
                        f = XPATHS["fields"]
                        
                        item = {
                            "contratacao": self.driver.find_element(By.XPATH, f"{base_xpath}{f['contratacao']}").text,
                            "descricao": self.driver.find_element(By.XPATH, f"{base_xpath}{f['descricao']}").text,
                            "categoria": self.driver.find_element(By.XPATH, f"{base_xpath}{f['categoria']}").text,
                            "valor": self._parse_vba_cdbl(self.driver.find_element(By.XPATH, f"{base_xpath}{f['valor']}").text),
                            "inicio": self.driver.find_element(By.XPATH, f"{base_xpath}{f['inicio']}").text,
                            "fim": self.driver.find_element(By.XPATH, f"{base_xpath}{f['fim']}").text,
                            "status": status_vba,
                            "status_tipo": status_vba,
                            "dfd": self._format_dfd(self.driver.find_element(By.XPATH, f"{base_xpath}{f['descricao']}").text)
                        }
                        
                        # Correção de erro temporário do VBA (Linha 2461)
                        if item["dfd"] == "157/2024":
                            item["dfd"] = "157/2025"
                            
                        # Status específico para Pendentes (Linha 2629)
                        if aba_id == "pendentes":
                            item["status"] = self.driver.find_element(By.XPATH, f"{base_xpath}{f['status_pendente']}").text

                        self.data_collected.append(item)
                    except Exception as e:
                        logger.warning(f"Erro ao coletar item {i} na aba {aba_id}: {e}")

        except Exception as e:
            logger.error(f"Erro na coleta da aba {aba_id}: {e}")

    def _parse_vba_cdbl(self, text: str) -> float:
        """Emula CDbl do VBA."""
        if not text or text.strip() == "":
            return 0.0
        try:
            # Remove R$, pontos de milhar e troca vírgula por ponto
            clean = text.replace("R$", "").replace(".", "").replace(",", ".").strip()
            return float(clean)
        except:
            return 0.0

    def _format_dfd(self, text: str) -> str:
        """Emula Format(Left(SoNumero(...), 7), "@@@\/@@@@") do VBA."""
        nums = so_numero(text)
        if len(nums) >= 7:
            left_7 = nums[:7]
            return f"{left_7[:3]}/{left_7[3:]}"
        return nums

def run_pncp_scraper_vba(ano_ref: str = "2025") -> List[Dict[str, Any]]:
    """Entrypoint para o scraper PNCP com lógica VBA."""
    from .driver_factory import create_driver
    # Usa headless=False para permitir login manual via noVNC se necessário, 
    # embora o PNCP no VBA pareça herdar o login do PGC.
    driver = create_driver(headless=False)
    try:
        scraper = PNCPScraperVBA(driver, ano_ref)
        # O VBA chama A_Loga_Acessa_PGC antes de Dados_PNCP
        # Vamos assumir que o login já foi feito ou será feito.
        # Para manter a estrutura do PGC, vamos usar a mesma abordagem.
        from .pgc_scraper_vba_logic import PGCScraperVBA
        pgc_login = PGCScraperVBA(driver, ano_ref)
        if pgc_login.A_Loga_Acessa_PGC():
            return scraper.Dados_PNCP()
        return []
    finally:
        driver.quit()
