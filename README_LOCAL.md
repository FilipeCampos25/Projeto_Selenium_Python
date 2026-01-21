# Guia de Execução LOCAL (Sem Docker)

🔴 **ESTE É UM MODO TEMPORÁRIO DE EXECUÇÃO**  
🔴 **PARA VOLTAR AO DOCKER, REVERTA AS MODIFICAÇÕES MARCADAS COM `🔴`**

---

## 📋 Pré-requisitos

### 1. Google Chrome
- Baixar e instalar: https://www.google.com/chrome/
- Verificar instalação: `google-chrome --version`

### 2. ChromeDriver (Opcional - Selenium pode gerenciar)
- Baixar: https://chromedriver.chromium.org/
- Colocar no PATH ou na pasta do projeto
- Verificar: `chromedriver --version`

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

# 4. Executar script de inicialização
python run_local.py
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

# 4. Criar arquivo .env (copiar do .env de exemplo)
# Copiar conteúdo do artifact "env_local"

# 5. Executar servidor
python -m backend.app.main
```

---

## 🌐 Acessar Sistema

1. **Interface Web**: http://localhost:8000/pgc
2. **API Docs**: http://localhost:8000/docs
3. **Health Check**: http://localhost:8000/api/ready

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
google-chrome --version

# Se não estiver, instalar:
# Windows: Baixar de https://www.google.com/chrome/
# Linux: sudo apt install google-chrome-stable
```

### Erro: "ChromeDriver not compatible"
```bash
# Verificar versão do Chrome
google-chrome --version

# Baixar ChromeDriver compatível
# https://chromedriver.chromium.org/downloads

# Colocar chromedriver.exe no PATH ou na pasta do projeto
```

### Erro: "Module not found"
```bash
# Reinstalar dependências
pip install --upgrade -r requirements.txt
```

### Navegador não abre
```bash
# Verificar se SELENIUM_HEADLESS=false no .env
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

# Postgres desabilitado
# DATABASE_URL=disabled
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
4. Chrome abre AUTOMATICAMENTE e VISÍVEL
5. Usuário faz LOGIN MANUAL
6. Sistema realiza coleta automaticamente
7. Dados salvos em:
   - outputs_local/PGC_2025.xlsx (Excel)
   - dados_locais_temp/PGC_timestamp.json (temporário)
```

---

## ⚠️ Limitações do Modo Local

1. **Sem Postgres**: Dados não persistidos em banco
2. **Sem noVNC**: Navegador abre localmente (não via web)
3. **Sem Docker**: Ambiente menos isolado
4. **Manual**: Requer Chrome e ChromeDriver instalados

---

## 📞 Suporte

Se encontrar problemas:

1. Verificar se Chrome está instalado e atualizado
2. Verificar logs em tempo real na console
3. Verificar se todas as dependências foram instaladas
4. Verificar se o arquivo `.env` existe e está correto

---

**🔴 LEMBRETE: Este é um modo TEMPORÁRIO. Voltar para Docker assim que possível!**