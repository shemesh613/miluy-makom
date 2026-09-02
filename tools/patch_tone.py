# -*- coding: utf-8 -*-
"""ניסוח ההודעות למלמדים: ענייני ומכבד, לא מתחנן.

הכלל: שיבוץ שכבר נקבע נמסר כעובדה ולא כבקשה ("היום בשעה 5 מילוי מקום בב1"),
פנייה פתוחה נשארת בקשה רכה אחת. סוגרים ב"תודה" אחד — לא "תודה רבה!" ולא
"נודה לך מאוד". בלי סימני קריאה.
"""
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

APP = 'miluy-makom/index.html'
src = open(APP, encoding='utf-8').read()
before = len(src)
n = 0


def rep(old, new, label):
    global src, n
    if old not in src:
        print('!! לא נמצא: %s' % label)
        sys.exit(1)
    src = src.replace(old, new, 1)
    n += 1
    print('  ✓ %s' % label)


# --- פנייה כללית (עוד לא שובץ — זו באמת בקשה) ---
rep("`שלום ${teacher}, האם תוכל בבקשה למלא מקום היום (יום ${dayNames[currentDay]})? תודה רבה!`",
    "`${teacher}, שלום. מחפש מילוי מקום להיום (יום ${dayNames[currentDay]}). אם אתה פנוי — עדכן אותי בבקשה. תודה רבה.`",
    'פנייה כללית')

rep("`שלום ${t.name}, האם תוכל בבקשה למלא מקום היום (יום ${dayNames[currentDay]})? אשלח פרטים מדויקים בהמשך. תודה רבה!`",
    "`${t.name}, שלום. מחפש מילוי מקום להיום (יום ${dayNames[currentDay]}). אם אתה פנוי — עדכן אותי בבקשה ואשלח פרטים. תודה רבה.`",
    'פנייה כללית (רשימת פנויים)')

rep("`שלום ${teacher}, האם תוכל בבקשה למלא מקום היום (יום ${dayNames[currentDay]}) ב${slotsText}? נודה לך מאוד! תודה רבה!`",
    "`${teacher}, שלום. יש מילוי מקום להיום (יום ${dayNames[currentDay]}) ב${slotsText}. בבקשה עדכן אותי אם זה מסתדר. תודה רבה.`",
    'פנייה עם שעות')

# --- שיבוצים שכבר נקבעו — נמסרים כעובדה ---
rep("`שלום ${a.substitute}, האם תוכל בבקשה למלא מקום ביום ${dayNames[currentDay]} בשעה ${hourDisplay}${classAtHour ? ' בכיתה ' + classAtHour : ''}? תודה רבה!`",
    "`${a.substitute}, שלום. ביום ${dayNames[currentDay]} בשעה ${hourDisplay}${classAtHour ? ' בכיתה ' + classAtHour : ''} — מילוי מקום בבקשה. תודה רבה.`",
    'שיבוץ שנקבע')

rep("`שלום ${teacher}, האם תוכל בבקשה למלא מקום ביום ${dayNames[currentDay]} בשעה ${hour}${classAtHour ? ' בכיתה ' + classAtHour : ''}? תודה רבה!`",
    "`${teacher}, שלום. ביום ${dayNames[currentDay]} בשעה ${hour}${classAtHour ? ' בכיתה ' + classAtHour : ''} — מילוי מקום בבקשה. תודה רבה.`",
    'שיבוץ ישיר')

# --- איחודי כיתות ---
rep("`שלום ${r.host}, ${m.teacher} נעדר ב${h}. כיתות ${r.hostClasses.join(' + ')} יושבות יחד אצלך בכיתה ${r.where}. תודה רבה!`",
    "`${r.host}, שלום. ${m.teacher} נעדר ב${h}, וכיתות ${r.hostClasses.join(' + ')} יושבות יחד אצלך בכיתה ${r.where} בבקשה. תודה רבה.`",
    'איחוד — מאחד')

rep("`שלום ${r.mover}, ${m.teacher} נעדר ב${h}. הכיתה שלך מתאחדת, ואתה מתפנה לכיתה ${r.moverTo}. תודה רבה!`",
    "`${r.mover}, שלום. ${m.teacher} נעדר ב${h}. הכיתה שלך מתאחדת, ואתה עובר בבקשה לכיתה ${r.moverTo}. תודה רבה.`",
    'איחוד — עובר')

for tag, old, new in [
    ('איחוד מאושר — מלמד מאוחדת',
     "`שלום ${a.substitute}, היום (יום ${dayNames[currentDay]}) בשעה ${hourDisplay} מאחדים את כיתות ${subsLabel} (${a.teacher} נעדר) — אתה מלמד את הכיתה המאוחדת. תודה רבה!`",
     "`${a.substitute}, שלום. היום (יום ${dayNames[currentDay]}) בשעה ${hourDisplay} כיתות ${subsLabel} יושבות יחד אצלך (${a.teacher} נעדר). תודה.`"),
    ('איחוד מאושר — עובר',
     "`שלום ${a.substitute}, היום (יום ${dayNames[currentDay]}) בשעה ${hourDisplay} כיתות ${subsLabel} מאוחדות${a.stayingTeacher ? ' אצל ' + a.stayingTeacher : ''}, ואתה עובר ללמד את כיתה ${absentCls} (במקום ${a.teacher}). תודה רבה!`",
     "`${a.substitute}, שלום. היום (יום ${dayNames[currentDay]}) בשעה ${hourDisplay} כיתות ${subsLabel} יושבות יחד${a.stayingTeacher ? ' אצל ' + a.stayingTeacher : ''}, ואתה עובר לכיתה ${absentCls} (במקום ${a.teacher}). תודה.`"),
    ('איחוד מאושר — נשאר',
     "`שלום ${a.stayingTeacher}, היום (יום ${dayNames[currentDay]}) בשעה ${hourDisplay} כיתות ${subsLabel} מאוחדות אצלך — אתה מלמד את הכיתה המאוחדת. תודה רבה!`",
     "`${a.stayingTeacher}, שלום. היום (יום ${dayNames[currentDay]}) בשעה ${hourDisplay} כיתות ${subsLabel} יושבות יחד אצלך. תודה.`"),
    ('איחוד (תצוגה) — מלמד מאוחדת',
     "`שלום ${coverTeacher}, היום (יום ${dayNames[currentDay]}) בשעה ${hourDisplay} מאחדים את כיתות ${subsLabel} (${a.teacher} נעדר) — אתה מלמד את הכיתה המאוחדת. תודה רבה!`",
     "`${coverTeacher}, שלום. היום (יום ${dayNames[currentDay]}) בשעה ${hourDisplay} כיתות ${subsLabel} יושבות יחד אצלך (${a.teacher} נעדר). תודה.`"),
    ('איחוד (תצוגה) — עובר',
     "`שלום ${coverTeacher}, היום (יום ${dayNames[currentDay]}) בשעה ${hourDisplay} כיתות ${subsLabel} מאוחדות${stayTeacher ? ' אצל ' + stayTeacher : ''}, ואתה עובר ללמד את כיתה ${absentClass} (במקום ${a.teacher}). תודה רבה!`",
     "`${coverTeacher}, שלום. היום (יום ${dayNames[currentDay]}) בשעה ${hourDisplay} כיתות ${subsLabel} יושבות יחד${stayTeacher ? ' אצל ' + stayTeacher : ''}, ואתה עובר לכיתה ${absentClass} (במקום ${a.teacher}). תודה.`"),
    ('איחוד (תצוגה) — נשאר',
     "`שלום ${stayTeacher}, היום (יום ${dayNames[currentDay]}) בשעה ${hourDisplay} כיתות ${subsLabel} מאוחדות אצלך — אתה מלמד את הכיתה המאוחדת. תודה רבה!`",
     "`${stayTeacher}, שלום. היום (יום ${dayNames[currentDay]}) בשעה ${hourDisplay} כיתות ${subsLabel} יושבות יחד אצלך. תודה.`"),
]:
    rep(old, new, tag)

# --- טיולים ---
rep("`שלום ${t.name}, ${t.transferredFrom ? `בעקבות היעדרות של ${t.transferredFrom} והטיול היום` : 'הכיתה שלך בטיול היום'} (יום ${dayNames[currentDay]}) שובצת למילוי מקום: ${details}. תודה רבה!`",
    "`${t.name}, שלום. ${t.transferredFrom ? `${t.transferredFrom} נעדר והכיתה בטיול` : 'הכיתה שלך בטיול'} היום (יום ${dayNames[currentDay]}), ולכן שובצת למילוי מקום: ${details}. תודה.`",
    'טיול — שיבוץ מפורט')

rep("`שלום ${t.name}, ${t.transferredFrom ? `אתה מחליף היום את ${t.transferredFrom} והכיתה שלו בטיול` : 'הכיתה שלך בטיול היום'} (יום ${dayNames[currentDay]}), ולכן עליך למלא מקום בשעות ${freeHours.join(', ')}. פרטי השיבוץ המדויקים יישלחו בהמשך. תודה רבה!`",
    "`${t.name}, שלום. ${t.transferredFrom ? `אתה מחליף היום את ${t.transferredFrom}, והכיתה שלו בטיול` : 'הכיתה שלך בטיול היום'} (יום ${dayNames[currentDay]}), ולכן יש לך מילוי מקום בשעות ${freeHours.join(', ')}. הפרטים המדויקים יישלחו בהמשך. תודה.`",
    'טיול — שיבוץ כללי')

# --- תורנות חצר ---
rep("`שלום ${p.cover || ''}, ${p.toran} נעדר היום ולכן התורנות של ${p.slot} ב${p.post} עוברת אליך. תודה רבה!`",
    "`${p.cover || ''}, שלום. ${p.toran} נעדר היום, ולכן תורנות ${p.slot} ב${p.post} עוברת אליך. תודה.`",
    'תורנות חצר')

open(APP, 'w', encoding='utf-8').write(src)
print('\n%d הודעות נוסחו מחדש. גודל: %d → %d תווים' % (n, before, len(src)))
