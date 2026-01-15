-- 005_upsert_pgc.sql
-- Garante que exista uma restrição/índice único em PGC_2025(dfd)
-- para permitir operações de upsert baseadas em `dfd`.

DO $$
BEGIN
    -- Cria índice único se não existir
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes WHERE tablename = 'pgc_2025' AND indexname = 'uq_pgc_dfd'
    ) THEN
        CREATE UNIQUE INDEX uq_pgc_dfd ON PGC_2025(dfd);
    END IF;
END$$;

-- Observação: se o projeto preferir outra coluna como chave de identidade
-- (ex.: dfd + requisitante), altere o índice e o SQL de upsert em repositories.py.
