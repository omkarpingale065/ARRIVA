"""Deterministic, stateful train movement simulator for the ARRIVA prototype.

This module is deliberately independent from FastAPI, WebSockets, and the
frontend. It models a small set of Maharashtra-style routes using synthetic
coordinates and operational rules.
"""

from __future__ import annotations

import copy
import random
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any


@dataclass(frozen=True)
class Route:
    route_id: str
    stations: tuple[str, ...]
    station_codes: tuple[str, ...]
    distances_km: tuple[float, ...]
    travel_minutes: tuple[float, ...]
    coordinates: tuple[tuple[float, float], ...]


ROUTES = (
    Route(
        "PUNE_MUMBAI",
        ("Pune", "Lonavala", "Karjat", "Kalyan", "Mumbai"),
        ("PUNE", "LNL", "KJT", "KYN", "BCT"),
        (0.0, 64.0, 105.0, 145.0, 192.0),
        (0.0, 35.0, 70.0, 105.0, 140.0),
        ((18.5204, 73.8567), (18.7503, 73.4074), (19.0762, 73.3181), (19.2356, 73.1305), (19.0760, 72.8777)),
    ),
    Route(
        "MUMBAI_NASHIK",
        ("Mumbai", "Kalyan", "Kasara", "Nashik"),
        ("BCT", "KYN", "KSA", "NSK"),
        (0.0, 52.0, 116.0, 185.0),
        (0.0, 42.0, 98.0, 155.0),
        ((19.0760, 72.8777), (19.2356, 73.1305), (19.3940, 73.4760), (20.0110, 73.7905)),
    ),
    Route(
        "PUNE_SOLAPUR",
        ("Pune", "Daund", "Kurduvadi", "Solapur"),
        ("PUNE", "DD", "KWV", "SUR"),
        (0.0, 75.0, 180.0, 265.0),
        (0.0, 55.0, 135.0, 205.0),
        ((18.5204, 73.8567), (18.4655, 74.5874), (18.0320, 75.1050), (17.6599, 75.9064)),
    ),
)


@dataclass
class TrainState:
    train_id: str
    train_number: str
    train_name: str
    origin: str
    destination: str
    origin_code: str
    destination_code: str
    current_station: str
    next_station: str | None
    latitude: float
    longitude: float
    current_speed_kmh: float
    current_delay_minutes: float
    distance_remaining_km: float
    scheduled_destination_arrival: str
    route_section: str
    station_dwell_time_min: float
    weather_condition: str
    track_condition: str
    signal_aspect: str
    status: str
    simulated_at: str
    route_id: str
    station_index: int
    section_progress_km: float
    elapsed_minutes: float
    progress_ratio: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class _TrainRuntime:
    state: TrainState
    route: Route
    departure_time: datetime
    dwell_remaining_min: float
    rng: random.Random
    disruption_remaining_min: float = 0.0
    disruption_kind: str | None = None
    forced_route_section: str | None = None


class TrainSimulator:
    """Manage reproducible movement for multiple simulated trains."""

    def __init__(self, seed: int | None = None, start_time: datetime | None = None) -> None:
        self.seed = seed
        self.start_time = start_time or datetime(2026, 3, 1, 6, 0)
        self._master_rng = random.Random(seed)
        self._trains: dict[str, _TrainRuntime] = {}

    def add_train(
        self,
        train_id: str,
        train_number: str,
        train_name: str,
        route_id: str = "PUNE_MUMBAI",
        scheduled_departure: datetime | None = None,
        initial_delay_minutes: float = 0.0,
        weather_condition: str = "clear",
        track_condition: str = "normal",
        signal_aspect: str | None = None,
        origin_code: str | None = None,
        destination_code: str | None = None,
    ) -> dict[str, Any]:
        if train_id in self._trains:
            raise ValueError(f"Train {train_id!r} is already registered.")
        route = next((item for item in ROUTES if item.route_id == route_id), None)
        if route is None:
            raise ValueError(f"Unknown route_id: {route_id}")

        departure = scheduled_departure or self.start_time
        rng = random.Random(self._master_rng.randint(0, 2**32 - 1))
        selected_signal = signal_aspect or rng.choice(
            ["GREEN", "GREEN", "DOUBLE_YELLOW", "YELLOW", "RED"]
        )
        if selected_signal not in {"GREEN", "YELLOW", "DOUBLE_YELLOW", "RED"}:
            raise ValueError(f"Unknown signal_aspect: {selected_signal}")
        scheduled_arrival = departure + timedelta(minutes=route.travel_minutes[-1])
        state = TrainState(
            train_id=train_id,
            train_number=train_number,
            train_name=train_name,
            origin=route.stations[0],
            destination=route.stations[-1],
            origin_code=origin_code or route.station_codes[0],
            destination_code=destination_code or route.station_codes[-1],
            current_station=route.stations[0],
            next_station=route.stations[1],
            latitude=route.coordinates[0][0],
            longitude=route.coordinates[0][1],
            current_speed_kmh=0.0,
            current_delay_minutes=round(initial_delay_minutes, 2),
            distance_remaining_km=route.distances_km[-1],
            scheduled_destination_arrival=scheduled_arrival.isoformat(),
            route_section=f"{route.stations[0]}->{route.stations[1]}",
            station_dwell_time_min=0.0,
            weather_condition=weather_condition,
            track_condition=track_condition,
            signal_aspect=selected_signal,
            status="dwelling",
            simulated_at=departure.isoformat(),
            route_id=route.route_id,
            station_index=0,
            section_progress_km=0.0,
            elapsed_minutes=0.0,
            progress_ratio=0.0,
        )
        self._trains[train_id] = _TrainRuntime(
            state=state,
            route=route,
            departure_time=departure,
            dwell_remaining_min=2.0,
            rng=rng,
        )
        return self.get_train_state(train_id)

    def get_train_state(self, train_id: str) -> dict[str, Any]:
        runtime = self._get_runtime(train_id)
        return copy.deepcopy(runtime.state.to_dict())

    def get_all_train_states(self) -> list[dict[str, Any]]:
        return [self.get_train_state(train_id) for train_id in sorted(self._trains)]

    def advance_train(self, train_id: str, minutes: float) -> dict[str, Any]:
        if minutes <= 0:
            raise ValueError("minutes must be greater than zero.")
        runtime = self._get_runtime(train_id)
        remaining = float(minutes)
        while remaining > 1e-9 and runtime.state.station_index < len(runtime.route.stations) - 1:
            if runtime.dwell_remaining_min > 0:
                consumed = min(remaining, runtime.dwell_remaining_min)
                runtime.dwell_remaining_min -= consumed
                remaining -= consumed
                runtime.state.elapsed_minutes += consumed
                runtime.state.current_speed_kmh = 0.0
                runtime.state.station_dwell_time_min += consumed
                runtime.state.status = "dwelling" if runtime.dwell_remaining_min > 0 else "running"
                continue
            consumed = self._advance_running(runtime, remaining)
            remaining -= consumed

        self._refresh_state(runtime)
        return self.get_train_state(train_id)

    def inject_disruption(
        self,
        train_id: str,
        duration_minutes: float,
        delay_minutes: float = 0.0,
        conflict_section: str | None = None,
    ) -> dict[str, Any]:
        """Inject a controlled operational disruption for a repeatable demo."""
        if duration_minutes <= 0:
            raise ValueError("duration_minutes must be greater than zero.")
        if delay_minutes < 0:
            raise ValueError("delay_minutes cannot be negative.")
        runtime = self._get_runtime(train_id)
        runtime.disruption_remaining_min = float(duration_minutes)
        runtime.disruption_kind = "demo_disruption"
        runtime.forced_route_section = conflict_section
        runtime.state.elapsed_minutes += float(delay_minutes)
        self._refresh_state(runtime)
        return self.get_train_state(train_id)

    def _advance_running(self, runtime: _TrainRuntime, available_minutes: float) -> float:
        state = runtime.state
        route = runtime.route
        index = state.station_index
        section_distance = route.distances_km[index + 1] - route.distances_km[index]
        remaining_section = section_distance - state.section_progress_km
        expected_speed = section_distance / ((route.travel_minutes[index + 1] - route.travel_minutes[index]) / 60)

        if runtime.disruption_remaining_min <= 0:
            roll = runtime.rng.random()
            if roll < 0.08:
                runtime.disruption_remaining_min = runtime.rng.uniform(2, 5)
                runtime.disruption_kind = "temporary_delay"
            elif roll < 0.16:
                runtime.disruption_remaining_min = runtime.rng.uniform(3, 8)
                runtime.disruption_kind = "congestion"
            else:
                runtime.disruption_kind = None

        speed_factor = 1.0
        if runtime.disruption_kind == "temporary_delay":
            speed_factor = 0.45
        elif runtime.disruption_kind == "congestion":
            speed_factor = 0.65
        if state.weather_condition == "rain" or state.track_condition == "wet":
            speed_factor *= 0.82
        target_speed = max(18.0, expected_speed * speed_factor + runtime.rng.uniform(-4, 4))
        state.current_speed_kmh = round(max(0.0, target_speed), 2)
        minutes_to_station = remaining_section / state.current_speed_kmh * 60
        consumed = min(available_minutes, minutes_to_station)
        distance_moved = state.current_speed_kmh * consumed / 60
        state.section_progress_km += distance_moved
        state.elapsed_minutes += consumed
        if runtime.disruption_remaining_min > 0:
            runtime.disruption_remaining_min = max(0.0, runtime.disruption_remaining_min - consumed)
            if runtime.disruption_remaining_min == 0:
                runtime.disruption_kind = None

        if consumed >= minutes_to_station - 1e-9:
            state.section_progress_km = 0.0
            state.station_index += 1
            state.current_station = route.stations[state.station_index]
            state.next_station = (
                route.stations[state.station_index + 1]
                if state.station_index + 1 < len(route.stations)
                else None
            )
            if state.next_station is None:
                state.status = "arrived"
                state.current_speed_kmh = 0.0
                runtime.dwell_remaining_min = 0.0
            else:
                runtime.dwell_remaining_min = 2.0 + runtime.rng.uniform(0, 3)
                state.status = "dwelling"
        return consumed

    def _refresh_state(self, runtime: _TrainRuntime) -> None:
        state = runtime.state
        route = runtime.route
        index = state.station_index
        if state.next_station is None:
            state.distance_remaining_km = 0.0
            state.route_section = f"{state.current_station}->{state.destination}"
        else:
            state.distance_remaining_km = round(
                max(0.0, route.distances_km[-1] - route.distances_km[index] - state.section_progress_km),
                2,
            )
            state.route_section = runtime.forced_route_section or f"{state.current_station}->{state.next_station}"
        state.progress_ratio = round(
            min(
                1.0,
                max(
                    0.0,
                    (route.distances_km[index] + state.section_progress_km)
                    / max(route.distances_km[-1], 1),
                ),
            ),
            4,
        )

        scheduled_elapsed = route.travel_minutes[index] + state.section_progress_km / max(
            route.distances_km[index + 1] - route.distances_km[index], 1
        ) * (route.travel_minutes[index + 1] - route.travel_minutes[index]) if state.next_station else route.travel_minutes[-1]
        state.current_delay_minutes = round(
            max(-5.0, state.elapsed_minutes - scheduled_elapsed),
            2,
        )
        state.simulated_at = (runtime.departure_time + timedelta(minutes=state.elapsed_minutes)).isoformat()
        if state.status != "arrived" and state.status != "dwelling":
            state.status = "running_late" if state.current_delay_minutes > 3 else "running"

        if state.next_station:
            start = route.coordinates[index]
            end = route.coordinates[index + 1]
            ratio = state.section_progress_km / max(route.distances_km[index + 1] - route.distances_km[index], 1)
            state.latitude = round(start[0] + (end[0] - start[0]) * ratio, 6)
            state.longitude = round(start[1] + (end[1] - start[1]) * ratio, 6)
        else:
            state.latitude, state.longitude = route.coordinates[-1]

    def _get_runtime(self, train_id: str) -> _TrainRuntime:
        try:
            return self._trains[train_id]
        except KeyError as exc:
            raise KeyError(f"Unknown train_id: {train_id}") from exc
