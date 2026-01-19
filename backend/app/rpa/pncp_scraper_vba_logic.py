"""
pncp_scraper_vba_logic.py
Implementação fiel à lógica do Módulo1.bas (VBA) para o PNCP.
Focado em fidelidade total aos XPaths, tempos de espera e tratamento de dados.
Implementação do Passo 11: Paginação PNCP fiel ao VBA.
"""
import json
import logging
import os
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .vba_compat import VBACompat, CheckpointFailureError
from ..api.schemas import PNCPItemSchema

logger = logging.getLogger(__name__)

# Carregar XPaths do arquivo JSON
XPATHS_PATH = os.path.join(os.path.dirname(__file__), "pncp_xpaths.json")
with open(XPATHS_PATH, "r", encoding="utf-8") as f:
    XPATHS = json.load(f)

def so_numero(text: str) -> str:
    """Emula a lógica de limpeza de números do VBA."""
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
        logger.info(f"=== INICIANDO COLETA PNCP (Lógica VBA - Passo 11: Paginação e Coleta Fiel) ===")
        
        # 1. Testa o spinner (VBA: Call testa_spinner)
        self.compat.testa_spinner()
        
        # 2. Aguarda a tela aparecer (VBA: Do ... Loop Until driver.FindElementByXPath(...).IsDisplayed)
        start_wait = time.time()
        while time.time() - start_wait < 50:
            time.sleep(0.25)
            try:
                if self.driver.find_element(By.XPATH, XPATHS["pca_selection"]["button_formacao_pca"]).is_displayed():
                    break
            except:
                pass
        else:
            logger.error("Falha ao aguardar botão 'Formação do PCA' (Timeout).")
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
            logger.error("Falha ao aguardar dropdown PCA.")
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
        self._coletar_aba("pendentes", "PENDENTE")

        return self.data_collected

    def _coletar_aba(self, aba_id: str, status_vba: str):
        """Lógica de coleta para cada aba (Reprovadas, Aprovadas, Pendentes) com Paginação Fiel (Passo 11)."""
        logger.info(f"Iniciando coleta na aba: {aba_id}")
        
        # 1. Clica na aba (VBA: driver.FindElementByXPath(...).Click)
        aba_xpath = XPATHS["tabs"][aba_id]
        self.driver.find_element(By.XPATH, aba_xpath).click()
        
        # 2. Sincronização Fiel (VBA: Call testa_spinner)
        self.compat.testa_spinner()
        
        # 3. Dá um tempo (VBA: Application.Wait Now + TimeValue("00:00:01"))
        time.sleep(1)
        
        # 4. Testa se não encontrou nada (VBA: If Not driver.IsElementPresent(By.XPath(...)) Then)
        # O VBA usa um XPath específico para a mensagem de "nenhum registro encontrado"
        xpath_vazio = f"//div[@aria-labelledby='{aba_id}']/div[@class='search-results']/div/div/div/div/div[2]/span"
        if len(self.driver.find_elements(By.XPATH, xpath_vazio)) > 0:
            logger.info(f"Nenhum item encontrado na aba {aba_id} (Mensagem de vazio detectada).")
            return

        # 5. Obtém o total de demandas (VBA: Do While txt = "" ... demandas = SoNumero(txt))
        xpath_label_total = XPATHS["table"]["label_total_template"].replace("{aba_id}", aba_id)
        txt = ""
        start_wait = time.time()
        while not txt and (time.time() - start_wait < 20):
            try:
                txt = self.driver.find_element(By.XPATH, xpath_label_total).text
            except:
                time.sleep(0.5)
        
        if not txt:
            logger.warning(f"Não foi possível obter o total de demandas na aba {aba_id}.")
            return
            
        demandas = int(so_numero(txt))
        logger.info(f"Detectadas {demandas} demandas na aba {aba_id}.")

        # 6. Clica na tabela para garantir foco (VBA: driver.FindElementByXPath(...).Click)
        xpath_tbody = XPATHS["table"]["tbody_template"].replace("{aba_id}", aba_id)
        try:
            tabela_el = self.driver.find_element(By.XPATH, xpath_tbody)
            tabela_el.click()
        except:
            logger.warning(f"Não foi possível clicar no tbody da aba {aba_id}")

        # 7. Lógica de Paginação/Rolagem Fiel (VBA: Do While Not driver.IsElementPresent(... div[demandas] ...))
        # O VBA rola a tabela até que o último item (div[demandas]) esteja presente
        xpath_ultimo_item = f"{xpath_tbody}[@class='p-element p-datatable-tbody']/div[{demandas}]"
        
        logger.info(f"Rolando tabela até o item {demandas} (Lógica de Paginação VBA)...")
        start_scroll = time.time()
        while (time.time() - start_scroll < 120): # Timeout de 2 min para rolagem
            if len(self.driver.find_elements(By.XPATH, xpath_ultimo_item)) > 0:
                break
            
            # Rola a tabela (VBA: tabela.ScrollIntoView)
            try:
                self.driver.execute_script("arguments[0].scrollIntoView();", tabela_el)
                self.driver.execute_script("window.scrollBy(0, 500);") # Pequeno ajuste para forçar trigger de scroll
            except:
                pass
                
            # Testa o spinner (VBA: Call testa_spinner)
            self.compat.testa_spinner()
            time.sleep(0.5)
        else:
            logger.warning(f"Timeout ao tentar carregar todos os {demandas} itens da aba {aba_id}.")

        # 8. Dá um tempo após rolagem (VBA: Application.Wait Now + TimeValue("00:00:01"))
        time.sleep(1)
        self.compat.testa_spinner()

        # 9. Loop de Coleta (VBA: For i = 1 To demandas)
        f = XPATHS["fields"]
        item_base_xpath = XPATHS["table"]["item_base_template"].replace("{aba_id}", aba_id)
        
        for i in range(1, demandas + 1):
            try:
                base_xpath = item_base_xpath.replace("{index}", str(i))
                
                # 1. Coluna A: ID Contratação (VBA: .Range("A" ...).Value = driver.FindElementByXPath(...).Text)
                xpath_a = f"{base_xpath}{f['contratacao']}"
                el_a = self.driver.find_element(By.XPATH, xpath_a)
                val_a = el_a.text
                
                # 2. Coluna B: Descrição (VBA: .Range("B" ...).Value = driver.FindElementByXPath(...).Text)
                xpath_b = f"{base_xpath}{f['descricao']}"
                val_b = self.driver.find_element(By.XPATH, xpath_b).text
                
                # 3. Coluna I: DFD (VBA: Format(Left(SoNumero(...), 7), "@@@\/@@@@"))
                val_i = self._format_dfd(val_b)
                # Regra de Negócio Específica (VBA: If ... Value = "157/2024" Then ... = "157/2025")
                if val_i == "157/2024":
                    val_i = "157/2025"
                
                # 4. Coluna C: Categoria (VBA: .Range("C" ...).Value = driver.FindElementByXPath(...).Text)
                xpath_c = f"{base_xpath}{f['categoria']}"
                val_c = self.driver.find_element(By.XPATH, xpath_c).text
                
                # 5. Coluna D: Valor (VBA: CDbl(...))
                xpath_d = f"{base_xpath}{f['valor']}"
                val_d_raw = self.driver.find_element(By.XPATH, xpath_d).text
                # No VBA para Pendentes, há um check de vazio: If Trim(...) = "" Then ... = 0
                if aba_id == "pendentes" and not val_d_raw.strip():
                    val_d = 0.0
                else:
                    val_d = self._parse_vba_cdbl(val_d_raw)
                
                # 6. Coluna E: Início (VBA: CDate(...))
                xpath_e = f"{base_xpath}{f['inicio']}"
                val_e_raw = self.driver.find_element(By.XPATH, xpath_e).text
                val_e = self._parse_vba_cdate(val_e_raw)
                
                # 7. Coluna F: Fim (VBA: CDate(...))
                xpath_f = f"{base_xpath}{f['fim']}"
                val_f_raw = self.driver.find_element(By.XPATH, xpath_f).text
                val_f = self._parse_vba_cdate(val_f_raw)
                
                # 8. Coluna G: Status (VBA: .Range("G" ...).Value = ...)
                if aba_id == "reprovadas":
                    val_g = "REPROVADA"
                elif aba_id == "aprovadas":
                    xpath_g = f"{base_xpath}{f['status_aprovada']}" # /div[8]/p
                    val_g = self.driver.find_element(By.XPATH, xpath_g).text
                else: # pendentes
                    xpath_g = f"{base_xpath}{f['status_pendente']}"
                    val_g = self.driver.find_element(By.XPATH, xpath_g).text
                
                # 9. Coluna H: Status Tipo (VBA: .Range("H" ...).Value = ...)
                if aba_id == "reprovadas":
                    val_h = "REPROVADA"
                elif aba_id == "aprovadas":
                    val_h = "APROVADA"
                else: # pendentes
                    val_h = val_g # No VBA: .Range("H" ...).Value = driver.FindElementByXPath(... status_pendente ...).Text
                
                # Montagem do item validado pelo contrato (Passo 5)
                raw_item = {
                    "col_a_contratacao": val_a,
                    "col_b_descricao": val_b,
                    "col_c_categoria": val_c,
                    "col_d_valor": val_d,
                    "col_e_inicio": val_e,
                    "col_f_fim": val_f,
                    "col_g_status": val_g,
                    "col_h_status_tipo": val_h,
                    "col_i_dfd": val_i
                }

                # Validação via Contrato de Dados (Passo 5)
                validated_item = PNCPItemSchema(**raw_item)
                
                # Log de validação cruzada (Passo 10)
                logger.info(
                    f"[VALIDACAO-CRUZADA] Item {i}/{demandas} Aba {aba_id} | "
                    f"A:{validated_item.col_a_contratacao} | "
                    f"D:{validated_item.col_d_valor} | "
                    f"I:{validated_item.col_i_dfd} | "
                    f"Status:{validated_item.col_g_status}"
                )
                
                self.data_collected.append(validated_item.dict())
            except Exception as e:
                logger.warning(f"Erro ao coletar item {i} na aba {aba_id}: {e}")

    def _parse_vba_cdbl(self, text: str) -> float:
        """Emula CDbl(Replace(Replace(..., ".", ""), ",", ".")) do VBA."""
        if not text: return 0.0
        try:
            # Remove R$, pontos de milhar e troca vírgula por ponto
            clean = text.replace("R$", "").replace(".", "").replace(",", ".").strip()
            return float(clean)
        except:
            return 0.0

    def _parse_vba_cdate(self, text: str) -> Optional[str]:
        """Emula CDate do VBA, retornando YYYY-MM-DD para o Postgres."""
        if not text or "/" not in text: return None
        try:
            return datetime.strptime(text.strip(), "%d/%m/%Y").date().isoformat()
        except:
            return None

    def _format_dfd(self, descricao: str) -> str:
        """Emula a extração e formatação do DFD do VBA (Passo 3)."""
        nums = so_numero(descricao)
        if len(nums) >= 7:
            left_7 = nums[:7]
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
