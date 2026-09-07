"""Print repeated Dynamic ETA Engine predictions for one simulated train."""

from datetime import datetime
import json

from eta_engine import DynamicETAEngine
from simulator import TrainSimulator


def main() -> None:
    simulator = TrainSimulator(seed=42, start_time=datetime(2026, 3, 1, 6, 0))
    simulator.add_train("ARRIVA-12123", "12123", "Deccan Express")
    engine = DynamicETAEngine()
    predictions = []
    for minutes in (0, 5, 5):
        if minutes:
            simulator.advance_train("ARRIVA-12123", minutes)
        predictions.append(engine.predict(simulator.get_train_state("ARRIVA-12123")))
    print(json.dumps({"predictions": predictions, "history": engine.get_prediction_history("ARRIVA-12123")}, indent=2))


if __name__ == "__main__":
    main()
