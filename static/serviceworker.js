const CACHE_NAME = 'p2p-connect-v2'; // Changed version to force update
const urlsToCache = [
    '/static/manifest.json',
    '/static/images/logo_192.png',
    '/static/images/logo_512.png',
    'https://cdn.tailwindcss.com',
    'https://unpkg.com/htmx.org@1.9.6',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'
];

self.addEventListener('install', event => {
    self.skipWaiting(); // Force new worker to take over immediately
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache))
    );
});

self.addEventListener('fetch', event => {
    const requestUrl = new URL(event.request.url);

    // 1. IGNORE Non-GET requests (POST, etc. for Login/Chat)
    if (event.request.method !== 'GET') return;

    // 2. IGNORE Dynamic Pages (Dashboard, Chat Rooms, HTMX calls)
    // We only want to cache static assets
    if (requestUrl.pathname === '/' || 
        requestUrl.pathname.startsWith('/chat/') || 
        requestUrl.pathname.startsWith('/ws/') ||
        requestUrl.pathname.startsWith('/auth/')) {
        return; // Go straight to network
    }

    // 3. For everything else (Images, CSS), look in Cache first
    event.respondWith(
        caches.match(event.request).then(response => {
            return response || fetch(event.request);
        })
    );
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});