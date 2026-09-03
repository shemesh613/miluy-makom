# -*- coding: utf-8 -*-
"""מורות שהמערכת לא רואה במלואן + עדיפות דשא. רץ אחרי patch_reserve.py."""
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


# ---------- 1. הגדרת המורות ----------
BLOCK = """        /* ============ מורות שקובץ המערכת אינו משקף במלואן ============
           כמחצית משעותיהן היא הוראה מתקנת שאינה רשומה במערכת השעות, והמורה
           נועה אינה מופיעה בקובץ כלל. לכן **כל חישוב עומס מהקובץ מודד אותן
           בחסר**, ואסור להסיק מהקובץ שהן פנויות או שאינן זמינות.
           סוכם: התורנויות הקבועות נשארות, והן מחליפות בעדיפות ראשונה
           בעמדת הדשא. כל שיבוץ שלהן מסומן "לוודא זמינות" ולצידו חלופה
           מאומתת מהמערכת. כשיגיעו שעות הנוכחות האמיתיות — לעדכן כאן. */
        const PARTIAL_DATA = {
            'שרה תורג\\'מן': 'כמחצית משעותיה בהוראה מתקנת — לא רשומה במערכת',
            'המורה שרה אליה': 'כמחצית משעותיה בהוראה מתקנת — לא רשומה במערכת',
            'המורה נועה': 'אינה מופיעה בקובץ המערכת כלל',
        };
        const isPartialData = t => !!PARTIAL_DATA[t];
        const DASHA_POST = 'דשא (למטה)';

        // מורה שאין עליה נתונים מלאים נחשבת נוכחת — פשוט לא יודעים מתי.
        // רישום השעות שלה בקובץ אינו ראיה לכלום, לכן היא תמיד מועמדת אפשרית
        // בעמדת הדשא, ותמיד מסומנת לאימות.
        function partialDashaCandidates(dutyKey) {
            if (yardParse(dutyKey).post !== DASHA_POST) return [];
            const toran = YARD_DUTY[dutyKey];
            return Object.keys(PARTIAL_DATA).filter(t => t !== toran);
        }

"""
sub(r'(?=        /\* ==================== מצב מילואים ====================)', BLOCK,
    'הגדרת מורות ללא נתונים מלאים')

# ---------- 2. הוספת המורה נועה לצוות (אינה בקובץ) ----------
sub(r"        const allTeachers = \[",
    "        // המורה נועה אינה בקובץ המערכת — מתווספת לצוות ידנית\n"
    "        const EXTRA_STAFF = ['המורה נועה'];\n"
    "        const allTeachers = [",
    'הגדרת צוות נוסף')

sub(r'        enforcePersonalBlocks\(\);\n',
    '        enforcePersonalBlocks();\n'
    '        EXTRA_STAFF.forEach(t => { if (!allTeachers.includes(t)) allTeachers.push(t); });\n'
    '        allTeachers.sort((a, b) => a.localeCompare(b, \'he\'));\n',
    'צירוף המורה נועה לרשימה')

# הרשימה נבנית מחדש בכל החלפת מערכת — לשמור עליה גם שם
sub(r"            const names = new Set\(\[\.\.\.Object\.keys\(teacherSchedule\), \.\.\.Object\.keys\(teacherContacts\)\]\);",
    "            const names = new Set([...Object.keys(teacherSchedule), ...Object.keys(teacherContacts),\n"
    "                                   ...EXTRA_STAFF]);",
    'שמירת הצוות הנוסף בהחלפת מערכת')

# ---------- 3. עדיפות דשא + סימון לאימות בתורנות ----------
sub(r"""                const cands = \(\(YARD_SUBS\[d\.key\] \|\| \{\}\)\.cands \|\| \[\]\);
                const free = cands\.filter\(c =>
                    !taken\.has\(d\.slot \+ '\|' \+ c\.name\) && !yardAbsentAt\(c\.name, dayIdx, d\.slot\)
                    && !yardCoveringLesson\(c\.name, dayIdx, d\.slot\)\);""",
    """                const cands = ((YARD_SUBS[d.key] || {}).cands || []);
                const free = cands.filter(c =>
                    !taken.has(d.slot + '|' + c.name) && !yardAbsentAt(c.name, dayIdx, d.slot)
                    && !yardCoveringLesson(c.name, dayIdx, d.slot));
                // בעמדת הדשא המורות בעדיפות ראשונה — אך תמיד לאימות,
                // ותמיד עם חלופה מאומתת לצידן
                const partial = partialDashaCandidates(d.key)
                    .filter(t => !taken.has(d.slot + '|' + t) && !yardAbsentAt(t, dayIdx, d.slot)
                                 && !yardCoveringLesson(t, dayIdx, d.slot))
                    .map(t => ({ name: t, repay: [], verify: true }));""",
    'מועמדות דשא בעדיפות')

sub(r"""                if \(free\.length\) \{
                    const c = free\[0\];
                    taken\.add\(d\.slot \+ '\|' \+ c\.name\);
                    const repay = \(c\.repay \|\| \[\]\)\.find\(r => yardParse\(r\)\.day !== d\.day\) \|\| null;
                    return \{ \.\.\.d, status: 'auto', cover: c\.name, repay, options: free\.slice\(1\) \};
                \}""",
    """                const ranked = [...partial, ...free];
                if (ranked.length) {
                    const c = ranked[0];
                    taken.add(d.slot + '|' + c.name);
                    const repay = (c.repay || []).find(r => yardParse(r).day !== d.day) || null;
                    return { ...d, status: 'auto', cover: c.name, repay,
                             verify: !!c.verify,
                             backup: c.verify ? (free[0] ? free[0].name : null) : null,
                             options: ranked.slice(1) };
                }""",
    'בחירת מחליף עם עדיפות דשא')

# ---------- 4. תצוגת "לוודא זמינות" ----------
sub(r"""                const clashTxt = p\.clash""",
    """                const verifyTxt = p.verify
                    ? `<div class="yard-verify">🔎 לוודא זמינות — ${PARTIAL_DATA[p.cover] || ''}` +
                      (p.backup ? `<br>חלופה מאומתת: <strong>${p.backup}</strong>` : '') + '</div>'
                    : '';
                const clashTxt = p.clash""",
    'טקסט לוודא זמינות')

sub(r"""                        \$\{repayTxt\}
                        \$\{clashTxt\}""",
    """                        ${repayTxt}
                        ${verifyTxt}
                        ${clashTxt}""",
    'הצגת האימות בשורה')

# ---------- 5. סימון במסכי מילוי המקום ----------
sub(r"""        // Get contact button HTML for a teacher
        function getContactButtonsHTML\(teacher, message\) \{""",
    """        // תג לצד שם של מורה שאין עליה נתונים מלאים
        function partialBadge(teacher) {
            return isPartialData(teacher)
                ? ` <span class="partial-tag" title="${PARTIAL_DATA[teacher]}">לוודא זמינות</span>`
                : '';
        }

        // Get contact button HTML for a teacher
        function getContactButtonsHTML(teacher, message) {""",
    'תג לוודא זמינות')

CSS = """        .yard-verify { margin-top:4px; font-size:0.82rem; color:#8a5300;
            background:#fdf3e0; border-radius:8px; padding:4px 8px; }
        .partial-tag { display:inline-block; background:#fdf3e0; color:#8a5300;
            border:1px solid rgba(178,106,0,0.3); border-radius:999px;
            padding:0 8px; font-size:0.72rem; font-weight:600; }
    </style>"""
sub(r'    </style>', CSS, 'עיצוב')

open(APP, 'w', encoding='utf-8').write(src)
print('\n%d תיקונים הוחלו. גודל: %d → %d תווים' % (n, before, len(src)))
