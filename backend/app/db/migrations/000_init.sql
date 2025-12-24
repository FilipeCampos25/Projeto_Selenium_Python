-- 000_init.sql
-- Full DDL for projeto reestruturado
-- PTA
CREATE TABLE IF NOT EXISTS PTA (
    id_pta VARCHAR(6) PRIMARY KEY CHECK (id_pta ~ '^\d{3}/\d{2}$'),
    descricao TEXT,
    ano INT NOT NULL CHECK (ano >= 2020),
    classificacao VARCHAR(100),
    iniciativa_anterior VARCHAR(6),
    dfd VARCHAR(9) CHECK (dfd ~ '^\d{3}/2025$' OR dfd IS NULL),
    contrato VARCHAR(15),
    grupo VARCHAR(50),
    situacao VARCHAR(50),
    tipo VARCHAR(50),
    prioridade VARCHAR(20),
    demandante VARCHAR(100),
    executor VARCHAR(100),
    valor_ano DECIMAL(15,2),
    investimento DECIMAL(15,2),
    custeio DECIMAL(15,2),
    seq INT,
    id_pncp VARCHAR(17) CHECK (id_pncp ~ '^\d{5}-\d{5}-\d{4}$' OR id_pncp IS NULL),
    desc_pca TEXT,
    valor_pca DECIMAL(15,2),
    chave_planejamento VARCHAR(50),
    status_iniciativa VARCHAR(50),
    situacao_vinculacao VARCHAR(50),
    criado_em TIMESTAMP DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW()
);

-- PCA
CREATE TABLE IF NOT EXISTS PCA (
    id_pca VARCHAR(8) PRIMARY KEY CHECK (id_pca ~ '^\d{3}/2025$'),
    descricao TEXT NOT NULL,
    valor DECIMAL(15,2) NOT NULL,
    tipo VARCHAR(100),
    status VARCHAR(50) NOT NULL DEFAULT 'Preparação',
    observacoes TEXT,
    forma_aquisicao VARCHAR(50),
    processo VARCHAR(20) UNIQUE CHECK (processo ~ '^\d{5}-\d{6}/2025-\d{2}$' OR processo IS NULL),
    dt_processo TIMESTAMP,
    dt_dfd DATE,
    dt_portaria TIMESTAMP,
    dt_artefato TIMESTAMP,
    dt_nuconf TIMESTAMP,
    dt_colic TIMESTAMP,
    dt_conjur TIMESTAMP,
    dt_vigencia TIMESTAMP,
    execucao_estimada_2025 DECIMAL(15,2),
    valor_estimado_aquisicao DECIMAL(15,2),
    valor_final_aquisicao DECIMAL(15,2),
    localizacao_atribuicao VARCHAR(100),
    publicacao_compra DATE,
    criado_em TIMESTAMP DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pca_dt_vigencia_desc ON PCA(dt_vigencia DESC NULLS LAST);

-- PTA_PCA
CREATE TABLE IF NOT EXISTS PTA_PCA (
    id_pta VARCHAR(6) REFERENCES PTA(id_pta) ON DELETE CASCADE,
    id_pca VARCHAR(8) REFERENCES PCA(id_pca) ON DELETE CASCADE,
    vinculo_principal BOOLEAN DEFAULT FALSE,
    percentual_alocacao DECIMAL(5,2) DEFAULT 100.00 CHECK (percentual_alocacao BETWEEN 0 AND 100),
    observacao TEXT,
    criado_em TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (id_pta, id_pca)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_pta_principal ON PTA_PCA(id_pta) WHERE vinculo_principal = TRUE;

-- PNCP
CREATE TABLE IF NOT EXISTS PNCP (
    id_pncp VARCHAR(17) PRIMARY KEY CHECK (id_pncp ~ '^\d{5}-\d{5}-\d{4}$'),
    id_pca VARCHAR(8) NOT NULL UNIQUE REFERENCES PCA(id_pca) ON DELETE CASCADE,
    dfd VARCHAR(9) NOT NULL CHECK (dfd ~ '^\d{3}/2025$'),
    id_contratacao VARCHAR(15),
    descricao TEXT,
    categoria VARCHAR(50),
    valor DECIMAL(15,2),
    inicio DATE,
    fim DATE,
    status VARCHAR(50),
    status_tipo VARCHAR(50),
    criado_em TIMESTAMP DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pncp_dfd ON PNCP(dfd);

-- Processo
CREATE TABLE IF NOT EXISTS Processo (
    num_processo VARCHAR(20) PRIMARY KEY CHECK (num_processo ~ '^\d{5}-\d{6}/2025-\d{2}$'),
    id_pncp VARCHAR(17) UNIQUE REFERENCES PNCP(id_pncp) ON DELETE CASCADE,
    area VARCHAR(50),
    objeto TEXT,
    status VARCHAR(50),
    recebido DATE,
    tipo VARCHAR(100),
    inicio DATE,
    fim DATE,
    dias_conclusao INT,
    conclusao TIMESTAMP,
    pgc_dfd VARCHAR(9),
    limite_busca_sei DATE,
    documentos_sem_assinatura INT DEFAULT 0,
    restricoes TEXT,
    migracao_2025_solicitada BOOLEAN DEFAULT FALSE,
    data_dfd DATE,
    criado_em TIMESTAMP DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_processo_status ON Processo(status);

-- PGC_2025
CREATE TABLE IF NOT EXISTS PGC_2025 (
    pag SERIAL PRIMARY KEY,
    pta VARCHAR(6) REFERENCES PTA(id_pta) ON DELETE SET NULL,
    status_pta VARCHAR(50),
    tipo_pta VARCHAR(50),
    valor_pta DECIMAL(15,2),
    ano INT,
    dfd VARCHAR(9),
    requisitante VARCHAR(100),
    descricao TEXT,
    valor DECIMAL(15,2),
    situacao VARCHAR(50),
    conclusao TIMESTAMP,
    editor VARCHAR(100),
    responsaveis TEXT[],
    id_contratacao VARCHAR(15),
    desc_contratacao TEXT,
    tipo_contratacao VARCHAR(50),
    valor_pca DECIMAL(15,2),
    inicio DATE,
    fim DATE,
    status_iniciativa VARCHAR(50),
    acao TEXT,
    inclusao_dfd DATE,
    nro_processo VARCHAR(20) REFERENCES Processo(num_processo) ON DELETE SET NULL,
    tipo_status VARCHAR(50),
    estimado DECIMAL(15,2),
    realizado DECIMAL(15,2),
    observacoes TEXT,
    justificativa TEXT,
    classificacao VARCHAR(100),
    requisitante_observacoes TEXT,
    contratada BOOLEAN,
    id_compra VARCHAR(20),
    publicacao TIMESTAMP,
    status_compra VARCHAR(50),
    contrato VARCHAR(15),
    tipo_contrato VARCHAR(50),
    inicio_vigencia DATE,
    valor_compra DECIMAL(15,2),
    atualizado_em TIMESTAMP DEFAULT NOW()
);

-- Licitacoes
CREATE TABLE IF NOT EXISTS Licitacoes (
    nro_processo VARCHAR(20) REFERENCES Processo(num_processo) ON DELETE CASCADE,
    numero_ano_compra VARCHAR(10),
    modalidade_desc VARCHAR(100),
    valor_total_estimado DECIMAL(15,2),
    valor_total_adjudicado DECIMAL(15,2),
    data_publicacao TIMESTAMP,
    status_desc VARCHAR(100),
    PRIMARY KEY (nro_processo, numero_ano_compra)
);

-- Contratacoes
CREATE TABLE IF NOT EXISTS Contratacoes (
    nro_processo VARCHAR(20) REFERENCES Processo(num_processo) ON DELETE CASCADE,
    numero_ano_compra VARCHAR(10),
    numero_contrato VARCHAR(15),
    tipo_contrato_desc VARCHAR(100),
    valor_global DECIMAL(15,2),
    data_inicio TIMESTAMP,
    status_desc VARCHAR(50),
    PRIMARY KEY (nro_processo, numero_contrato)
);

CREATE INDEX IF NOT EXISTS idx_licitacoes_processo ON Licitacoes(nro_processo);

-- PCA_Historico
CREATE TABLE IF NOT EXISTS PCA_Historico (
    id SERIAL PRIMARY KEY,
    operacao CHAR(1) CHECK (operacao IN ('I','U','D')),
    data_op TIMESTAMP DEFAULT NOW(),
    usuario VARCHAR(50) DEFAULT CURRENT_USER,
    dados_antigos JSONB,
    dados_novos JSONB
);

-- Sequence for gerar_dfd
CREATE SEQUENCE IF NOT EXISTS seq_dfd_2025 START 1;
