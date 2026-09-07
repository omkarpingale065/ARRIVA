"""Small, replaceable interfaces for ARRIVA ingestion sources.

The adapters deliberately return the same dictionaries as the existing
simulator, so callers can migrate without changing the API contract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from time import monotonic
from typing import Any

import httpx

from simulator import TrainSimulator


class DataSource(ABC):
    """Replaceable source for positions, signal state, and weather observations."""

    @abstractmethod
    def get_train_positions(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_signal_state(self, train_id: str) -> str:
        raise NotImplementedError


class TrainDataSource(DataSource):
    """Compatibility name for train-focused data sources."""

    @abstractmethod
    def get_train_state(self, train_id: str) -> dict[str, Any]:
        raise NotImplementedError

    def get_all_train_states(self) -> list[dict[str, Any]]:
        return self.get_train_positions()


class SimulatedTrainDataSource(TrainDataSource):
    """Compatibility adapter around the existing :class:`TrainSimulator`."""

    def __init__(self, simulator: TrainSimulator) -> None:
        self.simulator = simulator

    def get_train_state(self, train_id: str) -> dict[str, Any]:
        return self.simulator.get_train_state(train_id)

    def get_all_train_states(self) -> list[dict[str, Any]]:
        return self.simulator.get_all_train_states()

    def get_train_positions(self) -> list[dict[str, Any]]:
        return self.simulator.get_all_train_states()

    def get_signal_state(self, train_id: str) -> str:
        return self.simulator.get_train_state(train_id)["signal_aspect"]

    def add_train(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return self.simulator.add_train(*args, **kwargs)

    def advance_train(self, train_id: str, minutes: float) -> dict[str, Any]:
        return self.simulator.advance_train(train_id, minutes)

    def inject_disruption(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return self.simulator.inject_disruption(*args, **kwargs)


@dataclass(frozen=True)
class WeatherData:
    """Normalized weather observation used by ETA feature generation."""

    condition: str = "clear"
    temperature_c: float | None = None
    precipitation_mm: float | None = None
    wind_speed_kmh: float | None = None
    weather_code: int | None = None
    is_fallback: bool = False


class WeatherDataSource:
    """Fetch current weather from Open-Meteo with a safe deterministic fallback.

    ``http_client`` can be an ``httpx.Client`` or a small test double exposing
    ``get``. Network errors, malformed responses, and non-2xx responses all
    return clear weather rather than interrupting train operations.
    """

    endpoint = "https://api.open-meteo.com/v1/forecast"

    def __init__(
        self,
        http_client: Any | None = None,
        timeout_seconds: float = 2.0,
        endpoint: str | None = None,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero")
        self.http_client = http_client or httpx.Client()
        self.timeout_seconds = timeout_seconds
        self.endpoint = endpoint or self.endpoint
        self._cache: dict[tuple[float, float], tuple[float, WeatherData]] = {}
        self.cache_seconds = 60.0

    def get_weather(self, latitude: float, longitude: float) -> WeatherData:
        key = (round(latitude, 3), round(longitude, 3))
        cached = self._cache.get(key)
        if cached and monotonic() - cached[0] < self.cache_seconds:
            return cached[1]
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,precipitation,wind_speed_10m,weather_code",
            "timezone": "UTC",
        }
        try:
            response = self.http_client.get(
                self.endpoint, params=params, timeout=self.timeout_seconds
            )
            response.raise_for_status()
            current = response.json()["current"]
            code = int(current["weather_code"])
            weather = WeatherData(
                condition=self._condition_for_code(code),
                temperature_c=float(current["temperature_2m"]),
                precipitation_mm=float(current["precipitation"]),
                wind_speed_kmh=float(current["wind_speed_10m"]),
                weather_code=code,
            )
            self._cache[key] = (monotonic(), weather)
            return weather
        except Exception:
            return WeatherData(is_fallback=True)

    # Short alias useful to generic ingestion callers.
    fetch = get_weather

    @staticmethod
    def _condition_for_code(code: int) -> str:
        if code in {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82}:
            return "rain"
        if code in {71, 73, 75, 77, 85, 86}:
            return "snow"
        if code in {1, 2, 3, 45, 48}:
            return "cloudy"
        if code in {95, 96, 99}:
            return "storm"
        return "clear"
