"""
driver_global.py
Armazena a instância global do driver para respeitar a lógica antiga.
"""
from selenium.webdriver.remote.webdriver import WebDriver
from typing import Optional

# Variável global para o driver
driver: Optional[WebDriver] = None

def get_driver() -> WebDriver:
    """Retorna a instância global do driver."""
    global driver
    if driver is None:
        raise RuntimeError("Driver não inicializado. Chame initialize_driver primeiro.")
    return driver

def set_driver(new_driver: WebDriver):
    """Define a instância global do driver."""
    global driver
    driver = new_driver

def close_driver():
    """Fecha o driver e limpa a variável global."""
    global driver
    if driver:
        try:
            driver.quit()
        except:
            pass
        driver = None
