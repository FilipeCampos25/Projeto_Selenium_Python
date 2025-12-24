"""
Arquivo: pncp_downloader.py
Descrição: Este arquivo faz parte do projeto e foi comentado para explicar a função de cada bloco de código.
"""

# pncp_downloader.py (trecho final / entrypoint)
if __name__ == "__main__":
    import argparse
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    import time
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", action="store_true", help="Rodar sem UI (não recomendado para login manual)")
    parser.add_argument("--wait-after-login", type=int, default=3, help="Segundos para aguardar após confirmação de login")
    args = parser.parse_args()

    chrome_opts = Options()
    if args.headless:
        chrome_opts.add_argument("--headless=new")
    # configurar opções que o projeto já usa (downloads, perfil, etc)
    driver = webdriver.Chrome(options=chrome_opts)

    # Abre a página de login
    driver.get("https://pncp.gov.br/")  # ajuste para a URL de login correta
    print("\n=== AÇÃO REQUERIDA: faça o login MANUALMENTE no browser que abriu ===")
    input("Quando terminar o login e a página estiver pronto, pressione Enter aqui para continuar...")

    # opcional: esperar alguns segundos depois do Enter
    time.sleep(args.wait_after_login)

    # Agora chame a classe/fluxo principal do scraper (exemplo)
    try:
        from pncp_scraper import PncpScraper  # ajuste o import conforme seu projeto
        scraper = PncpScraper(driver=driver, headless=not args.headless)
        scraper.run()  # método que percorre páginas/itens — mantenha sleeps internos
    except Exception as e:
        print("Erro ao iniciar o scraper:", e)
        driver.quit()
        raise
