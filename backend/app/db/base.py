"""
Arquivo: base.py
Descrição: Este arquivo faz parte do projeto e foi comentado para explicar a função de cada bloco de código.
"""

# backend/app/db/base.py
"""
Módulo base importado por main.py.
Aqui definimos a Base do SQLAlchemy caso no futuro haja modelos declarativos.
No momento mantemos um placeholder simples para que importações não quebrem.
"""
from sqlalchemy.orm import declarative_base

Base = declarative_base()
