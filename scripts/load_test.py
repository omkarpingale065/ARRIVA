"""Measure REST/WebSocket behavior of a running ARRIVA backend.

The current service seeds three trains. ``--trains`` records the intended target
for a scaled fixture; it does not pretend to create server-side train records.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import time
import urllib.request


def request_ms(url: str) -> float:
    started = time.perf_counter()
    with urllib.request.urlopen(url, timeout=10) as response:
        json.load(response)
    return (time.perf_counter() - started) * 1000


async def websocket_messages(url: str, seconds: float) -> int:
    try:
        import websockets
    except ImportError:
        return 0
    count = 0
    try:
        async with websockets.connect(url, open_timeout=10) as socket:
            deadline = time.monotonic() + seconds
            while time.monotonic() < deadline:
                await asyncio.wait_for(socket.recv(), timeout=max(0.1, deadline - time.monotonic()))
                count += 1
    except (OSError, asyncio.TimeoutError, websockets.WebSocketException):
        return count
    return count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--trains", type=int, choices=(500, 2000), default=500)
    parser.add_argument("--requests", type=int, default=100)
    parser.add_argument("--duration", type=float, default=10)
    args = parser.parse_args()
    latencies = []
    errors = 0
    for _ in range(args.requests):
        try:
            latencies.append(request_ms(f"{args.base_url.rstrip('/')}/api/trains"))
        except Exception:
            errors += 1
    ws_url = args.base_url.replace("https://", "wss://").replace("http://", "ws://")
    messages = asyncio.run(websocket_messages(
        f"{ws_url.rstrip('/')}/ws/trains?interval_seconds=1", args.duration
    ))
    quantile = lambda percentile: statistics.quantiles(latencies, n=100, method="inclusive")[percentile - 1] if len(latencies) > 1 else (latencies[0] if latencies else 0)
    print(json.dumps({
        "target_trains": args.trains,
        "observed_train_count": "reported by /api/trains; current prototype seeds 3",
        "rest_requests": len(latencies),
        "rest_errors": errors,
        "rest_ms": {"p50": quantile(50), "p95": quantile(95), "p99": quantile(99)},
        "websocket_messages": messages,
        "websocket_messages_per_second": messages / args.duration,
        "backend_cpu_and_rss": "measure with pidstat/container metrics; not inferred by this client",
    }, indent=2))


if __name__ == "__main__":
    main()
