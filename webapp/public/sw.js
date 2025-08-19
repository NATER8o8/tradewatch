
self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const cache = await caches.open('otp-v3');
    await cache.addAll(['/', '/manifest.json']);
  })());
});
self.addEventListener('fetch', event => {
  event.respondWith(caches.match(event.request).then(resp => resp || fetch(event.request)));
});
self.addEventListener('push', event => {
  let data = {};
  try { data = event.data.json(); } catch(e) { data = { body: 'New alert' }; }
  const title = data.title || 'Official Trades Pro';
  const body = data.body || 'You have a new alert';
  event.waitUntil(self.registration.showNotification(title, { body }));
});
self.addEventListener('notificationclick', event => {
  event.notification.close();
  event.waitUntil(clients.openWindow('/'));
});
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'notify' && event.data.text) {
    self.registration.showNotification('Official Trades Pro', { body: event.data.text });
  }
});
