-- 003_test_data.sql
-- INSERT: PTA
INSERT INTO PTA (
    id_pta, descricao, ano, classificacao, iniciativa_anterior, prioridade, demandante, executor,
    valor_ano, investimento, custeio, seq, situacao_vinculacao
) VALUES (
    '001/25', 'Aquisição de equipamentos de TI para modernização', 2025,
    'Nova Contratação(objeto Novo)', NULL, NULL, 'ABCDE', NULL,
    100000.00, 110000.00, 120000.00, 1, 'Aprovado'
),
(
    '002/25', 'Construção de muro', 2025,
    'Nova Contratação(objeto Novo)', NULL, NULL, 'FGHIJ', NULL,
    150000.00, 160000.00, 170000.00, 1, 'Preparação'
);

-- INSERT: PCA
INSERT INTO PCA (
    id_pca, descricao, valor, tipo, status, observacoes, forma_aquisicao,
    processo, dt_processo, dt_dfd, dt_portaria, dt_artefato, dt_nuconf, dt_colic, dt_conjur, dt_vigencia,
    execucao_estimada_2025, valor_estimado_aquisicao, valor_final_aquisicao, publicacao_compra
) VALUES (
    '001/2025', 'Compra de servidores e storages', 120000.00,
    'Nova Contratação (Substituição de Contrato)', 'Preparação',
    'Aguardando homologação - substituição de contrato 00/00/2025',
    'PREGAO ELETRONICO',
    '99991-999999/2025-00', '2025-03-10 10:30:00', '2025-02-15', '2025-03-20 14:00:00', NULL,
    NULL, NULL, NULL, '2025-06-01 00:00:00',
    120000.00, 120000.00, NULL, '2025-03-25'
),
(
    '002/2025', 'Construção de muro perimetral', 140000.00,
    'Nova Contratação (Substituição de Contrato)', 'Concluido',
    'Aguardando homologação - substituição de contrato 00/00/2025',
    'PREGAO ELETRONICO',
    '99992-999999/2025-00', '2025-03-10 10:30:00', '2025-02-15', '2025-03-20 14:00:00', NULL,
    NULL, NULL, NULL, '2025-06-01 00:00:00',
    120000.00, 120000.00, NULL, '2025-03-25'
);

-- PTA_PCA
INSERT INTO PTA_PCA (id_pta, id_pca, vinculo_principal, percentual_alocacao)
VALUES ('001/25', '001/2025', TRUE, 100.00),
       ('002/25', '002/2025', TRUE, 100.00);

-- PNCP
INSERT INTO PNCP (
    id_pncp, id_pca, dfd, id_contratacao, descricao, categoria, valor, inicio, fim, status, status_tipo
) VALUES (
    '12345-67890-2025', '001/2025', '001/2025', '999991-999/2025',
    'Aquisição de servidores', 'Serviços', 120000.00,
    '2025-06-01', '2025-12-31', 'REPROVADA', 'REPROVADA'
),
(
    '12345-67891-2025', '002/2025', '002/2025', '999992-999/2025',
    'Construção de muro perimetral', 'Obras', 140000.00,
    '2025-06-01', '2025-12-31', 'EM_ANDAMENTO', 'VINCULADA'
);

-- Processo
INSERT INTO Processo (
    num_processo, id_pncp, area, objeto, status, recebido, tipo, inicio, fim,
    dias_conclusao, conclusao, limite_busca_sei, documentos_sem_assinatura,
    migracao_2025_solicitada
) VALUES (
    '99991-999999/2025-00', '12345-67890-2025', 'TI',
    'Aquisição de equipamentos de TI', 'EM_ANDAMENTO',
    '2025-01-15', 'PREGAO_ELETRONICO', '2025-03-10', NULL, NULL,
    '2025-04-01', NULL, 1, NULL
);

-- Licitacoes
INSERT INTO Licitacoes (
    nro_processo, numero_ano_compra, modalidade_desc, valor_total_estimado,
    valor_total_adjudicado, data_publicacao, status_desc
) VALUES (
    '99991-999999/2025-00', '00001/2025', 'Pregão Eletrônico',
    120000.00, 118000.00, '2025-03-25 09:00:00', 'Homologado'
);

-- Contratacoes
INSERT INTO Contratacoes (
    nro_processo, numero_ano_compra, numero_contrato, tipo_contrato_desc,
    valor_global, data_inicio, status_desc
) VALUES (
    '99991-999999/2025-00', '00001/2025', '110511-242',
    'Contratação de Serviços de TI', 118000.00, '2025-06-01 00:00:00', 'VIGENTE'
);

-- PGC_2025
INSERT INTO PGC_2025 (
    pta, status_pta, tipo_pta, valor_pta, ano, dfd, requisitante, descricao,
    valor, situacao, conclusao, editor, responsaveis,
    id_contratacao, desc_contratacao, tipo_contratacao, valor_pca,
    inicio, fim, status_iniciativa, acao, inclusao_dfd, nro_processo,
    tipo_status, estimado, realizado, observacoes, classificacao,
    requisitante_observacoes, contratada, id_compra, publicacao,
    status_compra, contrato, tipo_contrato, inicio_vigencia, valor_compra
) VALUES (
    '001/25', 'Aprovado', 'Nova Contratação(objeto Novo)', 100000.00, 2025, '001/2025', 'ABCDE',
    'Aquisição de equipamentos de TI para modernização', 120000.00, 'EM_ANDAMENTO', NULL, 'joao.silva',
    ARRAY['Maria', 'José'], '999991-999/2025', 'Aquisição de servidores', 'Serviços', 120000.00,
    '2025-06-01', '2025-12-31', 'VINCULADA', 'Substituição de contrato anterior', '2025-02-15',
    '99991-999999/2025-00', 'ATIVO', 120000.00, 0.00, 'Aguardando publicação no PNCP',
    'Nova Contratação(objeto Novo)', 'Urgente para modernização', FALSE, '00001/2025',
    '2025-03-25 09:00:00', 'Homologado', '110511-242', 'Contratação de Serviços de TI',
    '2025-06-01', 118000.00
);

-- Refresh materialized view PGC after inserts (safe in migrations)
REFRESH MATERIALIZED VIEW PGC;

