"""
Arquivo: config.py
Configuração adaptada para execução LOCAL (sem Docker)
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Configuração do carregamento de variáveis
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # API
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # ============================================================
    # 🔴 INÍCIO MODIFICAÇÃO LOCAL - REMOVER QUANDO VOLTAR DOCKER
    # ============================================================
    
    # Database (DESABILITADO PARA EXECUÇÃO LOCAL)
    # POSTGRES_USER: str = "postgres"
    # POSTGRES_PASSWORD: str = "postgres"
    # POSTGRES_DB: str = "projeto"
    # POSTGRES_HOST: str = "db"
    # POSTGRES_PORT: int = 5432
    # DATABASE_URL: Optional[str] = None
    
    # Valores dummy para não quebrar imports
    POSTGRES_USER: str = "local_disabled"
    POSTGRES_PASSWORD: str = "local_disabled"
    POSTGRES_DB: str = "local_disabled"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[str] = None

    # Selenium (MODO LOCAL - Chrome instalado na máquina)
    SELENIUM_MODE: str = "local"  # Alterado de "auto" para "local"
    SELENIUM_REMOTE_URL: Optional[str] = None  # Sem URL remota
    SELENIUM_HEADLESS: bool = False  # Navegador visível
    SELENIUM_TIMEOUT: int = 60

    # ============================================================
    # 🔴 FIM MODIFICAÇÃO LOCAL
    # ============================================================

    # App specific
    PNCP_DEFAULT_TIMEOUT: int = 2
    PGC_URL: Optional[str] = None

    @property
    def db_url(self) -> str:
        """
        DATABASE DESABILITADO PARA EXECUÇÃO LOCAL
        """
        # ============================================================
        # 🔴 INÍCIO MODIFICAÇÃO LOCAL - REMOVER QUANDO VOLTAR DOCKER
        # ============================================================
        
        # Retorna URL dummy para não quebrar código
        return "postgresql://disabled:disabled@localhost:5432/disabled"
        
        # ============================================================
        # 🔴 FIM MODIFICAÇÃO LOCAL
        # ============================================================
        
        # CÓDIGO ORIGINAL (DESCOMENTAR QUANDO VOLTAR DOCKER):
        # if self.DATABASE_URL:
        #     return self.DATABASE_URL
        # return (
        #     f"postgresql+psycopg2://"
        #     f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
        #     f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        # )


settings = Settings()