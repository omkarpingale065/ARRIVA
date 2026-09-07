"""Generate clearly labelled synthetic railway observations for the ARRIVA prototype.

This is not a real railway feed. It exists so the Day 1 preprocessing pipeline can
be exercised before a licensed historical source is selected.
"""

from __future__ import annotations

import argparse
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path


ROUTES = [
    {
        "route_id": "PUNE_MUMBAI",
        "origin": "Pune",
        "destination": "Mumbai",
        "stations": ["Pune", "Lonavala", "Karjat", "Kalyan", "Mumbai"],
        "section_km": [0, 64, 105, 145, 192],
        "travel_minutes": [0, 35, 70, 105, 140],
    },
    {
        "route_id": "MUMBAI_NASHIK",
        "origin": "Mumbai",
        "destination": "Nashik",
        "stations": ["Mumbai", "Kalyan", "Kasara", "Nashik"],
        "section_km": [0, 52, 116, 185],
        "travel_minutes": [0, 42, 98, 155],
    },
    {
        "route_id": "PUNE_SOLAPUR",
        "origin": "Pune",
        "destination": "Solapur",
        "stations": ["Pune", "Daund", "Kurduvadi", "Solapur"],
        "section_km": [0, 75, 180, 265],
        "travel_minutes": [0, 55, 135, 205],
    },
]

TRAIN_NAMES = [
    "Deccan Express",
    "Konark Express",
    "Shivneri Express",
    "Mumbai Rajdhani",
    "Solapur Express",
    "Sahyadri Express",
]


def build_rows(seed: int = 20260906) -> list[dict[str, object]]:
    rng = random.Random(seed)
    rows: list[dict[str, object]] = []
    observation_id = 1
    start_date = datetime(2026, 1, 1)

    for day in range(60):
        service_date = start_date + timedelta(days=day)
        for train_index, train_name in enumerate(TRAIN_NAMES):
            route = ROUTES[train_index % len(ROUTES)]
            departure_hour = 5 + ((train_index * 2 + day) % 12)
            departure = service_date.replace(
                hour=departure_hour,
                minute=15 + ((train_index * 7) % 30),
                second=0,
                microsecond=0,
            )
            section_delay = max(0, round(rng.gauss(5 + (day % 5), 4), 1))
            final_delay = max(
                -2,
                round(section_delay + rng.gauss(2, 5) + (3 if train_index == 4 else 0), 1),
            )
            actual_destination_arrival = departure + timedelta(
                minutes=route["travel_minutes"][-1] + final_delay
            )

            for sequence, station in enumerate(route["stations"][:-1]):
                scheduled_arrival = departure + timedelta(
                    minutes=route["travel_minutes"][sequence]
                )
                scheduled_departure = scheduled_arrival + timedelta(
                    minutes=2 if sequence else 0
                )
                observation_offsets = [10, 25, 40]

                for offset in observation_offsets:
                    progress_minutes = route["travel_minutes"][sequence] + offset
                    observation_time = departure + timedelta(minutes=progress_minutes)
                    current_delay = round(
                        final_delay * (progress_minutes / route["travel_minutes"][-1])
                        + rng.gauss(0, 2),
                        1,
                    )
                    current_delay = max(-3, current_delay)
                    speed = max(18, round(rng.gauss(68 - current_delay * 0.8, 9), 1))
                    distance_remaining = max(
                        1,
                        route["section_km"][-1]
                        - (route["section_km"][sequence] + (offset / 60) * speed),
                    )
                    dwell = round(max(0, rng.gauss(2.5, 0.9)), 1) if offset == 10 else 0

                    rows.append(
                        {
                            "record_id": f"OBS-{observation_id:06d}",
                            "train_id": f"{12000 + train_index}",
                            "train_name": train_name,
                            "service_date": service_date.date().isoformat(),
                            "route_id": route["route_id"],
                            "origin_station": route["origin"],
                            "destination_station": route["destination"],
                            "section_id": f"{station.upper()}_{route['stations'][sequence + 1].upper()}",
                            "station_sequence": sequence,
                            "station_name": station,
                            "scheduled_departure": departure.isoformat(sep=" "),
                            "scheduled_arrival": scheduled_arrival.isoformat(sep=" "),
                            "scheduled_destination_arrival": (
                                departure + timedelta(minutes=route["travel_minutes"][-1])
                            ).isoformat(sep=" "),
                            "actual_observation_time": observation_time.isoformat(sep=" "),
                            "actual_destination_arrival": actual_destination_arrival.isoformat(sep=" "),
                            "latitude": round(18.4 + sequence * 0.28 + rng.uniform(-0.03, 0.03), 6),
                            "longitude": round(73.0 + sequence * 0.35 + rng.uniform(-0.03, 0.03), 6),
                            "current_speed_kmh": speed,
                            "distance_remaining_km": round(distance_remaining, 2),
                            "current_delay_minutes": current_delay,
                            "station_arrival_time": (scheduled_arrival + timedelta(minutes=current_delay)).isoformat(sep=" "),
                            "station_departure_time": (
                                scheduled_departure + timedelta(minutes=current_delay + dwell)
                            ).isoformat(sep=" "),
                            "weather_condition": rng.choice(["clear", "clear", "cloudy", "rain"]),
                            "track_condition": rng.choice(["normal", "normal", "wet"]),
                            "signal_aspect": rng.choice(
                                ["GREEN", "GREEN", "DOUBLE_YELLOW", "YELLOW", "RED"]
                            ),
                            "historical_section_delay_minutes": section_delay,
                        }
                    )
                    observation_id += 1

    # Add deliberately messy records so cleaning behavior is exercised and auditable.
    rows[10]["current_speed_kmh"] = ""
    rows[25]["distance_remaining_km"] = -8
    rows[40]["actual_observation_time"] = "not-a-timestamp"
    rows[55]["current_speed_kmh"] = 480
    rows[70]["current_delay_minutes"] = 999
    rows[85]["weather_condition"] = ""
    rows.append(rows[100].copy())  # exact duplicate
    rows.append(rows[100].copy())  # second duplicate
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default="data/raw/historical_train_observations.csv",
        help="Output CSV path relative to the repository root.",
    )
    args = parser.parse_args()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = build_rows()

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows):,} synthetic raw observations to {output_path}")


if __name__ == "__main__":
    main()
