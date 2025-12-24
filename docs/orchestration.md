# Orquestração & Deploy

## Docker Compose (recomendado)
- Serviços sugeridos:
  - `web`: aplicação FastAPI (imagem construída a partir do Dockerfile).
  - `db`: Postgres (volume persistente ou volume do Docker Desktop).
  - `selenium`: Selenium standalone-chrome para jobs RPA.
- Otimizações:
  - Usar `depends_on` entre serviços; adicionar `healthcheck` para `db` e só iniciar `web` quando o DB estiver pronto.
  - Montar código fonte no container `web` em desenvolvimento (bind mount).

## Recomendações para Dockerfile
- Base: `python:3.11-slim`.
- Instalar dependências mínimas para compilação de pacotes se necessário.
- Criar usuário não-root no container.
- Usar multi-stage builds se empacotar assets do frontend.
- Fixar versões das dependências (`requirements.txt` ou `poetry.lock`).

## Executando localmente (dev)
1. Subir o compose: `docker compose up --build`.
2. Acessar docs do FastAPI: `http://localhost:8000/docs`.
3. Acionar scrapes via API ou UI; inspecionar registros no banco com psql ou cliente DB.

## Produção
- Preferir Postgres gerenciado (RDS/Cloud SQL) ou Postgres auto-hospedado com hardening.
- Substituir container Selenium por infraestrutura de browser headless escalável conforme necessário.
- Introduzir fila de tarefas para agendamento/concorrência e auto-scaling.
- CI/CD para build, testes e deploy.

## Backups & Migrações
- Usar Alembic para migrações versionadas.
- Rotina de backups regulares (pg_dump) e testes de restore.

## Segredos & Configurações
- Não armazenar segredos em arquivos do compose.
- Utilizar secret manager ou variáveis de ambiente; registrar política de rotação.
- Centralizar logs e métricas (ELK, Prometheus + Grafana, etc.).
