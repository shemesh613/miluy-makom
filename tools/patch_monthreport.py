# -*- coding: utf-8 -*-
"""
patch_monthreport.py — 24.10.2026

**"אני צריך דוח חודשי של כל המ"מ, ואפשר שזה כבר יחול על אוקטובר?"**

בדקתי ישירות ב-Firebase: שום דבר לא אבד. הארכיון השבועי האוטומטי
(`email-service.js checkAndRunWeeklyCleanup`, רץ כל שישי) מעתיק את
`/absences` ל-`/archived/{weekKey}/absences` **לפני** שהוא מנקה —
יש שם נתונים רציפים עוד מפברואר 2026. בדקתי את אוקטובר ספציפית:
93 רשומות מ"מ מ-30.9 עד היום, פזורות בין שלושה שבועות ארכיון
(2026-10-09, 2026-10-16, 2026-10-23) ועוד הנתונים החיים של השבוע
הנוכחי. כלומר **כן אפשר להחיל את זה כבר על אוקטובר** — אין צורך
לחכות לחודש הבא.

**הבעיה המבנית שפתרתי כדי שזה בכלל אפשרי:** רשומת היעדרות לא שומרת
תאריך קלנדרי אמיתי — רק `day` (0–6, יום בשבוע) ו-`createdAt` (מתי
דווח, לא בהכרח היום שבו ההיעדרות בפועל). בניתי שחזור תאריך אמין
מהשניים האלה יחד עם `forNextWeek` (שהאפליקציה כבר קובעת אוטומטית
לפי `isReportForNextWeek()`), ובדקתי שהוא תואם בדיוק את ההיגיון
הקיים באפליקציה למקרה הגבול היחיד שבאמת דו-משמעי — דיווח על "היום"
אחרי שעת הנעילה.

הדוח: לשונית הגדרות ← כרטיס "דוח חודשי" ← בחירת חודש ← "הפק דוח" →
יומן מלא, שורה לכל מ"מ (תאריך, יום, שעה, כיתה, נעדר, ממלא מקום/איחוד),
עם כפתור העתקה (טקסט מופרד-טאבים, מתאים להדבקה לאקסל/שיטס).

הרצה: python tools/patch_monthreport.py [index.html]   ·   אידמפוטנטי.
"""
import io
import sys

PATH = sys.argv[1] if len(sys.argv) > 1 else 'index.html'

with io.open(PATH, encoding='utf-8') as f:
    src = f.read()

if u'buildMonthlyReport' in src:
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


# ------------------------------------------------------------ 1. ה-HTML
swap('monthly report card',
     u'''            <div class="card">
                <h2><span class="icon">🗑️</span> איפוס שבועי</h2>
                <p style="color: #666; margin-bottom: 15px;">מחיקת כל הנתונים והתחלה מחדש לשבוע הבא</p>
                <button class="btn btn-danger" onclick="resetWeek()">🔄 אפס את כל הנתונים</button>
            </div>''',
     u'''            <div class="card">
                <h2><span class="icon">🗑️</span> איפוס שבועי</h2>
                <p style="color: #666; margin-bottom: 15px;">מחיקת כל הנתונים והתחלה מחדש לשבוע הבא</p>
                <button class="btn btn-danger" onclick="resetWeek()">🔄 אפס את כל הנתונים</button>
            </div>

            <div class="card">
                <h2><span class="icon">📊</span> דוח חודשי — כל מילויי המקום</h2>
                <p style="color: #666; margin-bottom: 15px;">יומן מלא של כל מילויי המקום בחודש הנבחר. פועל גם על חודשים
                    שעברו — הנתונים נשמרים בארכיון השבועי האוטומטי, לא רק בשבוע הנוכחי.</p>
                <div id="monthly-report-picker"></div>
                <div id="monthly-report-result" style="margin-top:14px"></div>
            </div>''')

# -------------------------------------------------------------- 2. ה-JS
swap('monthly report JS',
     u'''        // Restore permanent/pinned absences from /permanentAbsences/''',
     u'''        /* ====================== דוח חודשי — כל מילויי המקום ======================
           24.10: רשומת היעדרות לא שומרת תאריך קלנדרי, רק day (0-6) ו-createdAt
           (מתי דווח — לא בהכרח היום שבו ההיעדרות בפועל). משחזרים תאריך אמיתי
           מהשילוב של שניהם + forNextWeek, שכבר נקבע אוטומטית בזמן השמירה
           (isReportForNextWeek). הנתונים ההיסטוריים יושבים ב-/archived/{weekKey}
           — הארכיון השבועי האוטומטי של email-service.js — ולא רק ב-/absences
           החי של השבוע הנוכחי. */
        const MONTH_NAMES_HE = ['ינואר','פברואר','מרץ','אפריל','מאי','יוני',
                                 'יולי','אוגוסט','ספטמבר','אוקטובר','נובמבר','דצמבר'];
        let monthlyReportYM = null;   // { year, month } — month הוא 1-12
        let monthlyReportText = '';   // הטקסט להעתקה, נבנה יחד עם הטבלה

        function reconstructAbsenceDate(a) {
            if (!a.createdAt || a.day === undefined || a.day === null) return null;
            const reported = new Date(a.createdAt);
            const dow = reported.getDay();
            let offset = (Number(a.day) - dow + 7) % 7;
            // המקרה הדו-משמעי היחיד: יום הדיווח עצמו, שעבר את שעת הנעילה —
            // ה-offset הטבעי יוצא 0 ("היום"), אבל forNextWeek אומר שזה בעוד שבוע
            if (offset === 0 && a.forNextWeek) offset = 7;
            const real = new Date(reported);
            real.setHours(0, 0, 0, 0);
            real.setDate(real.getDate() + offset);
            return real;
        }

        function renderMonthlyReportPicker() {
            const el = document.getElementById('monthly-report-picker');
            if (!el) return;
            if (!monthlyReportYM) {
                const now = new Date();
                monthlyReportYM = { year: now.getFullYear(), month: now.getMonth() + 1 };
            }
            const { year, month } = monthlyReportYM;
            el.innerHTML = `
                <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
                    <button type="button" class="btn btn-secondary btn-sm" onclick="shiftMonthlyReport(-1)">◀ חודש קודם</button>
                    <strong style="font-size:1.05rem;min-width:110px;text-align:center">${MONTH_NAMES_HE[month - 1]} ${year}</strong>
                    <button type="button" class="btn btn-secondary btn-sm" onclick="shiftMonthlyReport(1)">חודש הבא ▶</button>
                    <button type="button" class="btn btn-primary btn-sm" onclick="buildMonthlyReport()">📊 הפק דוח</button>
                </div>`;
        }

        function shiftMonthlyReport(delta) {
            if (!monthlyReportYM) renderMonthlyReportPicker();
            let { year, month } = monthlyReportYM;
            month += delta;
            if (month < 1) { month = 12; year--; }
            if (month > 12) { month = 1; year++; }
            monthlyReportYM = { year, month };
            renderMonthlyReportPicker();
            document.getElementById('monthly-report-result').innerHTML = '';
        }

        async function buildMonthlyReport() {
            const resEl = document.getElementById('monthly-report-result');
            if (!monthlyReportYM) renderMonthlyReportPicker();
            const { year, month } = monthlyReportYM;
            if (!isOnline || !database) {
                resEl.innerHTML = '<p style="color:#c62828">אין חיבור לרשת — הדוח צריך לקרוא גם נתוני עבר מהענן.</p>';
                return;
            }
            resEl.innerHTML = '<p>⏳ טוען נתונים...</p>';

            const [archSnap, liveSnap] = await Promise.all([
                database.ref('archived').once('value'),
                database.ref('absences').once('value')
            ]);

            const rows = [];
            const collect = (obj) => {
                if (!obj) return;
                Object.values(obj).forEach(a => {
                    const dt = reconstructAbsenceDate(a);
                    if (!dt || dt.getFullYear() !== year || dt.getMonth() + 1 !== month) return;
                    rows.push({ dt, a });
                });
            };
            const archived = archSnap.val();
            if (archived) Object.values(archived).forEach(wk => collect(wk && wk.absences));
            collect(liveSnap.val());

            rows.sort((x, y) => x.dt - y.dt ||
                SCHEDULE_HOUR_ORDER.indexOf(x.a.hour) - SCHEDULE_HOUR_ORDER.indexOf(y.a.hour));

            if (!rows.length) {
                resEl.innerHTML = `<p>אין נתוני מילוי מקום ל${MONTH_NAMES_HE[month - 1]} ${year}.</p>`;
                monthlyReportText = '';
                return;
            }

            const coverLabel = a => a.merged
                ? `איחוד (${mergedLabel(a)}) — ${a.substitute || '—'}`
                : (a.substitute || '❗ לא שובץ');

            const header = ['תאריך', 'יום', 'שעה', 'כיתה', 'נעדר', 'ממלא מקום', 'סיבה'];
            const lines = [header.join('\\t')];
            const tableRows = rows.map(({ dt, a }) => {
                const dd = String(dt.getDate()).padStart(2, '0');
                const mm = String(dt.getMonth() + 1).padStart(2, '0');
                const dateStr = `${dd}/${mm}`;
                const dayStr = dayNames[dt.getDay()] || '';
                const cover = coverLabel(a);
                lines.push([dateStr, dayStr, a.hour || '', a.classAtHour || '',
                    a.teacher || '', cover, a.reason || ''].join('\\t'));
                const reasonFull = (a.reason || '').replace(/"/g, '&quot;');
                const reasonShort = reasonFull.length > 40 ? reasonFull.slice(0, 40) + '…' : reasonFull;
                return `<tr><td>${dateStr}</td><td>${dayStr}</td><td>${a.hour || ''}</td>` +
                    `<td>${a.classAtHour || ''}</td><td>${a.teacher || ''}</td>` +
                    `<td>${cover}</td>` +
                    `<td style="max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${reasonFull}">${reasonShort}</td></tr>`;
            }).join('');
            monthlyReportText = `📊 דוח מילוי מקום — ${MONTH_NAMES_HE[month - 1]} ${year}\\n\\n` + lines.join('\\n');

            resEl.innerHTML = `
                <p style="margin:0 0 10px"><strong>${rows.length}</strong> מילויי מקום ב${MONTH_NAMES_HE[month - 1]} ${year}</p>
                <div style="overflow-x:auto">
                    <table style="width:100%;border-collapse:collapse;font-size:0.88rem">
                        <thead><tr style="background:#f0f2f5">
                            <th style="padding:6px 8px;text-align:right">תאריך</th>
                            <th style="padding:6px 8px;text-align:right">יום</th>
                            <th style="padding:6px 8px;text-align:right">שעה</th>
                            <th style="padding:6px 8px;text-align:right">כיתה</th>
                            <th style="padding:6px 8px;text-align:right">נעדר</th>
                            <th style="padding:6px 8px;text-align:right">ממלא מקום</th>
                            <th style="padding:6px 8px;text-align:right">סיבה</th>
                        </tr></thead>
                        <tbody>${tableRows}</tbody>
                    </table>
                </div>
                <button class="btn btn-primary btn-sm" style="margin-top:12px" onclick="copyOut(monthlyReportText)">📋 העתק דוח</button>`;
        }

        // Restore permanent/pinned absences from /permanentAbsences/''')

# ----------------------------- 3. לרנדר את הבורר בכניסה לדף הגדרות
swap('settings page hook',
     u'''            if (pageId === 'report') updateLockedNotice();''',
     u'''            if (pageId === 'report') updateLockedNotice();
            if (pageId === 'settings') renderMonthlyReportPicker();''')

with io.open(PATH, 'w', encoding='utf-8', newline='') as f:
    f.write(src)

print(u'✓ דוח חודשי הוטמע  (%d → %d תווים)' % (before, len(src)))
