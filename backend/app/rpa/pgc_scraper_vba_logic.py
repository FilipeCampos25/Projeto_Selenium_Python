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
from selenium.common.exceptions import WebDriverException
from .vba_compat import VBACompat, CheckpointFailureError
from .driver_factory import create_attached_driver, create_driver
from .chrome_attach import start_manual_login_session, wait_until_logged_in

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
        """
        Replica o "ponto de transição" do VBA antigo:
        - Aqui assumimos que o usuário JÁ fez o login manualmente no Chrome.
        - O WebDriver já está anexado na instância (debuggerAddress).
        - Portanto, não abrimos login e não interferimos no CAPTCHA/IdGov durante o login.

        O que fazemos:
        1) Validar que estamos na página pós-login (portal que lista o PGC).
        2) Clicar no card/atalho "PGC".
        3) Trocar para a nova janela/aba do PGC (como no VBA).
        """
        logger.info("=== PONTO DE TRANSIÇÃO (VBA) - Selenium assume APÓS login manual ===")

        # Checkpoint: portal pós-login carregado (equivalente ao VBA checando URL via /json)
        try:
            self.compat.wait_for_checkpoint(
                XPATHS["login"]["span_pgc_title"],
                "Planejamento e Gerenciamento de Contratações",
                timeout=45
            )
        except CheckpointFailureError:
            logger.error(
                "Não detectei a tela pós-login do portal. "
                "Garanta que o login manual foi concluído antes de iniciar a coleta."
            )
            return False
        except WebDriverException as e:
            logger.error(f"Conexão com o Chrome/Driver foi perdida: {e}")
            return False
        except Exception as e:
            logger.error(f"Falha inesperada validando pós-login: {e}")
            return False

        # Clica no PGC
        self.compat.safe_click(XPATHS["login"]["div_pgc_access"])

        # Troca de janela (Item 7 - fiel ao VBA)
        original_handles = set(self.driver.window_handles)
        if not self.compat.wait_for_new_window(original_handles):
            logger.error("Falha ao esperar pela nova janela do PGC.")
            return False

        for handle in self.driver.window_handles:
            self.driver.switch_to.window(handle)
            if XPATHS["login"]["window_title"] in (self.driver.title or ""):
                self.compat.last_handle = handle
                break
        else:
            logger.error("Não encontrou a janela do PGC.")
            return False

        logger.info("PGC acessado com sucesso (Selenium anexado pós-login).")
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

        # Coleta de dados com paginação (Replicando VBA: Do While ExisteBotaoProximaPagina)
        all_data = []
        pos = 1
        
        # Primeiro, calcula o total de páginas no VBA original (contando até o final)
        posM = self._count_total_pages()
        
        logger.info(f"Total de páginas detectadas (VBA): {posM}")
        
        # Volta para a primeira página (VBA: SelecionarPrimeiraPagina)
        self._go_to_first_page()
        
        while True:
            logger.info(f"Coletando página {pos}/{posM}")
            page_data = self._collect_current_page_rows()
            all_data.extend(page_data)
            
            if not self._has_next_page():
                break
            
            self._go_next_page()
            pos += 1
        
        logger.info(f"Coleta concluída. Total de registros: {len(all_data)}")
        return all_data

    def _count_total_pages(self) -> int:
        """Conta páginas totais como no VBA original."""
        count = 1
        # Vai avançando até não existir mais "próxima página"
        while self._has_next_page():
            self._go_next_page()
            count += 1
        return count

    def _go_to_first_page(self) -> None:
        """Volta para primeira página (equivalente VBA)."""
        # Implementação: clicar no botão "primeira página" se existir, senão usar setinha/atalho.
        first_xpath = XPATHS["pagination"].get("btn_first")
        if first_xpath:
            try:
                self.compat.safe_click(first_xpath)
                self.compat.testa_spinner()
                return
            except Exception:
                pass

        # fallback: tenta voltar várias páginas
        prev_xpath = XPATHS["pagination"].get("btn_prev")
        if prev_xpath:
            for _ in range(10):
                if not self._has_prev_page():
                    break
                self.compat.safe_click(prev_xpath)
                self.compat.testa_spinner()

    def _has_prev_page(self) -> bool:
        """Verifica existência da página anterior."""
        prev_xpath = XPATHS["pagination"].get("btn_prev")
        if not prev_xpath:
            return False
        try:
            el = self.driver.find_element(By.XPATH, prev_xpath)
            return el.is_enabled()
        except Exception:
            return False

    def _has_next_page(self) -> bool:
        """Verifica se existe próxima página."""
        next_xpath = XPATHS["pagination"].get("btn_next")
        if not next_xpath:
            return False
        try:
            el = self.driver.find_element(By.XPATH, next_xpath)
            return el.is_enabled()
        except Exception:
            return False

    def _go_next_page(self) -> None:
        """Avança para próxima página e aguarda carregamento."""
        next_xpath = XPATHS["pagination"].get("btn_next")
        if not next_xpath:
            raise RuntimeError("XPath de próxima página não configurado em pgc_xpaths.json")
        self.compat.safe_click(next_xpath)
        self.compat.testa_spinner()

    def _collect_current_page_rows(self) -> List[Dict[str, Any]]:
        """Coleta linhas da página atual."""
        rows_xpath = XPATHS["table"]["rows"]
        rows = self.driver.find_elements(By.XPATH, rows_xpath)
        data = []
        for r in rows:
            try:
                cols = r.find_elements(By.TAG_NAME, "td")
                if not cols:
                    continue
                row_dict = {
                    "DFD": cols[0].text.strip() if len(cols) > 0 else "",
                    "Requisitante": cols[1].text.strip() if len(cols) > 1 else "",
                    "Valor": cols[2].text.strip() if len(cols) > 2 else "",
                }
                data.append(row_dict)
            except Exception:
                continue
        return data


def run_pgc_scraper_vba(
    ano_ref: Optional[str] = None,
    ano: Optional[int] = None,
    mes: Optional[int] = None,
    driver=None,
    close_driver: bool = True
):
    """
    Wrapper do scraper PGC para compatibilidade com o service.

    MUDANÇA (fidelidade ao VBA antigo):
    - Se `driver` NÃO for fornecido, NÃO criamos Selenium de cara.
      Em vez disso:
        1) Abrimos o Chrome fora do Selenium com remote debugging.
        2) Usuário faz login manual.
        3) Detectamos pós-login via /json.
        4) Só então anexamos o Selenium (create_attached_driver).

    - Se `driver` for fornecido (ex: coleta unificada), assumimos que o driver
      já está logado e pronto (Selenium já anexado ou já controlando).
    """
    local_driver = None
    try:
        if not ano_ref and ano is not None:
            ano_ref = str(ano)
        if not ano_ref:
            raise ValueError("ano_ref é obrigatório.")

        if driver is None:
            # 1) Abrir Chrome fora do Selenium (equivalente ao VBA)
            start_url = os.getenv("PGC_URL") or XPATHS["login"]["url"]
            session = start_manual_login_session(start_url=start_url)

            # 2) Usuário faz login manual e nós monitoramos a URL via DevTools (/json)
            #    (equivalente ao loop do VBA lendo "urlAtual")
            wait_until_logged_in(
                port=session.port,
                timeout_s=int(os.getenv("LOGIN_TIMEOUT_S", "600"))
            )

            # 3) Somente agora anexamos o Selenium na instância existente
            debugger_address = f"127.0.0.1:{session.port}"
            local_driver = create_attached_driver(debugger_address=debugger_address, headless=False)
            driver = local_driver
        else:
            # Se veio de fora, não fecha aqui
            close_driver = False

        scraper = PGCScraperVBA(driver, ano_ref=ano_ref)
        if not scraper.A_Loga_Acessa_PGC():
            logger.error("[PGC] Pós-login não validado / PGC não acessado. Abortando coleta.")
            return []

        dados = scraper.A1_Demandas_DFD_PCA()
        return dados

    except Exception as e:
        logger.exception(f"[PGC] Erro: {e}")
        raise

    finally:
        if close_driver and driver is not None:
            try:
                driver.quit()
            except Exception:
                pass
