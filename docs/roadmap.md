# ARRIVA Roadmap

## Continuous retraining and scale

The signal-aware retrain selected Linear Regression over the tree-ensemble
baseline on
the current feature set, using lowest MAE as the selection criterion.

The current system is a synthetic, three-route prototype. Continuous
retraining will begin when a licensed operational feed is available:

1. Persist actual arrival outcomes alongside each prediction, including
   section, zone, signal, weather, and operational context.
2. Run scheduled batch jobs that compare actual-versus-predicted arrivals,
   monitor drift, rebuild features, and retrain only after leakage checks and
   holdout evaluation pass.
3. Promote a model artifact with versioned metrics and rollback metadata rather
   than retraining during live inference.

The path from three simulated routes to thousands of trains is architectural:
asynchronous ingestion for location and operational events, partitioned batch
or streaming inference by zone, and per-zone model variants where route
behavior differs. Capacity, latency, and accuracy must be measured against
real workloads before making a production-scale claim.
