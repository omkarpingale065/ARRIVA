# ARRIVA mobile client

This is a separate, dependency-free installable PWA/static client. It is not
part of the Vite application: serve this directory with any static server and
point it at the existing FastAPI service.

```sh
cd mobile
python3 -m http.server 4174
# open http://127.0.0.1:4174/?api=http://127.0.0.1:8000
```

The app loads `/api/trains`, fetches `/api/trains/{id}/eta`, and subscribes to
`/ws/trains`. It supports train/route/station search, selection, ETA, delay,
risk/status, next station, and live location/status/ETA updates. The API URL
can also be stored in `localStorage` under `arriva-api`.

PWA is justified for field/station users: the shell is cacheable and
installable, opens fullscreen from a home screen, and retains the UI during
brief network loss while live data remains explicitly network-backed. A
service worker never caches REST or WebSocket responses, preventing stale
operational status.
