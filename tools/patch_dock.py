# -*- coding: utf-8 -*-
"""החלון הצף מתכווץ בגלילה, עם כפתור הרחבה/הקטנה ידני."""
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


# ---------- כפתור ההרחבה/הקטנה ----------
sub(r'        <div class="top-bar">',
    '        <div class="top-bar">\n'
    '            <button id="dock-toggle" class="dock-toggle" onclick="toggleDock()"\n'
    '                    title="הקטן / הרחב את הסרגל" aria-label="הקטן או הרחב את הסרגל">⌃</button>',
    'כפתור הקטנה')

# ---------- לוגיקה ----------
sub(r'(?=        // ===== Schedule file upload & override)',
    """        /* ===== הסרגל הצף =====
           בגלילה למטה הוא מתכווץ מעצמו כדי לא לאכול חצי מסך בנייד, ובחזרה
           למעלה נפתח. כפתור ⌃/⌄ מאפשר לקבע מצב ידנית — הבחירה נשמרת,
           והיא גוברת על ההתנהגות האוטומטית עד שמבטלים אותה. */
        let dockManual = localStorage.getItem('dockState');   // 'compact' | 'full' | null

        function applyDock(compact) {
            const bar = document.querySelector('.top-bar');
            const btn = document.getElementById('dock-toggle');
            if (!bar) return;
            bar.classList.toggle('compact', compact);
            if (btn) {
                btn.textContent = compact ? '⌄' : '⌃';
                btn.title = compact ? 'הרחב את הסרגל' : 'הקטן את הסרגל';
            }
        }

        function dockAuto() {
            if (dockManual) return;                    // המשתמש קבע — לא נוגעים
            applyDock(window.scrollY > 120);
        }

        function toggleDock() {
            const bar = document.querySelector('.top-bar');
            const nowCompact = !bar.classList.contains('compact');
            dockManual = nowCompact ? 'compact' : 'full';
            localStorage.setItem('dockState', dockManual);
            applyDock(nowCompact);
        }

        // לחיצה ארוכה מחזירה לאוטומטי
        document.addEventListener('DOMContentLoaded', () => {
            const btn = document.getElementById('dock-toggle');
            if (btn) btn.addEventListener('dblclick', () => {
                dockManual = null;
                localStorage.removeItem('dockState');
                dockAuto();
            });
            if (dockManual) applyDock(dockManual === 'compact');
            else dockAuto();
        });
        window.addEventListener('scroll', dockAuto, { passive: true });

""", 'לוגיקת הסרגל')

CSS = """        .top-bar { transition: padding .22s ease, background .22s ease; position: relative; }
        .dock-toggle { position:absolute; top:6px; left:10px; z-index:3;
            background:rgba(255,255,255,0.08); color:#e8edf7;
            border:1px solid rgba(201,169,97,0.35); border-radius:8px;
            width:26px; height:22px; line-height:1; cursor:pointer; font-size:13px;
            padding:0; display:flex; align-items:center; justify-content:center; }
        .dock-toggle:hover { background:rgba(255,255,255,0.16); }

        .top-bar.compact { padding: 6px 10px 2px; }
        .top-bar.compact .day-selector { margin-bottom: 5px; }
        .top-bar.compact .nav-tabs { margin-bottom: 3px; gap: 5px; }
        .top-bar.compact .day-btn { padding: 3px 10px; font-size: 0.76rem; }
        .top-bar.compact .nav-tab { padding: 4px 10px; font-size: 0.78rem; }
        /* בנייד הסרגל תופס הכי הרבה — שם מכווצים גם את שורת הימים */
        @media (max-width: 620px) {
            .top-bar.compact .day-selector { display: none; }
            .top-bar.compact::after { content: 'הסרגל מוקטן — הקש ⌄ להרחבה';
                display:block; text-align:center; font-size:0.68rem;
                color:rgba(232,237,247,0.5); padding-bottom:3px; }
        }
    </style>"""
sub(r'    </style>', CSS, 'עיצוב הסרגל')

open(APP, 'w', encoding='utf-8').write(src)
print('\n%d תיקונים הוחלו. גודל: %d → %d תווים' % (n, before, len(src)))
