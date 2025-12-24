"""
Arquivo: pncp_item.py
Descrição: Este arquivo faz parte do projeto e foi comentado para explicar a função de cada bloco de código.
"""

# backend/app/rpa/pncp_item.py
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from ..config import config
from .dfd_ocr import perform_ocr_on_dfd
import time
from typing import Dict, Any

def _safe_text(el):
    """
    Função _safe_text:
    Executa a lógica principal definida nesta função.
    """
    try:
        return el.text.strip()
    except Exception:
        return ""

def extract_item_details(driver) -> Dict[str, Any]:
    """
    Função extract_item_details:
    Executa a lógica principal definida nesta função.
    """
    """
    Extract details from an opened item page. Returns a dict with header, tables and DFD info.
    """
    wait = WebDriverWait(driver, config.EXPLICIT_TIMEOUT)
    details = {"header": {}, "tables": [], "dfd": None}

    # header: try multiple common patterns
    try:
        # common header region
        header_selectors = [
            (By.CSS_SELECTOR, "div.header"),
            (By.XPATH, "//div[contains(@class,'cabecalho') or contains(@class,'header')]"),
            (By.CSS_SELECTOR, "div.item-header"),
        ]
        header_text = {}
        for sel in header_selectors:
            try:
                el = driver.find_element(*sel)
                # collect label/value pairs if present
                rows = el.find_elements(By.XPATH, ".//div[contains(@class,'row') or .//label]")
                if rows:
                    for r in rows:
                        try:
                            labels = r.find_elements(By.XPATH, ".//label")
                            spans = r.find_elements(By.XPATH, ".//span")
                            if labels and spans:
                                for i in range(min(len(labels), len(spans))):
                                    header_text[labels[i].text.strip()] = spans[i].text.strip()
                            else:
                                # fallback: split by colon
                                txt = r.text.strip()
                                if ":" in txt:
                                    k, v = txt.split(":", 1)
                                    header_text[k.strip()] = v.strip()
                        except Exception:
                            continue
                if header_text:
                    details["header"] = header_text
                    break
            except Exception:
                continue
        # if still empty, try page title
        if not details["header"]:
            try:
                title = driver.find_element(By.XPATH, "//h1").text.strip()
                details["header"]["title"] = title
            except Exception:
                pass
    except Exception:
        pass

    # tables: discover tables within the item
    try:
        tables = driver.find_elements(By.XPATH, "//table")
        for t in tables:
            try:
                hdrs = [th.text.strip() for th in t.find_elements(By.XPATH, ".//thead//th")]
                body_rows = []
                for tr in t.find_elements(By.XPATH, ".//tbody//tr"):
                    cols = [td.text.strip() for td in tr.find_elements(By.XPATH, ".//td")]
                    body_rows.append(cols)
                details["tables"].append({"headers": hdrs, "rows": body_rows})
            except Exception:
                continue
    except Exception:
        pass

    # DFD: find image or link with DFD and call OCR stub
    try:
        # try common DFD selectors
        for sel in [
            (By.XPATH, "//img[contains(@src,'dfd') or contains(@alt,'DFD')]"),
            (By.XPATH, "//a[contains(.,'DFD') or contains(@href,'dfd') or contains(@title,'DFD')]"),
            (By.CSS_SELECTOR, "img.dfd"),
        ]:
            try:
                el = driver.find_element(*sel)
                tag = el.tag_name.lower()
                if tag == "img":
                    src = el.get_attribute("src")
                    dfd_text = perform_ocr_on_dfd(src)
                    details["dfd"] = {"src": src, "ocr_text": dfd_text}
                    break
                else:
                    href = el.get_attribute("href")
                    dfd_text = perform_ocr_on_dfd(href)
                    details["dfd"] = {"href": href, "ocr_text": dfd_text}
                    break
            except Exception:
                continue
    except Exception:
        pass

    return details
