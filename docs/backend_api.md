# ARRIVA Day 2, Step 3: FastAPI REST Backend

The backend is a thin REST layer over the existing `TrainSimulator` and
`DynamicETAEngine`. Routes contain no model logic.

## Start

From the repository root:

```bash
PYTHONPATH=. uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
```

OpenAPI documentation is available at:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/redoc`

## Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/health` | Service health |
| GET | `/api/trains` | List seeded simulator trains |
| GET | `/api/trains/{train_id}` | Read current train state |
| GET | `/api/trains/{train_id}/eta` | Generate current ETA prediction |
| GET | `/api/trains/{train_id}/delay-risk` | Read risk and supported factors |
| GET | `/api/trains/{train_id}/history` | Read persisted prediction history (`page`, `page_size` optional) |
| GET | `/api/trains/{train_id}/section-impact` | Estimate shared-section knock-on delay |
| GET | `/api/model/comparison` | Return saved model vs. naive baseline MAE comparison |
| POST | `/api/simulation/advance` | Advance a train and return state plus ETA |
| POST | `/api/simulation/inject-disruption` | Inject a deterministic shared-section demo conflict |
| POST | `/api/simulation/reset` | Restore all seeded trains to their initial state |

## Examples

```bash
curl http://127.0.0.1:8000/api/trains
curl http://127.0.0.1:8000/api/trains/ARRIVA-12123/eta
curl http://127.0.0.1:8000/api/trains/ARRIVA-12123/delay-risk
curl http://127.0.0.1:8000/api/trains/ARRIVA-12123/section-impact
curl http://127.0.0.1:8000/api/model/comparison
curl -X POST http://127.0.0.1:8000/api/simulation/advance \
  -H 'Content-Type: application/json' \
  -d '{"train_id":"ARRIVA-12123","minutes":5}'
curl -X POST http://127.0.0.1:8000/api/simulation/inject-disruption \
  -H 'Content-Type: application/json' \
  -d '{"train_id":"ARRIVA-12123","affected_train_id":"ARRIVA-11017","duration_minutes":10,"delay_minutes":20}'
```

The advance response contains:

```json
{
  "train": {"train_id": "ARRIVA-12123", "current_station": "Pune"},
  "eta": {
    "train_id": "ARRIVA-12123",
    "predicted_delay_minutes": 1.31,
    "risk_level": "MEDIUM"
  }
}
```

ETA responses also include `eta_lower_bound` and `eta_upper_bound`. These are
the predicted arrival plus or minus the selected model's published validation
MAE; they are an uncertainty band for this prototype, not a calibrated
probability interval.

The prototype uses in-memory state, local-development CORS for the Vite
frontend, and no authentication or database.

`section-impact` compares the selected train's current/next section with other
simulated trains. Matching trains receive a bounded rule-based added-delay
estimate. When a HIGH-risk train has a conflict, the response includes a
controller-facing recommendation; no conflict produces no recommendation.
The response labels each affected train as `current` or `upcoming`; upcoming
means one of the next two sections on the selected train's route.

`POST /api/simulation/reset` restores the deterministic seeded train states and
clears in-memory prediction history. It is intended for repeatable demos.

`inject-disruption` is a demo-only, in-memory control. It applies a bounded
delay and temporary disruption to one train, aligns a selected second train to
the disrupted train's section, and returns the resulting ETA and section
impact. It does not represent a live railway control action.

## WebSocket live updates

The live stream is available at:

```text
ws://127.0.0.1:8000/ws/trains
```

Optional bounded query parameters:

- `interval_seconds`: update interval from `0.05` to `60` seconds; default `5`.
- `advance_minutes`: simulated minutes per update from above `0` to `60`;
  default `5`.

Each interval advances all registered simulator trains and sends one message
per train. Messages contain simulator coordinates/state plus the Dynamic ETA
Engine prediction and risk:

```json
{
  "train_id": "ARRIVA-12123",
  "timestamp": "2026-03-01T06:05:00",
  "latitude": 18.539918,
  "longitude": 73.818555,
  "current_speed": 108.67,
  "current_delay": 2.03,
  "distance_remaining": 186.57,
  "predicted_delay": 1.76,
  "predicted_arrival": "2026-03-01T08:21:45.600000",
  "delay_risk": "LOW",
  "next_station": "Lonavala"
}
```

The endpoint owns one bounded async loop per connected client, stops on
disconnect/cancellation, and logs connection and unexpected errors. A simple
client is provided:

```bash
PYTHONPATH=. python3 scripts/websocket_test_client.py
```
