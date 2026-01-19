# Guia de Desenvolvimento

## Estrutura do Projeto
```
backend/
  app/
    main.py
    config.py
    api/routers/ (pncp.py, pgc.py, etc.)
    rpa/ (scrapers, xpaths.json)
    db/ (repositories.py, migrations/)
    services/
frontend/templates/
docker-compose.yml
docs/
```

## Primeiros Passos
1. Instalar Docker.
2. `docker compose up --build`.
3. Acessar http://localhost:8000.

## Workflows Críticos
- **Iniciar dev**: `docker compose up --build`.
- **Debug scraping**: `SELENIUM_HEADLESS=false`.
- **Adicionar scraper**: Criar módulo em `rpa/`, XPaths em JSON, integrar via service.
- **Testes**: `tests/run_db_tests.sh` contra Postgres container.

## Convenções
- **VBA Fidelity**: Seguir `docs/vba_deep_analysis.md` para lógica exata.
- **Waits**: Usar `waiter_vba.py` com POLL=0.1.
- **Selectors**: Em JSON files, não hardcoded.
- **Data Storage**: JSONB em Postgres.
- **Logs**: Estruturados com json.dumps.

## Boas Práticas
- Hooks pre-commit: black, flake8.
- Testes para mudanças.
- Atualizar docs para mudanças públicas.
