-- 004_coletas.sql
-- Cria tabela coletas para armazenar JSON da coleta completa
CREATE TABLE IF NOT EXISTS coletas (
  id SERIAL PRIMARY KEY,
  dados JSONB NOT NULL,
  criado_em TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() at time zone 'utc')
);

CREATE INDEX IF NOT EXISTS idx_coletas_criado_em ON coletas (criado_em);
