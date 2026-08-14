"""
Testes unitários para a Camada Bronze (ingest_batch.py).
Valida mapeamento de queries, datasets da Base dos Dados, entidades e tratamento de erros com mocks.
"""

from pathlib import Path
import sys
import pytest
from unittest.mock import MagicMock, patch
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from pipeline.bronze.ingest_batch import (
    QUERIES,
    query_to_dataframe,
    save_to_gcs_parquet,
    log_metadata,
)


class TestBronzeQueriesCatalog:
    def test_queries_contain_all_required_entities(self):
        expected_entities = [
            "municipios",
            "ufs",
            "indicador_alfabetizacao",
            "alunos",
            "meta_brasil",
            "meta_uf",
            "meta_municipio",
        ]
        for entity in expected_entities:
            assert entity in QUERIES, f"Entidade {entity} ausente em QUERIES"

    def test_queries_point_to_correct_official_datasets(self):
        # Mapeamentos oficiais validados
        assert "br_inep_avaliacao_alfabetizacao.municipio" in QUERIES["indicador_alfabetizacao"]
        assert "br_inep_avaliacao_alfabetizacao.alunos" in QUERIES["alunos"]
        assert "br_bd_diretorios_brasil.municipio" in QUERIES["municipios"]
        assert "br_bd_diretorios_brasil.uf" in QUERIES["ufs"]
        assert "br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_brasil" in QUERIES["meta_brasil"]
        assert "br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_uf" in QUERIES["meta_uf"]
        assert "br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_municipio" in QUERIES["meta_municipio"]


class TestBronzeExtractionWithMock:
    def test_query_to_dataframe_success(self):
        mock_bq = MagicMock()
        mock_query_job = MagicMock()
        mock_df = pd.DataFrame([{"id_municipio": "3550308", "ano": 2023, "indicador": 85.0}])
        mock_query_job.to_dataframe.return_value = mock_df
        mock_bq.query.return_value = mock_query_job

        df = query_to_dataframe(mock_bq, "SELECT 1")
        assert len(df) == 1
        assert "id_municipio" in df.columns

    def test_save_to_gcs_parquet_mock(self):
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_bucket.name = "tc-datalake"
        mock_bucket.blob.return_value = mock_blob

        sample_df = pd.DataFrame([{"id": 1, "val": "teste"}])
        uri = save_to_gcs_parquet(sample_df, mock_bucket, "teste_entity")

        assert "gs://tc-datalake" in uri
        assert "teste_entity" in uri
        assert mock_blob.upload_from_filename.called

    def test_log_metadata(self):
        meta = log_metadata("municipios", 5570, "gs://tc-datalake/bronze/municipios/test.parquet")
        assert meta["entity"] == "municipios"
        assert meta["row_count"] == 5570
        assert meta["status"] == "SUCCESS"
