# -*- coding: utf-8 -*-
"""מוסיף את מצב המילואים ל-index.html. רץ אחרי patch_app.py."""
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


# ---- המודול עצמו ----
module = open('reserve_module.js', encoding='utf-8').read()
sub(r'(?=        // ===== Schedule file upload & override)', module + '\n',
    'הזרקת מודול מילואים')

# ---- הצהרה מוקדמת: loadFromLocalStorage משתמש ב-reserveData ----
sub(r'        let yardSwapsData = \{\};      // dutyKey -> \{ cover, repay, mode, at \} — חילופי תורנות חצר',
    '        let yardSwapsData = {};      // dutyKey -> { cover, repay, mode, at } — חילופי תורנות חצר\n'
    '        let reserveData = {};        // מלמד -> { since, preferred, cover } — מצב מילואים',
    'הצהרת reserveData')

sub(r"            yardSwapsData = JSON\.parse\(localStorage\.getItem\('yardSwaps'\) \|\| '\{\}'\);",
    "            yardSwapsData = JSON.parse(localStorage.getItem('yardSwaps') || '{}');\n"
    "            reserveData = JSON.parse(localStorage.getItem('reserve') || '{}');",
    'טעינה מקומית')

# ---- סנכרון Firebase ----
sub(r"            database\.ref\('yardSwaps'\)\.on\('value', \(snapshot\) => \{",
    "            database.ref('reserve').on('value', (snapshot) => {\n"
    "                const raw = snapshot.val() || {};\n"
    "                reserveData = {};\n"
    "                Object.entries(raw).forEach(([k, v]) => {\n"
    "                    const real = allTeachers.find(t => t.replace(/[.#$/\\[\\]]/g, '_') === k) || k;\n"
    "                    reserveData[real] = v;\n"
    "                });\n"
    "                updateReserve();\n"
    "                updateAllViews();\n"
    "            });\n\n"
    "            database.ref('yardSwaps').on('value', (snapshot) => {",
    'מאזין Firebase')

# ---- רענון ----
sub(r'            updateMissingContacts\(\);\n        \}',
    '            updateMissingContacts();\n'
    '            populateReserveSelect();\n'
    '            updateReserve();\n        }',
    'חיבור לרענון התצוגות')

# ---- ממשק ----
PAGE = """        <!-- Reserve duty page -->
        <div id="page-reserve" class="page">
            <div class="card">
                <h2><span class="icon">🎖️</span> מצב מילואים</h2>
                <p style="color:#6e7482; margin:6px 0 14px;">
                    מזינים <strong>פעם אחת</strong> את ממלאי המקום הקבועים, והמערכת מחלקת ביניהם
                    בלבד — גם את השיעורים וגם את תורנויות החצר — לכל תקופת המילואים.
                    הזמינות נבדקת בפועל: משבצת שאף אחד מהם אינו יכול לקחת תסומן, יחד עם מי כן יכול.
                </p>
                <div style="display:flex; gap:8px; flex-wrap:wrap; align-items:center; margin-bottom:10px;">
                    <select id="reserve-teacher" style="padding:8px; border-radius:8px;"
                            onchange="populateReserveSelect()"></select>
                    <button class="btn btn-primary" onclick="reserveAdd()">➕ הכנס למילואים</button>
                </div>
                <div style="font-size:0.9rem; color:#6e7482; margin-bottom:6px;">
                    ממלאי המקום הקבועים לכל התקופה — סמן את כולם:
                </div>
                <div id="reserve-subs" class="res-picks"></div>
                <div id="reserve-list"></div>
            </div>
        </div>

        <div id="page-suggestions" class="page">"""
sub(r'        <div id="page-suggestions" class="page">', PAGE, 'עמוד מילואים')

sub(r'                <button class="nav-tab" data-page="yard">',
    '                <button class="nav-tab" data-page="reserve">🎖️ מילואים</button>\n'
    '                <button class="nav-tab" data-page="yard">',
    'לשונית מילואים')

CSS = """        .res-box { border:1px solid #e4e7ec; border-radius:12px; padding:14px; margin-bottom:14px; }
        .res-head { display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap; }
        .res-sum { display:flex; gap:14px; flex-wrap:wrap; margin:10px 0 6px; font-size:0.9rem; }
        .res-ok { color:#2e7d5b; } .res-none { color:#c62828; }
        .res-load { display:flex; gap:6px; flex-wrap:wrap; margin-bottom:10px; }
        .res-chip { background:#eef2f7; border-radius:999px; padding:2px 10px; font-size:0.82rem; }
        .res-over { background:#fdecec; color:#c62828; font-weight:600; }
        .res-tbl { width:100%; border-collapse:collapse; font-size:0.88rem; }
        .res-tbl th, .res-tbl td { border:1px solid #e4e7ec; padding:5px 8px; text-align:right; }
        .res-tbl th { background:rgba(128,128,128,0.08); }
        .res-tbl tr.res-gap td { background:#fff8f4; }
        .res-tbl select { width:100%; padding:3px; border-radius:6px; }
        .res-alt { font-size:0.78rem; color:#6e7482; margin-top:2px; }
        .res-picks { display:flex; flex-wrap:wrap; gap:6px; margin-bottom:14px; }
        .res-pick { display:inline-flex; align-items:center; gap:5px; background:#eef2f7;
            border-radius:8px; padding:4px 10px; font-size:0.86rem; cursor:pointer; }
        .muted { color:#8b93a0; }
    </style>"""
sub(r'    </style>', CSS, 'עיצוב מילואים')

open(APP, 'w', encoding='utf-8').write(src)
print('\n%d תיקוני מילואים הוחלו. גודל: %d → %d תווים' % (n, before, len(src)))
