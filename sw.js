/* Service Worker — כדי שחזרה לאתר תהיה מיידית.
   בנייד, יציאה לשיחה מפנה את הדף, ובחזרה הדפדפן מוריד מחדש את כל הדף
   (320KB) + ה-SDK של Firebase + הגופנים. כאן שומרים אותם, ומגישים מהמטמון
   מיד תוך כדי בדיקת עדכון ברקע (stale-while-revalidate).
   התוצאה: החזרה מרגישה מיידית, וגרסה חדשה נתפסת בטעינה הבאה.

   ⚠️ 11.10: החיסרון של stale-while-revalidate הוא שגרסה חדשה מגיעה רק
   בטעינה **הבאה** — כלומר אחרי דחיפה רואים עדיין את הישן, וזה נראה כאילו
   השינוי לא נדחף. לכן עכשיו: המטמון נושא את מספר הגרסה (`BUILD`), ובכל
   פעם שהדף שחזר מהרשת שונה מזה שבמטמון — נשלחת הודעה לדף והוא מציג
   פס "יש גרסה חדשה · רענן".
   📌 **לעדכן את BUILD בכל דחיפה שמשנה קוד.** */
const BUILD = '2026-10-12a';
const CACHE = 'miluy-' + BUILD;
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

// חותם הגרסה של תשובה — ETag של GitHub Pages, ואם אין אז זמן השינוי
const stamp = res => res && (res.headers.get('ETag') || res.headers.get('Last-Modified'));

function announceUpdate() {
  self.clients.matchAll({ type: 'window' }).then(cs =>
    cs.forEach(c => c.postMessage({ type: 'NEW_VERSION' })));
}

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  // נתוני אמת חייבים תמיד להגיע מהרשת — לא ממטמון
  if (/firebaseio|firebasedatabase|green-api|twilio/.test(url.hostname)) return;

  const cacheable = url.origin === location.origin ||
                    /gstatic\.com|googleapis\.com/.test(url.hostname);
  if (!cacheable) return;

  // רק על הדף עצמו שווה להתריע — לא על גופנים ו-SDK
  const isDoc = req.mode === 'navigate' ||
                (url.origin === location.origin && /(^\/|\/|index\.html)$/.test(url.pathname));

  e.respondWith(
    caches.open(CACHE).then(cache =>
      cache.match(req).then(hit => {
        const net = fetch(req).then(res => {
          if (res && res.status === 200) {
            const was = stamp(hit), now = stamp(res);
            cache.put(req, res.clone());
            // הדף במטמון ישן מזה שברשת — להודיע לדף שיציע רענון
            if (isDoc && hit && was && now && was !== now) announceUpdate();
          }
          return res;
        }).catch(() => hit);
        return hit || net;          // יש במטמון → מיידי, והעדכון נמשך ברקע
      })
    )
  );
});
