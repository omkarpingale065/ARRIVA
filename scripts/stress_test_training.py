"""Run the ETA trainer against a larger, perturbed synthetic dataset.

This deliberately stays separate from the normal artifacts. For example:

    python3 scripts/stress_test_training.py --scale 10

It is a smoke/performance check, not a substitute for validation on licensed
railway data.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from train_eta_models import run_training


ROOT = Path(__file__).resolve().parents[1]


def _expand(
    frame: pd.DataFrame, copies: int, seed: int, start_copy: int = 0
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    blocks = []
    for copy in range(start_copy, start_copy + copies):
        block = frame.copy()
        block["service_date"] = (
            pd.to_datetime(block["service_date"])
            + pd.to_timedelta(copy * 366, unit="D")
        ).dt.strftime("%Y-%m-%d")
        numeric = block.select_dtypes(include="number").columns
        if len(numeric):
            noise = rng.normal(0, 0.001, size=(len(block), len(numeric)))
            block.loc[:, numeric] = (
                block[numeric].astype(float).to_numpy() + noise
            )
        blocks.append(block)
    return pd.concat(blocks, ignore_index=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scale", type=int, default=5, help="Number of copies per split.")
    parser.add_argument("--cv-folds", type=int, default=5)
    parser.add_argument("--output-dir", default=".stress_test_output")
    args = parser.parse_args()
    if args.scale < 1:
        raise ValueError("--scale must be at least 1")

    train = pd.read_csv(ROOT / "data/processed/train.csv")
    test = pd.read_csv(ROOT / "data/processed/test.csv")
    output = ROOT / args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    train_path = output / "train.csv"
    test_path = output / "test.csv"
    _expand(train, args.scale, 42).sort_values("service_date").to_csv(
        train_path, index=False
    )
    _expand(test, args.scale, 43, start_copy=args.scale).sort_values(
        "service_date"
    ).to_csv(
        test_path, index=False
    )
    report = run_training(train_path, test_path, output / "model", args.cv_folds)
    print(
        f"Stress training complete: {report['train_rows']:,} train / "
        f"{report['test_rows']:,} test rows; selected {report['selected_model']}"
    )


if __name__ == "__main__":
    main()
