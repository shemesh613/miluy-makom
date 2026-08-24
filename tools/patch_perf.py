# -*- coding: utf-8 -*-
"""האצת הטעינה: ביטול קריאת Twilio בעלייה, פחות משקלי גופן, ביטול 404 של favicon."""
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


# ---------- 1. הקריאה ל-Twilio בכל טעינה ----------
# 735ms, המשאב האיטי ביותר בדף, ורק כדי לבדוק את מספר הטלפון של החשבון.
# אין בזה שום צורך בעלייה — נשאר זמין לקריאה ידנית מהקונסול בעת הצורך.
sub(r'\n        checkTwilioSetup\(\);',
    '\n        // לא נקרא בעלייה — זו הייתה הבקשה האיטית ביותר בדף (735ms) ואין בה\n'
    '        // צורך לפני שליחה בפועל. להרצה ידנית: checkTwilioSetup() מהקונסול.',
    'ביטול קריאת Twilio בעלייה')

# ---------- 2. משקלי גופן ----------
# בשימוש בפועל: 300, 500, 600, 700, 900. הורדנו את מה שאינו בשימוש
# (Heebo 400 נטען כברירת מחדל ממילא) — פחות קבצי גופן בנייד.
sub(r'family=Frank\+Ruhl\+Libre:wght@500;700;900&family=Heebo:wght@300;400;500;600;700',
    'family=Frank+Ruhl+Libre:wght@700;900&family=Heebo:wght@400;600;700',
    'צמצום משקלי גופן')

# ---------- 3. favicon ----------
sub(r'    <link href="https://fonts\.googleapis\.com/css2',
    '    <link rel="icon" href="data:image/svg+xml,'
    '%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 16 16\'%3E'
    '%3Ctext y=\'14\' font-size=\'14\'%3E🔄%3C/text%3E%3C/svg%3E">\n'
    '    <link href="https://fonts.googleapis.com/css2',
    'favicon מוטמע (ביטול 404)')

open(APP, 'w', encoding='utf-8').write(src)
print('\n%d תיקונים הוחלו. גודל: %d → %d תווים' % (n, before, len(src)))
