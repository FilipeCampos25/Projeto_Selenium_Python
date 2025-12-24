"""
Arquivo: pages.py
Descrição: Este arquivo faz parte do projeto e foi comentado para explicar a função de cada bloco de código.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

router = APIRouter()

# Esta variável SERÁ injetada pelo main.py
templates = None


@router.get("/", response_class=HTMLResponse)
def root_redirect():
    """
    Função root_redirect:
    Executa a lógica principal definida nesta função.
    """
    """
    Redireciona a raiz do router para a página principal.
    """
    return RedirectResponse(url="/pgc")


@router.get("/pgc", response_class=HTMLResponse)
def pagina_pgc(request: Request):
    """
    Função pagina_pgc:
    Executa a lógica principal definida nesta função.
    """
    """
    Página inicial do sistema PGC.
    """
    if templates is None:
        # Erro explícito para não mascarar problema de configuração
        raise RuntimeError(
            "Jinja2Templates não foi configurado. "
            "Verifique a injeção no main.py."
        )

    return templates.TemplateResponse(
        "pgn_inicial.html",
        {"request": request}
    )
