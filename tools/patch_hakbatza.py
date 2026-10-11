# -*- coding: utf-8 -*-
"""
patch_hakbatza.py — 11.10.2026

**הקבצות בז׳ ובח׳.** הרב אליהו שמשון והרב סימון מלמדים את ז ואת ח
בו-זמנית, כל אחד הקבצה אחרת. כשאחד מהם נעדר — השני מאחד את שתי
ההקבצות. זה המצב בפועל ב-8 משבצות: ראשון/שני/רביעי ש10 ח, שני/שלישי/
רביעי ש8 ז, שלישי ש9 ח, חמישי ש10 ז.

המערכת לא הציעה את זה: ז ו-ח הן כיתה אחת כל אחת (`parallelClasses`
מחזיר null), ושניהם אינם מחנכים שלהן — ולכן מסלול "מקבילה" לא נתפס,
ובמקומו הוצע איחוד עם **כיתה סמוכה** (ו או ח), שזו תשובה גרועה כשהשותף
להקבצה יושב ממש באותה שעה.

⚠️ למה רשימה מפורשת ולא "שניהם מלמדים אותה כיתה באותה שעה":
בקובץ המערכת יש 32 חפיפות כאלה, ורובן אינן הקבצות — הרב משה חיים נתן
מופיע בטעות על ג2 בשש משבצות (באג ידוע בקובץ), ו-ו/ה מסומנות לפעמים
בכיתת הבסיס בלי הספרה. גזירה אוטומטית הייתה מייצרת הצעות שגויות.

הרצה: python tools/patch_hakbatza.py [index.html]   ·   אידמפוטנטי.
"""
import io
import sys

PATH = sys.argv[1] if len(sys.argv) > 1 else 'index.html'

with io.open(PATH, encoding='utf-8') as f:
    src = f.read()

if u'HAKBATZA_GROUPS' in src:
    print(u'↻ כבר קיים — לא שונה דבר')
    raise SystemExit(0)

before = len(src)
applied = []


def swap(label, old, new):
    global src
    if old not in src:
        raise SystemExit(u'✗ %s: המקור לא נמצא' % label)
    if src.count(old) != 1:
        raise SystemExit(u'✗ %s: %d התאמות, צפויה אחת' % (label, src.count(old)))
    src = src.replace(old, new)
    applied.append(label)


# ------------------------------------------------- 1. הגדרת ההקבצות
swap('HAKBATZA_GROUPS',
     u'''        // Class names for display
        const classNames = ['א','ב','ג','ד','ה','ו','ז','ח'];''',
     u'''        /* ===== הקבצות =====
           כיתה שמתפצלת לשתי קבוצות רמה הנלמדות **בו-זמנית** אצל שני
           מלמדים. זו אינה "כיתה מקבילה": ז ו-ח הן כיתה אחת כל אחת,
           ולכן `parallelClasses` מחזיר להן null והמסלול הרגיל לא תופס.
           כשאחד השניים נעדר — השני מאחד את שתי ההקבצות, ואף אחד לא עובר.

           ⚠️ רשימה מפורשת בכוונה. "שניהם מלמדים אותה כיתה באותה שעה"
           נראה ככלל אוטומטי יפה, אבל בקובץ יש 32 חפיפות כאלה ורובן
           אינן הקבצות: הרב משה חיים נתן רשום בטעות על ג2 בשש משבצות,
           ו-ה/ו מסומנות לפעמים בכיתת הבסיס בלי הספרה. */
        const HAKBATZA_GROUPS = [
            { teachers: ['הרב אליהו שמשון', 'הרב סימון'], classes: ['ז', 'ח'] },
        ];

        // השותף להקבצה באותה שעה — רק אם שניהם באמת על אותה כיתה אז
        function hakbatzaPartner(teacher, day, hour) {
            const mine = ((dayHourClassesData[teacher] || {})[day] || {})[hour];
            if (!mine) return null;
            for (const g of HAKBATZA_GROUPS) {
                if (!g.teachers.includes(teacher) || !g.classes.includes(mine)) continue;
                const other = g.teachers.find(t => t !== teacher &&
                    ((dayHourClassesData[t] || {})[day] || {})[hour] === mine);
                if (other) return { teacher: other, cls: mine };
            }
            return null;
        }

        // Class names for display
        const classNames = ['א','ב','ג','ד','ה','ו','ז','ח'];''')

# ------------------------------------------- 2. הצעת האיחוד עצמה
swap('suggest hakbatza',
     u'''                // Always also check adjacent classes (even if parallel was found)''',
     u'''                // הקבצה — השותף שיושב באותה שעה מאחד את שתי הקבוצות.
                // חשוב שזה יבוא לפני בדיקת הכיתות הסמוכות.
                const hak = hakbatzaPartner(a.teacher, currentDay, absenceHour);
                if (hak && !isTeacherUnavailable(hak.teacher, absenceHour)) {
                    mergeable.push({
                        id, teacher: a.teacher, hour: absenceHour,
                        absentClass: hak.cls, parallelClass: hak.cls,
                        coveringTeacher: hak.teacher, isHakbatza: true
                    });
                }

                // Always also check adjacent classes (even if parallel was found)''')

swap('suppress adjacent',
     u'''            const seenMerge = new Set();
            const cleanedMerges = mergeable.filter(m => {
                if (!m.absentClass) return false;''',
     u'''            // כשיש שותף להקבצה — הוא התשובה. איחוד עם כיתה סמוכה
            // באותה שעה הוא רעש שמסתיר אותה.
            const hakSlots = new Set(mergeable.filter(m => m.isHakbatza)
                                              .map(m => m.id + '|' + m.hour));
            const seenMerge = new Set();
            const cleanedMerges = mergeable.filter(m => {
                if (!m.absentClass) return false;
                if (m.isAdjacent && hakSlots.has(m.id + '|' + m.hour)) return false;''')

# ------------------------------------------------- 3. תפקידים וניסוח
swap('mergeRoles',
     u'''        function mergeRoles(m) {
            const cls = m.absentClass || '';
            if (!m.isAdjacent) {''',
     u'''        function mergeRoles(m) {
            const cls = m.absentClass || '';
            // הקבצה: אותה כיתה, שתי קבוצות, אחד מאחד ואיש לא עובר
            if (m.isHakbatza) {
                return { host: m.coveringTeacher, hostClasses: [cls], where: cls,
                         mover: null, hak: true,
                         note: `${cls} מתפצלת להקבצות — השותף להקבצה הוא שמאחד` };
            }
            if (!m.isAdjacent) {''')

swap('mergeDescription',
     u'''            rows.push(`<div class="merge-row"><span class="merge-role">מאחד</span>` +
                `<strong>${r.host || '—'}</strong> — כיתות <strong>${r.hostClasses.join(' + ')}</strong> יושבות יחד בכיתה ${r.where}</div>`);''',
     u'''            rows.push(r.hak
                ? `<div class="merge-row"><span class="merge-role">מאחד</span>` +
                  `<strong>${r.host || '—'}</strong> — <strong>שתי ההקבצות של ${r.where}</strong> יושבות יחד אצלו</div>`
                : `<div class="merge-row"><span class="merge-role">מאחד</span>` +
                  `<strong>${r.host || '—'}</strong> — כיתות <strong>${r.hostClasses.join(' + ')}</strong> יושבות יחד בכיתה ${r.where}</div>`);''')

swap('mergeMessages',
     u'''                host: r.host ? { name: r.host,
                    msg: `${r.host}, שלום. ${m.teacher} נעדר ב${h}, וכיתות ${r.hostClasses.join(' + ')} יושבות יחד אצלך בכיתה ${r.where} בבקשה. תודה רבה.` } : null,''',
     u'''                host: r.host ? { name: r.host,
                    msg: r.hak
                        ? `${r.host}, שלום. ${m.teacher} ${isFem(m.teacher) ? 'נעדרת' : 'נעדר'} ב${h}, ושתי ההקבצות של ${r.where} יושבות יחד אצלך בבקשה. תודה רבה.`
                        : `${r.host}, שלום. ${m.teacher} נעדר ב${h}, וכיתות ${r.hostClasses.join(' + ')} יושבות יחד אצלך בכיתה ${r.where} בבקשה. תודה רבה.` } : null,''')

# ------------------------------------------------- 4. אישור האיחוד
swap('approve onclick',
     u'''                        <button class="btn-merge" onclick="approveMerge('${m.id}', '${m.parallelClass}', '${escapedTeacher}')">🔗 אחד</button>''',
     u'''                        <button class="btn-merge" onclick="approveMerge('${m.id}', '${m.parallelClass}', '${escapedTeacher}', ${m.isHakbatza ? 'true' : 'false'})">🔗 אחד</button>''')

swap('approveMerge sig',
     u'''        function approveMerge(id, parallelClass, coveringTeacher) {''',
     u'''        function approveMerge(id, parallelClass, coveringTeacher, isHakbatza) {''')

swap('approve confirm',
     u'''            const noParallel = !parallelClasses[parallelClass];
            const confirmMsg = isDirectMerge''',
     u'''            const noParallel = !parallelClasses[parallelClass];
            const confirmMsg = isHakbatza
                ? `לאשר?\\n\\nשתי ההקבצות של ${parallelClass} יושבות יחד בשעה ${absenceHour}\\nמאחד: ${coverName}\\nאף אחד לא עובר`
                : isDirectMerge''')

swap('approve save',
     u'''            const updateData = {
                merged: true,
                mergedClass: parallelClass,
                directMerge: isDirectMerge,
                substitute: coverName,
                stayingTeacher: stayingTeacher || null
            };''',
     u'''            const updateData = {
                merged: true,
                mergedClass: parallelClass,
                // הקבצה היא איחוד ישיר: מלמד אחד, תפקיד אחד, אף אחד לא עובר
                directMerge: isHakbatza ? true : isDirectMerge,
                hakbatza: isHakbatza ? true : null,
                substitute: coverName,
                stayingTeacher: isHakbatza ? null : (stayingTeacher || null)
            };''')

# --------------------------------- 5. תווית אחידה בשלושת מסכי התצוגה
swap('mergedLabel helper',
     u'''        // Approve a merge
        function approveMerge(''',
     u'''        // איך קוראים לאיחוד בכל מסכי התצוגה — הקבצה אינה "כיתות ז"
        function mergedLabel(a) {
            if (a && a.hakbatza) return `שתי ההקבצות של ${a.mergedClass || ''}`;
            const subs = parallelClasses[(a && a.mergedClass) || ''];
            return subs ? subs.join('+') : ('כיתות ' + ((a && (a.mergedClass || a.mergedWith)) || ''));
        }

        // Approve a merge
        function approveMerge(''')

swap('label site 1',
     u'''                const subsLabel = mergedSubs ? mergedSubs.join('+') : ('כיתות ' + (a.mergedClass || a.mergedWith || ''));''',
     u'''                const subsLabel = mergedLabel(a);''')

swap('label site 2',
     u'''                    const mergedSubs = parallelClasses[mergedClass];
                    const subsLabel = mergedSubs ? mergedSubs.join('+') : ('כיתות ' + mergedClass);''',
     u'''                    const mergedSubs = parallelClasses[mergedClass];
                    const subsLabel = mergedLabel(a);''')

swap('label site 3',
     u'''                    const mergedSubs = parallelClasses[a.mergedClass];
                    const subsLabel = mergedSubs ? mergedSubs.join('+') : (a.mergedClass || '');''',
     u'''                    const mergedSubs = parallelClasses[a.mergedClass];
                    const subsLabel = mergedLabel(a);''')

with io.open(PATH, 'w', encoding='utf-8', newline='') as f:
    f.write(src)

print(u'✓ הוחלו: %d' % len(applied))
for a in applied:
    print(u'   · %s' % a)
print(u'  %d → %d תווים' % (before, len(src)))
