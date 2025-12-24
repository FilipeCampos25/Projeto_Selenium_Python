"""
Arquivo: __init__.py
Descrição: Este arquivo faz parte do projeto e foi comentado para explicar a função de cada bloco de código.
"""

# backend/app/core/__init__.py
"""
Módulo core - componentes fundamentais do sistema.
"""
from backend.app.core.base_scraper import (
    BasePortalScraper,
    ScraperError,
    LoginFailedError,
    ElementNotFoundError,
    PaginationError
)

__all__ = [
    "BasePortalScraper",
    "ScraperError",
    "LoginFailedError",
    "ElementNotFoundError",
    "PaginationError",
]