-- =============================================================================
-- Tech Challenge - Fase 2: Pipeline de Alfabetização no Brasil
-- Script 01: Ingestão Batch para a Camada Bronze (BigQuery)
-- Extrai dados das tabelas oficiais da Base dos Dados (INEP / SAEB / IBGE)
-- =============================================================================

-- 1. Ingestão do Indicador Criança Alfabetizada por Município
CREATE OR REPLACE TABLE `bronze_alfabetizacao.raw_indicador_municipio` AS
SELECT
  *,
  CURRENT_TIMESTAMP() AS _ingestion_timestamp,
  'basedosdados.br_inep_avaliacao_alfabetizacao.municipio' AS _source_table
FROM `basedosdados.br_inep_avaliacao_alfabetizacao.municipio`;

-- 2. Ingestão dos Microdados de Alunos (SAEB)
CREATE OR REPLACE TABLE `bronze_alfabetizacao.raw_alunos` AS
SELECT
  *,
  CURRENT_TIMESTAMP() AS _ingestion_timestamp,
  'basedosdados.br_inep_avaliacao_alfabetizacao.alunos' AS _source_table
FROM `basedosdados.br_inep_avaliacao_alfabetizacao.alunos`;

-- 3. Ingestão da Meta Alfabetização Brasil (Nacional)
CREATE OR REPLACE TABLE `bronze_alfabetizacao.raw_meta_brasil` AS
SELECT
  *,
  CURRENT_TIMESTAMP() AS _ingestion_timestamp,
  'basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_brasil' AS _source_table
FROM `basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_brasil`;

-- 4. Ingestão da Meta Alfabetização por UF (Estadual)
CREATE OR REPLACE TABLE `bronze_alfabetizacao.raw_meta_uf` AS
SELECT
  *,
  CURRENT_TIMESTAMP() AS _ingestion_timestamp,
  'basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_uf' AS _source_table
FROM `basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_uf`;

-- 5. Ingestão da Meta Alfabetização por Município
CREATE OR REPLACE TABLE `bronze_alfabetizacao.raw_meta_municipio` AS
SELECT
  *,
  CURRENT_TIMESTAMP() AS _ingestion_timestamp,
  'basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_municipio' AS _source_table
FROM `basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_municipio`;

-- 6. Ingestão do Diretório de Municípios (IBGE)
CREATE OR REPLACE TABLE `bronze_alfabetizacao.raw_municipios` AS
SELECT
  id_municipio,
  nome,
  sigla_uf,
  id_uf,
  CURRENT_TIMESTAMP() AS _ingestion_timestamp,
  'basedosdados.br_bd_diretorios_brasil.municipio' AS _source_table
FROM `basedosdados.br_bd_diretorios_brasil.municipio`;

-- 7. Ingestão do Diretório de UFs (IBGE)
CREATE OR REPLACE TABLE `bronze_alfabetizacao.raw_ufs` AS
SELECT
  id_uf,
  sigla,
  nome,
  CURRENT_TIMESTAMP() AS _ingestion_timestamp,
  'basedosdados.br_bd_diretorios_brasil.uf' AS _source_table
FROM `basedosdados.br_bd_diretorios_brasil.uf`;
