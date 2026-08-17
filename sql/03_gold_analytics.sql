-- =============================================================================
-- Tech Challenge - Fase 2: Pipeline de Alfabetização no Brasil
-- Script 03: Camada Gold - Datasets Analíticos (BigQuery)
-- Cria tabelas analíticas particionadas e clusterizadas para Dashboards e Relatórios
-- =============================================================================

-- 1. Gold: Indicador de Alfabetização por Município (Enriquecido com Metas e Gaps)
CREATE OR REPLACE TABLE `gold_alfabetizacao.indicador_municipio`
PARTITION BY RANGE_BUCKET(ano, GENERATE_ARRAY(2000, 2030, 1))
CLUSTER BY sigla_uf, id_municipio
AS
SELECT
  ind.id_municipio,
  mun.nome_municipio AS nome,
  mun.sigla_uf,
  mun.id_uf,
  u.nome_uf,
  ind.ano,
  ind.indicador_alfabetizacao,
  mm.meta_municipio,
  mb.meta_nacional,
  ROUND(ind.indicador_alfabetizacao - mm.meta_municipio, 2) AS gap_vs_meta_municipio,
  ROUND(ind.indicador_alfabetizacao - mb.meta_nacional, 2) AS gap_vs_meta_nacional,
  CASE
    WHEN mm.meta_municipio IS NULL THEN 'SEM_META'
    WHEN (ind.indicador_alfabetizacao - mm.meta_municipio) >= 0 THEN 'ATINGIDA'
    ELSE 'NAO_ATINGIDA'
  END AS status_meta_municipio,
  ind.meta_atingida,
  CURRENT_TIMESTAMP() AS _gold_timestamp
FROM `silver_alfabetizacao.fct_indicador_alfabetizacao` ind
LEFT JOIN `silver_alfabetizacao.dim_municipios` mun ON ind.id_municipio = mun.id_municipio
LEFT JOIN `silver_alfabetizacao.dim_ufs` u ON mun.id_uf = u.id_uf
LEFT JOIN `silver_alfabetizacao.fct_meta_municipio` mm ON ind.id_municipio = mm.id_municipio AND ind.ano = mm.ano
LEFT JOIN `silver_alfabetizacao.fct_meta_brasil` mb ON ind.ano = mb.ano;

-- 2. Gold: Evolução Temporal por UF
CREATE OR REPLACE TABLE `gold_alfabetizacao.evolucao_uf`
CLUSTER BY id_uf, ano
AS
WITH agg_uf AS (
  SELECT
    mun.id_uf,
    mun.sigla_uf,
    u.nome_uf,
    ind.ano,
    ROUND(AVG(ind.indicador_alfabetizacao), 2) AS indicador_medio,
    ROUND(MIN(ind.indicador_alfabetizacao), 2) AS indicador_min,
    ROUND(MAX(ind.indicador_alfabetizacao), 2) AS indicador_max,
    COUNT(DISTINCT ind.id_municipio) AS total_municipios,
    COUNTIF(ind.meta_atingida = TRUE) AS municipios_meta_atingida
  FROM `silver_alfabetizacao.fct_indicador_alfabetizacao` ind
  LEFT JOIN `silver_alfabetizacao.dim_municipios` mun ON ind.id_municipio = mun.id_municipio
  LEFT JOIN `silver_alfabetizacao.dim_ufs` u ON mun.id_uf = u.id_uf
  GROUP BY mun.id_uf, mun.sigla_uf, u.nome_uf, ind.ano
)
SELECT
  a.id_uf,
  a.sigla_uf,
  a.nome_uf,
  a.ano,
  a.indicador_medio,
  a.indicador_min,
  a.indicador_max,
  a.total_municipios,
  a.municipios_meta_atingida,
  muf.meta_uf,
  ROUND((a.municipios_meta_atingida / NULLIF(a.total_municipios, 0)) * 100, 2) AS pct_municipios_meta_atingida,
  ROUND(a.indicador_medio - LAG(a.indicador_medio) OVER (PARTITION BY a.id_uf ORDER BY a.ano), 2) AS variacao_yoy,
  CURRENT_TIMESTAMP() AS _gold_timestamp
FROM agg_uf a
LEFT JOIN `silver_alfabetizacao.fct_meta_uf` muf ON a.id_uf = muf.id_uf AND a.ano = muf.ano;

-- 3. Gold: Painel Nacional Consolidado (Progresso rumo a 2030)
CREATE OR REPLACE TABLE `gold_alfabetizacao.painel_nacional` AS
SELECT
  ind.ano,
  ROUND(AVG(ind.indicador_alfabetizacao), 2) AS indicador_medio_nacional,
  COUNT(DISTINCT ind.id_municipio) AS total_municipios,
  COUNTIF(ind.meta_atingida = TRUE) AS municipios_meta_atingida,
  mb.meta_nacional,
  ROUND((COUNTIF(ind.meta_atingida = TRUE) / NULLIF(COUNT(DISTINCT ind.id_municipio), 0)) * 100, 2) AS pct_municipios_alfabetizados,
  ROUND(AVG(ind.indicador_alfabetizacao) - mb.meta_nacional, 2) AS gap_meta,
  CURRENT_TIMESTAMP() AS _gold_timestamp
FROM `silver_alfabetizacao.fct_indicador_alfabetizacao` ind
LEFT JOIN `silver_alfabetizacao.fct_meta_brasil` mb ON ind.ano = mb.ano
GROUP BY ind.ano, mb.meta_nacional;
