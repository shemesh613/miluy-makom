# -*- coding: utf-8 -*-
"""כלל ההחזרים במילוי מקום + עדכון סטטוס שלוש המורות."""
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


# ============ 1. שלוש המורות — שרה אליה כבר זמינה ============
# הן בבניין, אבל לא פנויות: חצי משעותיהן הוראה מתקנת — שיעור פרטני לתלמיד
# מתקשה, לא חלון. למשוך אותן למ"מ = לבטל לילד את הטיפול.
# מה שידוע בוודאות שונה בין השלוש, ולכן גם היחס אליהן שונה.
sub(r"""        const PARTIAL_DATA = \{
            'שרה תורג\\'מן': 'כמחצית משעותיה בהוראה מתקנת — לא רשומה במערכת',
            'המורה שרה אליה': 'כמחצית משעותיה בהוראה מתקנת — לא רשומה במערכת',
            'המורה נועה': 'אינה מופיעה בקובץ המערכת כלל',
        \};""",
    """        const PARTIAL_DATA = {
            'שרה תורג\\'מן': 'מסרה (27.8): "אני עדיין בכיתה ה\\' בשעה הזו" — שעות שנראות ריקות אינן ריקות',
            'המורה נועה': 'מסרה (17.8): "נמצאת בדר\\"כ בת\\"ת עד 14:30" — לא ידוע מה תפוס בתוך הזמן',
        };
        // המורה שרה אליה לא מסרה שום אילוץ למרות הפניות — ולכן היא זמינה
        // למילוי מקום כרגיל. עדיין נספרת כמי שהמערכת מודדת בחסר לצורך
        // עדיפות הדשא ולצורך התקרה, אבל בלי סימון "לוודא".
        const PARTIAL_YARD = ['שרה תורג\\'מן', 'המורה שרה אליה', 'המורה נועה'];""",
    'עדכון סטטוס המורות')

sub(r'        const isPartialData = t => !!PARTIAL_DATA\[t\];',
    '        const isPartialData = t => !!PARTIAL_DATA[t];          // צריכה בירור לפני מ"מ\n'
    '        const isPartialYard = t => PARTIAL_YARD.includes(t);   // שעותיה אינן במערכת',
    'הפרדת שני המצבים')

# עדיפות הדשא ותקרה — לפי הרשימה הרחבה
sub(r'            return Object\.keys\(PARTIAL_DATA\)\.filter\(t => t !== toran\);',
    '            return PARTIAL_YARD.filter(t => t !== toran);',
    'עדיפות דשא לשלושתן')
sub(r'            if \(isPartialData\(teacher\)\) return null;      // שעותיהן אינן במערכת',
    '            if (isPartialYard(teacher)) return null;      // שעותיהן אינן במערכת',
    'תקרה לשלושתן')

# ============ 2. כלל ההחזרים ============
sub(r'(?=        // Update available teachers\n        function updateAvailableTeachers)',
    """        /* ===== מי חייב מילוי מקום בחזרה =====
           העיקרון: מי שנעדר וקיבל כיסוי — חייב להחזיר. זה לא עונש אלא
           מנגנון; כשיודעים שהיעדרות עולה מ"מ בחזרה, נעדרים פחות.

           אבל לא תמיד. מי שכיסה ועדיין מתחת למכסה — הכיסוי נספר לו **כחלק
           מהמכסה**, ואף אחד לא חייב לו כלום. רק מי שכיסה כשהוא כבר על
           המכסה או מעליה זכאי להחזר.

           סדר הבדיקה חשוב: קודם האם ההחזר בכלל **אפשרי** (יש לנעדר שעה
           שבה הוא יכול לכסות את מי שכיסה אותו), ורק אז האם הוא **נדרש**.
           החזר לא אפשרי גובר על החזר נדרש. */
        function debtStatus(absentee, coverer) {
            if (!absentee || !coverer) return null;

            // א. האם בכלל אפשרי — צריך שעה שבה הנעדר פנוי והמכוסה עסוק
            const order = ['בוקר', '4', '5', '6', '7', '8', '9', '10', 'סדר ערב'];
            const opts = [];
            const at = teacherSchedule[absentee], ct = teacherSchedule[coverer];
            if (at && ct) {
                (at.days || []).forEach(d => {
                    if (!(ct.days || []).includes(d)) return;
                    order.forEach(h => {
                        const absFree = !(at.dayHours[d] || []).includes(h);
                        const covBusy = (ct.dayHours[d] || []).includes(h);
                        const cls = (dayHourClassesData[coverer] || {})[d];
                        // רק שעה שבה למכוסה יש באמת כיתה, ושהנעדר בטוח בבניין
                        if (absFree && covBusy && cls && cls[h] &&
                            safeWindows(absentee, d).includes(h)) opts.push({ day: d, hour: h, cls: cls[h] });
                    });
                });
            }
            if (!opts.length)
                return { owed: false, possible: false,
                         text: 'אין לנעדר שעה מתאימה להחזיר בה — לתאם ידנית', cls: 'debt-manual' };

            // ב. האם נדרש — רק אם המכסה שלו כבר מלאה
            const cap = substCap(coverer);
            if (cap === null)
                return { owed: false, possible: true, opts,
                         text: `${coverer} — שעותיה אינן במערכת, לתאם החזר ידנית`, cls: 'debt-manual' };
            // נמדד מול המכסה האישית של מי שכיסה, לא מול מספר קבוע
            const personal = combinedCap(coverer);
            const used = assignedCount(coverer) + yardDutyCount(coverer);
            if (used <= personal)
                return { owed: false, possible: true, opts, quota: true,
                         text: `אין חוב — הכיסוי נספר ל${coverer} בתוך המכסה שלו (${used} מתוך ${personal})`,
                         cls: 'debt-none' };
            return { owed: true, possible: true, opts,
                     text: `${absentee} ${isFem(absentee) ? 'חייבת' : 'חייב'} מ"מ בחזרה ל${coverer} — ${isFem(coverer) ? 'היא' : 'הוא'} כבר מעל המכסה`,
                     cls: 'debt-owed', suggest: opts[0] };
        }

        // הודעה לאישה בלשון נקבה — "חגית תחזיר", לא "יחזיר"
        const FEMALE_STAFF = ["חגית", "לאה", "שרה תורג'מן", "המורה שרה אליה",
                              "המורה רבקי", "המורה נועה"];
        const isFem = t => FEMALE_STAFF.includes(t);

        // ההודעה למי שמכסה — חייבת לומר מראש אם מגיע לו החזר או לא,
        // כדי שלא יגלה בדיעבד שזה "נספר לו במכסה". זו תחושת עוקץ.
        function coverMessageWithDebt(coverer, absentee, day, hour, cls) {
            const d = debtStatus(absentee, coverer);
            const f = isFem(coverer);
            const base = `${coverer}, שלום. ביום ${dayNames[day]} בשעה ${hour}`
                + `${cls ? ' בכיתה ' + cls : ''} — מילוי מקום בבקשה, במקום ${absentee}.`;
            if (!d) return base + ' תודה רבה.';
            const back = isFem(absentee) ? 'תחזיר' : 'יחזיר';
            if (d.owed && d.suggest)
                return base + ` ${absentee} ${back} לך מ"מ ביום ${dayNames[d.suggest.day]}`
                     + ` שעה ${d.suggest.hour} (${d.suggest.cls}). תודה רבה.`;
            if (d.owed) return base + ` ${absentee} ${back} לך מ"מ, נתאם מתי. תודה רבה.`;
            if (d.quota) return base + (f ? ' זה נספר לך בתוך המכסה השבועית.' : ' זה נספר לך בתוך המכסה השבועית.') + ' תודה רבה.';
            return base + ' תודה רבה.';
        }

""", 'מנגנון ההחזרים')

# ============ 3. תצוגה ברשימת השיבוצים ============
# מצב החוב מוצג בשורת ההיעדרות, וההודעה למכסה אומרת אותו מראש
sub(r"""                const contactBtnId = `contact-\$\{id\}`;
                return `""",
    """                const contactBtnId = `contact-${id}`;
                const dbt = a.substitute ? debtStatus(a.teacher, a.substitute) : null;
                return `""",
    'חישוב חוב בשורת שיבוץ')

sub(r"""                        \$\{a\.suggestion \? `<div class="suggestion-detail" style="display:none; margin-top:6px; padding:8px; background:#fff3e0; border-radius:8px; border-right:3px solid #ff9800; font-size:0\.9rem;">📖 <strong>הנחיות:</strong> \$\{a\.suggestion\}</div>` : ''\}""",
    """                        ${a.suggestion ? `<div class="suggestion-detail" style="display:none; margin-top:6px; padding:8px; background:#fff3e0; border-radius:8px; border-right:3px solid #ff9800; font-size:0.9rem;">📖 <strong>הנחיות:</strong> ${a.suggestion}</div>` : ''}
                        ${dbt ? `<div class="debt ${dbt.cls}">${dbt.owed ? '↩️' : 'ℹ️'} ${dbt.text}</div>` : ''}""",
    'הצגת מצב החוב')

sub(r"""                            \$\{a\.substitute \? getContactButtonsHTML\(a\.substitute, `\$\{a\.substitute\}, שלום\. ביום \$\{dayNames\[currentDay\]\} בשעה \$\{hourDisplay\}\$\{classAtHour \? ' בכיתה ' \+ classAtHour : ''\} — מילוי מקום בבקשה\. תודה רבה\.`\) : ''\}""",
    """                            ${a.substitute ? getContactButtonsHTML(a.substitute,
                                coverMessageWithDebt(a.substitute, a.teacher, currentDay, hourDisplay, classAtHour)) : ''}""",
    'הודעה שאומרת מראש אם מגיע החזר')

CSS = """        .debt { font-size:0.8rem; margin-top:3px; border-radius:8px; padding:3px 8px; display:inline-block; }
        .debt-owed { background:#e7f0fa; color:#1565c0; font-weight:600; }
        .debt-none { background:#eef0f3; color:#5a6069; }
        .debt-manual { background:#fdf3e0; color:#8a5300; }
    </style>"""
sub(r'    </style>', CSS, 'עיצוב')

open(APP, 'w', encoding='utf-8').write(src)
print('\n%d תיקונים הוחלו. גודל: %d → %d תווים' % (n, before, len(src)))
