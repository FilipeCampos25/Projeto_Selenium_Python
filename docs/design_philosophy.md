# Filosofia de Design

## Objetivos Principais

### 1. Fidelidade ao VBA
- Replicar **exatamente** a lógica, XPaths e padrões de espera do código VBA original para garantir compatibilidade 100%
- Manter os mesmos algoritmos de navegação, paginação e extração de dados
- Documentar todas as diferenças comportamentais entre VBA e Python

### 2. Confiabilidade
- Scrapes previsíveis com tratamento robusto de erros
- Waits adequados e sincronização com elementos da página
- Logs estruturados para auditoria e debugging

### 3. Manutenibilidade
- Código modular com separação clara de responsabilidades
- Cada scraper é um módulo independente
- Configurações externalizadas (XPaths em JSON, settings em Pydantic)
- Documentação inline e externa
- Type hints em todo o código Python

### 4. Observabilidade
- Logs estruturados em JSON para análise
- Diferentes níveis (DEBUG, INFO, WARNING, ERROR)
- Logs de auditoria detalhando cada etapa do scraping

### 5. Reprodutibilidade
- Ambientes conteinerizados para consistência entre dev e prod
- Docker Compose com volumes persistentes
- Testes contra dados de teste conhecidos

## Princípios de Design

### 1. Responsabilidade Única
- Cada scraper trata um portal específico
- Cada service orquestra uma coleta completa
- Cada repositório gerencia uma fonte de dados
- Cada router expõe um conjunto de endpoints relacionados

### 2. Separação de Camadas
- **RPA Layer**: Automação web pura (Selenium)
- **Service Layer**: Orquestração, persistência, logs
- **API Layer**: Endpoints HTTP, validação, background tasks
- **DB Layer**: Persistência, queries, migrations
- **Core Layer**: Utilitários compartilhados

### 3. Fail Fast
- Erros são expostos claramente ao usuário
- Evitar exceções silenciosas ("swallow exceptions")
- Logs detalhados em caso de erro
- Stack traces completos para debugging

### 4. Configuração Externa
- XPaths em arquivos JSON centralizados (não hardcoded)
- Timeouts e polls em constantes
- Credenciais via variáveis de ambiente
- Feature flags para controlar comportamento

### 5. Idempotência
- Persistência evita duplicatas via chaves únicas
- Upserts em vez de inserts puros
- Possibilidade de reexecutar coletas sem efeitos colaterais

### 6. Testabilidade
- Lógica isolável para testes unitários
- Mocks de Selenium para testes sem navegador
- Testes de integração com DB efêmero
- Testes E2E com Selenium em container

## Padrões de Código

### Type Hints
Todas as funções têm type hints:
```python
def coleta_pncp(ano_ref: str = "2025") -> Dict[str, Any]:
    ...
```

### Exceções Customizadas
Exceções de domínio para diferentes erros:
```python
class PNCPCollectionError(Exception):
    """Erro durante coleta PNCP"""
    pass

class XPathNotFoundError(Exception):
    """XPath não encontrado na página"""
    pass
```

### Injeção de Dependências
FastAPI `Depends()` para injetar serviços:
```python
@router.post("/iniciar")
async def iniciar_coleta(request: PNCPRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(coleta_pncp, str(request.ano_ref))
```

### Logging Estruturado
Logs com contexto e dados estruturados:
```python
logger.info(f"[LOG-VBA] Coleta iniciada", extra={
    "ano_ref": "2025",
    "portal": "PNCP",
    "total_itens": len(dados)
})
```

### Validação com Pydantic
Schemas para validação:
```python
class PNCPItemSchema(BaseModel):
    col_a_contratacao: str
    col_d_valor: float
    col_e_inicio: Optional[str]
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat()
        }
```

## Estratégia de Testes

### Unitários
- Testes para funções utilitárias (conversões, formatações)
- Testes sem necessidade de Selenium
- Rápidos e isolados

### Integração
- Testes com DB efêmero (PostgreSQL em container)
- Testes de repositórios e queries
- Testes de schemas e validação

### E2E
- Testes com Selenium em container
- Contra ambientes de teste conhecidos
- Validam fluxo completo de coleta

## Tratamentos VBA Emulados

### Conversão de Tipos
Emulamos as funções VBA de conversão em Python:

| VBA | Python | Propósito |
|-----|--------|-----------|
| `CDbl("1.234,56")` | `parse_vba_cdbl("1.234,56")` → `1234.56` | Valores monetários |
| `CDate("01/02/2025")` | `parse_vba_cdate("01/02/2025")` → `"2025-02-01"` | Datas DD/MM/YYYY |
| `Format(num, "@@@/@@@")` | `format_dfd(num)` | Formatação DFD |
| `Left(str, n)` | `str[:n]` | Pegar N primeiros chars |
| `SoNumero(str)` | `so_numero(str)` | Apenas dígitos |

### Controle de Fluxo
```python
# VBA: On Error Resume Next
try:
    valor = parser(elemento)
except:
    valor = default  # Continua mesmo com erro
```

### Esperas e Sincronização
Replicamos as esperas do VBA com POLL=0.1 segundos:
```python
wait_spinner(driver, XPATHS["spinner"])
compat.wait(0.1)  # Equivalent to TimeValue("00:00:01")/10 in VBA
```

## Arquitetura Escalável

### Adição de Novos Scrapers
1. Criar arquivo `novo_scraper.py` em `backend/app/rpa/`
2. Adicionar XPaths em `novo_xpaths.json`
3. Criar service em `backend/app/services/novo_service.py`
4. Criar router em `backend/app/api/routers/novo.py`
5. Invocar via API: `POST /api/novo/iniciar`

### Adição de Novas Fontes de Dados
1. Estender schema em `backend/app/api/schemas.py`
2. Adicionar tabela em migrations SQL
3. Adicionar método em `backend/app/db/repositories.py`
4. Invocar via service e API

### Escalabilidade Futura
- Adicionar Celery para filas de tarefas assíncronas
- Adicionar Redis para cache e rate limiting
- Adicionar Elasticsearch para logs e auditoria
- Adicionar Prometheus/Grafana para métricas
- Adicionar Kubernetes para orquestração em produção

## Convenções de Nomes

- **Variáveis**: `snake_case` (Python)
- **Classes**: `PascalCase`
- **Constantes**: `UPPER_SNAKE_CASE`
- **Métodos privados**: `_leading_underscore`
- **XPath prefixes**: `xpath_*` na classe, ou chaves em JSON
- **Funções de parsing**: `parse_vba_*` para emular VBA

## Boas Práticas Implementadas

- ✅ Hooks pre-commit: black, flake8, mypy
- ✅ Type checking com mypy
- ✅ Formatação com black
- ✅ Linting com flake8
- ✅ Docstrings em todas as funções públicas
- ✅ Testes antes de merges
- ✅ Documentação atualizada para mudanças públicas
- ✅ Logs estruturados para observabilidade
- ✅ Tratamento de erros granulares
- ✅ Validação de entrada/saída
