const CACHE_NAME = 'odoo-pwa-cache-v1';

var urlsToCache = [
    '/',
    '/pwa/offline',
    '/emipro_theme_base/static/src/img/offline_app.png',
    '/emipro_theme_base/static/src/img/pwa_offline.jpg',
];

// Service worker installation event, prefetch some data
// during installation of service worker
self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open(CACHE_NAME)
        .then(function(cache) {
            return cache.addAll(urlsToCache);
        })
    );
});
self.addEventListener('activate', function(evt) {
    evt.waitUntil(
        caches.keys().then(function(keyList) {
            return Promise.all(keyList.map(function(key) {
                if (key !== CACHE_NAME) {
                    return caches.delete(key);
                }
            }));
        })
    );
    self.clients.claim();
});
// override request fetch event so that we can manipulate it and respond data from cache
self.addEventListener('fetch', function(event) {

    // check if request is made by chrome extensions or web page
    // if request is made for web page url must contains http.
    if (!(event.request.url.indexOf('http') === 0)) return;
    // skip the request. if request is not made with http protocol

    self.addEventListener('fetch', event => {
        event.respondWith(handleRequest(event));
    });

    async function handleRequest(event) {
        const request = event.request;

        try {
            // Try the network first
            const networkResponse = await fetch(request);

            // If invalid network response, return it as-is
            if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
                return networkResponse;
            }

            // If GET request → cache it (but don't block returning response)
            if (request.method === 'GET') {
                const cache = await caches.open(CACHE_NAME);
                cache.put(request, networkResponse.clone()); // async but not awaited
            }

            return networkResponse; // network success
        } catch (error) {
            // NETWORK FAILED → return cached version or offline fallback

            const cache = await caches.open(CACHE_NAME);

            const cachedResponse = await cache.match(request);
            if (cachedResponse) {
                return cachedResponse; // valid cached resource
            }

            // final fallback
            const offlineFallback = await cache.match('/pwa/offline');
            return offlineFallback || Response.error();
        }
    }
});
