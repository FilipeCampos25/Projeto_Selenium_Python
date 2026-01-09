"""
FastAPI main app — VERSÃO FINAL CORRIGIDA
"""

# ============================================================
# DEBUGPY — PRIMEIRA COISA A EXECUTAR
# ============================================================

import os
from pathlib import Path


# ============================================================
# IMPORTS DA APLICAÇÃO
# ============================================================

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

import logging
import time
import uvicorn

from backend.app.config import settings
from backend.app.api.routers import health, pages
from backend.app.api.routers.pncp import router as pncp_router_refactored
from backend.app.api.routers.pgc import router as pgc_router
from backend.app.core.logging_config import setup_logging
from backend.app.db.repositories import ColetasRepository

# ============================================================
# PATHS ABSOLUTOS (CRÍTICO PARA DOCKER)
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"

if not TEMPLATES_DIR.exists():
    # Fallback para o layout atual do projeto (templates em /frontend)
    fallback_dir = BASE_DIR.parent.parent / "frontend" / "templates"
    if fallback_dir.exists():
        TEMPLATES_DIR = fallback_dir
    else:
        raise RuntimeError(
            f"Diretório de templates NÃO encontrado: {TEMPLATES_DIR}"
        )
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
    title="Sistema de Coleta PGC/PNCP",
    version="2.0.0",
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
    logger.info(
        f"← {request.method} {request.url.path} "
        f"[{response.status_code}] {duration:.2f}ms"
    )
    return response

# ============================================================
# EXCEPTION HANDLER GLOBAL
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

# 🔥 INJEÇÃO EXPLÍCITA DOS TEMPLATES NO ROUTER DE PÁGINAS
pages.templates = templates

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(pages.router, tags=["pages"])
app.include_router(pncp_router_refactored)
app.include_router(pgc_router)

# ============================================================
# EVENTS
# ============================================================

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 70)
    logger.info("🚀 Sistema de Coleta PGC/PNCP INICIADO")
    logger.info(f"📁 Templates: {TEMPLATES_DIR}")
    
    # Inicialização do Banco de Dados
    try:
        logger.info("🗄️ Inicializando tabelas do banco de dados...")
        repo = ColetasRepository()
        logger.info("✅ Banco de dados inicializado com sucesso.")
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar banco de dados: {e}")
        
    logger.info("=" * 70)

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Sistema desligando")

# ============================================================
# ROOT GLOBAL
# ============================================================

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/pgc")

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", settings.PORT)),
        reload=False,
        log_level="info"
    )
