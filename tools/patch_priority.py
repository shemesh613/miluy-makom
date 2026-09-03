# -*- coding: utf-8 -*-
"""עדיפות למילוי מקום בשעות חלון. רץ אחרי patch_partial.py."""
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


HELPERS = """        /* ===== עדיפות למילוי מקום בשעות חלון =====
           שעת חלון = שעה פנויה שנמצאת *בין* השיעורים של אותו יום, כלומר
           המלמד ודאי בבניין. זה שונה משעה פנויה לפני היום שלו או אחריו,
           שבה הוא כנראה בכלל לא כאן. מי שברשימה יוצג ראשון בשעות כאלה. */
        const WINDOW_PRIORITY_SUBS = ['הרב אליהו שמשון'];

        function windowHours(teacher, day) {
            const order = ['בוקר', '4', '5', '6', '7', '8', '9', '10', 'סדר ערב'];
            const t = teacherSchedule[teacher];
            if (!t || !(t.days || []).includes(day)) return [];
            const taught = (t.dayHours[day] || []).map(h => order.indexOf(h)).filter(i => i >= 0);
            if (taught.length < 2) return [];      // בלי שני עוגנים אין "בין"
            const lo = Math.min(...taught), hi = Math.max(...taught);
            return order.filter((h, i) => i > lo && i < hi && !(t.dayHours[day] || []).includes(h));
        }

"""
sub(r'(?=        // Update available teachers\n        function updateAvailableTeachers)',
    HELPERS, 'עזרי שעות חלון')

# קידום אחרי המיון הקיים
sub(r'            // Sort optional by priority\n            optional\.sort\(\(a, b\) => \(a\.priority \|\| 99\) - \(b\.priority \|\| 99\)\);',
    """            // מי שהוגדר לעדיפות מקודם — אך ורק לשעות החלון שלו, ורק אם
            // הן באמת קיימות היום. שאר שעותיו הפנויות נשארות כרגיל.
            WINDOW_PRIORITY_SUBS.forEach(name => {
                const wh = windowHours(name, currentDay);
                if (!wh.length) return;
                const entry = optional.find(o => o.name === name);
                if (!entry) return;
                const rest = (entry.hours || []).filter(h => !wh.includes(h));
                entry.hours = wh;
                entry.priority = 1.5;                 // אחרי ממלא מקום קבוע, לפני השאר
                entry.windowPriority = true;
                entry.otherHours = rest;
                entry.reason = 'עדיפות — שעות חלון';
            });

            // Sort optional by priority
            optional.sort((a, b) => (a.priority || 99) - (b.priority || 99));""",
    'קידום שעות חלון')

# תצוגה
sub(r"""                    let hoursInfo = '';
                    if \(t\.reason === 'פנוי בשעות מסוימות'\) \{
                        hoursInfo = `שעות פנויות: <strong>\$\{t\.hours\.join\(', '\)\}</strong> \| מלמד בשעות: \$\{t\.teachingHours\.join\(', '\)\}`;
                    \} else \{""",
    """                    let hoursInfo = '';
                    if (t.windowPriority) {
                        hoursInfo = `שעות חלון: <strong>${t.hours.join(', ')}</strong> — נמצא בבניין בין השיעורים`
                            + (t.otherHours && t.otherHours.length ? ` | פנוי גם: ${t.otherHours.join(', ')}` : '')
                            + ` | מלמד בשעות: ${(t.teachingHours || []).join(', ')}`;
                    } else if (t.reason === 'פנוי בשעות מסוימות') {
                        hoursInfo = `שעות פנויות: <strong>${t.hours.join(', ')}</strong> | מלמד בשעות: ${t.teachingHours.join(', ')}`;
                    } else {""",
    'תיאור שעות חלון')

sub(r"""                        <span class="badge badge-optional">\$\{t\.reason === 'ממלא מקום קבוע' \? 'קבוע' : 'פנוי'\}</span>""",
    """                        <span class="badge badge-optional">${t.windowPriority ? '⭐ עדיפות' : (t.reason === 'ממלא מקום קבוע' ? 'קבוע' : 'פנוי')}</span>""",
    'תג עדיפות')

open(APP, 'w', encoding='utf-8').write(src)
print('\n%d תיקונים הוחלו. גודל: %d → %d תווים' % (n, before, len(src)))
