# -*- coding: utf-8 -*-
"""מחליף את נתוני תשפ"ו בתשפ"ז ומוסיף את מודול תורנות החצר ל-index.html."""
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

APP = 'miluy-makom/index.html'
src = open(APP, encoding='utf-8').read()
orig_len = len(src)

blocks = open('blocks.js', encoding='utf-8').read()
B = {}
for part in blocks.split('/*')[1:]:
    tag, body = part.split('*/', 1)
    B[tag] = body.rstrip('\n')

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


# ---------- 1. נתוני המערכת ----------
sub(r'        const parallelClasses = \{.*?\n        \};', B['PC'], 'parallelClasses')
sub(r'        const classNames = \[[^\]]*\];', B['CN'], 'classNames')
sub(r'        const classesWithParallel = \[[^\]]*\];', B['CWP'], 'classesWithParallel')
sub(r'        const classMechanech = \{.*?\n        \};', B['CM'], 'classMechanech')
sub(r'        const allTeachers = \[.*?\n        \];', B['AT'], 'allTeachers')
sub(r'        const teacherSchedule = \{.*?\n        \};', B['TS'], 'teacherSchedule')
sub(r'        const dayHourClassesData = \{.*?\n        \};', B['DHC'], 'dayHourClassesData')

# ---------- 2. פרטי קשר ----------
CONTACTS = """        const teacherContacts = {
            'הרב אבי': { phone: '0546640059', method: 'whatsapp', email: 'avibenhaim74@gmail.com' },
            'הרב אלי': { phone: '0539614048', method: 'sms', email: 'eliben9943@gmail.com' },
            'הרב אליהו שמשון': { phone: '0504131511', method: 'call', email: 'eliyahushim12@gmail.com' },
            'הרב אורי פ.': { phone: '0527638269', method: 'call', email: 'uriprans@gmail.com' },
            'הרב בישמוט': { phone: '0527157890', method: 'call', email: 'y0527157890@gmail.com' },
            'הרב בני': { phone: '0523502280', method: 'whatsapp', email: 'benyaminaltman@gmail.com' },
            'הרב דוד': { phone: '0525793572', method: 'whatsapp', email: 'davidschwartzbaum32@gmail.com' },
            'הרב יובל': { phone: '0506731527', method: 'whatsapp', email: 'yuvalshoshani@gmail.com' },
            'הרב ינון': { phone: '0548422021', method: 'call', email: 'yinon3281@gmail.com' },
            'הרב יעקב': { phone: '0532212156', method: 'sms', email: 'yakovhdad@gmail.com' },
            'הרב מור': { phone: '0526410794', method: 'whatsapp', email: 'wmor74@gmail.com' },
            'הרב משה': { phone: '0526476608', method: 'sms', email: 'moshedavid.st@gmail.com' },
            'הרב נועם': { phone: '0542461346', method: 'whatsapp', email: 'noamkor1@gmail.com' },
            'הרב נריה': { phone: '0509919012', method: 'whatsapp', email: 'neriabsh@gmail.com' },
            'הרב סימון': { phone: '0584405828', method: 'sms', email: 'simonbenzion@gmail.com' },
            'הרב פורת': { phone: '0545965321', method: 'sms', email: 'poratyona@gmail.com' },
            'הרב צבי': { phone: '0503883660', method: 'whatsapp' },
            'הרב צביקה': { phone: '0527671159', method: 'call', email: 'zvi0527671159@gmail.com' },
            'הרב שלומי': { phone: '0543052239', method: 'sms' },
            'הרב שמואל': { phone: '0546390328', method: 'whatsapp', email: 'fischelsn@gmail.com' },
            'הרב שמשון': { phone: '0526953500', method: 'whatsapp', email: 'shemesh613@gmail.com' },
            'המורה שרה אליה': { phone: '0504100954', method: 'call', email: 's0504100954@gmail.com' },
            'שרה תורג\\'מן': { phone: '0548463377', method: 'call' },
            'לאה': { phone: '0538202498', method: 'call' },
            'חגית': { phone: '0548415819', method: 'call', email: 'chagitb1000@gmail.com' },
            // ⚠️ חדשים בתשפ"ז — חסרים פרטי קשר: הרב אביגדור, הרב חגי,
            //    הרב משה חיים נתן, המורה רבקי, הרב ליאור (סייע), הרב אורי אסייג (סייע).
            //    להוסיף כאן באותו פורמט וכפתורי הקשר יופיעו אוטומטית.
        };

        // מלמדים שאינם בתשפ"ז — נשמר כדי לא לאבד מספרים אם יחזרו
        const legacyContacts = {
            'הרב אופיר': { phone: '0548455189', method: 'whatsapp' },
            'הרב נהוראי': { phone: '0526583616', method: 'whatsapp' },
            'הרב ליאור אלקה': { phone: '0587148971', method: 'whatsapp', email: 'liorelka1@gmail.com' },
            'המורה זוהרה': { phone: '0527186621', method: 'call', email: 'zoara6621@gmail.com' },
        };"""
sub(r'        const teacherContacts = \{.*?\n        \};', CONTACTS, 'teacherContacts')

# ---------- 3. נתוני תורנות + מודול ----------
module = open('yard_module.js', encoding='utf-8').read()
YARD = ('\n        /* ---- נתוני תורנות החצר תשפ"ז (מתוך "תורנות חצר תשפז.xlsx") ---- */\n'
        + B['YD'] + '\n' + B['YS'] + '\n' + module + '\n')
sub(r'(?=        // ===== Schedule file upload & override)', YARD,
    'הזרקת מודול תורנות חצר')

# ---------- 4. שמירה על העדפת המערכת המובנית ----------
STAMP = """        // חותמת המערכת המובנית. override ישן יותר (תשפ"ו) מוזנח אוטומטית,
        // אחרת הוא היה דורס את מערכת תשפ"ז שמוטמעת כאן.
        const BUILTIN_SCHEDULE_STAMP = Date.parse('2026-08-07T00:00:00Z');
        const BUILTIN_SCHEDULE_YEAR = 'תשפ"ז';

        function isStaleOverride(o) {
            return !!o && (!o.updatedAt || o.updatedAt < BUILTIN_SCHEDULE_STAMP);
        }

        let activeScheduleInfo = null; // {fileName, updatedAt} when an override is active"""
sub(r'        let activeScheduleInfo = null; // \{fileName, updatedAt\} when an override is active',
    STAMP, 'חותמת מערכת מובנית')

sub(r"""            database\.ref\('scheduleOverride'\)\.on\('value', \(snapshot\) => \{
                const val = snapshot\.val\(\);""",
    """            database.ref('scheduleOverride').on('value', (snapshot) => {
                let val = snapshot.val();
                if (isStaleOverride(val)) {
                    console.warn('מתעלם ממערכת ישנה שהועלתה בעבר — עוברים למערכת תשפ"ז המובנית');
                    database.ref('scheduleOverride').remove();
                    val = null;
                }""", 'התעלמות מ-override ישן (Firebase)')

sub(r"""            const cachedOverride = localStorage\.getItem\('scheduleOverride'\);
            if \(cachedOverride\) \{
                try \{ applyScheduleOverride\(JSON\.parse\(cachedOverride\)\); \} catch \(e\) \{ console\.error\('Bad cached scheduleOverride', e\); \}
            \}""",
    """            yardSwapsData = JSON.parse(localStorage.getItem('yardSwaps') || '{}');
            const cachedOverride = localStorage.getItem('scheduleOverride');
            if (cachedOverride) {
                try {
                    const parsed = JSON.parse(cachedOverride);
                    if (isStaleOverride(parsed)) localStorage.removeItem('scheduleOverride');
                    else applyScheduleOverride(parsed);
                } catch (e) { console.error('Bad cached scheduleOverride', e); }
            }""", 'התעלמות מ-override ישן (localStorage)')

# ---------- 5. מאזין Firebase לחילופי תורנות ----------
sub(r"""            database\.ref\('tripExemptions'\)\.on\('value', \(snapshot\) => \{""",
    """            database.ref('yardSwaps').on('value', (snapshot) => {
                const raw = snapshot.val() || {};
                yardSwapsData = {};
                Object.entries(raw).forEach(([k, v]) => {
                    const real = Object.keys(YARD_DUTY).find(d => d.replace(/[.#$/\\[\\]]/g, '_') === k) || k;
                    yardSwapsData[real] = v;
                });
                updateYardDuty();
            });

            database.ref('tripExemptions').on('value', (snapshot) => {""",
    'מאזין yardSwaps')

# ---------- 6. חיבור לרענון התצוגות ----------
sub(r'            updateHonorBoard\(\);\n        \}\n\n        // Update trip notice',
    '            updateHonorBoard();\n            updateYardDuty();\n        }\n\n        // Update trip notice',
    'updateAllViews → updateYardDuty')

# ---------- 7. ממשק ----------
sub(r'                <button class="nav-tab" data-page="suggestions">📖 הנחיות</button>',
    '                <button class="nav-tab" data-page="yard">🏫 תורנות חצר '
    '<span id="yard-badge" class="yard-badge" style="display:none"></span></button>\n'
    '                <button class="nav-tab" data-page="suggestions">📖 הנחיות</button>',
    'לשונית תורנות חצר')

PAGE = """        <!-- Yard duty page -->
        <div id="page-yard" class="page">
            <div class="card">
                <h2><span class="icon">🏫</span> תורנות חצר — יום <span id="yard-day-name"></span></h2>
                <p style="color:#6e7482; margin:6px 0 14px;">
                    מלמד שדווח כנעדר מוחלף אוטומטית במי שפנוי באותה הפסקה, והוא מחזיר לו
                    תורנות בהמשך השבוע. כשאין אף מחליף פנוי — ממלא המקום של השיעור לוקח.
                </p>
                <div id="yard-duty-list"></div>
                <div style="margin-top:14px; display:flex; gap:8px; flex-wrap:wrap;">
                    <button class="btn btn-primary" onclick="yardCopyText()">📋 העתק שינויים לפרסום</button>
                </div>
            </div>
        </div>

        <div id="page-suggestions" class="page">"""
sub(r'        <div id="page-suggestions" class="page">', PAGE, 'עמוד תורנות חצר')

CSS = """        .yard-badge { background:#c62828; color:#fff; border-radius:10px; padding:0 6px;
            font-size:0.72rem; min-width:18px; height:18px; align-items:center;
            justify-content:center; display:inline-flex; margin-inline-start:4px; }
        .yard-summary { display:flex; gap:16px; flex-wrap:wrap; padding:10px 14px; margin-bottom:12px;
            background:#f5f7fa; border-radius:12px; font-size:0.95rem; }
        .yard-good { color:#2e7d5b; } .yard-warn { color:#c62828; }
        .yard-table { display:flex; flex-direction:column; gap:8px; }
        .yard-row { display:grid; grid-template-columns:82px 1fr 1.6fr auto; gap:10px;
            align-items:center; padding:10px 12px; border-radius:12px; border:1px solid #e4e7ec; }
        .yard-row-ok { background:#fbfcfd; }
        .yard-row-need { background:#fff8f4; border-color:rgba(198,40,40,0.28); }
        .yard-slot { display:flex; flex-direction:column; line-height:1.25; }
        .yard-slot small { color:#8a9099; font-size:0.72rem; }
        .yard-post { color:#5a6069; font-size:0.9rem; }
        .yard-absent { color:#c62828; text-decoration:line-through; font-size:0.9rem; }
        .yard-cover { margin-top:2px; }
        .yard-repay { margin-top:4px; font-size:0.82rem; color:#2e5d7d; }
        .yard-repay-none { color:#b26a00; }
        .yard-status { display:flex; flex-direction:column; gap:6px; align-items:flex-end; }
        .yard-actions { display:flex; gap:4px; flex-wrap:wrap; justify-content:flex-end; }
        .yard-pill { font-size:0.72rem; padding:2px 8px; border-radius:999px; white-space:nowrap; }
        .yard-pill-ok { background:#e8f3ed; color:#2e7d5b; }
        .yard-pill-auto { background:#e7f0fa; color:#1565c0; }
        .yard-pill-manual { background:#efeafa; color:#5b3fa0; }
        .yard-pill-fallback { background:#fdf3e0; color:#b26a00; }
        .yard-pill-open { background:#fdecec; color:#c62828; }
        @media (max-width:620px) {
            .yard-row { grid-template-columns:66px 1fr; grid-auto-rows:min-content; }
            .yard-post { grid-column:2; } .yard-who, .yard-status { grid-column:1 / -1; }
            .yard-status { align-items:flex-start; }
        }
    </style>"""
sub(r'    </style>', CSS, 'עיצוב תורנות חצר')

open(APP, 'w', encoding='utf-8').write(src)
print('\n%d תיקונים הוחלו. גודל: %d → %d תווים' % (n, orig_len, len(src)))
