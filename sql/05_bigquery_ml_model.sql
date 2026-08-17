-- =============================================================================
-- Tech Challenge - Fase 2: Pipeline de Alfabetização no Brasil
-- Script 05: Demonstração de Aplicação em Inteligência Artificial no BigQuery
-- Treina um modelo de Machine Learning nativo no BigQuery (BigQuery ML)
-- para prever a probabilidade de um município atingir a meta de alfabetização.
-- =============================================================================

-- 1. Treinamento do Modelo de Regressão Logística para Classificação
CREATE OR REPLACE MODEL `gold_alfabetizacao.modelo_predicao_meta_alfabetizacao`
OPTIONS (
  model_type = 'LOGISTIC_REG',
  input_label_cols = ['meta_atingida'],
  auto_class_weights = TRUE,
  data_split_method = 'AUTO_SPLIT',
  max_iterations = 20
) AS
SELECT
  -- Features históricas preditoras (sem vazamento)
  sigla_uf,
  indicador_lag1,
  indicador_lag2,
  tendencia_historica,
  gap_historico_vs_meta_municipio,
  gap_historico_vs_meta_nacional,
  meta_municipio,
  meta_nacional,
  -- Target
  meta_atingida
FROM `gold_alfabetizacao.ml_features`
WHERE meta_atingida IS NOT NULL;

-- 2. Avaliação de Performance do Modelo
SELECT
  *
FROM ML.EVALUATE(MODEL `gold_alfabetizacao.modelo_predicao_meta_alfabetizacao`);

-- 3. Geração de Predições para Análise de Risco Municipal
SELECT
  id_municipio,
  nome,
  sigla_uf,
  ano,
  predicted_meta_atingida,
  predicted_meta_atingida_probs[OFFSET(0)].prob AS prob_nao_atingir,
  predicted_meta_atingida_probs[OFFSET(1)].prob AS prob_atingir
FROM ML.PREDICT(
  MODEL `gold_alfabetizacao.modelo_predicao_meta_alfabetizacao`,
  (SELECT * FROM `gold_alfabetizacao.ml_features`)
)
ORDER BY prob_nao_atingir DESC;
