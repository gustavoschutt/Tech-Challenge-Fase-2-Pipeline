"""
Testes unitários para o módulo de Data Quality (scripts/data_quality.py).
Valida todos os checks de qualidade, consistência entre camadas e runner.
"""

from pathlib import Path
import sys
import pytest
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.data_quality import (
    DataQualityRunner,
    CheckResult,
    check_no_duplicates,
    check_no_nulls_critical,
    check_minimum_volume,
    check_indicador_range,
    check_valid_years,
    check_gold_silver_consistency,
)


class TestIndividualDataQualityChecks:
    def test_check_no_duplicates_pass(self):
        df = pd.DataFrame([{"id": 1, "val": "a"}, {"id": 2, "val": "b"}])
        res = check_no_duplicates(df, "ent", "silver", ["id"])
        assert bool(res.passed) is True
        assert res.failed_count == 0

    def test_check_no_duplicates_fail(self):
        df = pd.DataFrame([{"id": 1, "val": "a"}, {"id": 1, "val": "b"}])
        res = check_no_duplicates(df, "ent", "silver", ["id"])
        assert bool(res.passed) is False
        assert res.failed_count == 1

    def test_check_no_nulls_critical(self):
        df_valid = pd.DataFrame([{"id": 1, "nome": "SP"}])
        res_v = check_no_nulls_critical(df_valid, "ent", "silver", ["id", "nome"])
        assert bool(res_v.passed) is True

        df_invalid = pd.DataFrame([{"id": 1, "nome": None}])
        res_inv = check_no_nulls_critical(df_invalid, "ent", "silver", ["id", "nome"])
        assert bool(res_inv.passed) is False
        assert res_inv.failed_count == 1

    def test_check_minimum_volume(self):
        df = pd.DataFrame([{"id": i} for i in range(10)])
        assert bool(check_minimum_volume(df, "ent", "silver", 5).passed) is True
        assert bool(check_minimum_volume(df, "ent", "silver", 20).passed) is False

    def test_check_gold_silver_consistency_within_tolerance(self):
        silver_df = pd.DataFrame([{"id": i} for i in range(100)])
        gold_df = pd.DataFrame([{"id": i} for i in range(98)])  # 2% de perda (tolerância de 5%)

        res = check_gold_silver_consistency(gold_df, silver_df, "indicador", tolerance=0.05)
        assert bool(res.passed) is True
        assert res.check_name == "consistencia_gold_vs_silver"

    def test_check_gold_silver_consistency_exceeds_tolerance(self):
        silver_df = pd.DataFrame([{"id": i} for i in range(100)])
        gold_df = pd.DataFrame([{"id": i} for i in range(80)])  # 20% de perda (tolerância 5%)

        res = check_gold_silver_consistency(gold_df, silver_df, "indicador", tolerance=0.05)
        assert bool(res.passed) is False


class TestDataQualityRunner:
    def test_runner_summary_calculation(self):
        runner = DataQualityRunner()
        runner.results = [
            CheckResult("c1", "e1", "silver", True, "ok"),
            CheckResult("c2", "e1", "silver", True, "ok"),
            CheckResult("c3", "e1", "silver", False, "erro"),
        ]

        summary = runner.summary()
        assert summary["total"] == 3
        assert summary["passed"] == 2
        assert summary["failed"] == 1
        assert summary["pass_rate"] == pytest.approx(66.7, rel=1e-1)
        assert summary["status"] == "FAILED"

    def test_runner_summary_zero_checks(self):
        runner = DataQualityRunner()
        runner.results = []
        summary = runner.summary()
        assert summary["total"] == 0
        assert summary["status"] == "NO_CHECKS_RUN"
