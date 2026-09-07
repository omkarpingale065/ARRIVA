# ARRIVA Day 2, Step 1: Train Movement Simulator

The simulator is an independent Python module. It does not open network
connections and does not depend on FastAPI, WebSockets, or the frontend.

## Architecture

- `Route`: immutable station, distance, travel-time, and coordinate definition.
- `TrainState`: serializable state returned to callers.
- `_TrainRuntime`: internal mutable state for dwell time, seeded randomness,
  and temporary disruptions.
- `TrainSimulator`: registry and public API for multiple trains.

Public methods:

```python
simulator.add_train(...)
simulator.advance_train(train_id, minutes)
simulator.get_train_state(train_id)
simulator.get_all_train_states()
```

Movement is section-based. The simulator advances a train through a section
using speed and distance, transitions to the next station when the section is
complete, then applies a realistic station dwell. Speed variation is bounded
and can be affected by rain/wet track, congestion, or temporary slowdowns.
Delay is derived from elapsed simulated time versus the route schedule rather
than assigned independently. Coordinates are interpolated between station
coordinates, and distance remaining never increases.

Supplying a seed makes the per-train random streams reproducible:

```python
simulator = TrainSimulator(seed=42)
```

## Run the demo

From the repository root:

```bash
PYTHONPATH=. python3 scripts/run_simulator_demo.py
```

The demo prints a state before and after advancing Train 12123 by five minutes,
plus the state of a second train.

## Run tests

```bash
PYTHONPATH=. python3 -m unittest discover -s tests -v
```

This simulator produces synthetic prototype movement states. It is not a real
GPS feed and should not be described as live railway data.
