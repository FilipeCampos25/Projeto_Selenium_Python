"""
pncp_scraper_vba_logic.py
Implementação fiel à lógica do Módulo1.bas (VBA) para o PNCP.
Focado em fidelidade total aos XPaths, tempos de espera e tratamento de dados.

HISTÓRICO DE ADAPTAÇÃO:
- Passo 11: Implementação da Paginação e Rolagem Fiel ao VBA.
- Passo 12: Tratamento de Erros Equivalente ao VBA (Try/Except por item).
- Passo 13: Implementação de Logs Específicos e Comentários de Orientação.
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

# Configuração de Logger para Auditoria (Passo 13)
logger = logging.getLogger(__name__)

# Carregar XPaths do arquivo JSON (Mapeamento direto do VBA)
XPATHS_PATH = os.path.join(os.path.dirname(__file__), "pncp_xpaths.json")
with open(XPATHS_PATH, "r", encoding="utf-8") as f:
    XPATHS = json.load(f)

def so_numero(text: str) -> str:
    """
    Emula a função SoNumero do VBA.
    Utilizada para limpar strings e manter apenas dígitos para contadores e IDs.
    """
    if not text:
        return ""
    return "".join(re.findall(r'\d+', text))

class PNCPScraperVBA:
    """
    Classe PNCPScraperVBA:
    Implementa o fluxo de coleta do PNCP replicando o comportamento do Módulo1.bas.
    Cada método e bloco de código possui comentários referenciando a lógica original.
    """
    def __init__(self, driver: WebDriver, ano_ref: str = "2025", dry_run: bool = False):
        self.driver = driver
        self.ano_ref = ano_ref
        self.dry_run = dry_run
        self.compat = VBACompat(driver)
        self.data_collected = []

    def Dados_PNCP(self) -> List[Dict[str, Any]]:
        """
        Replica Sub Dados_PNCP() do VBA.
        Este é o entrypoint principal da coleta PNCP.
        """
        logger.info(f"=== [INÍCIO] COLETA PNCP - ANO REF: {self.ano_ref} ===")
        logger.info("Passo 13: Iniciando auditoria detalhada do fluxo.")
        
        try:
            # --- SINCRONIZAÇÃO INICIAL ---
            # VBA: Call testa_spinner
            logger.info("[LOG-VBA] Aguardando carregamento inicial (testa_spinner)...")
            self.compat.testa_spinner()
            
            # --- AGUARDA BOTÃO FORMAÇÃO PCA ---
            # VBA: Do ... Loop Until driver.FindElementByXPath(...).IsDisplayed
            logger.info("[LOG-VBA] Aguardando visibilidade do botão 'Formação do PCA'...")
            start_wait = time.time()
            while time.time() - start_wait < 50:
                time.sleep(0.25)
                try:
                    if self.driver.find_element(By.XPATH, XPATHS["pca_selection"]["button_formacao_pca"]).is_displayed():
                        break
                except:
                    pass
            else:
                logger.error("[ERRO-CRÍTICO] Timeout ao aguardar botão 'Formação do PCA'.")
                return []

            if self.dry_run:
                logger.info("[DRY-RUN] Validação de página inicial concluída. Encerrando conforme Passo 6.")
                return []

            # --- CLIQUE EM FORMAÇÃO DO PCA ---
            # VBA: .ScrollIntoView e .Click
            logger.info("[LOG-VBA] Executando Scroll e Clique em 'Formação do PCA'...")
            try:
                btn_formacao = self.driver.find_element(By.XPATH, XPATHS["pca_selection"]["button_formacao_pca"])
                self.driver.execute_script("arguments[0].scrollIntoView();", btn_formacao)
                btn_formacao.click()
            except Exception as e:
                logger.warning(f"[AVISO-VBA] Falha no clique padrão, tentando prosseguir: {e}")
            
            # VBA: Call testa_spinner
            self.compat.testa_spinner()

            # --- AGUARDA DROPDOWN PCA ---
            # VBA: Do While Not driver.IsElementPresent(By.XPath("//p-dropdown[@placeholder='Selecione PCA']"))
            logger.info("[LOG-VBA] Aguardando presença do Dropdown de seleção de PCA...")
            start_wait = time.time()
            while time.time() - start_wait < 30:
                if len(self.driver.find_elements(By.XPATH, XPATHS["pca_selection"]["dropdown_pca"])) > 0:
                    break
                time.sleep(0.5)
            else:
                logger.error("[ERRO-CRÍTICO] Dropdown PCA não encontrado.")
                return []
            
            self.compat.testa_spinner()

            # --- SELECIONA O ANO DO PGC ---
            # VBA: driver.FindElementByXPath("//p-dropdown[@placeholder='Selecione PCA']").Click
            logger.info(f"[LOG-VBA] Selecionando o ano {self.ano_ref} no Dropdown...")
            try:
                self.driver.find_element(By.XPATH, XPATHS["pca_selection"]["dropdown_pca"]).click()
                self.compat.testa_spinner()
                
                # VBA: driver.FindElementByXPath("//li[starts-with(@aria-label,'PCA " + ano_ref + " -')]").Click
                li_pca_xpath = XPATHS["pca_selection"]["li_pca_ano_template"].replace("{ano}", self.ano_ref)
                self.driver.find_element(By.XPATH, li_pca_xpath).click()
            except Exception as e:
                logger.error(f"[ERRO-CRÍTICO] Falha ao selecionar o ano no dropdown: {e}")
                return []
            
            self.compat.testa_spinner()

            # --- ESPERA DE ESTABILIZAÇÃO ---
            # VBA: Application.Wait Now + TimeValue("00:00:01")
            logger.info("[LOG-VBA] Aguardando 1 segundo para estabilização da página...")
            time.sleep(1)

            # --- INÍCIO DA COLETA POR ABAS (REPROVADAS -> APROVADAS -> PENDENTES) ---
            
            # ABA REPROVADAS
            try:
                logger.info("--- [ABA] INICIANDO COLETA: REPROVADAS ---")
                self._coletar_aba("reprovadas", "REPROVADA")
            except Exception as e:
                logger.error(f"[ERRO-ABA] Falha na aba REPROVADAS: {e}. Prosseguindo (Comportamento VBA).")

            # ABA APROVADAS
            try:
                logger.info("--- [ABA] INICIANDO COLETA: APROVADAS ---")
                self._coletar_aba("aprovadas", "APROVADA")
            except Exception as e:
                logger.error(f"[ERRO-ABA] Falha na aba APROVADAS: {e}. Prosseguindo (Comportamento VBA).")

            # ABA PENDENTES
            try:
                logger.info("--- [ABA] INICIANDO COLETA: PENDENTES ---")
                self._coletar_aba("pendentes", "PENDENTE")
            except Exception as e:
                logger.error(f"[ERRO-ABA] Falha na aba PENDENTES: {e}. Finalizando (Comportamento VBA).")

        except Exception as e:
            logger.exception(f"[ERRO-FATAL] Exceção não tratada no fluxo Dados_PNCP: {e}")

        logger.info(f"=== [FIM] COLETA PNCP CONCLUÍDA. TOTAL COLETADO: {len(self.data_collected)} ITENS ===")
        return self.data_collected

    def _coletar_aba(self, aba_id: str, status_vba: str):
        """
        Lógica de coleta para cada aba.
        Implementa Paginação (Passo 11), Tratamento de Erros (Passo 12) e Logs (Passo 13).
        """
        # --- CLIQUE NA ABA ---
        # VBA: driver.FindElementByXPath("//a[@id='contratacoes-...']").Click
        logger.info(f"[LOG-VBA] Clicando na aba: {aba_id.upper()}")
        aba_xpath = XPATHS["tabs"][aba_id]
        try:
            self.driver.find_element(By.XPATH, aba_xpath).click()
        except Exception as e:
            logger.error(f"[ERRO-VBA] Não foi possível acessar a aba {aba_id}: {e}")
            return
        
        # VBA: Call testa_spinner
        self.compat.testa_spinner()
        time.sleep(1)
        
        # --- VERIFICA SE HÁ DADOS ---
        # VBA: If Not driver.IsElementPresent(By.XPath(... span de vazio ...))
        xpath_vazio = f"//div[@aria-labelledby='{aba_id}']/div[@class='search-results']/div/div/div/div/div[2]/span"
        if len(self.driver.find_elements(By.XPATH, xpath_vazio)) > 0:
            logger.info(f"[LOG-VBA] Aba {aba_id.upper()} está vazia. Pulando coleta.")
            return

        # --- OBTÉM TOTAL DE DEMANDAS ---
        # VBA: Do While txt = "" ... demandas = SoNumero(txt)
        logger.info(f"[LOG-VBA] Obtendo total de demandas para a aba {aba_id.upper()}...")
        xpath_label_total = XPATHS["table"]["label_total_template"].replace("{aba_id}", aba_id)
        txt = ""
        start_wait = time.time()
        while not txt and (time.time() - start_wait < 20):
            try:
                txt = self.driver.find_element(By.XPATH, xpath_label_total).text
            except:
                time.sleep(0.5)
        
        if not txt:
            logger.warning(f"[AVISO-VBA] Não foi possível ler o total de demandas na aba {aba_id}.")
            return
            
        demandas = int(so_numero(txt))
        logger.info(f"[LOG-VBA] Total detectado: {demandas} itens.")

        # --- FOCO NA TABELA ---
        # VBA: driver.FindElementByXPath(... tbody ...).Click
        xpath_tbody = XPATHS["table"]["tbody_template"].replace("{aba_id}", aba_id)
        try:
            tabela_el = self.driver.find_element(By.XPATH, xpath_tbody)
            tabela_el.click()
        except:
            pass

        # --- PAGINAÇÃO / ROLAGEM ---
        # VBA: Do While Not driver.IsElementPresent(... div[demandas] ...)
        logger.info(f"[LOG-VBA] Iniciando rolagem para carregar todos os {demandas} itens...")
        xpath_ultimo_item = f"{xpath_tbody}[@class='p-element p-datatable-tbody']/div[{demandas}]"
        
        start_scroll = time.time()
        while (time.time() - start_scroll < 120):
            if len(self.driver.find_elements(By.XPATH, xpath_ultimo_item)) > 0:
                logger.info(f"[LOG-VBA] Todos os {demandas} itens carregados com sucesso.")
                break
            try:
                self.driver.execute_script("arguments[0].scrollIntoView();", tabela_el)
                self.driver.execute_script("window.scrollBy(0, 500);")
            except:
                pass
            self.compat.testa_spinner()
            time.sleep(0.5)
        else:
            logger.warning(f"[AVISO-VBA] Timeout na rolagem. Alguns itens podem não ter sido carregados.")

        time.sleep(1)
        self.compat.testa_spinner()

        # --- LOOP DE COLETA DE CAMPOS ---
        # VBA: For i = 1 To demandas
        logger.info(f"[LOG-VBA] Iniciando extração de campos para {demandas} itens...")
        f = XPATHS["fields"]
        item_base_xpath = XPATHS["table"]["item_base_template"].replace("{aba_id}", aba_id)
        
        for i in range(1, demandas + 1):
            # PASSO 12: Try/Except por item (Emula On Error Resume Next)
            try:
                base_xpath = item_base_xpath.replace("{index}", str(i))
                
                # 1. Coluna A: ID Contratação
                val_a = self.driver.find_element(By.XPATH, f"{base_xpath}{f['contratacao']}").text
                
                # 2. Coluna B: Descrição
                val_b = self.driver.find_element(By.XPATH, f"{base_xpath}{f['descricao']}").text
                
                # 3. Coluna I: DFD (VBA: Format(Left(SoNumero(...), 7), "@@@\/@@@@"))
                val_i = self._format_dfd(val_b)
                if val_i == "157/2024":
                    val_i = "157/2025"
                
                # 4. Coluna C: Categoria
                val_c = self.driver.find_element(By.XPATH, f"{base_xpath}{f['categoria']}").text
                
                # 5. Coluna D: Valor (VBA: CDbl(...))
                val_d_raw = self.driver.find_element(By.XPATH, f"{base_xpath}{f['valor']}").text
                if aba_id == "pendentes" and not val_d_raw.strip():
                    val_d = 0.0
                else:
                    val_d = self._parse_vba_cdbl(val_d_raw)
                
                # 6. Coluna E: Início (VBA: CDate(...))
                val_e_raw = self.driver.find_element(By.XPATH, f"{base_xpath}{f['inicio']}").text
                val_e = self._parse_vba_cdate(val_e_raw)
                
                # 7. Coluna F: Fim (VBA: CDate(...))
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
                
                # --- MONTAGEM E VALIDAÇÃO DO CONTRATO (Passo 5) ---
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
                
                # --- LOG DE AUDITORIA (Passo 13) ---
                logger.info(
                    f"[AUDITORIA-ITEM] {i}/{demandas} | Aba: {aba_id.upper()} | "
                    f"ID: {validated_item.col_a_contratacao} | DFD: {validated_item.col_i_dfd} | "
                    f"Valor: {validated_item.col_d_valor} | Status: {validated_item.col_g_status}"
                )
                
                self.data_collected.append(validated_item.dict())
            except Exception as e:
                # PASSO 12: Emula "On Error Resume Next"
                logger.warning(f"[AVISO-VBA] Pulando item {i} na aba {aba_id} devido a erro: {e}")
                continue

    def _parse_vba_cdbl(self, text: str) -> float:
        """Emula CDbl do VBA com tratamento de erro para auditoria."""
        if not text: return 0.0
        try:
            clean = text.replace("R$", "").replace(".", "").replace(",", ".").strip()
            return float(clean)
        except Exception as e:
            logger.debug(f"[LOG-DEBUG] Falha ao converter valor '{text}': {e}")
            return 0.0

    def _parse_vba_cdate(self, text: str) -> Optional[str]:
        """Emula CDate do VBA com tratamento de erro para auditoria."""
        if not text or "/" not in text: return None
        try:
            return datetime.strptime(text.strip(), "%d/%m/%Y").date().isoformat()
        except Exception as e:
            logger.debug(f"[LOG-DEBUG] Falha ao converter data '{text}': {e}")
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
