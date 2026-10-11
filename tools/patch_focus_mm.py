# -*- coding: utf-8 -*-
"""
patch_focus_mm.py — 11.10.2026

שני שינויים, שניהם בניסוח ובחישוב ולא במבנה:

1. **תורנויות החצר יוצאות מחישוב מילוי המקום לגמרי.** הן מערכת נפרדת
   שמנוהלת במקום אחר. עד עכשיו הן הורידו את התקרה האישית (`substCap`),
   נספרו בחובות (`debtStatus`) והופיעו בהודעות ובאזהרות — וזה בלבל:
   המערכת דיברה על תורנויות בזמן שמשבצים מילוי מקום. מעתה היא מודדת
   מילויי מקום בלבד. (לשונית התורנות עצמה לא נוגעים.)

   תופעת לוואי מכוונת: ה-22-מתוך-27-על-אפס נעלם מעצמו, כי האפס נבע
   כולו מחיסור התורנויות.

2. **המורה נועה והמורה טובי — תמיד אופציה.** לשתיהן הרבה שעות פנויות
   כרגע, ושתיהן אינן בקובץ המערכת, ולכן אין ממה לגזור זמינות. הן
   מוצעות בכל שעה (כמו הרב צביקה), בלי תקרה ובלי סימון "לוודא".

הרצה: python tools/patch_focus_mm.py [index.html]
הסקריפט אידמפוטנטי — הרצה חוזרת לא תשנה דבר.
"""
import io
import re
import sys

PATH = sys.argv[1] if len(sys.argv) > 1 else 'index.html'

with io.open(PATH, encoding='utf-8') as f:
    src = f.read()

before = len(src)
applied, skipped = [], []


def swap(label, old, new, sentinel=None):
    """החלפה מדויקת, בדיוק פעם אחת. אם ה'חדש' כבר שם — דילוג שקט.

    `sentinel` נדרש כשה'חדש' מכיל בתוכו את ה'ישן' (הוספה לפני קוד קיים) —
    בלעדיו ההרצה השנייה תתאים שוב ותכפיל את הבלוק."""
    global src
    if sentinel and sentinel in src:
        skipped.append(label)
        return
    if old not in src:
        if new in src:
            skipped.append(label)
            return
        raise SystemExit(u'✗ %s: המקור לא נמצא — הקובץ אינו במצב המצופה' % label)
    if src.count(old) != 1:
        raise SystemExit(u'✗ %s: %d התאמות, צפויה אחת' % (label, src.count(old)))
    src = src.replace(old, new)
    applied.append(label)


# ---------------------------------------------------------------- 1. התקרה
swap('comment: cap', u'''        /* ===== תקרה משולבת, פרופורציונלית לשעות =====
           3.9: התקרה אינה 4 שטוח לכולם. מלמד עם 8 ש"ש לא אמור לשאת כמו
           מלמד עם 38. הנוסחה: round(ש"ש/9), בין 1 ל-4 — אותו היגיון
           שנקבע לתורנויות החצר: מי שעובד יותר שעות סופג יותר.

           תורנויות החצר הן "קבועות" וגוברות: הן נשארות כפי שהן, והתקרה
           המשולבת מגבילה רק את מילויי המקום. מי שהחצר כבר מילאה את
           המכסה שלו — לא יקבל מ"מ בכלל. עד 2 ביום לאותו מלמד. */''',
     u'''        /* ===== תקרת מילוי מקום, פרופורציונלית לשעות =====
           התקרה אינה 4 שטוח לכולם. מלמד עם 8 ש"ש לא אמור לשאת כמו מלמד
           עם 38. הנוסחה: round(ש"ש/9), בין 1 ל-4. עד 2 ביום לאותו מלמד.

           ⚠️ 11.10: **תורנויות החצר יצאו מהחישוב לגמרי.** הן מערכת נפרדת
           שמנוהלת במקום אחר, ולכן אין להן מה להופיע כאן — לא בתקרה, לא
           בחובות ולא בהודעות למלמדים. המערכת הזו מודדת מילויי מקום בלבד.
           `yardDutyCount` נשאר בקוד כי לשונית התורנות עדיין משתמשת בו,
           אבל **אסור להחזיר אותו לכאן.** */''')

swap('substCap', u'''        function substCap(teacher) {
            if (isPartialYard(teacher)) return null;      // שעותיהן אינן במערכת
            return Math.max(0, combinedCap(teacher) - yardDutyCount(teacher));
        }''',
     u'''        function substCap(teacher) {
            if (noCapData(teacher)) return null;          // שעותיהן אינן במערכת
            return combinedCap(teacher);
        }''')

swap('capacityNote', u'''            if (cap === null) return { text: 'שעותיה אינן במערכת — לוודא', cls: 'cap-unknown', left: 99 };
            const used = assignedCount(teacher);
            const left = cap - used;
            if (cap === 0) return { text: `0 — ${yardDutyCount(teacher)} תורנויות חצר, מכסה ${combinedCap(teacher)} (${weeklyHours(teacher)} ש"ש)`,
                                    cls: 'cap-none', left: 0 };''',
     u'''            if (cap === null) return {
                text: ALWAYS_AVAILABLE.includes(teacher) ? 'זמינה — הרבה שעות פנויות'
                                                         : 'שעותיה אינן במערכת — לוודא',
                cls: 'cap-unknown', left: 99 };
            const used = assignedCount(teacher);
            const left = cap - used;''')

swap('debtStatus: used', u'''            const used = assignedCount(coverer) + yardDutyCount(coverer);''',
     u'''            const used = assignedCount(coverer);   // מ"מ בלבד — תורנויות אינן נספרות''')

swap('assign warning', u'''                    if (used >= cap) warn.push(cap === 0
                        ? `${substitute} כבר על ${yardDutyCount(substitute)} תורנויות חצר — התקרה המשולבת שלו מלאה.`
                        : `${substitute} כבר על ${used} מילויי מקום השבוע (התקרה שלו ${cap}).`);''',
     u'''                    if (used >= cap) warn.push(
                        `${substitute} כבר על ${used} מילויי מקום השבוע (התקרה שלו ${cap}).`);''')

# ------------------------------------------------- 2. נועה וטובי כאופציה
swap('EXTRA_STAFF', u'''        // המורה נועה אינה בקובץ המערכת — מתווספת לצוות ידנית
        const EXTRA_STAFF = ['המורה נועה'];''',
     u'''        // נועה וטובי אינן בקובץ המערכת — מתווספות לצוות ידנית
        const EXTRA_STAFF = ['המורה נועה', 'המורה טובי'];

        /* 11.10: לשתיהן יש **כרגע** הרבה שעות פנויות, ואין להן שעות בקובץ
           המערכת — כלומר אין ממה לגזור זמינות. לכן הן מוצעות תמיד, בכל
           שעה, כמו ממלא מקום קבוע: בלי תקרה שבועית ובלי סימון "לוודא".
           זה מצב זמני — כשיתייצבו שעותיהן יש להוציא אותן מכאן. */
        const ALWAYS_AVAILABLE = ['המורה נועה', 'המורה טובי'];

        // מי שאי אפשר לחשב לו תקרה, כי שעותיו אינן במערכת
        const noCapData = t => isPartialYard(t) || ALWAYS_AVAILABLE.includes(t);''')

swap('always-available picker', u'''            return filtered;
        }

        // Check if a class matches a trip class (handles ה1/ה2 → ה)''',
     u'''            // נועה וטובי — תמיד אופציה. שעותיהן אינן בקובץ, ולכן אם לא
            // נוסיף אותן כאן הן פשוט לא תופענה באף שעה.
            ALWAYS_AVAILABLE.forEach(name => {
                if (filtered.some(t => t.name === name)) return;
                if (isTeacherUnavailable(name, hour)) return;
                filtered.push({
                    name: name,
                    hours: ['בוקר', '4', '5', '6', '7', '8', '9', '10', 'סדר ערב'],
                    reason: 'שעות פנויות — זמינה למ"מ',
                    isRequired: false,
                    alwaysAvailable: true
                });
            });

            return filtered;
        }

        // Check if a class matches a trip class (handles ה1/ה2 → ה)''',
     sentinel=u'ALWAYS_AVAILABLE.forEach')

swap('always-available in panel',
     u'''            // מי שהוגדר לעדיפות מקודם — אך ורק לשעות החלון שלו, ורק אם
            // הן באמת קיימות היום. שאר שעותיו הפנויות נשארות כרגיל.''',
     u'''            /* נועה וטובי אינן בקובץ המערכת, ולכן הלולאה שמעל דילגה עליהן
               לגמרי — הן לא היו מופיעות ברשימת הפנויים בשום יום. מוסיפים
               אותן ידנית, עם כל השעות, כל עוד הן לא מלוות טיול. */
            ALWAYS_AVAILABLE.forEach(name => {
                if (teachersOnTrip.includes(name)) {
                    notWorking.push({ name: name, reason: 'מלווה בטיול' });
                    return;
                }
                if (optional.some(o => o.name === name) ||
                    required.some(o => o.name === name)) return;
                optional.push({
                    name: name,
                    hours: ['בוקר', '4', '5', '6', '7', '8', '9', '10', 'סדר ערב'],
                    teachingHours: [],
                    reason: 'שעות פנויות — זמינה למ"מ',
                    priority: 1.2,            // אחרי ממלא מקום קבוע, לפני השאר
                    alwaysAvailable: true
                });
            });

            // מי שהוגדר לעדיפות מקודם — אך ורק לשעות החלון שלו, ורק אם
            // הן באמת קיימות היום. שאר שעותיו הפנויות נשארות כרגיל.''',
     sentinel=u'ALWAYS_AVAILABLE.forEach(name => {\n                if (teachersOnTrip')

swap('FEMALE_STAFF', u'''        const FEMALE_STAFF = ["חגית", "לאה", "שרה תורג'מן", "המורה שרה אליה",
                              "המורה רבקי", "המורה נועה"];''',
     u'''        const FEMALE_STAFF = ["חגית", "לאה", "שרה תורג'מן", "המורה שרה אליה",
                              "המורה רבקי", "המורה נועה", "המורה טובי"];''')

# נועה יוצאת מ-PARTIAL_DATA — ההערה מ-17.8 התיישנה, ובכל שיבוץ שלה
# היא הקפיצה אזהרת "לוודא זמינות". היא נשארת ב-PARTIAL_YARD (אין שעות).
m = re.search(u"\n *'המורה נועה': 'מסרה \\(17\\.8\\)[^\n]*\n", src)
if m:
    src = src[:m.start()] + (
        u"\n            // המורה נועה הוצאה מכאן ב-11.10: היא זמינה בפועל בהרבה "
        u"שעות\n            // (ראה ALWAYS_AVAILABLE), וההערה מ-17.8 רק הקפיצה אזהרה מיותרת.\n"
    ) + src[m.end():]
    applied.append('PARTIAL_DATA: נועה')
else:
    skipped.append('PARTIAL_DATA: נועה')

swap('cap badge tooltip',
     u'''                        <span class="badge badge-optional">${t.windowPriority ? '⭐ עדיפות' : (t.reason === 'ממלא מקום קבוע' ? 'קבוע' : 'פנוי')}</span>
                        <span class="cap-badge ${cap.cls}" title="תורנויות חצר + מילויי מקום ≤ 4 בשבוע">${cap.text}</span>''',
     u'''                        <span class="badge badge-optional">${t.windowPriority ? '⭐ עדיפות'
                            : t.alwaysAvailable ? 'זמינה'
                            : (t.reason === 'ממלא מקום קבוע' ? 'קבוע' : 'פנוי')}</span>
                        <span class="cap-badge ${cap.cls}" title="תקרת מילויי מקום לשבוע, לפי ש&quot;ש">${cap.text}</span>''')

# ------------------------------------------------------ 3. פרטי קשר חסרים
swap('contacts', u'''            'המורה רבקי': { method: 'email', only: [], email: 'rivkiamar5@gmail.com' },
        };''',
     u'''            'המורה רבקי': { method: 'email', only: [], email: 'rivkiamar5@gmail.com' },
            // 11.10: שתיהן זמינות למ"מ אבל אין להן פרטי קשר במערכת.
            // `only: []` מונע כפתורים שבורים, וה-note מוצג כתזכורת להשלים.
            'המורה נועה': { method: 'email', only: [], note: 'חסרים טלפון ומייל — להשלים' },
            'המורה טובי': { method: 'email', only: [], note: 'חסרים טלפון ומייל — להשלים' },
        };''')

swap('contact buttons note', u'''            const contact = teacherContacts[teacher];
            if (!contact) return '';
            const msg = message''',
     u'''            const contact = teacherContacts[teacher];
            if (!contact) return '';
            // אין במה ליצור קשר — תזכורת במקום כפתורים שלא יעבדו
            if (!contact.phone && !contact.email)
                return `<span style="font-size:0.82rem;color:#b26a00;">\\u260e\\ufe0f ${contact.note || 'חסרים פרטי קשר'}</span>`;
            const msg = message''')

with io.open(PATH, 'w', encoding='utf-8', newline='') as f:
    f.write(src)

print(u'✓ הוחלו: %d' % len(applied))
for a in applied:
    print(u'   · %s' % a)
if skipped:
    print(u'↻ דולגו (כבר קיימים): %s' % u', '.join(skipped))
print(u'  %d → %d תווים' % (before, len(src)))
