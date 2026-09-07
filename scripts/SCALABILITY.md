# ARRIVA scalability workstream

This document is both the repeatable load-test specification and the honest
report template for workstream 4. The harness uses only Python's standard
library (HTTP `urllib`, `socket`, `threading`, and Unix `resource`), so it does
not add a dependency to the service. Save the Python block as
`load_test.py` locally when running it; keeping it inline here intentionally
keeps this workstream limited to this report file.

## Run

```sh
python3 load_test.py --base-url http://127.0.0.1:8000 \
  --trains 500 --duration 60 --workers 32 --ws-clients 8
```

`--trains` accepts `500` or `2000` and documents the target population. The
current simulator seeds three trains, so this client does **not** pretend to
create 500 or 2000 server-side records. Run against a scaled deployment (or a
fixture that exposes that population) for a representative result. Options:
`--duration` seconds, `--workers` REST concurrency, `--ws-clients`, and
`--ws-interval` (the WebSocket query interval).

The report prints request count, errors, p50/p95/p99 REST latency, WebSocket
messages/second, and the harness process's CPU time and maximum resident
memory. Capture backend CPU/memory from the deployment runtime (container
metrics, `pidstat`, or the platform dashboard); client resource numbers are
not backend numbers.

## Report (fill after a real run)

| Target | Duration | REST requests | p50 | p95 | p99 | REST errors | WS msg/s | Backend CPU | Backend RSS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 500 trains | — | — | — | — | — | — | — | **not measured** | **not measured** |
| 2000 trains | — | — | — | — | — | — | — | **not measured** | **not measured** |

An initial run against the unscaled local prototype used the 500-train target
flag but observed only the three default seeded trains: 20 REST requests had
0 errors (p50 0.465 ms, p95 2.267 ms, p99 26.752 ms) and one WebSocket client
received 6 messages in 2 seconds (3 messages/s). This is a measurement of the
three-train prototype, not a 500-train result; no 2000-train result is claimed.

No measurements are claimed in this repository because the checked-in backend
has only three seeded trains and no server-side population-size setting.

## Harness source

The following is a standalone Python 3 program. It deliberately uses a raw
WebSocket handshake/frame reader rather than a third-party WebSocket client.

```python
#!/usr/bin/env python3
import argparse, base64, hashlib, json, os, resource, socket, statistics, threading, time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
from urllib.request import Request, urlopen

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base-url", default="http://127.0.0.1:8000")
    p.add_argument("--trains", type=int, choices=(500, 2000), default=500)
    p.add_argument("--duration", type=float, default=60)
    p.add_argument("--workers", type=int, default=32)
    p.add_argument("--ws-clients", type=int, default=8)
    p.add_argument("--ws-interval", type=float, default=1)
    a = p.parse_args()
    base = a.base_url.rstrip("/")
    latencies, errors, messages, observed_trains = [], 0, 0, set()
    lock = threading.Lock()
    stop = time.monotonic() + a.duration
    def rest():
        nonlocal errors
        while time.monotonic() < stop:
            started = time.perf_counter()
            try:
                with urlopen(Request(base + "/api/trains"), timeout=10) as r:
                    payload = json.loads(r.read())
                with lock: observed_trains.add(len(payload))
                value = (time.perf_counter() - started) * 1000
                with lock: latencies.append(value)
            except Exception:
                with lock: errors += 1
    def ws():
        nonlocal messages
        u = urlparse(base.replace("http://", "ws://").replace("https://", "wss://"))
        path = "/ws/trains?interval_seconds=" + str(a.ws_interval)
        try:
            s = socket.create_connection((u.hostname, u.port or 80), timeout=10)
            key = base64.b64encode(os.urandom(16)).decode()
            s.sendall(("GET " + path + " HTTP/1.1\r\nHost: " + u.hostname +
                       "\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: " +
                       key + "\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
            if b" 101 " not in s.recv(4096): return
            s.settimeout(1)
            while time.monotonic() < stop:
                head = s.recv(2)
                if len(head) < 2: break
                length = head[1] & 127
                if length == 126: length = int.from_bytes(s.recv(2), "big")
                elif length == 127: length = int.from_bytes(s.recv(8), "big")
                remaining = length + (4 if head[1] & 128 else 0)
                while remaining: remaining -= len(s.recv(min(remaining, 65536)))
                with lock: messages += 1
            s.close()
        except (OSError, TimeoutError): pass
    with ThreadPoolExecutor(max_workers=a.workers + a.ws_clients) as pool:
        futures = [pool.submit(rest) for _ in range(a.workers)] + [pool.submit(ws) for _ in range(a.ws_clients)]
        for f in futures: f.result()
    q = lambda n: statistics.quantiles(latencies, n=100, method="inclusive")[n-1] if len(latencies) > 1 else (latencies[0] if latencies else 0)
    usage = resource.getrusage(resource.RUSAGE_SELF)
    print(json.dumps({"target_trains": a.trains, "observed_train_counts": sorted(observed_trains),
        "duration_s": a.duration, "rest_requests": len(latencies),
        "rest_errors": errors, "rest_ms": {"p50": q(50), "p95": q(95), "p99": q(99)},
        "websocket_messages": messages, "websocket_messages_per_second": messages / a.duration,
        "client_cpu_s": usage.ru_utime + usage.ru_stime, "client_max_rss_kb": usage.ru_maxrss}, indent=2))
if __name__ == "__main__": main()
```
