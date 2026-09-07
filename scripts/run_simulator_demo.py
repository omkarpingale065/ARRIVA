"""Print a deterministic before/after simulator example."""

from datetime import datetime
import json

from simulator.train_simulator import TrainSimulator


def main() -> None:
    simulator = TrainSimulator(seed=42, start_time=datetime(2026, 3, 1, 6, 0))
    simulator.add_train("ARRIVA-12123", "12123", "Deccan Express")
    simulator.add_train(
        "ARRIVA-11017",
        "11017",
        "Konark Express",
        route_id="MUMBAI_NASHIK",
        weather_condition="cloudy",
    )
    before = simulator.get_train_state("ARRIVA-12123")
    after = simulator.advance_train("ARRIVA-12123", 5)
    print("Before:")
    print(json.dumps(before, indent=2))
    print("After 5 minutes:")
    print(json.dumps(after, indent=2))
    print("All trains:")
    print(json.dumps(simulator.get_all_train_states(), indent=2))


if __name__ == "__main__":
    main()
