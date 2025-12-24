-- 001_triggers.sql
-- atualizar_timestamp trigger
CREATE OR REPLACE FUNCTION atualizar_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- validar existência da função (opcional, mas mantido)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'atualizar_timestamp') THEN
        NULL;
    END IF;
END$$;

-------------------------------------------------------------------------------
-- TRIGGER: trg_atualizar_pta
-------------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_atualizar_pta'
    ) THEN
        CREATE TRIGGER trg_atualizar_pta
        BEFORE UPDATE ON PTA
        FOR EACH ROW EXECUTE FUNCTION atualizar_timestamp();
    END IF;
END;
$$;

-------------------------------------------------------------------------------
-- TRIGGER: trg_atualizar_pca
-------------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_atualizar_pca'
    ) THEN
        CREATE TRIGGER trg_atualizar_pca
        BEFORE UPDATE ON PCA
        FOR EACH ROW EXECUTE FUNCTION atualizar_timestamp();
    END IF;
END;
$$;

-------------------------------------------------------------------------------
-- TRIGGER: trg_atualizar_pncp
-------------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_atualizar_pncp'
    ) THEN
        CREATE TRIGGER trg_atualizar_pncp
        BEFORE UPDATE ON PNCP
        FOR EACH ROW EXECUTE FUNCTION atualizar_timestamp();
    END IF;
END;
$$;

-------------------------------------------------------------------------------
-- TRIGGER: trg_atualizar_processo
-------------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_atualizar_processo'
    ) THEN
        CREATE TRIGGER trg_atualizar_processo
        BEFORE UPDATE ON Processo
        FOR EACH ROW EXECUTE FUNCTION atualizar_timestamp();
    END IF;
END;
$$;

-------------------------------------------------------------------------------
-- TRIGGER: trg_atualizar_pgc
-------------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_atualizar_pgc'
    ) THEN
        CREATE TRIGGER trg_atualizar_pgc
        BEFORE UPDATE ON PGC_2025
        FOR EACH ROW EXECUTE FUNCTION atualizar_timestamp();
    END IF;
END;
$$;

-------------------------------------------------------------------------------
-- validar_dt_vigencia
-------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION validar_dt_vigencia()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.dt_vigencia IS NOT NULL AND OLD.dt_vigencia IS NOT NULL
       AND NEW.dt_vigencia < OLD.dt_vigencia THEN
        RAISE EXCEPTION 'dt_vigencia não pode ser anterior à atual (%)', OLD.dt_vigencia;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-------------------------------------------------------------------------------
-- TRIGGER: trg_dt_vigencia
-------------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_dt_vigencia'
    ) THEN
        CREATE TRIGGER trg_dt_vigencia
        BEFORE UPDATE OF dt_vigencia ON PCA
        FOR EACH ROW EXECUTE FUNCTION validar_dt_vigencia();
    END IF;
END;
$$;

-------------------------------------------------------------------------------
-- log_pca_historico
-------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION log_pca_historico()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO PCA_Historico(operacao, dados_novos)
        VALUES ('I', to_jsonb(NEW));
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO PCA_Historico(operacao, dados_antigos, dados_novos)
        VALUES ('U', to_jsonb(OLD), to_jsonb(NEW));
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO PCA_Historico(operacao, dados_antigos)
        VALUES ('D', to_jsonb(OLD));
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-------------------------------------------------------------------------------
-- TRIGGER: trg_historico_pca
-------------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_historico_pca'
    ) THEN
        CREATE TRIGGER trg_historico_pca
        AFTER INSERT OR UPDATE OR DELETE ON PCA
        FOR EACH ROW EXECUTE FUNCTION log_pca_historico();
    END IF;
END;
$$;
