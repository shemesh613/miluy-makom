# -*- coding: utf-8 -*-
"""הסרגל הצף בגודל בינוני קבוע — בלי התכווצות בגלילה ובלי כפתור."""
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


# גודל בינוני קבוע — בין המקור (243px) לבין המצב המכווץ (117px).
# בלי מאזין גלילה ובלי כפתור: הסרגל לא זז ולא מקפיץ את התוכן.
CSS = """        /* הסרגל הצף — גודל בינוני קבוע, ללא שינוי בגלילה */
        .top-bar { padding: 9px 13px 4px; }
        .top-bar .day-selector { margin-bottom: 7px; }
        .top-bar .nav-tabs { margin-bottom: 5px; gap: 7px; }
        .day-btn { padding: 6px 15px; font-size: 0.88rem; }
        .nav-tab { padding: 7px 16px; font-size: 0.88rem; }
        @media (max-width: 620px) {
            .day-btn { padding: 5px 11px; font-size: 0.82rem; }
            .nav-tab { padding: 6px 12px; font-size: 0.82rem; }
        }
    </style>"""
sub(r'    </style>', CSS, 'גודל בינוני קבוע')

open(APP, 'w', encoding='utf-8').write(src)
print('\n%d תיקונים הוחלו. גודל: %d → %d תווים' % (n, before, len(src)))
