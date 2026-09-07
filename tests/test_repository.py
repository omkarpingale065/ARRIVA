from datetime import datetime, timedelta

from backend.repository import PredictionRepository


def test_prediction_repository_persists_explicit_fields_and_paginates():
    repository = PredictionRepository(":memory:")
    for index in range(3):
        repository.write_prediction(
            {
                "train_id": "T1",
                "timestamp": datetime(2026, 1, 1) + timedelta(minutes=index),
                "scheduled_destination_arrival": datetime(2026, 1, 1, 8),
                "predicted_arrival": datetime(2026, 1, 1, 8, index),
                "predicted_delay_minutes": float(index),
                "delay_factors": [{"factor": "weather"}],
                "upcoming_station_etas": [{"station": "Pune"}],
            }
        )

    assert repository.count_predictions("T1") == 3
    assert len(repository.read_predictions("T1", limit=2)) == 2
    assert repository.read_predictions("T1", limit=2, offset=2)[0]["predicted_delay_minutes"] == 2
