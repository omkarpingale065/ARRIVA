"""Reusable ETA regression prediction helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import pandas as pd


def load_model(model_path: str | Path) -> dict[str, Any]:
    """Load a saved ARRIVA model bundle."""
    return joblib.load(model_path)


def predict_eta_delay(
    model_bundle: dict[str, Any],
    observations: pd.DataFrame | dict[str, Any],
) -> pd.Series:
    """Predict destination arrival delay in minutes for one or more observations.

    ``observations`` must contain the same model feature columns used during
    training. The returned value is the predicted
    ``target_arrival_delay_minutes``.
    """
    if isinstance(observations, dict):
        observations = pd.DataFrame([observations])

    feature_columns = model_bundle["feature_columns"]
    missing = sorted(set(feature_columns) - set(observations.columns))
    if missing:
        raise ValueError(f"Prediction input is missing feature columns: {missing}")

    model_input = observations.loc[:, feature_columns]
    predictions = model_bundle["model"].predict(model_input)
    return pd.Series(predictions, index=observations.index, name=model_bundle["target"])


def predict_from_csv(
    model_path: str | Path,
    csv_path: str | Path,
) -> pd.Series:
    """Load model and CSV observations, then return predicted delay minutes."""
    bundle = load_model(model_path)
    observations = pd.read_csv(csv_path)
    return predict_eta_delay(bundle, observations)
