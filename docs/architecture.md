# Arquitetura do Sistema

## Visão Geral
Este projeto é uma adaptação Python de um sistema VBA para scraping de dados de compras públicas brasileiras. Suporta coleta de dois portais governamentais:

- **PGC (Portal Comprasnet)** - Planejamento e Gerenciamento de Contratações
- **PNCP (Portal Nacional de Contratações Públicas)** - Demandas por aba

Utiliza Selenium para automação web, FastAPI para API de orquestração, PostgreSQL para persistência de dados e Docker para conteinerização. O foco é replicar exatamente a lógica VBA original enquanto moderniza para uma arquitetura modular e escalável.

## Componentes Principais

### Layer 1: Scrapers RPA (Camada de Automação)
- **Localização**: `backend/app/rpa/`
- **Responsabilidades**: Navegação automatizada nos portais governamentais usando Selenium Chrome.
- **Módulos principais**:
  - `pgc_scraper_vba_logic.py`: Replica exatamente a lógica VBA para scraping do PGC (9 etapas de login, paginação descoberta, extração de DFDs).
  - `pncp_scraper_vba_logic.py`: Implementação completa do PNCP com suporte a 3 abas (Reprovadas, Aprovadas, Pendentes), coleta dinâmica de itens, logs de auditoria.
  - `pncp_downloader.py`, `pncp_table.py`, `pncp_item.py`: Utilitários auxiliares para PNCP.
  - `waiter_vba.py`: Funções de espera que replicam timing do VBA (POLL=0.1).
  - `vba_compat.py`: Emulação de funções VBA (CDbl, CDate, Format, etc).
  - `driver_factory.py`: Fábrica moderna de drivers Selenium.
  - `chromedriver_manager.py`: Gerenciamento automático de ChromeDriver.
  - `context_manager.py`: Gestão de contextos de navegação.
  - `semantic_waiter.py`: Esperas semânticas avançadas.
  - `dfd_ocr.py`: Processamento OCR para DFDs (quando necessário).

- **Configurações**: 
  - XPaths centralizados em JSON: `pgc_xpaths.json`, `pncp_xpaths.json`
  - VBA config: `config_vba.py`, `vba_compat_config.py`
  
- **Saída**: JSON estruturado com dados validados via Pydantic schemas.

### Layer 2: Serviços (Camada de Orquestração)
- **Localização**: `backend/app/services/`
- **Módulos**:
  - `pncp_service.py`: Orquestração de coleta PNCP, persistência em DB e Excel, logs estruturados.
  - `pgc_service.py`: Orquestração de coleta PGC.
  - `excel_persistence.py`: Persistência em arquivos Excel.
  
- **Função**: Camada intermediária que:
  - Invoca scrapers com parâmetros validados
  - Trata erros granulares
  - Persiste resultados em Postgres e Excel
  - Emite logs de auditoria

### Layer 3: API REST (FastAPI)
- **Localização**: `backend/app/api/routers/`
- **Routers**:
  - `pncp.py`: Endpoints para iniciar scrapes PNCP (POST /api/pncp/iniciar)
  - `pgc.py`: Endpoints para PGC (POST /api/pgc/iniciar)
  - `health.py`: Verificação de saúde do sistema
  - `pages.py`: Servir páginas estáticas HTML

- **Características**:
  - Background tasks para coletas assíncronas
  - Validação de schemas Pydantic
  - Tratamento de exceções com HTTP status codes
  - Logs estruturados em JSON

### Layer 4: Persistência (PostgreSQL)
- **Banco**: PostgreSQL conteinerizado com volume persistente.
- **Modelos**: SQLAlchemy com JSONB para dados flexíveis.
- **Repositórios**: `backend/app/db/repositories.py`
  - `salvar_bruto()`: Armazena dados brutos de coletas
  - `consolidar_dados()`: Consolida e deduplica registros
  - Suporte a queries customizadas
  
- **Migrações**: Scripts SQL manuais em `db/migrations/`
  - `000_init.sql`: Schema base (coletas, demandas)
  - `001_triggers.sql`: Triggers para auditoria
  - `002_views.sql`: Views para consultas
  - `003_test_data.sql`: Dados de teste
  - `004_coletas.sql`: Tabelas de rastreamento
  - `005_upsert_pgc.sql`: Lógica de upsert PGC

### Layer 5: Core Utilities
- **Localização**: `backend/app/core/`
- **base_scraper.py**: Classe base para todos os scrapers
- **logging_config.py**: Configuração de logs estruturados

### Infraestrutura e Configuração
- **Docker Compose**: Stack conteinerizado com serviços:
  - `web`: FastAPI app (porta 8000)
  - `db`: PostgreSQL 15 (porta 5432)
  - `selenium`: Chrome standalone (porta 4444)
  
- **Configuração**: 
  - `backend/config.py`: Settings via Pydantic (DATABASE_URL, SELENIUM_URL, etc)
  - `.env`: Variáveis de ambiente (não commitadas) - na raiz do projeto
  - `docker-compose.yml`: Orquestração de containers

## Fluxo de Dados - PGC

```
Usuário/API
    ↓
POST /api/pgc/iniciar (ano_ref=2025)
    ↓
pgc_service.coleta_pgc()
    ↓
PGCScraperVBA(driver)
    ↓
├─ A_Loga_Acessa_PGC() [9 etapas de login]
├─ Descobre_Total_Paginas()
├─ Extrai_Por_Pagina() [para cada página]
│  ├─ Extrai_Tabela()
│  └─ Lê_DFD() [opcional, pode ir mais fundo]
└─ Retorna JSON[] validado
    ↓
ColetasRepository.salvar_bruto(fonte="PGC", dados=[...])
    ↓
PostgreSQL (JSONB) + Excel (.xlsx)
```

## Fluxo de Dados - PNCP

```
Usuário/API
    ↓
POST /api/pncp/iniciar (ano_ref=2025)
    ↓
pncp_service.coleta_pncp()
    ↓
PNCPScraperVBA(driver, ano_ref)
    ↓
├─ Dados_PNCP() [entrypoint]
├─ _preparar_navegação_inicial() [sync + click]
├─ _selecionar_ano_pca() [dropdown]
├─ _coletar_aba("reprovadas", "REPROVADA")
│  ├─ _obter_total_demandas() [descobre total]
│  ├─ _executar_rolagem_tabela() [carrega itens]
│  └─ _extrair_itens_tabela() [coleta campos]
├─ _coletar_aba("aprovadas", "APROVADA")
└─ _coletar_aba("pendentes", "PENDENTE")
    ↓
Retorna JSON[] validado (9 campos por item)
    ↓
ColetasRepository.salvar_bruto(fonte="PNCP", dados=[...])
    ↓
PostgreSQL (JSONB) + Excel (.xlsx)
```

## Tratamentos VBA Emulados

### Conversão de Tipos
- **CDbl()**: Converte strings monetárias para float
- **CDate()**: Converte DD/MM/YYYY para ISO date
- **Format()**: Formata números e datas
- **Left()**, **Right()**: Manipulação de strings

### Controle de Fluxo
- **On Error Resume Next**: Granulação por campo com try/except
- **Waits**: Spinners, timeouts, retry logic
- **Sincronização**: Esperas inteligentes com POLL=0.1s

## Segurança e Configuração

- **Credenciais**: Via variáveis de ambiente, não commitadas
- **Isolamento**: Selenium em container separado
- **Logs**: Estruturados em JSON com níveis (INFO, WARNING, ERROR)
- **Validação**: Schemas Pydantic em todas as camadas
- **Auditoria**: Logs de todos os passos críticos

## Extensibilidade

- **Novos Scrapers**: Criar módulo em `rpa/`, herdar de `BaseScraper`, adicionar XPaths em JSON
- **Novos Endpoints**: Criar router em `api/routers/`, invocar service
- **Novos Serviços**: Criar em `services/`, seguir padrão de erro e log
- **Escalabilidade**: Possibilidade de adicionar filas (Celery) para scrapes paralelos
- **Monitoramento**: Integração com ELK stack ou similar via logs estruturados
