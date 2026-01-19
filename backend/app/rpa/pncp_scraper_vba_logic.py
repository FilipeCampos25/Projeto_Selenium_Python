"""
pncp_scraper_vba_logic.py
Scraper do PNCP replicando FIELMENTE a lógica do VBA (Sub Dados_PNCP).
Implementação do Passo 3: Inventário de campos e validações de integridade.
"""
import json
import time
import logging
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from .vba_compat import VBACompat, CheckpointFailureError
from ..api.schemas import PNCPItemSchema

logger = logging.getLogger(__name__)

# Carregar XPaths do arquivo JSON
XPATHS_FILE = os.path.join(os.path.dirname(__file__), "pncp_xpaths.json")
with open(XPATHS_FILE, 'r', encoding='utf-8') as f:
    XPATHS = json.load(f)

def so_numero(text: str) -> str:
    """Emula a função SoNumero do VBA: remove tudo que não é dígito."""
    if not text:
        return ""
    return "".join(re.findall(r'\d+', text))

class PNCPScraperVBA:
    """
    Classe que implementa o inventário de campos do PNCP (Passo 3).
    Mantém fidelidade total aos tipos de dados e formatações do VBA.
    """
    def __init__(self, driver: WebDriver, ano_ref: str = "2025", dry_run: bool = False):
        self.driver = driver
        self.ano_ref = ano_ref
        self.dry_run = dry_run
        self.compat = VBACompat(driver)
        self.data_collected = []

    def Dados_PNCP(self) -> List[Dict[str, Any]]:
        """Replica Sub Dados_PNCP() do VBA."""
        logger.info(f"=== INICIANDO COLETA PNCP (Lógica VBA - Passo 7: Navegação Inicial) ===")
        
        # 1. Testa o spinner (VBA: Call testa_spinner)
        self.compat.testa_spinner()
        
        # 2. Aguarda a tela aparecer (VBA: Do ... Loop Until driver.FindElementByXPath(...).IsDisplayed)
        # Replicando o loop de espera do VBA com Application.Wait interno
        start_wait = time.time()
        while time.time() - start_wait < 50:
            # VBA: Application.Wait Now + TimeValue("00:00:01") / 4
            time.sleep(0.25)
            try:
                if self.driver.find_element(By.XPATH, XPATHS["pca_selection"]["button_formacao_pca"]).is_displayed():
                    break
            except:
                pass
        else:
            logger.error("Falha ao aguardar botão 'Formação do PCA' (Timeout Passo 7).")
            return []

        if self.dry_run:
            logger.info("Dry Run ativo: Parando após validação da página inicial (Passo 6/7).")
            return []

        # 3. Seleciona Formação do PCA (VBA: .ScrollIntoView e .Click)
        btn_formacao = self.driver.find_element(By.XPATH, XPATHS["pca_selection"]["button_formacao_pca"])
        self.driver.execute_script("arguments[0].scrollIntoView();", btn_formacao)
        btn_formacao.click()
        
        # 4. Testa o spinner (VBA: Call testa_spinner)
        self.compat.testa_spinner()

        # 5. Aguarda combo de seleção de período (VBA: Do While Not driver.IsElementPresent(...))
        start_wait = time.time()
        while time.time() - start_wait < 30:
            if len(self.driver.find_elements(By.XPATH, XPATHS["pca_selection"]["dropdown_pca"])) > 0:
                break
            time.sleep(0.5)
        else:
            logger.error("Falha ao aguardar dropdown PCA (Timeout Passo 7).")
            return []
        
        # 6. Testa o spinner (VBA: Call testa_spinner)
        self.compat.testa_spinner()

        # 7. Seleciona o combo (VBA: driver.FindElementByXPath(...).Click)
        self.driver.find_element(By.XPATH, XPATHS["pca_selection"]["dropdown_pca"]).click()
        
        # 8. Testa o spinner (VBA: Call testa_spinner)
        self.compat.testa_spinner()

        # 9. Seleciona o ano do PGC pretendido (VBA: driver.FindElementByXPath(...).Click)
        li_pca_xpath = XPATHS["pca_selection"]["li_pca_ano_template"].replace("{ano}", self.ano_ref)
        self.driver.find_element(By.XPATH, li_pca_xpath).click()
        
        # 10. Testa o spinner (VBA: Call testa_spinner)
        self.compat.testa_spinner()

        # 11. Dá um tempo (VBA: Application.Wait Now + TimeValue("00:00:01"))
        time.sleep(1)

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

        # Testa se não encontrou nada (VBA: If driver.FindElementsByXPath(...).Count = 0 Then)
        xpath_vazio = f"//div[@aria-labelledby='{aba_id}']/div[@class='search-results']/div/div/div/div/div[2]/span"
        try:
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

                # Rola a tabela até carregar todos os itens (VBA: Do While driver.FindElementsByXPath(...).Count = 0)
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

                # Varre as demandas (VBA: For i = 1 To demandas)
                for i in range(1, demandas + 1):
                    try:
                        base_xpath = XPATHS["table"]["item_base_template"].replace("{aba_id}", aba_id).replace("{index}", str(i))
                        f = XPATHS["fields"]
                        
                        # Validação de existência do elemento antes da coleta (Imita o comportamento do driver.FindElement no VBA)
                        try:
                            el_contratacao = self.driver.find_element(By.XPATH, f"{base_xpath}{f['contratacao']}")
                        except:
                            logger.warning(f"Item {i} não encontrado na aba {aba_id}. Pulando.")
                            continue

                        # INVENTÁRIO DE CAMPOS (Passo 3) & CONTRATO DE DADOS (Passo 5)
                        # Mapeamento fiel às colunas do Excel (A a I) e tipos de dados do VBA
                        raw_item = {
                            "col_a_contratacao": el_contratacao.text,
                            "col_b_descricao": self.driver.find_element(By.XPATH, f"{base_xpath}{f['descricao']}").text,
                            "col_c_categoria": self.driver.find_element(By.XPATH, f"{base_xpath}{f['categoria']}").text,
                            "col_d_valor": self._parse_vba_cdbl(self.driver.find_element(By.XPATH, f"{base_xpath}{f['valor']}").text),
                            "col_e_inicio": self._parse_vba_cdate(self.driver.find_element(By.XPATH, f"{base_xpath}{f['inicio']}").text),
                            "col_f_fim": self._parse_vba_cdate(self.driver.find_element(By.XPATH, f"{base_xpath}{f['fim']}").text),
                            "col_g_status": status_vba,
                            "col_h_status_tipo": status_vba,
                            "col_i_dfd": self._format_dfd(self.driver.find_element(By.XPATH, f"{base_xpath}{f['descricao']}").text)
                        }
                        
                        # Regra de Negócio Específica (VBA: If ... Value = "157/2024" Then ... = "157/2025")
                        if raw_item["col_i_dfd"] == "157/2024":
                            raw_item["col_i_dfd"] = "157/2025"
                            
                        # Status específico para Pendentes (VBA: .Range("G" ...).Value = driver.FindElementByXPath(...).Text)
                        if aba_id == "pendentes":
                            try:
                                raw_item["col_g_status"] = self.driver.find_element(By.XPATH, f"{base_xpath}{f['status_pendente']}").text
                            except:
                                pass # Mantém o status padrão se falhar

                        # Validação via Contrato de Dados (Passo 5)
                        validated_item = PNCPItemSchema(**raw_item)
                        self.data_collected.append(validated_item.dict())
                    except Exception as e:
                        # No VBA, erros individuais no loop geralmente não param a execução (On Error Resume Next implícito no fluxo)
                        logger.warning(f"Erro ao coletar item {i} na aba {aba_id}: {e}")

        except Exception as e:
            logger.error(f"Erro na coleta da aba {aba_id}: {e}")

    def _parse_vba_cdbl(self, text: str) -> float:
        """Emula CDbl do VBA: converte string monetária para Double."""
        if not text or text.strip() == "":
            return 0.0
        try:
            # Limpeza idêntica ao comportamento implícito do CDbl em strings PT-BR
            clean = text.replace("R$", "").replace(".", "").replace(",", ".").strip()
            return float(clean)
        except:
            return 0.0

    def _parse_vba_cdate(self, text: str) -> str:
        """Emula CDate do VBA: converte string de data para objeto de data (ISO string para o DB)."""
        if not text or text.strip() == "":
            return None
        try:
            # VBA CDate em sistema PT-BR espera DD/MM/YYYY
            dt = datetime.strptime(text.strip(), "%d/%m/%Y")
            return dt.strftime("%Y-%m-%d")
        except:
            return text

    def _format_dfd(self, text: str) -> str:
        """
        Emula a lógica complexa do VBA para o DFD:
        Format(Left(SoNumero(descricao), 7), "@@@\/@@@@")
        """
        nums = so_numero(text)
        if len(nums) >= 7:
            left_7 = nums[:7]
            # Formata como 000/0000
            return f"{left_7[:3]}/{left_7[3:]}"
        return nums

def run_pncp_scraper_vba(ano_ref: str = "2025", dry_run: bool = False) -> List[Dict[str, Any]]:
    """Entrypoint para o scraper PNCP com lógica VBA."""
    from .driver_factory import create_driver
    driver = create_driver(headless=False)
    try:
        scraper = PNCPScraperVBA(driver, ano_ref, dry_run=dry_run)
        from .pgc_scraper_vba_logic import PGCScraperVBA
        pgc_login = PGCScraperVBA(driver, ano_ref)
        if pgc_login.A_Loga_Acessa_PGC():
            return scraper.Dados_PNCP()
        return []
    finally:
        driver.quit()
