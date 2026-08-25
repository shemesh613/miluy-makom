# -*- coding: utf-8 -*-
"""בורר יום בולט בטופס הדיווח + הסרת הכיתוב על 22:30 + סרגל לא צף."""
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


# ---------- 1. ביטול הכיתוב על 22:30 ----------
# ההתנהגות נשארת (נוח לסדר את מחר בערב), אבל ההסבר ירד — במקומו יש
# בורר יום מפורש בטופס הדיווח, ששם הבלבול באמת עלול לקרות.
sub(r"""            el\.innerHTML = onAuto
                \? `🌙 אחרי \$\{AUTO_NEXT_DAY_HOUR\}:\$\{String\(AUTO_NEXT_DAY_MIN\)\.padStart\(2, '0'\)\} — עברנו אוטומטית ל<strong>יום \$\{dayNames\[info\.day\]\}</strong> \(מחר\)\. כל דיווח יירשם ליום הזה\.`
                : `⚠️ אתה מציג את <strong>יום \$\{dayNames\[currentDay\]\}</strong>, אבל השעה כבר אחרי \$\{AUTO_NEXT_DAY_HOUR\}:\$\{String\(AUTO_NEXT_DAY_MIN\)\.padStart\(2, '0'\)\} — הדיווח הרגיל עכשיו הוא ל<strong>יום \$\{dayNames\[info\.day\]\}</strong>\. <button class="btn btn-sm" onclick="goToAutoDay\(\)">קפוץ ליום \$\{dayNames\[info\.day\]\}</button>`;""",
    """            el.style.display = 'none';        // הכיתוב בוטל — הבורר בטופס הדיווח מחליף אותו""",
    'ביטול הכיתוב על 22:30')

# ---------- 2. הסרגל לא צף ----------
sub(r'        /\* הסרגל הצף — גודל בינוני קבוע, ללא שינוי בגלילה \*/\n        \.top-bar \{ padding: 9px 13px 4px; \}',
    '        /* הסרגל — גודל בינוני קבוע, ואינו צף: נגלל עם הדף */\n'
    '        .top-bar { padding: 9px 13px 4px; position: static; }',
    'ביטול הציפה')

# ---------- 3. בורר יום בולט בטופס הדיווח ----------
sub(r'                <h2><span class="icon">📝</span> דיווח היעדרות חדשה</h2>',
    '                <h2><span class="icon">📝</span> דיווח היעדרות חדשה</h2>\n'
    '                <div id="report-day-picker" class="rdp"></div>',
    'מקום לבורר היום')

sub(r'(?=        // ===== Schedule file upload & override)',
    """        /* ===== על איזה יום מדווחים =====
           רוב הדיווחים נכנסים יום מראש: מי שמדווח בשלישי מתכוון בדרך כלל
           לרביעי. לכן היום שעליו מדווחים חייב להיות מוצג גדול ומפורש —
           עם תאריך, לא רק שם יום — ואפשר להחליף אותו במקום, בלי לחפש
           את בורר הימים למעלה. */
        function reportDayLabel(d) {
            const t = israelNow();
            const today = t.day;
            const rel = d === today ? 'היום' : (d === (today + 1) % 7 ? 'מחר' : '');
            // תאריך אמיתי לאותו יום בשבוע הקרוב
            const now = new Date();
            let diff = (d - now.getDay() + 7) % 7;
            const dt = new Date(now.getTime() + diff * 864e5);
            return { rel, date: `${dt.getDate()}/${dt.getMonth() + 1}` };
        }

        function renderReportDayPicker() {
            const el = document.getElementById('report-day-picker');
            if (!el) return;
            const t = israelNow();
            const opts = [t.day, (t.day + 1) % 7, (t.day + 2) % 7]
                .filter(d => d !== 6)                       // אין דיווח לשבת
                .filter((d, i, a) => a.indexOf(d) === i);
            const cur = reportDayLabel(currentDay);
            el.innerHTML = `
                <div class="rdp-head">מדווחים על היום הזה:</div>
                <div class="rdp-now">${dayNames[currentDay]}${cur.rel ? ` · ${cur.rel}` : ''}
                    <span class="rdp-date">${cur.date}</span></div>
                <div class="rdp-btns">${opts.map(d => {
                    const l = reportDayLabel(d);
                    return `<button type="button" class="rdp-btn${d === currentDay ? ' on' : ''}"
                        onclick="setReportDay(${d})">${dayNames[d]}${l.rel ? ` (${l.rel})` : ''}</button>`;
                }).join('')}</div>`;
        }

        function setReportDay(d) {
            currentDay = d;
            document.querySelectorAll('.day-btn').forEach(b =>
                b.classList.toggle('active', +b.dataset.day === d));
            renderReportDayPicker();
            if (typeof flashDay === 'function') flashDay();
            updateAllViews();
        }

""", 'בורר יום הדיווח')

# רענון הבורר בכל עדכון תצוגות
sub(r'            updateMissingContacts\(\);\n            populateReserveSelect\(\);',
    '            updateMissingContacts();\n'
    '            renderReportDayPicker();\n'
    '            populateReserveSelect();',
    'רענון הבורר')

# שם היום גם על כפתור השמירה
sub(r'                    <button class="btn btn-primary" id="save-btn" disabled>💾 שמור היעדרות</button>',
    '                    <button class="btn btn-primary" id="save-btn" disabled>💾 שמור היעדרות</button>',
    'כפתור שמירה (ללא שינוי מבני)')

sub(r"        function renderAutoDayNotice\(\) \{",
    """        function syncSaveBtnDay() {
            const b = document.getElementById('save-btn');
            if (b) b.textContent = `💾 שמור היעדרות ליום ${dayNames[currentDay]}`;
        }

        function renderAutoDayNotice() {""",
    'שם היום על כפתור השמירה')

sub(r'            renderReportDayPicker\(\);\n            populateReserveSelect\(\);',
    '            renderReportDayPicker();\n'
    '            syncSaveBtnDay();\n'
    '            populateReserveSelect();',
    'חיבור כפתור השמירה')

CSS = """        .rdp { background:rgba(21,101,192,0.06); border:1px solid rgba(21,101,192,0.3);
            border-radius:12px; padding:12px 14px; margin-bottom:16px; text-align:center; }
        .rdp-head { font-size:0.82rem; color:#5a6069; letter-spacing:.02em; }
        .rdp-now { font-size:1.45rem; font-weight:700; color:#1565c0; margin:2px 0 10px; }
        .rdp-date { font-size:0.9rem; font-weight:600; color:#6e7482; margin-inline-start:6px; }
        .rdp-btns { display:flex; gap:7px; flex-wrap:wrap; justify-content:center; }
        .rdp-btn { background:#fff; border:1px solid #cfd8e3; border-radius:999px;
            padding:6px 15px; font-size:0.88rem; font-family:inherit; cursor:pointer; color:#33415c; }
        .rdp-btn:hover { border-color:#1565c0; }
        .rdp-btn.on { background:#1565c0; border-color:#1565c0; color:#fff; font-weight:700; }
    </style>"""
sub(r'    </style>', CSS, 'עיצוב הבורר')

open(APP, 'w', encoding='utf-8').write(src)
print('\n%d תיקונים הוחלו. גודל: %d → %d תווים' % (n, before, len(src)))
