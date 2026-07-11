-- =============================================================================
-- 0_criar_banco.sql
-- Desafio: Pipeline de Dados - Viagens a Servico (Portal da Transparencia)
-- Arquitetura Medallion: camadas RAW e SILVER
-- SGBD: PostgreSQL
-- =============================================================================
-- Como rodar:
--   1. Crie o database (ex.: CREATE DATABASE transparencia;) ou garanta que o
--      database configurado no .env (POSTGRES_DATABASE) ja existe.
--   2. Rode este script conectado a esse database:
--      psql -h localhost -U postgres -d transparencia -f 0_criar_banco.sql
-- =============================================================================


-- =============================================================================
-- CAMADA RAW
-- Copia fiel dos CSVs: todas as colunas VARCHAR, sem constraints (nem PK/FK).
-- Os nomes de coluna abaixo espelham as colunas originais do CSV (em snake_case).
-- =============================================================================

DROP TABLE IF EXISTS raw_viagem;
CREATE TABLE raw_viagem (
    id_processo_viagem         VARCHAR(50),
    num_proposta                VARCHAR(50),
    situacao                    VARCHAR(50),
    viagem_urgente               VARCHAR(10),
    justificativa_urgencia       VARCHAR(4000),
    cod_orgao_superior            VARCHAR(50),
    nome_orgao_superior           VARCHAR(255),
    cod_orgao_solicitante         VARCHAR(50),
    nome_orgao_solicitante         VARCHAR(255),
    cpf_viajante                 VARCHAR(50),
    nome_viajante                 VARCHAR(255),
    cargo                        VARCHAR(255),
    funcao                       VARCHAR(255),
    descricao_funcao              VARCHAR(255),
    data_inicio                  VARCHAR(20),
    data_fim                     VARCHAR(20),
    destinos                     VARCHAR(4000),
    motivo                       VARCHAR(4000),
    valor_diarias                 VARCHAR(30),
    valor_passagens               VARCHAR(30),
    valor_devolucao               VARCHAR(30),
    valor_outros_gastos            VARCHAR(30)
);

DROP TABLE IF EXISTS raw_pagamento;
CREATE TABLE raw_pagamento (
    id_processo_viagem         VARCHAR(50),
    num_proposta                VARCHAR(50),
    cod_orgao_superior            VARCHAR(50),
    nome_orgao_superior           VARCHAR(255),
    cod_orgao_pagador             VARCHAR(50),
    nome_orgao_pagador            VARCHAR(255),
    cod_ug_pagadora               VARCHAR(50),
    nome_ug_pagadora              VARCHAR(255),
    tipo_pagamento                VARCHAR(50),
    valor                        VARCHAR(30)
);

DROP TABLE IF EXISTS raw_passagem;
CREATE TABLE raw_passagem (
    id_processo_viagem         VARCHAR(50),
    num_proposta                VARCHAR(50),
    meio_transporte               VARCHAR(50),
    pais_origem_ida               VARCHAR(60),
    uf_origem_ida                 VARCHAR(40),
    cidade_origem_ida             VARCHAR(80),
    pais_destino_ida              VARCHAR(60),
    uf_destino_ida                VARCHAR(40),
    cidade_destino_ida            VARCHAR(80),
    pais_origem_volta             VARCHAR(60),
    uf_origem_volta                VARCHAR(40),
    cidade_origem_volta            VARCHAR(80),
    pais_destino_volta             VARCHAR(60),
    uf_destino_volta               VARCHAR(40),
    cidade_destino_volta           VARCHAR(80),
    valor_passagem                VARCHAR(30),
    taxa_servico                  VARCHAR(30),
    data_emissao                  VARCHAR(20),
    hora_emissao                  VARCHAR(20)
);

DROP TABLE IF EXISTS raw_trecho;
CREATE TABLE raw_trecho (
    id_processo_viagem         VARCHAR(50),
    num_proposta                VARCHAR(50),
    sequencia_trecho              VARCHAR(20),
    origem_data                   VARCHAR(20),
    origem_pais                   VARCHAR(60),
    origem_uf                     VARCHAR(40),
    origem_cidade                 VARCHAR(80),
    destino_data                  VARCHAR(20),
    destino_pais                  VARCHAR(60),
    destino_uf                    VARCHAR(40),
    destino_cidade                VARCHAR(80),
    meio_transporte               VARCHAR(50),
    numero_diarias                VARCHAR(30),
    missao                       VARCHAR(10)
);


-- =============================================================================
-- CAMADA SILVER
-- Dados limpos e tipados, com PK, FK e constraints extras (NOT NULL, CHECK,
-- UNIQUE), conforme dicionario de dados e tabela de constraints do projeto.
-- =============================================================================

DROP TABLE IF EXISTS silver_trecho;
DROP TABLE IF EXISTS silver_pagamento;
DROP TABLE IF EXISTS silver_passagem;
DROP TABLE IF EXISTS silver_viagem;

-- -----------------------------------------------------------------------------
-- silver_viagem
-- Constraints extras: 
--		PRIMARY KEY em id_viagem 
--		NOT NULL em nome_orgao_superior
--		CHECK em valor_diarias >= 0
-- -----------------------------------------------------------------------------
CREATE TABLE silver_viagem (
    id_viagem              VARCHAR(20) PRIMARY KEY,
    num_proposta            VARCHAR(20),
    situacao                VARCHAR(50),
    viagem_urgente           VARCHAR(5),
    cod_orgao_superior        VARCHAR(20),
    nome_orgao_superior       VARCHAR(255)    NOT NULL,
    nome_viajante             VARCHAR(255),
    cargo                    VARCHAR(255),
    data_inicio              DATE,
    data_fim                 DATE,
    destinos                 VARCHAR(4000),
    motivo                   VARCHAR(4000),
    valor_diarias             DECIMAL(10,2),
    valor_passagens           DECIMAL(10,2),
    valor_devolucao           DECIMAL(10,2),
    valor_outros_gastos        DECIMAL(10,2),
    valor_total               DECIMAL(12,2),
    duracao_dias              INT,

    -- Impede que valor_diarias receba numero negativo
    CONSTRAINT chk_viagem_valor_diarias CHECK (valor_diarias >= 0)
);

-- -----------------------------------------------------------------------------
-- silver_passagem
-- Constraints extras: 
--		PRIMARY KEY em id_passagem 
--		FOREIGN KEY e NOT NULL em id_viagem
--		CHECK em valor_passagem >= 0; 
--		CHECK em taxa_servico >= 0
-- -----------------------------------------------------------------------------
CREATE TABLE silver_passagem (
    id_passagem            SERIAL   PRIMARY KEY,
    id_viagem                VARCHAR(20)   NOT NULL,
    meio_transporte           VARCHAR(50),
    pais_origem_ida           VARCHAR(60),
    uf_origem_ida             VARCHAR(40),
    cidade_origem_ida         VARCHAR(80),
    pais_destino_ida          VARCHAR(60),
    uf_destino_ida            VARCHAR(40),
    cidade_destino_ida        VARCHAR(80),
    valor_passagem            DECIMAL(10,2),
    taxa_servico              DECIMAL(10,2),
    data_emissao              DATE,

    FOREIGN KEY (id_viagem) REFERENCES silver_viagem(id_viagem),

    -- Impede valores negativos em passagem e taxa de servico
    CONSTRAINT chk_passagem_valor CHECK (valor_passagem >= 0),
    CONSTRAINT chk_passagem_taxa CHECK (taxa_servico >= 0)
);

-- -----------------------------------------------------------------------------
-- silver_pagamento
-- Constraints extras: 
--		PRIMARY KEY em id_pagamento
--		FOREIGN KEY em id_viagem
--		CHECK em valor >= 0 
--		NOT NULL em tipo_pagamento e id_viagem
-- -----------------------------------------------------------------------------
CREATE TABLE silver_pagamento (
    id_pagamento           SERIAL   PRIMARY KEY,
    id_viagem                VARCHAR(20)   NOT NULL,
    num_proposta             VARCHAR(20),
    nome_orgao_pagador        VARCHAR(255),
    nome_ug_pagadora          VARCHAR(255),
    tipo_pagamento            VARCHAR(50)   NOT NULL,
    valor                    DECIMAL(10,2),

    FOREIGN KEY (id_viagem) REFERENCES silver_viagem(id_viagem),

    -- Impede que a coluna valor receba numero negativo
    CONSTRAINT chk_pagamento_valor CHECK (valor >= 0)
);

-- -----------------------------------------------------------------------------
-- silver_trecho
-- Constraints extras: 
--		PRIMARY KEY em id_trecho
--		FOREIGN KEY em id_viagem 
--		CHECK em numero_diarias >= 0
--		UNIQUE (id_viagem, sequencia_trecho)
-- -----------------------------------------------------------------------------
CREATE TABLE silver_trecho (
    id_trecho              SERIAL   PRIMARY KEY,
    id_viagem                VARCHAR(20)   NOT NULL,
    sequencia_trecho          INT,
    origem_data               DATE,
    origem_uf                 VARCHAR(40),
    origem_cidade             VARCHAR(80),
    destino_data              DATE,
    destino_uf                VARCHAR(40),
    destino_cidade            VARCHAR(80),
    meio_transporte           VARCHAR(50),
    numero_diarias            DECIMAL(10,2),

    FOREIGN KEY (id_viagem) REFERENCES silver_viagem(id_viagem),

    -- Impede numero_diarias negativo
    CONSTRAINT chk_trecho_diarias CHECK (numero_diarias >= 0),

    -- Impede a mesma viagem ter dois trechos com a mesma sequencia
    CONSTRAINT uq_trecho_sequencia UNIQUE (id_viagem, sequencia_trecho)
);
