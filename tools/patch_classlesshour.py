# -*- coding: utf-8 -*-
"""
patch_classlesshour.py — 1.11.2026

**"הרב חגי היום שעה שישית — נוצרה טעות כי חישבה שעת הדרכה שלו כצריך מ"מ."**

אומת ב-Firebase: רשומת היעדרות שנשמרה הבוקר לחגי כוללת שעה 6 עם
`classAtHour: ""` — ובכל זאת שובץ לה ממלא מקום. חגי מלמד בשעה הזו
(`dayHours[0]` כוללת `'6'`), אבל אין לו כיתה בה (`dayHourClassesData`
לא ממפה שעה 6) — זו שעת הדרכה, בדיוק כמו "גנים"/"קב\"ש" שכבר מתועדות
כ"תפוס, אין כיתה: אם הוא נעדר אין מה לכסות".

**מקור הטעות:** כפתור "📅 כל היום" בטופס הדיווח בחר את **כל** השעות
ב-`dayHours[currentDay]` של המורה, בלי לסנן החוצה שעות שאין בהן כיתה.
כך נבחרה גם שעה 6 יחד עם שעות ההוראה האמיתיות, ונשמרה כהיעדרות
"צריכה מ\"מ" לצד השאר.

**התיקון:** גם "כל היום" וגם שמירת הדיווח מסננים שעות בלי כיתה —
אלה לא נשמרות כלל כהיעדרות הדורשת כיסוי (בדיוק כמו "הדרכה"/"גנים"
בכל שאר המערכת). אם סוננו שעות, ההודעה לפני השמירה אומרת זאת
במפורש, כדי ששמשון לא יחשוב ששעה "נעלמה" בלי הסבר.

הרצה: python tools/patch_classlesshour.py [index.html]   ·   אידמפוטנטי.
"""
import io
import sys

PATH = sys.argv[1] if len(sys.argv) > 1 else 'index.html'

with io.open(PATH, encoding='utf-8') as f:
    src = f.read()

if u'classlessHours' in src:
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


# --------------------------------------------- 0. תקלה סמויה שנחשפה
# בבדיקה: #all-day-btn נושא גם class="hour-btn", ולכן המאזין הכללי
# (למטה) מתלבש עליו גם הוא — toggle על עצמו + updateSuggestionFields()
# עם hour=undefined שמתרסק. בפועל זה "נבלע" כי המאזין הייעודי של
# all-day-btn רץ מיד אחריו ומתקן את התצוגה — אבל זו שגיאת קונסול
# מיותרת על כל לחיצה, ותלות שברירית. לא קשור לבקשה של שמשון, אבל
# עלה תוך כדי הבדיקה ותיקונו חד-שורה ובטוח.
swap('all-day-btn not a real hour',
     u'''        // Hours selector
        document.querySelectorAll('.hour-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                this.classList.toggle('selected');
                updateSuggestionFields();
            });
        });''',
     u'''        // Hours selector
        document.querySelectorAll('.hour-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                if (!this.dataset.hour) return;   // #all-day-btn — יש לו מאזין משלו
                this.classList.toggle('selected');
                updateSuggestionFields();
            });
        });''')

# ------------------------------------------- 1. כפתור "כל היום"
swap('all-day filter',
     u'''            // Get today's hours for this teacher
            const todayHours = schedule.dayHours ? (schedule.dayHours[currentDay] || []) : [];

            if (todayHours.length === 0) {
                alert(`${teacher} לא מלמד ביום ${dayNames[currentDay]}`);
                return;
            }''',
     u'''            // Get today's hours for this teacher
            // שעות בלי כיתה ממופה (הדרכה/גנים/קב"ש וכדומה) אינן נכללות —
            // "תפוס, אין כיתה": אם נעדר באותה שעה אין מה לכסות, ולכן אין
            // טעם לדווח עליה כהיעדרות הדורשת מ"מ.
            const allDayHours = schedule.dayHours ? (schedule.dayHours[currentDay] || []) : [];
            const todayHours = allDayHours.filter(h => getTeacherClassAtHour(teacher, currentDay, h));
            const skippedNonClass = allDayHours.filter(h => !todayHours.includes(h));

            if (allDayHours.length === 0) {
                alert(`${teacher} לא מלמד ביום ${dayNames[currentDay]}`);
                return;
            }
            if (todayHours.length === 0) {
                alert(`${teacher} ביום ${dayNames[currentDay]} — כל השעות הן שעות הדרכה בלי כיתה, אין מה לדווח.`);
                return;
            }''')

# -------------------------------------------- 2. שמירת הדיווח עצמה
swap('save filter',
     u'''            const teacher = teacherSelect.value === 'other' ? teacherManual.value : teacherSelect.value;
            const hours = getSelectedHours();
            const reason = document.getElementById('absence-reason').value;''',
     u'''            const teacher = teacherSelect.value === 'other' ? teacherManual.value : teacherSelect.value;
            const selectedHours = getSelectedHours();
            // הגנה גם כשהשעה נבחרה ידנית (לא רק דרך "כל היום") — שעה בלי
            // כיתה ממופה אינה נשמרת כהיעדרות; "תפוס, אין כיתה" כמו הדרכה/גנים.
            const hours = selectedHours.filter(h => getTeacherClassAtHour(teacher, currentDay, h));
            const classlessHours = selectedHours.filter(h => !hours.includes(h));
            const reason = document.getElementById('absence-reason').value;''')

swap('confirm message note',
     u'''            const confirmMsg = `האם אתה בטוח שברצונך לדווח על היעדרות?\\n\\nמורה: ${teacher}\\nיום: ${dayName}${forNextWeek ? ' (📅 שבוע הבא!)' : ''}\\nשעות: ${hoursText}`;''',
     u'''            const confirmMsg = `האם אתה בטוח שברצונך לדווח על היעדרות?\\n\\nמורה: ${teacher}\\nיום: ${dayName}${forNextWeek ? ' (📅 שבוע הבא!)' : ''}\\nשעות: ${hoursText}`
                + (classlessHours.length ? `\\n\\nℹ️ לא נשמרות: שעה ${classlessHours.join(', ')} — הדרכה, אין כיתה לכסות.` : '');''')

swap('empty-after-filter guard',
     u'''            if (!teacher) { alert('נא לבחור מורה'); return; }
            if (hours.length === 0) { alert('נא לבחור לפחות שעה אחת'); return; }''',
     u'''            if (!teacher) { alert('נא לבחור מורה'); return; }
            if (hours.length === 0 && classlessHours.length) {
                alert(`כל השעות שנבחרו (${classlessHours.join(', ')}) הן שעות הדרכה בלי כיתה — אין צורך לדווח עליהן.`);
                return;
            }
            if (hours.length === 0) { alert('נא לבחור לפחות שעה אחת'); return; }''')

with io.open(PATH, 'w', encoding='utf-8', newline='') as f:
    f.write(src)

print(u'✓ סינון שעות ללא כיתה הוטמע  (%d → %d תווים)' % (before, len(src)))
