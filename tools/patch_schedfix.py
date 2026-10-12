# -*- coding: utf-8 -*-
"""
patch_schedfix.py — 12.10.2026

**שני ש7 — הרב אליהו שמשון מלמד טבע בכיתה ח.**

בקובץ המערכת התא הזה מכיל רק את שם המקצוע בלי הכיתה, ולכן הפרסר הוציא
"תפוס, אין כיתה". המשמעות המעשית הייתה חמורה: כשהוא נעדר בשעה הזו,
המערכת חשבה ש**אין מה לכסות** — כיתה ח הייתה נשארת בלי מלמד ובלי שאף
אחד ידע. זו הייתה השעה היחידה בכל השבוע שלו בלי כיתה, מה שמאשר שזו
תקלת נתונים ולא שעה אמיתית ללא כיתה.

`SCHEDULE_FIXES` מתקן תאים כאלה, ונאכף **גם על קובץ שיועלה בהמשך** —
אחרת כל העלאה הייתה מחזירה את הבאג.

🔴 ובדרך — באג שהתגלה: `enforcePersonalBlocks()` נקרא רק על המערכת
המובנית ולא אחרי החלת קובץ שהועלה, למרות שבהערה בקוד כתוב במפורש
שהוא נאכף "כדי שגם מערכת שתועלה בהמשך לא תחזיר אותו לרשימת הפנויים".
כלומר העלאת קובץ הייתה מוחקת את כל החסימות האישיות — ינון, פורת
ושלומי היו חוזרים להיות מוצעים בשעות שהם לא בבניין. תוקן.

הרצה: python tools/patch_schedfix.py [index.html]   ·   אידמפוטנטי.
"""
import io
import sys

PATH = sys.argv[1] if len(sys.argv) > 1 else 'index.html'

with io.open(PATH, encoding='utf-8') as f:
    src = f.read()

if u'SCHEDULE_FIXES' in src:
    print(u'↻ כבר קיים — לא שונה דבר')
    raise SystemExit(0)

before = len(src)
applied = []


def swap(label, old, new, count=1):
    global src
    if old not in src:
        raise SystemExit(u'✗ %s: המקור לא נמצא' % label)
    if src.count(old) != count:
        raise SystemExit(u'✗ %s: %d התאמות, צפויות %d' % (label, src.count(old), count))
    src = src.replace(old, new)
    applied.append(label)


# ------------------------------------------------ 1. טבלת התיקונים
swap('SCHEDULE_FIXES',
     u'''        function isMechanechMeeting(day, hour) {''',
     u'''        /* ===== תאים שקובץ המערכת מוסר בהם מידע =====
           תא שמכיל רק את שם המקצוע בלי הכיתה יוצא מהפרסר כ"תפוס, אין
           כיתה" — ואז כשהמלמד נעדר, המערכת חושבת **שאין מה לכסות**
           והכיתה נשארת בלי מלמד בלי שאף אחד ידע. זה לא "שעה בלי כיתה",
           זו אבדן נתון.

           ⚠️ נאכף גם על קובץ שיועלה בהמשך — אחרת כל העלאה מחזירה את הבאג.
           כשהקובץ יתוקן במקור אפשר להסיר מכאן. */
        const SCHEDULE_FIXES = [
            { teacher: 'הרב אליהו שמשון', day: 1, hour: '7', cls: 'ח',
              note: 'טבע בח — בקובץ התא מכיל רק את שם המקצוע (שמשון, 11.10.26)' },
        ];

        function enforceScheduleFixes() {
            const order = ['בוקר', '4', '5', '6', '7', '8', '9', '10', 'סדר ערב'];
            SCHEDULE_FIXES.forEach(f => {
                const t = teacherSchedule[f.teacher];
                if (!t) return;
                t.days = t.days || [];
                if (!t.days.includes(f.day)) t.days = [...t.days, f.day].sort((a, b) => a - b);
                t.dayHours = t.dayHours || {};
                const hours = t.dayHours[f.day] || (t.dayHours[f.day] = []);
                if (!hours.includes(f.hour)) {
                    hours.push(f.hour);
                    hours.sort((a, b) => order.indexOf(a) - order.indexOf(b));
                }
                t.dayClasses = t.dayClasses || {};
                const dc = t.dayClasses[f.day] || (t.dayClasses[f.day] = []);
                const base = f.cls.charAt(0);
                if (!dc.includes(base)) dc.push(base);
                const map = dayHourClassesData[f.teacher] || (dayHourClassesData[f.teacher] = {});
                const dm = map[f.day] || (map[f.day] = {});
                dm[f.hour] = f.cls;
            });
        }

        function isMechanechMeeting(day, hour) {''')

# ------------------------------------- 2. הפעלה על המערכת המובנית
swap('builtin call',
     u'''        enforceMechanechMeeting();   // גם על המערכת המובנית, לא רק על קובץ שהועלה
        enforcePersonalBlocks();''',
     u'''        enforceMechanechMeeting();   // גם על המערכת המובנית, לא רק על קובץ שהועלה
        enforcePersonalBlocks();
        enforceScheduleFixes();''')

# ------------------- 3. הפעלה אחרי החלת קובץ שהועלה (+ באג החסימות)
swap('override call',
     u'''            enforceMechanechMeeting();
            activeScheduleInfo = o ? { fileName: o.fileName || '', updatedAt: o.updatedAt || 0 } : null;''',
     u'''            enforceMechanechMeeting();
            // 🔴 enforcePersonalBlocks לא נקרא כאן עד 12.10 — כלומר כל העלאת
            // קובץ מחקה את החסימות האישיות (ינון, פורת, שלומי) והחזירה אותם
            // לרשימת הפנויים בשעות שהם אינם בבניין.
            enforcePersonalBlocks();
            enforceScheduleFixes();
            activeScheduleInfo = o ? { fileName: o.fileName || '', updatedAt: o.updatedAt || 0 } : null;''')

with io.open(PATH, 'w', encoding='utf-8', newline='') as f:
    f.write(src)

print(u'✓ הוחלו: %d' % len(applied))
for a in applied:
    print(u'   · %s' % a)
print(u'  %d → %d תווים' % (before, len(src)))
