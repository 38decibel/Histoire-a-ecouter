// Service worker : l'histoire fonctionne hors connexion une fois chargée.
const CACHE = 'lumina-v9';
self.addEventListener('install', e => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(
  caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())));
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.origin !== location.origin) return;
  const isAudio = url.pathname.includes('/audio/');
  if (isAudio) {
    // sons : cache d'abord
    e.respondWith(caches.open(CACHE).then(async c => {
      const hit = await c.match(e.request);
      if (hit) return hit;
      const r = await fetch(e.request);
      if (r.ok) c.put(e.request, r.clone());
      return r;
    }));
  } else {
    // pages et scénario : réseau d'abord (pour les mises à jour), cache si hors ligne
    e.respondWith(fetch(e.request).then(r => {
      if (r.ok) caches.open(CACHE).then(c => c.put(e.request, r.clone()));
      return r;
    }).catch(() => caches.match(e.request)));
  }
});
