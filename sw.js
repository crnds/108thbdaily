// Service worker for 108THBDAILY — offline support + instant revisits.
//
// GitHub Pages serves everything with Cache-Control: max-age=600, so after
// 10 minutes every revisit re-downloads the chart library and data files.
// Strategy here:
//   - navigations (index.html)  → network-first, cache fallback (stays fresh,
//     works offline)
//   - same-origin static assets → stale-while-revalidate (instant from cache,
//     refreshed in the background for the next visit)
//   - cross-origin requests (Kraken/Binance/Yahoo/FX APIs) → untouched
//
// Bump CACHE_NAME when the caching strategy changes; old caches are removed
// on activate.

const CACHE_NAME = '108thbdaily-v1';

self.addEventListener('install', () => {
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const { request } = event;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;   // never intercept API calls

  if (request.mode === 'navigate') {
    // Network-first: a deploy shows up on the very next load; offline falls
    // back to the cached page.
    event.respondWith(
      fetch(request)
        .then(res => {
          const copy = res.clone();
          caches.open(CACHE_NAME).then(c => c.put(request, copy));
          return res;
        })
        .catch(() => caches.match(request).then(m => m || caches.match('./index.html')))
    );
    return;
  }

  // Stale-while-revalidate for vendor libs and data files.
  event.respondWith(
    caches.match(request).then(cached => {
      const refresh = fetch(request)
        .then(res => {
          if (res.ok) {
            const copy = res.clone();
            caches.open(CACHE_NAME).then(c => c.put(request, copy));
          }
          return res;
        })
        .catch(() => cached);
      return cached || refresh;
    })
  );
});
