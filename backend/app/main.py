"""
FastAPI main app — VERSÃO ADAPTADA PARA EXECUÇÃO LOCAL
"""

import os
from pathlib import Path
import logging
import time
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from backend.app.config import settings
from backend.app.api.routers import health, pages
from backend.app.api.routers.pncp import router as pncp_router_refactored
from backend.app.api.routers.pgc import router as pgc_router
from backend.app.api.routers.coleta_unificada import router as coleta_unificada_router
from backend.app.core.logging_config import setup_logging

# ============================================================
# 🔴 INÍCIO MODIFICAÇÃO LOCAL - REMOVER QUANDO VOLTAR DOCKER
# ============================================================

# NÃO IMPORTAR ColetasRepository (requer Postgres)
# from backend.app.db.repositories import ColetasRepository

# ============================================================
# 🔴 FIM MODIFICAÇÃO LOCAL
# ============================================================

# ============================================================
# PATHS ABSOLUTOS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"

if not TEMPLATES_DIR.exists():
    fallback_dir = BASE_DIR.parent.parent / "frontend" / "templates"
    if fallback_dir.exists():
        TEMPLATES_DIR = fallback_dir
    else:
        os.makedirs(TEMPLATES_DIR, exist_ok=True)

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# ============================================================
# LOGGING
# ============================================================

setup_logging()
logger = logging.getLogger(__name__)

# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="Sistema de Coleta PGC/PNCP - MODO LOCAL",
    version="2.0.0-LOCAL",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ============================================================
# MIDDLEWARE
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    logger.info(f"→ {request.method} {request.url.path}")
    response = await call_next(request)
    duration = (time.time() - start) * 1000
    logger.info(f"← {request.method} {request.url.path} [{response.status_code}] {duration:.2f}ms")
    return response

# ============================================================
# EXCEPTION HANDLER
# ============================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Erro não tratado")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Erro interno do servidor",
            "error": str(exc),
            "path": request.url.path
        }
    )

# ============================================================
# ROUTERS
# ============================================================

pages.templates = templates
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(pages.router, tags=["pages"])
app.include_router(pncp_router_refactored)
app.include_router(pgc_router)
app.include_router(coleta_unificada_router)

# ============================================================
# EVENTS
# ============================================================

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 70)
    logger.info("🚀 Sistema de Coleta PGC/PNCP INICIADO - MODO LOCAL")
    
    # ============================================================
    # 🔴 INÍCIO MODIFICAÇÃO LOCAL - REMOVER QUANDO VOLTAR DOCKER
    # ============================================================
    
    logger.warning("⚠️  MODO LOCAL ATIVO")
    logger.warning("⚠️  Postgres DESABILITADO")
    logger.warning("⚠️  Dados salvos apenas em Excel e JSON temporário")
    logger.warning("⚠️  Selenium usando Chrome LOCAL da máquina")
    
    # NÃO INICIALIZAR BANCO DE DADOS
    # try:
    #     logger.info("Verificando banco de dados...")
    #     repo = ColetasRepository()
    #     logger.info("Banco de dados OK.")
    # except Exception as e:
    #     logger.error(f"Erro ao inicializar banco: {e}")
    
    # ============================================================
    # 🔴 FIM MODIFICAÇÃO LOCAL
    # ============================================================
        
    logger.info("=" * 70)

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Sistema desligando - MODO LOCAL")

# ============================================================
# ROOT
# ============================================================

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/pgc")

if __name__ == "__main__":
    # ============================================================
    # 🔴 INÍCIO MODIFICAÇÃO LOCAL
    # ============================================================
    
    logger.info("=" * 70)
    logger.info("INSTRUÇÕES PARA EXECUÇÃO LOCAL:")
    logger.info("1. Certifique-se que o Google Chrome está instalado")
    logger.info("2. Certifique-se que o ChromeDriver está no PATH")
    logger.info("3. Execute: python -m backend.app.main")
    logger.info("4. Acesse: http://localhost:8000")
    logger.info("5. Os arquivos Excel serão salvos em: ./outputs_local/")
    logger.info("=" * 70)
    
    # ============================================================
    # 🔴 FIM MODIFICAÇÃO LOCAL
    # ============================================================
    
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", settings.PORT)),
        reload=False,  # Modo local sem reload para evitar problemas
        log_level="info"
    )