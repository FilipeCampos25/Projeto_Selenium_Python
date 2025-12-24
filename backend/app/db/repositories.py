"""
repositories.py
Repositório atualizado para suportar a Ordem de Tratamento (Item 9).
"""
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from .engine import get_engine

logger = logging.getLogger(__name__)

class ColetasRepository:
    def __init__(self):
        self._engine = get_engine()
        self._ensure_tables()

    def _ensure_tables(self):
        """Cria tabelas necessárias para o fluxo de dados (Item 9)."""
        sql = """
        CREATE TABLE IF NOT EXISTS coletas_brutas (
            id SERIAL PRIMARY KEY,
            fonte TEXT NOT NULL, -- 'PGC' ou 'PNCP'
            dados JSONB NOT NULL,
            status TEXT DEFAULT 'bruto', -- 'bruto', 'normalizado', 'validado'
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS dfds_consolidados (
            id SERIAL PRIMARY KEY,
            dfd_id TEXT UNIQUE,
            requisitante TEXT,
            descricao TEXT,
            valor NUMERIC(15,2),
            situacao TEXT,
            fonte TEXT,
            atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        try:
            with self._engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
        except Exception as e:
            logger.error(f"Erro ao criar tabelas: {e}")

    def salvar_bruto(self, fonte: str, dados: List[Dict[str, Any]]):
        """Etapa 1 e 2: Coletar tudo e armazenar com flags (Item 9)."""
        sql = text("INSERT INTO coletas_brutas (fonte, dados, status) VALUES (:fonte, :dados, 'bruto')")
        try:
            with self._engine.connect() as conn:
                conn.execute(sql, {"fonte": fonte, "dados": json.dumps(dados)})
                conn.commit()
                logger.info(f"Dados brutos de {fonte} salvos com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao salvar dados brutos: {e}")
            # Fallback para arquivo
            self._fallback_save(fonte, dados)

    def consolidar_dados(self):
        """Etapa 3 a 6: Normalizar, Deduplicação, Validar e Consolidar (Item 9)."""
        logger.info("Iniciando consolidação de dados...")
        
        # 1. Buscar dados brutos não processados
        sql_select = text("SELECT id, dados FROM coletas_brutas WHERE status = 'bruto' AND fonte = 'PGC'")
        
        try:
            with self._engine.connect() as conn:
                brutos = conn.execute(sql_select).fetchall()
                
                if not brutos:
                    logger.info("Nenhum dado bruto do PGC para processar.")
                    return
                
                for coleta_id, dados_json in brutos:
                    dados: List[Dict[str, Any]] = json.loads(dados_json)
                    
                    # 3. Normalizar (já feito no scraper, mas pode ser refinado aqui)
                    # 4. Deduplicar (simplesmente inserindo no consolidado com UNIQUE constraint)
                    # 5. Validar (assumindo que a validação semântica foi feita pelo checkpoint)
                    # 6. Consolidar
                    
                    for item in dados:
                        # Assumindo que 'dfd' é o identificador único (dfd_id)
                        sql_upsert = text("""
                            INSERT INTO dfds_consolidados (dfd_id, requisitante, descricao, valor, situacao, fonte)
                            VALUES (:dfd_id, :requisitante, :descricao, :valor, :situacao, 'PGC')
                            ON CONFLICT (dfd_id) DO UPDATE SET
                                requisitante = EXCLUDED.requisitante,
                                descricao = EXCLUDED.descricao,
                                valor = EXCLUDED.valor,
                                situacao = EXCLUDED.situacao,
                                atualizado_em = CURRENT_TIMESTAMP
                        """)
                        
                        try:
                            conn.execute(sql_upsert, {
                                "dfd_id": item.get("dfd"),
                                "requisitante": item.get("requisitante"),
                                "descricao": item.get("descricao"),
                                "valor": item.get("valor"),
                                "situacao": item.get("situacao"),
                            })
                        except SQLAlchemyError as e:
                            logger.error(f"Erro ao consolidar DFD {item.get('dfd')}: {e}")
                            # Continua para o próximo item (comportamento de "ignorar erro" do VBA - Item 10)
                            continue
                    
                    # Atualizar status da coleta bruta
                    sql_update = text("UPDATE coletas_brutas SET status = 'consolidado' WHERE id = :id")
                    conn.execute(sql_update, {"id": coleta_id})
                
                conn.commit()
                logger.info(f"Consolidação de {len(brutos)} coletas brutas concluída.")
                
        except Exception as e:
            logger.error(f"Erro fatal durante a consolidação de dados: {e}")

    def _fallback_save(self, fonte: str, dados: Any):
        path = f"/tmp/{fonte}_fallback_{int(time.time())}.json"
        with open(path, "w") as f:
            json.dump(dados, f)
        logger.warning(f"Dados salvos em fallback: {path}")

    def salvar_pncp(self, payload: Dict[str, Any]) -> Optional[int]:
        """Mantendo compatibilidade com código antigo."""
        return self.salvar_bruto("PNCP", [payload])
