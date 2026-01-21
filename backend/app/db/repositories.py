"""
repositories.py
Repositório adaptado para EXECUÇÃO LOCAL - Postgres DESABILITADO
Dados salvos apenas em arquivo de fallback (JSON temporário)
"""
import json
import logging
import time
import os
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class ColetasRepository:
    """
    Repositório ADAPTADO PARA EXECUÇÃO LOCAL.
    - Postgres DESABILITADO
    - Dados salvos em arquivos JSON temporários
    - Excel será gerado pelo ExcelPersistence
    """
    
    def __init__(self):
        # ============================================================
        # 🔴 INÍCIO MODIFICAÇÃO LOCAL - REMOVER QUANDO VOLTAR DOCKER
        # ============================================================
        
        logger.warning("[LOCAL] Repositório em MODO LOCAL - Postgres DESABILITADO")
        logger.warning("[LOCAL] Dados serão salvos apenas em JSON temporário")
        
        # Cria pasta para dados temporários
        self.local_data_dir = os.path.join(os.getcwd(), "dados_locais_temp")
        os.makedirs(self.local_data_dir, exist_ok=True)
        
        # NÃO INICIALIZAR ENGINE DO POSTGRES
        # self._engine = get_engine()
        # self._ensure_db_objects()
        
        # ============================================================
        # 🔴 FIM MODIFICAÇÃO LOCAL
        # ============================================================

    # ============================================================
    # 🔴 MÉTODOS MODIFICADOS PARA EXECUÇÃO LOCAL
    # ============================================================

    def salvar_bruto(self, fonte: str, dados: List[Dict[str, Any]]):
        """
        MODO LOCAL: Salva dados apenas em arquivo JSON temporário.
        Postgres DESABILITADO.
        """
        if not dados:
            logger.warning("[LOCAL] Nenhum dado para salvar")
            return
        
        # ============================================================
        # 🔴 INÍCIO MODIFICAÇÃO LOCAL
        # ============================================================
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{fonte}_{timestamp}.json"
        filepath = os.path.join(self.local_data_dir, filename)
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump({
                    "fonte": fonte,
                    "timestamp": timestamp,
                    "total_itens": len(dados),
                    "dados": dados
                }, f, ensure_ascii=False, indent=2)
            
            logger.info(f"[LOCAL] ✅ Dados salvos em: {filepath}")
            logger.info(f"[LOCAL] Total de itens: {len(dados)}")
            
        except Exception as e:
            logger.error(f"[LOCAL] ❌ Erro ao salvar arquivo JSON: {e}")
        
        # ============================================================
        # 🔴 FIM MODIFICAÇÃO LOCAL
        # ============================================================
        
        # CÓDIGO ORIGINAL POSTGRES (DESCOMENTAR QUANDO VOLTAR DOCKER):
        # sql_bruta = text("INSERT INTO coletas_brutas ...")
        # with self._engine.connect() as conn:
        #     result = conn.execute(sql_bruta, ...)
        #     conn.commit()

    def consolidar_dados(self):
        """
        MODO LOCAL: Consolidação desabilitada (sem Postgres).
        """
        # ============================================================
        # 🔴 INÍCIO MODIFICAÇÃO LOCAL
        # ============================================================
        
        logger.warning("[LOCAL] Consolidação desabilitada - apenas Excel será gerado")
        return
        
        # ============================================================
        # 🔴 FIM MODIFICAÇÃO LOCAL
        # ============================================================
        
        # CÓDIGO ORIGINAL (DESCOMENTAR QUANDO VOLTAR DOCKER):
        # logger.info("Iniciando consolidação de dados...")
        # sql_select = text("SELECT id, dados, fonte FROM coletas_brutas ...")
        # ...

    def verify_last_collection(self, fonte: str) -> Dict[str, Any]:
        """
        MODO LOCAL: Verifica último arquivo JSON salvo.
        """
        # ============================================================
        # 🔴 INÍCIO MODIFICAÇÃO LOCAL
        # ============================================================
        
        try:
            arquivos = [f for f in os.listdir(self.local_data_dir) 
                       if f.startswith(fonte) and f.endswith(".json")]
            
            if not arquivos:
                return {"found": False, "msg": "Nenhuma coleta encontrada"}
            
            ultimo = sorted(arquivos)[-1]
            filepath = os.path.join(self.local_data_dir, ultimo)
            
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            return {
                "found": True,
                "arquivo": ultimo,
                "items_count": data.get("total_itens", 0),
                "timestamp": data.get("timestamp")
            }
            
        except Exception as e:
            return {"found": False, "msg": str(e)}
        
        # ============================================================
        # 🔴 FIM MODIFICAÇÃO LOCAL
        # ============================================================

    def salvar_pncp(self, payload: Dict[str, Any]) -> Optional[int]:
        """
        Compatibilidade - redireciona para salvar_bruto
        """
        dados = [payload] if isinstance(payload, dict) else payload
        self.salvar_bruto("PNCP", dados)
        return 1
    
    # ============================================================
    # 🔴 MÉTODOS ORIGINAIS COMENTADOS (POSTGRES)
    # ============================================================
    
    # def _ensure_db_objects(self):
    #     """POSTGRES - Descomentar quando voltar Docker"""
    #     pass
    
    # def _create_basic_tables(self, conn=None):
    #     """POSTGRES - Descomentar quando voltar Docker"""
    #     pass
    
    # def _fallback_save(self, fonte: str, dados: Any):
    #     """POSTGRES - Descomentar quando voltar Docker"""
    #     pass