# -*- coding: utf-8 -*-
"""
patch_extrapresence.py — 1.11.2026

**"הרב אורי פרנסקי, למרות שלא מלמד ביום ראשון, שים אותו כמי שנמצא
ויש לו שעות פנויות — כי הוא אוהב למלא מקום."**

בשונה מ-ALWAYS_AVAILABLE (נועה/טובי, שאינן בקובץ המערכת בכלל ולכן
מוצעות בכל שעה בכל יום): הרב אורי פ. **כן** מלמד בפועל ראשון-חמישי
לפי מערכת אמיתית (ד/ה/ו/ז/ח), ואת זה אסור לגעת בו. הבקשה כאן צרה
יותר — יום ראשון בלבד, שבו הוא כרגע נעדר לגמרי מהמערכת (`days` לא
כולל 0) ולכן לא מוצע כלל.

`EXTRA_PRESENCE_DAYS` מוסיף לו את יום ראשון כ"עובד, בלי שיעורים" —
כל 9 השעות יוצאות פנויות, בלי לגעת בשאר ימות השבוע שלו. נאכף גם
על קובץ שיועלה (כמו SCHEDULE_FIXES/PERSONAL_BLOCKS), אחרת העלאת
מערכת חדשה הייתה מוחקת את זה.

הרצה: python tools/patch_extrapresence.py [index.html]   ·   אידמפוטנטי.
"""
import io
import sys

PATH = sys.argv[1] if len(sys.argv) > 1 else 'index.html'

with io.open(PATH, encoding='utf-8') as f:
    src = f.read()

if u'EXTRA_PRESENCE_DAYS' in src:
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


swap('EXTRA_PRESENCE_DAYS',
     u'''        function isMechanechMeeting(day, hour) {''',
     u'''        /* ===== מלמדים שרוצים להופיע כזמינים ביום שאינם מלמדים בו =====
           בשונה מ-ALWAYS_AVAILABLE: מי שברשימה הזו כן מלומד כרגיל בשאר
           השבוע לפי מערכת אמיתית — זה מוסיף רק את היום הנקוב כ"עובד,
           בלי שיעורים", כך שכל השעות בו יוצאות פנויות. שאר השבוע שלו
           לא נוגעים. נאכף גם על קובץ שיועלה. */
        const EXTRA_PRESENCE_DAYS = {
            'הרב אורי פ.': { days: [0], reason: 'אוהב למלא מקום — שמשון, 1.11.26' },
        };

        function enforceExtraPresenceDays() {
            Object.entries(EXTRA_PRESENCE_DAYS).forEach(([name, rule]) => {
                const t = teacherSchedule[name];
                if (!t) return;
                t.days = t.days || [];
                rule.days.forEach(d => {
                    if (!t.days.includes(d)) t.days = [...t.days, d].sort((a, b) => a - b);
                    t.dayHours = t.dayHours || {};
                    if (!t.dayHours[d]) t.dayHours[d] = [];      // אין שיעורים = כל השעות פנויות
                    t.dayClasses = t.dayClasses || {};
                    if (!t.dayClasses[d]) t.dayClasses[d] = [];
                });
            });
        }

        function isMechanechMeeting(day, hour) {''')

swap('builtin call',
     u'''        enforcePersonalBlocks();
        enforceScheduleFixes();
        EXTRA_STAFF.forEach''',
     u'''        enforcePersonalBlocks();
        enforceScheduleFixes();
        enforceExtraPresenceDays();
        EXTRA_STAFF.forEach''')

swap('override call',
     u'''            enforceScheduleFixes();
            activeScheduleInfo = o ? { fileName: o.fileName || '', updatedAt: o.updatedAt || 0 } : null;''',
     u'''            enforceScheduleFixes();
            enforceExtraPresenceDays();
            activeScheduleInfo = o ? { fileName: o.fileName || '', updatedAt: o.updatedAt || 0 } : null;''')

with io.open(PATH, 'w', encoding='utf-8', newline='') as f:
    f.write(src)

print(u'✓ נוכחות נוספת ביום ראשון להרב אורי פ. הוטמעה  (%d → %d תווים)' % (before, len(src)))
