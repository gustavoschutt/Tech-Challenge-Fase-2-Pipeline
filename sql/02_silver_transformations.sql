-- =============================================================================
-- Tech Challenge - Fase 2: Pipeline de Alfabetização no Brasil
-- Script 02: Transformações e Limpeza na Camada Silver (BigQuery)
-- Aplica desduplicação, cast de tipos, normalização de texto, integridade referencial
-- e regra oficial de 743 pontos SAEB para alfabetização.
-- =============================================================================

-- 1. Silver: UFs
CREATE OR REPLACE TABLE `silver_alfabetizacao.dim_ufs` AS
SELECT DISTINCT
  CAST(id_uf AS STRING) AS id_uf,
  UPPER(TRIM(sigla)) AS sigla_uf,
  UPPER(TRIM(nome)) AS nome_uf,
  CURRENT_TIMESTAMP() AS _silver_timestamp
FROM `bronze_alfabetizacao.raw_ufs`
WHERE id_uf IS NOT NULL;

-- 2. Silver: Municípios (com integridade referencial validada contra UFs)
CREATE OR REPLACE TABLE `silver_alfabetizacao.dim_municipios` AS
SELECT DISTINCT
  CAST(m.id_municipio AS STRING) AS id_municipio,
  COALESCE(UPPER(TRIM(m.nome)), 'NAO INFORMADO') AS nome_municipio,
  UPPER(TRIM(m.sigla_uf)) AS sigla_uf,
  CAST(m.id_uf AS STRING) AS id_uf,
  CURRENT_TIMESTAMP() AS _silver_timestamp
FROM `bronze_alfabetizacao.raw_municipios` m
INNER JOIN `silver_alfabetizacao.dim_ufs` u
  ON m.sigla_uf = u.sigla_uf
WHERE m.id_municipio IS NOT NULL;

-- 3. Silver: Metas Brasil
CREATE OR REPLACE TABLE `silver_alfabetizacao.fct_meta_brasil` AS
SELECT DISTINCT
  CAST(ano AS INT64) AS ano,
  CAST(meta AS FLOAT64) AS meta_nacional,
  CURRENT_TIMESTAMP() AS _silver_timestamp
FROM `bronze_alfabetizacao.raw_meta_brasil`
WHERE ano IS NOT NULL AND meta IS NOT NULL;

-- 4. Silver: Metas UF
CREATE OR REPLACE TABLE `silver_alfabetizacao.fct_meta_uf` AS
SELECT DISTINCT
  CAST(m.id_uf AS STRING) AS id_uf,
  CAST(m.ano AS INT64) AS ano,
  CAST(m.meta AS FLOAT64) AS meta_uf,
  CURRENT_TIMESTAMP() AS _silver_timestamp
FROM `bronze_alfabetizacao.raw_meta_uf` m
INNER JOIN `silver_alfabetizacao.dim_ufs` u
  ON CAST(m.id_uf AS STRING) = u.id_uf
WHERE m.ano IS NOT NULL AND m.meta IS NOT NULL;

-- 5. Silver: Metas Município
CREATE OR REPLACE TABLE `silver_alfabetizacao.fct_meta_municipio` AS
SELECT DISTINCT
  CAST(m.id_municipio AS STRING) AS id_municipio,
  CAST(m.ano AS INT64) AS ano,
  CAST(m.meta AS FLOAT64) AS meta_municipio,
  CURRENT_TIMESTAMP() AS _silver_timestamp
FROM `bronze_alfabetizacao.raw_meta_municipio` m
INNER JOIN `silver_alfabetizacao.dim_municipios` mun
  ON CAST(m.id_municipio AS STRING) = mun.id_municipio
WHERE m.ano IS NOT NULL AND m.meta IS NOT NULL;

-- 6. Silver: Alunos (Aplica Ponto de Corte de 743 pontos SAEB)
CREATE OR REPLACE TABLE `silver_alfabetizacao.fct_alunos_saeb` AS
SELECT
  CAST(a.ano AS INT64) AS ano,
  CAST(a.id_municipio AS STRING) AS id_municipio,
  CAST(a.proficiencia AS FLOAT64) AS proficiencia_saeb,
  -- Ponto de corte do Indicador Criança Alfabetizada: 743 pontos
  IF(CAST(a.proficiencia AS FLOAT64) >= 743.0, TRUE, FALSE) AS aluno_alfabetizado,
  CURRENT_TIMESTAMP() AS _silver_timestamp
FROM `bronze_alfabetizacao.raw_alunos` a
INNER JOIN `silver_alfabetizacao.dim_municipios` mun
  ON CAST(a.id_municipio AS STRING) = mun.id_municipio
WHERE a.proficiencia IS NOT NULL;

-- 7. Silver: Indicador de Alfabetização Consolidado
CREATE OR REPLACE TABLE `silver_alfabetizacao.fct_indicador_alfabetizacao` AS
WITH deduplicated AS (
  SELECT
    CAST(i.id_municipio AS STRING) AS id_municipio,
    CAST(i.ano AS INT64) AS ano,
    CAST(i.indicador_alfabetizacao AS FLOAT64) AS indicador_alfabetizacao,
    CAST(i.quantidade_matriculas AS INT64) AS quantidade_matriculas,
    ROW_NUMBER() OVER (PARTITION BY i.id_municipio, i.ano ORDER BY i._ingestion_timestamp DESC) AS rn
  FROM `bronze_alfabetizacao.raw_indicador_municipio` i
  INNER JOIN `silver_alfabetizacao.dim_municipios` mun
    ON CAST(i.id_municipio AS STRING) = mun.id_municipio
  WHERE i.id_municipio IS NOT NULL AND i.ano IS NOT NULL
)
SELECT
  id_municipio,
  ano,
  indicador_alfabetizacao,
  quantidade_matriculas,
  IF(indicador_alfabetizacao >= 50.0, TRUE, FALSE) AS meta_atingida,
  CURRENT_TIMESTAMP() AS _silver_timestamp
FROM deduplicated
WHERE rn = 1;
