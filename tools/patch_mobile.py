# -*- coding: utf-8 -*-
"""שמירת מצב בנייד · דיווח להיום או מחר · העתקה משולבת · הודעות החזר · שליחה מרוכזת."""
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


# ============ 1. חזרה לאותה לשונית אחרי יציאה מהאתר ============
# בנייד המערכת מפנה את הדף כשעוברים לשיחה, ובחזרה הוא נטען מחדש ונוחת
# בדף הבית. שומרים את הלשונית ואת היום, ומשחזרים בטעינה.
sub(r'        function navigateToPage\(pageId\) \{',
    """        const UI_STATE = 'uiState';
        function saveUiState() {
            try { sessionStorage.setItem(UI_STATE, JSON.stringify({
                page: (document.querySelector('.nav-tab.active') || {}).dataset?.page || 'home',
                day: currentDay, at: Date.now() })); } catch (e) {}
        }
        function restoreUiState() {
            try {
                const s = JSON.parse(sessionStorage.getItem(UI_STATE) || 'null');
                if (!s) return false;
                if (Date.now() - (s.at || 0) > 6 * 3600e3) return false;   // אחרי 6 שעות מתחילים נקי
                if (typeof s.day === 'number' && s.day !== currentDay) {
                    currentDay = s.day;
                    document.querySelectorAll('.day-btn').forEach(b =>
                        b.classList.toggle('active', +b.dataset.day === s.day));
                }
                if (s.page && s.page !== 'home' && document.getElementById('page-' + s.page)) {
                    navigateToPage(s.page);
                    return true;
                }
            } catch (e) {}
            return false;
        }
        // בנייד היציאה לשיחה לא תמיד מפעילה unload — pagehide/visibilitychange כן
        window.addEventListener('pagehide', saveUiState);
        window.addEventListener('beforeunload', saveUiState);
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'hidden') saveUiState();
        });

        function navigateToPage(pageId) {""",
    'שמירת מצב הממשק')

sub(r'            if \(pageId === \'report\'\) updateLockedNotice\(\);\n            updateAllViews\(\);\n        \}',
    '            if (pageId === \'report\') updateLockedNotice();\n'
    '            updateAllViews();\n'
    '            saveUiState();\n        }',
    'שמירה בכל מעבר לשונית')

sub(r'        document\.querySelector\(`\.day-btn\[data-day="\$\{currentDay\}"\]`\)\.classList\.add\(\'active\'\);\n        renderAutoDayNotice\(\);',
    '        document.querySelector(`.day-btn[data-day="${currentDay}"]`).classList.add(\'active\');\n'
    '        setTimeout(restoreUiState, 0);   // חוזרים ללשונית שממנה יצאת\n'
    '        renderAutoDayNotice();',
    'שחזור בטעינה')

# ============ 2. דיווח להיום או למחר גם כשהיום נעול ============
# הנעילה נועדה למנוע דיווח מאוחר על יום שכבר עבר, אבל היא חסמה גם דיווח
# לגיטימי על היום עצמו. מעכשיו היום ומחר תמיד פתוחים לדיווח.
sub(r'        function isDayLocked\(targetDay\) \{\n            // Check if day was manually unlocked by admin\n            if \(unlockedDaysData\[targetDay\]\) \{\n                return false; // Manually unlocked\n            \}',
    """        function isDayLocked(targetDay) {
            // Check if day was manually unlocked by admin
            if (unlockedDaysData[targetDay]) {
                return false; // Manually unlocked
            }
            // היום ומחר תמיד פתוחים — אלה הדיווחים הרגילים, ואין סיבה לנעול אותם
            const t = israelNow();
            if (targetDay === t.day || targetDay === (t.day + 1) % 7) return false;""",
    'היום ומחר תמיד פתוחים')

# ============ 3. הודעות מפורטות לשני הצדדים בחילופי תורנות ============
sub(r'        // טקסט לפרסום בקבוצת המלמדים\n        function yardCopyText\(\) \{',
    """        /* שתי הודעות נפרדות לכל חילוף תורנות: אחת למי שלוקח עכשיו,
           ואחת לנעדר שחייב להחזיר — כל אחת עם התאריך המדויק של ההחזר. */
        function yardSwapMessages(p) {
            const day = dayNames[currentDay];
            const back = p.repay ? yardFmt(p.repay) : null;
            return {
                cover: p.cover ? { name: p.cover, role: 'לוקח את התורנות',
                    msg: `${p.cover}, שלום. ${p.toran} נעדר היום, ולכן תורנות ${p.slot} ב${p.post} (יום ${day}) עוברת אליך בבקשה.`
                        + (back ? ` ${p.toran} יחזיר לך ב${back}.` : ' ההחזר יתואם בהמשך.')
                        + ' תודה.' } : null,
                owes: p.cover ? { name: p.toran, role: 'חייב החזר',
                    msg: `${p.toran}, שלום. התורנות שלך היום (${p.slot} ב${p.post}) עברה ל${p.cover}.`
                        + (back ? ` בבקשה החזר לו ב${back}.` : ' נתאם החזר בהמשך.')
                        + ' תודה.' } : null,
            };
        }

        // טקסט לפרסום בקבוצת המלמדים
        function yardCopyText() {""",
    'הודעות חילוף לשני הצדדים')

sub(r"""                const msg = `\$\{p\.cover \|\| ''\}, שלום\. \$\{p\.toran\} נעדר היום, ולכן תורנות \$\{p\.slot\} ב\$\{p\.post\} עוברת אליך\. תודה\.`;
                const contact = p\.cover \? getContactButtonsHTML\(p\.cover, msg\) : '';""",
    """                const sw = yardSwapMessages(p);
                const contact = sw.cover
                    ? `<div class="yard-send"><span>לוקח: <strong>${sw.cover.name}</strong></span>${getContactButtonsHTML(sw.cover.name, sw.cover.msg)}</div>`
                      + `<div class="yard-send"><span>מחזיר: <strong>${sw.owes.name}</strong></span>${getContactButtonsHTML(sw.owes.name, sw.owes.msg)}</div>`
                    : '';""",
    'כפתורי שליחה לשני הצדדים')

# ============ 4. העתקה משולבת — תורנות חצר + מילוי מקום ============
sub(r"""            const txt = `🏫 שינויים בתורנות חצר — יום \$\{dayNames\[currentDay\]\}\\n\\n` \+ lines\.join\('\\n'\);
            navigator\.clipboard\.writeText\(txt\)
                \.then\(\(\) => alert\('✅ הועתק ללוח'\)\)
                \.catch\(\(\) => prompt\('העתק:', txt\)\);
        \}""",
    """            const txt = `🏫 שינויים בתורנות חצר — יום ${dayNames[currentDay]}\\n\\n` + lines.join('\\n');
            copyOut(txt);
        }

        function copyOut(txt) {
            // בדפדפני נייד ובהקשר לא-מאובטח navigator.clipboard פשוט לא קיים,
            // ואז צריך ליפול ל-prompt במקום לזרוק שגיאה
            const cb = navigator.clipboard;
            if (!cb || !cb.writeText) { prompt('העתק:', txt); return; }
            cb.writeText(txt)
                .then(() => alert('✅ הועתק ללוח'))
                .catch(() => prompt('העתק:', txt));
        }

        /* העתקה אחת שמכילה גם את מילויי המקום וגם את תורנות החצר —
           בפועל מפרסמים את שניהם יחד, ולא היה טעם בשתי העתקות נפרדות. */
        function copyEverything() {
            const day = dayNames[currentDay];
            const out = [`📋 סיכום יום ${day}`, ''];

            const subs = Object.values(absencesData)
                .filter(a => a.day === currentDay && !a.forNextWeek);
            out.push('🔄 *מילוי מקום*');
            if (!subs.length) out.push('   אין היעדרויות');
            else subs.forEach(a => out.push(
                `   ${a.teacher} · שעה ${a.hour}${a.classAtHour ? ' · ' + a.classAtHour : ''} → `
                + (a.merged ? 'איחוד כיתות' : (a.substitute || '❗טרם שובץ'))));

            out.push('', '🏫 *תורנות חצר*');
            const plan = yardCoverPlan(currentDay);
            const need = plan.filter(p => p.status !== 'ok');
            if (!need.length) out.push('   ללא שינוי — הכל מאויש');
            else need.forEach(p => out.push(
                `   ${p.slot} ${p.post}: ${p.cover || '❗טרם שובץ'} (במקום ${p.toran})`
                + (p.repay ? ` | החזר: ${yardFmt(p.repay)}` : '')));

            copyOut(out.join('\\n'));
        }

        /* שליחה מרוכזת לעצמי: הודעה אחת עם קישור מוכן לכל נמען, כדי שאפשר
           יהיה להעביר אחד-אחד מתוך ווטסאפ בלי לצאת מהאתר בכל פעם. */
        function buildAllWaLinks() {
            const day = dayNames[currentDay];
            const items = [];
            Object.values(absencesData)
                .filter(a => a.day === currentDay && !a.forNextWeek && a.substitute)
                .forEach(a => items.push({ name: a.substitute,
                    msg: `${a.substitute}, שלום. היום (יום ${day}) בשעה ${a.hour}`
                        + `${a.classAtHour ? ' בכיתה ' + a.classAtHour : ''} — מילוי מקום בבקשה, במקום ${a.teacher}. תודה.` }));
            yardCoverPlan(currentDay).filter(p => p.status !== 'ok').forEach(p => {
                const sw = yardSwapMessages(p);
                if (sw.cover) items.push(sw.cover);
                if (sw.owes) items.push(sw.owes);
            });
            if (!items.length) { alert('אין הודעות לשלוח היום.'); return null; }
            const lines = items.map(it => {
                const c = teacherContacts[it.name];
                const link = c && c.phone
                    ? `https://wa.me/${phoneToInternational(c.phone)}?text=${encodeURIComponent(it.msg)}`
                    : '(אין טלפון)';
                return `▸ *${it.name}*\\n${link}`;
            });
            return `📤 הודעות ליום ${day} — ${items.length} נמענים\\n\\n` + lines.join('\\n\\n');
        }

        async function sendAllLinksToSelf() {
            const txt = buildAllWaLinks();
            if (!txt) return;
            try {
                await sendWhatsAppDirect(ADMIN_PHONE || '0526953500', txt);
                alert('✅ נשלח אליך בווטסאפ — משם אפשר להעביר אחד-אחד');
            } catch (e) {
                copyOut(txt);
                alert('השליחה נכשלה, אז הרשימה הועתקה ללוח: ' + e.message);
            }
        }""",
    'העתקה משולבת ושליחה מרוכזת')

sub(r'                    <button class="btn btn-primary" onclick="yardCopyText\(\)">📋 העתק שינויים לפרסום</button>',
    '                    <button class="btn btn-primary" onclick="copyEverything()">📋 העתק הכל — מילוי מקום + תורנות</button>\n'
    '                    <button class="btn" onclick="sendAllLinksToSelf()">📤 שלח לי את כל ההודעות לווטסאפ</button>\n'
    '                    <button class="btn" onclick="yardCopyText()">🏫 רק תורנות</button>',
    'כפתורי הפעולה')

CSS = """        .yard-send { display:flex; align-items:center; gap:6px; font-size:0.8rem;
            color:#5a6069; margin-top:4px; flex-wrap:wrap; justify-content:flex-end; }
    </style>"""
sub(r'    </style>', CSS, 'עיצוב')

open(APP, 'w', encoding='utf-8').write(src)
print('\n%d תיקונים הוחלו. גודל: %d → %d תווים' % (n, before, len(src)))
