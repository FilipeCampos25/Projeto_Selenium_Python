# Arquitetura do Sistema

## Visão Geral
Este projeto é uma adaptação Python de um sistema VBA para scraping de dados de compras públicas brasileiras (portais PGC e PNCP). Utiliza Selenium para automação web, FastAPI para API de orquestração, PostgreSQL para persistência de dados e Docker para conteinerização. O foco é replicar exatamente a lógica VBA original enquanto moderniza para uma arquitetura modular.

## Componentes Principais

### Scrapers RPA
- **Localização**: `backend/app/rpa/`
- **Responsabilidades**: Navegação automatizada nos portais governamentais usando Selenium Chrome.
- **Módulos principais**:
  - `pgc_scraper_vba_logic.py`: Replica a lógica VBA para scraping do PGC.
  - `pncp_scraper.py`, `pncp_downloader.py`, etc.: Para PNCP.
- **Configurações**: XPaths armazenados em JSON (e.g., `pgc_xpaths.json`).
- **Saída**: JSON estruturado com dados extraídos e metadados.

### API de Orquestração (FastAPI)
- **Localização**: `backend/app/api/routers/`
- **Routers**:
  - `pncp.py`: Endpoints para iniciar scrapes PNCP.
  - `pgc.py`: Para PGC.
  - `health.py`: Verificação de saúde.
  - `pages.py`: Servir páginas estáticas.
- **Função**: Recebe solicitações HTTP, aciona scrapers e persiste resultados.

### Camada de Persistência
- **Banco**: PostgreSQL conteinerizado.
- **Modelos**: SQLAlchemy com JSONB para dados flexíveis.
- **Repositórios**: `backend/app/db/repositories.py` - Funções como `salvar_pncp()` para inserir dados.
- **Migrações**: Scripts SQL manuais em `db/migrations/`.

### Serviços
- **Localização**: `backend/app/services/`
- **Função**: Camada intermediária entre API e scrapers, aplicando lógica de negócio.

### Infraestrutura
- **Docker Compose**: Serviços `web` (FastAPI), `db` (Postgres), `selenium` (Chrome standalone).
- **Configuração**: Pydantic settings em `config.py`, variáveis de ambiente.

## Fluxo de Dados
1. Usuário aciona endpoint via API (e.g., POST /api/pncp/iniciar).
2. FastAPI chama serviço, que invoca scraper.
3. Scraper usa Selenium para navegar, extrair dados e retornar JSON.
4. Dados são validados e salvos no Postgres via repositório.
5. Resultados acessíveis via queries ou exports.

## Segurança e Configuração
- Credenciais via variáveis de ambiente.
- Selenium isolado em container próprio.
- Logs estruturados com JSON.

## Extensibilidade
- Novos scrapers como módulos em `rpa/`.
- Possibilidade de adicionar filas (Celery) para scrapes assíncronos.
