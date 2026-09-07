const CACHE = "arriva-mobile-v1";
self.addEventListener("install", event => event.waitUntil(caches.open(CACHE).then(c => c.addAll(["./","./index.html","./styles.css","./app.js","./manifest.webmanifest","./icon.svg"]))));
self.addEventListener("activate", event => event.waitUntil(self.clients.claim()));
self.addEventListener("fetch", event => { if (event.request.url.includes("/api/") || event.request.url.startsWith("ws")) return; event.respondWith(caches.match(event.request).then(r => r || fetch(event.request))); });
