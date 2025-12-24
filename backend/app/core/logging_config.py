"""
Arquivo: logging_config.py
Descrição: Este arquivo faz parte do projeto e foi comentado para explicar a função de cada bloco de código.
"""

# Patched logging_config.py
# - small enhancement: include process and thread id and ISO timestamp
import logging
import time

def setup_logging():
    """
    Função setup_logging:
    Executa a lógica principal definida nesta função.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(process)d:%(thread)d | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z"
    )
