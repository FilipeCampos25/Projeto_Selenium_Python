# Instruções de Uso - Projeto Python Adaptado

## Visão Geral

Este projeto Python foi adaptado para replicar fielmente a lógica do código VBA original, mantendo a mesma funcionalidade de coleta de dados do PGC (Planejamento e Gerenciamento de Contratações), mas sem as interações diretas com o Excel.

## Arquivos Principais

### Novos Arquivos Criados

1. **`backend/app/rpa/pgc_scraper_vba_logic.py`**
   - Implementação principal que replica a lógica do VBA
   - Contém a classe `PGCScraperVBA` com os métodos principais

2. **`backend/app/rpa/pgc_xpaths.json`**
   - Arquivo de configuração com todos os XPaths específicos do VBA
   - Centraliza os seletores para facilitar manutenção

3. **`backend/app/rpa/waiter_vba.py`**
   - Funções de espera otimizadas para replicar o comportamento do VBA
   - Inclui `wait_spinner()` e outras funções de sincronização

### Documentação

1. **`MUDANCAS_VBA_TO_PYTHON.md`**
   - Documentação técnica detalhada de todas as mudanças
   - Mapeamento de funções VBA → Python
   - Exemplos de uso

2. **`RELATORIO_ADAPTACAO_VBA_PYTHON.md`**
   - Relatório executivo da análise e adaptação
   - Comparação entre VBA e Python
   - Resultados e recomendações

3. **`INSTRUCOES_DE_USO.md`** (este arquivo)
   - Guia prático de uso do código adaptado

## Pré-requisitos

### Software Necessário

- Python 3.11 ou superior
- Google Chrome (versão compatível com ChromeDriver)
- ChromeDriver (gerenciado automaticamente pelo Selenium)

### Dependências Python

Instale as dependências do projeto:

```bash
pip install -r requirements.txt
```

As principais dependências são:
- `selenium` - Automação web
- `requests` - Requisições HTTP
- Outras dependências listadas em `requirements.txt`

## Como Usar

### Opção 1: Uso Básico (Standalone)

Execute o scraper diretamente via linha de comando:

```bash
cd /caminho/para/projeto_adaptado
python3 -m backend.app.rpa.pgc_scraper_vba_logic <CPF> <SENHA> [ANO_REF]
```

**Parâmetros:**
- `<CPF>`: Seu CPF (apenas números)
- `<SENHA>`: Sua senha de acesso ao Comprasnet
- `[ANO_REF]`: Ano de referência do PCA (opcional, padrão: 2025)

**Exemplo:**
```bash
python3 -m backend.app.rpa.pgc_scraper_vba_logic 12345678901 minha_senha 2025
```

### Opção 2: Uso Programático

Importe e use no seu código Python:

```python
from backend.app.rpa.pgc_scraper_vba_logic import run_pgc_scraper_vba

# Executar scraper
data = run_pgc_scraper_vba(
    username="12345678901",
    password="minha_senha",
    ano_ref="2025"
)

# Processar dados coletados
print(f"Total de registros coletados: {len(data)}")

for item in data:
    print(f"DFD: {item['dfd']}")
    print(f"Requisitante: {item['requisitante']}")
    print(f"Valor: R$ {item['valor']:.2f}")
    print(f"Situação: {item['situacao']}")
    print("-" * 50)
```

### Opção 3: Uso com Driver Customizado

Se você precisa de mais controle sobre o driver do Selenium:

```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from backend.app.rpa.pgc_scraper_vba_logic import PGCScraperVBA

# Configurar opções do Chrome
options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-gpu")
# options.add_argument("--headless")  # Descomente para modo headless

# Criar driver
driver = webdriver.Chrome(options=options)

try:
    # Criar scraper
    scraper = PGCScraperVBA(
        driver=driver,
        username="12345678901",
        password="minha_senha",
        ano_ref="2025"
    )
    
    # Executar login
    scraper.A_Loga_Acessa_PGC()
    
    # Coletar dados
    data = scraper.A1_Demandas_DFD_PCA()
    
    # Processar dados
    print(f"Total de registros: {len(data)}")
    
finally:
    driver.quit()
```

## Estrutura dos Dados Coletados

Cada registro coletado é um dicionário com a seguinte estrutura:

```python
{
    "pag": 1,                           # Número da página onde foi encontrado
    "dfd": "00012345",                  # DFD formatado com 8 dígitos
    "requisitante": "Nome do Requisitante",
    "descricao": "Descrição da demanda",
    "valor": 10000.50,                  # Valor em float
    "situacao": "Em andamento",
    "conclusao": "2025-12-31",          # Data no formato YYYY-MM-DD
    "editor": "Nome do Editor",
    "responsaveis": "Nome / Cargo\nNome2 / Cargo2",  # Separados por \n
    "pta": "",                          # PTA (se disponível)
    "justificativa": ""                 # Justificativa (se disponível)
}
```

## Salvando os Dados

### Salvar em JSON

```python
import json
from backend.app.rpa.pgc_scraper_vba_logic import run_pgc_scraper_vba

# Coletar dados
data = run_pgc_scraper_vba("cpf", "senha", "2025")

# Salvar em JSON
with open("dados_pgc.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

### Salvar em CSV

```python
import csv
from backend.app.rpa.pgc_scraper_vba_logic import run_pgc_scraper_vba

# Coletar dados
data = run_pgc_scraper_vba("cpf", "senha", "2025")

# Salvar em CSV
with open("dados_pgc.csv", "w", encoding="utf-8", newline="") as f:
    if data:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
```

### Salvar em Banco de Dados (PostgreSQL)

Se você estiver usando o projeto completo com banco de dados:

```python
from backend.app.rpa.pgc_scraper_vba_logic import run_pgc_scraper_vba
from backend.app.db.repositories import save_pgc_data

# Coletar dados
data = run_pgc_scraper_vba("cpf", "senha", "2025")

# Salvar no banco
save_pgc_data(data)
```

## Configuração dos XPaths

Se os XPaths mudarem no sistema PGC, você pode atualizá-los editando o arquivo `backend/app/rpa/pgc_xpaths.json`:

```json
{
  "login": {
    "url": "http://www.comprasnet.gov.br/seguro/loginPortal.asp",
    "btn_expand_governo": "//button[@class='br-button circle expand governo']",
    ...
  },
  ...
}
```

## Logging

O código usa o módulo `logging` do Python. Para ativar logs detalhados:

```python
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Executar scraper (os logs serão exibidos)
from backend.app.rpa.pgc_scraper_vba_logic import run_pgc_scraper_vba
data = run_pgc_scraper_vba("cpf", "senha", "2025")
```

## Tratamento de Erros

O código implementa tratamento de erros robusto. Em caso de falha:

1. **Verifique os logs** para identificar o ponto de falha
2. **Verifique os XPaths** - eles podem ter mudado no site
3. **Verifique a conexão** - o site pode estar fora do ar
4. **Verifique as credenciais** - login/senha podem estar incorretos

Exemplo de tratamento de erro:

```python
from backend.app.rpa.pgc_scraper_vba_logic import run_pgc_scraper_vba
import logging

logging.basicConfig(level=logging.INFO)

try:
    data = run_pgc_scraper_vba("cpf", "senha", "2025")
    print(f"Sucesso! {len(data)} registros coletados.")
except Exception as e:
    print(f"Erro durante a coleta: {e}")
    logging.exception("Detalhes do erro:")
```

## Dicas de Uso

### 1. Modo Headless

Para executar sem abrir o navegador (útil em servidores):

```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from backend.app.rpa.pgc_scraper_vba_logic import PGCScraperVBA

options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=options)
scraper = PGCScraperVBA(driver, "cpf", "senha", "2025")
# ... resto do código
```

### 2. Timeout Customizado

Se a rede estiver lenta, você pode aumentar os timeouts:

```python
# Editar waiter_vba.py
DEFAULT_TIMEOUT = 60  # Aumentar de 30 para 60 segundos
```

### 3. Coletar Apenas Algumas Páginas (para testes)

Modifique temporariamente o método `A1_Demandas_DFD_PCA`:

```python
# No arquivo pgc_scraper_vba_logic.py, linha ~350
# Adicione uma condição de parada:
while not sai:
    # ... código existente ...
    
    # TESTE: Parar após 2 páginas
    if pos >= 2:
        sai = True
        break
    
    # ... resto do código ...
```

## Comparação com o VBA

| Funcionalidade | VBA | Python Adaptado |
|----------------|-----|-----------------|
| Login | ✅ 9 etapas | ✅ 9 etapas (idêntico) |
| Paginação | ✅ Descobre total | ✅ Descobre total (idêntico) |
| Extração de tabela | ✅ `.AsTable` | ✅ Extração manual com mesmos índices |
| Formatação DFD | ✅ 8 dígitos | ✅ 8 dígitos (idêntico) |
| Detalhes DFD | ✅ Completo | ✅ Completo (idêntico) |
| Saída | Excel | JSON/CSV/Banco de dados |

## Próximos Passos (Opcional)

Se você precisar das funcionalidades adicionais do VBA:

1. **Integração com PNCP**: Implementar `Dados_PNCP()`
2. **Integração com SEI**: Implementar `A2_leitura_SEI()`
3. **Criação de Contratações**: Implementar `A3_Cria_Contratacao()`
4. **Atualização de Contratações**: Implementar `A4_Atualiza_Contratacao()`

Estes podem ser implementados seguindo o mesmo padrão de análise e adaptação usado para o PGC.

## Suporte

Para dúvidas ou problemas:

1. Consulte a documentação em `MUDANCAS_VBA_TO_PYTHON.md`
2. Verifique os logs de execução
3. Revise o código VBA original para entender a lógica
4. Teste em ambiente de desenvolvimento antes de produção

## Licença e Avisos

- Este código foi adaptado de um sistema VBA legado
- Certifique-se de ter autorização para acessar os sistemas governamentais
- Use credenciais válidas e não compartilhe senhas
- Respeite os limites de taxa e políticas de uso dos sistemas
