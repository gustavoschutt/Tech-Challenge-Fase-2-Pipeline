"""
Testes unitários para a Camada Gold (build_analytics.py).
Valida criação de tabelas analíticas, agregações, lags de ML e classificação de metas.
"""

from pathlib import Path
import sys
import pandas as pd
import numpy as np
import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from pipeline.gold.build_analytics import (
    build_indicador_municipio,
    build_evolucao_uf,
    build_painel_nacional,
    build_ml_features,
    calcular_status_meta,
)


@pytest.fixture
def gold_sample_data():
    indicador = pd.DataFrame([
        {"id_municipio": "3550308", "ano": 2021, "indicador_alfabetizacao": 60.0, "quantidade_matriculas": 1000, "meta_atingida": True},
        {"id_municipio": "3550308", "ano": 2022, "indicador_alfabetizacao": 70.0, "quantidade_matriculas": 1100, "meta_atingida": True},
        {"id_municipio": "3550308", "ano": 2023, "indicador_alfabetizacao": 80.0, "quantidade_matriculas": 1200, "meta_atingida": True},
        {"id_municipio": "3304557", "ano": 2023, "indicador_alfabetizacao": 45.0, "quantidade_matriculas": 800, "meta_atingida": False},
        {"id_municipio": "3106200", "ano": 2023, "indicador_alfabetizacao": 90.0, "quantidade_matriculas": 500, "meta_atingida": True},
    ])

    municipios = pd.DataFrame([
        {"id_municipio": "3550308", "nome": "SAO PAULO", "id_uf": "35", "sigla_uf": "SP"},
        {"id_municipio": "3304557", "nome": "RIO DE JANEIRO", "id_uf": "33", "sigla_uf": "RJ"},
        {"id_municipio": "3106200", "nome": "BELO HORIZONTE", "id_uf": "31", "sigla_uf": "MG"},
    ])

    ufs = pd.DataFrame([
        {"id_uf": "35", "sigla": "SP", "nome": "SAO PAULO"},
        {"id_uf": "33", "sigla": "RJ", "nome": "RIO DE JANEIRO"},
        {"id_uf": "31", "sigla": "MG", "nome": "MINAS GERAIS"},
    ])

    meta_mun = pd.DataFrame([
        {"id_municipio": "3550308", "ano": 2023, "meta": 75.0},
        {"id_municipio": "3304557", "ano": 2023, "meta": 50.0},
        # 3106200 não tem meta pactuada propositalmente
    ])

    meta_uf = pd.DataFrame([
        {"id_uf": "35", "ano": 2023, "meta": 70.0},
        {"id_uf": "33", "ano": 2023, "meta": 55.0},
        {"id_uf": "31", "ano": 2023, "meta": 80.0},
    ])

    meta_brasil = pd.DataFrame([
        {"ano": 2021, "meta": 55.0},
        {"ano": 2022, "meta": 60.0},
        {"ano": 2023, "meta": 65.0},
    ])

    return {
        "indicador": indicador,
        "municipios": municipios,
        "ufs": ufs,
        "meta_mun": meta_mun,
        "meta_uf": meta_uf,
        "meta_brasil": meta_brasil,
    }


class TestStatusMetaCalculation:
    def test_meta_atingida(self):
        row = pd.Series({"meta_municipio": 70.0, "gap_vs_meta_municipio": 5.0})
        assert calcular_status_meta(row) == "ATINGIDA"

    def test_meta_nao_atingida(self):
        row = pd.Series({"meta_municipio": 70.0, "gap_vs_meta_municipio": -5.0})
        assert calcular_status_meta(row) == "NAO_ATINGIDA"

    def test_sem_meta_pactuada(self):
        row = pd.Series({"meta_municipio": np.nan, "gap_vs_meta_municipio": np.nan})
        assert calcular_status_meta(row) == "SEM_META"


class TestBuildIndicadorMunicipio:
    def test_indicador_municipio_columns_and_gaps(self, gold_sample_data):
        df = build_indicador_municipio(
            gold_sample_data["indicador"],
            gold_sample_data["municipios"],
            gold_sample_data["ufs"],
            gold_sample_data["meta_mun"],
            gold_sample_data["meta_brasil"],
        )

        assert "id_municipio" in df.columns
        assert "status_meta_municipio" in df.columns
        assert "gap_vs_meta_municipio" in df.columns

        # Município 3550308 em 2023: ind=80, meta_mun=75 -> gap=+5.0 -> ATINGIDA
        sp_2023 = df[(df["id_municipio"] == "3550308") & (df["ano"] == 2023)].iloc[0]
        assert sp_2023["gap_vs_meta_municipio"] == pytest.approx(5.0)
        assert sp_2023["status_meta_municipio"] == "ATINGIDA"

        # Município 3106200 em 2023: sem meta -> status SEM_META
        mg_2023 = df[(df["id_municipio"] == "3106200") & (df["ano"] == 2023)].iloc[0]
        assert mg_2023["status_meta_municipio"] == "SEM_META"


class TestBuildEvolucaoUF:
    def test_evolucao_uf_aggregations(self, gold_sample_data):
        df = build_evolucao_uf(
            gold_sample_data["indicador"],
            gold_sample_data["municipios"],
            gold_sample_data["ufs"],
            gold_sample_data["meta_uf"],
        )

        assert "id_uf" in df.columns
        assert "indicador_medio" in df.columns
        assert "pct_municipios_meta_atingida" in df.columns
        assert "variacao_yoy" in df.columns
        assert len(df) > 0


class TestBuildPainelNacional:
    def test_painel_nacional_metrics(self, gold_sample_data):
        df = build_painel_nacional(
            gold_sample_data["indicador"],
            gold_sample_data["meta_brasil"],
        )

        assert "ano" in df.columns
        assert "indicador_medio_nacional" in df.columns
        assert "pct_municipios_alfabetizados" in df.columns
        assert "gap_meta" in df.columns


class TestBuildMLFeatures:
    def test_lag_features_and_trend(self, gold_sample_data):
        ind_gold = build_indicador_municipio(
            gold_sample_data["indicador"],
            gold_sample_data["municipios"],
            gold_sample_data["ufs"],
            gold_sample_data["meta_mun"],
            gold_sample_data["meta_brasil"],
        )
        ml_df = build_ml_features(ind_gold)

        assert "indicador_lag1" in ml_df.columns
        assert "tendencia" in ml_df.columns

        # Para SP (3550308) em 2023 (80.0): lag1=70.0 (2022) -> tendencia = 80 - 70 = 10.0
        sp_2023 = ml_df[(ml_df["id_municipio"] == "3550308") & (ml_df["ano"] == 2023)].iloc[0]
        assert sp_2023["indicador_lag1"] == pytest.approx(70.0)
        assert sp_2023["tendencia"] == pytest.approx(10.0)
