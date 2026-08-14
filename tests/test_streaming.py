"""
Testes unitários para o módulo de Streaming (streaming_pipeline.py).
Valida simulação de eventos, schema do payload, enriquecimento e regras de validação do consumer.
"""

from pathlib import Path
import sys
import pytest
import json

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from streaming.streaming_pipeline import (
    AlfabetizacaoEventProducer,
    AlfabetizacaoEventConsumer,
    EVENT_TYPES,
    SAMPLE_MUNICIPIOS,
)


class TestStreamingProducer:
    def test_build_event_structure(self):
        producer = AlfabetizacaoEventProducer()
        event = producer._build_event("INDICADOR_ATUALIZADO")

        assert "event_id" in event
        assert event["event_type"] == "INDICADOR_ATUALIZADO"
        assert "timestamp" in event
        assert "payload" in event

        payload = event["payload"]
        assert payload["id_municipio"] in SAMPLE_MUNICIPIOS
        assert payload["ano"] == 2024
        assert 0 <= payload["indicador_alfabetizacao"] <= 100
        assert payload["quantidade_matriculas"] > 0
        assert payload["fonte"] == "SAEB_STREAMING"

    def test_publish_offline_fallback(self):
        producer = AlfabetizacaoEventProducer()
        producer._publisher = False
        event_id = producer.publish("META_REVISADA")
        assert event_id.startswith("evt-")

    def test_publish_with_mocked_publisher(self, mocker):
        producer = AlfabetizacaoEventProducer()
        mock_pub = mocker.MagicMock()
        mock_future = mocker.MagicMock()
        mock_future.result.return_value = "msg-12345"
        mock_pub.publish.return_value = mock_future
        producer._publisher = mock_pub

        msg_id = producer.publish("INDICADOR_ATUALIZADO")
        assert msg_id == "msg-12345"
        assert mock_pub.publish.called


class TestStreamingConsumerValidation:
    def test_validate_valid_event(self):
        consumer = AlfabetizacaoEventConsumer()
        valid_event = {
            "event_id": "evt-123",
            "payload": {
                "id_municipio": "3550308",
                "indicador_alfabetizacao": 82.5,
            }
        }
        assert consumer._validate_event(valid_event) is True

    def test_validate_event_missing_municipio(self):
        consumer = AlfabetizacaoEventConsumer()
        invalid_event = {
            "event_id": "evt-123",
            "payload": {
                "indicador_alfabetizacao": 82.5,
            }
        }
        assert consumer._validate_event(invalid_event) is False

    def test_validate_event_out_of_range_indicador(self):
        consumer = AlfabetizacaoEventConsumer()
        invalid_event = {
            "event_id": "evt-123",
            "payload": {
                "id_municipio": "3550308",
                "indicador_alfabetizacao": 150.0,
            }
        }
        assert consumer._validate_event(invalid_event) is False

    def test_enrich_event_metadata(self):
        consumer = AlfabetizacaoEventConsumer()
        event = {"event_id": "evt-123", "payload": {"id_municipio": "3550308"}}
        enriched = consumer._enrich_event(event)

        assert enriched["_layer"] == "bronze_streaming"
        assert "_processing_date" in enriched
        assert enriched["_pipeline_version"] == "1.0.0"
