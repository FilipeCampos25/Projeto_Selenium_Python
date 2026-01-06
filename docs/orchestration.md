# Orquestração e Deploy

## Docker Compose
- **Serviços**:
  - `web`: FastAPI app (porta 8000).
  - `db`: PostgreSQL com volume persistente.
  - `selenium`: Chrome standalone para RPA.
- **Comando**: `docker compose up --build` para iniciar tudo.

## Desenvolvimento Local
1. Clonar repo.
2. Configurar `.env` com DATABASE_URL, etc.
3. `docker compose up --build`.
4. Acessar API em http://localhost:8000/docs.
5. Para debug: `SELENIUM_HEADLESS=false` e `DEBUGPY=1`.

## Produção
- Usar Postgres gerenciado.
- Adicionar CI/CD para build e deploy.
- Monitoramento com logs e métricas.

## Configurações
- Variáveis em `backend/.env`.
- Segredos não commitados.
