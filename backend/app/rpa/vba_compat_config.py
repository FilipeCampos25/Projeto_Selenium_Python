"""
vba_compat_config.py

Módulo para gerenciar o estado do "Modo Compatibilidade VBA" (Item 2).
"""
import os
import logging

logger = logging.getLogger(__name__)

# Variável global para o estado do modo de compatibilidade
_VBA_COMPAT_MODE = False

# Constantes de tempo de espera para o modo compatibilidade (baseado na análise do VBA)
# Estes valores simulam as esperas longas e redundantes do VBA.
VBA_COMPAT_WAIT_TIME_SECONDS = 0.5  # Simula Application.Wait Now + TimeValue("00:00:00.5")
VBA_COMPAT_SPINNER_TIMEOUT_SECONDS = 60 # Timeout longo para o spinner

def is_vba_compat_mode() -> bool:
    """
    Verifica se o Modo Compatibilidade VBA está ativo.
    Pode ser ativado via variável de ambiente ou programaticamente.
    """
    global _VBA_COMPAT_MODE
    # Prioriza a variável de ambiente para fácil controle externo
    env_mode = os.getenv("VBA_COMPAT_MODE", "false").lower() in ("true", "1", "yes")
    return _VBA_COMPAT_MODE or env_mode

def set_vba_compat_mode(active: bool):
    """
    Ativa ou desativa o Modo Compatibilidade VBA programaticamente.
    """
    global _VBA_COMPAT_MODE
    _VBA_COMPAT_MODE = active
    logger.info(f"Modo Compatibilidade VBA {'ATIVADO' if active else 'DESATIVADO'}.")

# Por padrão, o modo deve ser ativado para replicar o comportamento inicial
set_vba_compat_mode(True)
