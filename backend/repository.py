"""SQLite persistence for ETA predictions."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any


class PredictionRepository:
    """Small, dependency-free repository for prediction snapshots."""

    def __init__(self, database: str | Path = "data/arriva.sqlite3") -> None:
        self.database = str(database)
        if self.database != ":memory:":
            Path(self.database).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.database, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._lock = Lock()
        with self._connection:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    train_id TEXT NOT NULL,
                    station TEXT,
                    scheduled_eta TEXT,
                    predicted_eta TEXT,
                    actual_arrival TEXT,
                    delay_minutes REAL,
                    factors TEXT NOT NULL DEFAULT '[]',
                    timestamp TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )
            existing = {
                row["name"]
                for row in self._connection.execute("PRAGMA table_info(predictions)")
            }
            for name, definition in (
                ("station", "TEXT"),
                ("scheduled_eta", "TEXT"),
                ("predicted_eta", "TEXT"),
                ("actual_arrival", "TEXT"),
                ("delay_minutes", "REAL"),
                ("factors", "TEXT NOT NULL DEFAULT '[]'"),
            ):
                if name not in existing:
                    self._connection.execute(
                        f"ALTER TABLE predictions ADD COLUMN {name} {definition}"
                    )
            self._connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_predictions_train_time "
                "ON predictions (train_id, timestamp, id)"
            )

    def write_prediction(self, prediction: dict[str, Any]) -> None:
        timestamp = prediction["timestamp"]
        if isinstance(timestamp, datetime):
            timestamp = timestamp.isoformat()
        upcoming = prediction.get("upcoming_station_etas") or []
        payload = json.dumps(prediction, default=self._json_default)
        with self._lock, self._connection:
            self._connection.execute(
                """
                INSERT INTO predictions (
                    train_id, station, scheduled_eta, predicted_eta,
                    actual_arrival, delay_minutes, factors, timestamp, payload
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    prediction["train_id"],
                    upcoming[0].get("station") if upcoming else None,
                    self._as_iso(prediction.get("scheduled_destination_arrival")),
                    self._as_iso(prediction.get("predicted_arrival")),
                    self._as_iso(prediction.get("actual_arrival")),
                    prediction.get("predicted_delay_minutes"),
                    json.dumps(prediction.get("delay_factors", []), default=self._json_default),
                    str(timestamp),
                    payload,
                ),
            )

    # Short aliases keep the repository convenient for callers that do not
    # need to know the storage-specific method names.
    write = write_prediction

    def read_predictions(
        self, train_id: str, *, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        if limit < 1 or offset < 0:
            raise ValueError("limit must be positive and offset must not be negative")
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT payload FROM predictions
                WHERE train_id = ?
                ORDER BY timestamp ASC, id ASC
                LIMIT ? OFFSET ?
                """,
                (train_id, limit, offset),
            ).fetchall()
        return [json.loads(row["payload"]) for row in rows]

    read = read_predictions

    def count_predictions(self, train_id: str) -> int:
        with self._lock:
            row = self._connection.execute(
                "SELECT COUNT(*) AS count FROM predictions WHERE train_id = ?",
                (train_id,),
            ).fetchone()
        return int(row["count"])

    def clear(self, train_id: str | None = None) -> None:
        with self._lock, self._connection:
            if train_id is None:
                self._connection.execute("DELETE FROM predictions")
            else:
                self._connection.execute(
                    "DELETE FROM predictions WHERE train_id = ?", (train_id,)
                )

    @staticmethod
    def _as_iso(value: Any) -> str | None:
        if value is None:
            return None
        return value.isoformat() if isinstance(value, datetime) else str(value)

    @staticmethod
    def _json_default(value: Any) -> str:
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)
