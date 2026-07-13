import json
from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app


ROOT = Path(__file__).resolve().parents[1]


def test_health_and_prediction() -> None:
    payload = json.loads((ROOT / "examples" / "request.json").read_text(encoding="utf-8"))
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        response = client.post("/predict", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert 0 <= body["default_probability"] <= 1
        assert body["predicted_default"] in (0, 1)
        assert body["risk_band"] in {"baixo", "moderado", "alto", "critico"}


def test_rejects_future_leakage_fields() -> None:
    payload = json.loads((ROOT / "examples" / "request.json").read_text(encoding="utf-8"))
    payload["status_apos_90d"] = "default"
    with TestClient(app) as client:
        response = client.post("/predict", json=payload)
        assert response.status_code == 422


def test_openapi_contains_valid_request_example_and_enums() -> None:
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()
    credit_schema = schema["components"]["schemas"]["CreditApplication"]
    example = credit_schema["example"]
    assert example["canal_aquisicao"] == "app"
    assert example["regiao"] == "Sudeste"
    assert example["tipo_produto"] == "emprestimo_pessoal"
    assert "app" in credit_schema["properties"]["canal_aquisicao"]["enum"]
