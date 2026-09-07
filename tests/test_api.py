from fastapi.testclient import TestClient
from pathlib import Path

from backend.app import app, service
import backend.services as services_module


client = TestClient(app)


def test_list_trains():
    response = client.get("/api/trains")
    assert response.status_code == 200
    assert len(response.json()) >= 12


def test_model_comparison_endpoint():
    response = client.get("/api/model/comparison")
    assert response.status_code == 200
    payload = response.json()
    assert payload["naive_mae"] > payload["model_mae"]
    assert payload["mae_reduction_percent"] > 0
    assert payload["selected_model"]
    assert len(payload["models"]) == 3


def test_model_metrics_endpoint_reads_training_report():
    response = client.get("/api/model/metrics")
    assert response.status_code == 200
    payload = response.json()
    assert payload["selected_model"] == "Linear Regression"
    assert payload["selected"]["MAE"] > 0
    assert payload["selected"]["RMSE"] > 0
    assert "R2" in payload["selected"]


def test_model_metrics_endpoint_handles_missing_report(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(services_module, "TRAINING_REPORT", tmp_path / "missing.json")
    response = client.get("/api/model/metrics")
    assert response.status_code == 400
    assert "metrics are unavailable" in response.json()["detail"]


def test_model_metrics_endpoint_handles_malformed_report(monkeypatch, tmp_path: Path):
    report = tmp_path / "malformed.json"
    report.write_text("{not-json", encoding="utf-8")
    monkeypatch.setattr(services_module, "TRAINING_REPORT", report)
    response = client.get("/api/model/metrics")
    assert response.status_code == 400
    assert "metrics are unavailable" in response.json()["detail"]


def test_train_and_eta_endpoints():
    assert client.get("/api/trains/ARRIVA-12123").status_code == 200
    eta = client.get("/api/trains/ARRIVA-12123/eta")
    assert eta.status_code == 200
    assert eta.json()["train_id"] == "ARRIVA-12123"
    assert eta.json()["risk_level"] in {"LOW", "MEDIUM", "HIGH"}


def test_advance_and_history():
    response = client.post(
        "/api/simulation/advance",
        json={"train_id": "ARRIVA-11017", "minutes": 5},
    )
    assert response.status_code == 200
    assert response.json()["eta"]["train_id"] == "ARRIVA-11017"
    history = client.get("/api/trains/ARRIVA-11017/history")
    assert history.status_code == 200
    assert len(history.json()["predictions"]) >= 1


def test_validation_and_unknown_train_errors():
    assert client.post("/api/simulation/advance", json={"train_id": "ARRIVA-12123", "minutes": 0}).status_code == 422
    assert client.get("/api/trains/missing-train").status_code == 404
    assert client.get("/api/trains/missing-train/eta").status_code == 404


def test_delay_risk_endpoint():
    response = client.get("/api/trains/ARRIVA-22123/delay-risk")
    assert response.status_code == 200
    assert response.json()["risk_level"] in {"LOW", "MEDIUM", "HIGH"}


def test_section_impact_and_factor_contributions():
    impact = client.get("/api/trains/ARRIVA-12123/section-impact")
    assert impact.status_code == 200
    assert impact.json()["train_id"] == "ARRIVA-12123"
    eta = client.get("/api/trains/ARRIVA-12123/eta")
    assert eta.status_code == 200
    assert all("contribution_minutes" in factor for factor in eta.json()["delay_factors"])


def test_inject_disruption_creates_demo_conflict_and_recommendation():
    response = client.post(
        "/api/simulation/inject-disruption",
        json={
            "train_id": "ARRIVA-12123",
            "affected_train_id": "ARRIVA-11017",
            "duration_minutes": 10,
            "delay_minutes": 20,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["disrupted_train"]["route_section"] == payload["section_impact"]["route_section"]
    assert any(
        train["train_id"] == "ARRIVA-11017"
        for train in payload["section_impact"]["affected_trains"]
    )
    assert payload["section_impact"]["affected_trains"][0]["conflict_type"] == "current"
    assert payload["eta"]["risk_level"] == "HIGH"
    assert payload["eta"]["recommendation"]


def test_section_impact_distinguishes_upcoming_conflict():
    client.post("/api/simulation/reset")
    service.simulator.inject_disruption(
        "ARRIVA-12123",
        duration_minutes=10,
        conflict_section="Kalyan->Kasara",
    )
    response = client.get("/api/trains/ARRIVA-11017/section-impact")
    assert response.status_code == 200
    conflicts = response.json()["affected_trains"]
    assert any(
        conflict["train_id"] == "ARRIVA-12123"
        and conflict["conflict_type"] == "upcoming"
        for conflict in conflicts
    )


def test_reset_restores_initial_simulator_state():
    service_initial = client.post("/api/simulation/reset").json()
    client.post(
        "/api/simulation/inject-disruption",
        json={
            "train_id": "ARRIVA-12123",
            "affected_train_id": "ARRIVA-11017",
            "duration_minutes": 10,
            "delay_minutes": 20,
        },
    )
    client.post("/api/simulation/advance", json={"train_id": "ARRIVA-11017", "minutes": 5})
    reset = client.post("/api/simulation/reset")
    assert reset.status_code == 200
    assert reset.json() == service_initial
