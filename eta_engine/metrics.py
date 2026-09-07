"""Published evaluation metrics used by inference-facing features."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DAY1_REPORT = ROOT / "ml/models/day1_completion.json"
def load_model_mae() -> float:
    """Load the selected model MAE from the published training artifacts."""
    report: dict[str, Any] = json.loads(DAY1_REPORT.read_text(encoding="utf-8"))
    selected_model = report["selected_model"]
    for metric in report["metrics"]:
        if metric["model"] == selected_model:
            return float(metric["MAE"])
    raise ValueError(f"Selected model {selected_model!r} has no MAE metric.")
