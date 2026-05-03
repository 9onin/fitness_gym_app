const CACHE_VERSION = 'fitness-gym-mobile-v1';
const APP_SHELL = [
    '/static/css/main.css',
    '/static/js/main.js',
    '/static/favicon.svg',
    '/static/icon-192.png',
    '/static/icon-512.png',
    '/static/images/homepage-gym-bg.png',
    '/static/offline.html'
];

self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open(CACHE_VERSION).then(function(cache) {
            return cache.addAll(APP_SHELL);
        })
    );
    self.skipWaiting();
});

self.addEventListener('activate', function(event) {
    event.waitUntil(
        caches.keys().then(function(keys) {
            return Promise.all(keys.map(function(key) {
                if (key !== CACHE_VERSION) {
                    return caches.delete(key);
                }
                return undefined;
            }));
        })
    );
    self.clients.claim();
});

self.addEventListener('fetch', function(event) {
    const request = event.request;

    if (request.method !== 'GET') {
        return;
    }

    if (request.mode === 'navigate') {
        event.respondWith(
            fetch(request).catch(function() {
                return caches.match('/static/offline.html');
            })
        );
        return;
    }

    event.respondWith(
        caches.match(request).then(function(cachedResponse) {
            return cachedResponse || fetch(request).then(function(networkResponse) {
                const sameOrigin = new URL(request.url).origin === self.location.origin;
                if (sameOrigin && networkResponse.ok) {
                    const responseClone = networkResponse.clone();
                    caches.open(CACHE_VERSION).then(function(cache) {
                        cache.put(request, responseClone);
                    });
                }
                return networkResponse;
            });
        })
    );
});
