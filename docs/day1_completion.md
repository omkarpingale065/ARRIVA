# ARRIVA Day 1 Completion Report

## Pipeline status

- [x] Dataset: 3,602 synthetic raw observations; synthetic data is explicitly
  not real railway data.
- [x] Cleaning: duplicate, missing, invalid-value, timestamp, and outlier
  handling completed.
- [x] Feature engineering: 48 model-ready features including speed, distance,
  current delay, scheduled travel time, historical delay, dwell time, route
  section, and calendar features.
- [x] Model training: Linear Regression, Random Forest Regressor, and Gradient
  Boosting Regressor.
- [x] Model evaluation: MAE, RMSE, and R² on the chronological test split.
- [x] Best model: Linear Regression (signal-aspect retrain supersedes the
  original Day 1 selection).
- [x] Saved model: `ml/models/eta_model.pkl`.
- [x] Prediction test: `ml/test_prediction.py` passed.

## Evaluation

| Model | MAE | RMSE | R² |
| --- | ---: | ---: | ---: |
| Linear Regression | 2.614 | 3.380 | 0.683 |
| Tree-ensemble regression baseline | 2.795 | 3.604 | 0.640 |
| Random Forest Regressor | 3.122 | 3.921 | 0.574 |

Linear Regression was selected by lowest MAE on the held-out chronological
test set after the signal-aspect retrain. These results are experimental and
use synthetic data; they do not establish production performance.

## Reproduce the complete pipeline

From the repository root:

```bash
python3 -m pip install -r requirements-data.txt
python3 scripts/generate_synthetic_dataset.py
python3 scripts/preprocess_eta_data.py
python3 ml/train.py
python3 ml/test_prediction.py
```

## Make predictions

For model-ready feature rows:

```bash
python3 ml/predict.py \
  --input-csv data/processed/test.csv \
  --limit 3
```

The model predicts destination arrival delay in minutes. To also receive a
predicted clock-time ETA, include a `scheduled_destination_arrival` ISO
timestamp column in the input. The prediction script adds the predicted delay
to that timestamp.

## Published artifacts

- `ml/models/eta_model.pkl`: joblib-serialized selected model bundle.
- `ml/models/preprocessing.joblib`: feature schema and target metadata required
  for prediction compatibility.
- `ml/models/day1_completion.json`: metrics, leakage checks, and publication
  paths.
- `ml/models/model_metrics.csv`: model comparison table.
