"""
Arquivo: pncp_scraper.py
Descrição: Este arquivo faz parte do projeto e foi comentado para explicar a função de cada bloco de código.
"""

# Possui:
# - validação de selectors.json
# - placeholder substitution ({ano_ref})
# - fluxo completo pós-login (apply_login_context)
# - mantém login manual
# - mesma lógica madura de paginação e coleta
# - preserva fidelidade total ao projeto original + ao VBA antigo (selecionar PCA e buscar)

import os
import json
import time
import logging
from typing import Dict, Any, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from backend.app.core.base_scraper import (
    BasePortalScraper,
    LoginFailedError,
    ElementNotFoundError,
    ScraperError
)

logger = logging.getLogger(__name__)

# Caminho para arquivo de seletores
SELECTORS_PATH = os.path.join(os.path.dirname(__file__), "selectors.json")

def load_selectors(path: str = SELECTORS_PATH) -> Dict[str, Any]:
    """
    Função load_selectors:
    Executa a lógica principal definida nesta função.
    """
    """Carrega seletores do arquivo JSON e realiza validações básicas."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            selectors = json.load(f)
            logger.info(f"Seletores carregados de {path}")
    except FileNotFoundError:
        logger.error(f"Arquivo de seletores não encontrado: {path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao parsear JSON de seletores: {e}")
        raise

    # Valida chaves essenciais
    required = ["login_url"]
    missing = [k for k in required if k not in selectors]
    if missing:
        logger.error(f"Selectors.json inválido - chaves ausentes: {missing}")
        raise ValueError(f"Selectors.json inválido - chaves ausentes: {missing}")

    return selectors

def substitute_placeholders(selectors: Dict[str, Any], context: Dict[str, str]) -> Dict[str, Any]:
    """
    Função substitute_placeholders:
    Executa a lógica principal definida nesta função.
    """
    """Substitui placeholders simples em valores string dentro do dicionário de seletores."""
    def sub_value(v):
        """
        Função sub_value:
        Executa a lógica principal definida nesta função.
        """
        if isinstance(v, str):
            try:
                return v.format(**context)
            except Exception:
                return v
        return v

    return {
        k: (
            sub_value(v)
            if not isinstance(v, dict)
            else {sk: sub_value(sv) for sk, sv in v.items()}
        )
        for k, v in selectors.items()
    }


class PNCPScraperRefactored(BasePortalScraper):
    
    """
    Versão conservadora do scraper com melhorias de validação.
    Mantém fidelidade ao projeto original: login manual, sequência idêntica e uso dos XPATHs tal como informados em selectors.json.
    """

    def __init__(
        
        # Função __init__:
        # Executa a lógica principal definida nesta função.
        
        self,
        driver: Optional[WebDriver] = None,
        selectors: Optional[Dict[str, Any]] = None,
        wait_short: int = 10,
        wait_long: int = 60,
        headless: bool = False,
        remote_url: Optional[str] = None
    ):
        if selectors is None:
            selectors = load_selectors()

        super().__init__(
            driver=driver,
            selectors=selectors,
            wait_short=wait_short,
            wait_long=wait_long,
            headless=headless,
            remote_url=remote_url
        )
        self.ano_referencia: Optional[str] = None
        logger.info("PNCPScraperRefactored inicializado")

    # -------------------------------------------------------------------------
    # ENTRYPOINT
    # -------------------------------------------------------------------------
    def run(self, ano_ref: Optional[str] = None, max_pages: int = 0, output_path: Optional[str] = None):
        """
        Função run:
        Executa a lógica principal definida nesta função.
        """
        """
        Wrapper para compatibilidade com BasePortalScraper.
        Garante fechamento do driver.
        """
        try:
            return self.run_collection(ano_ref=ano_ref, max_pages=max_pages, output_path=output_path)
        finally:
            try:
                self.quit()
            except Exception:
                pass

    # -------------------------------------------------------------------------
    # IMPLEMENTAÇÕES ABSTRATAS
    # -------------------------------------------------------------------------
    def open_portal(self):
        """
        Função open_portal:
        Executa a lógica principal definida nesta função.
        """
        # A URL de login é aberta automaticamente pelo Selenium no docker-compose.yml (SE_START_URL)
        # O driver já deve estar na página de login.
        logger.info("Portal PNCP já deve estar aberto. Verifique o VNC na porta 7900.")
        # Não é necessário chamar self.driver.get(login_url) aqui, pois o Selenium já fez isso.
        # Se o driver não estiver na URL correta, o wait_manual_login falhará.
        time.sleep(2)
        logger.info("Pronto para login manual.")


    def wait_manual_login(self, timeout: int = 300) -> bool:
        """
        Função wait_manual_login:
        Executa a lógica principal definida nesta função.
        """
        """Aguarda login manual e detecta troca de URL."""
        logger.info("Aguardando login manual do usuário...")
        start = time.time()
        login_marker = self.selectors.get("login_success_marker")

        while True:
            if time.time() - start > timeout:
                raise LoginFailedError(
                    "Falha no processo de autenticação: nenhuma ação do usuário foi detectada no período esperado ou as credenciais informadas são inválidas."
                )

            try:
                if login_marker:
                    try:
                        # Tenta encontrar o marcador de sucesso de login
                        _ = self.driver.find_element(By.XPATH, login_marker)
                        logger.info("Login detectado por marcador")
                        return True
                    except Exception:
                        pass

                current = self.driver.current_url
                # Se a URL mudou e não contém "login", considera sucesso
                if current and "login" not in current.lower():
                    logger.info(f"Login detectado por mudança de URL: {current}")
                    return True
            except Exception:
                pass

            time.sleep(1)

    # -------------------------------------------------------------------------
    # MÉTODO ADICIONADO — Fluxo pós-login
    # -------------------------------------------------------------------------
    def apply_login_context(self, ano_ref: str):
        """
        Função apply_login_context:
        Executa a lógica principal definida nesta função.
        """
        """
        Executa:
        1) clicar PGC
        2) clicar Formação do PCA
        3) abrir dropdown PCA
        4) selecionar opção do ano {ano_ref}
        5) clicar buscar (se existir)
        6) aguardar spinner
        """

        s = self.selectors

        def resolve_selector(entry):
            """
            Função resolve_selector:
            Executa a lógica principal definida nesta função.
            """
            """Resolve dict {'by','value'} ou string XPATH"""
            if isinstance(entry, dict):
                by = entry.get("by", "xpath").lower()
                value = entry.get("value")
                if by == "id":
                    return (By.ID, value)
                if by == "css":
                    return (By.CSS_SELECTOR, value)
                return (By.XPATH, value)
            return (By.XPATH, entry)

        def safe_click(key, wait=0.4):
            """
            Função safe_click:
            Executa a lógica principal definida nesta função.
            """
            entry = s.get(key)
            if not entry:
                logger.debug(f"safe_click: seletor '{key}' não existe, pulando")
                return False
            by, val = resolve_selector(entry)
            try:
                el = self.driver.find_element(by, val)
                el.click()
                time.sleep(wait)
                return True
            except Exception as e:
                logger.debug(f"safe_click falhou '{key}': {e}")
                return False

        def wait_spinner(timeout=15):
            """
            Função wait_spinner:
            Executa a lógica principal definida nesta função.
            """
            entry = s.get("spinner")
            if not entry:
                return
            by, val = resolve_selector(entry)
            logger.debug("Aguardando spinner desaparecer...")
            start = time.time()
            while time.time() - start < timeout:
                try:
                    items = self.driver.find_elements(by, val)
                    if not items:
                        return
                except Exception:
                    return
                time.sleep(0.4)

        # 1) Clicar no PGC
        safe_click("link_pgc")
        wait_spinner()

        # 2) Clicar em Formação do PCA
        safe_click("button_formacao_pca")
        wait_spinner()

        # 3) abrir dropdown
        safe_click("pca_dropdown_toggle")
        wait_spinner()

        # 4) selecionar ano
        opt_tmpl = s.get("pca_option_template")
        if opt_tmpl:
            # O placeholder {ano_ref} já foi substituído em run_collection
            by, val = resolve_selector(opt_tmpl)
            start = time.time()
            found = False
            while time.time() - start < 10:
                try:
                    els = self.driver.find_elements(by, val)
                    if els:
                        els[0].click()
                        found = True
                        break
                except Exception:
                    pass
                time.sleep(0.4)
            if not found:
                logger.warning(f"Não encontrou opção PCA para ano {ano_ref}")

        wait_spinner()

        # 5) clicar buscar — se existir
        safe_click("buscar_button")
        wait_spinner()

        logger.info("apply_login_context finalizado: página preparada para coleta.")

    # -------------------------------------------------------------------------
    # Coleta dos dados
    # -------------------------------------------------------------------------
    def collect_page_data(self):
        """
        Função collect_page_data:
        Executa a lógica principal definida nesta função.
        """
        results = []

        table = self.selectors.get("minhauasg_table")
        rows_sel = self.selectors.get("table_rows")

        if not table or not rows_sel:
            logger.warning("Selectors da tabela não definidos")
            return results

        try:
            by_t, v_t = (
                (By.XPATH, table) if isinstance(table, str)
                else (By.XPATH if table["by"] == "xpath" else By.ID, table["value"])
            )
            _ = self.driver.find_element(by_t, v_t)  # garante que tabela existe

            by_r = By.XPATH if rows_sel["by"] == "xpath" else By.ID
            rows = self.driver.find_elements(by_r, rows_sel["value"])

            for i, r in enumerate(rows):
                cols = r.text.split("\n")
                results.append({"index": i, "raw": cols})

        except Exception as e:
            logger.error(f"collect_page_data erro: {e}")

        return results

    # -------------------------------------------------------------------------
    # Fluxo principal
    # -------------------------------------------------------------------------
    def run_collection(self, ano_ref: Optional[str] = None, max_pages: int = 0, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Função run_collection:
        Executa a lógica principal definida nesta função.
        """
        context = {}

        if ano_ref:
            context["ano_ref"] = ano_ref

        try:
            # Substitui placeholders ANTES de abrir o portal (se necessário)
            self.selectors = substitute_placeholders(self.selectors, context)
        except Exception:
            pass

        try:
            self.open_portal()
            self.wait_manual_login()

            # Se ano_ref não foi fornecido (o que não deve acontecer se a API for chamada),
            # o fluxo deve parar aqui, pois a API garante o ano_ref.
            if not ano_ref:
                raise ValueError("Ano de referência não fornecido após login manual.")

            # AQUI É ONDE ELE PARAVA — AGORA ENTRA O FLUXO CORRETO
            self.apply_login_context(ano_ref)

            pages = 0
            total = 0
            errors = []

            # ... (lógica de coleta de dados permanece a mesma)
            while True:
                data = self.collect_page_data()
                total += len(data)
                pages += 1

                if not self.go_next_page(next_button_key="paginator_next"):
                    break

                if max_pages and pages >= max_pages:
                    break

            result = {
                "status": "ok",
                "ano_referencia": ano_ref,
                "pages_collected": pages,
                "total_items": total,
                "errors": errors
            }

            if output_path:
                try:
                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    logger.warning(f"Falha ao salvar arquivo: {e}")

            return result

        except Exception as e:
            logger.exception(f"Erro durante run_collection: {e}")
            return {"status": "error", "msg": str(e)}
