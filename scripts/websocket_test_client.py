"""Receive consecutive ARRIVA WebSocket updates for one train."""

from __future__ import annotations

import argparse
import asyncio
import json
from typing import Any

import websockets


async def receive_updates(url: str, train_id: str, count: int) -> list[dict[str, Any]]:
    updates = []
    async with websockets.connect(url) as socket:
        while len(updates) < count:
            update = json.loads(await socket.recv())
            if update["train_id"] == train_id:
                updates.append(update)
    return updates


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="ws://127.0.0.1:8000/ws/trains?interval_seconds=1&advance_minutes=5")
    parser.add_argument("--train-id", default="ARRIVA-12123")
    parser.add_argument("--count", type=int, default=3)
    args = parser.parse_args()
    updates = asyncio.run(receive_updates(args.url, args.train_id, args.count))
    print(json.dumps(updates, indent=2))
    if len(updates) >= 2:
        assert updates[-1]["timestamp"] != updates[0]["timestamp"]
        assert updates[-1]["distance_remaining"] < updates[0]["distance_remaining"]
        print(f"verified {len(updates)} changing updates for {args.train_id}")


if __name__ == "__main__":
    main()
