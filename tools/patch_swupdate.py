# -*- coding: utf-8 -*-
"""
patch_swupdate.py — 11.10.2026

"אני עדיין רואה את הישן — הכל נדחף?"

כן נדחף. ה-Service Worker עבד ב-stale-while-revalidate: הוא מגיש את
הגרסה שבמטמון **מיד** ובודק עדכון ברקע, ולכן הגרסה החדשה נראית רק
בטעינה הבאה. זה נהדר למהירות וגרוע לאמון — נראה כאילו שום דבר לא קרה.

התיקון (יחד עם sw.js המעודכן):
  · ה-SW מזהה שהדף ברשת שונה מזה שבמטמון ושולח הודעה לדף
  · הדף מציג פס תחתון "יש גרסה חדשה · רענן" עם כפתור
  · בכל חזרה לאתר נבדק עדכון (`reg.update()`)

הרצה: python tools/patch_swupdate.py [index.html]
אידמפוטנטי.
"""
import io
import sys

PATH = sys.argv[1] if len(sys.argv) > 1 else 'index.html'

with io.open(PATH, encoding='utf-8') as f:
    src = f.read()

SENTINEL = u"getElementById('update-bar')"
if SENTINEL in src:
    print(u'↻ כבר קיים — לא שונה דבר')
    raise SystemExit(0)

OLD = u'''        if ('serviceWorker' in navigator && location.protocol === 'https:') {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('sw.js').catch(e =>
                    console.warn('SW registration failed', e));
            });
        }'''

NEW = u'''        /* פס "יש גרסה חדשה". לא מרעננים לבד — אפשר שמישהו באמצע הזנה. */
        function showUpdateBar() {
            if (document.getElementById('update-bar')) return;
            const bar = document.createElement('div');
            bar.id = 'update-bar';
            bar.setAttribute('role', 'status');
            bar.style.cssText = 'position:fixed;inset-inline:0;bottom:0;z-index:9999;'
                + 'background:#1f6f4a;color:#fff;padding:11px 16px;display:flex;'
                + 'align-items:center;justify-content:center;gap:12px;font-size:0.95rem;'
                + 'box-shadow:0 -2px 12px rgba(0,0,0,.25)';
            bar.innerHTML = '<span>🔄 יש גרסה חדשה של האתר</span>'
                + '<button id="update-bar-btn" style="background:#fff;color:#1f6f4a;'
                + 'border:none;border-radius:8px;padding:6px 16px;font-weight:700;'
                + 'font-size:0.95rem;cursor:pointer;">רענן</button>'
                + '<button id="update-bar-x" aria-label="סגור" style="background:none;'
                + 'border:none;color:#fff;font-size:1.1rem;cursor:pointer;">✕</button>';
            document.body.appendChild(bar);
            bar.querySelector('#update-bar-btn').onclick = () => location.reload();
            bar.querySelector('#update-bar-x').onclick = () => bar.remove();
        }

        if ('serviceWorker' in navigator && location.protocol === 'https:') {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('sw.js').then(reg => {
                    // כל חזרה לאתר בודקת אם יש גרסה חדשה
                    document.addEventListener('visibilitychange', () => {
                        if (document.visibilityState === 'visible')
                            reg.update().catch(() => {});
                    });
                }).catch(e => console.warn('SW registration failed', e));

                navigator.serviceWorker.addEventListener('message', e => {
                    if (e.data && e.data.type === 'NEW_VERSION') showUpdateBar();
                });
            });
        }'''

if OLD not in src:
    raise SystemExit(u'✗ רישום ה-SW לא נמצא במצב המצופה')
if src.count(OLD) != 1:
    raise SystemExit(u'✗ %d התאמות, צפויה אחת' % src.count(OLD))

before = len(src)
src = src.replace(OLD, NEW)

with io.open(PATH, 'w', encoding='utf-8', newline='') as f:
    f.write(src)

print(u'✓ פס העדכון הוטמע  (%d → %d תווים)' % (before, len(src)))
