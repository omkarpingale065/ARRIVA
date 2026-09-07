import unittest
from datetime import datetime

from simulator.train_simulator import TrainSimulator


class TrainSimulatorTests(unittest.TestCase):
    def build_simulator(self, seed=7):
        simulator = TrainSimulator(seed=seed, start_time=datetime(2026, 3, 1, 6, 0))
        simulator.add_train("T1", "12123", "Deccan Express")
        simulator.add_train("T2", "11017", "Konark Express", route_id="MUMBAI_NASHIK")
        return simulator

    def test_advancing_changes_position_and_reduces_distance(self):
        simulator = self.build_simulator()
        before = simulator.get_train_state("T1")
        after = simulator.advance_train("T1", 5)
        self.assertNotEqual((before["latitude"], before["longitude"]), (after["latitude"], after["longitude"]))
        self.assertLess(after["distance_remaining_km"], before["distance_remaining_km"])
        self.assertGreater(after["elapsed_minutes"], before["elapsed_minutes"])

    def test_station_transition_updates_route_state(self):
        simulator = self.build_simulator()
        after = simulator.advance_train("T1", 50)
        self.assertEqual(after["current_station"], "Lonavala")
        self.assertEqual(after["next_station"], "Karjat")
        self.assertEqual(after["route_section"], "Lonavala->Karjat")
        self.assertIn(after["status"], {"dwelling", "running", "running_late"})

    def test_seed_makes_multiple_train_runs_reproducible(self):
        first = self.build_simulator(seed=19)
        second = self.build_simulator(seed=19)
        for train_id in ("T1", "T2"):
            first.advance_train(train_id, 35)
            second.advance_train(train_id, 35)
        self.assertEqual(first.get_all_train_states(), second.get_all_train_states())

    def test_invalid_inputs_are_rejected(self):
        simulator = self.build_simulator()
        with self.assertRaises(ValueError):
            simulator.advance_train("T1", 0)
        with self.assertRaises(KeyError):
            simulator.get_train_state("missing")

    def test_demo_disruption_sets_delay_and_conflict_section(self):
        simulator = self.build_simulator()
        source_section = simulator.get_train_state("T1")["route_section"]
        disrupted = simulator.inject_disruption("T1", 10, delay_minutes=20, conflict_section=source_section)
        self.assertGreaterEqual(disrupted["current_delay_minutes"], 20)
        self.assertEqual(disrupted["route_section"], source_section)


if __name__ == "__main__":
    unittest.main()
