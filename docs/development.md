# Guia de Desenvolvimento

## Estrutura do Projeto
```
backend/
  app/
    main.py                    # FastAPI app
    config.py                  # Settings via Pydantic
    schemas.py                 # Validação de dados
    api/
      routers/
        pncp.py               # Endpoints PNCP
        pgc.py                # Endpoints PGC
        health.py             # Health check
        pages.py              # Static pages
    rpa/
      pgc_scraper_vba_logic.py      # Scraper PGC
      pncp_scraper_vba_logic.py     # Scraper PNCP
      pgc_xpaths.json               # XPaths PGC
      pncp_xpaths.json              # XPaths PNCP
      waiter_vba.py                 # Wait utilities
      vba_compat.py                 # VBA emulation
      driver_factory.py             # Selenium factory
      *.py                          # Outros módulos
    services/
      pncp_service.py         # PNCP orchestration
      pgc_service.py          # PGC orchestration
      excel_persistence.py    # Excel export
    db/
      repositories.py         # Data access
      migrations/             # SQL migrations
      engine.py               # DB connection
      session.py              # Session manager
    core/
      logging_config.py       # Logging setup
      base_scraper.py         # Base class
frontend/
  templates/
    index.html               # Web UI
tests/
  run_db_tests.sh           # DB tests
docker-compose.yml
requirements.txt
```

## Primeiros Passos

### 1. Instalar Docker
```bash
# Windows (WSL2)
wsl --install
docker --version
```

### 2. Clonar e Navegar
```bash
git clone <repo>
cd projeto_python
```

### 3. Iniciar Stack Docker
```bash
docker compose up --build
```

Isso vai:
- Construir a imagem FastAPI
- Iniciar PostgreSQL com migrations
- Iniciar Chrome Selenium standalone
- Servir API em http://localhost:8000

### 4. Acessar Interface
- **API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **VNC (Browser)**: http://localhost:7900 (senha: secret)

## Workflows Críticos

### Workflow 1: Iniciar Desenvolvimento
```bash
# Build e start tudo
docker compose up --build

# Em outro terminal, tail logs
docker compose logs -f web

# Para quando necessário
docker compose down
```

### Workflow 2: Debug de Scraping
```bash
# Ativar navegador visível e modo debug
docker compose down
SELENIUM_HEADLESS=false DEBUGPY=1 docker compose up --build

# Conectar debugger em VSCode:
# 1. Adicionar breakpoint no código
# 2. VSCode irá conectar automaticamente
# 3. Step through o código
```

### Workflow 3: Adicionar Novo Scraper
1. Criar `novo_scraper_vba_logic.py` em `backend/app/rpa/`
2. Herdar de `BaseScraper` ou criar classe independente
3. Adicionar XPaths em `novo_xpaths.json`:
   ```json
   {
     "login": { "username_field": "//input[@id='user']" },
     "main": { "button_start": "//button[text()='Iniciar']" }
   }
   ```
4. Criar `novo_service.py` em `backend/app/services/`
5. Criar `novo.py` em `backend/app/api/routers/`
6. Registrar router em `main.py`:
   ```python
   from backend.app.api.routers import novo
   app.include_router(novo.router)
   ```

### Workflow 4: Executar Testes de DB
```bash
# Contra Postgres container em execução
cd tests
bash run_db_tests.sh

# Ou manualmente
docker compose exec db psql -U postgres -d procurement_data -f /app/db/migrations/000_init.sql
```

### Workflow 5: Executar Coleta PNCP
```bash
# Via API
curl -X POST http://localhost:8000/api/pncp/iniciar \
  -H "Content-Type: application/json" \
  -d '{"ano_ref": 2025}'

# Via Python programático
docker compose exec web python3 -c "
from backend.app.rpa.pncp_scraper_vba_logic import run_pncp_scraper_vba
dados = run_pncp_scraper_vba('2025')
print(f'Coletados {len(dados)} itens')
"

# Acompanhar pelo VNC
# http://localhost:7900 (password: secret)
```

## Convenções de Código

### VBA Fidelity
Sempre seguir `docs/vba_deep_analysis.md` para replicar exatamente:
- Mesmo número de etapas de login
- Mesmos XPaths (não substituir sem validar)
- Mesmos padrões de espera
- Mesma ordem de extração de campos

### Waits com VBA Timing
```python
from backend.app.rpa.waiter_vba import wait_spinner
from backend.app.rpa.vba_compat import VBACompat

compat = VBACompat(driver)
compat.wait(0.1)  # POLL = 0.1s, equals VBA's TimeValue("00:00:01")/10
wait_spinner(driver, XPATHS["spinner"])
```

### Seletores em JSON
**NUNCA hardcode XPaths!**
```python
# ❌ ERRADO
button = driver.find_element(By.XPATH, "//button[@id='btn123']")

# ✅ CORRETO
with open("pncp_xpaths.json") as f:
    XPATHS = json.load(f)
button = driver.find_element(By.XPATH, XPATHS["tabs"]["reprovadas"])
```

### Persistência com JSONB
```python
# ✅ CORRETO
repo = ColetasRepository()
repo.salvar_bruto(fonte="PNCP", dados=items_list)
repo.consolidar_dados()  # Deduplica e consolida
```

### Logs Estruturados
```python
import logging
logger = logging.getLogger(__name__)

logger.info(f"[LOG-VBA] Coleta iniciada", extra={
    "ano_ref": "2025",
    "portal": "PNCP",
    "total": len(dados)
})
```

### Error Handling Granular
```python
# Emular VBA's "On Error Resume Next" por campo
def get_safe_text(xpath, default=""):
    try:
        return driver.find_element(By.XPATH, xpath).text
    except:
        return default

valor = get_safe_text(XPATHS["fields"]["valor"], "0")
```

## Boas Práticas

### Pre-Commit Hooks
```bash
# Instalar hooks
pip install pre-commit
pre-commit install

# Hooks irão executar automaticamente:
# - black (formatting)
# - flake8 (linting)
# - mypy (type checking)
```

### Type Checking
```bash
# Rodar mypy manualmente
mypy backend/app --strict
```

### Linting
```bash
# Rodar flake8
flake8 backend/app --max-line-length=120
```

### Formatting
```bash
# Formatar código com black
black backend/app
```

## Testes

### Teste Unitário
```python
# backend/tests/test_vba_compat.py
import pytest
from backend.app.rpa.vba_compat import parse_vba_cdbl

def test_parse_vba_cdbl():
    assert parse_vba_cdbl("1.234,56") == 1234.56
    assert parse_vba_cdbl("") == 0.0
```

### Teste de Integração
```bash
# Contra DB efêmero
docker compose exec db python3 -m pytest tests/ -v
```

### Teste E2E
```bash
# Contra Selenium em container
docker compose exec web pytest tests/e2e/ -v
```

## Troubleshooting

### Erro: "Connection refused"
```bash
# Verificar se containers estão rodando
docker compose ps

# Reiniciar stack
docker compose restart
```

### Erro: "XPath not found"
1. Verificar se XPath em JSON está correto
2. Abrir VNC (http://localhost:7900) e inspect element
3. Atualizar XPath em JSON
4. Reexecutar coleta

### Erro: "Timeout waiting for element"
1. Aumentar timeout em config.py
2. Adicionar logs para ver onde está travando
3. Verificar se página carregou corretamente
4. Usar VNC para debug visual

### Erro: "Database connection failed"
```bash
# Verificar Postgres
docker compose logs db

# Verificar migrations rodaram
docker compose exec db psql -U postgres -c "\dt"

# Recriar DB do zero
docker compose down -v
docker compose up
```

### Performance Lenta
1. Desativar headless: `SELENIUM_HEADLESS=false`
2. Aumentar POLL_TIME em waiter_vba.py
3. Paralelizar coletas com Celery (future)
4. Usar Redis para cache (future)

## Documentação

Após fazer mudanças públicas:
1. Atualizar docstrings
2. Atualizar arquivo relevante em `docs/`
3. Atualizar README.md se mudança é significativa
4. Commitar documentação junto com código

## Deployment

### Produção Local
```bash
# Build otimizado
docker compose -f docker-compose.prod.yml up -d

# Checklist:
# - Environment variables configurados
# - Volume de dados criado
# - Backups de DB agendados
# - Logs centralizados (ELK, Splunk, etc)
```

### Cloud (AWS, GCP, Azure)
- Usar Kubernetes ou ECS
- Postgres gerenciado (RDS, Cloud SQL, etc)
- Upload de logs para CloudWatch/Stackdriver
- Monitoramento com alertas
