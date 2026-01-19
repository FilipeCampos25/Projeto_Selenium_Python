# Projeto Python - Adaptação do Sistema VBA de Coleta de Dados PGC e PNCP

## 📋 Visão Geral

Este projeto é uma adaptação em Python de um sistema legado em VBA (Visual Basic for Applications) para automação de coleta de dados dos portais governamentais brasileiros:

- **PGC (Planejamento e Gerenciamento de Contratações)** - Portal Comprasnet
- **PNCP (Portal Nacional de Contratações Públicas)** - Coleta de demandas em abas (reprovadas, aprovadas, pendentes)

A adaptação mantém **fielmente a lógica de negócio** do sistema VBA original, mas implementada em Python moderno com arquitetura modular, tornando o código mais manutenível, testável e escalável.

## 🎯 Objetivos do Projeto

- ✅ Replicar **exatamente** a lógica de coleta de dados do VBA para PGC e PNCP
- ✅ Manter a **mesma funcionalidade** de navegação e extração em ambos portais
- ✅ Usar os **mesmos XPaths** e seletores do VBA
- ✅ Implementar **todos os padrões de sincronização** (spinners, esperas, timeouts)
- ✅ Substituir saída Excel por **JSON/CSV/Banco de dados**
- ✅ Criar código **modular e bem documentado**
- ✅ Suportar coleta paralela de **PGC** e **PNCP** com configuração flexível

## 📁 Estrutura do Projeto

```
projeto_adaptado/
├── backend/
│   └── app/
│       ├── rpa/
│       │   ├── pgc_scraper_vba_logic.py      ✅ Lógica PGC replicada do VBA
│       │   ├── pgc_xpaths.json               ✅ XPaths PGC centralizados
│       │   ├── pncp_scraper_vba_logic.py     ✅ Lógica PNCP replicada do VBA
│       │   ├── pncp_xpaths.json              ✅ XPaths PNCP centralizados
│       │   ├── waiter_vba.py                 ✅ Funções de espera do VBA
│       │   ├── driver_factory.py             ✅ Fábrica de drivers moderna
│       │   ├── vba_compat.py                 ✅ Compatibilidade VBA
│       │   └── *.py                          ✅ Utilitários (OCR, downloader, etc)
│       ├── db/                               (banco de dados PostgreSQL)
│       ├── api/routers/
│       │   ├── pncp.py                       🔗 Endpoints PNCP
│       │   ├── pgc.py                        🔗 Endpoints PGC
│       │   └── *.py                          🔗 Outros endpoints
│       ├── services/
│       │   ├── pncp_service.py               ⚙️ Orquestração PNCP
│       │   ├── pgc_service.py                ⚙️ Orquestração PGC
│       │   └── *.py                          ⚙️ Serviços auxiliares
│       └── core/                             (camada base)
├── docs/
│   ├── architecture.md                   📊 Arquitetura geral
│   ├── design_philosophy.md              📊 Filosofia de design
│   ├── development.md                    📊 Guia de desenvolvimento
│   ├── orchestration.md                  📊 Deploy e orquestração
│   ├── pncp_implementation.md             📊 Implementação detalhada PNCP
│   └── *.md                              📊 Outros documentos
├── docker-compose.yml                    🐳 Stack Docker
├── MUDANCAS_VBA_TO_PYTHON.md             📖 Documentação técnica das mudanças
├── RELATORIO_ADAPTACAO_VBA_PYTHON.md     📖 Relatório executivo da adaptação
├── INSTRUCOES_DE_USO.md                  📖 Guia de uso do código adaptado
└── README.md                             📖 Este arquivo
```

## 🚀 Início Rápido

### Pré-requisitos

- Python 3.11+
- Google Chrome
- Credenciais de acesso ao Comprasnet

### Instalação

```bash
# 1. Extrair o projeto
unzip projeto_python_adaptado.zip
cd projeto_adaptado

# 2. Instalar dependências
pip install -r requirements.txt
```

### Uso Básico

```bash
# Executar coleta de dados PGC
python3 -m backend.app.rpa.pgc_scraper_vba_logic <CPF> <SENHA> 2025

# Executar coleta de dados PNCP
python3 -m backend.app.rpa.pncp_scraper_vba_logic 2025
```

### Uso Programático

```python
# Coleta PGC
from backend.app.rpa.pgc_scraper_vba_logic import run_pgc_scraper_vba
pgc_data = run_pgc_scraper_vba(ano_ref="2025")
print(f"PGC: {len(pgc_data)} registros coletados")

# Coleta PNCP
from backend.app.rpa.pncp_scraper_vba_logic import run_pncp_scraper_vba
pncp_data = run_pncp_scraper_vba(ano_ref="2025")
print(f"PNCP: {len(pncp_data)} itens coletados")
```

### Uso via API

- **PGC**: POST `/api/pgc/iniciar` com `{"ano_ref": 2025}` (login manual via noVNC)
- **PNCP**: POST `/api/pncp/iniciar` com `{"ano_ref": 2025}` (login manual via noVNC)

## 📚 Documentação

| Documento | Descrição |
|-----------|-----------|
| **INSTRUCOES_DE_USO.md** | Guia completo de uso do código adaptado |
| **MUDANCAS_VBA_TO_PYTHON.md** | Documentação técnica detalhada de todas as mudanças |
| **RELATORIO_ADAPTACAO_VBA_PYTHON.md** | Relatório executivo da análise e adaptação |
| **docs/architecture.md** | Arquitetura geral do sistema (PGC + PNCP) |
| **docs/design_philosophy.md** | Filosofia de design e princípios |
| **docs/development.md** | Guia de desenvolvimento e workflows |
| **docs/orchestration.md** | Deploy, Docker e orquestração |
| **docs/pncp_implementation.md** | Detalhes técnicos da implementação PNCP |

## 🔍 Principais Mudanças

### PGC - Fluxo de Login Completo

**Antes (Python original):**
- Login básico em 3 etapas

**Depois (Python adaptado):**
- Login completo em **9 etapas** exatamente como o VBA
- Inclui todas as esperas, scrolls e troca de janela

### PGC - Lógica de Paginação Correta

**Antes:**
- Tentativa de iterar por `range(1000)` páginas

**Depois:**
- Vai para última página para descobrir o total
- Retorna para primeira página
- Itera clicando em cada botão de página específico
- Aguarda confirmação de que está na página correta

### PNCP - Coleta Multi-Aba Completa (NOVO)

**Implementado:**
- ✅ Suporte a 3 abas: **Reprovadas, Aprovadas, Pendentes**
- ✅ Descoberta dinâmica de total de itens por aba
- ✅ Rolagem inteligente e carregamento de todos os itens
- ✅ Extração granular com tratamento de erro por item
- ✅ Mapeamento preciso de colunas (9 campos por item)
- ✅ Logs de auditoria fiéis ao VBA
- ✅ Persistência automática em Postgres e Excel

### PNCP - Tratamentos de Dados (NOVO)

**Conversões VBA Emuladas:**
- `CDbl()` para valores monetários
- `CDate()` para datas em formato DD/MM/YYYY
- `Format()` para formatação de DFD (XXX/XXXX)
- `Left()` e `SoNumero()` para manipulação de strings
- `On Error Resume Next` granular por campo

### Extração de Tabela Precisa (PGC)

**Antes:**
- Índices de coluna genéricos (0, 1, 2, 3, 4)

**Depois:**
- Índices exatos do VBA (4, 6, 7, 8, 9)
- Formatação de DFD com 8 dígitos
- Conversão correta de valores monetários

### Leitura Detalhada de DFDs (PGC)

**Antes:**
- Não implementado ou parcial

**Depois:**
- Construção de URL específica para cada DFD
- Extração de todos os campos (conclusão, editor, responsáveis)
- Processamento de tabela interna de responsáveis

### XPaths Específicos

**Antes:**
- XPaths genéricos (`//table`, `//button`)

**Depois:**
- XPaths específicos do VBA centralizados em JSON
- Exemplo PGC: `//body/app-root/ng-http-loader/div[@id='spinner']`
- Exemplo PNCP: `//div[@aria-labelledby='reprovadas']//span[contains(text(), 'registros')]`

## 📊 Comparação VBA vs Python

| Aspecto | VBA Original | Python Adaptado |
|---------|--------------|-----------------|
| **PGC - Linhas de código** | 9.900 (1 arquivo) | 2.622 (modular) |
| **PNCP - Suporte** | ❌ Não | ✅ Completo |
| **PGC - Login** | 9 etapas | 9 etapas ✅ |
| **PGC - Paginação** | Descobre total primeiro | Descobre total primeiro ✅ |
| **PNCP - Multi-aba** | ❌ Não | ✅ Reprovadas/Aprovadas/Pendentes |
| **PNCP - Itens por aba** | ❌ Não | ✅ Com tratamento granular |
| **XPaths** | Específicos | Específicos ✅ |
| **Formatação DFD** | 8 dígitos | 8 dígitos ✅ |
| **Sincronização** | 117 chamadas spinner | 117+ chamadas spinner ✅ |
| **Saída** | Excel | JSON/CSV/Postgres ✅ |
| **Arquitetura** | Monolítica | Modular ✅ |
| **API REST** | ❌ Não | ✅ FastAPI |
| **Persistência** | Excel | Postgres ✅ |

## 🛠️ Tecnologias Utilizadas

- **Python 3.11+** - Linguagem principal
- **Selenium** - Automação web
- **PostgreSQL** - Banco de dados (opcional)
- **FastAPI** - API REST (opcional)
- **Docker** - Containerização (opcional)

## 📦 Estrutura de Dados

### PGC - Cada registro coletado contém:

```python
{
    "pag": 1,                           # Número da página
    "dfd": "00012345",                  # DFD formatado (8 dígitos)
    "requisitante": "Nome",             # Requisitante
    "descricao": "Descrição",           # Descrição da demanda
    "valor": 10000.50,                  # Valor (float)
    "situacao": "Em andamento",         # Situação
    "conclusao": "2025-12-31",          # Data de conclusão
    "editor": "Nome do Editor",         # Editor
    "responsaveis": "Nome / Cargo\n...", # Responsáveis
    "pta": "",                          # PTA
    "justificativa": ""                 # Justificativa
}
```

### PNCP - Cada item coletado contém:

```python
{
    "col_a_contratacao": "ID-12345",    # Número da contratação
    "col_b_descricao": "Descrição",     # Descrição do item
    "col_c_categoria": "Categoria",     # Categoria
    "col_d_valor": 50000.00,            # Valor (float)
    "col_e_inicio": "2025-01-01",       # Data início (ISO)
    "col_f_fim": "2025-12-31",          # Data fim (ISO)
    "col_g_status": "APROVADA",         # Status atual
    "col_h_status_tipo": "APROVADA",    # Tipo de status
    "col_i_dfd": "157/2025"             # DFD formatado (XXX/YYYY)
}
```

## 🧪 Testes

```bash
# Teste básico
python3 -m backend.app.rpa.pgc_scraper_vba_logic <CPF> <SENHA> 2025

# Com logging detalhado
python3 -c "
import logging
logging.basicConfig(level=logging.INFO)
from backend.app.rpa.pgc_scraper_vba_logic import run_pgc_scraper_vba
data = run_pgc_scraper_vba('cpf', 'senha', '2025')
print(f'Total: {len(data)} registros')
"
```

## 🔧 Configuração

### XPaths Customizados

Edite `backend/app/rpa/pgc_xpaths.json` para atualizar seletores:

```json
{
  "login": {
    "url": "http://www.comprasnet.gov.br/seguro/loginPortal.asp",
    "btn_expand_governo": "//button[@class='br-button circle expand governo']",
    ...
  }
}
```

### Timeouts

Edite `backend/app/rpa/waiter_vba.py`:

```python
DEFAULT_TIMEOUT = 30  # Aumentar se necessário
POLL = 0.1            # Intervalo de verificação
```

## 📈 Próximos Passos (Opcional)

Funcionalidades do VBA não implementadas (podem ser adicionadas):

- [ ] **Dados_PNCP()** - Integração com PNCP
- [ ] **A2_leitura_SEI()** - Integração com SEI
- [ ] **A3_Cria_Contratacao()** - Criação de contratações
- [ ] **A4_Atualiza_Contratacao()** - Atualização de contratações

## 🤝 Contribuindo

Este projeto foi criado como uma adaptação específica de um sistema legado. Para modificações:

1. Consulte a documentação em `docs/`
2. Mantenha a compatibilidade com a lógica VBA
3. Atualize os XPaths em `pgc_xpaths.json`
4. Documente as mudanças

## ⚠️ Avisos Importantes

- Use apenas com **credenciais válidas** e autorizadas
- Respeite os **limites de taxa** dos sistemas governamentais
- Teste em **ambiente de desenvolvimento** antes de produção
- Não compartilhe **senhas** ou credenciais

## 📄 Licença

Este projeto é uma adaptação de um sistema interno. Consulte as políticas de uso dos sistemas governamentais antes de utilizar.

## 📞 Suporte

Para dúvidas ou problemas:

1. Consulte `INSTRUCOES_DE_USO.md`
2. Revise a documentação técnica em `MUDANCAS_VBA_TO_PYTHON.md`
3. Verifique os logs de execução
4. Compare com o código VBA original em `docs/vba_deep_analysis.md`

---

**Desenvolvido por:** Filipe de Campos Duarte  
**Data:** 24 Dezembro de 2025  
**Versão:** 1.0.0
