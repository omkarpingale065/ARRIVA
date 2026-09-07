# ARRIVA Internal Hackathon Demo Script

Target duration: 3–4 minutes. One person drives the browser; a second person
narrates. The backend and frontend should already be running, with the live
dashboard open and the WebSocket connected.

For a clean launch, run `scripts/run_demo.sh`. It starts both services and
prints the dashboard, station display, and API documentation URLs.

## Setup

Use the standalone dashboard at `http://localhost:5173/`. Keep the section
impact panel visible but quiet before the demonstration. The repeatable demo
uses:

- Disrupted train: `ARRIVA-12123` (Deccan Express)
- Affected train: `ARRIVA-11017` (Konark Express)
- Disruption: 20 simulated minutes, 10-minute active window

Reset the backend before rehearsals if a clean state is required.

## Run of show

### 1. Normal state — 30 seconds

**Narrator:** “Every train has a scheduled ETA and a predicted ETA. The
schedule says where a train should be; ARRIVA estimates where it will actually
arrive as operating conditions change.”

Point to the live train table, scheduled versus predicted ETA, risk/factor
panels, and the moving WebSocket-backed state.

### 2. Inject disruption — 30 seconds

Click **Inject demo disruption**.

**Narrator:** “I’m simulating a train entering the same section as another
train. This is a deterministic prototype control for demonstrating the
cascading-delay workflow, not a real dispatch command.”

The equivalent API call is:

```bash
curl -X POST http://127.0.0.1:8000/api/simulation/inject-disruption \
  -H 'Content-Type: application/json' \
  -d '{"train_id":"ARRIVA-12123","affected_train_id":"ARRIVA-11017","duration_minutes":10,"delay_minutes":20}'
```

On a fresh reset, the retrained model currently reports a predicted delay of
**22.03 minutes**, `HIGH` risk, and the recommendation: “Hold ARRIVA-12123 at
Pune for 10 min to let ARRIVA-11017 clear the section.” Repeated ETA reads can
change slightly because the in-memory historical-delay average updates with
new predictions.

### 3. Re-forecast and explain — 45 seconds

Show the updated ETA/risk and section-impact panels.

**Narrator:** “The state changes and the saved regression model
re-forecasts the ETA. The response includes the operational factors behind the
prediction, rather than presenting an unexplained number.”

Point out current delay, speed, dwell, weather/track indicators, and the
published ETA band. The band is predicted arrival ± the model’s validation MAE;
it is not a calibrated probability interval.

### 4. Recommendation — 30 seconds

Show the recommendation returned by the section-impact response.

**Narrator:** “Once a HIGH-risk conflict is detected, ARRIVA goes beyond
prediction and gives a controller-facing action recommendation. This is
decision support, not just a passenger-facing number.”

### 5. Close on the measured comparison — 30 seconds

Open:

```text
http://127.0.0.1:8000/api/model/comparison
```

**Narrator:** “On the chronological synthetic test split, the model’s MAE is
2.61 minutes versus 5.40 minutes for schedule plus current delay: a 51.58%
reduction. This is prototype evaluation data, not a claim of real railway
accuracy.”

For the multi-surface story, open:

```text
http://localhost:5173/station-display?train_id=ARRIVA-11017
```

This station display uses the same train and ETA APIs as the control-room
dashboard.

## Fallback

Keep a short recording of the same sequence available. If the live environment
fails, say: “I’ll show a recorded run of the exact same workflow.” Do not
describe the prototype as connected to live railway telemetry.

## One-line judge answers

- **Scale:** “Today this is a three-route simulator proving the loop; scaling
  requires streaming ingestion and asynchronous inference.”
- **Data:** “The data is synthetic and clearly labelled; the pipeline is
  structured to accept a licensed real feed later.”
- **Model choice:** “Linear Regression won on MAE for the retrained
  signal-aware feature set on the chronological leakage-checked split.”
- **Conflicting recommendations:** “Conflicts are currently resolved
  independently; a controller-facing priority queue is the next step.”

Closing line: “Static schedules tell you where a train should be. Arriva tells
you where it will be—and what to do about it.”
