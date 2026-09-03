# -*- coding: utf-8 -*-
"""אחרי 22:30 המערכת עוברת אוטומטית ליום הבא, עם סימון בולט. רץ אחרון."""
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


# ---------- 1. חישוב היום הפעיל ----------
sub(r'        let currentDay = new Date\(\)\.getDay\(\); // 0=Sunday\n'
    r'        if \(currentDay === 6\) currentDay = 0; // If Saturday, show Sunday',
    """        /* ===== היום הפעיל =====
           אחרי 22:30 כבר לא מדווחים על היום שנגמר אלא על מחר, ולכן המערכת
           עוברת מעצמה ליום הבא. השעה נלקחת משעון ישראל ולא מהמכשיר, כדי
           שטלפון עם אזור זמן שגוי לא יזיז את היום.
           כדי שלא יקרו טעויות — המעבר תמיד מלווה בהודעה בולטת ובהבהוב. */
        const AUTO_NEXT_DAY_HOUR = 22, AUTO_NEXT_DAY_MIN = 30;

        function israelNow() {
            const f = new Intl.DateTimeFormat('en-GB', {
                timeZone: 'Asia/Jerusalem', hour12: false,
                weekday: 'short', hour: '2-digit', minute: '2-digit',
                day: '2-digit', month: '2-digit'
            });
            const p = Object.fromEntries(f.formatToParts(new Date()).map(x => [x.type, x.value]));
            return {
                day: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].indexOf(p.weekday),
                hour: parseInt(p.hour, 10), minute: parseInt(p.minute, 10),
                date: `${p.day}/${p.month}`,
            };
        }

        // מחזיר את היום שיש להציג, והאם הוא "מחר" ולא היום
        function activeDayInfo() {
            const t = israelNow();
            const past = t.hour > AUTO_NEXT_DAY_HOUR ||
                         (t.hour === AUTO_NEXT_DAY_HOUR && t.minute >= AUTO_NEXT_DAY_MIN);
            let day = t.day, advanced = false;
            if (past) { day = (day + 1) % 7; advanced = true; }
            if (day === 6) { day = 0; advanced = true; }   // שבת -> ראשון
            return { day, advanced, time: t };
        }

        let autoDayAdvanced = false;
        let currentDay = (() => {
            const info = activeDayInfo();
            autoDayAdvanced = info.advanced;
            return info.day;
        })();""",
    'חישוב היום הפעיל')

# ---------- 2. הודעה מעל בורר הימים ----------
sub(r'            <div class="day-selector">',
    '            <div id="auto-day-notice" class="auto-day-notice" style="display:none"></div>\n'
    '            <div class="day-selector">',
    'מקום להודעה')

# ---------- 3. סימון והבהוב ----------
sub(r"        document\.querySelector\(`\.day-btn\[data-day=\"\$\{currentDay\}\"\]`\)\.classList\.add\('active'\);",
    """        document.querySelector(`.day-btn[data-day="${currentDay}"]`).classList.add('active');
        renderAutoDayNotice();
        if (autoDayAdvanced) flashDay();

        // מציג במפורש על איזה יום עובדים — כדי שלא ידווחו על היום הלא נכון
        function renderAutoDayNotice() {
            const el = document.getElementById('auto-day-notice');
            if (!el) return;
            const info = activeDayInfo();
            if (!info.advanced) { el.style.display = 'none'; return; }
            const onAuto = currentDay === info.day;
            el.style.display = 'block';
            el.className = 'auto-day-notice' + (onAuto ? '' : ' off-auto');
            el.innerHTML = onAuto
                ? `🌙 אחרי ${AUTO_NEXT_DAY_HOUR}:${String(AUTO_NEXT_DAY_MIN).padStart(2, '0')} — עברנו אוטומטית ל<strong>יום ${dayNames[info.day]}</strong> (מחר). כל דיווח יירשם ליום הזה.`
                : `⚠️ אתה מציג את <strong>יום ${dayNames[currentDay]}</strong>, אבל השעה כבר אחרי ${AUTO_NEXT_DAY_HOUR}:${String(AUTO_NEXT_DAY_MIN).padStart(2, '0')} — הדיווח הרגיל עכשיו הוא ל<strong>יום ${dayNames[info.day]}</strong>. <button class="btn btn-sm" onclick="goToAutoDay()">קפוץ ליום ${dayNames[info.day]}</button>`;
        }

        function flashDay() {
            const btn = document.querySelector(`.day-btn[data-day="${currentDay}"]`);
            if (!btn) return;
            btn.classList.remove('day-flash');
            void btn.offsetWidth;               // מאתחל את האנימציה
            btn.classList.add('day-flash');
            setTimeout(() => btn.classList.remove('day-flash'), 4000);
        }

        function goToAutoDay() {
            const info = activeDayInfo();
            currentDay = info.day;
            document.querySelectorAll('.day-btn').forEach(b => b.classList.remove('active'));
            const btn = document.querySelector(`.day-btn[data-day="${currentDay}"]`);
            if (btn) btn.classList.add('active');
            renderAutoDayNotice();
            flashDay();
            updateAllViews();
        }""",
    'הודעה והבהוב')

# ---------- 4. עדכון ההודעה בכל החלפת יום ידנית ----------
sub(r"""                currentDay = parseInt\(this\.dataset\.day\);
                document\.querySelectorAll\('\.day-btn'\)\.forEach\(b => b\.classList\.remove\('active'\)\);""",
    """                currentDay = parseInt(this.dataset.day);
                setTimeout(renderAutoDayNotice, 0);
                document.querySelectorAll('.day-btn').forEach(b => b.classList.remove('active'));""",
    'רענון ההודעה בבחירה ידנית')

# ---------- 5. מעבר ליום הבא בכניסה לדיווח היעדרות ----------
sub(r"""                const pageId = this\.dataset\.page;""",
    """                const pageId = this.dataset.page;
                // בכניסה לדיווח היעדרות אחרי 22:30 — קופצים ליום שמדווחים עליו
                if (pageId === 'report') {
                    const info = activeDayInfo();
                    if (info.advanced && currentDay !== info.day) goToAutoDay();
                    else if (info.advanced) flashDay();
                }""",
    'קפיצה ליום הבא בדיווח')

CSS = """        .auto-day-notice { background:rgba(242,193,78,0.16); border:1px solid rgba(242,193,78,0.5);
            color:#7a5b12; border-radius:10px; padding:7px 12px; margin-bottom:8px;
            font-size:0.86rem; text-align:center; }
        .auto-day-notice.off-auto { background:rgba(255,107,107,0.14);
            border-color:rgba(255,107,107,0.5); color:#8c2f2f; }
        @media (prefers-color-scheme: dark) {
            .auto-day-notice { color:#f2d99a; }
            .auto-day-notice.off-auto { color:#ffb3b3; }
        }
        @keyframes dayFlash {
            0%,100% { box-shadow:0 0 0 0 rgba(242,193,78,0); }
            50%     { box-shadow:0 0 0 6px rgba(242,193,78,0.55); }
        }
        .day-btn.day-flash { animation: dayFlash 0.9s ease-in-out 4; }
    </style>"""
sub(r'    </style>', CSS, 'עיצוב')

open(APP, 'w', encoding='utf-8').write(src)
print('\n%d תיקונים הוחלו. גודל: %d → %d תווים' % (n, before, len(src)))
