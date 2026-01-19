"""
config_vba.py

Módulo para gerenciar o estado do "Modo Compatibilidade VBA" (Item 2).
Configurações de tempo de espera baseadas na análise do VBA original.
Implementação do Passo 20: Ativação definitiva da implementação real.
"""
import os
import logging

logger = logging.getLogger(__name__)

# Variável global para o estado do modo de compatibilidade
_VBA_COMPAT_MODE = False

# Variável global para a Feature Flag do PNCP Real (Passo 16/20)
# PASSO 20: Alterado para True por padrão após validação completa.
_FEATURE_PNCP_REAL = True

# Constantes de tempo de espera para o modo compatibilidade (baseado na análise do VBA)
VBA_COMPAT_WAIT_TIME_SECONDS = 0.5  
VBA_COMPAT_SPINNER_TIMEOUT_SECONDS = 60 


class VBAConfig:
    """
    Classe de configuração para o Modo Compatibilidade VBA.
    """
    
    @staticmethod
    def get_wait_time() -> float:
        if is_vba_compat_mode():
            return VBA_COMPAT_WAIT_TIME_SECONDS
        else:
            return 0.2
    
    @staticmethod
    def get_spinner_timeout() -> int:
        if is_vba_compat_mode():
            return VBA_COMPAT_SPINNER_TIMEOUT_SECONDS
        else:
            return 30


def is_vba_compat_mode() -> bool:
    """Verifica se o Modo Compatibilidade VBA está ativo."""
    global _VBA_COMPAT_MODE
    env_mode = os.getenv("VBA_COMPAT_MODE", "false").lower() in ("true", "1", "yes")
    return _VBA_COMPAT_MODE or env_mode


def set_vba_compat_mode(active: bool):
    """Ativa ou desativa o Modo Compatibilidade VBA programaticamente."""
    global _VBA_COMPAT_MODE
    _VBA_COMPAT_MODE = active
    logger.info(f"Modo Compatibilidade VBA {'ATIVADO' if active else 'DESATIVADO'}.")


def is_pncp_real_enabled() -> bool:
    """
    Verifica se a implementação real do PNCP está ativa (Passo 16/20).
    Prioriza a variável de ambiente FEATURE_PNCP_REAL se definida.
    """
    global _FEATURE_PNCP_REAL
    env_flag = os.getenv("FEATURE_PNCP_REAL")
    if env_flag is not None:
        return env_flag.lower() in ("true", "1", "yes")
    return _FEATURE_PNCP_REAL


def set_pncp_real_enabled(active: bool):
    """Ativa ou desativa a implementação real do PNCP programaticamente."""
    global _FEATURE_PNCP_REAL
    _FEATURE_PNCP_REAL = active
    logger.info(f"Feature Flag PNCP_REAL {'ATIVADA' if active else 'DESATIVADA'}.")


# Por padrão, o modo compatibilidade deve ser ativado para replicar o comportamento inicial
set_vba_compat_mode(True)

# PASSO 20: Implementação real agora é o padrão do sistema.
set_pncp_real_enabled(True)
