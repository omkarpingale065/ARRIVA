# ARRIVA Day 1: ETA Data Preparation

## Data source

The repository uses a deterministic synthetic dataset because no licensed real
railway movement/ETA history was supplied. It is explicitly **not real railway
data** and must be replaced or validated against a licensed source before
production use.

Generate it with:

```bash
python3 scripts/generate_synthetic_dataset.py
```

The generator creates 3,602 raw observations across three representative routes,
six services, 60 service dates, and three observations per station section. It
also includes a small number of intentional missing, invalid, outlier, and
duplicate values so the cleaning pipeline is testable.

## Raw columns

| Column | Meaning |
| --- | --- |
| `record_id` | Unique observation identifier. |
| `train_id` | Service identifier. |
| `train_name` | Human-readable service name. |
| `service_date` | Date on which the service operated. |
| `route_id` | Stable route/corridor identifier. |
| `origin_station` | Scheduled origin station. |
| `destination_station` | Scheduled destination station. |
| `section_id` | Current origin-to-next-station section. |
| `station_sequence` | Zero-based station position on the route. |
| `station_name` | Current or most recently reached station. |
| `scheduled_departure` | Scheduled service departure timestamp. |
| `scheduled_arrival` | Scheduled arrival timestamp for the current station. |
| `scheduled_destination_arrival` | Scheduled final arrival timestamp at the destination. |
| `actual_observation_time` | Timestamp at which the observation was captured. |
| `actual_destination_arrival` | Actual final destination arrival timestamp used to define the target. |
| `latitude`, `longitude` | Observed train coordinates. |
| `current_speed_kmh` | Speed at observation time, km/h. |
| `distance_remaining_km` | Approximate distance to the destination, km. |
| `current_delay_minutes` | Delay at observation time versus schedule. |
| `station_arrival_time` | Observed/estimated arrival at current station. |
| `station_departure_time` | Observed/estimated departure from current station. |
| `weather_condition` | Simplified operating weather category. |
| `track_condition` | Simplified track condition category. |
| `historical_section_delay_minutes` | Historical average delay for the current route section. |

## Cleaning and feature engineering

[`scripts/preprocess_eta_data.py`](../scripts/preprocess_eta_data.py) performs:

- strict raw-schema validation and timestamp parsing with invalid values
  coerced to missing;
- exact observation deduplication;
- invalid-range handling for speed, distance, delay, and coordinates;
- required-row removal for unusable identifiers/timestamps;
- route-median then global-median numeric imputation;
- categorical mode imputation;
- reasonable speed and station-dwell outlier capping;
- feature construction:
  `current_speed_kmh`, `distance_remaining_km`,
  `current_delay_minutes`, `scheduled_travel_time_min`,
  `historical_delay_minutes`, `station_dwell_time_min`, `route_section`,
  `progress_ratio`, `observation_hour`, and `day_of_week`.

## Target

`target_arrival_delay_minutes` is:

```text
actual_destination_arrival - scheduled_destination_arrival
```

It is measured in minutes. Negative values mean early arrival; positive values
mean late arrival.

## Outputs and split

The pipeline writes:

- `data/processed/eta_features.csv`: cleaned, human-readable engineered data;
- `data/processed/train.csv`: model-ready, one-hot encoded chronological train set;
- `data/processed/test.csv`: model-ready, one-hot encoded chronological test set;
- `data/processed/metadata.json`: schema, target definition, cleaning counts, and split details.

The split is chronological (first 80% of service dates for training, final 20%
for testing) to avoid future observations leaking into training.

Run the full pipeline:

```bash
python3 scripts/generate_synthetic_dataset.py
python3 scripts/preprocess_eta_data.py
```
