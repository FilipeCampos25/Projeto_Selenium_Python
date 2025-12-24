"""
pgc_table_mapper.py

Mapeador avançado de tabelas internas.
"""

from typing import List, Dict, Any
import re
from decimal import Decimal, InvalidOperation
from dateutil import parser as dateparser
import logging
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def normalize_header(header: str) -> str:
    """
    Função normalize_header:
    Executa a lógica principal definida nesta função.
    """
    if header is None:
        return ""
    s = header.strip().lower()
    s = re.sub(r"\(.*?\)", "", s)
    replacements = {
        'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a',
        'é': 'e', 'ê': 'e',
        'í': 'i',
        'ó': 'o', 'ô': 'o', 'õ': 'o',
        'ú': 'u', 'ü': 'u',
        'ç': 'c'
    }
    for k, v in replacements.items():
        s = s.replace(k, v)
    s = re.sub(r"[^0-9a-z]+", "_", s)
    s = re.sub(r"_+", "_", s)
    s = s.strip("_")
    return s

TABLE_TYPE_KEYWORDS = {
    "itens": ["item", "descricao", "quantidade", "valor unitario", "valor", "total"],
    "subitens": ["subitem", "sub-item", "microitem", "descricao"],
    "origens": ["fonte", "origem", "recurso", "dotacao", "origem recurso"],
    "metas": ["meta", "indicador", "resultado", "quantidade meta"],
    "responsaveis": ["responsavel", "responsável", "executor", "gestor"],
    "cronograma": ["periodo", "mes", "ano", "data inicio", "data fim", "inicio", "fim"],
    "historico": ["historico", "observacao", "observação", "andamento"],
    "orcam": ["elemento", "elemento de despesa", "classificacao"],
    "documentos": ["arquivo", "documento", "anexo"]
}

def _score_table_type(headers_norm: List[str]):
    """
    Função _score_table_type:
    Executa a lógica principal definida nesta função.
    """
    scores = {}
    for tname, keywords in TABLE_TYPE_KEYWORDS.items():
        score = 0
        for h in headers_norm:
            for kw in keywords:
                if kw in h:
                    score += 1
        scores[tname] = score
    best = max(scores.items(), key=lambda x: (x[1], _type_priority(x[0])))
    return best[0], best[1]

def _type_priority(t: str) -> int:
    """
    Função _type_priority:
    Executa a lógica principal definida nesta função.
    """
    order = ["itens", "subitens", "origens", "metas", "responsaveis", "cronograma", "orcam", "documentos", "historico"]
    try:
        return len(order) - order.index(t)
    except ValueError:
        return 0

CURRENCY_RE = re.compile(r"[-+]?\s*[\d\.\,]+\s*(?:r\$|\$|eur|€)?", re.IGNORECASE)
NUMBER_CLEAN_RE = re.compile(r"[^\d\-\.,]")

def parse_money(value: str):
    """
    Função parse_money:
    Executa a lógica principal definida nesta função.
    """
    if value is None:
        return None
    s = value.strip()
    if s == "":
        return None
    s_clean = NUMBER_CLEAN_RE.sub("", s)
    if '.' in s_clean and ',' in s_clean:
        s_tmp = s_clean.replace('.', '').replace(',', '.')
    else:
        if ',' in s_clean and s_clean.count(',') > 0 and '.' not in s_clean:
            last_comma_idx = s_clean.rfind(',')
            decimals = len(s_clean) - last_comma_idx - 1
            if decimals == 2:
                s_tmp = s_clean.replace('.', '').replace(',', '.')
            else:
                s_tmp = s_clean.replace(',', '')
        else:
            s_tmp = s_clean
    try:
        d = Decimal(s_tmp)
        return float(d)
    except (InvalidOperation, ValueError):
        try:
            return float(s_tmp.replace(',', ''))
        except Exception:
            return None

def parse_number(value: str):
    """
    Função parse_number:
    Executa a lógica principal definida nesta função.
    """
    if value is None:
        return None
    s = value.strip()
    if s == "":
        return None
    s_clean = NUMBER_CLEAN_RE.sub("", s)
    try:
        if '.' in s_clean or ',' in s_clean:
            return parse_money(s)
        return float(s_clean)
    except:
        return None

def parse_date(value: str):
    """
    Função parse_date:
    Executa a lógica principal definida nesta função.
    """
    if value is None:
        return None
    s = value.strip()
    if s == "":
        return None
    try:
        dt = dateparser.parse(s, dayfirst=True, fuzzy=True)
        if dt:
            return dt.date().isoformat()
    except Exception:
        pass
    return s

def parse_cell(value: str):
    """
    Função parse_cell:
    Executa a lógica principal definida nesta função.
    """
    if value is None:
        return None
    v = value.strip()
    if v == "":
        return None
    if CURRENCY_RE.search(v):
        m = parse_money(v)
        if m is not None:
            return m
    if v.endswith("%"):
        try:
            return float(v.replace("%", "").replace(",", ".").strip()) / 100.0
        except:
            pass
    dt = parse_date(v)
    if dt and isinstance(dt, str) and re.match(r"^\d{4}-\d{2}-\d{2}$", dt):
        return dt
    num = parse_number(v)
    if num is not None:
        return num
    return v

def map_table(headers, rows, table_index=0):
    """
    Função map_table:
    Executa a lógica principal definida nesta função.
    """
    headers_norm = [normalize_header(h or "") for h in headers]
    headers_display = [h.strip() for h in headers]
    guessed_type, score = _score_table_type(headers_norm)
    mapped_rows = []
    for r_idx, row in enumerate(rows):
        parsed = {}
        if len(row) < len(headers_norm):
            row = row + [""] * (len(headers_norm) - len(row))
        for i, raw_cell in enumerate(row[:len(headers_norm)]):
            hnorm = headers_norm[i] if i < len(headers_norm) else f"col_{i}"
            try:
                parsed_value = parse_cell(raw_cell)
            except Exception as e:
                logger.debug("parse_cell error on row %d col %d: %s", r_idx, i, e)
                parsed_value = raw_cell.strip() if raw_cell is not None else None
            parsed[hnorm] = parsed_value
            parsed[f"{hnorm}__raw"] = raw_cell.strip() if raw_cell is not None else None
        mapped_rows.append(parsed)
    return {
        "table_index": table_index,
        "table_type_guess": guessed_type,
        "table_type_score": score,
        "headers": headers_display,
        "headers_normalized": headers_norm,
        "rows_parsed": mapped_rows,
        "rows_raw": rows
    }

def validate_pgc_table(driver: WebDriver, expected_title_xpath: str, expected_headers: List[str]) -> bool:
    """
    Implementa a validação semântica da tabela PGC (Item 8).
    
    Problema: O Python lê tabelas válidas, porém erradas.
    Correção: Confirmar título da página e cabeçalhos esperados.
    """
    logger.info("Iniciando validação semântica da tabela PGC...")
    
    # 1. Confirmar que o título da página corresponde ao PGC
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, expected_title_xpath))
        )
        logger.info("Título da página PGC confirmado.")
    except Exception as e:
        logger.warning(f"Título da página PGC NÃO CONFIRMADO: {e}")
        return False
        
    # 2. Confirmar cabeçalhos esperados
    try:
        # Encontra a tabela principal (assumindo que é a primeira ou a única relevante)
        table_el = driver.find_element(By.XPATH, "//table[contains(@class, 'table')] | //table")
        
        # Extrai os cabeçalhos
        ths = table_el.find_elements(By.XPATH, ".//thead//th")
        current_headers = [normalize_header(h.text.strip()) for h in ths if (h.text or "").strip() != ""]
        
        # Verifica se todos os cabeçalhos esperados estão presentes
        expected_norm = [normalize_header(h) for h in expected_headers]
        
        missing_headers = [h for h in expected_norm if h not in current_headers]
        
        if not missing_headers:
            logger.info("Cabeçalhos da tabela PGC confirmados.")
            return True
        else:
            logger.warning(f"Cabeçalhos da tabela PGC INCOMPATÍVEIS. Faltando: {missing_headers}")
            logger.debug(f"Cabeçalhos atuais normalizados: {current_headers}")
            return False
            
    except Exception as e:
        logger.warning(f"Falha ao validar cabeçalhos da tabela: {e}")
        return False

def map_tables_from_selenium(tables):
    """
    Função map_tables_from_selenium:
    Executa a lógica principal definida nesta função.
    """
    mapped = []
    for idx, t in enumerate(tables):
        try:
            if hasattr(t, "find_elements"):
                try:
                    ths = t.find_elements("xpath", ".//thead//th")
                except Exception:
                    ths = []
                headers = [h.text.strip() for h in ths if (h.text or "").strip() != ""]
                if not headers:
                    try:
                        first_row = t.find_element("xpath", ".//tbody/tr[1]")
                        cols = first_row.find_elements("xpath", "./td")
                        headers = [c.text.strip() for c in cols]
                        rows_el = t.find_elements("xpath", ".//tbody/tr[position()>1]")
                    except Exception:
                        rows_el = t.find_elements("xpath", ".//tbody/tr")
                else:
                    rows_el = t.find_elements("xpath", ".//tbody/tr")
                rows = []
                for r in rows_el:
                    try:
                        cols = r.find_elements("xpath", "./td")
                        row_vals = [c.text.strip() for c in cols]
                        rows.append(row_vals)
                    except:
                        rows.append([])
            else:
                headers = t.get("headers", [])
                rows = t.get("rows", [])
        except Exception as e:
            logger.exception("Erro extraindo tabela selenium index %s: %s", idx, e)
            continue
        mapped_t = map_table(headers, rows, table_index=idx)
        mapped.append(mapped_t)
    return mapped

def aggregate_mapped_tables(mapped_tables):
    """
    Função aggregate_mapped_tables:
    Executa a lógica principal definida nesta função.
    """
    agg = {"itens": [], "subitens": [], "origens": [], "metas": [], "responsaveis": [], "cronograma": [], "orcam": [], "documentos": [], "historico": [], "others": []}
    for mt in mapped_tables:
        typ = mt.get("table_type_guess")
        if typ in agg:
            agg[typ].append(mt)
        else:
            agg["others"].append(mt)
    return agg

def map_tables_from_extracted(extracted_tables):
    """
    Função map_tables_from_extracted:
    Executa a lógica principal definida nesta função.
    """
    tables_list = []
    if isinstance(extracted_tables, dict):
        for k, v in extracted_tables.items():
            headers = v.get("headers", [])
            rows = v.get("rows", [])
            tables_list.append({"headers": headers, "rows": rows})
    mapped = map_tables_from_selenium(tables_list)
    return aggregate_mapped_tables(mapped)