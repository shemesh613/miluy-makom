/* Service Worker — כדי שחזרה לאתר תהיה מיידית.
   בנייד, יציאה לשיחה מפנה את הדף, ובחזרה הדפדפן מוריד מחדש את כל הדף
   (320KB) + ה-SDK של Firebase + הגופנים. כאן שומרים אותם, ומגישים מהמטמון
   מיד תוך כדי בדיקת עדכון ברקע (stale-while-revalidate).
   התוצאה: החזרה מרגישה מיידית, וגרסה חדשה נתפסת בטעינה הבאה. */
const CACHE = 'miluy-v1';
const SHELL = [
  './',
  './index.html',
  'https://www.gstatic.com/firebasejs/9.22.0/firebase-app-compat.js',
  'https://www.gstatic.com/firebasejs/9.22.0/firebase-database-compat.js',
];

self.addEventListener('install', e => {
  self.skipWaiting();
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL).catch(() => {})));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  // נתוני אמת חייבים תמיד להגיע מהרשת — לא ממטמון
  if (/firebaseio|firebasedatabase|green-api|twilio/.test(url.hostname)) return;

  const cacheable = url.origin === location.origin ||
                    /gstatic\.com|googleapis\.com/.test(url.hostname);
  if (!cacheable) return;

  e.respondWith(
    caches.open(CACHE).then(cache =>
      cache.match(req).then(hit => {
        const net = fetch(req).then(res => {
          if (res && res.status === 200) cache.put(req, res.clone());
          return res;
        }).catch(() => hit);
        return hit || net;          // יש במטמון → מיידי, והעדכון נמשך ברקע
      })
    )
  );
});
