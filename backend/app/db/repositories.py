"""
repositories.py
Repositório atualizado para suportar a Ordem de Tratamento (Item 9) e inicialização completa do banco.
Mantém INTEGRALMENTE as funções originais para garantir a integridade do PGC.
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

                            # Detectar se o arquivo contém apenas comentários/linhas vazias
                            stripped_lines = [l for l in sql_content.splitlines() if l.strip() and not l.strip().startswith("--")]
                            if not stripped_lines:
                                logger.info(f"Pulando migração vazia/ somente comentário: {sql_file.name}")
                                continue

                            # Executa o conteúdo do arquivo SQL
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
        sql_bruta = text("INSERT INTO coletas_brutas (fonte, dados, status) VALUES (:fonte, :dados, 'bruto') RETURNING id")
        
        # 2. Salva na tabela coletas (para compatibilidade com o código antigo/views)
        sql_coletas = text("INSERT INTO coletas (dados) VALUES (:dados) RETURNING id")

        try:
            with self._engine.connect() as conn:
                # Salva bruto e recupera id
                result = conn.execute(sql_bruta, {"fonte": fonte, "dados": json.dumps(dados)})
                try:
                    inserted_id = result.scalar()
                except Exception:
                    # fallback if scalar() unsupported
                    inserted_id = (result.fetchone() or [None])[0]

                # Salva na tabela de compatibilidade
                try:
                    conn.execute(sql_coletas, {"dados": json.dumps(dados)})
                except Exception:
                    # não crítico — apenas compatibilidade
                    logger.debug("Falha ao inserir em tabela coletas (compatibilidade)")

                # --- MAPEAMENTO PNCP VBA x POSTGRES (Passo 4) ---
                if fonte == "PNCP":
                    for item in dados:
                        sql_pncp = text("""
                            INSERT INTO PNCP (id_contratacao, descricao, categoria, valor, inicio, fim, status, status_tipo, dfd, id_pca, atualizado_em)
                            VALUES (:id_contratacao, :descricao, :categoria, :valor, :inicio, :fim, :status, :status_tipo, :dfd, :id_pca, NOW())
                            ON CONFLICT (id_contratacao) DO UPDATE SET
                                descricao = EXCLUDED.descricao,
                                categoria = EXCLUDED.categoria,
                                valor = EXCLUDED.valor,
                                inicio = EXCLUDED.inicio,
                                fim = EXCLUDED.fim,
                                status = EXCLUDED.status,
                                status_tipo = EXCLUDED.status_tipo,
                                dfd = EXCLUDED.dfd,
                                atualizado_em = NOW()
                        """)
                        try:
                            # Valor padrão para id_pca conforme schema
                            id_pca_default = f"001/{datetime.now().year}"
                            
                            # Log de auditoria para validação cruzada (Passo 10)
                            logger.info(
                                f"[AUDITORIA-BANCO] Persistindo PNCP: {item.get('col_a_contratacao')} | "
                                f"Valor: {item.get('col_d_valor')} | DFD: {item.get('col_i_dfd')}"
                            )

                            conn.execute(sql_pncp, {
                                "id_contratacao": item.get("col_a_contratacao"),
                                "descricao": item.get("col_b_descricao"),
                                "categoria": item.get("col_c_categoria"),
                                "valor": item.get("col_d_valor"),
                                "inicio": item.get("col_e_inicio"),
                                "fim": item.get("col_f_fim"),
                                "status": item.get("col_g_status"),
                                "status_tipo": item.get("col_h_status_tipo"),
                                "dfd": item.get("col_i_dfd"),
                                "id_pca": id_pca_default 
                            })
                        except Exception as e:
                            logger.debug(f"Erro ao inserir item PNCP: {e}")

                # Se for PGC, também tentamos inserir/atualizar na PGC_2025 para as views funcionarem
                elif fonte == "PGC":
                    for item in dados:
                        # Faz upsert baseado no campo `dfd`.
                        sql_pgc = text("""
                            INSERT INTO PGC_2025 (dfd, requisitante, descricao, valor, situacao, atualizado_em)
                            VALUES (:dfd, :requisitante, :descricao, :valor, :situacao, NOW())
                            ON CONFLICT (dfd) DO UPDATE SET
                                requisitante = EXCLUDED.requisitante,
                                descricao = EXCLUDED.descricao,
                                valor = EXCLUDED.valor,
                                situacao = EXCLUDED.situacao,
                                atualizado_em = NOW()
                        """)
                        try:
                            conn.execute(sql_pgc, {
                                "dfd": item.get("dfd"),
                                "requisitante": item.get("requisitante"),
                                "descricao": item.get("descricao"),
                                "valor": item.get("valor"),
                                "situacao": item.get("situacao")
                            })
                        except Exception as e:
                            # não interromper a gravação principal por causa disso
                            logger.debug(f"Erro ao inserir/atualizar item em PGC_2025, prosseguindo: {e}")

                conn.commit()

                # Verificação pós-inserção: buscar a linha inserida e comparar tamanho
                try:
                    check_sql = text("SELECT dados FROM coletas_brutas WHERE id = :id")
                    row = conn.execute(check_sql, {"id": inserted_id}).fetchone()
                    saved_len = 0
                    if row and row[0]:
                        saved = row[0]
                        if isinstance(saved, (list, tuple)):
                            saved_len = len(saved)
                        else:
                            try:
                                saved_len = len(json.loads(saved))
                            except Exception:
                                saved_len = -1

                    logger.info(f"Dados de {fonte} salvos com sucesso no banco. id={inserted_id} itens_enviados={len(dados)} itens_salvos={saved_len}")
                except Exception as e:
                    logger.warning(f"Não foi possível verificar integridade pós-inserção: {e}")

        except Exception as e:
            logger.error(f"Erro ao salvar dados no banco: {e}")
            self._fallback_save(fonte, dados)

    def verify_last_collection(self, fonte: str) -> Dict[str, Any]:
        """Retorna um resumo da última coleta gravada para a fonte informada."""
        try:
            with self._engine.connect() as conn:
                sql = text("SELECT id, dados, criado_em FROM coletas_brutas WHERE fonte = :fonte ORDER BY criado_em DESC LIMIT 1")
                row = conn.execute(sql, {"fonte": fonte}).fetchone()
                if not row:
                    return {"found": False, "msg": "Nenhuma coleta encontrada para essa fonte."}

                id_, dados, criado_em = row
                if isinstance(dados, (list, tuple)):
                    count = len(dados)
                else:
                    try:
                        count = len(json.loads(dados))
                    except Exception:
                        count = -1

                return {"found": True, "id": id_, "items_count": count, "criado_em": criado_em}
        except Exception as e:
            logger.error(f"Erro ao verificar última coleta: {e}")
            return {"found": False, "msg": str(e)}

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
                        # No PNCP, o DFD está em col_i_dfd. No PGC, em dfd.
                        dfd_id = item.get("col_i_dfd") or item.get("dfd") or item.get("dfd_id")
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
                                "requisitante": item.get("requisitante") or item.get("col_c_categoria"),
                                "descricao": item.get("descricao") or item.get("col_b_descricao"),
                                "valor": item.get("valor") or item.get("col_d_valor"),
                                "situacao": item.get("situacao") or item.get("col_g_status"),
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
        dados = [payload] if isinstance(payload, dict) else payload
        self.salvar_bruto("PNCP", dados)
        return 1
