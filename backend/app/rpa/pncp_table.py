"""
Arquivo: pncp_table.py
Descrição: Este arquivo faz parte do projeto e foi comentado para explicar a função de cada bloco de código.
"""

# backend/app/rpa/pncp_table.py
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from ..config import config
from typing import List, Dict
import time
import re

def _safe_text(el):
    """
    Função _safe_text:
    Executa a lógica principal definida nesta função.
    """
    try:
        return el.text.strip()
    except Exception:
        return ""

def extract_results_table(driver) -> List[Dict]:
    """
    Função extract_results_table:
    Executa a lógica principal definida nesta função.
    """
    """
    Locate the results table in page and return a list of row dicts.
    Each row dict includes core columns and a special key '_item_selector' containing an XPath to the details link.
    """
    wait = WebDriverWait(driver, config.EXPLICIT_TIMEOUT)
    possible_table_selectors = [
        (By.CSS_SELECTOR, "table#results"),
        (By.CSS_SELECTOR, "table.table"),
        (By.XPATH, "//table[contains(@class,'tabela') or contains(@id,'results') or contains(@class,'table')]"),
    ]
    table_el = None
    for sel in possible_table_selectors:
        try:
            table_el = driver.find_element(*sel)
            if table_el:
                break
        except Exception:
            table_el = None
    rows_data = []
    if not table_el:
        # try to find rows by common patterns
        try:
            rows = driver.find_elements(By.XPATH, "//div[contains(@class,'result-row') or contains(@class,'item-row')]")
            for i, r in enumerate(rows):
                rows_data.append({
                    "row_id": f"div-{i}",
                    "title": _safe_text(r),
                    "_item_selector": None
                })
        except Exception:
            return rows_data
        return rows_data

    try:
        # parse header to get column indices
        headers = []
        try:
            hdrs = table_el.find_elements(By.XPATH, ".//thead//th")
            headers = [h.text.strip() for h in hdrs if h.text.strip()]
        except Exception:
            pass

        tbody = table_el.find_element(By.TAG_NAME, "tbody")
        trs = tbody.find_elements(By.TAG_NAME, "tr")
        for ridx, tr in enumerate(trs):
            cols = tr.find_elements(By.TAG_NAME, "td")
            row = {"row_id": str(ridx)}
            # map columns by header length if possible
            for cidx, col in enumerate(cols):
                key = headers[cidx] if cidx < len(headers) else f"col_{cidx}"
                row[key] = _safe_text(col)
            # try to detect a details link inside row
            try:
                a = tr.find_element(By.XPATH, ".//a[contains(.,'Detalhes') or contains(.,'Visualizar') or contains(@title,'Visualizar')]")
                # store an XPath to this anchor relative to the whole document (for later clicking)
                # build a robust XPath using row index:
                xpath = f"(//table[contains(@class,'table') or contains(@id,'results')]//tbody//tr)[{ridx+1}]//a[contains(.,'Detalhes') or contains(.,'Visualizar') or contains(@title,'Visualizar')]"
                row["_item_selector"] = xpath
            except Exception:
                row["_item_selector"] = None
            rows_data.append(row)
    except Exception:
        # fallback generic parse
        try:
            trs = table_el.find_elements(By.XPATH, ".//tr")
            for i, tr in enumerate(trs):
                row_text = tr.text.strip()
                if not row_text:
                    continue
                rows_data.append({"row_id": str(i), "title": row_text, "_item_selector": None})
        except Exception:
            pass

    return rows_data
