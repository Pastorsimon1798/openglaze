const CACHE_NAME = 'openglaze-v1';

const STATIC_ASSETS = [
    '/',
    '/index.html',
    '/styles/variables.css',
    '/styles/reset.css',
    '/styles/typography.css',
    '/styles/layout.css',
    '/styles/components.css',
    '/styles/gamification.css',
    '/styles/prediction.css',
    '/styles/tips.css',
    '/scripts/data.js',
    '/scripts/api.js',
    '/scripts/components/GlazeSwatch.js',
    '/scripts/components/GlazeAutocomplete.js',
    '/scripts/components/ComboCard.js',
    '/scripts/components/StageBar.js',
    '/scripts/components/KamaPanel.js',
    '/scripts/components/ComboDetailPanel.js',
    '/scripts/components/StudioPanel.js',
    '/scripts/components/LabQueueBoard.js',
    '/scripts/components/FiringLogForm.js',
    '/scripts/components/GamificationPanel.js',
    '/scripts/components/PredictionMarket.js',
    '/scripts/components/Leaderboard.js',
    '/scripts/components/ProgressTracker.js',
    '/scripts/components/GlazeTips.js',
    '/scripts/PhotoUploadForm.js',
    '/scripts/PhotoGallery.js',
    '/scripts/app.js',
    '/manifest.json'
];

// Install: cache static assets
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(STATIC_ASSETS))
            .then(() => self.skipWaiting())
    );
});

// Activate: clean old caches
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(
                keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
            )
        ).then(() => self.clients.claim())
    );
});

// Fetch: cache-first for static, network-first for API
self.addEventListener('fetch', event => {
    const url = new URL(event.request.url);

    // Network-first for API calls
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(
            fetch(event.request)
                .then(response => {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
                    return response;
                })
                .catch(() => caches.match(event.request))
        );
        return;
    }

    // Cache-first for static assets
    event.respondWith(
        caches.match(event.request)
            .then(cached => cached || fetch(event.request))
    );
});
