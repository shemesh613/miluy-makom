# -*- coding: utf-8 -*-
"""Replicates miluy-makom's parseScheduleRows / parseMechanechRows in Python,
so the תשפ"ז timetable can be baked into index.html as the built-in schedule."""
import io, sys, re, json
import openpyxl

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

XLSX = r"C:\Users\user\AppData\Local\Temp\claude\C--Users-user\a8680844-0fb9-46e3-9fe1-90977275f04e\scratchpad\files2\19fd6d6d22751ce6__מערכת תשפז למלמדים.xlsx"

ALIASES = {'הרב שימשון': 'הרב שמשון'}
CLASS_TOKEN = re.compile(r'^[א-ח][12]?$')
HOUR_ORDER = ['בוקר', '4', '5', '6', '7', '8', '9', '10', 'סדר ערב']


def norm(n):
    t = str(n).strip()
    return ALIASES.get(t, t)


def extract_class(cell):
    for tok in re.split(r'[\s,/|]+', str(cell)):
        if CLASS_TOKEN.match(tok):
            return tok
    return None


def sheet_rows(ws):
    rows = []
    for r in ws.iter_rows(values_only=True):
        rows.append(['' if c is None else str(c).strip() for c in r])
    return rows


# פעילויות שאינן שיעור עם כיתה. השעה נחשבת תפוסה (המלמד לא פנוי למילוי מקום),
# אבל אסור לשייך לה כיתה — "י. מחנכים" היא ישיבת מחנכים, לא שיעור.
NON_CLASS = {'י. מחנכים', 'ישיבת מחנכים', 'י.מחנכים'}


def parse_schedule(rows):
    header_rows = [i for i, r in enumerate(rows) if any(c == 'ראשון' for c in r)]
    if not header_rows:
        raise SystemExit('לא נמצאה שורת ימים')
    acc = {}
    for si, hr in enumerate(header_rows):
        blocks = []
        for c, cell in enumerate(rows[hr]):
            if cell == 'ראשון':
                prev = rows[hr - 1] if hr - 1 >= 0 else []
                name = norm(prev[c - 1] if c - 1 < len(prev) else '')
                if name:
                    blocks.append((c - 1, name))
        end = header_rows[si + 1] - 1 if si + 1 < len(header_rows) else len(rows)
        for col, name in blocks:
            a = acc.setdefault(name, {'dayHours': {}, 'hourClasses': {}, 'meetings': set()})
            for i in range(hr + 1, end):
                row = rows[i] if i < len(rows) else []
                raw = row[col] if col < len(row) else ''
                try:
                    hour_num = int(float(raw))
                except (ValueError, TypeError):
                    continue
                if hour_num < 1 or hour_num > 12:
                    continue
                for d in range(6):
                    idx = col + 1 + d
                    cell = row[idx] if idx < len(row) else ''
                    if not cell:
                        continue
                    label = 'בוקר' if hour_num <= 3 else (str(hour_num) if hour_num <= 10 else None)
                    if label is None:
                        continue
                    a['dayHours'].setdefault(d, set()).add(label)
                    if cell in NON_CLASS:
                        a['meetings'].add((d, label))
                        continue
                    cls = extract_class(cell)
                    if cls:
                        hc = a['hourClasses'].setdefault(d, {})
                        hc.setdefault(label, cls)
    out = {}
    for name, data in acc.items():
        days = sorted(data['dayHours'])
        if not days:
            continue
        day_hours, day_classes = {}, {}
        for d in days:
            day_hours[d] = sorted(data['dayHours'][d], key=HOUR_ORDER.index)
            bases = {c.replace('1', '').replace('2', '') for c in data['hourClasses'].get(d, {}).values()}
            day_classes[d] = sorted(bases)
        out[name] = {'days': days, 'dayHours': day_hours, 'dayClasses': day_classes,
                     'hourClasses': data['hourClasses'],
                     'meetings': sorted('%s|%s' % m for m in data['meetings'])}
    return out


def resolve(raw, known):
    if raw in known:
        return raw
    m = [k for k in known if raw in k or k in raw]
    return m[0] if len(m) == 1 else raw


def parse_mechanech(rows, known):
    mech = {}
    for i, r in enumerate(rows):
        if not any(c == 'ראשון' for c in r):
            continue
        for c, cell in enumerate(r):
            if cell == 'ראשון':
                prev = rows[i - 1] if i - 1 >= 0 else []
                header = (prev[c - 1] if c - 1 < len(prev) else '').strip()
                m = re.match(r'^([א-ח][12]?)\s+(.+)$', header)
                if m:
                    mech[m.group(1)] = resolve(norm(m.group(2)), known)
    return mech


wb = openpyxl.load_workbook(XLSX, data_only=True)
print('גיליונות:', wb.sheetnames)
t_sheet = next((n for n in wb.sheetnames if 'מלמדים' in n), wb.sheetnames[-1])
c_sheet = next((n for n in wb.sheetnames if 'כתות' in n or 'כיתות' in n), None)

t_rows = sheet_rows(wb[t_sheet])
parsed = parse_schedule(t_rows)
mech = parse_mechanech(sheet_rows(wb[c_sheet]), list(parsed)) if c_sheet else {}
mech['ו2'] = 'הרב משה'          # בקובץ רשום "משה" בלבד — התאמה חד-משמעית

# מחנך שהתא שלו מכיל רק את שם המקצוע ("ב\"מ", "ברכות", "מחנך", "קב\"ש") מלמד
# את כיתתו שלו. בלי ההשלמה הזו מחנכי ז/ח יוצאים בלי אף כיתה.
own = {t: c for c, t in mech.items()}
filled = 0
for name, t in parsed.items():
    cls = own.get(name)
    if not cls:
        continue
    meets = set(t['meetings'])
    for d in t['days']:
        hc = t['hourClasses'].setdefault(d, {})
        for h in t['dayHours'][d]:
            if h not in hc and '%s|%s' % (d, h) not in meets:
                hc[h] = cls
                filled += 1
        t['dayClasses'][d] = sorted({c.replace('1', '').replace('2', '')
                                     for c in hc.values()})
print('הושלמו %d משבצות של מחנכים לפי כיתתם' % filled)

total = sum(len(h) for t in parsed.values() for h in t['dayHours'].values())
print('גיליון מלמדים: %s | גיליון כיתות: %s' % (t_sheet, c_sheet))
print('מורים: %d | משבצות שבועיות: %d | מחנכים: %d' % (len(parsed), total, len(mech)))
print()
for n in sorted(parsed, key=lambda x: -sum(len(h) for h in parsed[x]['dayHours'].values())):
    print('  %-24s %2d ש"ש  ימים %s' % (
        n, sum(len(h) for h in parsed[n]['dayHours'].values()), parsed[n]['days']))
print()
print('מחנכים:', json.dumps(mech, ensure_ascii=False))

json.dump({'teachers': parsed, 'mechanech': mech},
          open('tashpaz_parsed.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
