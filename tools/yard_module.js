
        /* ==================== תורנות חצר — סנכרון עם מערכת התורנות ====================
           מקור הנתונים: "תורנות חצר תשפז.xlsx" שנבנתה מהמערכת + האילוצים.
           כשמלמד מדווח כנעדר, התורנויות שלו באותו יום עוברות אוטומטית למחליף
           שפנוי באותה הפסקה, והנעדר מחזיר לו תורנות בהמשך השבוע.
           אם אין אף מחליף פנוי — ממלא המקום של השיעור הצמוד לוקח את התורנות. */

        // שעות הלימוד הצמודות לכל הפסקה. נעדר באחת מהן — לא יכול לעמוד בתורנות.
        const YARD_ADJACENT = {
            '10:05': ['בוקר', '4'], '10:20': ['בוקר', '4'],
            '11:20': ['4', '5'], '12:10': ['5', '6'],
            '13:15': ['6', '7'], '13:30': ['6', '7'],
            '15:15': ['8', '9'], 'סוף יום': ['4', '5']
        };
        // איזו קבוצת גיל יוצאת בכל הפסקה
        const YARD_GROUP = {
            '10:05': 'ד–ו', '11:20': 'ד–ו', '13:15': 'ד–ו', '15:15': 'ד–ו',
            '10:20': 'א–ג', '12:10': 'א–ג', '13:30': 'א–ג', 'סוף יום': 'הכל'
        };
        const YARD_SLOT_ORDER = ['10:05', '10:20', '11:20', '12:10', '13:15', '13:30', '15:15', 'סוף יום'];

        let yardSwapsData = {};   // dutyKey -> { cover, repay, mode, at }

        const yardParse = k => { const [slot, day, post] = k.split('|'); return { slot, day, post }; };
        const yardFmt = k => { const p = yardParse(k); return `יום ${p.day}, ${p.slot} — ${p.post}`; };

        // כל התורנויות של יום (0=ראשון .. 5=שישי), ממוינות לפי סדר ההפסקות
        function yardDutiesForDay(dayIdx) {
            const dayName = dayNames[dayIdx];
            return Object.keys(YARD_DUTY)
                .filter(k => yardParse(k).day === dayName)
                .sort((a, b) => {
                    const A = yardParse(a), B = yardParse(b);
                    return (YARD_SLOT_ORDER.indexOf(A.slot) - YARD_SLOT_ORDER.indexOf(B.slot))
                        || A.post.localeCompare(B.post, 'he');
                })
                .map(k => ({ key: k, ...yardParse(k), toran: YARD_DUTY[k] }));
        }

        // האם המלמד נעדר באחת השעות הצמודות להפסקה
        function yardAbsentAt(teacher, dayIdx, slot) {
            const adj = YARD_ADJACENT[slot] || [];
            return Object.values(absencesData).some(a =>
                a.teacher === teacher && a.day === dayIdx && !a.forNextWeek && adj.includes(a.hour));
        }

        // מי ממלא את מקומו בשיעור הצמוד להפסקה (מתוך שיבוץ מילוי המקום)
        function yardLessonSubstitute(teacher, dayIdx, slot) {
            const adj = YARD_ADJACENT[slot] || [];
            const hit = Object.values(absencesData).find(a =>
                a.teacher === teacher && a.day === dayIdx && adj.includes(a.hour) && a.substitute);
            return hit ? hit.substitute : null;
        }

        // התוכנית ליום: לכל תורנות — האם היא מכוסה, מי מחליף, ומה ההחזר
        function yardCoverPlan(dayIdx) {
            const duties = yardDutiesForDay(dayIdx);
            const taken = new Set();   // "slot|teacher" — מי כבר עומד בהפסקה הזו
            duties.forEach(d => {
                if (!yardAbsentAt(d.toran, dayIdx, d.slot)) taken.add(d.slot + '|' + d.toran);
            });

            return duties.map(d => {
                if (!yardAbsentAt(d.toran, dayIdx, d.slot)) return { ...d, status: 'ok' };

                const cands = ((YARD_SUBS[d.key] || {}).cands || []);
                const free = cands.filter(c =>
                    !taken.has(d.slot + '|' + c.name) && !yardAbsentAt(c.name, dayIdx, d.slot));

                // שיבוץ ידני שנקבע קודם — מכבדים אותו
                const manual = yardSwapsData[d.key];
                if (manual && manual.cover) {
                    taken.add(d.slot + '|' + manual.cover);
                    return { ...d, status: 'manual', cover: manual.cover, repay: manual.repay || null, options: free };
                }

                if (free.length) {
                    const c = free[0];
                    taken.add(d.slot + '|' + c.name);
                    const repay = (c.repay || []).find(r => yardParse(r).day !== d.day) || null;
                    return { ...d, status: 'auto', cover: c.name, repay, options: free.slice(1) };
                }

                // אין ברירה — ממלא המקום של השיעור לוקח את התורנות
                const ms = yardLessonSubstitute(d.toran, dayIdx, d.slot);
                return { ...d, status: ms ? 'fallback' : 'open', cover: ms, repay: null, options: [] };
            });
        }

        // ---------- שמירה וסנכרון ----------
        function yardSetCover(key, cover, repay, mode) {
            yardSwapsData[key] = { cover, repay: repay || null, mode: mode || 'manual', at: Date.now() };
            if (isOnline && database) database.ref('yardSwaps/' + key.replace(/[.#$/\[\]]/g, '_')).set(yardSwapsData[key]);
            else localStorage.setItem('yardSwaps', JSON.stringify(yardSwapsData));
            updateYardDuty();
        }

        function yardClearCover(key) {
            delete yardSwapsData[key];
            if (isOnline && database) database.ref('yardSwaps/' + key.replace(/[.#$/\[\]]/g, '_')).remove();
            else localStorage.setItem('yardSwaps', JSON.stringify(yardSwapsData));
            updateYardDuty();
        }

        function yardPickCover(key) {
            const plan = yardCoverPlan(currentDay).find(p => p.key === key);
            if (!plan) return;
            const opts = plan.options || [];
            if (!opts.length) { alert('אין מועמד פנוי נוסף לתורנות הזו.'); return; }
            const list = opts.map((c, i) => `${i + 1}. ${c.name}`).join('\n');
            const pick = prompt(`מי יחליף ב${yardFmt(key)}?\n\n${list}\n\nהקלד מספר:`, '1');
            const idx = parseInt(pick, 10) - 1;
            if (isNaN(idx) || !opts[idx]) return;
            const c = opts[idx];
            const repay = (c.repay || []).find(r => yardParse(r).day !== plan.day) || null;
            yardSetCover(key, c.name, repay, 'manual');
        }

        // ---------- תצוגה ----------
        function yardCountNeeding(dayIdx) {
            return yardCoverPlan(dayIdx).filter(p => p.status !== 'ok').length;
        }

        function updateYardDuty() {
            const el = document.getElementById('yard-duty-list');
            if (!el) return;
            document.getElementById('yard-day-name').textContent = dayNames[currentDay];

            const plan = yardCoverPlan(currentDay);
            if (!plan.length) {
                el.innerHTML = '<div class="empty-state">אין תורנויות חצר ביום זה.</div>';
                updateYardBadge();
                return;
            }
            const need = plan.filter(p => p.status !== 'ok');

            const summary = `
                <div class="yard-summary">
                    <div><strong>${plan.length}</strong> תורנויות היום</div>
                    <div class="${need.length ? 'yard-warn' : 'yard-good'}">
                        ${need.length ? `<strong>${need.length}</strong> דורשות החלפה` : 'הכל מאויש ✓'}
                    </div>
                </div>`;

            const rows = plan.map(p => {
                const badge = {
                    ok: '<span class="yard-pill yard-pill-ok">מאויש</span>',
                    auto: '<span class="yard-pill yard-pill-auto">הוחלף אוטומטית</span>',
                    manual: '<span class="yard-pill yard-pill-manual">נקבע ידנית</span>',
                    fallback: '<span class="yard-pill yard-pill-fallback">ממלא המקום לוקח</span>',
                    open: '<span class="yard-pill yard-pill-open">אין מחליף — לטפל</span>'
                }[p.status];

                if (p.status === 'ok') {
                    return `<div class="yard-row yard-row-ok">
                        <div class="yard-slot"><strong>${p.slot}</strong><small>${p.post === 'שער' ? 'הכל' : (YARD_GROUP[p.slot] || '')}</small></div>
                        <div class="yard-post">${p.post}</div>
                        <div class="yard-who">${p.toran}</div>
                        <div class="yard-status">${badge}</div>
                    </div>`;
                }

                const msg = `שלום ${p.cover || ''}, ${p.toran} נעדר היום ולכן התורנות של ${p.slot} ב${p.post} עוברת אליך. תודה רבה!`;
                const contact = p.cover ? getContactButtonsHTML(p.cover, msg) : '';
                const repayTxt = p.repay
                    ? `<div class="yard-repay">↩️ ${p.toran} יחזיר ל${p.cover}: <strong>${yardFmt(p.repay)}</strong></div>`
                    : (p.cover ? '<div class="yard-repay yard-repay-none">↩️ אין תורנות שאפשר להחזיר בה — לסכם ידנית</div>' : '');

                return `<div class="yard-row yard-row-need">
                    <div class="yard-slot"><strong>${p.slot}</strong><small>${p.post === 'שער' ? 'הכל' : (YARD_GROUP[p.slot] || '')}</small></div>
                    <div class="yard-post">${p.post}</div>
                    <div class="yard-who">
                        <div class="yard-absent">${p.toran} — נעדר</div>
                        <div class="yard-cover">${p.cover ? '➜ <strong>' + p.cover + '</strong>' : '➜ טרם נמצא מחליף'}</div>
                        ${repayTxt}
                    </div>
                    <div class="yard-status">
                        ${badge}
                        <div class="yard-actions">
                            ${contact}
                            ${(p.options || []).length ? `<button class="btn btn-sm" onclick="yardPickCover('${p.key}')">🔄 החלף</button>` : ''}
                            ${p.status === 'manual' ? `<button class="btn btn-sm" onclick="yardClearCover('${p.key}')">↺ אוטומטי</button>` : ''}
                        </div>
                    </div>
                </div>`;
            }).join('');

            el.innerHTML = summary + `<div class="yard-table">${rows}</div>`;
            updateYardBadge();
        }

        function updateYardBadge() {
            const b = document.getElementById('yard-badge');
            if (!b) return;
            const n = yardCountNeeding(currentDay);
            b.textContent = n ? String(n) : '';
            b.style.display = n ? 'inline-flex' : 'none';
        }

        // טקסט לפרסום בקבוצת המלמדים
        function yardCopyText() {
            const plan = yardCoverPlan(currentDay).filter(p => p.status !== 'ok');
            if (!plan.length) { alert('אין שינויים בתורנות החצר היום.'); return; }
            const lines = plan.map(p =>
                `${p.slot} ${p.post}: ${p.cover || '❗טרם שובץ'} (במקום ${p.toran})`
                + (p.repay ? ` | החזר: ${yardFmt(p.repay)}` : ''));
            const txt = `🏫 שינויים בתורנות חצר — יום ${dayNames[currentDay]}\n\n` + lines.join('\n');
            navigator.clipboard.writeText(txt)
                .then(() => alert('✅ הועתק ללוח'))
                .catch(() => prompt('העתק:', txt));
        }
