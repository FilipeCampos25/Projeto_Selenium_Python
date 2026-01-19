"""
config_vba.py

Módulo para gerenciar o estado do "Modo Compatibilidade VBA" (Item 2).
Configurações de tempo de espera baseadas na análise do VBA original.
Implementação do Passo 16: Feature Flags para controle de implementação real vs mock.
"""
import os
import logging

logger = logging.getLogger(__name__)

# Variável global para o estado do modo de compatibilidade
_VBA_COMPAT_MODE = False

# Variável global para a Feature Flag do PNCP Real (Passo 16)
_FEATURE_PNCP_REAL = False

# Constantes de tempo de espera para o modo compatibilidade (baseado na análise do VBA)
# Estes valores simulam as esperas longas e redundantes do VBA.
VBA_COMPAT_WAIT_TIME_SECONDS = 0.5  # Simula Application.Wait Now + TimeValue("00:00:00.5")
VBA_COMPAT_SPINNER_TIMEOUT_SECONDS = 60 # Timeout longo para o spinner


class VBAConfig:
    """
    Classe de configuração para o Modo Compatibilidade VBA.
    Fornece métodos estáticos para gerenciar tempos de espera e modo de operação.
    """
    
    @staticmethod
    def get_wait_time() -> float:
        """
        Retorna o tempo de espera apropriado baseado no modo de compatibilidade.
        
        Returns:
            float: Tempo em segundos para aguardar após operações.
        """
        if is_vba_compat_mode():
            return VBA_COMPAT_WAIT_TIME_SECONDS
        else:
            # Modo otimizado: espera reduzida
            return 0.2
    
    @staticmethod
    def get_spinner_timeout() -> int:
        """
        Retorna o timeout apropriado para espera de spinner.
        
        Returns:
            int: Timeout em segundos para aguardar o spinner desaparecer.
        """
        if is_vba_compat_mode():
            return VBA_COMPAT_SPINNER_TIMEOUT_SECONDS
        else:
            # Modo otimizado: timeout reduzido
            return 30


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


def is_pncp_real_enabled() -> bool:
    """
    Verifica se a implementação real do PNCP está ativa (Passo 16).
    Pode ser controlada via variável de ambiente FEATURE_PNCP_REAL.
    """
    global _FEATURE_PNCP_REAL
    env_flag = os.getenv("FEATURE_PNCP_REAL", "false").lower() in ("true", "1", "yes")
    return _FEATURE_PNCP_REAL or env_flag


def set_pncp_real_enabled(active: bool):
    """
    Ativa ou desativa a implementação real do PNCP programaticamente.
    """
    global _FEATURE_PNCP_REAL
    _FEATURE_PNCP_REAL = active
    logger.info(f"Feature Flag PNCP_REAL {'ATIVADA' if active else 'DESATIVADA'}.")


# Por padrão, o modo compatibilidade deve ser ativado para replicar o comportamento inicial
set_vba_compat_mode(True)

# Por padrão, a implementação real inicia desativada (Mock ativo) conforme Passo 16
set_pncp_real_enabled(False)
