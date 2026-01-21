#!/usr/bin/env python3
"""
Wrapper para executar a aplicação LOCAL
Carrega as variáveis de ambiente antes de qualquer import
"""

import os
import sys
from pathlib import Path

# Carregar .env.local se existir
env_local = Path(".env.local")
if env_local.exists():
    print(f"[INFO] Carregando configuracoes de: {env_local.absolute()}")
    from dotenv import load_dotenv
    load_dotenv(env_local)
else:
    print(f"[WARN] .env.local nao encontrado, usando .env padrao")
    from dotenv import load_dotenv
    load_dotenv(".env")

# Agora é seguro importar o resto da aplicação
import uvicorn
from backend.app.main import app
from backend.app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", settings.PORT)),
        reload=False,
        log_level="info"
    )
