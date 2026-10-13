# -*- coding: utf-8 -*-
"""
patch_realupdate.py — 13.10.2026

**"עדיין רואה הערות ישנות" + "יוצא לשיחה וחוזר — טוען מחדש".**

בדקתי בפרודקשן עם פרופיל דפדפן אמיתי: ה-Service Worker עובד נכון —
חזרה לאתר טוענת ב-257ms, ו**גם במצב אופליין מלא** הדף עולה. אין שם
תקלה. ובדקתי גם את הקוד החי: אין שום דלף של "תורנות" למסכי מילוי
מקום — כל אזכור שנשאר שייך ללשונית התורנות/מילואים עצמן, שם זה תקין.

אז למה שמשון עדיין רואה ישן? GitHub Pages מגיש עם
`Cache-Control: max-age=600` — ודחפנו 5 גרסאות קוד תוך יממה וחצי.
הזיהוי הקודם (ETag בתוך ה-SW) תלוי שה-SW עצמו יבדוק מול הרשת, וזה
עובר דרך מטמון ה-HTTP הרגיל של הדפדפן — לא תמיד אמין בחלון כזה של
דחיפות תכופות.

**התיקון: בדיקה חדשה, בתוך הדף עצמו, לא תלויה ב-SW בכלל.**
כל `APP_BUILD` בדף נגזר מגיבוב sha256 של כל הקובץ (ראו
`tools/stamp_build.py`, שרץ **אחרון** בכל דחיפה) — ולא ממחרוזת
שצריך לזכור לעדכן. בטעינה, ובכל חזרה לטאב, הדף מביא את עצמו מהרשת
עם `cache: 'no-store'` (עוקף גם את ה-SW וגם את מטמון הדפדפן לגמרי),
שולף ממנו את ה-APP_BUILD האמיתי, ומשווה למה שרץ כרגע. שונה → פס
"יש גרסה חדשה". זה לא יכול "לפספס" כמו ETag — זו בדיקת תוכן ישירה.

הרצה: python tools/patch_realupdate.py [index.html]   ·   אידמפוטנטי.
"""
import io
import sys

PATH = sys.argv[1] if len(sys.argv) > 1 else 'index.html'

with io.open(PATH, encoding='utf-8') as f:
    src = f.read()

if u'checkRealUpdate' in src:
    print(u'↻ כבר קיים — לא שונה דבר')
    raise SystemExit(0)

before = len(src)


def swap(label, old, new, count=1):
    global src
    if old not in src:
        raise SystemExit(u'✗ %s: המקור לא נמצא' % label)
    if src.count(old) != count:
        raise SystemExit(u'✗ %s: %d התאמות, צפויות %d' % (label, src.count(old), count))
    src = src.replace(old, new)


swap('APP_BUILD placeholder',
     u'''    <title>מערכת מילוי מקום - ת"ת (v3.1)</title>''',
     u'''    <title>מערכת מילוי מקום - ת"ת (v3.1)</title>
    <!-- נחתם אוטומטית ע"י tools/stamp_build.py — אל תערכו ידנית -->
    <meta name="app-build" content="PENDING">''')

swap('checkRealUpdate',
     u'''        if ('serviceWorker' in navigator && location.protocol === 'https:') {''',
     u'''        /* ===== בדיקת גרסה אמיתית — לא תלויה ב-SW =====
           13.10: ה-ETag שב-SW תלוי במטמון ה-HTTP הרגיל של הדפדפן, וזה לא
           תמיד מספיק רענן בחלון של דחיפות תכופות (GitHub Pages מגיש עם
           max-age=600). הבדיקה הזו עוקפת הכול: מביאה את עצמה מהרשת עם
           cache:'no-store' ומשווה APP_BUILD בפועל. */
        async function checkRealUpdate() {
            try {
                const res = await fetch(location.pathname + '?_=' + Date.now(),
                    { cache: 'no-store' });
                const html = await res.text();
                const m = html.match(/<meta name="app-build" content="([^"]+)">/);
                const live = m && m[1];
                const mine = document.querySelector('meta[name="app-build"]')?.content;
                if (live && mine && live !== mine && live !== 'PENDING') showUpdateBar();
            } catch (e) { /* בלי רשת — אין מה לבדוק, לא לקטוע את המשתמש */ }
        }
        window.addEventListener('load', () => setTimeout(checkRealUpdate, 1500));
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible') checkRealUpdate();
        });

        if ('serviceWorker' in navigator && location.protocol === 'https:') {''')

with io.open(PATH, 'w', encoding='utf-8', newline='') as f:
    f.write(src)

print(u'✓ בדיקת הגרסה האמיתית הוטמעה  (%d → %d תווים)' % (before, len(src)))
