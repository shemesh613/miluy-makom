# -*- coding: utf-8 -*-
"""
stamp_build.py — 13.10.2026

חותם ל-index.html חתימת גרסה שאי אפשר לשכוח לעדכן: sha256 של כל
הקובץ (12 תווים ראשונים), שנכנס ל-<meta name="app-build">. חייב
לרוץ **אחרון**, אחרי כל שאר ה-patch_*.py — אחרת החתימה לא תשקף את
השינויים האחרונים.

למה לא מחרוזת תאריך ידנית כמו BUILD ב-sw.js: עם מחרוזת ידנית קל
לשכוח לעדכן (זה בדיוק מה שקרה וגרם לשמשון לראות קוד ישן). hash לא
אפשר לשכוח — הוא נגזר מהתוכן עצמו.

הרצה: python tools/stamp_build.py [index.html]   ·   אידמפוטנטי
(אם מריצים פעמיים ברצף בלי שינוי נוסף, השני לא ישנה דבר כי הגיבוב
מחושב על התוכן **בלי** החתימה הנוכחית).
"""
import hashlib
import io
import re
import sys

PATH = sys.argv[1] if len(sys.argv) > 1 else 'index.html'

with io.open(PATH, encoding='utf-8') as f:
    src = f.read()

PATTERN = r'<meta name="app-build" content="[^"]*">'
if not re.search(PATTERN, src):
    raise SystemExit(u'✗ אין <meta name="app-build"> — להריץ קודם patch_realupdate.py')

# לחשב את הגיבוב על התוכן אחרי שהחתימה אופסה לקבוע, כדי שההרצה תהיה דטרמיניסטית
neutral = re.sub(PATTERN, '<meta name="app-build" content="PENDING">', src)
digest = hashlib.sha256(neutral.encode('utf-8')).hexdigest()[:12]

stamped = re.sub(PATTERN, '<meta name="app-build" content="%s">' % digest, src)

if stamped == src:
    print(u'↻ החתימה כבר עדכנית: %s' % digest)
else:
    with io.open(PATH, 'w', encoding='utf-8', newline='') as f:
        f.write(stamped)
    print(u'✓ נחתם: %s' % digest)
