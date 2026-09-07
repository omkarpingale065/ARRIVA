# ARRIVA Day 2, Step 2: Dynamic ETA Engine

The Dynamic ETA Engine is an inference-only layer between the train movement
simulator and the saved Day 1 model. It does not retrain the model and does
not use FastAPI, WebSockets, or the frontend.

## Architecture

`DynamicETAEngine`:

1. Loads `ml/models/eta_model.pkl` and `ml/models/preprocessing.joblib` once.
2. Converts a simulator `TrainState` dictionary into the exact 48-column model
   feature schema, including one-hot route, section, weather, track, signal,
   and train columns.
3. Calls the saved Linear Regression model for destination delay minutes.
4. Adds predicted delay to `scheduled_destination_arrival`.
5. Estimates upcoming station ETAs from route distances and current speed.
6. Assigns LOW, MEDIUM, or HIGH risk using current delay, predicted delay,
   speed, weather, track, signal, and remaining-distance signals.
7. Stores each prediction in in-memory history by `train_id`.
8. Returns an interpretable contribution in minutes for every supported factor.

The contribution values are rule-based operational indicators, not SHAP values:
current delay, low speed, distance remaining, dwell, weather, wet track, late
status, signal aspect, and recovery speed each receive a bounded signed estimate.
RED, YELLOW, and DOUBLE_YELLOW aspects add increasing operational penalties.
They explain
the inputs used by the risk calculation without claiming causal model
attribution.

The backend also exposes `/api/trains/{train_id}/section-impact`. It compares
the current section and the next two route sections across simulator trains and
estimates bounded knock-on delay for shared occupancy. Each affected train is
labelled `current` or `upcoming` so downstream look-ahead conflicts are
distinguishable. A HIGH-risk conflict can produce a controller recommendation;
an empty conflict list produces none.

The adapter computes `historical_delay_minutes` from the rolling average of
previously observed `current_delay` values in the engine's in-memory prediction
history for that train. A new train has no prior observations and therefore
starts at `0.0`; this source is used because the simulator has no persisted
historical section store.

## Usage

```python
from eta_engine import DynamicETAEngine

engine = DynamicETAEngine()
prediction = engine.predict(train_state)
history = engine.get_prediction_history(train_state["train_id"])
```

## Demo

```bash
PYTHONPATH=. python3 scripts/run_eta_engine_demo.py
```

## Tests

```bash
PYTHONPATH=. python3 -m unittest discover -s tests -v
```

Tests cover normal, delayed, slow, near-destination, and repeated prediction
states.
