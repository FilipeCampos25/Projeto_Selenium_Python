# Guia de Desenvolvimento

## Estrutura do repositório (base no projeto analisado)
```
backend/
  app/
    main.py
    routers/
      pncp.py
      pages.py
      health.py
    rpa/
      pncp_scraper.py
    db/
      session.py
      repositories.py
      migrations/
    services/
    docs/
  Dockerfile
docker-compose.yml
```

## Primeiros passos (desenvolvimento)
1. Instale Docker & Docker Desktop (usar Postgres via Docker Desktop).
2. Coloque variáveis de ambiente em `.env` (ex.: DATABASE_URL).
3. Inicie os serviços:
   ```
   docker compose up --build
   ```
4. Acesse `http://localhost:8000/docs` para a documentação interativa da API.

## Dicas de desenvolvimento local
- Use `uvicorn --reload backend.app.main:app` para hot-reload em desenvolvimento.
- Se precisar debugar com um navegador local, encaminhe portas do Selenium ou use browser local.

## Testes
- Adicionar `pytest` e configurar:
  - `tests/unit/` para scrapers e utilitários.
  - `tests/integration/` para interações com DB (Postgres efêmero).
- Fixtures: gravar amostras de páginas para testes determinísticos.
- Cobertura mínima: cobrir caminhos críticos antes de grandes refatorações.

## Boas práticas de código
- Hooks pre-commit (black, isort, flake8).
- Tipagem estática com mypy como etapa de CI.
- Documentar mudanças públicas em `docs/`.

- **Persistir um resultado de scrape:**
  Use `salvar_pncp(session, data)` em `backend/app/db/repositories.py`.

## Checklist antes de PR
- Adicionar/atualizar testes relevantes.
- Incluir migrações para quaisquer mudanças de esquema.
- Atualizar documentação (`docs/`) sobre endpoints públicos.


**Nota:** O uso de MOCKs está proibido neste projeto — execução deve usar Selenium (standalone/container) ou driver local.
