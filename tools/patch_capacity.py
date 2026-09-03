# -*- coding: utf-8 -*-
"""חלון בודד מול רצף + תקרה משולבת של תורנויות ומילויי מקום."""
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

APP = 'miluy-makom/index.html'
src = open(APP, encoding='utf-8').read()
before = len(src)
n = 0


def sub(pattern, repl, label, count=1, flags=re.S):
    global src, n
    new, k = re.subn(pattern, lambda m: repl, src, count=count, flags=flags)
    if k != count:
        print('!! נכשל: %s (נמצאו %d)' % (label, k))
        sys.exit(1)
    src = new
    n += 1
    print('  ✓ %s' % label)


HELPERS = """        /* ===== חלון בודד מול רצף — ההבחנה שקובעת הכול =====
           חלון במערכת אינו הבטחה שהמלמד בבניין. נשרפנו על זה פעמיים,
           והמשותף לשני המקרים היה **רצף של שעתיים**:
             · הרב ינון  — 4–5 ריקות → יוצא מהמתחם עד 12:30
             · הרב שלומי — חמישי 4–5 ריקות → יוצא לקניות
           שעה בודדת בין שני שיעורים היא בטוחה: אין לו לאן ללכת ולחזור.
           רצף של 2+ — להניח שהוא יוצא, ולשאול לפני ששולחים. */
        function windowRuns(teacher, day) {
            const order = ['בוקר', '4', '5', '6', '7', '8', '9', '10', 'סדר ערב'];
            const t = teacherSchedule[teacher];
            if (!t || !(t.days || []).includes(day)) return [];
            const taught = (t.dayHours[day] || []).map(h => order.indexOf(h)).filter(i => i >= 0);
            if (taught.length < 2) return [];
            const lo = Math.min(...taught), hi = Math.max(...taught);
            const runs = []; let cur = [];
            for (let i = lo + 1; i < hi; i++) {
                if ((t.dayHours[day] || []).includes(order[i])) {
                    if (cur.length) { runs.push(cur); cur = []; }
                } else cur.push(order[i]);
            }
            if (cur.length) runs.push(cur);
            return runs;
        }
        const safeWindows  = (t, d) => windowRuns(t, d).filter(r => r.length === 1).flat();
        const riskyWindows = (t, d) => windowRuns(t, d).filter(r => r.length > 1).flat();
        function windowKind(teacher, day, hour) {
            if (safeWindows(teacher, day).includes(hour)) return 'safe';
            if (riskyWindows(teacher, day).includes(hour)) return 'risky';
            return null;
        }

        /* ===== תקרה משולבת =====
           התקרה נגזרת מהיקף המשרה ולא קבועה לכולם: round(ש"ש/9), בין 1 ל-4.
           כך מי שהחצר כבר העמיסה עליו לא מקבל גם מילויי מקום, ושתי
           המערכות מתאזנות מעצמן. עד 2 ביום לאותו מלמד. */
        const WEEK_CAP = 4, DAY_CAP = 2;
        const combinedCap = t => Math.max(1, Math.min(4, Math.round(weeklyHours(t) / 9)));
        const LAST_RESORT = ['הרב משה'];        // מנהל — רק אם אין ברירה

        function yardDutyCount(teacher) {
            return Object.values(YARD_DUTY).filter(t => t === teacher).length;
        }
        function weeklyHours(teacher) {
            const t = teacherSchedule[teacher];
            if (!t) return 0;
            return (t.days || []).reduce((s, d) => s + (t.dayHours[d] || []).length, 0);
        }
        function substCap(teacher) {
            if (isPartialData(teacher)) return null;      // שעותיהן אינן במערכת
            return Math.max(0, combinedCap(teacher) - yardDutyCount(teacher));
        }
        function assignedCount(teacher, day) {
            return Object.values(absencesData).filter(a =>
                a.substitute === teacher && !a.forNextWeek &&
                (day === undefined || a.day === day)).length;
        }
        function capacityNote(teacher) {
            const cap = substCap(teacher);
            if (cap === null) return { text: 'שעותיה אינן במערכת — לוודא', cls: 'cap-unknown', left: 99 };
            const used = assignedCount(teacher);
            const left = cap - used;
            if (cap === 0) return { text: `0 — ${yardDutyCount(teacher)} תורנויות חצר מילאו את המכסה (${combinedCap(teacher)})`, cls: 'cap-none', left: 0 };
            return { text: `${Math.max(0, left)} מתוך ${cap} השבוע`, cls: left > 0 ? 'cap-ok' : 'cap-none', left };
        }

"""
sub(r'(?=        // Update available teachers\n        function updateAvailableTeachers)',
    HELPERS, 'כללי חלון ותקרה')

# ---------- מיון: מי שנשארה לו מכסה קודם, המנהל אחרון ----------
sub(r'            // Sort optional by priority\n            optional\.sort\(\(a, b\) => \(a\.priority \|\| 99\) - \(b\.priority \|\| 99\)\);',
    """            // מיון: קודם לפי עדיפות, אחר כך מי שנשארה לו מכסה, והמנהל אחרון
            optional.sort((a, b) => {
                const lr = LAST_RESORT.indexOf(a.name) - LAST_RESORT.indexOf(b.name);
                if (LAST_RESORT.includes(a.name) !== LAST_RESORT.includes(b.name))
                    return LAST_RESORT.includes(a.name) ? 1 : -1;
                const ca = capacityNote(a.name).left > 0 ? 0 : 1;
                const cb = capacityNote(b.name).left > 0 ? 0 : 1;
                return (a.priority || 99) - (b.priority || 99) || ca - cb || lr;
            });""",
    'מיון לפי מכסה')

# ---------- תצוגה ----------
sub(r"""                    let hoursInfo = '';
                    if \(t\.windowPriority\) \{""",
    """                    const safe = safeWindows(t.name, currentDay).filter(h => (t.hours || []).includes(h));
                    const risky = riskyWindows(t.name, currentDay).filter(h => (t.hours || []).includes(h));
                    const cap = capacityNote(t.name);
                    let hoursInfo = '';
                    if (safe.length || risky.length) {
                        hoursInfo = (safe.length ? `✅ בטוח: <strong>${safe.join(', ')}</strong>` : '')
                            + (safe.length && risky.length ? ' · ' : '')
                            + (risky.length ? `<span class="risky">⚠️ רצף — לברר: ${risky.join(', ')}</span>` : '')
                            + ` | מלמד: ${(t.teachingHours || []).join(', ')}`;
                    } else if (t.windowPriority) {""",
    'תצוגת חלונות')

sub(r"""                        <span class="badge badge-optional">\$\{t\.windowPriority \? '⭐ עדיפות' : \(t\.reason === 'ממלא מקום קבוע' \? 'קבוע' : 'פנוי'\)\}</span>""",
    """                        <span class="badge badge-optional">${t.windowPriority ? '⭐ עדיפות' : (t.reason === 'ממלא מקום קבוע' ? 'קבוע' : 'פנוי')}</span>
                        <span class="cap-badge ${cap.cls}" title="תורנויות חצר + מילויי מקום ≤ 4 בשבוע">${cap.text}</span>""",
    'תג מכסה')

# ---------- אזהרה בשיבוץ ----------
sub(r"""            // Check if this is a new assignment \(not just changing\)
            const previousSubstitute = absencesData\[id\]\?\.substitute;
            const isNewAssignment = substitute && substitute !== previousSubstitute;""",
    """            // Check if this is a new assignment (not just changing)
            const previousSubstitute = absencesData[id]?.substitute;
            const isNewAssignment = substitute && substitute !== previousSubstitute;

            // שתי בדיקות לפני שמשבצים — תקרה שבועית, ורצף שבו הוא אולי לא בבניין
            if (isNewAssignment) {
                const a = absencesData[id] || {};
                const warn = [];
                const cap = substCap(substitute);
                if (cap !== null) {
                    const used = assignedCount(substitute);
                    if (used >= cap) warn.push(cap === 0
                        ? `${substitute} — ${yardDutyCount(substitute)} תורנויות חצר כבר מילאו את המכסה שלו (${combinedCap(substitute)} לפי ${weeklyHours(substitute)} ש"ש).`
                        : `${substitute} כבר על ${used} מילויי מקום השבוע (התקרה שלו ${cap}).`);
                    const day = assignedCount(substitute, a.day);
                    if (day >= DAY_CAP) warn.push(`כבר ${day} מילויי מקום באותו יום (המקסימום ${DAY_CAP}).`);
                }
                if (windowKind(substitute, a.day, a.hour) === 'risky')
                    warn.push(`השעה הזו היא חלק מרצף חלונות — ${substitute} עלול לא להיות בבניין. כדאי לוודא איתו.`);
                if (isPartialData(substitute))
                    warn.push(`${substitute} — ${PARTIAL_DATA[substitute]}. לוודא זמינות.`);
                if (warn.length && !confirm('⚠️ שים לב:\\n\\n· ' + warn.join('\\n· ') + '\\n\\nלשבץ בכל זאת?')) {
                    updateAllViews();
                    return;
                }
            }""",
    'אזהרות שיבוץ')

CSS = """        .risky { color:#b26a00; }
        .cap-badge { display:inline-block; border-radius:999px; padding:1px 9px;
            font-size:0.72rem; font-weight:600; white-space:nowrap; margin-inline-start:4px; }
        .cap-ok { background:#e8f3ed; color:#2e7d5b; }
        .cap-none { background:#fdecec; color:#c62828; }
        .cap-unknown { background:#fdf3e0; color:#8a5300; }
    </style>"""
sub(r'    </style>', CSS, 'עיצוב')

open(APP, 'w', encoding='utf-8').write(src)
print('\n%d תיקונים הוחלו. גודל: %d → %d תווים' % (n, before, len(src)))
