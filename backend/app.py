from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .schemas import (
    AdvanceSimulationRequest,
    AdvanceSimulationResponse,
    DelayRiskResponse,
    ETAPredictionResponse,
    PredictionHistoryResponse,
    TrainStateResponse,
    SectionImpactResponse,
    InjectDisruptionRequest,
    InjectDisruptionResponse,
    ModelComparisonResponse,
)
from .services import ARRIVAService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ARRIVA Train ETA API",
    description="Prototype REST API over the ARRIVA train simulator and Dynamic ETA Engine.",
    version="0.1.0",
)
allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        os.getenv(
        "ARRIVA_ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174",
        ),
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
service = ARRIVAService()


@app.exception_handler(KeyError)
async def key_error_handler(_request: Request, exc: KeyError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc).strip("'")})


@app.exception_handler(ValueError)
async def value_error_handler(_request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/api/model/comparison",
    response_model=ModelComparisonResponse,
    tags=["model"],
)
def get_model_comparison() -> dict[str, float]:
    return service.get_model_comparison()


@app.get("/api/model/metrics", tags=["model"])
def get_model_metrics() -> dict[str, Any]:
    return service.get_model_metrics()


@app.get("/api/trains", response_model=list[TrainStateResponse], tags=["trains"])
def list_trains() -> list[dict[str, Any]]:
    return service.list_trains()


@app.get("/api/trains/{train_id}", response_model=TrainStateResponse, tags=["trains"])
def get_train(train_id: str) -> dict[str, Any]:
    return service.get_train(train_id)


@app.get("/api/trains/{train_id}/eta", response_model=ETAPredictionResponse, tags=["eta"])
def get_eta(train_id: str) -> dict[str, Any]:
    return service.get_eta(train_id)


@app.get(
    "/api/trains/{train_id}/delay-risk",
    response_model=DelayRiskResponse,
    tags=["eta"],
)
def get_delay_risk(train_id: str) -> dict[str, Any]:
    return service.get_delay_risk(train_id)


@app.get(
    "/api/trains/{train_id}/section-impact",
    response_model=SectionImpactResponse,
    tags=["operations"],
)
def get_section_impact(train_id: str) -> dict[str, Any]:
    return service.get_section_impact(train_id)


@app.get(
    "/api/trains/{train_id}/history",
    response_model=PredictionHistoryResponse,
    tags=["eta"],
)
def get_history(
    train_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
) -> dict[str, Any]:
    return {
        "train_id": train_id,
        "predictions": service.get_history(train_id, page=page, page_size=page_size),
    }


@app.post(
    "/api/simulation/advance",
    response_model=AdvanceSimulationResponse,
    tags=["simulation"],
)
def advance_simulation(request: AdvanceSimulationRequest) -> dict[str, Any]:
    state, prediction = service.advance(request.train_id, request.minutes)
    return {"train": state, "eta": prediction}


@app.post(
    "/api/simulation/inject-disruption",
    response_model=InjectDisruptionResponse,
    tags=["simulation"],
)
def inject_disruption(request: InjectDisruptionRequest) -> dict[str, Any]:
    return service.inject_disruption(
        request.train_id,
        request.affected_train_id,
        request.duration_minutes,
        request.delay_minutes,
    )


@app.post(
    "/api/simulation/reset",
    response_model=list[TrainStateResponse],
    tags=["simulation"],
)
def reset_simulation() -> list[dict[str, Any]]:
    return service.reset_simulation()


@app.websocket("/ws/trains")
async def train_updates(
    websocket: WebSocket,
    interval_seconds: float = Query(default=5.0, gt=0.05, le=60.0),
    advance_minutes: float = Query(default=5.0, gt=0.0, le=60.0),
) -> None:
    """Stream simulator-backed updates for every train on each interval."""
    await websocket.accept()
    client = websocket.client
    logger.info(
        "WebSocket client connected: %s:%s",
        client.host if client else "unknown",
        client.port if client else "unknown",
    )
    try:
        while True:
            for update in service.advance_all(advance_minutes):
                await websocket.send_json(update)
            await asyncio.sleep(interval_seconds)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except asyncio.CancelledError:
        logger.info("WebSocket connection task cancelled")
        raise
    except Exception:
        logger.exception("Unexpected WebSocket update failure")
        if websocket.client_state.name != "DISCONNECTED":
            await websocket.close(code=1011, reason="Unexpected update failure")
