# -*- coding: utf-8 -*-
"""מייצר את בלוקי ה-JS של תשפ"ז להזרקה ל-index.html של מילוי מקום."""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

P = json.load(open('tashpaz_parsed.json', encoding='utf-8'))
teachers, mech = P['teachers'], P['mechanech']
T_DIR = 'toranut/'
assign = json.load(open(T_DIR + 'assign.json', encoding='utf-8'))
gate = json.load(open(T_DIR + 'gate.json', encoding='utf-8'))
subs = json.load(open(T_DIR + 'subs_full.json', encoding='utf-8'))

ASSIST = ['הרב ליאור (סייע)', 'הרב אורי אסייג (סייע)']

# בקבצי המקור יש שמות עם רווח כפול ("הרב  אליהו שמשון"). מנרמלים בכל מקום,
# אחרת השם לא יתאים בין המערכת, התורנות ופרטי הקשר.
import re as _re
NM = lambda s: _re.sub(r'\s+', ' ', str(s)).strip()
teachers = {NM(k): v for k, v in teachers.items()}
mech = {k: NM(v) for k, v in mech.items()}
assign = {k: NM(v) for k, v in assign.items()}
gate = {k: NM(v) for k, v in gate.items()}
subs = {k: {'toran': NM(v['toran']),
            'cands': [{'name': NM(c['name']), 'repay': c['repay']} for c in v['cands']]}
        for k, v in subs.items()}
HOUR_ORDER = ['בוקר', '4', '5', '6', '7', '8', '9', '10', 'סדר ערב']

roster = sorted(set(teachers) | set(ASSIST), key=lambda s: s.strip())


def q(s):
    return "'" + str(s).replace('\\', '\\\\').replace("'", "\\'") + "'"


def jarr(xs):
    return '[' + ','.join(q(x) for x in xs) + ']'


# ---------- teacherSchedule ----------
lines = ['        const teacherSchedule = {']
for n in roster:
    t = teachers.get(n)
    if not t:   # סייעים — אין להם מערכת שעות, אך הם חלק מהצוות
        lines.append('            %s: { days: [], dayHours: {}, dayClasses: {}, assistant: true },' % q(n))
        continue
    dh = ', '.join('%s: %s' % (d, jarr(t['dayHours'][str(d)] if str(d) in t['dayHours'] else t['dayHours'].get(d, [])))
                   for d in t['days'])
    dc = ', '.join('%s: %s' % (d, jarr(t['dayClasses'][str(d)] if str(d) in t['dayClasses'] else t['dayClasses'].get(d, [])))
                   for d in t['days'])
    lines.append('            %s: { days: %s, dayHours: { %s }, dayClasses: { %s } },'
                 % (q(n), json.dumps(t['days']), dh, dc))
lines.append('        };')
TS = '\n'.join(lines)

# ---------- dayHourClassesData ----------
lines = ['        const dayHourClassesData = {']
for n in roster:
    t = teachers.get(n)
    if not t:
        continue
    parts = []
    for d in t['days']:
        hc = t['hourClasses'].get(str(d), t['hourClasses'].get(d, {}))
        if not hc:
            continue
        inner = ', '.join('%s:%s' % (q(h), q(hc[h]))
                          for h in sorted(hc, key=HOUR_ORDER.index))
        parts.append('%s: {%s}' % (d, inner))
    lines.append('            %s: {%s},' % (q(n), ', '.join(parts)))
lines.append('        };')
DHC = '\n'.join(lines)

# ---------- classMechanech ----------
CM = '        const classMechanech = {\n' + '\n'.join(
    '            %s: %s,' % (q(k), q(v)) for k, v in mech.items()) + '\n        };'

# ---------- allTeachers ----------
AT = '        const allTeachers = [\n' + '\n'.join(
    '            ' + ', '.join(q(x) for x in roster[i:i + 4]) + ','
    for i in range(0, len(roster), 4)).rstrip(',') + '\n        ];'

# ---------- class structure ----------
bases = {}
for c in mech:
    bases.setdefault(c[0], []).append(c)
PC = '        const parallelClasses = {\n' + '\n'.join(
    '            %s: %s,' % (q(b), jarr(sorted(v)) if len(v) > 1 else 'null')
    for b, v in bases.items()) + '\n        };'
CN = '        const classNames = %s;' % jarr(sorted(bases))
CWP = '        const classesWithParallel = %s;' % jarr(
    sorted(b for b, v in bases.items() if len(v) > 1))

# ---------- yard duty ----------
YD = '        const YARD_DUTY = ' + json.dumps(
    {**assign, **{'%s|%s|שער' % (tm, d): w
                  for k, w in gate.items() for d, tm in [k.split('|')]}},
    ensure_ascii=False, indent=0).replace('\n', ' ') + ';'
YS = '        const YARD_SUBS = ' + json.dumps(subs, ensure_ascii=False, separators=(',', ':')) + ';'

open('blocks.js', 'w', encoding='utf-8').write(
    '\n\n'.join(['/*PC*/' + PC, '/*CN*/' + CN, '/*CWP*/' + CWP, '/*CM*/' + CM,
                 '/*AT*/' + AT, '/*TS*/' + TS, '/*DHC*/' + DHC,
                 '/*YD*/' + YD, '/*YS*/' + YS]))

print('roster (%d):' % len(roster))
for n in roster:
    print('   ', n, '' if n in teachers else '(סייע — ללא מערכת שעות)')
print('\nמחנכים:', json.dumps(mech, ensure_ascii=False))
print('כיתות:', json.dumps(bases, ensure_ascii=False))
print('תורנויות:', len(assign) + len(gate), '| מפת מחליפים:', len(subs))
print('גדלים: TS=%dB DHC=%dB YD=%dB YS=%dB' % (len(TS), len(DHC), len(YD), len(YS)))
