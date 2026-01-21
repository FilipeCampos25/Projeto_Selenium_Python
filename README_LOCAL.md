# Guia de Execução LOCAL (Sem Docker)

🔴 **ESTE É UM MODO TEMPORÁRIO DE EXECUÇÃO**  
🔴 **PARA VOLTAR AO DOCKER, REVERTA AS MODIFICAÇÕES MARCADAS COM `🔴`**

---

## 📋 Pré-requisitos

### 1. Google Chrome
- Baixar e instalar: https://www.google.com/chrome/
- Verificar instalação: `google-chrome --version` (ou procure no menu Iniciar)
- **Nota**: Não precisa estar no PATH, o Selenium gerencia automaticamente

### 2. ChromeDriver
- **AUTOMÁTICO**: O projeto usa `webdriver-manager` que baixa o ChromeDriver compatível automaticamente
- Não precisa instalar manualmente (era necessário em versões antigas do Selenium)

### 3. Python 3.11+
- Verificar: `python --version`

---

## 🚀 Como Executar

### Opção 1: Script Automático (Recomendado)

```bash
# 1. Criar ambiente virtual
python -m venv venv

# 2. Ativar ambiente
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Executar script de inicialização (com carregamento de .env.local)
python run_local_server.py
```

### Opção 2: Manual

```bash
# 1. Criar ambiente virtual
python -m venv venv

# 2. Ativar ambiente
venv\Scripts\activate  # Windows
# ou
source venv/bin/activate  # Linux/Mac

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Arquivo .env.local é criado automaticamente (OU edit manualmente)
# Se quiser editar: abra o arquivo .env.local com seu editor de texto

# 5. Executar servidor usando o wrapper que carrega .env.local
python run_local_server.py
```

---

## 🌐 Acessar Sistema

1. **Interface Web**: http://localhost:8000/pgc
2. **API Docs**: http://localhost:8000/docs
3. **Health Check**: http://localhost:8000/api/ready

### Em Modo Local (Sem Docker):
- ❌ **SEM noVNC**: O navegador Chrome abrirá **localmente em sua máquina**
- ✅ **Com Chrome local**: Você verá o navegador normalmente
- 🖱️ **Login manual**: Quando a página do portal abrir, você fará o login normalmente (sem precisar de VNC)

---

## 📁 Onde Ficam os Arquivos

```
projeto_adaptado/
├── outputs_local/          ← 📊 ARQUIVOS EXCEL SALVOS AQUI
├── dados_locais_temp/      ← 💾 JSON temporário
├── downloads_local/        ← ⬇️ Downloads do navegador
└── ...
```

---

## 🔧 Solução de Problemas

### Erro: "Chrome not found"
```bash
# Verificar se Chrome está instalado
# Windows: Procure "Google Chrome" no menu Iniciar
# Linux: sudo apt install google-chrome-stable
# Mac: https://www.google.com/chrome/

# Se der erro mesmo depois de instalar, tente reiniciar o terminal e o Python
```

### Erro: "ChromeDriver version mismatch" ou "WebDriverException"
```bash
# O projeto usa webdriver-manager que gerencia automaticamente
# Se der erro, tente:

# 1. Deletar cache de drivers
rm -r ~/.wdm -ErrorAction SilentlyContinue  # Windows

# 2. Deletar cache do Selenium
rm -r ~/.cache/webdriver-manager -ErrorAction SilentlyContinue  # Windows

# 3. Reinstalar dependências
pip install --upgrade -r requirements.txt
```

### Erro: "Module not found"
```bash
# Reinstalar dependências
pip install --upgrade -r requirements.txt
```

### Navegador não abre
```bash
# Verificar se SELENIUM_HEADLESS=false no .env.local
# Se estiver true, o navegador fica invisível
```

---

## ⚙️ Configurações Importantes

### Arquivo `.env` (criar na raiz)

```bash
# Modo local
SELENIUM_MODE=local
SELENIUM_HEADLESS=false

# Porta da API
PORT=8000
LOG_LEVEL=INFO

# Database desabilitado
DATABASE_URL=disabled
```

---

## 🔄 Como Voltar para Docker

### 1. Reverter Modificações nos Arquivos

Em cada arquivo modificado, **REMOVER** os blocos marcados com:

```python
# ============================================================
# 🔴 INÍCIO MODIFICAÇÃO LOCAL - REMOVER QUANDO VOLTAR DOCKER
# ============================================================

# ... código local ...

# ============================================================
# 🔴 FIM MODIFICAÇÃO LOCAL
# ============================================================
```

E **DESCOMENTAR** os blocos originais:

```python
# CÓDIGO ORIGINAL (DESCOMENTAR QUANDO VOLTAR DOCKER):
# ... código original ...
```

### 2. Arquivos que Precisam de Reversão

- `backend/app/config.py`
- `backend/app/rpa/driver_factory.py`
- `backend/app/db/repositories.py`
- `backend/app/services/excel_persistence.py`
- `backend/app/services/pgc_service.py`
- `backend/app/services/pncp_service.py`
- `backend/app/main.py`

### 3. Deletar Arquivos Temporários

```bash
# Deletar arquivos criados para execução local
rm run_local.py
rm README_LOCAL.md
rm -rf outputs_local/
rm -rf dados_locais_temp/
rm -rf downloads_local/
```

### 4. Voltar ao Docker

```bash
docker compose up --build
```

---

## 📊 Fluxo de Coleta

```
1. Usuário acessa http://localhost:8000/pgc
2. Clica em "Iniciar Coleta"
3. Informa ano de referência (ex: 2025)
4. Chrome abre AUTOMATICAMENTE e LOCALMENTE em sua máquina
5. Você faz LOGIN MANUALMENTE no portal (sem VNC)
6. Sistema realiza coleta automaticamente
7. Dados salvos em:
   - outputs_local/PGC_2025.xlsx (Excel)
   - dados_locais_temp/PGC_timestamp.json (temporário)
```

### Diferença de Modo LOCAL vs DOCKER:
| Aspecto | Local | Docker |
|--------|-------|--------|
| Navegador | Abre localmente na sua máquina | Acessa via noVNC (web) |
| Login | Manual no Chrome | Manual via VNC |
| Banco de dados | Desabilitado (Excel local) | PostgreSQL ativo |
| Ambiente | Sistema operacional nativo | Container isolado |

---

## ⚠️ Limitações do Modo Local

1. **Sem Postgres**: Dados não persistidos em banco (apenas Excel local)
2. **Sem noVNC**: Navegador abre localmente (não via web)
3. **Sem Docker**: Ambiente menos isolado (usa recursos da sua máquina)
4. **Chrome local**: Requer Chrome instalado na máquina
5. **Login manual**: Você faz o login normalmente, sem precisar de VNC

---

## 📞 Suporte

Se encontrar problemas:

1. Verificar se Chrome está instalado e atualizado
2. Verificar logs em tempo real na console
3. Verificar se todas as dependências foram instaladas
4. Verificar se o arquivo `.env` existe e está correto

---

**🔴 LEMBRETE: Este é um modo TEMPORÁRIO. Voltar para Docker assim que possível!**