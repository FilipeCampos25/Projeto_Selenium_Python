"""
run_local.py
Script de inicialização para EXECUÇÃO LOCAL (sem Docker)

🔴 ARQUIVO CRIADO PARA EXECUÇÃO LOCAL
🔴 DELETAR QUANDO VOLTAR PARA DOCKER

COMO USAR:
1. Certifique-se que está no ambiente virtual (venv)
2. Execute: python run_local.py
3. Acesse: http://localhost:8000
"""

import sys
import os
import subprocess
from pathlib import Path

# Cores para terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header():
    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("=" * 70)
    print(" Sistema de Coleta PGC/PNCP - MODO LOCAL (SEM DOCKER)")
    print("=" * 70)
    print(f"{Colors.ENDC}")

def check_chrome():
    """Verifica se o Chrome está instalado"""
    print(f"{Colors.OKCYAN}[1/4] Verificando Google Chrome...{Colors.ENDC}")
    
    try:
        # Tenta executar chrome --version
        result = subprocess.run(
            ["google-chrome", "--version"], 
            capture_output=True, 
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"{Colors.OKGREEN}✓ Chrome encontrado: {result.stdout.strip()}{Colors.ENDC}")
            return True
    except:
        pass
    
    # Tenta alternativas
    for cmd in ["chrome", "chromium", "chromium-browser"]:
        try:
            result = subprocess.run(
                [cmd, "--version"], 
                capture_output=True, 
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"{Colors.OKGREEN}✓ Chrome encontrado: {result.stdout.strip()}{Colors.ENDC}")
                return True
        except:
            continue
    
    print(f"{Colors.FAIL}✗ Google Chrome NÃO encontrado!{Colors.ENDC}")
    print(f"{Colors.WARNING}Por favor, instale o Google Chrome antes de continuar.{Colors.ENDC}")
    return False

def check_chromedriver():
    """Verifica se o ChromeDriver está no PATH"""
    print(f"{Colors.OKCYAN}[2/4] Verificando ChromeDriver...{Colors.ENDC}")
    
    try:
        result = subprocess.run(
            ["chromedriver", "--version"], 
            capture_output=True, 
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"{Colors.OKGREEN}✓ ChromeDriver encontrado: {result.stdout.strip()}{Colors.ENDC}")
            return True
    except:
        pass
    
    print(f"{Colors.WARNING}⚠ ChromeDriver NÃO encontrado no PATH{Colors.ENDC}")
    print(f"{Colors.WARNING}O Selenium tentará gerenciar automaticamente.{Colors.ENDC}")
    print(f"{Colors.WARNING}Se houver erros, baixe manualmente em: https://chromedriver.chromium.org/{Colors.ENDC}")
    return True  # Não bloquear, Selenium pode gerenciar

def check_dependencies():
    """Verifica se as dependências Python estão instaladas"""
    print(f"{Colors.OKCYAN}[3/4] Verificando dependências Python...{Colors.ENDC}")
    
    required = [
        "fastapi",
        "uvicorn",
        "selenium",
        "openpyxl",
        "pydantic"
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"{Colors.FAIL}✗ Dependências faltando: {', '.join(missing)}{Colors.ENDC}")
        print(f"{Colors.WARNING}Execute: pip install -r requirements.txt{Colors.ENDC}")
        return False
    
    print(f"{Colors.OKGREEN}✓ Todas as dependências estão instaladas{Colors.ENDC}")
    return True

def create_folders():
    """Cria pastas necessárias"""
    print(f"{Colors.OKCYAN}[4/4] Criando pastas necessárias...{Colors.ENDC}")
    
    folders = [
        "outputs_local",
        "dados_locais_temp",
        "downloads_local"
    ]
    
    for folder in folders:
        path = Path(folder)
        path.mkdir(exist_ok=True)
        print(f"{Colors.OKGREEN}✓ Pasta criada/verificada: {folder}{Colors.ENDC}")

def print_instructions():
    """Imprime instruções de uso"""
    print(f"\n{Colors.OKGREEN}{Colors.BOLD}Sistema pronto para iniciar!{Colors.ENDC}\n")
    print(f"{Colors.OKCYAN}Instruções:{Colors.ENDC}")
    print(f"  1. O servidor FastAPI será iniciado em: {Colors.BOLD}http://localhost:8000{Colors.ENDC}")
    print(f"  2. Acesse a interface web: {Colors.BOLD}http://localhost:8000/pgc{Colors.ENDC}")
    print(f"  3. O navegador Chrome abrirá automaticamente (VISÍVEL)")
    print(f"  4. Faça o login manualmente quando solicitado")
    print(f"  5. Os arquivos Excel serão salvos em: {Colors.BOLD}./outputs_local/{Colors.ENDC}")
    print(f"\n{Colors.WARNING}Pressione Ctrl+C para parar o servidor{Colors.ENDC}\n")

def run_server():
    """Executa o servidor FastAPI"""
    try:
        # Importa e executa o app
        import uvicorn
        from backend.app.main import app
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Servidor parado pelo usuário{Colors.ENDC}")
    except Exception as e:
        print(f"\n{Colors.FAIL}Erro ao iniciar servidor: {e}{Colors.ENDC}")
        sys.exit(1)

def main():
    print_header()
    
    # Verificações
    if not check_chrome():
        sys.exit(1)
    
    check_chromedriver()
    
    if not check_dependencies():
        sys.exit(1)
    
    create_folders()
    
    # Instruções
    print_instructions()
    
    # Aguarda confirmação
    try:
        input(f"{Colors.BOLD}Pressione ENTER para iniciar o servidor...{Colors.ENDC}")
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Cancelado pelo usuário{Colors.ENDC}")
        sys.exit(0)
    
    # Inicia servidor
    print(f"\n{Colors.OKGREEN}Iniciando servidor...{Colors.ENDC}\n")
    run_server()

if __name__ == "__main__":
    main()