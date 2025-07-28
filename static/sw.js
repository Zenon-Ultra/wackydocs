// Service Worker for WackyDocs PWA
const CACHE_NAME = 'wackydocs-v1.0.0';
const STATIC_CACHE = 'wackydocs-static-v1.0.0';
const DYNAMIC_CACHE = 'wackydocs-dynamic-v1.0.0';

// Files to cache for offline functionality
const STATIC_FILES = [
  '/',
  '/static/css/style.css',
  '/static/js/main.js',
  '/static/manifest.json',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js'
];

// Routes that should work offline
const OFFLINE_PAGES = [
  '/',
  '/dashboard',
  '/english-dictionary',
  '/suneung/korean',
  '/pdf-resources'
];

// Install event - cache static assets
self.addEventListener('install', event => {
  console.log('Service Worker installing...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => {
        console.log('Caching static files...');
        return cache.addAll(STATIC_FILES);
      })
      .then(() => {
        console.log('Static files cached successfully');
        return self.skipWaiting();
      })
      .catch(error => {
        console.error('Failed to cache static files:', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('Service Worker activating...');
  
  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => {
            if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
              console.log('Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('Service Worker activated');
        return self.clients.claim();
      })
  );
});

// Fetch event - serve from cache with network fallback
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }
  
  // Skip external requests (except CDN resources)
  if (url.origin !== self.location.origin && !STATIC_FILES.includes(request.url)) {
    return;
  }
  
  event.respondWith(
    caches.match(request)
      .then(cachedResponse => {
        if (cachedResponse) {
          // Serve from cache
          return cachedResponse;
        }
        
        // Network request with caching
        return fetch(request)
          .then(networkResponse => {
            // Don't cache if not a valid response
            if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
              return networkResponse;
            }
            
            // Cache dynamic content
            const responseToCache = networkResponse.clone();
            caches.open(DYNAMIC_CACHE)
              .then(cache => {
                cache.put(request, responseToCache);
              });
            
            return networkResponse;
          })
          .catch(error => {
            console.log('Network request failed:', error);
            
            // Serve offline page for navigation requests
            if (request.destination === 'document') {
              return caches.match('/offline.html')
                .then(offlineResponse => {
                  return offlineResponse || new Response(
                    '<!DOCTYPE html><html><head><title>오프라인</title></head><body><h1>인터넷 연결을 확인해주세요</h1><p>현재 오프라인 상태입니다.</p></body></html>',
                    { headers: { 'Content-Type': 'text/html' } }
                  );
                });
            }
            
            // For other requests, just throw the error
            throw error;
          });
      })
  );
});

// Background sync for offline actions
self.addEventListener('sync', event => {
  if (event.tag === 'vocabulary-sync') {
    event.waitUntil(syncVocabulary());
  } else if (event.tag === 'quiz-score-sync') {
    event.waitUntil(syncQuizScores());
  }
});

// Push notifications
self.addEventListener('push', event => {
  if (!event.data) return;
  
  const data = event.data.json();
  const options = {
    body: data.body,
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/icon-96x96.png',
    vibrate: [200, 100, 200],
    tag: data.tag || 'wackydocs-notification',
    actions: [
      {
        action: 'open',
        title: '열기',
        icon: '/static/icons/icon-96x96.png'
      },
      {
        action: 'close',
        title: '닫기'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// Notification click handling
self.addEventListener('notificationclick', event => {
  event.notification.close();
  
  if (event.action === 'open' || !event.action) {
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

// Sync functions for offline data
async function syncVocabulary() {
  try {
    // Get offline vocabulary data from IndexedDB
    const offlineData = await getOfflineVocabulary();
    
    for (const item of offlineData) {
      try {
        await fetch('/add-vocabulary', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: new URLSearchParams(item)
        });
        
        // Remove from offline storage after successful sync
        await removeOfflineVocabulary(item.id);
      } catch (error) {
        console.error('Failed to sync vocabulary item:', error);
      }
    }
  } catch (error) {
    console.error('Vocabulary sync failed:', error);
  }
}

async function syncQuizScores() {
  try {
    // Get offline quiz scores from IndexedDB
    const offlineScores = await getOfflineQuizScores();
    
    for (const score of offlineScores) {
      try {
        await fetch('/submit-quiz-score', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(score)
        });
        
        // Remove from offline storage after successful sync
        await removeOfflineQuizScore(score.id);
      } catch (error) {
        console.error('Failed to sync quiz score:', error);
      }
    }
  } catch (error) {
    console.error('Quiz score sync failed:', error);
  }
}

// IndexedDB helpers (simplified)
async function getOfflineVocabulary() {
  // Implementation would use IndexedDB to store offline data
  return [];
}

async function removeOfflineVocabulary(id) {
  // Implementation would remove item from IndexedDB
}

async function getOfflineQuizScores() {
  // Implementation would use IndexedDB to store offline data
  return [];
}

async function removeOfflineQuizScore(id) {
  // Implementation would remove item from IndexedDB
}