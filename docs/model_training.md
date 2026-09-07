# ARRIVA Day 1: ETA Model Training and Evaluation

Run:

```bash
python3 scripts/train_eta_models.py
```

The script loads `data/processed/train.csv` and `data/processed/test.csv`,
which were created by the data preparation pipeline. It trains:

- Linear Regression with standardization;
- Random Forest Regressor;
- Tree-ensemble regression baseline.

All three models are evaluated on the same feature matrix. The chronological
test split is an untouched out-of-sample evaluation. The report uses five-fold (shuffled, fixed-seed) cross-validation on the
training split, so test outcomes cannot influence the CV recommendation.
Linear Regression remains the published default for backwards-compatible
serving behavior; the CV recommendation is recorded separately. Override the
fold count with `--cv-folds N`.

XGBoost was checked and is not installed in this environment. The current
published artifact selects Linear Regression after the signal-aspect retrain;
The tree-ensemble model remains a comparison baseline.

## Metrics

- **MAE (Mean Absolute Error):** average absolute prediction error in minutes.
  Lower is better and it is the primary selection metric because it is easy to
  interpret operationally.
- **RMSE (Root Mean Squared Error):** square root of average squared error in
  minutes. Lower is better; it penalizes large misses more heavily than MAE.
- **R²:** proportion of target variance explained by the model. Higher is
  generally better, but it should be interpreted alongside MAE/RMSE.

## Leakage checks

The training script verifies that:

- `target_arrival_delay_minutes` is not a model feature;
- `service_date` is not a model feature;
- train dates end before test dates begin;
- no identical feature rows occur across the split.

## Outputs

- `data/processed/model/model_metrics.csv`: comparison table;
- `data/processed/model/training_report.json`: metrics, leakage checks,
  cross-validation and out-of-sample metrics, selection rationale, and sample
  predictions;
- `data/processed/model/best_eta_model.joblib`: temporary serialized model
  bundle containing the selected estimator and exact feature column order.

`scripts/eta_model.py` exposes `predict_eta_delay()` and
`predict_from_csv()` for reuse by future application code. The saved model is a
Day 1 experiment on synthetic data and is not production-ready.

## Published ML interface

The stable Day 1 entry points are:

```bash
python3 ml/train.py
python3 ml/test_prediction.py
```

`ml/train.py` publishes:

- `ml/models/eta_model.pkl`: selected Linear Regression model bundle;
- `ml/models/preprocessing.joblib`: feature schema and prediction metadata;
- `ml/models/day1_completion.json`: evaluation and publication report.

To predict from a model-ready CSV:

```bash
python3 ml/predict.py --input-csv data/processed/test.csv --limit 3
```

To return a predicted clock-time ETA, include
`scheduled_destination_arrival` in the input row. The model predicts delay
minutes; the script adds that delay to the scheduled arrival timestamp.

## Naive baseline comparison

The saved Linear Regression model was compared with a schedule-based baseline
on the same chronological `data/processed/test.csv` split. The baseline uses
the current recorded delay as its predicted destination delay; it does not
train or use future test outcomes.

| Method | MAE (minutes) | RMSE (minutes) |
| --- | ---: | ---: |
| Schedule + current delay | 5.3974 | 6.9909 |
| Linear Regression model | 2.6135 | 3.3804 |

The model reduces MAE by **51.58%** versus the baseline on this synthetic
prototype split. This is an offline comparison, not a claim about real
railway accuracy. The computed artifact is
`data/processed/model/baseline_comparison.json`, generated with:

```bash
PYTHONPATH=. python3 scripts/evaluate_baseline.py
```

## Signal-aspect feature update

The retrained model includes one-hot `signal_aspect` values (`GREEN`,
`YELLOW`, `DOUBLE_YELLOW`, and `RED`) alongside route, section, weather, and
track features. The current synthetic chronological split produced:

| Model | MAE | RMSE | R² |
| --- | ---: | ---: | ---: |
| Linear Regression | 2.614 | 3.380 | 0.683 |
| Tree-ensemble regression baseline | 2.795 | 3.604 | 0.640 |
| Random Forest Regressor | 3.122 | 3.921 | 0.574 |

The selected model and CV recommendation are recorded explicitly in
`training_report.json`. These are synthetic prototype metrics, not real
railway accuracy.

## Larger synthetic stress test

To exercise the trainer on a larger copy of the prototype data without
overwriting normal artifacts:

```bash
python3 scripts/stress_test_training.py --scale 10
```

This writes inputs and a report under `.stress_test_output/` and adds tiny
numeric perturbations so duplicated rows cannot mask leakage checks.
