"""
config_vba.py

Módulo para gerenciar o estado do "Modo Compatibilidade VBA" (Item 2).
Configurações de tempo de espera baseadas na análise do VBA original.
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


# Por padrão, o modo deve ser ativado para replicar o comportamento inicial
set_vba_compat_mode(True)