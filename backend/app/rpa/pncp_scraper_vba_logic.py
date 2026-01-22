"""
pncp_scraper_vba_logic.py
Implementação FINAL, 100% FIEL e COMPLETA à lógica do Módulo1.bas (VBA) para o PNCP.
Mantém todos os logs de auditoria, tratamentos de erro granulares e lógica de persistência.
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
from .driver_factory import create_driver

# Configuração de Logger para Auditoria (Fidelidade Passo 4.2)
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
    Fidelidade total aos XPaths, tempos de espera e tratamento de dados.
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
        logger.info("[LOG-VBA] Sincronizando (testa_spinner)...")
        self.compat.testa_spinner()
        
        logger.info("[LOG-VBA] Aguardando botão 'Formação do PCA'...")
        start_wait = time.time()
        while time.time() - start_wait < 50:
            self.compat.wait(0.25)
            try:
                if self.driver.find_element(By.XPATH, XPATHS["pca_selection"]["button_formacao_pca"]).is_displayed():
                    break
            except:
                pass
        else:
            raise TimeoutError("Botão 'Formação do PCA' não apareceu.")

        logger.info("[LOG-VBA] Acessando 'Formação do PCA'...")
        btn = self.driver.find_element(By.XPATH, XPATHS["pca_selection"]["button_formacao_pca"])
        self.driver.execute_script("arguments[0].scrollIntoView();", btn)
        btn.click()
        self.compat.testa_spinner()

    def _selecionar_ano_pca(self):
        """Seleção do ano no dropdown PCA (Passo 2.1)."""
        logger.info("[LOG-VBA] Aguardando Dropdown PCA...")
        start_wait = time.time()
        while time.time() - start_wait < 30:
            if len(self.driver.find_elements(By.XPATH, XPATHS["pca_selection"]["dropdown_pca"])) > 0:
                break
            self.compat.wait(0.5)
        
        self.compat.testa_spinner()
        logger.info(f"[LOG-VBA] Selecionando ano {self.ano_ref}...")
        self.driver.find_element(By.XPATH, XPATHS["pca_selection"]["dropdown_pca"]).click()
        self.compat.testa_spinner()
        
        li_xpath = XPATHS["pca_selection"]["li_pca_ano_template"].replace("{ano}", self.ano_ref)
        self.driver.find_element(By.XPATH, li_xpath).click()
        self.compat.testa_spinner()
        self.compat.wait(1)

    def _coletar_aba(self, aba_id: str, status_vba: str):
        """Lógica de coleta por aba (Passo 2.1)."""
        logger.info(f"[LOG-VBA] Acessando aba: {aba_id.upper()}")
        btn_aba = self.driver.find_element(By.XPATH, XPATHS["tabs"][aba_id])
        self.driver.execute_script("arguments[0].scrollIntoView();", btn_aba)
        btn_aba.click()
        self.compat.wait(1)
        self.compat.testa_spinner()
        
        xpath_vazio = f"//div[@aria-labelledby='{aba_id}']/div[@class='search-results']/div/div/div/div/div[2]/span"
        if len(self.driver.find_elements(By.XPATH, xpath_vazio)) > 0:
            logger.info(f"[LOG-VBA] Aba {aba_id.upper()} vazia.")
            return

        demandas = self._obter_total_demandas(aba_id)
        if demandas == 0: 
            logger.info(f"[LOG-VBA] Nenhuma demanda encontrada na aba {aba_id}.")
            return

        logger.info(f"[LOG-VBA] Total de demandas {aba_id}: {demandas}")
        self._executar_rolagem_tabela(aba_id, demandas)
        logger.info(f"[LOG-VBA] Varrendo as demandas {aba_id}...")
        self._extrair_itens_tabela(aba_id, demandas)

    def _obter_total_demandas(self, aba_id: str) -> int:
        """Extrai o número total de demandas da aba (Passo 3.2)."""
        xpath = XPATHS["table"]["label_total_template"].replace("{aba_id}", aba_id)
        txt = ""
        start = time.time()
        while not txt and (time.time() - start < 20):
            try:
                txt = self.driver.find_element(By.XPATH, xpath).text
            except:
                time.sleep(0.5)
        return int(so_numero(txt)) if txt else 0

    def _get_scrollable_container(self, element):
        """
        Encontra o container realmente scrollável (overflow auto/scroll) subindo no DOM.
        Isso é essencial para tabelas virtualizadas (PrimeNG/p-table etc.), onde o scroll
        não acontece no window.
        """
        js = r"""
        const el = arguments[0];
        function isScrollable(node) {
            if (!node) return false;
            const style = window.getComputedStyle(node);
            const overflowY = style.overflowY;
            const canScroll = (overflowY === 'auto' || overflowY === 'scroll');
            if (!canScroll) return false;
            return (node.scrollHeight - node.clientHeight) > 10;
        }

        let node = el;
        // sobe até encontrar um pai scrollável
        while (node && node !== document.body) {
            if (isScrollable(node)) return node;
            node = node.parentElement;
        }

        // fallback: tentar body/documentElement se fizer sentido
        if (isScrollable(document.documentElement)) return document.documentElement;
        if (isScrollable(document.body)) return document.body;

        return null;
        """
        try:
            return self.driver.execute_script(js, element)
        except:
            return None

    def _count_items_loaded(self, xpath_tbody: str) -> int:
        """
        Conta itens carregados no tbody de forma tolerante a variações:
        - alguns layouts usam <tr>
        - outros usam <div> dentro do tbody (ou wrappers)
        """
        js = r"""
        const xpath = arguments[0];
        const r = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
        const tbody = r.singleNodeValue;
        if (!tbody) return 0;

        // conta filhos diretos comuns
        const direct = tbody.querySelectorAll(':scope > tr, :scope > div').length;
        if (direct > 0) return direct;

        // fallback: conta linhas/cards em profundidade (último recurso)
        const deep = tbody.querySelectorAll('tr, div').length;
        return deep;
        """
        try:
            return int(self.driver.execute_script(js, xpath_tbody) or 0)
        except:
            # fallback Python puro
            try:
                tbody_el = self.driver.find_element(By.XPATH, xpath_tbody)
                # tenta tr primeiro, depois div
                trs = tbody_el.find_elements(By.XPATH, "./tr")
                if trs:
                    return len(trs)
                divs = tbody_el.find_elements(By.XPATH, "./div")
                return len(divs)
            except:
                return 0

    def _get_scrollable_container(self, element):
        """
        Encontra o container realmente scrollável (overflow auto/scroll) subindo no DOM.
        Isso é essencial para tabelas virtualizadas (PrimeNG/p-table etc.), onde o scroll
        não acontece no window.
        """
        js = r"""
        const el = arguments[0];
        function isScrollable(node) {
            if (!node) return false;
            const style = window.getComputedStyle(node);
            const overflowY = style.overflowY;
            const canScroll = (overflowY === 'auto' || overflowY === 'scroll');
            if (!canScroll) return false;
            return (node.scrollHeight - node.clientHeight) > 10;
        }

        let node = el;
        // sobe até encontrar um pai scrollável
        while (node && node !== document.body) {
            if (isScrollable(node)) return node;
            node = node.parentElement;
        }

        // fallback: tentar body/documentElement se fizer sentido
        if (isScrollable(document.documentElement)) return document.documentElement;
        if (isScrollable(document.body)) return document.body;

        return null;
        """
        try:
            return self.driver.execute_script(js, element)
        except:
            return None

    def _count_items_loaded(self, xpath_tbody: str) -> int:
        """
        Conta itens carregados no tbody de forma tolerante a variações:
        - alguns layouts usam <tr>
        - outros usam <div> dentro do tbody (ou wrappers)
        """
        js = r"""
        const xpath = arguments[0];
        const r = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
        const tbody = r.singleNodeValue;
        if (!tbody) return 0;

        // conta filhos diretos comuns
        const direct = tbody.querySelectorAll(':scope > tr, :scope > div').length;
        if (direct > 0) return direct;

        // fallback: conta linhas/cards em profundidade (último recurso)
        const deep = tbody.querySelectorAll('tr, div').length;
        return deep;
        """
        try:
            return int(self.driver.execute_script(js, xpath_tbody) or 0)
        except:
            # fallback Python puro
            try:
                tbody_el = self.driver.find_element(By.XPATH, xpath_tbody)
                # tenta tr primeiro, depois div
                trs = tbody_el.find_elements(By.XPATH, "./tr")
                if trs:
                    return len(trs)
                divs = tbody_el.find_elements(By.XPATH, "./div")
                return len(divs)
            except:
                return 0

    def _executar_rolagem_tabela(self, aba_id: str, demandas: int):
        """
        Executa a rolagem para carregar todos os itens (estilo VBA),
        porém corrigindo o problema comum do PNCP: o scroll real ocorre
        num container interno (overflow auto), não no window.

        Critérios de parada:
        - atingiu 'demandas' itens carregados, OU
        - estabilizou (não aumentou contagem) após várias tentativas, OU
        - timeout.
        """
        xpath_tbody = XPATHS["table"]["tbody_template"].replace("{aba_id}", aba_id)

        if not demandas or demandas <= 0:
            logger.info("[LOG-VBA] Demandas = 0, nenhuma rolagem necessária.")
            self.compat.testa_spinner()
            return

        logger.info(f"[LOG-VBA] Rolando para carregar até {demandas} itens...")

        # 1) localizar o tbody e o container scrollável correto
        tbody_el = None
        container = None

        try:
            tbody_el = self.driver.find_element(By.XPATH, xpath_tbody)
        except Exception as e:
            logger.warning(f"[LOG-VBA] Não foi possível localizar tbody para rolagem: {e}")
            self.compat.testa_spinner()
            return

        try:
            # tenta dar foco (como no VBA)
            try:
                tbody_el.click()
            except:
                pass

            container = self._get_scrollable_container(tbody_el)

            # fallback se não achou container: tenta usar o próprio tbody
            if container is None:
                container = tbody_el
        except:
            container = tbody_el

        # 2) loop de rolagem com “estabilização” (robusto para virtualização)
        start = time.time()
        timeout_s = 180

        stagnant_rounds = 0
        max_stagnant_rounds = 10  # ~10 ciclos sem aumento => fim provável
        last_count = -1

        # scroll step: maior que 800 para reduzir iterações em listas longas
        step_px = 1200

        while (time.time() - start) < timeout_s:
            # sempre espera spinner antes de medir
            self.compat.testa_spinner()

            current_count = self._count_items_loaded(xpath_tbody)

            # se atingiu o esperado, encerra
            if current_count >= demandas:
                logger.info(f"[LOG-VBA] Itens carregados: {current_count}/{demandas} (OK).")
                break

            # heurística de estabilização (virtualização pode impedir item N existir no DOM)
            if current_count == last_count:
                stagnant_rounds += 1
            else:
                stagnant_rounds = 0
                last_count = current_count

            logger.info(
                f"[LOG-VBA] Itens visíveis/carregados: {current_count}/{demandas} | "
                f"estagnado: {stagnant_rounds}/{max_stagnant_rounds}"
            )

            # se não cresce mais, provavelmente chegou no fim do que a tela consegue carregar
            if stagnant_rounds >= max_stagnant_rounds:
                logger.warning(
                    "[LOG-VBA] Contagem estabilizou; encerrando rolagem para evitar loop infinito. "
                    "Isso é esperado em tabelas virtualizadas."
                )
                break

            # 3) rolar no container certo
            try:
                # garante que o container esteja em viewport (só por segurança)
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", container)
                except:
                    pass

                # scroll “à la VBA”, mas no elemento certo
                js_scroll = r"""
                const el = arguments[0];
                const step = arguments[1];

                // se for o documentElement/body, usa window
                if (el === document.body || el === document.documentElement) {
                    window.scrollBy(0, step);
                    return;
                }

                // caso container comum
                el.scrollTop = el.scrollTop + step;

                // força disparo de evento scroll (alguns frameworks escutam isso)
                el.dispatchEvent(new Event('scroll', { bubbles: true }));
                """
                self.driver.execute_script(js_scroll, container, step_px)
            except Exception:
                # fallback extremo: tenta window
                try:
                    self.driver.execute_script("window.scrollBy(0, arguments[0]);", step_px)
                except:
                    pass

            # 4) espera “VBA-style”
            self.compat.testa_spinner()
            time.sleep(0.5)

        # pós loop
        self.compat.wait(1)
        self.compat.testa_spinner()

    def _extrair_itens_tabela(self, aba_id: str, demandas: int):
        """Loop de extração de campos com tratamento de erro por item (Passo 3.3)."""
        f = XPATHS["fields"]
        base_tmpl = XPATHS["table"]["item_base_template"].replace("{aba_id}", aba_id)
        
        for i in range(1, demandas + 1):
            try:
                base_xpath = base_tmpl.replace("{index}", str(i))
                
                # Função auxiliar para emular On Error Resume Next granular por campo
                def get_safe_text(xpath_suffix, default=""):
                    try:
                        return self.driver.find_element(By.XPATH, f"{base_xpath}{xpath_suffix}").text
                    except:
                        return default

                # Extração direta seguindo XPaths do VBA (Passo 3.2)
                val_a = get_safe_text(f['contratacao'])
                val_b = get_safe_text(f['descricao'])
                val_c = get_safe_text(f['categoria'])
                
                # Valor com tratamento CDbl (Passo 3.1)
                val_d_raw = get_safe_text(f['valor'])
                val_d = 0.0 if (not val_d_raw.strip()) else self._parse_vba_cdbl(val_d_raw)
                
                # Datas com tratamento CDate (Passo 3.1)
                val_e = self._parse_vba_cdate(get_safe_text(f['inicio']))
                val_f = self._parse_vba_cdate(get_safe_text(f['fim']))
                
                # Status e DFD (Passo 3.2)
                try:
                    if aba_id == "reprovadas": 
                        val_g = "REPROVADA"
                    else:
                        xpath_status = f"{base_xpath}{f['status_aprovada' if aba_id == 'aprovadas' else 'status_pendente']}"
                        val_g = self.driver.find_element(By.XPATH, xpath_status).text
                except:
                    val_g = "ERRO_STATUS"
                
                # Lógica DFD: Format(Left(SoNumero(descricao), 7), "@@@\/@@@@")
                val_i = self._format_dfd(val_b)
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
                logger.warning(f"[AVISO-VBA] Falha ao coletar item {i} na aba {aba_id.upper()}. Erro: {str(e)}. Pulando...")

    def _parse_vba_cdbl(self, text: str) -> float:
        """Emula CDbl do VBA (Passo 3.1)."""
        if not text: return 0.0
        try:
            clean = text.replace("R$", "").replace(".", "").replace(",", ".").strip()
            return float(clean)
        except: return 0.0

    def _parse_vba_cdate(self, text: str) -> Optional[str]:
        """Emula CDate do VBA (Passo 3.1)."""
        if not text or "/" not in text: return None
        try:
            return datetime.strptime(text.strip(), "%d/%m/%Y").date().isoformat()
        except: return None

    def _format_dfd(self, descricao: str) -> str:
        r"""Emula Format(Left(SoNumero(desc), 7), '@@@\/@@@@') do VBA (Passo 3.1)."""
        nums = so_numero(descricao)
        base = nums[:7]
        if len(base) >= 7:
            return f"{base[:3]}/{base[3:7]}"
        return base

def run_pncp_scraper_vba(
    ano_ref: Optional[str] = None,
    ano: Optional[int] = None,
    mes: Optional[int] = None,
    driver=None,
    close_driver: bool = True,
    reuse_driver: bool = False
):
    """
    Wrapper do scraper PNCP para compatibilidade com o service.
    Aceita `ano_ref` (preferencial) e mantém compatibilidade com `ano`.
    """
    local_driver = None
    helper = None
    try:
        if not ano_ref and ano is not None:
            ano_ref = str(ano)
        if not ano_ref:
            raise ValueError("ano_ref é obrigatório.")

        if driver is None:
            local_driver = create_driver(headless=False)
            driver = local_driver
        else:
            close_driver = False

        # Login manual + contexto inicial usando helpers já existentes
        from .pncp_scraper import load_selectors, substitute_placeholders, PNCPScraperRefactored

        selectors = load_selectors()
        try:
            selectors = substitute_placeholders(selectors, {"ano_ref": ano_ref})
        except Exception:
            pass

        login_url = selectors.get("login_url")
        if login_url and not reuse_driver:
            driver.get(login_url)

        helper = PNCPScraperRefactored(driver=driver, selectors=selectors, headless=False)
        if not reuse_driver:
            helper.wait_manual_login()
        helper.apply_login_context(ano_ref)

        pncp_vba = PNCPScraperVBA(driver, ano_ref)
        dados = pncp_vba.Dados_PNCP()
        return dados

    except Exception as e:
        logger.exception(f"[PNCP] Erro: {e}")
        raise

    finally:
        if helper is not None and close_driver:
            try:
                helper.quit()
            except Exception:
                pass
            # helper.quit() já encerra o driver
            driver = None
        if close_driver and driver is not None:
            try:
                driver.quit()
            except Exception:
                pass
