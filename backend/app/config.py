"""
Arquivo: config.py
Descrição: Este arquivo faz parte do projeto e foi comentado para explicar a função de cada bloco de código.
"""

# backend/app/config.py
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

    # Database
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "projeto"
    POSTGRES_HOST: str = "db"          # <--- necessário no Docker
    POSTGRES_PORT: int = 5432

    DATABASE_URL: Optional[str] = None

    # Selenium
    SELENIUM_MODE: str = "auto"
    SELENIUM_REMOTE_URL: Optional[str] = "http://selenium:4444"
    SELENIUM_HEADLESS: bool = True
    SELENIUM_TIMEOUT: int = 60

    # App specific
    PNCP_DEFAULT_TIMEOUT: int = 2
    PGC_URL: Optional[str] = None

    @property
    def db_url(self) -> str:
        """
        Função db_url:
        Executa a lógica principal definida nesta função.
        """
        """
        Retorna DATABASE_URL do .env, ou monta automaticamente se faltar.
        Isso evita 99% dos erros de conexão no Docker.
        """
        if self.DATABASE_URL:
            return self.DATABASE_URL

        return (
            f"postgresql+psycopg2://"
            f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()
