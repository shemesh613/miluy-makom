# -*- coding: utf-8 -*-
"""לכל תורנות: רשימת מחליפים מדורגת + לאיזו תורנות הנעדר מחזיר לכל אחד מהם.
מייצא subs_full.json לשילוב במערכת מילוי המקום."""
import io, os, sys, json, random, importlib.util
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
os.environ.setdefault('MAXCAP', '4')
random.seed(23)

spec = importlib.util.spec_from_file_location('bt', 'build_toranut.py')
bt = importlib.util.module_from_spec(spec)
_r, _s = sys.stdout, open('_buildlog.txt', 'w', encoding='utf-8')
sys.stdout = _s
try:
    spec.loader.exec_module(bt)
finally:
    sys.stdout = _r
    _s.close()

DAYS, POOL = bt.DAYS, bt.POOL

# ---------------------------------------------------------------------------
# הלוח המפורסם הוא מקור האמת — לא בונים אותו מחדש.
# build_toranut משמש כאן רק לכללי הכשירות (can / span / אילוצים), שמחושבים
# מקובץ המערכת העדכני. בנייה מחדש הייתה מטלטלת את כל הלוח בגלל כמה שיעורים
# שזזו, והלוח כבר חולק למלמדים.
# ---------------------------------------------------------------------------
pub_assign = json.load(open('assign.json', encoding='utf-8'))
pub_gate = json.load(open('gate.json', encoding='utf-8'))

ALL = {tuple(k.split('|')): v for k, v in pub_assign.items()}
for k, v in pub_gate.items():
    d, tm = k.split('|')
    ALL[(tm, d, 'שער')] = v
print('נטען הלוח המפורסם: %d משבצות + %d שער' % (len(pub_assign), len(pub_gate)))

# כמה הלוח המפורסם שונה מבנייה טרייה — אינפורמטיבי בלבד
fresh = {'%s|%s|%s' % k: v for k, v in bt.assign.items()}
drift = [k for k in set(fresh) | set(pub_assign) if fresh.get(k) != pub_assign.get(k)]
if drift:
    print('  (בנייה טרייה הייתה משנה %d משבצות — לא נוגעים בלוח המפורסם)' % len(drift))

duties = defaultdict(list)
for k, w in ALL.items():
    duties[w].append(k)

busy_at = defaultdict(set)
for (tm, d, post), w in ALL.items():
    busy_at[(tm, d)].add(w)


def feasible(t, key):
    """אותם כללי ברזל של בניית התורנות — שעות נוכחות, אילוצים, התאמת גיל."""
    tm, d, post = key
    if tm not in bt.MIN:                      # שער סוף יום שישי
        c = bt.C.get(t, {})
        if d in c.get('off', []):
            return False
        if 'days_only' in c and d not in c['days_only']:
            return False
        if t in bt.ASSIST:
            return False
        return bt.span.get((t, d)) is not None
    return bt.can(t, d, tm, post)


def repay_options(absentee, sub, skip_day):
    """אילו תורנויות של המחליף הנעדר יכול לקחת במקומו בהמשך השבוע"""
    return ['%s|%s|%s' % k for k in duties[sub]
            if k[1] != skip_day and feasible(absentee, k)]


# הבדיקה שבאמת חשובה: האם כל תורנות בלוח המפורסם עדיין חוקית לפי המערכת
# החדשה. זה מה שתופס תורן שהשיעור שלו זז ועכשיו הוא בכלל לא בבית הספר.
illegal = [(k, w) for k, w in ALL.items() if not feasible(w, k)]
if illegal:
    print('\n⚠️  %d תורנויות בלוח המפורסם אינן חוקיות לפי המערכת החדשה:' % len(illegal))
    for (tm, d, post), w in illegal:
        print('   %s %s %s — %s' % (d, tm, post, w))
else:
    print('✓ כל התורנויות בלוח המפורסם חוקיות לפי המערכת החדשה')

N_CANDS = 5
sub_count = defaultdict(int)
out = {}

for key in sorted(ALL, key=lambda k: (DAYS.index(k[1]), k[0], k[2])):
    T = ALL[key]
    tm, d, post = key
    cands = [c for c in POOL
             if c != T and c not in busy_at[(tm, d)] and feasible(c, key)]
    scored = []
    for c in cands:
        reps = repay_options(T, c, d)
        scored.append((0 if reps else 1,       # עדיפות למי שאפשר להחזיר לו
                       sub_count[c],            # לפזר את תפקיד המחליף
                       len(duties[c]),          # מי שעמוס פחות
                       random.random(), c, reps))
    scored.sort()
    chosen = scored[:N_CANDS]
    if chosen:
        sub_count[chosen[0][4]] += 1
    out['%s|%s|%s' % key] = {
        'toran': T,
        'cands': [{'name': c, 'repay': reps} for *_, c, reps in chosen],
    }

json.dump(out, open('subs_full.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

nosub = [k for k, v in out.items() if not v['cands']]
norep = [k for k, v in out.items() if v['cands'] and not v['cands'][0]['repay']]
print('סה"כ תורנויות: %d' % len(out))
print('בלי שום מחליף אפשרי: %d %s' % (len(nosub), nosub or ''))
print('עם מחליף אך בלי החזר אפשרי (מועמד ראשון): %d' % len(norep))
for k in norep:
    print('   %s — תורן %s, מחליף %s' % (k, out[k]['toran'], out[k]['cands'][0]['name']))
avg = sum(len(v['cands']) for v in out.values()) / len(out)
print('ממוצע מועמדים לתורנות: %.2f' % avg)
print('\nפיזור תפקיד המחליף (מועמד ראשון):')
for c in sorted(sub_count, key=lambda x: -sub_count[x]):
    print('   %-24s %d' % (c, sub_count[c]))
