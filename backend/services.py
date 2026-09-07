from __future__ import annotations

import logging
import json
import os
from json import JSONDecodeError
from datetime import datetime
from pathlib import Path
from typing import Any

from eta_engine import DynamicETAEngine
from simulator import TrainSimulator
from simulator.train_simulator import ROUTES
from .ingestion import SimulatedTrainDataSource, WeatherDataSource
from .repository import PredictionRepository

logger = logging.getLogger(__name__)
BASELINE_REPORT = Path(__file__).resolve().parents[1] / "data/processed/model/baseline_comparison.json"
TRAINING_REPORT = Path(__file__).resolve().parents[1] / "ml/models/training_report.json"


class ARRIVAService:
    """Application service coordinating simulator state and ETA inference."""

    def __init__(
        self,
        seed: int = 42,
        db_path: str | Path | None = None,
        prediction_repository: PredictionRepository | None = None,
        weather_source: WeatherDataSource | None = None,
    ) -> None:
        self._seed = seed
        self._start_time = datetime(2026, 3, 1, 6, 0)
        self.simulator = TrainSimulator(seed=self._seed, start_time=self._start_time)
        self.train_source = SimulatedTrainDataSource(self.simulator)
        self.weather_source = weather_source or (
            WeatherDataSource(timeout_seconds=float(os.getenv("ARRIVA_WEATHER_TIMEOUT", "2")))
            if os.getenv("ARRIVA_WEATHER_ENABLED", "true").lower() not in {"0", "false", "no"}
            else None
        )
        self.eta_engine = DynamicETAEngine()
        self.prediction_repository = prediction_repository or PredictionRepository(
            db_path or os.getenv("ARRIVA_DB_PATH", "data/arriva.sqlite3")
        )
        self._seed_trains()

    def _seed_trains(self) -> None:
        self.train_source.add_train("ARRIVA-12123", "12123", "Deccan Express")
        self.train_source.add_train(
            "ARRIVA-11017",
            "11017",
            "Konark Express",
            route_id="MUMBAI_NASHIK",
            weather_condition="cloudy",
        )
        self.train_source.add_train(
            "ARRIVA-22123",
            "22123",
            "Solapur Express",
            route_id="PUNE_SOLAPUR",
            initial_delay_minutes=8,
            weather_condition="rain",
            track_condition="wet",
        )
        roster = [
            ("12951", "Mumbai Rajdhani", "MUMBAI_NASHIK"),
            ("12002", "Bhopal Shatabdi", "PUNE_MUMBAI"),
            ("18238", "Chhattisgarh Express", "PUNE_SOLAPUR"),
            ("12622", "Tamil Nadu Express", "MUMBAI_NASHIK"),
            ("12951A", "Punjab Mail", "PUNE_MUMBAI"),
            ("16032", "Andaman Express", "PUNE_SOLAPUR"),
            ("12127", "Intercity Express", "PUNE_MUMBAI"),
            ("11010", "Deccan Queen", "PUNE_MUMBAI"),
            ("12109", "Panchavati Express", "MUMBAI_NASHIK"),
        ]
        target_count = max(3, int(os.getenv("ARRIVA_SIMULATED_TRAIN_COUNT", "12")))
        for index, (train_number, train_name, route_id) in enumerate(roster, start=4):
            if index > target_count:
                break
            self.train_source.add_train(
                f"ARRIVA-{train_number}",
                train_number,
                train_name,
                route_id=route_id,
                initial_delay_minutes=(index % 7) * 0.5,
                weather_condition="clear",
            )
        route_ids = ["PUNE_MUMBAI", "MUMBAI_NASHIK", "PUNE_SOLAPUR"]
        for index in range(4 + len(roster), target_count + 1):
            route_id = route_ids[(index - 1) % len(route_ids)]
            self.train_source.add_train(
                f"ARRIVA-SIM-{index:05d}", f"SIM{index:05d}",
                f"Prototype Service {index:05d}", route_id=route_id,
                initial_delay_minutes=(index % 7) * 0.5, weather_condition="clear",
            )

    def list_trains(self) -> list[dict[str, Any]]:
        return self.train_source.get_all_train_states()

    def reset_simulation(self) -> list[dict[str, Any]]:
        """Restore the seeded simulator and clear transient prediction history."""
        self.simulator = TrainSimulator(seed=self._seed, start_time=self._start_time)
        self.train_source = SimulatedTrainDataSource(self.simulator)
        self.eta_engine.clear_history()
        self.prediction_repository.clear()
        self._seed_trains()
        logger.info("Reset simulator to its deterministic initial state")
        return self.train_source.get_all_train_states()

    def get_model_comparison(self) -> dict[str, Any]:
        report = json.loads(BASELINE_REPORT.read_text(encoding="utf-8"))
        training = json.loads(TRAINING_REPORT.read_text(encoding="utf-8"))
        return {
            "naive_mae": float(report["naive_mae"]),
            "model_mae": float(report["model_mae"]),
            "mae_reduction_percent": float(report["mae_reduction_percent"]),
            "selected_model": training.get("selected_model"),
            "models": training.get("metrics", []),
        }

    def get_model_metrics(self) -> dict[str, Any]:
        try:
            report = json.loads(TRAINING_REPORT.read_text(encoding="utf-8"))
            selected = next(item for item in report["metrics"] if item["model"] == report["selected_model"])
            selection_reason = report["selection_reason"]
            train_rows = report["train_rows"]
            test_rows = report["test_rows"]
            feature_count = report["feature_count"]
        except (OSError, JSONDecodeError, KeyError, StopIteration, TypeError) as exc:
            raise ValueError("Model training metrics are unavailable or malformed.") from exc
        return {
            "selected_model": report["selected_model"],
            "selection_reason": selection_reason,
            "train_rows": train_rows,
            "test_rows": test_rows,
            "feature_count": feature_count,
            "selected": selected,
            "metrics": report["metrics"],
        }

    def get_train(self, train_id: str) -> dict[str, Any]:
        return self.train_source.get_train_state(train_id)

    def _state_with_weather(self, state: dict[str, Any]) -> dict[str, Any]:
        """Overlay live weather only when an ingestion source was explicitly set."""
        if self.weather_source is None:
            return state
        weather = self.weather_source.get_weather(state["latitude"], state["longitude"])
        if weather.is_fallback:
            return state
        enriched = state.copy()
        enriched["weather_condition"] = weather.condition
        if weather.condition in {"rain", "storm"}:
            enriched["track_condition"] = "wet"
        return enriched

    def get_eta(self, train_id: str) -> dict[str, Any]:
        state = self._state_with_weather(self.get_train(train_id))
        prediction = self.eta_engine.predict(state)
        impact = self.get_section_impact(train_id)
        prediction["recommendation"] = self._recommendation(state, prediction, impact)
        self.prediction_repository.write_prediction(prediction)
        return prediction

    def get_section_impact(self, train_id: str) -> dict[str, Any]:
        state = self._state_with_weather(self.get_train(train_id))
        prediction = self.eta_engine.predict(state)
        route = next(route for route in ROUTES if route.route_id == state["route_id"])
        current_section = state["route_section"]
        upcoming_sections = {
            f"{route.stations[index]}->{route.stations[index + 1]}"
            for index in range(
                state["station_index"] + 1,
                min(state["station_index"] + 3, len(route.stations) - 1),
            )
        }
        sections = {current_section} | upcoming_sections
        affected = []
        for candidate in self.train_source.get_all_train_states():
            if candidate["train_id"] == train_id:
                continue
            if candidate["route_section"] not in sections:
                continue
            conflict_type = "current" if candidate["route_section"] == current_section else "upcoming"
            added_delay = round(max(2.0, min(15.0, prediction["predicted_delay_minutes"] * 0.25 + 2.0)), 2)
            affected.append(
                {
                    "train_id": candidate["train_id"],
                    "train_number": candidate["train_number"],
                    "train_name": candidate["train_name"],
                    "route_section": candidate["route_section"],
                    "conflict_type": conflict_type,
                    "estimated_added_delay_minutes": added_delay,
                    "reason": f"Shared {conflict_type} section occupancy with {train_id}",
                }
            )
        impact = {"train_id": train_id, "route_section": state["route_section"], "affected_trains": affected}
        impact["recommendation"] = self._recommendation(state, prediction, impact)
        return impact

    @staticmethod
    def _recommendation(state: dict[str, Any], prediction: dict[str, Any], impact: dict[str, Any]) -> str | None:
        if prediction["risk_level"] != "HIGH" or not impact["affected_trains"]:
            return None
        affected = impact["affected_trains"][0]
        station = state["current_station"] or state["origin"]
        minutes = max(1, round(affected["estimated_added_delay_minutes"]))
        return f"Hold {state['train_id']} at {station} for {minutes} min to let {affected['train_id']} clear the section."

    def get_delay_risk(self, train_id: str) -> dict[str, Any]:
        prediction = self.get_eta(train_id)
        return {
            "train_id": train_id,
            "risk_level": prediction["risk_level"],
            "predicted_delay_minutes": prediction["predicted_delay_minutes"],
            "delay_factors": prediction["delay_factors"],
            "timestamp": prediction["timestamp"],
        }

    def get_history(
        self, train_id: str, *, page: int = 1, page_size: int = 50
    ) -> list[dict[str, Any]]:
        if page < 1 or page_size < 1:
            raise ValueError("page and page_size must be positive")
        offset = (page - 1) * page_size
        if self.prediction_repository.count_predictions(train_id) == 0:
            self.get_eta(train_id)
        return self.prediction_repository.read_predictions(
            train_id, limit=page_size, offset=offset
        )

    def advance(self, train_id: str, minutes: float) -> tuple[dict[str, Any], dict[str, Any]]:
        state = self.train_source.advance_train(train_id, minutes)
        state = self._state_with_weather(state)
        prediction = self.eta_engine.predict(state)
        # Each advance is a durable snapshot, including updates produced by the
        # websocket's periodic advance loop.
        self.prediction_repository.write_prediction(prediction)
        logger.info("Advanced %s by %s minutes; risk=%s", train_id, minutes, prediction["risk_level"])
        return state, prediction

    def advance_all(self, minutes: float) -> list[dict[str, Any]]:
        """Advance every registered train once and build live update payloads."""
        updates = []
        for state in self.train_source.get_all_train_states():
            updated_state, prediction = self.advance(state["train_id"], minutes)
            updates.append(
                {
                    "train_id": updated_state["train_id"],
                    "timestamp": updated_state["simulated_at"],
                    "latitude": updated_state["latitude"],
                    "longitude": updated_state["longitude"],
                    "current_speed": updated_state["current_speed_kmh"],
                    "current_delay": updated_state["current_delay_minutes"],
                    "distance_remaining": updated_state["distance_remaining_km"],
                    "predicted_delay": prediction["predicted_delay_minutes"],
                    "predicted_arrival": prediction["predicted_arrival"],
                    "delay_risk": prediction["risk_level"],
                    "confidence_percent": prediction["confidence_percent"],
                    "progress_percent": round(updated_state["progress_ratio"] * 100, 1),
                    "next_station": updated_state["next_station"],
                }
            )
        return updates

    def inject_disruption(
        self,
        train_id: str,
        affected_train_id: str | None,
        duration_minutes: float,
        delay_minutes: float,
    ) -> dict[str, Any]:
        """Create a deterministic shared-section conflict for demonstrations."""
        disrupted = self.get_train(train_id)
        candidates = [
            state for state in self.train_source.get_all_train_states()
            if state["train_id"] != train_id
        ]
        if affected_train_id is None:
            if not candidates:
                raise ValueError("At least two trains are required for a disruption demo.")
            affected_train_id = candidates[0]["train_id"]
        affected = self.get_train(affected_train_id)
        section = disrupted["route_section"]
        disrupted = self.train_source.inject_disruption(
            train_id, duration_minutes, delay_minutes, conflict_section=section
        )
        affected = self.train_source.inject_disruption(
            affected_train_id, duration_minutes, conflict_section=section
        )
        eta = self.get_eta(train_id)
        impact = self.get_section_impact(train_id)
        logger.info(
            "Injected demo disruption: %s conflicts with %s in %s",
            train_id,
            affected_train_id,
            section,
        )
        return {
            "disrupted_train": disrupted,
            "affected_train": affected,
            "section_impact": impact,
            "eta": eta,
        }
