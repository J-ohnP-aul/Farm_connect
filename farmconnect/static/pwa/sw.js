/* Service worker — SDD §6.
   Caches static assets only. Map/listing data is ALWAYS network-first and
   is never cached, so offline content can never present itself as
   confirmed live availability (FR-34, NFR-09). */
const CACHE = 'lfm-static-v2';
const ASSETS = [
  '/static/css/main.css',
  '/static/pwa/manifest.webmanifest',
  '/static/pwa/icon.svg',
];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(ASSETS)));
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  // Never cache pages, the map data endpoint, or tiles: they must always
  // be live or simply fail — never stale-but-claimed-fresh.
  const staticOnly =
    url.pathname.startsWith('/static/') && event.request.method === 'GET';
  if (!staticOnly) return;

  event.respondWith(
    caches.match(event.request).then(
      (cached) =>
        cached ||
        fetch(event.request).then((response) => {
          const copy = response.clone();
          caches.open(CACHE).then((cache) => cache.put(event.request, copy));
          return response;
        })
    )
  );
});
