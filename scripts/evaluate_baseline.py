"""Compare the saved ETA model with a schedule-plus-current-delay baseline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error

from eta_model import predict_eta_delay
from train_eta_models import NON_FEATURE_COLUMNS, TARGET, check_no_leakage, load_splits


ROOT = Path(__file__).resolve().parents[1]


def evaluate(
    train_path: Path,
    test_path: Path,
    model_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    """Evaluate both methods on the already-published chronological test split."""
    train, test = load_splits(train_path, test_path)
    leakage_check = check_no_leakage(train, test)
    feature_columns = [
        column for column in train.columns if column not in NON_FEATURE_COLUMNS
    ]
    bundle = joblib.load(model_path)
    model_predictions = predict_eta_delay(bundle, test[feature_columns])
    actual = test[TARGET]
    naive_predictions = test["current_delay_minutes"]
    model_mae = float(mean_absolute_error(actual, model_predictions))
    model_rmse = float(np.sqrt(mean_squared_error(actual, model_predictions)))
    naive_mae = float(mean_absolute_error(actual, naive_predictions))
    naive_rmse = float(np.sqrt(mean_squared_error(actual, naive_predictions)))
    improvement = (naive_mae - model_mae) / naive_mae * 100 if naive_mae else 0.0
    result = {
        "data_source": "Synthetic prototype data; not real railway data.",
        "train_split": str(train_path),
        "test_split": str(test_path),
        "model": bundle["selected_model"],
        "naive_method": "scheduled arrival plus current_delay_minutes",
        "naive_mae": naive_mae,
        "naive_rmse": naive_rmse,
        "model_mae": model_mae,
        "model_rmse": model_rmse,
        "mae_reduction_percent": improvement,
        "leakage_check": leakage_check,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", default=str(ROOT / "data/processed/train.csv"))
    parser.add_argument("--test", default=str(ROOT / "data/processed/test.csv"))
    parser.add_argument("--model", default=str(ROOT / "ml/models/eta_model.pkl"))
    parser.add_argument(
        "--output",
        default=str(ROOT / "data/processed/model/baseline_comparison.json"),
    )
    args = parser.parse_args()
    print(
        json.dumps(
            evaluate(
                Path(args.train),
                Path(args.test),
                Path(args.model),
                Path(args.output),
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
