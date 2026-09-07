"""Generate an ETA/delay prediction from the saved ARRIVA model.

Input JSON must contain the model-ready feature columns. An optional
``scheduled_destination_arrival`` ISO timestamp is used to turn predicted
delay minutes into a predicted arrival time.

Examples:

    python3 ml/predict.py --input-json '{"...": "..."}'
    python3 ml/predict.py --input-csv data/processed/test.csv --limit 1
"""

from __future__ import annotations

import argparse
import json
from datetime import timedelta
from pathlib import Path
from typing import Any

import pandas as pd

import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from eta_model import load_model, predict_eta_delay

DEFAULT_MODEL = ROOT / "ml/models/eta_model.pkl"
DEFAULT_PREPROCESSING = ROOT / "ml/models/preprocessing.joblib"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input-json")
    source.add_argument("--input-csv")
    parser.add_argument("--model", default=str(DEFAULT_MODEL))
    parser.add_argument("--preprocessing", default=str(DEFAULT_PREPROCESSING))
    parser.add_argument("--limit", type=int, default=5)
    return parser.parse_args()


def _load_observations(args: argparse.Namespace) -> pd.DataFrame:
    if args.input_json:
        payload = json.loads(args.input_json)
        if not isinstance(payload, dict):
            raise ValueError("--input-json must contain a JSON object.")
        return pd.DataFrame([payload])
    return pd.read_csv(args.input_csv).head(args.limit)


def predict_observations(
    observations: pd.DataFrame,
    model_path: str | Path = DEFAULT_MODEL,
    preprocessing_path: str | Path = DEFAULT_PREPROCESSING,
) -> list[dict[str, Any]]:
    """Return delay and optional scheduled-time-adjusted ETA predictions."""
    model_bundle = load_model(model_path)
    preprocessing = load_model(preprocessing_path)
    expected = preprocessing["feature_columns"]
    if expected != model_bundle["feature_columns"]:
        raise ValueError("Model and preprocessing artifacts have different feature schemas.")

    predictions = predict_eta_delay(model_bundle, observations)
    results: list[dict[str, Any]] = []
    for index, delay in predictions.items():
        predicted_delay = round(float(delay), 2)
        result: dict[str, Any] = {
            "predicted_delay_minutes": predicted_delay,
            "delay_status": "early" if predicted_delay < 0 else "on_time" if predicted_delay == 0 else "delayed",
        }
        scheduled = observations.loc[index].get("scheduled_destination_arrival")
        if pd.notna(scheduled):
            scheduled_timestamp = pd.to_datetime(scheduled, errors="coerce")
            if pd.notna(scheduled_timestamp):
                result["scheduled_destination_arrival"] = scheduled_timestamp.isoformat()
                result["predicted_arrival_time"] = (
                    scheduled_timestamp + timedelta(minutes=predicted_delay)
                ).isoformat()
        results.append(result)
    return results


def main() -> None:
    args = parse_args()
    observations = _load_observations(args)
    results = predict_observations(observations, args.model, args.preprocessing)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
