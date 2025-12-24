# AI Coding Agent Instructions

## Project Overview
This is a Python adaptation of a VBA system for scraping Brazilian government procurement data (PGC/PNCP portals). The system uses Selenium for web automation, FastAPI for API orchestration, and PostgreSQL for data persistence. Key focus: **exact replication of VBA business logic** while modernizing to modular Python architecture.

## Architecture & Data Flow
- **Scrapers** (`backend/app/rpa/`): Modular Selenium-based extractors (e.g., `pgc_scraper_vba_logic.py`) that navigate portals and return structured JSON.
- **API Layer** (`backend/app/api/routers/`): FastAPI endpoints for triggering scrapes, health checks, and serving static pages.
- **Persistence** (`backend/app/db/`): SQLAlchemy repositories storing JSONB data in PostgreSQL with manual SQL migrations.
- **Infrastructure**: Docker-compose with web (FastAPI), db (Postgres), and selenium (Chrome) services.

Data flows: API → Scraper → JSON validation → DB storage → Query endpoints.

## Critical Developer Workflows
- **Start development**: `docker compose up --build` (builds containers, runs migrations, starts services).
- **Local dev**: `uvicorn --reload backend.app.main:app` with local Selenium if needed.
- **Debug scraping**: Use `SELENIUM_HEADLESS=false` to see browser; attach debugger via `DEBUGPY=1`.
- **Test DB**: Run `tests/run_db_tests.sh` against running Postgres container.
- **Add scraper**: Create module in `rpa/`, add XPaths to JSON file, integrate via service layer.

## Project-Specific Conventions
- **VBA Fidelity**: Replicate exact VBA logic, XPaths, and wait patterns. Reference `docs/vba_deep_analysis.md` for original behavior.
- **Wait Patterns**: Use `waiter_vba.py` functions with `POLL=0.1` (matches VBA's `TimeValue("00:00:01")/10`). Example: `wait_spinner(driver, XPATHS["spinner"])`.
- **Selectors**: Store all XPaths in JSON files (e.g., `pgc_xpaths.json`). Never hardcode selectors in code.
- **Data Storage**: Use JSONB columns for flexible schemas. Example: `salvar_pncp(session, {"records": [...], "metadata": {...}})` in repositories.
- **Error Handling**: Fail fast with descriptive logs; avoid swallowing exceptions. Use structured logging with `logger.info/json.dumps(data)`.
- **Configuration**: Load from Pydantic settings in `config.py`; override via `backend/.env`.

## Integration Points
- **Selenium**: Remote Chrome via `http://selenium:4444` in Docker; local driver for dev.
- **Database**: Auto-generated `DATABASE_URL` from Postgres env vars; use `get_engine()` for connections.
- **External APIs**: None; all data from web scraping government portals.
- **File Outputs**: JSON/CSV exports from DB queries; no direct file writes in scrapers.

## Key Files & Examples
- **Main scraper logic**: [backend/app/rpa/pgc_scraper_vba_logic.py](backend/app/rpa/pgc_scraper_vba_logic.py) - Exact VBA replication with login flow and pagination.
- **Wait utilities**: [backend/app/rpa/waiter_vba.py](backend/app/rpa/waiter_vba.py) - Spinner waits matching VBA timing.
- **XPaths config**: [backend/app/rpa/pgc_xpaths.json](backend/app/rpa/pgc_xpaths.json) - Centralized selectors.
- **DB operations**: [backend/app/db/repositories.py](backend/app/db/repositories.py) - JSONB inserts with transactions.
- **API router**: [backend/app/api/routers/pncp.py](backend/app/api/routers/pncp.py) - Orchestrates scrapes and returns results.

When modifying scrapers, always cross-reference with `docs/vba_analysis.md` and `MUDANCAS_VBA_TO_PYTHON.md` to maintain fidelity.</content>
<parameter name="filePath">c:\Users\filipe.duarte\Desktop\projeto_adaptado\.github\copilot-instructions.md