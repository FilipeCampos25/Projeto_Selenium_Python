"""
pncp_scraper_vba_logic.py
Implementação fiel à lógica do Módulo1.bas (VBA) para o PNCP.
Focado em fidelidade total aos XPaths, tempos de espera e tratamento de dados.
Implementação do Passo 12: Tratamento de erros equivalente ao VBA (Try/Except explícito).
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
        """Replica Sub Dados_PNCP() do VBA com tratamento de erro robusto (Passo 12)."""
        logger.info(f"=== INICIANDO COLETA PNCP (Lógica VBA - Passo 12: Tratamento de Erros) ===")
        
        try:
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
            try:
                btn_formacao = self.driver.find_element(By.XPATH, XPATHS["pca_selection"]["button_formacao_pca"])
                self.driver.execute_script("arguments[0].scrollIntoView();", btn_formacao)
                btn_formacao.click()
            except Exception as e:
                logger.warning(f"Erro ao clicar em Formação do PCA: {e}. Tentando prosseguir...")
            
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
            try:
                self.driver.find_element(By.XPATH, XPATHS["pca_selection"]["dropdown_pca"]).click()
            except Exception as e:
                logger.error(f"Erro crítico ao abrir dropdown PCA: {e}")
                return []
            
            # 8. Testa o spinner (VBA: Call testa_spinner)
            self.compat.testa_spinner()

            # 9. Seleciona o ano do PGC pretendido (VBA: driver.FindElementByXPath(...).Click)
            try:
                li_pca_xpath = XPATHS["pca_selection"]["li_pca_ano_template"].replace("{ano}", self.ano_ref)
                self.driver.find_element(By.XPATH, li_pca_xpath).click()
            except Exception as e:
                logger.error(f"Erro ao selecionar ano {self.ano_ref}: {e}")
                return []
            
            # 10. Testa o spinner (VBA: Call testa_spinner)
            self.compat.testa_spinner()

            # 11. Dá um tempo (VBA: Application.Wait Now + TimeValue("00:00:01"))
            time.sleep(1)

            # --- SEÇÃO REPROVADAS ---
            try:
                self._coletar_aba("reprovadas", "REPROVADA")
            except Exception as e:
                logger.error(f"Erro na aba REPROVADAS: {e}. Prosseguindo para próxima aba (Comportamento VBA).")

            # --- SEÇÃO APROVADAS ---
            try:
                self._coletar_aba("aprovadas", "APROVADA")
            except Exception as e:
                logger.error(f"Erro na aba APROVADAS: {e}. Prosseguindo para próxima aba (Comportamento VBA).")

            # --- SEÇÃO PENDENTES ---
            try:
                self._coletar_aba("pendentes", "PENDENTE")
            except Exception as e:
                logger.error(f"Erro na aba PENDENTES: {e}. Finalizando coleta (Comportamento VBA).")

        except Exception as e:
            logger.exception(f"Erro inesperado no fluxo principal Dados_PNCP: {e}")

        return self.data_collected

    def _coletar_aba(self, aba_id: str, status_vba: str):
        """Lógica de coleta para cada aba com tratamento de erro por item (Passo 12)."""
        logger.info(f"Iniciando coleta na aba: {aba_id}")
        
        # 1. Clica na aba (VBA: driver.FindElementByXPath(...).Click)
        aba_xpath = XPATHS["tabs"][aba_id]
        try:
            self.driver.find_element(By.XPATH, aba_xpath).click()
        except Exception as e:
            logger.error(f"Não foi possível clicar na aba {aba_id}: {e}")
            return
        
        # 2. Sincronização Fiel (VBA: Call testa_spinner)
        self.compat.testa_spinner()
        
        # 3. Dá um tempo (VBA: Application.Wait Now + TimeValue("00:00:01"))
        time.sleep(1)
        
        # 4. Testa se não encontrou nada (VBA: If Not driver.IsElementPresent(By.XPath(...)) Then)
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
            logger.warning(f"Não foi possível obter o total de demandas na aba {aba_id}. Tentando prosseguir...")
            return
            
        try:
            demandas = int(so_numero(txt))
        except:
            logger.error(f"Erro ao converter total de demandas: {txt}")
            return

        logger.info(f"Detectadas {demandas} demandas na aba {aba_id}.")

        # 6. Clica na tabela para garantir foco (VBA: driver.FindElementByXPath(...).Click)
        xpath_tbody = XPATHS["table"]["tbody_template"].replace("{aba_id}", aba_id)
        try:
            tabela_el = self.driver.find_element(By.XPATH, xpath_tbody)
            tabela_el.click()
        except:
            logger.warning(f"Não foi possível clicar no tbody da aba {aba_id}")

        # 7. Lógica de Paginação/Rolagem Fiel (VBA: Do While Not driver.IsElementPresent(... div[demandas] ...))
        xpath_ultimo_item = f"{xpath_tbody}[@class='p-element p-datatable-tbody']/div[{demandas}]"
        
        logger.info(f"Rolando tabela até o item {demandas} (Lógica VBA)...")
        start_scroll = time.time()
        while (time.time() - start_scroll < 120):
            if len(self.driver.find_elements(By.XPATH, xpath_ultimo_item)) > 0:
                break
            try:
                self.driver.execute_script("arguments[0].scrollIntoView();", tabela_el)
                self.driver.execute_script("window.scrollBy(0, 500);")
            except:
                pass
            self.compat.testa_spinner()
            time.sleep(0.5)

        # 8. Dá um tempo após rolagem (VBA: Application.Wait Now + TimeValue("00:00:01"))
        time.sleep(1)
        self.compat.testa_spinner()

        # 9. Loop de Coleta (VBA: For i = 1 To demandas)
        f = XPATHS["fields"]
        item_base_xpath = XPATHS["table"]["item_base_template"].replace("{aba_id}", aba_id)
        
        for i in range(1, demandas + 1):
            # PASSO 12: Try/Except por item para emular a continuidade do VBA
            try:
                base_xpath = item_base_xpath.replace("{index}", str(i))
                
                # 1. Coluna A: ID Contratação
                val_a = self.driver.find_element(By.XPATH, f"{base_xpath}{f['contratacao']}").text
                
                # 2. Coluna B: Descrição
                val_b = self.driver.find_element(By.XPATH, f"{base_xpath}{f['descricao']}").text
                
                # 3. Coluna I: DFD
                val_i = self._format_dfd(val_b)
                if val_i == "157/2024":
                    val_i = "157/2025"
                
                # 4. Coluna C: Categoria
                val_c = self.driver.find_element(By.XPATH, f"{base_xpath}{f['categoria']}").text
                
                # 5. Coluna D: Valor
                val_d_raw = self.driver.find_element(By.XPATH, f"{base_xpath}{f['valor']}").text
                if aba_id == "pendentes" and not val_d_raw.strip():
                    val_d = 0.0
                else:
                    val_d = self._parse_vba_cdbl(val_d_raw)
                
                # 6. Coluna E: Início
                val_e_raw = self.driver.find_element(By.XPATH, f"{base_xpath}{f['inicio']}").text
                val_e = self._parse_vba_cdate(val_e_raw)
                
                # 7. Coluna F: Fim
                val_f_raw = self.driver.find_element(By.XPATH, f"{base_xpath}{f['fim']}").text
                val_f = self._parse_vba_cdate(val_f_raw)
                
                # 8. Coluna G: Status
                if aba_id == "reprovadas":
                    val_g = "REPROVADA"
                elif aba_id == "aprovadas":
                    val_g = self.driver.find_element(By.XPATH, f"{base_xpath}{f['status_aprovada']}").text
                else: # pendentes
                    val_g = self.driver.find_element(By.XPATH, f"{base_xpath}{f['status_pendente']}").text
                
                # 9. Coluna H: Status Tipo
                if aba_id == "reprovadas":
                    val_h = "REPROVADA"
                elif aba_id == "aprovadas":
                    val_h = "APROVADA"
                else: # pendentes
                    val_h = val_g
                
                # Montagem e Validação
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

                validated_item = PNCPItemSchema(**raw_item)
                
                logger.info(
                    f"[VALIDACAO-CRUZADA] Item {i}/{demandas} Aba {aba_id} | "
                    f"A:{validated_item.col_a_contratacao} | Status:{validated_item.col_g_status}"
                )
                
                self.data_collected.append(validated_item.dict())
            except Exception as e:
                # PASSO 12: Emula "On Error Resume Next" - Loga o erro e pula para o próximo item
                logger.warning(f"PULANDO ITEM {i} na aba {aba_id} devido a erro (Comportamento VBA): {e}")
                continue

    def _parse_vba_cdbl(self, text: str) -> float:
        """Emula CDbl do VBA com tratamento de erro."""
        if not text: return 0.0
        try:
            clean = text.replace("R$", "").replace(".", "").replace(",", ".").strip()
            return float(clean)
        except:
            return 0.0

    def _parse_vba_cdate(self, text: str) -> Optional[str]:
        """Emula CDate do VBA com tratamento de erro."""
        if not text or "/" not in text: return None
        try:
            return datetime.strptime(text.strip(), "%d/%m/%Y").date().isoformat()
        except:
            return None

    def _format_dfd(self, descricao: str) -> str:
        """Emula a extração e formatação do DFD do VBA."""
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
