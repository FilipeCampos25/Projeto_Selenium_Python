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

        # Coleta de dados com paginação (Replicando VBA: Do While ExisteBotaoProximaPagina)
        all_data = []
        pos = 1
        
        # Primeiro, calcula o total de páginas no VBA original (contando até o final)
        posM = self._count_total_pages()
        logger.info(f"Total de páginas detectadas: {posM}")
        
        # Antes de iniciar a leitura, aguarda estabilidade do DOM/tabela
        if not self._wait_table_stable(max_checks=6, interval=0.5): # .
            logger.warning(f"Timeout aguardando estabilidade do DOM na página {pos}") # .

        while pos <= posM:
            logger.info(f"Coletando página {pos} de {posM}...")
            page_data = self._read_current_table()
            all_data.extend(page_data)

            # Log detalhado por página: quantidade e conteúdo dos itens coletados
            try:
                logger.info(f"Página {pos}: coletados {len(page_data)} itens")
                logger.info(f"Página {pos} - itens: {json.dumps(page_data, ensure_ascii=False)}")
            except Exception:
                logger.info(f"Página {pos}: erro ao serializar itens para log")
            
            if pos < posM:
                if not self._go_to_next_page():
                    logger.warning(f"Parado na página {pos}. Botão próxima não disponível ou erro na navegação.")
                    break
            pos += 1
            
        self.data_collected = all_data
        return all_data

    def _count_total_pages(self) -> int:
        """
        Adaptação fiel do VBA:
        - Vai direto para a última página (>>)
        - Descobre o número real da última página pelos botões numéricos
        - Volta para a primeira página (<<)
        """

        total_paginas = 1

        try:
            # 1. Ir direto para a última página (>>)
            self.compat.safe_click(XPATHS["pagination"]["btn_last"])
            self.compat.testa_spinner()

            # 2. Ler os botões numéricos (1,2,3,...)
            btns = self.driver.find_elements(
                By.XPATH,
                XPATHS["pagination"]["btns_pages"]
            )

            numeros = [
                int(b.text)
                for b in btns
                if b.text and b.text.isdigit()
            ]

            if numeros:
                total_paginas = max(numeros)
        except Exception as e:
            logger.warning(f"Erro ao descobrir total de páginas: {e}")

        finally:
            # 3. Voltar para a primeira página (<<)
            try:
                self.compat.safe_click(XPATHS["pagination"]["btn_first"])
                # self.compat.testa_spinner()
            except Exception as e:
               logger.warning(f"Erro ao voltar para página 1: {e}")

        return total_paginas

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

    # Espera a tabela estabilizar antes de ler
    def _wait_table_stable(self, max_checks: int = 10, interval: float = 0.5) -> bool:
        """
        Aguarda a tabela estabilizar antes de iniciar a leitura da página.
        Estratégia: verifica o número de linhas em duas leituras consecutivas
        separadas por `interval`. Também chama `testa_spinner` para garantir
        que o carregamento visual terminou.
        Retorna True se a tabela parecer estável (linhas > 0 e mesmo count duas vezes),
        ou False se timeout.
        """
        last_count = -1
        checks = 0
        while checks < max_checks:
            try:
                self.compat.testa_spinner()
                rows = self.driver.find_elements(By.XPATH, XPATHS["table"]["rows"])
                count = len(rows)
                if count > 0 and count == last_count:
                    return True
                last_count = count
            except Exception as e:
                logger.debug(f"_wait_table_stable check error: {e}")
            time.sleep(interval)
            checks += 1

        # Última tentativa: ver se há pelo menos alguma linha
        try:
            rows = self.driver.find_elements(By.XPATH, XPATHS["table"]["rows"])
            return len(rows) > 0
        except Exception:
            return False

    def _go_to_next_page(self) -> bool:
        """
        Clica no botão próxima e aguarda a tabela recarregar.
        Replica o comportamento do VBA: ClicarProximaPagina + EsperarCarregar.
        """
        try:
            # Clica próxima
            if not self.compat.safe_click(XPATHS["pagination"]["btn_next"]):
                logger.error("Falha ao clicar botão próxima.")
                return False
            
            # Aguarda a tabela recarregar (checkpoint na tabela)
            try:
                self.compat.wait_for_checkpoint(XPATHS["table"]["rows"], timeout=15)
            except CheckpointFailureError:
                logger.error("Falha ao aguardar recarga da tabela após clique próxima.")
                return False
            
            # Aguarda spinner desaparecer
            self.compat.testa_spinner()
            return True
            
        except Exception as e:
            logger.error(f"Erro inesperado ao avançar para próxima página: {e}")
            return False

    def _parse_currency(self, value_str: str) -> float:
        try:
            # Remove "R$", pontos de milhar e troca vírgula por ponto
            clean_value = value_str.replace("R$", "").replace(".", "").replace(",", ".").strip()
            return float(clean_value)
        except Exception as e:
            logger.warning(f"Erro ao converter valor monetário '{value_str}', retornando 0.0: {e}")
            return 0.0

def run_pgc_scraper_vba(
    ano: int,
    mes: int,
    driver=None,               # <-- NOVO
    close_driver: bool = True  # <-- NOVO (controle de quit)
):
    local_driver = None
    try:
        if driver is None:
            local_driver = create_driver(headless=False)
            driver = local_driver
        else:
            # se veio de fora, não fecha aqui
            close_driver = False

        # ... resto da lógica atual do PGC usando "driver" ...
        # exemplo:
        # scraper = PGCScraperVBA(driver, ...)  (ou do jeito que está no arquivo)
        # scraper.run()

        return True

    except Exception as e:
        logger.exception(f"[PGC] Erro: {e}")
        raise

    finally:
        if close_driver and driver is not None:
            try:
                driver.quit()
            except:
                pass

