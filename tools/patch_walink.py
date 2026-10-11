# -*- coding: utf-8 -*-
"""
patch_walink.py — 11.10.2026

**"למה ההודעות בקישורים מגיעות חתוכות?"**

האבחנה: הקישור שנשלח לשמשון בווטסאפ **שלם** — בדקתי את ההיסטוריה
ב-Green API, ה-URL מגיע במלואו (462–989 תווים). החיתוך קורה **אצל
ווטסאפ**, כשהוא מזהה איפה הקישור נגמר.

הסיבה: `encodeURIComponent` לא מקודד את התווים `! ' ( ) * ~`.
ההודעות שלנו מלאות בסוגריים — "היום (יום שני)", "(במקום הרב בישמוט)",
"(הרב שלומי נעדר)" — ומזהה-הקישורים של ווטסאפ **עוצר בסוגר הסוגר**,
כי `)` נחשב לפיסוק ולא לחלק מכתובת. לכן הלחיצה פתחה הודעה שנקטעה
בדיוק ב-"היום (יום שני".

התיקון: `waText()` שמקודד גם אותם ל-%28/%29 וכו׳, בכל חמשת המקומות
שבונים קישור wa.me.

הרצה: python tools/patch_walink.py [index.html]   ·   אידמפוטנטי.
"""
import io
import sys

PATH = sys.argv[1] if len(sys.argv) > 1 else 'index.html'

with io.open(PATH, encoding='utf-8') as f:
    src = f.read()

if u'function waText' in src:
    print(u'↻ כבר קיים — לא שונה דבר')
    raise SystemExit(0)

before = len(src)
applied = []


def swap(label, old, new, count=1):
    global src
    if old not in src:
        raise SystemExit(u'✗ %s: המקור לא נמצא' % label)
    if src.count(old) != count:
        raise SystemExit(u'✗ %s: %d התאמות, צפויות %d' % (label, src.count(old), count))
    src = src.replace(old, new)
    applied.append(u'%s ×%d' % (label, count))


# ------------------------------------------------------------ העוזר
swap('waText helper',
     u'''        // Format phone for WhatsApp link (0XX -> 972XX)
        function phoneToInternational(phone) {
            return '972' + phone.substring(1);
        }''',
     u'''        // Format phone for WhatsApp link (0XX -> 972XX)
        function phoneToInternational(phone) {
            return '972' + phone.substring(1);
        }

        /* ===== למה ההודעות הגיעו חתוכות =====
           `encodeURIComponent` משאיר כמו שהם את `! ' ( ) * ~`.
           ההודעות שלנו מלאות בסוגריים — "היום (יום שני)", "(במקום הרב
           בישמוט)" — ומזהה-הקישורים של ווטסאפ **עוצר בסוגר הסוגר**,
           כי `)` נחשב פיסוק ולא חלק מכתובת. התוצאה: הלחיצה פתחה הודעה
           שנקטעה בדיוק שם, למרות שהקישור עצמו נשלח שלם.
           ⚠️ כל בניית קישור wa.me חייבת לעבור כאן, לא ב-encodeURIComponent. */
        function waText(s) {
            return encodeURIComponent(s || '')
                .replace(/[!'()*~]/g, c => '%' + c.charCodeAt(0).toString(16).toUpperCase());
        }''')

# ------------------------------------------- חמשת בוני הקישורים
swap('getContactLink',
     u'''            const encoded = encodeURIComponent(message || '');
            if (contact.method === 'whatsapp') {
                return `https://wa.me/${phoneToInternational(contact.phone)}?text=${encoded}`;''',
     u'''            const encoded = encodeURIComponent(message || '');
            if (contact.method === 'whatsapp') {
                return `https://wa.me/${phoneToInternational(contact.phone)}?text=${waText(message)}`;''')

swap('sendWaLinkToAdmin',
     u'''            const waLink = `https://wa.me/${phoneToInternational(phone)}?text=${encodeURIComponent(message)}`;''',
     u'''            const waLink = `https://wa.me/${phoneToInternational(phone)}?text=${waText(message)}`;''')

swap('mass-send modal',
     u'''<a href="https://wa.me/${phoneToInternational(t.phone)}?text=${encodeURIComponent(t.message)}" target="_blank" class="contact-btn contact-whatsapp" title="שלח ווטסאפ">💬</a>''',
     u'''<a href="https://wa.me/${phoneToInternational(t.phone)}?text=${waText(t.message)}" target="_blank" class="contact-btn contact-whatsapp" title="שלח ווטסאפ">💬</a>''')

swap('sendAllWhatsApp',
     u'''                    const waUrl = `https://wa.me/${phoneToInternational(t.phone)}?text=${encodeURIComponent(t.message)}`;''',
     u'''                    const waUrl = `https://wa.me/${phoneToInternational(t.phone)}?text=${waText(t.message)}`;''')

swap('yard links',
     u'''                    ? `https://wa.me/${phoneToInternational(c.phone)}?text=${encodeURIComponent(it.msg)}`''',
     u'''                    ? `https://wa.me/${phoneToInternational(c.phone)}?text=${waText(it.msg)}`''')

with io.open(PATH, 'w', encoding='utf-8', newline='') as f:
    f.write(src)

print(u'✓ הוחלו: %d' % len(applied))
for a in applied:
    print(u'   · %s' % a)
print(u'  %d → %d תווים' % (before, len(src)))
