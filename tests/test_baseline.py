import json
from pathlib import Path

from scripts.evaluate_baseline import ROOT, evaluate


def test_baseline_reuses_chronological_split_without_leakage(tmp_path: Path):
    output = tmp_path / "baseline.json"
    result = evaluate(
        ROOT / "data/processed/train.csv",
        ROOT / "data/processed/test.csv",
        ROOT / "ml/models/eta_model.pkl",
        output,
    )
    assert json.loads(output.read_text(encoding="utf-8")) == result
    assert result["leakage_check"]["overlapping_feature_rows"] == 0
    assert result["leakage_check"]["train_max_date"] < result["leakage_check"]["test_min_date"]
