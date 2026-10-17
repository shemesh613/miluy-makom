# -*- coding: utf-8 -*-
"""
patch_reportahead.py — 17.10.2026

**"עכשיו אפשר לדווח רק עד מחר — מה אם אני רוצה לדווח כמה ימים קדימה?"**

הבדיקה: `isDayLocked()` כבר תומכת בזה במלואה — יום שהוא יותר מ"מחר"
מוחזר כ"פתוח" (`return false`), ו-`updateLockedNotice()` כבר יודעת
להציג טופס תקין לכל יום. **אין שום נעילה אמיתית שמונעת דיווח קדימה.**

התקלה היחידה: `renderReportDayPicker()` בנתה רק 3 כפתורים — היום,
מחר, מחרתיים — כך שלא הייתה דרך ללחוץ על יום רביעי אם היום ראשון.
(את היום הרביעי כן אפשר היה להגיע אליו בעקיפין דרך בורר היום הכללי
למעלה בדף, אבל זה לא מה שרואים בטופס הדיווח עצמו.)

התיקון: הכפתורים מכסים את כל השבוע הקרוב (א'–ו', לא כולל שבת) —
עד 6 יום קדימה, לא רק 3.

הרצה: python tools/patch_reportahead.py [index.html]   ·   אידמפוטנטי.
"""
import io
import sys

PATH = sys.argv[1] if len(sys.argv) > 1 else 'index.html'

with io.open(PATH, encoding='utf-8') as f:
    src = f.read()

OLD = u"""            const opts = [t.day, (t.day + 1) % 7, (t.day + 2) % 7]
                .filter(d => d !== 6)                       // אין דיווח לשבת
                .filter((d, i, a) => a.indexOf(d) === i);"""

if OLD not in src:
    if u"// כל השבוע הקרוב — לא רק 3 ימים" in src:
        print(u'↻ כבר קיים — לא שונה דבר')
        raise SystemExit(0)
    raise SystemExit(u'✗ המקור לא נמצא במצב המצופה')

NEW = u"""            // כל השבוע הקרוב — לא רק 3 ימים. isDayLocked כבר תומכת בדיווח
            // קדימה על כל יום; זו הייתה רק מגבלת תצוגה של הכפתורים.
            const opts = [0, 1, 2, 3, 4, 5, 6].map(i => (t.day + i) % 7)
                .filter(d => d !== 6)                       // אין דיווח לשבת
                .filter((d, i, a) => a.indexOf(d) === i);"""

src = src.replace(OLD, NEW)

# תאריך על כל כפתור — עם 6 ימים ולא רק 3, "שלישי" לבדו כבר לא חד-משמעי
OLD2 = u"""                <div class="rdp-btns">${opts.map(d => {
                    const l = reportDayLabel(d);
                    return `<button type="button" class="rdp-btn${d === currentDay ? ' on' : ''}"
                        onclick="setReportDay(${d})">${dayNames[d]}${l.rel ? ` (${l.rel})` : ''}</button>`;
                }).join('')}</div>`;"""
if OLD2 not in src:
    raise SystemExit(u'✗ בלוק הכפתורים לא נמצא')
NEW2 = u"""                <div class="rdp-btns">${opts.map(d => {
                    const l = reportDayLabel(d);
                    return `<button type="button" class="rdp-btn${d === currentDay ? ' on' : ''}"
                        onclick="setReportDay(${d})">${dayNames[d]}${l.rel ? ` (${l.rel})` : ''}
                        <span class="rdp-btn-date">${l.date}</span></button>`;
                }).join('')}</div>`;"""
src = src.replace(OLD2, NEW2)

OLD3 = u"""        .rdp-btn.on { background:#1565c0; border-color:#1565c0; color:#fff; font-weight:700; }"""
if OLD3 not in src:
    raise SystemExit(u'✗ CSS .rdp-btn.on לא נמצא')
NEW3 = OLD3 + u"""
        .rdp-btn-date { display:block; font-size:0.72rem; opacity:.7; margin-top:1px; }"""
src = src.replace(OLD3, NEW3)

with io.open(PATH, 'w', encoding='utf-8', newline='') as f:
    f.write(src)

print(u'✓ בורר יום הדיווח מכסה עכשיו שבוע שלם קדימה, עם תאריך על כל כפתור')
