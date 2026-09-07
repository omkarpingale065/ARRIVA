from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


RiskLevel = Literal["LOW", "MEDIUM", "HIGH"]


class TrainStateResponse(BaseModel):
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
    scheduled_destination_arrival: datetime
    route_section: str
    station_dwell_time_min: float
    weather_condition: str
    track_condition: str
    signal_aspect: str
    status: str
    simulated_at: datetime
    route_id: str
    station_index: int
    section_progress_km: float
    elapsed_minutes: float
    progress_ratio: float


class DelayFactor(BaseModel):
    factor: str
    detail: str
    contribution_minutes: float = 0.0


class StationETA(BaseModel):
    station: str
    predicted_arrival: datetime
    distance_from_current_km: float


class ETAPredictionResponse(BaseModel):
    timestamp: datetime
    train_id: str
    predicted_delay_minutes: float
    predicted_arrival: datetime
    eta_lower_bound: datetime
    eta_upper_bound: datetime
    confidence_percent: float = Field(ge=0, le=100)
    scheduled_destination_arrival: datetime
    current_speed: float
    current_delay: float
    distance_remaining: float
    risk_level: RiskLevel
    delay_factors: list[DelayFactor]
    upcoming_station_etas: list[StationETA]
    recommendation: str | None = None


class PredictionHistoryResponse(BaseModel):
    train_id: str
    predictions: list[ETAPredictionResponse]


class DelayRiskResponse(BaseModel):
    train_id: str
    risk_level: RiskLevel
    predicted_delay_minutes: float
    delay_factors: list[DelayFactor]
    timestamp: datetime


class SectionImpactTrain(BaseModel):
    train_id: str
    train_number: str
    train_name: str
    route_section: str
    conflict_type: Literal["current", "upcoming"]
    estimated_added_delay_minutes: float
    reason: str


class SectionImpactResponse(BaseModel):
    train_id: str
    route_section: str
    affected_trains: list[SectionImpactTrain]
    recommendation: str | None = None


class AdvanceSimulationRequest(BaseModel):
    train_id: str = Field(min_length=1)
    minutes: float = Field(gt=0, le=1440)


class AdvanceSimulationResponse(BaseModel):
    train: TrainStateResponse
    eta: ETAPredictionResponse


class InjectDisruptionRequest(BaseModel):
    train_id: str = Field(min_length=1)
    affected_train_id: str | None = Field(default=None, min_length=1)
    duration_minutes: float = Field(default=10.0, gt=0, le=120)
    delay_minutes: float = Field(default=20.0, ge=0, le=120)


class InjectDisruptionResponse(BaseModel):
    disrupted_train: TrainStateResponse
    affected_train: TrainStateResponse
    section_impact: SectionImpactResponse
    eta: ETAPredictionResponse


class ModelComparisonResponse(BaseModel):
    naive_mae: float
    model_mae: float
    mae_reduction_percent: float
    selected_model: str | None = None
    models: list[dict[str, Any]] = Field(default_factory=list)
