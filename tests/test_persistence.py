from backend.repository import PredictionRepository


def _prediction(train_id: str, timestamp: str, delay: float) -> dict:
    return {
        "train_id": train_id,
        "timestamp": timestamp,
        "predicted_delay_minutes": delay,
        "risk_level": "LOW",
        "delay_factors": [],
        "upcoming_station_etas": [],
    }


def test_prediction_repository_writes_and_reads_predictions():
    repository = PredictionRepository(":memory:")
    prediction = _prediction("T1", "2026-03-01T06:00:00", 2.5)

    repository.write_prediction(prediction)

    assert repository.read_predictions("T1") == [prediction]
    assert repository.count_predictions("T1") == 1


def test_prediction_repository_paginates_in_timestamp_order():
    repository = PredictionRepository(":memory:")
    for minute in range(5):
        repository.write_prediction(
            _prediction("T1", f"2026-03-01T06:0{minute}:00", float(minute))
        )

    assert [item["predicted_delay_minutes"] for item in repository.read_predictions(
        "T1", limit=2, offset=2
    )] == [2.0, 3.0]
    assert repository.read_predictions("T1", limit=2, offset=10) == []
