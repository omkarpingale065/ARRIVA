# React + Vite

## ARRIVA data preparation pipeline

Day 1 data preparation is documented in [docs/data_pipeline.md](docs/data_pipeline.md).
It uses clearly labelled synthetic prototype data until a licensed historical
railway source is selected.

```bash
python3 -m pip install -r requirements-data.txt
python3 scripts/generate_synthetic_dataset.py
python3 scripts/preprocess_eta_data.py
```

The preprocessing command writes cleaned features, chronological train/test
splits, and pipeline metadata under `data/processed/`. No model training is
included in that command.

## ARRIVA ETA model training

Train and evaluate the Day 1 regression baselines:

```bash
python3 scripts/train_eta_models.py
```

This compares Linear Regression, Random Forest, and a tree-ensemble baseline using
MAE, RMSE, and R². It saves the best temporary model and evaluation artifacts
under `data/processed/model/`.

The current signal-aspect retrain selects **Linear Regression** with MAE
`2.6135` minutes.

The final Day 1 publishing and prediction interface is:

```bash
python3 ml/train.py
python3 ml/test_prediction.py
```

This template provides a minimal setup to get React working in Vite with HMR and some Oxlint rules.

## Run the integrated prototype

Copy `.env.example` to `.env.local` when the backend is not running on the
default local URLs. Start the backend and frontend in separate terminals:

```bash
PYTHONPATH=. uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
npm run dev
```

The frontend now loads train, ETA, risk, history, and simulation data from the
FastAPI REST API and receives live movement updates from `/ws/trains`. The
production bundle can be checked with `npm run build`.

## Ingestion adapters and weather

`backend/ingestion/base.py` defines replaceable train and weather ingestion
interfaces. `SimulatedTrainDataSource` wraps the existing deterministic
`TrainSimulator` without changing its state or API. `WeatherDataSource` reads
current conditions from [Open-Meteo](https://open-meteo.com/) using a two-second
timeout by default; network, HTTP, and malformed-response failures safely fall
back to clear weather. `ARRIVAService` enables this source by default; set
`ARRIVA_WEATHER_ENABLED=false` for offline tests. Train GPS and signal state
remain simulated because no Indian Railways feed is available, while a real
GPS/signal adapter can be substituted behind the same interface.

## Persistence, validation, and mobile client

Prediction snapshots are persisted in `data/arriva.sqlite3` with paginated
history at `/api/trains/{train_id}/history?page=1&page_size=50`. The database
is a lightweight prototype store; PostgreSQL or another managed store would be
appropriate for a multi-process deployment. Model reports include chronological
holdout metrics and five-fold validation on the training split. The larger
proxy stress run is available with `python3 scripts/stress_test_training.py`.

The separate dependency-free mobile PWA lives under `mobile/`; run it with
`cd mobile && python3 -m http.server 4174` and open
`http://127.0.0.1:4174/?api=http://127.0.0.1:8000`. It consumes the same REST
and WebSocket APIs and is not part of the Vite frontend.

For simulator-scale experiments, set `ARRIVA_SIMULATED_TRAIN_COUNT=500` (or
`2000`) before starting Uvicorn, then run
`python3 scripts/load_test.py --trains 500`. The checked-in scalability report
separates measured three-train results from unmeasured scale targets.

For the internal hackathon presentation, see:

- [docs/hackathon_demo_script.md](docs/hackathon_demo_script.md)
- [docs/sih26028_alignment.md](docs/sih26028_alignment.md)

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the Oxlint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and Oxlint's TypeScript related rules in your project.
