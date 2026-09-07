from fastapi.testclient import TestClient

from backend.app import app


def test_websocket_streams_multiple_train_updates():
    client = TestClient(app)
    with client.websocket_connect(
        "/ws/trains?interval_seconds=0.1&advance_minutes=5"
    ) as websocket:
        first = websocket.receive_json()
        second = websocket.receive_json()

    assert first["train_id"].startswith("ARRIVA-")
    assert {
        "train_id",
        "timestamp",
        "latitude",
        "longitude",
        "current_speed",
        "current_delay",
        "distance_remaining",
        "predicted_delay",
        "predicted_arrival",
        "delay_risk",
        "next_station",
        "confidence_percent",
        "progress_percent",
    }.issubset(first)
    assert second["train_id"].startswith("ARRIVA-")


def test_websocket_rejects_invalid_interval():
    client = TestClient(app)
    try:
        with client.websocket_connect("/ws/trains?interval_seconds=0.001"):
            raise AssertionError("Expected WebSocket validation failure")
    except Exception as exc:
        assert "WebSocketDisconnect" in type(exc).__name__ or "1008" in str(exc)
