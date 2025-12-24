# Arquitetura — projeto_refatorado_final

## Visão geral
Este documento descreve a arquitetura de alto nível para a plataforma de raspagem refatorada (baseada no código fornecido). O sistema extrai conjuntos de dados de compras públicas (PGC, PNCP, PTA, etc.) de portais públicos usando Selenium, valida e transforma os resultados em serviços Python e persiste em PostgreSQL via SQLAlchemy. A API de orquestração e acesso é implementada com FastAPI. Os serviços são conteinerizados com Docker e orquestrados com docker-compose.

## Componentes
- **Serviço RPA / Scraper**
  - Local: `backend/app/rpa` (por exemplo `pncp_scraper`).
  - Executa Selenium (Chrome) para navegação e extração.
  - Responsabilidades: navegar, extrair, validação inicial e retorno de JSON estruturado.

- **API / Orquestração (FastAPI)**
  - Local: `backend/app`.
  - Routers observados: `pncp`, `pages`, `health`.
  - Expõe endpoints para acionar scrapes, checar saúde e servir assets estáticos do frontend.
  - Orquestra execução dos scrapers e delega persistência ao repositório de dados.

- **Camada de Persistência**
  - Banco de dados PostgreSQL (containerizado).
  - Modelos e repositórios SQLAlchemy em `backend/app/db`.
  - Tabela principal observada: `coletas` (armazena JSON bruto/normalizado, metadados, timestamps).
  - Migrações como arquivos SQL em `db/migrations/`.

- **Execução de Jobs / Workers**
  - Jobs de scraping são, por enquanto, de curta duração e podem ser executados de forma síncrona via API.
  - O `docker-compose` inclui um serviço `selenium` (standalone-chrome) para sessões remotas de navegador.

- **Frontend**
  - Templates estáticos servidos pelo router `pages` do FastAPI.
  - Interface mínima para checar status e acionar scrapes manualmente.

- **Infraestrutura**
  - `Dockerfile` para construir a imagem do app (base `python:3.11-slim`).
  - `docker-compose.yml` definindo serviços `web`, `db` e `selenium`.

## Fluxo de dados
1. Usuário ou scheduler aciona endpoint de scrape no FastAPI.
2. FastAPI invoca o scraper.
3. Scraper retorna JSON estruturado (registros + metadados).
4. Serviço valida/normaliza os dados e grava no Postgres via repositório.
5. Resultados ficam acessíveis via endpoints adicionais ou exportáveis.

## Segurança & Rede
- Conexão com DB via variável de ambiente `DATABASE_URL`; em Compose, use a rede interna do Docker.
- Limitar exposição do Selenium: somente o serviço app deve se conectar ao container Selenium.
- Segredos devem ser fornecidos via variáveis de ambiente ou secret manager (não commitar em repositórios).

## Extensibilidade
- Adicionar scrapers como plugins modulares (um módulo por portal alvo).
- Substituir chamadas síncronas por fila de tarefas (Celery/RQ) para escalabilidade.

## Limitações conhecidas (baseadas no código)
- Tratamento genérico de erros nos routers que pode mascarar causas reais.
- Falta de testes automatizados e tipagem incompleta.
- Migrações gerenciadas como SQL estático (considerar Alembic para melhorar).
