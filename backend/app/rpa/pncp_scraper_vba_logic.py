"""
pncp_scraper_vba_logic.py
Implementação fiel à lógica do Módulo1.bas (VBA) para o PNCP.
Focado em fidelidade total aos XPaths, tempos de espera e tratamento de dados.

HISTÓRICO DE ADAPTAÇÃO:
- Passo 11 a 17: Implementação de fidelidade, erros, logs, persistência e testes.
- Passo 18: Refatoração pós-fidelidade (Melhoria de legibilidade sem alteração lógica).
- Passo 2.1/2.2: Fidelidade de fluxo e esperas (Application.Wait).
- Passo 3.1/3.2/3.3: Fidelidade de tratamento de dados e extração (CDbl, CDate, SoNumero).
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
from .vba_compat import VBACompat
from ..api.schemas import PNCPItemSchema

# Configuração de Logger para Auditoria
logger = logging.getLogger(__name__)

# Carregar XPaths do arquivo JSON (Mapeamento direto do VBA)
XPATHS_PATH = os.path.join(os.path.dirname(__file__), "pncp_xpaths.json")
with open(XPATHS_PATH, "r", encoding="utf-8") as f:
    XPATHS = json.load(f)

def so_numero(text: str) -> str:
    """Emula a função SoNumero do VBA para limpeza de strings."""
    if not text:
        return ""
    return "".join(re.findall(r'\d+', text))

class PNCPScraperVBA:
    """
    Classe PNCPScraperVBA:
    Implementa o fluxo de coleta do PNCP replicando o comportamento do Módulo1.bas.
    Refatorada no Passo 18 para melhor legibilidade, mantendo fidelidade total.
    """
    def __init__(self, driver: WebDriver, ano_ref: str = "2025"):
        self.driver = driver
        self.ano_ref = ano_ref
        self.compat = VBACompat(driver)
        self.data_collected = []

    def Dados_PNCP(self) -> List[Dict[str, Any]]:
        """Replica Sub Dados_PNCP() do VBA. Entrypoint principal."""
        logger.info(f"=== [INÍCIO] COLETA PNCP REAL - ANO REF: {self.ano_ref} ===")
        
        try:
            self._preparar_navegação_inicial()
            self._selecionar_ano_pca()

            # --- COLETA POR ABAS (REPROVADAS -> APROVADAS -> PENDENTES) ---
            # Passo 4.2: Logs de auditoria fiéis ao VBA
            for aba_id, status in [("reprovadas", "REPROVADA"), ("aprovadas", "APROVADA"), ("pendentes", "PENDENTE")]:
                try:
                    logger.info(f"[LOG-VBA] Localizando demandas {aba_id}...")
                    self._coletar_aba(aba_id, status)
                except Exception as e:
                    logger.error(f"[ERRO-ABA] Falha na aba {aba_id.upper()}: {e}. Prosseguindo...")

        except Exception as e:
            logger.exception(f"[ERRO-FATAL] Exceção no fluxo Dados_PNCP: {e}")

        logger.info(f"=== [FIM] COLETA PNCP CONCLUÍDA. TOTAL: {len(self.data_collected)} ITENS ===")
        return self.data_collected

    def _preparar_navegação_inicial(self):
        """Sincronização e visibilidade inicial (Passo 2.1)."""
        # VBA: testa_spinner
        logger.info("[LOG-VBA] Sincronizando (testa_spinner)...")
        self.compat.testa_spinner()
        
        # VBA: Do ... Loop Until driver.FindElementByXPath(...).IsDisplayed
        logger.info("[LOG-VBA] Aguardando botão 'Formação do PCA'...")
        start_wait = time.time()
        while time.time() - start_wait < 50:
            # VBA: Application.Wait Now + TimeValue("00:00:01") / 4
            self.compat.wait(0.25)
            try:
                if self.driver.find_element(By.XPATH, XPATHS["pca_selection"]["button_formacao_pca"]).is_displayed():
                    break
            except:
                pass
        else:
            raise TimeoutError("Botão 'Formação do PCA' não apareceu.")

        # VBA: .ScrollIntoView e .Click
        logger.info("[LOG-VBA] Acessando 'Formação do PCA'...")
        btn = self.driver.find_element(By.XPATH, XPATHS["pca_selection"]["button_formacao_pca"])
        self.driver.execute_script("arguments[0].scrollIntoView();", btn)
        btn.click()
        
        # VBA: testa_spinner
        self.compat.testa_spinner()

    def _selecionar_ano_pca(self):
        """Seleção do ano no dropdown PCA (Passo 2.1)."""
        # VBA: Do While Not driver.IsElementPresent(By.XPath("//p-dropdown[@placeholder='Selecione PCA']"))
        logger.info("[LOG-VBA] Aguardando Dropdown PCA...")
        start_wait = time.time()
        while time.time() - start_wait < 30:
            if len(self.driver.find_elements(By.XPATH, XPATHS["pca_selection"]["dropdown_pca"])) > 0:
                break
            self.compat.wait(0.5)
        
        # VBA: testa_spinner
        self.compat.testa_spinner()
        
        # VBA: driver.FindElementByXPath("//p-dropdown[@placeholder='Selecione PCA']").Click
        logger.info(f"[LOG-VBA] Selecionando ano {self.ano_ref}...")
        self.driver.find_element(By.XPATH, XPATHS["pca_selection"]["dropdown_pca"]).click()
        
        # VBA: testa_spinner
        self.compat.testa_spinner()
        
        # VBA: driver.FindElementByXPath("//li[starts-with(@aria-label,'PCA " + self.ano_ref + " -')]", timeout:=50000, Raise:=False).Click
        li_xpath = XPATHS["pca_selection"]["li_pca_ano_template"].replace("{ano}", self.ano_ref)
        self.driver.find_element(By.XPATH, li_xpath).click()
        
        # VBA: testa_spinner
        self.compat.testa_spinner()
        
        # VBA: Application.Wait Now + TimeValue("00:00:01")
        self.compat.wait(1)

    def _coletar_aba(self, aba_id: str, status_vba: str):
        """Lógica de coleta por aba (Passo 2.1)."""
        # VBA: driver.FindElementByXPath("//a[@id='contratacoes-reprovadas']", ...).Click
        logger.info(f"[LOG-VBA] Acessando aba: {aba_id.upper()}")
        btn_aba = self.driver.find_element(By.XPATH, XPATHS["tabs"][aba_id])
        self.driver.execute_script("arguments[0].scrollIntoView();", btn_aba)
        btn_aba.click()
        
        # VBA: Application.Wait Now + TimeValue("00:00:01")
        self.compat.wait(1)
        
        # VBA: testa_spinner
        self.compat.testa_spinner()
        
        # 2. Verificação de dados
        xpath_vazio = f"//div[@aria-labelledby='{aba_id}']/div[@class='search-results']/div/div/div/div/div[2]/span"
        if len(self.driver.find_elements(By.XPATH, xpath_vazio)) > 0:
            logger.info(f"[LOG-VBA] Aba {aba_id.upper()} vazia.")
            return

        # 3. Total de demandas
        demandas = self._obter_total_demandas(aba_id)
        if demandas == 0: 
            logger.info(f"[LOG-VBA] Nenhuma demanda encontrada na aba {aba_id}.")
            return

        logger.info(f"[LOG-VBA] Total de demandas {aba_id}: {demandas}")

        # 4. Paginação/Rolagem (Passo 11)
        self._executar_rolagem_tabela(aba_id, demandas)

        # 5. Extração de itens (Passo 12/13)
        logger.info(f"[LOG-VBA] Varrendo as demandas {aba_id}...")
        self._extrair_itens_tabela(aba_id, demandas)

    def _obter_total_demandas(self, aba_id: str) -> int:
        """Extrai o número total de demandas da aba (Passo 3.2)."""
        xpath = XPATHS["table"]["label_total_template"].replace("{aba_id}", aba_id)
        txt = ""
        start = time.time()
        # VBA: Do While txt = ""
        while not txt and (time.time() - start < 20):
            try:
                txt = self.driver.find_element(By.XPATH, xpath).text
            except:
                time.sleep(0.5)
        # VBA: demandas = SoNumero(txt)
        return int(so_numero(txt)) if txt else 0

    def _executar_rolagem_tabela(self, aba_id: str, demandas: int):
        """Executa a rolagem fiel ao VBA para carregar todos os itens (Passo 5.1)."""
        xpath_tbody = XPATHS["table"]["tbody_template"].replace("{aba_id}", aba_id)
        xpath_ultimo = f"{xpath_tbody}[@class='p-element p-datatable-tbody']/div[{demandas}]"
        
        logger.info(f"[LOG-VBA] Rolando para carregar {demandas} itens...")
        
        try:
            tabela = self.driver.find_element(By.XPATH, xpath_tbody)
            # VBA: driver.FindElementByXPath(...).Click
            tabela.click()
        except: 
            tabela = None

        start = time.time()
        # VBA: Do While Not driver.IsElementPresent(By.XPath(.../div[demandas]))
        while (time.time() - start < 180): # Timeout estendido para segurança
            if len(self.driver.find_elements(By.XPATH, xpath_ultimo)) > 0:
                break
            
            try:
                # VBA: tabela.ScrollIntoView (Executado múltiplas vezes no loop)
                if tabela:
                    self.driver.execute_script("arguments[0].scrollIntoView();", tabela)
                
                # VBA: driver.FindElementByXPath(...tbody...).ScrollIntoView
                tbody_el = self.driver.find_element(By.XPATH, xpath_tbody)
                self.driver.execute_script("arguments[0].scrollIntoView();", tbody_el)
                
                # VBA: testa_spinner
                self.compat.testa_spinner()
                
                # Pequena rolagem adicional para forçar o lazy loading do portal
                self.driver.execute_script("window.scrollBy(0, 800);")
            except: 
                pass
            
            # VBA: testa_spinner (chamado novamente no loop)
            self.compat.testa_spinner()
            time.sleep(0.5)
        
        # VBA: Application.Wait Now + TimeValue("00:00:01")
        self.compat.wait(1)
        # VBA: testa_spinner
        self.compat.testa_spinner()

    def _extrair_itens_tabela(self, aba_id: str, demandas: int):
        """Loop de extração de campos com tratamento de erro por item (Passo 3.3)."""
        f = XPATHS["fields"]
        base_tmpl = XPATHS["table"]["item_base_template"].replace("{aba_id}", aba_id)
        
        for i in range(1, demandas + 1):
            try:
                base_xpath = base_tmpl.replace("{index}", str(i))
                
                # Extração direta seguindo XPaths do VBA (Passo 3.2)
                val_a = self.driver.find_element(By.XPATH, f"{base_xpath}{f['contratacao']}").text
                val_b = self.driver.find_element(By.XPATH, f"{base_xpath}{f['descricao']}").text
                val_c = self.driver.find_element(By.XPATH, f"{base_xpath}{f['categoria']}").text
                
                # Valor com tratamento CDbl (Passo 3.1)
                val_d_raw = self.driver.find_element(By.XPATH, f"{base_xpath}{f['valor']}").text
                # VBA: If Trim(...) = "" Then val = 0 Else val = CDbl(...)
                val_d = 0.0 if (not val_d_raw.strip()) else self._parse_vba_cdbl(val_d_raw)
                
                # Datas com tratamento CDate (Passo 3.1)
                val_e = self._parse_vba_cdate(self.driver.find_element(By.XPATH, f"{base_xpath}{f['inicio']}").text)
                val_f = self._parse_vba_cdate(self.driver.find_element(By.XPATH, f"{base_xpath}{f['fim']}").text)
                
                # Status e DFD (Passo 3.2)
                val_g = self._obter_status_item(aba_id, base_xpath, f)
                
                # Lógica DFD: Format(Left(SoNumero(descricao), 7), "@@@\/@@@@")
                val_i = self._format_dfd(val_b)
                # Correção erro temporário VBA: If val_i = "157/2024" Then val_i = "157/2025"
                if val_i == "157/2024": val_i = "157/2025"
                
                # Validação via Schema
                item = PNCPItemSchema(
                    col_a_contratacao=val_a, col_b_descricao=val_b, col_c_categoria=val_c,
                    col_d_valor=val_d, col_e_inicio=val_e, col_f_fim=val_f,
                    col_g_status=val_g, col_h_status_tipo="APROVADA" if aba_id == "aprovadas" else val_g,
                    col_i_dfd=val_i
                )
                
                logger.info(f"[AUDITORIA-ITEM] {i}/{demandas} | ID: {item.col_a_contratacao} | Status: {item.col_g_status}")
                self.data_collected.append(item.dict())
                
            except Exception as e:
                # Emula "On Error Resume Next" do VBA por item (Passo 6.2)
                logger.warning(f"[AVISO-VBA] Falha ao coletar item {i} na aba {aba_id.upper()}. Erro: {str(e)}. Pulando para o próximo item...")

    def _obter_status_item(self, aba_id: str, base_xpath: str, f: dict) -> str:
        """Extrai o status do item baseado na aba (Passo 3.2)."""
        if aba_id == "reprovadas": return "REPROVADA"
        # Na aba pendentes, o status vem de um span específico no XPath
        xpath = f"{base_xpath}{f['status_aprovada' if aba_id == 'aprovadas' else 'status_pendente']}"
        return self.driver.find_element(By.XPATH, xpath).text

    def _parse_vba_cdbl(self, text: str) -> float:
        """Emula CDbl do VBA (Passo 3.1)."""
        if not text: return 0.0
        try:
            # Remove R$, pontos de milhar e troca vírgula por ponto
            clean = text.replace("R$", "").replace(".", "").replace(",", ".").strip()
            return float(clean)
        except: return 0.0

    def _parse_vba_cdate(self, text: str) -> Optional[str]:
        """Emula CDate do VBA (Passo 3.1)."""
        if not text or "/" not in text: return None
        try:
            # Converte DD/MM/YYYY para ISO YYYY-MM-DD
            return datetime.strptime(text.strip(), "%d/%m/%Y").date().isoformat()
        except: return None

    def _format_dfd(self, descricao: str) -> str:
        """Emula Format(Left(SoNumero(desc), 7), '@@@\/@@@@') do VBA (Passo 3.1)."""
        nums = so_numero(descricao)
        # Pega os primeiros 7 dígitos
        base = nums[:7]
        if len(base) >= 7:
            return f"{base[:3]}/{base[3:7]}"
        return base

def run_pncp_scraper_vba(ano_ref: str = "2025") -> List[Dict[str, Any]]:
    """Entrypoint para o scraper PNCP com lógica VBA."""
    from .driver_factory import create_driver
    driver = create_driver(headless=False)
    try:
        scraper = PNCPScraperVBA(driver, ano_ref)
        from .pgc_scraper_vba_logic import PGCScraperVBA
        if PGCScraperVBA(driver, ano_ref).A_Loga_Acessa_PGC():
            return scraper.Dados_PNCP()
        return []
    finally:
        driver.quit()
