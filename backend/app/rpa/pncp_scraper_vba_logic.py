"""
pncp_scraper_vba_logic.py
Implementação fiel à lógica do Módulo1.bas (VBA) para o PNCP.
Focado em fidelidade total aos XPaths, tempos de espera e tratamento de dados.
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
        logger.info(f"=== INICIANDO COLETA PNCP (Lógica VBA - Passo 7/8: Navegação e Waits) ===")
        
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
        """Lógica de coleta para cada aba (Reprovadas, Aprovadas, Pendentes)."""
        logger.info(f"Coletando aba: {aba_id}")
        
        # 1. Clica na aba (VBA: driver.FindElementByXPath(...).Click)
        aba_xpath = XPATHS["tabs"][aba_id]
        self.driver.find_element(By.XPATH, aba_xpath).click()
        
        # 2. Sincronização Fiel (VBA: Call testa_spinner)
        self.compat.testa_spinner()
        
        # 3. Aguarda estabilização da tabela (Passo 8: WebDriverWait explícito)
        try:
            WebDriverWait(self.driver, 20).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            time.sleep(0.5)
        except Exception as e:
            logger.warning(f"Aviso: Estabilização da aba {aba_id} demorou: {e}")

        # 4. Testa se não encontrou nada (VBA: If driver.FindElementsByXPath(...).Count = 0 Then ...)
        xpath_vazio = XPATHS["table"]["empty_message"]
        if len(self.driver.find_elements(By.XPATH, xpath_vazio)) > 0:
            logger.info(f"Nenhum item encontrado na aba {aba_id}.")
            return

        # 5. Loop de Coleta (VBA: For i = 1 To demandas)
        # No VBA, ele rola a tela para carregar os itens.
        f = XPATHS["fields"]
        
        # Pega o número de itens (VBA: demandas = driver.FindElementsByXPath(...).Count)
        xpath_itens = XPATHS["table"]["row_count_template"]
        demandas = len(self.driver.find_elements(By.XPATH, xpath_itens))
        logger.info(f"Detectadas {demandas} demandas na aba {aba_id}.")

        for i in range(1, demandas + 1):
            try:
                base_xpath = f"({xpath_itens})[{i}]"
                el_contratacao = self.driver.find_element(By.XPATH, f"{base_xpath}{f['id_contratacao']}")
                
                # Rola para o elemento (VBA: .ScrollIntoView)
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el_contratacao)
                
                # --- COLETA INCREMENTAL DE CAMPOS (Passo 9) ---
                # Cada campo é coletado e logado individualmente para garantir fidelidade ao VBA.
                
                # 1. Coluna A: ID Contratação
                val_a = el_contratacao.text
                logger.debug(f"Campo A (Contratação) coletado: {val_a}")
                
                # 2. Coluna B: Descrição
                val_b = self.driver.find_element(By.XPATH, f"{base_xpath}{f['descricao']}").text
                logger.debug(f"Campo B (Descrição) coletado: {val_b[:50]}...")
                
                # 3. Coluna I: DFD (Extraído da Descrição - VBA: Format(Left(SoNumero(...), 7), "@@@\/@@@@"))
                val_i = self._format_dfd(val_b)
                # Regra de Negócio Específica (VBA: If ... Value = "157/2024" Then ... = "157/2025")
                if val_i == "157/2024":
                    val_i = "157/2025"
                logger.debug(f"Campo I (DFD) processado: {val_i}")
                
                # 4. Coluna C: Categoria
                val_c = self.driver.find_element(By.XPATH, f"{base_xpath}{f['categoria']}").text
                logger.debug(f"Campo C (Categoria) coletado: {val_c}")
                
                # 5. Coluna D: Valor (VBA: CDbl(...))
                val_d_raw = self.driver.find_element(By.XPATH, f"{base_xpath}{f['valor']}").text
                val_d = self._parse_vba_cdbl(val_d_raw)
                logger.debug(f"Campo D (Valor) processado: {val_d} (Original: {val_d_raw})")
                
                # 6. Coluna E: Início (VBA: CDate(...))
                val_e_raw = self.driver.find_element(By.XPATH, f"{base_xpath}{f['inicio']}").text
                val_e = self._parse_vba_cdate(val_e_raw)
                logger.debug(f"Campo E (Início) processado: {val_e} (Original: {val_e_raw})")
                
                # 7. Coluna F: Fim (VBA: CDate(...))
                val_f_raw = self.driver.find_element(By.XPATH, f"{base_xpath}{f['fim']}").text
                val_f = self._parse_vba_cdate(val_f_raw)
                logger.debug(f"Campo F (Fim) processado: {val_f} (Original: {val_f_raw})")
                
                # 8. Coluna G: Status
                val_g = status_vba
                if aba_id == "pendentes":
                    try:
                        val_g = self.driver.find_element(By.XPATH, f"{base_xpath}{f['status_pendente']}").text
                    except:
                        pass
                logger.debug(f"Campo G (Status) definido: {val_g}")
                
                # 9. Coluna H: Status Tipo (VBA: .Range("H" ...).Value = "REPROVADA" / "APROVADA" / "PENDENTE")
                val_h = status_vba
                logger.debug(f"Campo H (Status Tipo) definido: {val_h}")

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
                
                # --- LOG DE VALIDAÇÃO CRUZADA (Passo 10) ---
                # Este log permite comparar linha a linha com o Excel gerado pelo VBA.
                logger.info(
                    f"[VALIDACAO-CRUZADA] Item {i} Aba {aba_id} | "
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
