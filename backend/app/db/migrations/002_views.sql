-- 002_views.sql
-- Materialized view PGC
CREATE MATERIALIZED VIEW IF NOT EXISTS PGC AS
SELECT
    pag, dfd, requisitante, descricao, valor,
    situacao, responsaveis, pta, justificativa
FROM PGC_2025;

-- vw_pta_com_pca
CREATE OR REPLACE VIEW vw_pta_com_pca AS
SELECT
    pta.id_pta,
    pta.descricao AS descricao_pta,
    pta.ano,
    pta.classificacao,
    pta.iniciativa_anterior,
    pta.dfd AS dfd_pta,
    pta.contrato AS contrato_pta,
    pta.grupo,
    pta.situacao AS situacao_pta,
    pta.tipo AS tipo_pta,
    pta.prioridade,
    pta.demandante,
    pta.executor,
    pta.valor_ano,
    pta.investimento,
    pta.custeio,
    pta.seq,
    pta.id_pncp,
    pta.desc_pca AS desc_pca_pta,
    pta.valor_pca AS valor_pca_pta,
    pta.chave_planejamento,
    pta.status_iniciativa,
    pta.situacao_vinculacao,
    pta.criado_em AS pta_criado_em,
    pta.atualizado_em AS pta_atualizado_em,

    pca.id_pca,
    pca.descricao AS descricao_pca,
    pca.valor AS valor_pca_real,
    pca.tipo AS tipo_pca,
    pca.status AS status_pca,
    pca.observacoes,
    pca.forma_aquisicao,
    pca.processo,
    pca.dt_processo,
    pca.dt_dfd,
    pca.dt_portaria,
    pca.dt_artefato,
    pca.dt_nuconf,
    pca.dt_colic,
    pca.dt_conjur,
    pca.dt_vigencia,
    pca.execucao_estimada_2025,
    pca.valor_estimado_aquisicao,
    pca.valor_final_aquisicao,
    pca.localizacao_atribuicao,
    pca.publicacao_compra,
    pca.criado_em AS pca_criado_em,
    pca.atualizado_em AS pca_atualizado_em,

    pp.vinculo_principal,
    pp.percentual_alocacao,
    pp.observacao,
    pp.criado_em AS vinculo_criado_em
FROM PTA pta
JOIN PTA_PCA pp ON pta.id_pta = pp.id_pta AND pp.vinculo_principal = TRUE
JOIN PCA pca ON pp.id_pca = pca.id_pca;

-- vw_conflito_pca_pta
CREATE OR REPLACE VIEW vw_conflito_pca_pta AS
SELECT
    pca.id_pca,
    pca.descricao AS descricao_pca,
    pca.valor AS valor_pca_real,
    pca.processo AS processo_pca,
    pta.id_pta,
    pta.descricao AS descricao_pta,
    COALESCE(pta.valor_ano + pta.investimento + pta.custeio, 0) AS valor_pta_calculado,
    pta.valor_pca AS valor_pca_pta,
    pp.percentual_alocacao,
    ABS(pca.valor - COALESCE(pta.valor_ano + pta.investimento + pta.custeio, 0)) AS diferenca_valor
FROM PCA pca
LEFT JOIN PTA_PCA pp ON pca.id_pca = pp.id_pca AND pp.vinculo_principal = TRUE
LEFT JOIN PTA pta ON pp.id_pta = pta.id_pta
WHERE
    ABS(pca.valor - COALESCE(pta.valor_ano + pta.investimento + pta.custeio, 0)) > 0.01
    OR (pca.processo IS NOT NULL AND pp.id_pta IS NULL);
