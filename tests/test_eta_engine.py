import unittest
from datetime import datetime

from eta_engine import DynamicETAEngine
from simulator import TrainSimulator


class DynamicETAEngineTests(unittest.TestCase):
    def setUp(self):
        self.simulator = TrainSimulator(seed=11, start_time=datetime(2026, 3, 1, 6, 0))
        self.simulator.add_train("T1", "12123", "Deccan Express")
        self.engine = DynamicETAEngine()

    def test_normal_train_prediction(self):
        result = self.engine.predict(self.simulator.get_train_state("T1"))
        self.assertIn(result["risk_level"], {"LOW", "MEDIUM", "HIGH"})
        self.assertIsInstance(result["predicted_delay_minutes"], float)
        self.assertTrue(result["upcoming_station_etas"])
        self.assertLessEqual(result["eta_lower_bound"], result["predicted_arrival"])
        self.assertLessEqual(result["predicted_arrival"], result["eta_upper_bound"])

    def test_delayed_train_has_supported_delay_factor(self):
        state = self.simulator.get_train_state("T1")
        state["current_delay_minutes"] = 18.0
        result = self.engine.predict(state)
        self.assertTrue(any(item["factor"] == "current_delay" for item in result["delay_factors"]))
        self.assertIn(result["risk_level"], {"MEDIUM", "HIGH"})

    def test_slow_train_exposes_low_speed_factor(self):
        state = self.simulator.get_train_state("T1")
        state["current_speed_kmh"] = 20.0
        result = self.engine.predict(state)
        self.assertTrue(any(item["factor"] == "low_speed" for item in result["delay_factors"]))

    def test_restrictive_signal_changes_prediction_and_explanation(self):
        clear_state = self.simulator.get_train_state("T1")
        clear_state["signal_aspect"] = "GREEN"
        red_state = dict(clear_state)
        red_state["signal_aspect"] = "RED"
        clear_prediction = self.engine.predict(clear_state)
        red_prediction = self.engine.predict(red_state)
        self.assertGreater(red_prediction["predicted_delay_minutes"], clear_prediction["predicted_delay_minutes"])
        self.assertTrue(any(item["factor"] == "signal_aspect" for item in red_prediction["delay_factors"]))

    def test_near_destination_has_no_invalid_station_eta(self):
        state = self.simulator.get_train_state("T1")
        state.update(
            {
                "station_index": 3,
                "current_station": "Kalyan",
                "next_station": "Mumbai",
                "route_section": "Kalyan->Mumbai",
                "section_progress_km": 46.0,
                "distance_remaining_km": 1.0,
                "current_speed_kmh": 45.0,
            }
        )
        result = self.engine.predict(state)
        self.assertEqual(result["upcoming_station_etas"][-1]["station"], "Mumbai")

    def test_repeated_prediction_is_stored(self):
        self.engine.predict(self.simulator.get_train_state("T1"))
        self.simulator.advance_train("T1", 5)
        self.engine.predict(self.simulator.get_train_state("T1"))
        history = self.engine.get_prediction_history("T1")
        self.assertEqual(len(history), 2)
        self.assertNotEqual(history[0]["timestamp"], history[1]["timestamp"])
        self.assertEqual(history[1]["train_id"], "T1")

    def test_historical_delay_feature_uses_prior_observations(self):
        state = self.simulator.get_train_state("T1")
        first = dict(state)
        first["current_delay_minutes"] = 6.0
        self.engine.predict(first)
        second = dict(state)
        second["current_delay_minutes"] = 10.0
        features = self.engine._state_to_features(second)
        self.assertEqual(features.loc[0, "historical_delay_minutes"], 6.0)


if __name__ == "__main__":
    unittest.main()
