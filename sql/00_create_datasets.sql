-- =============================================================================
-- Tech Challenge - Fase 2: Pipeline de Alfabetização no Brasil
-- Script 00: Criação dos Datasets no BigQuery (Medalhão)
-- =============================================================================

-- Substitua `<PROJECT_ID>` pelo seu Project ID no GCP (ex: `tc-alfabetizacao-fiap`)

-- 1. Dataset Bronze (Dados Brutos / Landing Zone)
CREATE SCHEMA IF NOT EXISTS `bronze_alfabetizacao`
OPTIONS (
  location = 'US',
  description = 'Camada Bronze: Dados brutos das fontes educacionais (Base dos Dados / INEP / SAEB)'
);

-- 2. Dataset Silver (Dados Tratados, Integrados e Padronizados)
CREATE SCHEMA IF NOT EXISTS `silver_alfabetizacao`
OPTIONS (
  location = 'US',
  description = 'Camada Silver: Dados limpos, integrados, sem duplicatas e com regras SAEB aplicadas'
);

-- 3. Dataset Gold (Camada Analítica / Feature Store para ML)
CREATE SCHEMA IF NOT EXISTS `gold_alfabetizacao`
OPTIONS (
  location = 'US',
  description = 'Camada Gold: Datasets analíticos para BI, relatórios executivos e Feature Store para ML'
);
