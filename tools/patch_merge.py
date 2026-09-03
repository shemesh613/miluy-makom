# -*- coding: utf-8 -*-
"""הצעות איחוד ברורות + תיקון כיתה בלי מקבילה (ד בתשפ"ז)."""
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


# ---------- 1. לסמן כיתה סמוכה שאין לה מקבילה ----------
sub(r"""                        if \(adjTeacher && adjTeacher !== a\.teacher\) \{
                            mergeable\.push\(\{
                                id, teacher: a\.teacher, hour: absenceHour,
                                absentClass, parallelClass: adjClass, coveringTeacher: adjTeacher,
                                isAdjacent: true
                            \}\);
                        \}""",
    """                        if (adjTeacher && adjTeacher !== a.teacher) {
                            mergeable.push({
                                id, teacher: a.teacher, hour: absenceHour,
                                absentClass, parallelClass: adjClass, coveringTeacher: adjTeacher,
                                isAdjacent: true,
                                // לכיתה סמוכה בלי מקבילה אין מה לאחד בתוך עצמה
                                // (בתשפ"ז: ד, ז, ח). במקרה כזה הכיתה של הנעדר
                                // מצטרפת אליה, ולא להפך.
                                joinInto: !parallelClasses[adjClass],
                                // מי נשאר עם הכיתה המאוחדת כשהמלמד השני מתפנה
                                stayingTeacher: (parallelClasses[adjClass] || [])
                                    .map(sc => getTeacherOfClassAtHour(sc, currentDay, absenceHour))
                                    .find(t => t && t !== adjTeacher) || null
                            });
                        }""",
    'סימון כיתה בלי מקבילה')

# ---------- 2. ניסוח ברור ----------
sub(r"""                    let description;
                    if \(m\.isAdjacent\) \{
                        // Adjacent: e\.g\. "כיתות ב1\+ב2 יאוחדו → הרב שמשון יעבור לכיתה ג"
                        const mergedSubs = parallelClasses\[m\.parallelClass\];
                        const subsLabel = mergedSubs \? mergedSubs\.join\('\+'\) : m\.parallelClass;
                        description = `כיתות \$\{subsLabel\} יאוחדו → \$\{m\.coveringTeacher\} יעבור לכיתה \$\{classLabel\}`;
                    \} else \{
                        // Direct parallel merge: the parallel teacher teaches both sub-classes together
                        const mergedSubs = parallelClasses\[m\.parallelClass\];
                        const subsLabel = mergedSubs \? mergedSubs\.join\('\+'\) : 'כיתות ' \+ m\.parallelClass;
                        description = `איחוד כיתות \$\{subsLabel\} → \$\{m\.coveringTeacher\} ילמד את הכיתה המאוחדת`;
                    \}""",
    """                    // ניסוח מפורש: מי יושב עם מי, איפה, ומי מלמד
                    const description = mergeDescription(m);""",
    'שימוש בניסוח החדש')

# ---------- 2ב. ניקוי הצעות שאי אפשר להציג ----------
sub(r'            if \(mergeable\.length === 0\) \{',
    """            // שלוש הצעות שאסור להראות:
            //  · בלי כיתה מזוהה — לא ברור מי מתאחדת עם מי
            //  · איחוד בכיתה סמוכה שאין בה מי שיישאר עם המאוחדת
            //  · כפילות של אותה הצעה בדיוק
            const seenMerge = new Set();
            const cleanedMerges = mergeable.filter(m => {
                if (!m.absentClass) return false;
                const r = mergeRoles(m);
                if (!r.host) return false;
                const sig = [m.id, m.hour, r.host, r.mover || '', r.hostClasses.join('+')].join('|');
                if (seenMerge.has(sig)) return false;
                seenMerge.add(sig);
                return true;
            });
            mergeable.length = 0;
            cleanedMerges.forEach(m => mergeable.push(m));

            if (mergeable.length === 0) {""",
    'ניקוי הצעות')

sub(r'(?=        // Approve a merge\n        function approveMerge)',
    """        /* ===== ניסוח הצעת האיחוד =====
           שלוש אפשרויות שונות לגמרי, וחשוב שיהיה ברור איזו מהן מוצעת:
             1. לכיתה של הנעדר יש מקבילה — שתיהן יושבות יחד אצל מלמד המקבילה
             2. לכיתה סמוכה יש מקבילה — היא מתאחדת בתוך עצמה, ומלמד מתפנה לבוא
             3. לכיתה סמוכה אין מקבילה — הכיתה של הנעדר מצטרפת אליה
           המקרה השלישי נוצר בתשפ"ז כי ד, ז ו-ח הן כיתה אחת כל אחת. */
        // מפרק את ההצעה לתפקידים: מי מאחד (מארח) ומי עובר — אם בכלל
        function mergeRoles(m) {
            const cls = m.absentClass || '';
            if (!m.isAdjacent) {
                const subs = parallelClasses[m.parallelClass] || [];
                const other = subs.find(s => s !== cls) || m.parallelClass;
                return { host: m.coveringTeacher, hostClasses: [cls, other],
                         where: other, mover: null, note: '' };
            }
            if (m.joinInto) {
                return { host: m.coveringTeacher, hostClasses: [cls, m.parallelClass],
                         where: m.parallelClass, mover: null,
                         note: `לכיתה ${m.parallelClass} אין מקבילה השנה, לכן היא זו שמארחת` };
            }
            const subs = parallelClasses[m.parallelClass] || [];
            return { host: m.stayingTeacher, hostClasses: subs, where: subs[0] || m.parallelClass,
                     mover: m.coveringTeacher, moverTo: cls, note: '' };
        }

        function mergeDescription(m) {
            const r = mergeRoles(m);
            const rows = [];
            rows.push(`<div class="merge-row"><span class="merge-role">מאחד</span>` +
                `<strong>${r.host || '—'}</strong> — כיתות <strong>${r.hostClasses.join(' + ')}</strong> יושבות יחד בכיתה ${r.where}</div>`);
            if (r.mover) {
                rows.push(`<div class="merge-row"><span class="merge-role move">עובר</span>` +
                    `<strong>${r.mover}</strong> — מתפנה ובא לכיתה <strong>${r.moverTo}</strong></div>`);
            } else {
                rows.push(`<div class="merge-row"><span class="merge-role none">אף אחד לא עובר</span>` +
                    `<span class="muted">התלמידים מצטרפים, המלמדים נשארים במקומם</span></div>`);
            }
            if (r.note) rows.push(`<div class="merge-note">${r.note}</div>`);
            return rows.join('');
        }

        // הודעה מותאמת לכל אחד מהשניים
        function mergeMessages(m) {
            const r = mergeRoles(m);
            const h = `שעה ${m.hour}`;
            return {
                host: r.host ? { name: r.host,
                    msg: `שלום ${r.host}, ${m.teacher} נעדר ב${h}. כיתות ${r.hostClasses.join(' + ')} יושבות יחד אצלך בכיתה ${r.where}. תודה רבה!` } : null,
                mover: r.mover ? { name: r.mover,
                    msg: `שלום ${r.mover}, ${m.teacher} נעדר ב${h}. הכיתה שלך מתאחדת, ואתה מתפנה לכיתה ${r.moverTo}. תודה רבה!` } : null,
            };
        }

""", 'פונקציית הניסוח')

# ---------- 3. כרטיס ברור יותר ----------
sub(r"""                    return `
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px; background: white; border-radius: 8px; margin-bottom: 8px;">
                        <div>
                            <strong>\$\{m\.teacher\}</strong> - שעה \$\{m\.hour\}\$\{classLabel \? ` \(כיתה \$\{classLabel\}\)` : ''\}
                            <br><small style="color: #666;">\$\{description\}</small>
                        </div>
                        <button class="btn-merge" onclick="approveMerge\('\$\{m\.id\}', '\$\{m\.parallelClass\}', '\$\{escapedTeacher\}'\)">🔗 אחד</button>
                    </div>`;""",
    """                    const msgs = mergeMessages(m);
                    const contactRow = ['host', 'mover'].map(k => msgs[k]
                        ? `<div class="merge-send"><span>${k === 'host' ? 'מאחד' : 'עובר'}: <strong>${msgs[k].name}</strong></span>
                             ${getContactButtonsHTML(msgs[k].name, msgs[k].msg)}</div>` : '').join('');
                    return `
                    <div class="merge-card">
                        <div class="merge-body">
                            <div class="merge-head">
                                <span class="merge-hour">שעה ${m.hour}</span>
                                <span class="merge-absent">${m.teacher}${classLabel ? ` · כיתה ${classLabel}` : ''} נעדר</span>
                            </div>
                            <div class="merge-what">${description}</div>
                            <div class="merge-sends">${contactRow}</div>
                        </div>
                        <button class="btn-merge" onclick="approveMerge('${m.id}', '${m.parallelClass}', '${escapedTeacher}')">🔗 אחד</button>
                    </div>`;""",
    'כרטיס הצעה')

# ---------- 4. גם טקסט האישור ----------
sub(r"""            const confirmMsg = isDirectMerge
                \? `לאשר איחוד כיתות \$\{subsLabel\} בשעה \$\{absenceHour\}\?\\n\$\{coverName\} ילמד את הכיתה המאוחדת`
                : `לאשר איחוד\? כיתות \$\{subsLabel\} יאוחדו בשעה \$\{absenceHour\}\$\{stayingTeacher \? '\\n' \+ stayingTeacher \+ ' ילמד את הכיתה המאוחדת' : ''\}\\n\$\{coverName\} יעבור לכיתה \$\{absentClass\}`;""",
    """            const noParallel = !parallelClasses[parallelClass];
            const confirmMsg = isDirectMerge
                ? `לאשר?\\n\\nכיתות ${subsLabel} יושבות יחד בשעה ${absenceHour}\\nמאחד: ${coverName} — מלמד את שתיהן\\nאף אחד לא עובר`
                : noParallel
                ? `לאשר?\\n\\nכיתה ${absentClass} מצטרפת לכיתה ${parallelClass} בשעה ${absenceHour}\\nמאחד: ${coverName} — מלמד את שתיהן יחד\\nאף אחד לא עובר (לכיתה ${parallelClass} אין מקבילה השנה)`
                : `לאשר?\\n\\nכיתות ${subsLabel} יושבות יחד בשעה ${absenceHour}\\nמאחד: ${stayingTeacher || '—'}\\nעובר: ${coverName} → כיתה ${absentClass}`;""",
    'טקסט אישור')

CSS = """        .merge-card { display:flex; justify-content:space-between; align-items:center; gap:12px;
            padding:12px 14px; background:#fff; border:1px solid #d6e2f2;
            border-inline-start:4px solid #1565c0; border-radius:10px; margin-bottom:8px; }
        .merge-head { display:flex; gap:8px; align-items:center; flex-wrap:wrap; margin-bottom:4px; }
        .merge-hour { background:#1565c0; color:#fff; border-radius:6px;
            padding:1px 9px; font-size:0.78rem; font-weight:700; }
        .merge-absent { color:#c62828; font-size:0.86rem; }
        .merge-what { font-size:0.93rem; color:#1c2024; line-height:1.6; }
        .merge-row { display:flex; gap:8px; align-items:baseline; flex-wrap:wrap; margin-bottom:3px; }
        .merge-role { background:#e7f0fa; color:#1565c0; border-radius:6px; padding:1px 8px;
            font-size:0.75rem; font-weight:700; white-space:nowrap; }
        .merge-role.move { background:#fdf3e0; color:#8a5300; }
        .merge-role.none { background:#eef0f3; color:#6b7280; font-weight:600; }
        .merge-note { color:#8a5300; font-size:0.82rem; margin-top:3px; }
        .merge-sends { display:flex; flex-wrap:wrap; gap:10px; margin-top:8px;
            padding-top:8px; border-top:1px dashed #dbe2ea; }
        .merge-send { display:flex; align-items:center; gap:6px; font-size:0.82rem; color:#5a6069; }
    </style>"""
sub(r'    </style>', CSS, 'עיצוב הכרטיס')

open(APP, 'w', encoding='utf-8').write(src)
print('\n%d תיקונים הוחלו. גודל: %d → %d תווים' % (n, before, len(src)))
