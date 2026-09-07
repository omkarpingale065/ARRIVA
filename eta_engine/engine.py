"""Inference-only dynamic ETA engine.

The engine loads the published Day 1 model once, adapts simulator states to the
exact one-hot feature schema, and keeps prediction history in memory.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from eta_model import load_model, predict_eta_delay  # noqa: E402
from simulator.train_simulator import ROUTES  # noqa: E402
from eta_engine.metrics import load_model_mae


class DynamicETAEngine:
    """Generate repeatable ETA predictions for one or more train states."""

    def __init__(
        self,
        model_path: str | Path = ROOT / "ml/models/eta_model.pkl",
        preprocessing_path: str | Path = ROOT / "ml/models/preprocessing.joblib",
    ) -> None:
        self.model_bundle = load_model(model_path)
        self.preprocessing = load_model(preprocessing_path)
        if self.model_bundle["feature_columns"] != self.preprocessing["feature_columns"]:
            raise ValueError("Model and preprocessing schemas do not match.")
        self.feature_columns = self.model_bundle["feature_columns"]
        self.model_mae = load_model_mae()
        self._history: dict[str, list[dict[str, Any]]] = {}

    def predict(self, train_state: dict[str, Any]) -> dict[str, Any]:
        """Predict destination and upcoming-station ETAs from one simulator state."""
        self._validate_state(train_state)
        features = self._state_to_features(train_state)
        predicted_delay = round(
            float(predict_eta_delay(self.model_bundle, features).iloc[0]), 2
        )
        signal_penalty = {
            "RED": 4.0,
            "YELLOW": 2.0,
            "DOUBLE_YELLOW": 1.0,
            "GREEN": 0.0,
        }[train_state["signal_aspect"]]
        predicted_delay = round(predicted_delay + signal_penalty, 2)
        scheduled_arrival = pd.Timestamp(train_state["scheduled_destination_arrival"])
        predicted_arrival = scheduled_arrival + pd.to_timedelta(predicted_delay, unit="m")
        eta_lower_bound = predicted_arrival - timedelta(minutes=self.model_mae)
        eta_upper_bound = predicted_arrival + timedelta(minutes=self.model_mae)
        horizon_minutes = max(
            (predicted_arrival - pd.Timestamp(train_state["simulated_at"])).total_seconds() / 60,
            1.0,
        )
        confidence_percent = round(
            max(0.0, min(100.0, 100.0 - (2 * self.model_mae / horizon_minutes * 100.0))),
            1,
        )
        risk_level = self._risk_level(train_state, predicted_delay)
        factors = self._explain_factors(train_state)
        result = {
            "timestamp": train_state["simulated_at"],
            "train_id": train_state["train_id"],
            "predicted_delay_minutes": predicted_delay,
            "predicted_arrival": predicted_arrival.isoformat(),
            "eta_lower_bound": eta_lower_bound.isoformat(),
            "eta_upper_bound": eta_upper_bound.isoformat(),
            "confidence_percent": confidence_percent,
            "scheduled_destination_arrival": scheduled_arrival.isoformat(),
            "current_speed": train_state["current_speed_kmh"],
            "current_delay": train_state["current_delay_minutes"],
            "distance_remaining": train_state["distance_remaining_km"],
            "risk_level": risk_level,
            "delay_factors": factors,
            "upcoming_station_etas": self._upcoming_station_etas(
                train_state, predicted_delay
            ),
        }
        self._history.setdefault(train_state["train_id"], []).append(result.copy())
        return result

    def get_prediction_history(self, train_id: str) -> list[dict[str, Any]]:
        """Return prediction records for a train in prediction order."""
        return [record.copy() for record in self._history.get(train_id, [])]

    def clear_history(self, train_id: str | None = None) -> None:
        """Clear one train's history or all in-memory prediction history."""
        if train_id is None:
            self._history.clear()
        else:
            self._history.pop(train_id, None)

    def _state_to_features(self, state: dict[str, Any]) -> pd.DataFrame:
        route = self._route(state["route_id"])
        row: dict[str, Any] = {column: 0 for column in self.feature_columns}
        row.update(
            {
                "station_sequence": state["station_index"],
                "current_speed_kmh": state["current_speed_kmh"],
                "distance_remaining_km": state["distance_remaining_km"],
                "current_delay_minutes": state["current_delay_minutes"],
                "scheduled_travel_time_min": route.travel_minutes[-1],
                "historical_delay_minutes": self._historical_delay_average(
                    state["train_id"]
                ),
                "station_dwell_time_min": state["station_dwell_time_min"],
                "progress_ratio": self._progress_ratio(state, route),
                "observation_hour": pd.Timestamp(state["simulated_at"]).hour,
                "day_of_week": pd.Timestamp(state["simulated_at"]).dayofweek,
            }
        )
        self._set_one_hot(row, "train_id", self._normalise_train_id(state))
        self._set_one_hot(row, "route_id", state["route_id"])
        section_id = self._section_id(state["route_section"])
        self._set_one_hot(row, "section_id", section_id)
        self._set_one_hot(row, "route_section", f"{state['route_id']}:{section_id}")
        self._set_one_hot(row, "weather_condition", state["weather_condition"])
        self._set_one_hot(row, "track_condition", state["track_condition"])
        self._set_one_hot(row, "signal_aspect", state["signal_aspect"])
        return pd.DataFrame([row], columns=self.feature_columns)

    def _historical_delay_average(self, train_id: str, window: int = 5) -> float:
        """Average previously observed delays for this train in this process."""
        history = self._history.get(train_id, [])[-window:]
        values = [float(item["current_delay"]) for item in history if "current_delay" in item]
        return round(sum(values) / len(values), 2) if values else 0.0

    def _upcoming_station_etas(
        self, state: dict[str, Any], predicted_delay: float
    ) -> list[dict[str, Any]]:
        route = self._route(state["route_id"])
        index = state["station_index"]
        if index >= len(route.stations) - 1:
            return []
        speed = max(float(state["current_speed_kmh"]), 30.0)
        current_distance = route.distances_km[index] + state["section_progress_km"]
        current_time = pd.Timestamp(state["simulated_at"])
        station_etas = []
        for destination_index in range(index + 1, len(route.stations)):
            distance = max(0.0, route.distances_km[destination_index] - current_distance)
            travel_minutes = distance / speed * 60
            dwell_minutes = 2.5 * max(0, destination_index - index - 1)
            predicted_time = current_time + timedelta(
                minutes=travel_minutes + dwell_minutes + predicted_delay
            )
            station_etas.append(
                {
                    "station": route.stations[destination_index],
                    "predicted_arrival": predicted_time.isoformat(),
                    "distance_from_current_km": round(distance, 2),
                }
            )
        return station_etas

    @staticmethod
    def _risk_level(state: dict[str, Any], predicted_delay: float) -> str:
        score = max(0.0, predicted_delay) + max(0.0, state["current_delay_minutes"]) * 0.7
        if state["current_speed_kmh"] < 35 or state["track_condition"] == "wet":
            score += 5
        if state["weather_condition"] == "rain":
            score += 4
        if state["distance_remaining_km"] > 150:
            score += 3
        if score >= 25:
            return "HIGH"
        if score >= 8:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _explain_factors(state: dict[str, Any]) -> list[dict[str, Any]]:
        factors: list[dict[str, Any]] = []
        if state["current_delay_minutes"] > 0:
            contribution = round(min(state["current_delay_minutes"] * 0.35, 8.0), 2)
            factors.append({"factor": "current_delay", "detail": f"+{state['current_delay_minutes']} minutes currently recorded", "contribution_minutes": contribution})
        if state["current_speed_kmh"] < 45:
            contribution = round(max(1.0, (45.0 - state["current_speed_kmh"]) / 15.0), 2)
            factors.append({"factor": "low_speed", "detail": f"{state['current_speed_kmh']} km/h current speed", "contribution_minutes": contribution})
        if state["distance_remaining_km"] > 150:
            factors.append({"factor": "distance_remaining", "detail": f"{state['distance_remaining_km']} km remaining", "contribution_minutes": 2.5})
        if state["station_dwell_time_min"] > 0:
            contribution = round(min(state["station_dwell_time_min"] * 0.15, 3.0), 2)
            factors.append({"factor": "station_dwell", "detail": f"{state['station_dwell_time_min']} minutes of dwell", "contribution_minutes": contribution})
        if state["weather_condition"] == "rain":
            factors.append({"factor": "weather", "detail": "Rain is active in the simulated state", "contribution_minutes": 2.0})
        if state["track_condition"] == "wet":
            factors.append({"factor": "track_condition", "detail": "Wet track is active in the simulated state", "contribution_minutes": 2.5})
        signal_contributions = {"RED": 4.0, "YELLOW": 2.0, "DOUBLE_YELLOW": 1.0}
        if state["signal_aspect"] in signal_contributions:
            contribution = signal_contributions[state["signal_aspect"]]
            factors.append({"factor": "signal_aspect", "detail": f"{state['signal_aspect']} signal aspect is restricting movement", "contribution_minutes": contribution})
        if state["status"] == "running_late":
            factors.append({"factor": "late_status", "detail": "Simulator marks the train as running late", "contribution_minutes": 1.5})
        if state["current_speed_kmh"] >= 90 and state["current_delay_minutes"] <= 0:
            factors.append({"factor": "recovery_speed", "detail": "High current speed with no recorded delay", "contribution_minutes": -1.0})
        return factors

    @staticmethod
    def _progress_ratio(state: dict[str, Any], route: Any) -> float:
        index = state["station_index"]
        if index >= len(route.stations) - 1:
            return 1.0
        section_length = route.distances_km[index + 1] - route.distances_km[index]
        return min(1.0, max(0.0, state["section_progress_km"] / section_length))

    @staticmethod
    def _section_id(route_section: str) -> str:
        return route_section.upper().replace("->", "_").replace(" ", "_")

    @staticmethod
    def _normalise_train_id(state: dict[str, Any]) -> str:
        raw = str(state.get("train_id", ""))
        digits = "".join(character for character in raw if character.isdigit())
        return digits or str(state.get("train_number", ""))

    @staticmethod
    def _route(route_id: str) -> Any:
        for route in ROUTES:
            if route.route_id == route_id:
                return route
        raise ValueError(f"Unknown route_id: {route_id}")

    @staticmethod
    def _set_one_hot(row: dict[str, Any], prefix: str, value: str) -> None:
        key = f"{prefix}_{value}"
        if key in row:
            row[key] = 1

    @staticmethod
    def _validate_state(state: dict[str, Any]) -> None:
        required = {
            "train_id",
            "route_id",
            "station_index",
            "current_speed_kmh",
            "current_delay_minutes",
            "distance_remaining_km",
            "scheduled_destination_arrival",
            "simulated_at",
            "route_section",
            "station_dwell_time_min",
            "weather_condition",
            "track_condition",
            "signal_aspect",
            "section_progress_km",
            "status",
        }
        missing = sorted(required - set(state))
        if missing:
            raise ValueError(f"Train state is missing required fields: {missing}")
