-- =============================================================================
-- Tech Challenge - Fase 2: Pipeline de Alfabetização no Brasil
-- Script 04: Camada Gold - Feature Store para Machine Learning (Data Leakage Free)
-- As features preditoras são calculadas estritamente com base no histórico (t-1, t-2).
-- Os campos `indicador_alfabetizacao` e `meta_atingida` no ano atual (t) são os targets.
-- =============================================================================

CREATE OR REPLACE TABLE `gold_alfabetizacao.ml_features`
CLUSTER BY sigla_uf, ano
AS
WITH lags AS (
  SELECT
    id_municipio,
    nome,
    sigla_uf,
    id_uf,
    ano,
    meta_municipio,
    meta_nacional,
    indicador_alfabetizacao,
    meta_atingida,
    -- Lags temporais (apenas passado)
    LAG(indicador_alfabetizacao, 1) OVER (PARTITION BY id_municipio ORDER BY ano) AS indicador_lag1,
    LAG(indicador_alfabetizacao, 2) OVER (PARTITION BY id_municipio ORDER BY ano) AS indicador_lag2
  FROM `gold_alfabetizacao.indicador_municipio`
)
SELECT
  id_municipio,
  nome,
  sigla_uf,
  id_uf,
  ano,
  indicador_lag1,
  indicador_lag2,
  -- Tendência calculada exclusivamente sobre o histórico: (t-1) - (t-2)
  ROUND(indicador_lag1 - indicador_lag2, 2) AS tendencia_historica,
  -- Gap histórico: indicador anterior (t-1) vs metas pactuadas
  ROUND(indicador_lag1 - meta_municipio, 2) AS gap_historico_vs_meta_municipio,
  ROUND(indicador_lag1 - meta_nacional, 2) AS gap_historico_vs_meta_nacional,
  meta_municipio,
  meta_nacional,
  -- Variáveis Alvo (Ground Truth Targets para Supervised ML)
  indicador_alfabetizacao,
  meta_atingida,
  CURRENT_TIMESTAMP() AS _gold_timestamp
FROM lags
WHERE indicador_lag1 IS NOT NULL;
