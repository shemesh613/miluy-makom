# -*- coding: utf-8 -*-
"""בניית תורנות חצר תשפ"ז — תלמוד תורה מוריה"""
import json, io, os, sys, random
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
random.seed(11)

DAYS = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי']
# שתי העמדות. השמות שהיו בקובץ תשפ"ו ('מסדרון ונספחיו' / 'חצר') היו מבלבלים:
# בפועל *מסדרון ונספחיו = הדשא למטה*, ו*חצר = המגרש למעלה*. שונו לשמות האמיתיים.
POSTS = ['דשא (למטה)', 'מגרש (למעלה)']
DESHE, MIGRASH = POSTS

# חלון -> (שעה לפני, שעה אחרי), קבוצת גיל, ימים
SLOTS = [
    ('10:05', (3, 4), 'ד-ו', ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי']),
    ('10:20', (3, 4), 'א-ג', ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי']),
    ('11:20', (4, 5), 'ד-ו', ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי']),
    ('12:10', (5, 6), 'א-ג', ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי']),
    ('13:15', (6, 7), 'ד-ו', ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי']),
    ('13:30', (6, 7), 'א-ג', ['ראשון', 'שני', 'רביעי', 'חמישי']),
    ('15:15', (8, 9), 'ד-ו', ['ראשון', 'שני', 'רביעי', 'חמישי']),
]
MIN = {'10:05': 605, '10:20': 620, '11:20': 680, '12:10': 730, '13:15': 795, '13:30': 810, '15:15': 915}
SLOT_H = {s[0]: s[1] for s in SLOTS}
SLOT_G = {s[0]: s[2] for s in SLOTS}

data = json.load(open(os.environ.get('TASHPAZ', 'tashpaz.json'), encoding='utf-8'))
grid = data['teachers']
for t in list(grid):
    for h in list(grid[t]):
        if not h.replace('.', '').isdigit():
            del grid[t][h]

# ---------------- כיתה -> קבוצת גיל.  ז/ח אינן משתתפות כלל
YOUNG = {'א', 'א1', 'א2', 'ב', 'ב1', 'ב2', 'ג', 'ג1', 'ג2'}
OLDER = {'ד', 'ד1', 'ד2', 'ה', 'ה1', 'ה2', 'ו', 'ו1', 'ו2'}
NOPART = {'ז', 'ח'}

# פעילויות שאינן שיעור בכיתה (נוספו בעדכון 14.8).
# ⚠ הן *אינן* חוסמות תורנות. הסיבה: כלל קבוצת הגיל קיים רק בגלל *איפה הילדים*.
# ב-10:20 כיתות ד-ו אוכלות ארוחת בוקר בכיתה עם המלמד שלהן — ולכן מי שמלמד
# ד/ה/ו בשעה 4 תקוע איתן. בהדרכה אין ילדים: המלמד פנוי בהפסקה, וב-10:35
# הולך להדרכה. לכן מתייחסים לתא כזה כמו שעה פנויה — נוכח בביה"ס, לא חוסם.
NONCLASS = {'הדרכה', 'גנים', 'ישיבה', 'פגישה', 'קב"ש', 'קבש'}

HOMEROOM = {  # מחנך -> הכיתה שלו
    'הרב שלומי': 'א1', 'הרב יובל': 'א2', 'הרב אביגדור': 'ב1', 'הרב בישמוט': 'ב2',
    'הרב צבי': 'ג1', 'הרב שמשון': 'ג2', 'הרב אלי': 'ד', 'הרב נריה': 'ה1',
    'הרב נועם': 'ה2', 'הרב ינון': 'ו1', 'הרב משה': 'ו2', 'הרב אבי': 'ז', 'הרב יעקב': 'ח',
}
# מחנכי ז/ח – לא משתתפים בתורנות כלל
EXCLUDE = {'הרב אבי', 'הרב יעקב'}


def cls_of(cell, teacher):
    """הכיתה שהמלמד מלמד בתא הזה (או כיתת החינוך שלו אם אין ציון)."""
    if not cell:
        return None
    tok = cell.split()[-1]
    if tok and tok[0] in 'אבגדהוזח' and len(tok) <= 2 and (tok in YOUNG or tok in OLDER or tok in NOPART):
        return tok
    return HOMEROOM.get(teacher)


def group_of(cls):
    if cls in YOUNG:
        return 'א-ג'
    if cls in OLDER:
        return 'ד-ו'
    if cls in NOPART:
        return 'ז-ח'
    return None


ASSIST = ['הרב ליאור (סייע)', 'הרב אורי אסייג (סייע)']
for a in ASSIST:
    grid[a] = {}

# ---------------- טווח הנוכחות של כל מלמד בכל יום
span = {}
for t, g in grid.items():
    for d in DAYS:
        hrs = [float(h) for h, row in g.items() if row.get(d, '')]
        span[(t, d)] = (min(hrs), max(hrs)) if hrs else None

WH = {t: sum(1 for h in g for d in DAYS if g[h].get(d, '')) for t, g in grid.items()}
for a in ASSIST:
    WH[a] = 40          # סייע – נמצא כל היום, נושא עומס כמו מלמד מלא

C = {
 'הרב צבי':        dict(off=['ראשון'], late={'שני': 730, 'שלישי': 975, 'רביעי': 930, 'חמישי': 930},
                        only_slots=['10:20'], no_post=[MIGRASH],
                        days_only=['שלישי', 'רביעי', 'חמישי', 'שישי'], maxd=4,
                        group_ok=['10:20'], late_ok=['10:20'],
                        src='טופס (פעמיים): "תורנות חצר ב-10:20 בדשא שלישי עד ששי" — '
                            'מלמד אנגלית לד-ו בשעה 4, ביקש בכל זאת'),
 'הרב בישמוט':     dict(late={'חמישי': 795}, ban=['13:15', '13:30'], no_post=[MIGRASH],
                        src='רק בדשא, לא בזמן מנחה'),
 'הרב שמואל':      dict(days_only=['ראשון', 'שלישי', 'חמישי'], ban=['13:15', '13:30'],
                        no_post=[MIGRASH], src='בעיות עיניים: לא במגרש, לא במנחה'),
 'הרב נריה':       dict(off=['חמישי'], only_slots=['11:20'], late_ok=['11:20'],
                        src='טופס: "תורנות חצר לא בהפסקת הבוקר, ממש עדיף בהפסקה של 11:20"'),
 'הרב אורי פ.':    dict(only_slots=['11:20', '12:10', '15:15', '10:05'],
                        days_only=['ראשון', 'שלישי', 'חמישי', 'שישי'],
                        early_ok={'10:05': ['שישי']}, maxd=5,
                        extra_days={'ראשון': (4, 9)},
                        src='מייל 6.8: "מוכן לקחת כמה הפסקות כל שבוע" · לא מנחה, לא בימי הספורט של רב דוד'),
 'הרב יובל':       dict(late={'רביעי': 630}, ban=['13:15', '13:30'], src='ד׳ עד 10:30; לא במנחה ביום ארוך'),
 'הרב מור':        dict(days_only=['ראשון'], early={'ראשון': 840}, maxd=1, src='א׳ מ-14:00, שאר הימים מ-16:15'),
 'המורה רבקי':     dict(days_only=['ראשון', 'רביעי'], src='רק א׳ ו-ד׳'),
 'הרב פורת':       dict(days_only=['ראשון', 'רביעי'], ban=['13:15', '13:30'], src='א׳+ד׳ עד 15:15, לא במנחה'),
 'הרב  אליהו שמשון': dict(early={d: 690 for d in DAYS}, src='פנוי מ-11:30'),
 'הרב חגי':        dict(days_only=['ראשון', 'שלישי', 'חמישי'], src='מלמד רק א׳ ג׳ ה׳'),
 'לאה':            dict(off=['שלישי'], src='ג׳ יום חופשי'),
 'הרב נועם':       dict(off=['רביעי'], src='ד׳ חופשי'),
 'הרב בני':        dict(early={d: 620 for d in DAYS}, src='מתחיל 10:30'),
 'הרב שמשון':      dict(days_only=['ראשון', 'שישי'], late={d: 700 for d in DAYS},
                        src='נשאר רק ביום ראשון (שעה 4 טבע) ובשישי — שאר הימים הולך אחרי שעה 3'),
 'חגית':           dict(ban=['15:15'], src='משרת אם – לא סוף יום'),
 'הרב משה':        dict(maxd=1, hard=True, no_reg_days=['שישי'],
                        src='מנהל – תורנות אחת בלבד + שער סוף יום שישי (לא בוקר שישי)'),
 'הרב דוד':        dict(days_only=['שני', 'רביעי'], maxd=2, src='מורה להתעמלות'),
 'הרב סימון':      dict(early={d: 900 for d in DAYS}, src='זמין מאוחר / סדר ערב'),
 'שרה תורג\'מן':   dict(late={d: 840 for d in DAYS}, flex=1, maxd=1,
                        src='עד 14:00 · תורנות אחת בשבוע, צמוד לשיעור שהיא מלמדת'),
}
for a in ASSIST:
    C[a] = dict(off=['שישי'], maxd=6, hard=True, src='סייע – לא עובד בשישי')
for a in ASSIST:
    C[a]['ban'] = ['10:05', '10:20']
    C[a]['src'] = 'סייע – לא בשישי, ולא מגיע בבוקר'
# הסייעים נושאים יותר מהמלמדים (זה התפקיד שלהם, והמלמדים עובדים קשה),
# אבל שווים ביניהם ולא יותר מ-5.
for a in ASSIST:
    C[a]['maxd'] = 5
C['הרב צביקה'] = dict(flex=2, maxd=3,
                      src='אמרת: זורם — משובץ איפה שחסר, עד שעתיים מעבר לשעותיו')
DEFAULT_MAX = 3
MAXCAP = int(os.environ.get('MAXCAP', 4))   # תקרה קשיחה — לא להעמיס על אף אחד


def cap(t):
    """תקרת תורנויות — פרופורציונלית לשעות ההוראה השבועיות"""
    if 'maxd' in C.get(t, {}):
        return C[t]['maxd']
    return max(1, min(MAXCAP, round(WH.get(t, 0) / 6.0)))


def can(t, day, slot, post):
    if t in EXCLUDE:
        return False
    c = C.get(t, {})
    if day in c.get('off', []):
        return False
    if 'days_only' in c and day not in c['days_only']:
        return False
    if slot in c.get('ban', []):
        return False
    if 'only_slots' in c and slot not in c['only_slots']:
        return False
    if post in c.get('no_post', []):
        return False
    if post != 'שער' and day in c.get('no_reg_days', []):
        return False
    m = MIN[slot]
    if m > c.get('late', {}).get(day, 10 ** 9) or m < c.get('early', {}).get(day, 0):
        return False

    h1, h2 = SLOT_H[slot]
    grp = SLOT_G[slot]
    if t in ASSIST:                       # סייעים – ללא מערכת שעות, זמינים כל היום
        return True

    sp = c.get('extra_days', {}).get(day) or span.get((t, day))
    if sp is None:                        # ← אין לו שום שיעור ביום הזה = לא בבית הספר
        return False

    # ===== כלל ברזל =====
    # אסור לשבץ מלמד מחוץ לשעות ההוראה שלו — לא להגיע מוקדם ולא להישאר אחרי —
    # אלא אם הוא אישר זאת במפורש *לגבי תורנות*. "אפשר להתחיל מוקדם" בטופס
    # מתייחס להוראה ואינו אישור לתורנות.
    def allowed(key):
        v = c.get(key, [])
        if isinstance(v, dict):
            return day in v.get(slot, [])
        return slot in v

    fl = c.get('flex', 0)
    if h1 < sp[0] - fl and not allowed('early_ok'):
        return False
    if h2 > sp[1] + fl and not allowed('late_ok'):
        return False

    if post == 'שער':                     # שער סוף יום – בלי מגבלת קבוצת גיל
        return True

    # בשתי השעות הצמודות: או שהוא פנוי, או שהוא עם כיתה מאותה קבוצת גיל
    # (ואז הילדים שלו יוצאים להפסקה איתו). אם הוא עם קבוצת הגיל השנייה –
    # השיעור שלהם עדיין רץ והוא לא זמין.  'הדרכה'/'גנים' = תפוס לגמרי.
    if slot in c.get('group_ok', []):     # ביקש את המשבצת הזו במפורש
        return True
    for h in (h1, h2):
        cell = grid[t].get(str(int(h)), {}).get(day, '') or grid[t].get(str(h), {}).get(day, '')
        if not cell or cell.strip() in NONCLASS:
            continue                  # אין ילדים בשעה הזו — לא חוסם
        if group_of(cls_of(cell, t)) != grp:
            return False
    return True


slots = [(sl, day, post) for sl, _, _, days in SLOTS for day in days for post in POSTS]
count = defaultdict(int)
per_day = defaultdict(set)
assign = {}

FIXED = {
    ('10:20', 'שלישי', DESHE): 'הרב צבי',
    ('10:20', 'רביעי', DESHE): 'הרב צבי',
    ('10:20', 'חמישי', DESHE): 'הרב צבי',
    ('10:20', 'שישי', DESHE): 'הרב צבי',
    ('11:20', 'שלישי', MIGRASH): 'הרב אורי פ.',
    ('11:20', 'חמישי', DESHE): 'הרב אורי פ.',
    # שרה תורג'מן – אחת בשבוע, מיד אחרי השיעור שהיא מלמדת.
    # בעדכון 14.8 עברית ב1 עברה מראשון שעה 5 ל*חמישי* שעה 5 — התורנות זזה איתה.
    ('12:10', 'חמישי', DESHE): "שרה תורג'מן",
}
for k, v in FIXED.items():
    assign[k] = v
    count[v] += 1
    per_day[v].add(k[1])

POOL = [t for t in grid if t not in EXCLUDE]

if __name__ == '__main__' or os.environ.get('RUN_SCHED'):
    open_slots = [s for s in slots if s not in assign]
    for _ in range(len(open_slots)):
        best, cands = None, None
        for s in open_slots:
            sl, day, post = s
            used = {assign[k] for k in assign if k[0] == sl and k[1] == day}
            c = [t for t in POOL if t not in used and can(t, day, sl, post)
                 and count[t] < cap(t) and day not in per_day[t]]
            if best is None or len(c) < len(cands):
                best, cands = s, c
        if best is None:
            break
        if not cands:
            # הרפיה מדורגת. "תורנות אחת ליום" זו העדפה, לא כלל — מרפים אותה קודם.
            sl, day, post = best
            used = {assign[k] for k in assign if k[0] == sl and k[1] == day}
            base = [t for t in POOL if t not in used and can(t, day, sl, post)]
            for extra in (0, 1):
                cands = [t for t in base
                         if count[t] < cap(t) + (0 if C.get(t, {}).get('hard') else extra)]
                if cands:
                    break
        if not cands:
            assign[best] = '— לא שובץ —'
            open_slots.remove(best)
            continue
        cands.sort(key=lambda t: (count[t] / cap(t), count[t], random.random()))
        t = cands[0]
        assign[best] = t
        count[t] += 1
        per_day[t].add(best[1])
        open_slots.remove(best)

GATE = [('ראשון', '15:15'), ('שני', '15:15'), ('שלישי', '13:15'),
        ('רביעי', '15:15'), ('חמישי', '15:15'), ('שישי', 'סוף יום')]
gate = {('שישי', 'סוף יום'): 'הרב משה'}

if __name__ == '__main__' or os.environ.get('RUN_SCHED'):
    for day, sl in GATE:
        if (day, sl) in gate:
            continue
        used = {assign[k] for k in assign if k[1] == day and k[0] == sl} | set(gate.values())
        c = [t for t in POOL if t not in used and day not in per_day[t]
             and can(t, day, sl, 'שער') and count[t] < cap(t)]
        if not c:
            base = [t for t in POOL if t not in used and can(t, day, sl, 'שער')]
            for extra in (0, 1):
                c = [t for t in base
                     if count[t] < cap(t) + (0 if C.get(t, {}).get('hard') else extra)]
                if c:
                    break
        if not c:
            gate[(day, sl)] = '— לא שובץ —'
            continue
        c.sort(key=lambda t: (count[t] / cap(t), count[t], random.random()))
        gate[(day, sl)] = c[0]
        count[c[0]] += 1
        per_day[c[0]].add(day)


def would_fit(t, day, slot, post):
    """עומד בכל הכללים חוץ מהכלל שאסור לחרוג משעות ההוראה"""
    c = C.get(t, {})
    sp = span.get((t, day))
    if sp is None or t in EXCLUDE or t in ASSIST:
        return None
    c2 = dict(c); c2['early_ok'] = list(MIN); c2['late_ok'] = list(MIN)
    C[t] = c2
    ok = can(t, day, slot, post)
    C[t] = c
    if not ok:
        return None
    h1, h2 = SLOT_H[slot]
    if h1 < sp[0]:
        return 'להגיע %g שיעורים מוקדם (שיעור ראשון שלו: %g)' % (sp[0] - h1, sp[0])
    if h2 > sp[1]:
        return 'להישאר %g שיעורים אחרי (שיעור אחרון שלו: %g)' % (h2 - sp[1], sp[1])
    return None


if __name__ == '__main__':
    json.dump({'%s|%s|%s' % k: v for k, v in assign.items()},
              open('assign.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump({'%s|%s' % k: v for k, v in gate.items()},
              open('gate.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for sl, (h1, h2), grp, days in SLOTS:
        print('\n%s  (בין %s ל-%s)   קבוצה: %s' % (sl, h1, h2, grp))
        for post in POSTS:
            line = ['%s: %s' % (d, assign.get((sl, d, post), '—')) if d in days else '%s: ✗' % d for d in DAYS]
            print('   %-16s %s' % (post, '  |  '.join(line)))
    print('\n=== עומס ===')
    for t in sorted(POOL, key=lambda x: (-WH.get(x, 0))):
        print('%-22s %5d %6d %6d' % (t, WH.get(t, 0), cap(t), count[t]))
    print('לא שובצו:', sum(1 for v in assign.values() if v.startswith('—')))
