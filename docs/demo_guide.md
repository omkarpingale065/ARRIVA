# ARRIVA Demo Guide

## Overview

ARRIVA is a prototype for train ETA prediction and delay intelligence. It
uses documented synthetic railway data and simulated train movement; it is
not connected to a live railway feed.

## Architecture

```text
Synthetic railway data
  -> cleaning and feature engineering
  -> train/test split
  -> Linear Regression model selection
  -> saved model
  -> simulated train state
  -> Dynamic ETA Engine
  -> FastAPI REST and WebSocket
  -> React dashboard
```

The model is trained separately. Each movement update uses the saved model for
inference; it does not retrain the model.

## Start the system

From the repository root, use two terminals:

```bash
PYTHONPATH=. uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
npm run dev
```

- Backend: `http://127.0.0.1:8000`
- Frontend: `http://localhost:5173`
- REST base: `http://127.0.0.1:8000/api`
- WebSocket: `ws://127.0.0.1:8000/ws/trains`

The frontend can use `.env.local` to override `VITE_API_BASE_URL` and
`VITE_WS_URL`.

## Recommended demonstration train

Use **ARRIVA-11017 (Konark Express)**. It has a long route, upcoming station
information, changing simulator speed and coordinates, and a visible ETA
update after advancing the simulation.

## Demonstration flow

1. Open `/` and show the train count, current status, ETA, risk, and map.
2. Open `/trains` and select train `11017`.
3. Open `/trains/ARRIVA-11017` and show its route, speed, delay, distance,
   risk, upcoming station, and prediction history.
4. Open `/simulation`, keep train `11017` selected, and run the simulation
   advance. The slider value is sent as simulated minutes to the backend.
5. Return to the dashboard or train details page. WebSocket updates show new
   coordinates, speed, distance, delay, ETA, and risk.
6. Open `/delay-intelligence` to explain the backend-provided delay factors.

### Disruption and cascading-delay demo

From the standalone dashboard, click **Inject demo disruption**. This calls the
in-memory simulation endpoint for `ARRIVA-12123`, applies a bounded 20-minute
delay, and aligns `ARRIVA-11017` to the same simulated section. The section
impact panel then shows the affected train and controller recommendation.
The same flow can be triggered from a terminal:

```bash
curl -X POST http://127.0.0.1:8000/api/simulation/inject-disruption \
  -H 'Content-Type: application/json' \
  -d '{"train_id":"ARRIVA-12123","affected_train_id":"ARRIVA-11017","duration_minutes":10,"delay_minutes":20}'
```

This is a deterministic prototype demonstration control, not a real railway
dispatch command.

After the disruption is visible:

1. The ETA panel shows the computed lower and upper arrival bounds around the
   model prediction. The band uses the published model MAE and is not a
   calibrated probability interval.
2. Open `http://127.0.0.1:8000/api/model/comparison` to show the computed
   schedule-plus-current-delay baseline comparison. On the current synthetic
   test split, the model MAE is **51.58% lower** than the baseline.
3. Open
   `http://localhost:5173/station-display?train_id=ARRIVA-11017` to show the
   same ETA service in a readable passenger/station display view. Platform 3
   is a clearly labelled prototype display field.
4. Click **Reset demo** to restore all seeded trains and rerun the sequence
   without restarting either service.

The dashboard maintains one bounded WebSocket connection. If it closes, the
header shows `reconnecting…` and retries after approximately two seconds.

## Clean validation trace

On a fresh deterministic backend instance, before advancing:

- Train: ARRIVA-11017, Konark Express
- Route: Mumbai to Nashik
- Current station / next station: Mumbai / Kalyan
- Speed: `0.0 km/h`
- Delay: `0.0 minutes`
- Distance remaining: `185.0 km`
- Predicted arrival: `2026-03-01T08:36:41.400000`
- Risk: `MEDIUM`

After advancing five simulated minutes:

- Speed: `71.34 km/h`
- Delay: `2.12 minutes`
- Distance remaining: `181.43 km`
- Coordinates changed from `(19.076, 72.8777)` to
  `(19.086948, 72.895041)`
- Predicted arrival: `2026-03-01T08:37:07.200000`
- Risk: `LOW`
- Prediction history: `1` record to `2` records

The exact values can vary when using a long-running shared simulator because
the simulator is stateful.

## Explaining ETA and risk

The Dynamic ETA Engine converts the current simulator state into the saved
model's feature schema and predicts destination delay in minutes. Predicted
arrival is scheduled destination arrival plus predicted delay. Risk is derived
from the current state and prediction using `LOW`, `MEDIUM`, or `HIGH`.

Prediction history records timestamp, train ID, predicted delay and arrival,
speed, current delay, distance, and risk after each prediction.

## ML model

- Problem: destination delay regression.
- Target: `target_arrival_delay_minutes`.
- Selected model: Linear Regression.
- MAE: `2.614` minutes.
- RMSE: `3.380` minutes.
- R²: `0.683`.

These metrics are from synthetic prototype data and must not be presented as
real-world railway accuracy. Important features include current speed,
distance remaining, current delay, scheduled travel time, historical delay,
station dwell, route and section, station sequence, observation time, weather,
and track condition.

## Known limitations and claims to avoid

- Data is synthetic, not historical live railway data.
- Movement is simulated, not sourced from railway telemetry.
- The model is a prototype and is not production-ready.
- Prediction history is in memory and is not persistent.
- Do not claim live railway-feed capability or real-world accuracy.
