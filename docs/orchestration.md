# Orquestração e Deploy

## Docker Compose (Desenvolvimento)

### Estrutura do Stack

```yaml
version: '3.9'
services:
  web:
    # FastAPI app
    ports: [8000:8000]
    depends_on: [db, selenium]
    
  db:
    # PostgreSQL 15
    image: postgres:15
    ports: [5432:5432]
    volumes: [postgres_data:/var/lib/postgresql/data]
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=procurement_data
  
  selenium:
    # Chrome Standalone
    image: selenium/standalone-chrome:latest
    ports: [4444:4444, 7900:7900]
    shm_size: 2gb
    environment:
      - SE_VNC_NO_VIEWONLY=1
```

### Iniciar Stack

```bash
# Build e start tudo
docker compose up --build

# Start sem rebuild
docker compose up

# Start em background
docker compose up -d

# Tail logs
docker compose logs -f web

# Stop tudo
docker compose down

# Stop e limpar volumes
docker compose down -v
```

### Verificar Saúde

```bash
# Verificar containers em execução
docker compose ps

# Verificar logs específicos
docker compose logs web
docker compose logs db
docker compose logs selenium

# Health check manual
curl http://localhost:8000/health
```

## Variáveis de Ambiente

### Backend (.env)
```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@db:5432/procurement_data
SQLALCHEMY_ECHO=false

# Selenium
SELENIUM_URL=http://selenium:4444
SELENIUM_HEADLESS=false
SELENIUM_IMPLICIT_WAIT=10
SELENIUM_TIMEOUT=30

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# VBA Compatibility
POLL_TIME=0.1
RETRY_COUNT=3

# Feature Flags
PNCP_REAL_ENABLED=true
PGC_REAL_ENABLED=true

# API
API_PORT=8000
API_HOST=0.0.0.0
```

### Arquivo .env
```bash
# Criar arquivo .env na raiz do projeto
touch .env
# Adicionar variáveis acima
```

## Banco de Dados

### Migrations

Migrations são executadas automaticamente ao iniciar:

```bash
# Manualmente
docker compose exec db psql -U postgres -d procurement_data -f db/migrations/000_init.sql
docker compose exec db psql -U postgres -d procurement_data -f db/migrations/001_triggers.sql
# ... continue para outros migrations
```

### Schema
```sql
-- Tabelas principais
CREATE TABLE coletas (
    id SERIAL PRIMARY KEY,
    fonte VARCHAR(50),          -- "PGC", "PNCP"
    data_coleta TIMESTAMP DEFAULT NOW(),
    ano_referencia INT,
    dados JSONB,                -- Dados flexíveis
    status VARCHAR(20)          -- "success", "error"
);

CREATE TABLE demandas (
    id SERIAL PRIMARY KEY,
    coleta_id INT REFERENCES coletas(id),
    dfd VARCHAR(20),
    descricao TEXT,
    valor NUMERIC(15, 2),
    data_inicio DATE,
    data_fim DATE,
    status VARCHAR(50)
);
```

### Backups

```bash
# Backup do banco
docker compose exec db pg_dump -U postgres procurement_data > backup.sql

# Restaurar
docker compose exec -T db psql -U postgres procurement_data < backup.sql
```

## Logs

### Estrutura de Logs

Todos os logs são estruturados em JSON:

```json
{
  "timestamp": "2025-01-19T10:30:45.123Z",
  "level": "INFO",
  "logger": "backend.app.rpa.pncp_scraper_vba_logic",
  "message": "[LOG-VBA] Coleta iniciada",
  "ano_ref": "2025",
  "portal": "PNCP",
  "total_items": 150
}
```

### Visualizar Logs

```bash
# Logs em tempo real
docker compose logs -f web

# Últimas 100 linhas
docker compose logs --tail=100 web

# Logs de um horário específico
docker compose logs --since 2025-01-19T10:00:00 --until 2025-01-19T11:00:00 web
```

### Agregação de Logs (Futuro)

Integração com ELK Stack ou Splunk:

```yaml
# docker-compose.yml adicional
elasticsearch:
  image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
  
kibana:
  image: docker.elastic.co/kibana/kibana:8.0.0
```

## Monitoramento

### Health Check

```bash
# Verificar saúde da API
curl -s http://localhost:8000/health | jq

# Response esperada
{
  "status": "ok",
  "database": "connected",
  "selenium": "connected",
  "timestamp": "2025-01-19T10:30:45"
}
```

### Métricas (Futuro)

```bash
# Prometheus
curl http://localhost:9090/metrics

# Grafana dashboard
http://localhost:3000
```

## Desenvolvimento Local

### Estrutura de Desenvolvimento

```bash
# Python venv local (alternativa ao Docker)
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate no Windows

# Instalar dependências
pip install -r requirements.txt

# Executar FastAPI localmente
uvicorn backend.app.main:app --reload
```

### Debug com VSCode

Arquivo `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Debugpy",
      "type": "python",
      "request": "attach",
      "connect": {
        "host": "localhost",
        "port": 5678
      },
      "preLaunchTask": "docker-debugpy-attach"
    }
  ]
}
```

Executar:
```bash
DEBUGPY=1 docker compose up
# VSCode irá conectar automaticamente
```

### Desenvolvimento com Reload

```bash
# FastAPI com auto-reload local
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# Selenium standalone separado
docker run -d -p 4444:4444 -p 7900:7900 -e SE_VNC_NO_VIEWONLY=1 -e shm_size=2gb selenium/standalone-chrome
```

## Testes

### Teste Unitário

```bash
# Rodar testes unitários localmente
pytest tests/unit/ -v

# Com cobertura
pytest tests/unit/ --cov=backend --cov-report=html
```

### Teste de Integração

```bash
# Rodar contra DB container
docker compose up db
pytest tests/integration/ -v

# Específico para PNCP
pytest tests/integration/test_pncp_coleta.py -v
```

### Teste E2E

```bash
# Rodar contra stack completo
docker compose up

# Em outro terminal
pytest tests/e2e/ -v

# Pode acompanhar pelo VNC: http://localhost:7900
```

## Deployment em Produção

### Cloud (AWS ECS)

```bash
# Build e push para ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com

docker tag procurement-scraper:latest <account>.dkr.ecr.us-east-1.amazonaws.com/procurement-scraper:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/procurement-scraper:latest

# Deploy via ECS
aws ecs update-service --cluster procurement --service web --force-new-deployment
```

### Kubernetes

```bash
# Criar namespace
kubectl create namespace procurement

# Aplicar configs
kubectl apply -f k8s/postgres.yaml -n procurement
kubectl apply -f k8s/web.yaml -n procurement
kubectl apply -f k8s/selenium.yaml -n procurement

# Escalar pods
kubectl scale deployment web --replicas=3 -n procurement

# Verificar status
kubectl get pods -n procurement
kubectl logs -f deployment/web -n procurement
```

### Nginx Reverse Proxy

```nginx
upstream api {
    server web:8000;
}

server {
    listen 80;
    server_name api.procurement.gov.br;

    location / {
        proxy_pass http://api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req zone=api_limit burst=20;
}
```

### Checklist de Deploy

- [ ] Variáveis de ambiente configuradas
- [ ] Postgres gerenciado (RDS, Cloud SQL, etc)
- [ ] Backups automatizados
- [ ] SSL/TLS certificates
- [ ] Monitoramento ativo
- [ ] Alertas configurados
- [ ] Logs centralizados
- [ ] CDN para assets estáticos
- [ ] Rate limiting ativo
- [ ] Autoscaling policies

## Escalabilidade

### Coletas Paralelas (Futuro)

```python
# Usar Celery para paralelizar coletas
from celery import shared_task

@shared_task
def coleta_pncp_async(ano_ref: str):
    return coleta_pncp("", "", ano_ref)

# Queue de tarefas
celery_app.send_task(
    'coleta_pncp_async',
    args=['2025'],
    queue='coletas'
)
```

### Cache com Redis (Futuro)

```python
# Cache de resultados de coleta
from functools import lru_cache

@lru_cache(maxsize=128)
@cache.cached(timeout=3600, key_prefix='pncp_coleta_{ano}')
def coleta_pncp_cached(ano_ref: str):
    return coleta_pncp(ano_ref)
```

### Load Balancing

```yaml
# Múltiplas instâncias de web
services:
  web-1:
    ports: [8001:8000]
  web-2:
    ports: [8002:8000]
  web-3:
    ports: [8003:8000]
  
  nginx:
    image: nginx:latest
    ports: [80:80]
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on: [web-1, web-2, web-3]
```

## Troubleshooting de Deploy

### Container não inicia
```bash
# Verificar logs
docker compose logs web

# Rebuild sem cache
docker compose build --no-cache web

# Verificar imagem
docker images | grep procurement
```

### Lentidão na coleta
```bash
# Aumentar limites de recursos
docker update --memory 2g container_name

# Paralelizar com Celery
# Ver seção "Coletas Paralelas" acima
```

### Conexão com DB falha
```bash
# Verificar conexão
docker compose exec web python3 -c "
from backend.app.db.engine import get_engine
engine = get_engine()
conn = engine.connect()
print('OK')
"

# Resetar Postgres
docker compose down -v
docker compose up
```

### Erro de permissões em volumes
```bash
# Fixar permissões
docker compose exec db chown -R 999:999 /var/lib/postgresql/data
docker compose restart db
```
