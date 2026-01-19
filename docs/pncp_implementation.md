# Implementação Detalhada do PNCP

## Visão Geral

O módulo PNCP (`backend/app/rpa/pncp_scraper_vba_logic.py`) implementa a coleta completa de demandas do Portal Nacional de Contratações Públicas. A implementação replica fielmente a lógica VBA com suporte a 3 abas de status: **Reprovadas**, **Aprovadas** e **Pendentes**.

## Arquitetura PNCP

### Fluxo de Execução

```
PNCPScraperVBA.Dados_PNCP()
  ├─ _preparar_navegação_inicial()
  │   ├─ testa_spinner() [sync com página]
  │   └─ Aguarda botão 'Formação do PCA'
  │
  ├─ _selecionar_ano_pca()
  │   ├─ Aguarda dropdown PCA
  │   └─ Seleciona ano (e.g., 2025)
  │
  ├─ Para cada aba (reprovadas, aprovadas, pendentes):
  │   │
  │   ├─ _coletar_aba(aba_id, status_vba)
  │   │   ├─ Clica na aba
  │   │   ├─ Verifica se está vazia
  │   │   ├─ _obter_total_demandas() [descobre total]
  │   │   ├─ _executar_rolagem_tabela() [carrega todos itens]
  │   │   └─ _extrair_itens_tabela() [coleta campos]
  │   │
  │   ├─ Para cada item (i = 1 até total):
  │   │   ├─ Extrai 9 campos:
  │   │   │   ├─ col_a_contratacao (ID)
  │   │   │   ├─ col_b_descricao (Descrição)
  │   │   │   ├─ col_c_categoria (Categoria)
  │   │   │   ├─ col_d_valor (parse CDbl)
  │   │   │   ├─ col_e_inicio (parse CDate)
  │   │   │   ├─ col_f_fim (parse CDate)
  │   │   │   ├─ col_g_status (Status)
  │   │   │   ├─ col_h_status_tipo (Tipo status)
  │   │   │   └─ col_i_dfd (Formato DFD)
  │   │   │
  │   │   ├─ Validação via PNCPItemSchema
  │   │   ├─ Log de auditoria
  │   │   └─ Adiciona à lista de coleta
  │   │
  │   └─ Retorna para próxima aba
  │
  └─ Retorna dados_collected

Retorna: List[Dict[str, Any]]
```

## Componentes Principais

### 1. Classe PNCPScraperVBA

```python
class PNCPScraperVBA:
    def __init__(self, driver: WebDriver, ano_ref: str = "2025"):
        self.driver = driver
        self.ano_ref = ano_ref
        self.compat = VBACompat(driver)  # Emulação VBA
        self.data_collected = []
```

**Atributos**:
- `driver`: Instância Selenium WebDriver
- `ano_ref`: Ano de referência da coleta (string, e.g., "2025")
- `compat`: Instância de VBACompat para emulação de funções VBA
- `data_collected`: Lista de itens coletados

### 2. Funções Principais

#### `Dados_PNCP()` - Entrypoint Principal
```python
def Dados_PNCP(self) -> List[Dict[str, Any]]:
    """Replica Sub Dados_PNCP() do VBA. Entrypoint principal."""
    # [LOG-VBA] Logs de auditoria
    # Preparação inicial
    # Coleta por abas
    # Tratamento de erros granulares
    # Retorna dados validados
```

**Fluxo**:
1. Log inicial com parâmetros
2. Preparação de navegação
3. Seleção de ano
4. Loop sobre 3 abas
5. Tratamento de exceção por aba
6. Log final com total

#### `_preparar_navegação_inicial()` - Setup
```python
def _preparar_navegação_inicial(self):
    """Sincronização e visibilidade inicial (Passo 2.1)."""
    # testa_spinner() - aguarda carregamento
    # Aguarda botão 'Formação do PCA' aparecer
    # Scroll para visibilidade
    # Clica no botão
    # testa_spinner() novamente
```

**Responsabilidades**:
- Sincronização com página
- Localização do botão PCA
- Navegação para tela principal

#### `_selecionar_ano_pca()` - Dropdown Selection
```python
def _selecionar_ano_pca(self):
    """Seleção do ano no dropdown PCA (Passo 2.1)."""
    # Aguarda dropdown aparecer
    # Clica no dropdown
    # Encontra e clica no ano (template substituição)
    # Aguarda sincronização
```

**Pontos críticos**:
- XPath template com substituição de `{ano}`
- Esperas entre cliques
- Validação de carregamento

#### `_coletar_aba(aba_id, status_vba)` - Por Aba
```python
def _coletar_aba(self, aba_id: str, status_vba: str):
    """Lógica de coleta por aba (Passo 2.1)."""
    # Clica na aba
    # Verifica se vazia
    # Obtém total de demandas
    # Executa rolagem para carregar tudo
    # Extrai itens
    # Log de conclusão
```

**Abas suportadas**:
- `"reprovadas"` → status `"REPROVADA"`
- `"aprovadas"` → status `"APROVADA"`
- `"pendentes"` → status `"PENDENTE"`

#### `_obter_total_demandas(aba_id)` - Descoberta de Total
```python
def _obter_total_demandas(self, aba_id: str) -> int:
    """Extrai o número total de demandas da aba (Passo 3.2)."""
    # XPath template com substituição de `{aba_id}`
    # Aguarda até 20 segundos
    # Parse com so_numero() (apenas dígitos)
    # Retorna inteiro
```

**XPath Pattern**:
```
//span[contains(text(), 'Mostrando') and contains(text(), 'registros')]
```

#### `_executar_rolagem_tabela(aba_id, demandas)` - Smart Scrolling
```python
def _executar_rolagem_tabela(self, aba_id: str, demandas: int):
    """Executa a rolagem fiel ao VBA para carregar todos os itens (Passo 5.1)."""
    # Localiza o item último (index = demandas)
    # Executa scroll progressivo
    # Verifica se todas as 9 colunas carregaram
    # Aguarda até 180 segundos
    # Sincronização final
```

**Estratégia**:
1. Encontra XPath do último item
2. Se não existe, scroll e retry
3. Repete até aparecer ou timeout
4. Testa_spinner final

#### `_extrair_itens_tabela(aba_id, demandas)` - Extração de Dados
```python
def _extrair_itens_tabela(self, aba_id: str, demandas: int):
    """Loop de extração de campos com tratamento de erro por item (Passo 3.3)."""
    for i in range(1, demandas + 1):
        try:
            # Extração de 9 campos por item
            # Parsing VBA (CDbl, CDate, Format)
            # Validação via schema
            # Log de auditoria
            # Adiciona à lista
        except Exception:
            # Log de aviso, continua para próximo item
```

**Campos Extraídos**:

| Campo | XPath | Processamento | Tipo |
|-------|-------|---------------|------|
| `col_a_contratacao` | `fields['contratacao']` | Texto simples | str |
| `col_b_descricao` | `fields['descricao']` | Texto simples | str |
| `col_c_categoria` | `fields['categoria']` | Texto simples | str |
| `col_d_valor` | `fields['valor']` | `parse_vba_cdbl()` | float |
| `col_e_inicio` | `fields['inicio']` | `parse_vba_cdate()` | str (ISO) |
| `col_f_fim` | `fields['fim']` | `parse_vba_cdate()` | str (ISO) |
| `col_g_status` | `fields['status_*']` | Depende da aba | str |
| `col_h_status_tipo` | Calculado | Tipo de status | str |
| `col_i_dfd` | Calculado | `format_dfd()` | str |

### 3. Funções de Parsing VBA Emuladas

#### `_parse_vba_cdbl(text: str) -> float`
```python
def _parse_vba_cdbl(self, text: str) -> float:
    """Emula CDbl do VBA (Passo 3.1)."""
    # Remove "R$"
    # Substitui "." por "" (separador de milhares)
    # Substitui "," por "." (separador decimal)
    # Converte para float
    # Retorna 0.0 se falhar
```

**Exemplos**:
- `"R$ 1.234,56"` → `1234.56`
- `"1234567,89"` → `1234567.89`
- `""` → `0.0`

#### `_parse_vba_cdate(text: str) -> Optional[str]`
```python
def _parse_vba_cdate(self, text: str) -> Optional[str]:
    """Emula CDate do VBA (Passo 3.1)."""
    # Verifica formato DD/MM/YYYY (deve ter "/")
    # Converte para datetime
    # Retorna ISO format (YYYY-MM-DD)
    # Retorna None se falhar
```

**Exemplos**:
- `"01/02/2025"` → `"2025-02-01"`
- `"31/12/2024"` → `"2024-12-31"`
- `""` → `None`

#### `_format_dfd(descricao: str) -> str`
```python
def _format_dfd(self, descricao: str) -> str:
    """Emula Format(Left(SoNumero(desc), 7), '@@@\/@@@@') do VBA (Passo 3.1)."""
    # so_numero(desc) → apenas dígitos
    # Left(..., 7) → primeiros 7 dígitos
    # Format em XXX/XXXX
```

**Exemplos**:
- `"Demanda 1572025"` → `"157/2025"`
- `"DFD 1570000"` → `"157/0000"`

#### `so_numero(text: str) -> str`
```python
def so_numero(self, text: str) -> str:
    """Emula a função SoNumero do VBA para limpeza de strings."""
    # Apenas dígitos (0-9)
    # Remove tudo mais
```

**Exemplos**:
- `"DFD 157/2025"` → `"1572025"`
- `"ABC123DEF456"` → `"123456"`

### 4. XPaths PNCP

Arquivo: `backend/app/rpa/pncp_xpaths.json`

```json
{
  "pca_selection": {
    "button_formacao_pca": "//button[contains(text(), 'Formação do PCA')]",
    "dropdown_pca": "//ng-select[...]",
    "li_pca_ano_template": "//li[contains(text(), '{ano}')]"
  },
  "tabs": {
    "reprovadas": "//button[@aria-labelledby='reprovadas']",
    "aprovadas": "//button[@aria-labelledby='aprovadas']",
    "pendentes": "//button[@aria-labelledby='pendentes']"
  },
  "table": {
    "label_total_template": "//span[contains(., 'Mostrando') and contains(., '{aba_id}')]",
    "tbody_template": "//div[@aria-labelledby='{aba_id}']//table/tbody",
    "item_base_template": "//div[@aria-labelledby='{aba_id}']//tr[{index}]"
  },
  "fields": {
    "contratacao": "/td[1]",
    "descricao": "/td[2]",
    "categoria": "/td[3]",
    "valor": "/td[4]",
    "inicio": "/td[5]",
    "fim": "/td[6]",
    "status_aprovada": "/td[7]/span",
    "status_pendente": "/td[7]/span"
  }
}
```

## Fluxo de Dados Completo

### Input
```python
ano_ref: str = "2025"  # Ano de referência
```

### Processamento por Aba

1. **Sincronização**: `testa_spinner()` + aguarda elemento
2. **Navegação**: Clica na aba, aguarda carregamento
3. **Descoberta**: Lê total de demandas do label
4. **Carregamento**: Scroll progressivo até último item visível
5. **Extração**: Loop sobre cada item com parse de campos
6. **Validação**: Pydantic schema validação
7. **Persistência**: Adiciona à lista `data_collected`

### Output

```python
[
  {
    "col_a_contratacao": "CT-001/2025",
    "col_b_descricao": "Aquisição de materiais de escritório",
    "col_c_categoria": "Material de Consumo",
    "col_d_valor": 5000.00,
    "col_e_inicio": "2025-02-01",
    "col_f_fim": "2025-12-31",
    "col_g_status": "APROVADA",
    "col_h_status_tipo": "APROVADA",
    "col_i_dfd": "157/2025"
  },
  # ... mais itens
]
```

## Tratamento de Erros

### Granularidade por Campo
```python
def get_safe_text(xpath_suffix, default=""):
    """On Error Resume Next granular por campo"""
    try:
        return self.driver.find_element(By.XPATH, f"{base_xpath}{xpath_suffix}").text
    except:
        return default
```

### Granularidade por Item
```python
for i in range(1, demandas + 1):
    try:
        # Extração completa do item
    except Exception as e:
        logger.warning(f"[AVISO-VBA] Falha ao coletar item {i}. Pulando...")
        # Continua para próximo item
```

### Granularidade por Aba
```python
for aba_id, status in [...]:
    try:
        self._coletar_aba(aba_id, status)
    except Exception as e:
        logger.error(f"[ERRO-ABA] Falha na aba {aba_id}. Prosseguindo...")
        # Continua para próxima aba
```

## Logs de Auditoria

Todos os logs seguem o padrão `[LOG-VBA]` ou `[ERRO-*]`:

```
[LOG-VBA] Coleta iniciada - ANO REF: 2025
[LOG-VBA] Sincronizando (testa_spinner)...
[LOG-VBA] Localizando demandas reprovadas...
[LOG-VBA] Total de demandas reprovadas: 42
[LOG-VBA] Rolando para carregar 42 itens...
[AUDITORIA-ITEM] 1/42 | ID: CT-001/2025 | Status: REPROVADA
[AUDITORIA-ITEM] 2/42 | ID: CT-002/2025 | Status: REPROVADA
...
[LOG-VBA] Coleta PNCP Concluída. TOTAL: 157 ITENS
```

## Persistência

### Via Service

```python
from backend.app.services.pncp_service import coleta_pncp

resultado = coleta_pncp(
    username="",      # Login manual
    password="",      # Login manual
    ano_ref="2025"
)

# Persiste em:
# 1. PostgreSQL (JSONB em tabela coletas)
# 2. Excel (PGC_2025.xlsx)
```

### Via API

```bash
POST /api/pncp/iniciar
Content-Type: application/json

{"ano_ref": 2025}

Response:
{
  "status": "started",
  "ano_ref": 2025,
  "modo_execucao": "REAL",
  "message": "Coleta PNCP REAL iniciada..."
}
```

## Validação de Dados

### Pydantic Schema

```python
class PNCPItemSchema(BaseModel):
    col_a_contratacao: str
    col_b_descricao: str
    col_c_categoria: str
    col_d_valor: float
    col_e_inicio: Optional[str]  # ISO date
    col_f_fim: Optional[str]     # ISO date
    col_g_status: str
    col_h_status_tipo: str
    col_i_dfd: str
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat()
        }
```

## Métricas e Performance

### Tempos Típicos
- **Sincronização**: 2-5s
- **Por aba (100 itens)**: 30-60s
- **Total (3 abas, 200+ itens)**: 120-180s

### Otimizações
- Parallelizar abas (Celery) - FUTURO
- Cache de XPaths - PRONTO
- Pool de drivers - FUTURO
- Proxy rotation - FUTURO

## Debugging

### VNC Live View
```bash
# Acompanhar coleta em tempo real
http://localhost:7900
# Senha: secret
```

### Modo Verboso
```python
# Aumentar log level
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Breakpoints
```python
# Adicionar em qualquer ponto
breakpoint()
# Precisar de DEBUGPY=1 no docker compose
```
