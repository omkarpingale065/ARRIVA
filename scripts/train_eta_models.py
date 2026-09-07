"""Train and evaluate ARRIVA ETA regression models.

This script evaluates models on a chronological holdout and with k-fold
cross-validation on the training split. It is intended for experimentation
only; the synthetic source is not real railway data.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.model_selection import KFold, cross_validate
from sklearn.preprocessing import StandardScaler

from eta_model import predict_eta_delay


TARGET = "target_arrival_delay_minutes"
NON_FEATURE_COLUMNS = {"service_date", TARGET}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", default="data/processed/train.csv")
    parser.add_argument("--test", default="data/processed/test.csv")
    parser.add_argument("--output-dir", default="data/processed/model")
    parser.add_argument("--cv-folds", type=int, default=5)
    return parser.parse_args()


def load_splits(train_path: Path, test_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    train = pd.read_csv(train_path)
    test = pd.read_csv(test_path)
    if TARGET not in train or TARGET not in test:
        raise ValueError(f"Both splits must contain {TARGET!r}.")
    if list(train.columns) != list(test.columns):
        raise ValueError("Train and test columns do not match.")
    return train, test


def check_no_leakage(train: pd.DataFrame, test: pd.DataFrame) -> dict[str, Any]:
    """Check target/date exclusion and chronological split boundaries."""
    feature_columns = [
        column for column in train.columns if column not in NON_FEATURE_COLUMNS
    ]
    if TARGET in feature_columns:
        raise AssertionError("Target column is present in model features.")
    if "service_date" in feature_columns:
        raise AssertionError("Service date is present in model features.")
    if train["service_date"].max() >= test["service_date"].min():
        raise AssertionError("Train/test service-date ranges overlap or are reversed.")

    train_feature_hashes = pd.util.hash_pandas_object(
        train[feature_columns], index=False
    )
    test_feature_hashes = pd.util.hash_pandas_object(
        test[feature_columns], index=False
    )
    overlapping_feature_rows = int(
        train_feature_hashes.isin(set(test_feature_hashes)).sum()
    )
    if overlapping_feature_rows:
        raise AssertionError(
            f"Found {overlapping_feature_rows} overlapping feature rows across splits."
        )

    return {
        "target_excluded": True,
        "service_date_excluded": True,
        "train_max_date": str(train["service_date"].max()),
        "test_min_date": str(test["service_date"].min()),
        "overlapping_feature_rows": overlapping_feature_rows,
        "feature_count": len(feature_columns),
    }


def build_models() -> dict[str, Any]:
    return {
        "Linear Regression": Pipeline(
            [
                ("scaler", StandardScaler()),
                ("regressor", LinearRegression()),
            ]
        ),
        "Random Forest Regressor": RandomForestRegressor(
            n_estimators=250,
            max_features="sqrt",
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
        ),
        "Gradient Boosting Regressor": GradientBoostingRegressor(
            n_estimators=180,
            learning_rate=0.05,
            max_depth=3,
            loss="huber",
            random_state=42,
        ),
    }


def evaluate_model(
    model: Any,
    x_train: pd.DataFrame,
    y_train: pd.Series,
    x_test: pd.DataFrame,
    y_test: pd.Series,
    cv_folds: int,
) -> tuple[dict[str, float], dict[str, Any]]:
    """Fit once for the untouched chronological holdout and score CV on train only."""
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    holdout = {
        "MAE": float(mean_absolute_error(y_test, predictions)),
        "RMSE": float(np.sqrt(mean_squared_error(y_test, predictions))),
        "R2": float(r2_score(y_test, predictions)),
    }
    cv = KFold(n_splits=cv_folds, shuffle=True, random_state=42)
    cv_scores = cross_validate(
        model,
        x_train,
        y_train,
        cv=cv,
        scoring={
            "MAE": "neg_mean_absolute_error",
            "RMSE": "neg_root_mean_squared_error",
            "R2": "r2",
        },
        n_jobs=1,
        return_train_score=False,
    )
    cv_summary = {
        "folds": cv_folds,
        "MAE": {
            "mean": float(-cv_scores["test_MAE"].mean()),
            "std": float(cv_scores["test_MAE"].std()),
            "folds": [float(-value) for value in cv_scores["test_MAE"]],
        },
        "RMSE": {
            "mean": float(-cv_scores["test_RMSE"].mean()),
            "std": float(cv_scores["test_RMSE"].std()),
            "folds": [float(-value) for value in cv_scores["test_RMSE"]],
        },
        "R2": {
            "mean": float(cv_scores["test_R2"].mean()),
            "std": float(cv_scores["test_R2"].std()),
            "folds": [float(value) for value in cv_scores["test_R2"]],
        },
    }
    return holdout, cv_summary


def run_training(
    train_path: Path,
    test_path: Path,
    output_dir: Path,
    cv_folds: int = 5,
) -> dict[str, Any]:
    train, test = load_splits(train_path, test_path)
    leakage_check = check_no_leakage(train, test)
    feature_columns = [
        column for column in train.columns if column not in NON_FEATURE_COLUMNS
    ]
    x_train = train[feature_columns]
    y_train = train[TARGET]
    x_test = test[feature_columns]
    y_test = test[TARGET]

    if cv_folds < 2 or cv_folds > len(train):
        raise ValueError(f"cv_folds must be between 2 and {len(train)}.")
    models = build_models()
    results: list[dict[str, Any]] = []
    cv_results: dict[str, Any] = {}
    fitted_models: dict[str, Any] = {}
    for name, model in models.items():
        metrics, cv_summary = evaluate_model(
            model, x_train, y_train, x_test, y_test, cv_folds
        )
        results.append({"model": name, **metrics})
        cv_results[name] = cv_summary
        fitted_models[name] = model

    # Keep the existing Linear Regression deployment default stable while
    # exposing a CV recommendation. The chronological holdout remains genuinely
    # out-of-sample and is never used to choose either result.
    cv_ranked = sorted(
        results,
        key=lambda row: (
            cv_results[row["model"]]["MAE"]["mean"],
            cv_results[row["model"]]["RMSE"]["mean"],
            -cv_results[row["model"]]["R2"]["mean"],
        )
    )
    best = next(row for row in results if row["model"] == "Linear Regression")
    best_model = fitted_models[best["model"]]
    output_dir.mkdir(parents=True, exist_ok=True)
    model_bundle = {
        "model": best_model,
        "feature_columns": feature_columns,
        "target": TARGET,
        "selected_model": best["model"],
        "data_source": "Synthetic prototype data; not real railway data.",
    }
    model_path = output_dir / "best_eta_model.joblib"
    joblib.dump(model_bundle, model_path)

    sample_inputs = x_test.head(5).copy()
    sample_predictions = predict_eta_delay(model_bundle, sample_inputs)
    samples = [
        {
            "sample_index": int(index),
            "actual_delay_minutes": float(y_test.loc[index]),
            "predicted_delay_minutes": float(sample_predictions.loc[index]),
        }
        for index in sample_inputs.index
    ]
    metrics_path = output_dir / "model_metrics.csv"
    pd.DataFrame(results).to_csv(metrics_path, index=False)
    report = {
        "data_source": "Synthetic prototype data; not real railway data.",
        "train_rows": len(train),
        "test_rows": len(test),
        "feature_count": len(feature_columns),
        "target": TARGET,
        "metrics": results,
        "out_of_sample_evaluation": {
            "split": "chronological holdout",
            "metrics": results,
        },
        "cross_validation": {
            "method": "KFold(shuffle=True, random_state=42) on training split only",
            "models": cv_results,
        },
        "selected_model": best["model"],
        "recommended_model_by_cv": cv_ranked[0]["model"],
        "selection_reason": "Linear Regression remains the deployed default for backwards-compatible behavior; CV recommendation is reported separately and the chronological holdout is out-of-sample only.",
        "leakage_check": leakage_check,
        "sample_predictions": samples,
        "saved_model": str(model_path),
    }
    (output_dir / "training_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    return report


def main() -> None:
    args = parse_args()
    report = run_training(
        Path(args.train),
        Path(args.test),
        Path(args.output_dir),
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
