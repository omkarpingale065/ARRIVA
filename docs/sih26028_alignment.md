# Arriva vs. SIH26028 — Expected Solution, Line by Line

This mapping describes the current prototype honestly. It does not claim live
railway data, production scale, or real-world accuracy.

| SIH26028 expectation | Arriva today | Status |
| --- | --- | --- |
| Real-time ETA prediction using live train location data | GPS-style simulated location and movement streamed through WebSocket | ✅ |
| Operational parameters such as speed, congestion, and signal halts | Speed, distance, dwell, route section, track condition, weather, and disruption state are model inputs | ✅ |
| Historical delay trends | `historical_delay_minutes` exists in the feature schema; live simulator inference uses an explicit neutral zero because historical section data is not available there | ⚠️ Partial |
| Dynamic ETA updates in response to events | REST simulation advances and WebSocket updates trigger repeated inference | ✅ |
| ML/statistical methods that improve accuracy over time | Linear Regression selected over tree-ensemble and Random Forest baselines using MAE, RMSE, R², and chronological leakage checks | ✅ |
| Scale across thousands of trains and diverse zones | Three-route synthetic in-memory simulator | ⚠️ Roadmap |
| APIs for mobile apps, station displays, and control-room dashboards | FastAPI REST/WebSocket, control-room dashboard, and `/station-display` using the same ETA endpoint | ✅ |
| Decision-making and planning support | Section-impact conflict detection, controller recommendation, ETA band, and 51.58% MAE reduction versus the naive baseline | ✅ |

## Speaker notes

“We did not only build a delay predictor. We mapped the implementation against
the Ministry of Railways expectations line by line. Where the prototype is not
complete—historical live data and large-scale deployment—we label that gap and
have a clear next step: connect a licensed feed, persist historical section
outcomes, and move inference to a streaming and asynchronous architecture.”

## Claims to keep explicit

- Source data is synthetic prototype data.
- Train movement is simulated.
- The saved model is a prototype model, not production-ready.
- The ETA band is MAE-based and not statistically calibrated.
- The baseline improvement is an offline result on the current synthetic test
  split.
