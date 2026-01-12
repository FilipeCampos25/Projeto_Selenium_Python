"""
repositories.py
Repositório atualizado para suportar a Ordem de Tratamento (Item 9) e inicialização completa do banco.
"""
import json
import logging
import time
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from pathlib import Path
from .engine import get_engine

logger = logging.getLogger(__name__)

class ColetasRepository:
    def __init__(self):
        self._engine = get_engine()
        self._ensure_db_objects()

    def _ensure_db_objects(self):
        """
        Garante que todos os objetos do banco (tabelas, triggers, views) sejam criados
        lendo os arquivos SQL na pasta migrations/.
        """
        logger.info("Iniciando verificação/criação de objetos do banco de dados...")
        
        # Caminho para a pasta de migrações
        migrations_dir = Path(__file__).parent / "migrations"
        
        if not migrations_dir.exists():
            logger.error(f"Diretório de migrações não encontrado: {migrations_dir}")
            # Fallback para as tabelas básicas se as migrações sumirem
            self._create_basic_tables()
            return

        # Lista e ordena os arquivos .sql
        sql_files = sorted(migrations_dir.glob("*.sql"))
        
        try:
            with self._engine.connect() as conn:
                for sql_file in sql_files:
                    logger.info(f"Aplicando migração: {sql_file.name}")
                    try:
                        with open(sql_file, 'r', encoding='utf-8') as f:
                            sql_content = f.read()
                            # Executa o conteúdo do arquivo SQL
                            # Usamos text() para envolver o SQL e conn.execute
                            # Nota: Alguns scripts complexos com múltiplos comandos podem precisar ser divididos
                            # mas o SQLAlchemy lida bem com múltiplos comandos em uma string no Postgres.
                            conn.execute(text(sql_content))
                            conn.commit()
                            logger.info(f"Migração {sql_file.name} aplicada com sucesso.")
                    except Exception as e:
                        logger.error(f"Erro ao aplicar migração {sql_file.name}: {e}")
                        conn.rollback()
                
                # Garante que as tabelas de controle de coleta também existam
                self._create_basic_tables(conn)
                conn.commit()
                
        except Exception as e:
            logger.error(f"Erro fatal na inicialização do banco: {e}")

    def _create_basic_tables(self, conn=None):
        """Cria tabelas de controle de coleta se não existirem."""
        sql = """
        CREATE TABLE IF NOT EXISTS coletas_brutas (
            id SERIAL PRIMARY KEY,
            fonte TEXT NOT NULL, -- 'PGC' ou 'PNCP'
            dados JSONB NOT NULL,
            status TEXT DEFAULT 'bruto', -- 'bruto', 'consolidado'
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
        if conn:
            conn.execute(text(sql))
        else:
            with self._engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()

    def salvar_bruto(self, fonte: str, dados: List[Dict[str, Any]]):
        """Salva os dados coletados na tabela coletas_brutas e também na tabela coletas (compatibilidade)."""
        if not dados:
            return

        # 1. Salva na tabela coletas_brutas (para o novo fluxo de consolidação)
        sql_bruta = text("INSERT INTO coletas_brutas (fonte, dados, status) VALUES (:fonte, :dados, 'bruto')")
        
        # 2. Salva na tabela coletas (para compatibilidade com o código antigo/views)
        sql_coletas = text("INSERT INTO coletas (dados) VALUES (:dados)")

        try:
            with self._engine.connect() as conn:
                # Salva bruto
                conn.execute(sql_bruta, {"fonte": fonte, "dados": json.dumps(dados)})
                
                # Salva na tabela de compatibilidade
                conn.execute(sql_coletas, {"dados": json.dumps(dados)})
                
                # Se for PGC, também tentamos inserir/atualizar na PGC_2025 para as views funcionarem
                if fonte == "PGC":
                    for item in dados:
                        sql_pgc = text("""
                            INSERT INTO PGC_2025 (dfd, requisitante, descricao, valor, situacao, atualizado_em)
                            VALUES (:dfd, :requisitante, :descricao, :valor, :situacao, NOW())
                            ON CONFLICT DO NOTHING
                        """)
                        # Nota: PGC_2025 não tem PK clara no SQL original (usa SERIAL pag), 
                        # então o ON CONFLICT aqui é ilustrativo ou precisaria de uma UK em dfd.
                        try:
                            conn.execute(sql_pgc, {
                                "dfd": item.get("dfd"),
                                "requisitante": item.get("requisitante"),
                                "descricao": item.get("descricao"),
                                "valor": item.get("valor"),
                                "situacao": item.get("situacao")
                            })
                        except:
                            pass

                conn.commit()
                logger.info(f"Dados de {fonte} salvos com sucesso no banco.")
        except Exception as e:
            logger.error(f"Erro ao salvar dados no banco: {e}")
            self._fallback_save(fonte, dados)

    def consolidar_dados(self):
        """Processa dados da coletas_brutas para dfds_consolidados."""
        logger.info("Iniciando consolidação de dados...")
        
        sql_select = text("SELECT id, dados, fonte FROM coletas_brutas WHERE status = 'bruto'")
        
        try:
            with self._engine.connect() as conn:
                result = conn.execute(sql_select)
                rows = result.fetchall()
                
                if not rows:
                    logger.info("Nenhum dado bruto para processar.")
                    return
                
                for row_id, dados_json, fonte in rows:
                    dados = dados_json if isinstance(dados_json, list) else json.loads(dados_json)
                    
                    for item in dados:
                        # Identificador único pode variar por fonte, mas 'dfd' é comum
                        dfd_id = item.get("dfd") or item.get("dfd_id")
                        if not dfd_id: continue

                        sql_upsert = text("""
                            INSERT INTO dfds_consolidados (dfd_id, requisitante, descricao, valor, situacao, fonte)
                            VALUES (:dfd_id, :requisitante, :descricao, :valor, :situacao, :fonte)
                            ON CONFLICT (dfd_id) DO UPDATE SET
                                requisitante = EXCLUDED.requisitante,
                                descricao = EXCLUDED.descricao,
                                valor = EXCLUDED.valor,
                                situacao = EXCLUDED.situacao,
                                fonte = EXCLUDED.fonte,
                                atualizado_em = CURRENT_TIMESTAMP
                        """)
                        
                        try:
                            conn.execute(sql_upsert, {
                                "dfd_id": dfd_id,
                                "requisitante": item.get("requisitante"),
                                "descricao": item.get("descricao"),
                                "valor": item.get("valor"),
                                "situacao": item.get("situacao"),
                                "fonte": fonte
                            })
                        except SQLAlchemyError as e:
                            logger.error(f"Erro ao consolidar item {dfd_id}: {e}")
                    
                    # Atualizar status
                    conn.execute(text("UPDATE coletas_brutas SET status = 'consolidado' WHERE id = :id"), {"id": row_id})
                
                conn.commit()
                logger.info(f"Consolidação concluída.")
                
        except Exception as e:
            logger.error(f"Erro na consolidação: {e}")

    def _fallback_save(self, fonte: str, dados: Any):
        os.makedirs("/tmp/coletas", exist_ok=True)
        path = f"/tmp/coletas/{fonte}_fallback_{int(time.time())}.json"
        try:
            with open(path, "w") as f:
                json.dump(dados, f)
            logger.warning(f"Dados salvos em fallback: {path}")
        except Exception as e:
            logger.error(f"Falha crítica no fallback: {e}")

    def salvar_pncp(self, payload: Dict[str, Any]) -> Optional[int]:
        """Mantendo compatibilidade."""
        # Se o payload for um dicionário único (resultado do scraper PNCP), envolvemos em lista
        dados = [payload] if isinstance(payload, dict) else payload
        self.salvar_bruto("PNCP", dados)
        return 1
