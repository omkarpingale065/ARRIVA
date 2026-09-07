"""Smoke test for the published ARRIVA ETA model."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ml.predict import predict_observations  # noqa: E402


def main() -> None:
    test_path = ROOT / "data/processed/test.csv"
    test_row = pd.read_csv(test_path).head(1)
    test_row["scheduled_destination_arrival"] = "2026-03-01T12:00:00"

    results = predict_observations(
        test_row,
        ROOT / "ml/models/eta_model.pkl",
        ROOT / "ml/models/preprocessing.joblib",
    )
    assert len(results) == 1
    assert isinstance(results[0]["predicted_delay_minutes"], float)
    assert results[0]["delay_status"] in {"early", "on_time", "delayed"}
    assert "predicted_arrival_time" in results[0]
    print("prediction test: passed")
    print(results[0])


if __name__ == "__main__":
    main()
