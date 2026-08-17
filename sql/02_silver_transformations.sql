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

-- 2. Silver: Municípios
CREATE OR REPLACE TABLE `silver_alfabetizacao.dim_municipios` AS
SELECT DISTINCT
  CAST(m.id_municipio AS STRING) AS id_municipio,
  COALESCE(UPPER(TRIM(m.nome)), 'NAO INFORMADO') AS nome_municipio,
  UPPER(TRIM(m.sigla_uf)) AS sigla_uf,
  CAST(m.id_uf AS STRING) AS id_uf,
  CURRENT_TIMESTAMP() AS _silver_timestamp
FROM `bronze_alfabetizacao.raw_municipios` m
INNER JOIN `silver_alfabetizacao.dim_ufs` u ON UPPER(TRIM(m.sigla_uf)) = u.sigla_uf
WHERE m.id_municipio IS NOT NULL;

-- 3. Silver: Metas Brasil (UNPIVOT 2024-2030)
CREATE OR REPLACE TABLE `silver_alfabetizacao.fct_meta_brasil` AS
SELECT
  CAST(SUBSTR(ano_meta, -4) AS INT64) AS ano,
  CAST(meta_nacional AS FLOAT64) AS meta_nacional,
  CURRENT_TIMESTAMP() AS _silver_timestamp
FROM `bronze_alfabetizacao.raw_meta_brasil`
UNPIVOT (
  meta_nacional FOR ano_meta IN (
    meta_alfabetizacao_2024,
    meta_alfabetizacao_2025,
    meta_alfabetizacao_2026,
    meta_alfabetizacao_2027,
    meta_alfabetizacao_2028,
    meta_alfabetizacao_2029,
    meta_alfabetizacao_2030
  )
)
WHERE meta_nacional IS NOT NULL;

-- 4. Silver: Metas UF (UNPIVOT com CTE)
CREATE OR REPLACE TABLE `silver_alfabetizacao.fct_meta_uf` AS
WITH unpivoted AS (
  SELECT
    sigla_uf,
    CAST(SUBSTR(ano_meta, -4) AS INT64) AS ano,
    CAST(meta_uf AS FLOAT64) AS meta_uf
  FROM `bronze_alfabetizacao.raw_meta_uf`
  UNPIVOT (
    meta_uf FOR ano_meta IN (
      meta_alfabetizacao_2024,
      meta_alfabetizacao_2025,
      meta_alfabetizacao_2026,
      meta_alfabetizacao_2027,
      meta_alfabetizacao_2028,
      meta_alfabetizacao_2029,
      meta_alfabetizacao_2030
    )
  )
  WHERE meta_uf IS NOT NULL
)
SELECT
  u.id_uf,
  UPPER(TRIM(m.sigla_uf)) AS sigla_uf,
  m.ano,
  m.meta_uf,
  CURRENT_TIMESTAMP() AS _silver_timestamp
FROM unpivoted m
LEFT JOIN `silver_alfabetizacao.dim_ufs` u ON UPPER(TRIM(m.sigla_uf)) = u.sigla_uf;

-- 5. Silver: Metas Município (UNPIVOT com CTE)
CREATE OR REPLACE TABLE `silver_alfabetizacao.fct_meta_municipio` AS
WITH unpivoted AS (
  SELECT
    CAST(id_municipio AS STRING) AS id_municipio,
    CAST(SUBSTR(ano_meta, -4) AS INT64) AS ano,
    CAST(meta_municipio AS FLOAT64) AS meta_municipio
  FROM `bronze_alfabetizacao.raw_meta_municipio`
  UNPIVOT (
    meta_municipio FOR ano_meta IN (
      meta_alfabetizacao_2024,
      meta_alfabetizacao_2025,
      meta_alfabetizacao_2026,
      meta_alfabetizacao_2027,
      meta_alfabetizacao_2028,
      meta_alfabetizacao_2029,
      meta_alfabetizacao_2030
    )
  )
  WHERE meta_municipio IS NOT NULL
)
SELECT
  m.id_municipio,
  m.ano,
  m.meta_municipio,
  CURRENT_TIMESTAMP() AS _silver_timestamp
FROM unpivoted m
INNER JOIN `silver_alfabetizacao.dim_municipios` mun ON m.id_municipio = mun.id_municipio;

-- 6. Silver: Alunos (Ponto de corte 743 pontos SAEB)
CREATE OR REPLACE TABLE `silver_alfabetizacao.fct_alunos_saeb` AS
SELECT
  CAST(a.ano AS INT64) AS ano,
  CAST(a.id_municipio AS STRING) AS id_municipio,
  CAST(a.proficiencia AS FLOAT64) AS proficiencia_saeb,
  IF(CAST(a.proficiencia AS FLOAT64) >= 743.0, TRUE, FALSE) AS aluno_alfabetizado,
  CURRENT_TIMESTAMP() AS _silver_timestamp
FROM `bronze_alfabetizacao.raw_alunos` a
INNER JOIN `silver_alfabetizacao.dim_municipios` mun ON CAST(a.id_municipio AS STRING) = mun.id_municipio
WHERE a.proficiencia IS NOT NULL;

-- 7. Silver: Indicador de Alfabetização Consolidado
CREATE OR REPLACE TABLE `silver_alfabetizacao.fct_indicador_alfabetizacao` AS
WITH raw_ind AS (
  SELECT
    CAST(id_municipio AS STRING) AS id_municipio,
    CAST(ano AS INT64) AS ano,
    COALESCE(
      SAFE_CAST(taxa_alfabetizacao AS FLOAT64),
      SAFE_CAST(indicador_alfabetizacao AS FLOAT64)
    ) AS indicador_alfabetizacao,
    SAFE_CAST(quantidade_matriculas AS INT64) AS quantidade_matriculas,
    ROW_NUMBER() OVER (PARTITION BY id_municipio, ano ORDER BY _ingestion_timestamp DESC) AS rn
  FROM `bronze_alfabetizacao.raw_indicador_municipio`
  WHERE id_municipio IS NOT NULL AND ano IS NOT NULL
)
SELECT
  i.id_municipio,
  i.ano,
  i.indicador_alfabetizacao,
  i.quantidade_matriculas,
  IF(i.indicador_alfabetizacao >= 50.0, TRUE, FALSE) AS meta_atingida,
  CURRENT_TIMESTAMP() AS _silver_timestamp
FROM raw_ind i
INNER JOIN `silver_alfabetizacao.dim_municipios` mun ON i.id_municipio = mun.id_municipio
WHERE i.rn = 1 AND i.indicador_alfabetizacao IS NOT NULL;
