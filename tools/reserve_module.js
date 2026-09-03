
        /* ==================== מצב מילואים ====================
           היעדרות ממושכת: מזינים **פעם אחת** את ממלאי המקום הקבועים, והמערכת
           מחלקת ביניהם — ורק ביניהם — גם את השיעורים וגם את תורנויות החצר,
           לכל תקופת המילואים. אין חיפוש מחליף כל בוקר.

           החלוקה מאוזנת בין הממלאים שהוזנו, ונבדקת מול הזמינות בפועל:
           ממלא שאינו פנוי בשעה מסוימת פשוט לא יקבל אותה. משבצת שאף אחד
           מהממלאים אינו יכול לקחת מסומנת במפורש — כולל מי כן היה יכול —
           כי "מחליף בבקרים" לא אומר שהוא פנוי גם בהפסקות. */

        // teacher -> { since, subs: [], lessons: {"day|hour": sub}, duties: {dutyKey: sub} }
        // (ההצהרה עצמה למעלה, עם שאר נתוני הריצה)

        const isOnReserve = t => !!reserveData[t];

        // שיעורים שהנעדר מחזיק — רק שעות עם כיתה
        function reserveSlots(teacher) {
            const t = teacherSchedule[teacher];
            if (!t) return [];
            const out = [];
            (t.days || []).forEach(d => {
                const cls = (dayHourClassesData[teacher] || {})[d] || {};
                (t.dayHours[d] || []).forEach(h => {
                    if (cls[h]) out.push({ day: d, hour: h, cls: cls[h], key: d + '|' + h });
                });
            });
            return out;
        }

        // תורנויות החצר של הנעדר
        function reserveDuties(teacher) {
            return Object.keys(YARD_DUTY).filter(k => YARD_DUTY[k] === teacher)
                .sort((a, b) => {
                    const A = yardParse(a), B = yardParse(b);
                    return dayNames.indexOf(A.day) - dayNames.indexOf(B.day)
                        || YARD_SLOT_ORDER.indexOf(A.slot) - YARD_SLOT_ORDER.indexOf(B.slot);
                })
                .map(k => ({ key: k, ...yardParse(k) }));
        }

        // האם המלמד פנוי לשיעור באותה שעה — לפי המערכת, לא לפי התפקיד
        function freeAt(teacher, day, hour) {
            if (!teacher || isOnReserve(teacher)) return false;
            const t = teacherSchedule[teacher];
            if (!t || !(t.days || []).includes(day)) return false;   // לא בביה"ס באותו יום
            return !(t.dayHours[day] || []).includes(hour);          // שעה תפוסה = לא פנוי
        }

        // האם יכול לקחת תורנות מסוימת — לפי רשימת המועמדים שנבנתה עם כללי התורנות
        function canTakeDuty(teacher, dutyKey) {
            const cands = ((YARD_SUBS[dutyKey] || {}).cands || []).map(c => c.name);
            return cands.includes(teacher);
        }

        function dutyCandidates(dutyKey) {
            return ((YARD_SUBS[dutyKey] || {}).cands || []).map(c => c.name);
        }

        function weeklyLoad(teacher) {
            const t = teacherSchedule[teacher];
            if (!t) return 0;
            return (t.days || []).reduce((s, d) => s + (t.dayHours[d] || []).length, 0);
        }

        // חלוקה מאוזנת בין הממלאים שהוזנו בלבד
        function spread(items, subs, canTake) {
            const count = {};
            subs.forEach(s => count[s] = 0);
            const out = {};
            items.forEach(it => {
                const able = subs.filter(s => canTake(s, it));
                if (!able.length) { out[it.key] = null; return; }
                able.sort((a, b) => count[a] - count[b] || weeklyLoad(a) - weeklyLoad(b)
                                    || a.localeCompare(b, 'he'));
                out[it.key] = able[0];
                count[able[0]]++;
            });
            return { plan: out, count };
        }

        function buildReservePlan(teacher, subs) {
            subs = (subs || []).filter(s => s && s !== teacher && teacherSchedule[s]);
            const slots = reserveSlots(teacher);
            const duties = reserveDuties(teacher);
            const L = spread(slots, subs, (s, it) => freeAt(s, it.day, it.hour));
            const Dt = spread(duties, subs, (s, it) => canTakeDuty(s, it.key));
            return { slots, duties, subs, lessons: L.plan, duties_plan: Dt.plan,
                     lessonCount: L.count, dutyCount: Dt.count };
        }

        // ---------- שמירה ----------
        function reserveSave(teacher, rec) {
            reserveData[teacher] = rec;
            const key = teacher.replace(/[.#$/\[\]]/g, '_');
            if (isOnline && database) database.ref('reserve/' + key).set(rec);
            else localStorage.setItem('reserve', JSON.stringify(reserveData));
            updateReserve();
            updateAllViews();
        }

        function reserveAdd() {
            const teacher = document.getElementById('reserve-teacher').value;
            if (!teacher) { alert('בחר מי יוצא למילואים.'); return; }
            const picked = [...document.querySelectorAll('#reserve-subs input:checked')]
                .map(i => i.value);
            if (picked.length < 1) { alert('בחר לפחות ממלא מקום אחד קבוע.'); return; }
            const r = buildReservePlan(teacher, picked);
            reserveSave(teacher, {
                since: new Date().toISOString().slice(0, 10),
                subs: picked, lessons: r.lessons, duties: r.duties_plan,
            });
        }

        function reserveRemove(teacher) {
            if (!confirm(`${teacher} חוזר — להחזיר את השיבוץ המקורי?`)) return;
            delete reserveData[teacher];
            const key = teacher.replace(/[.#$/\[\]]/g, '_');
            if (isOnline && database) database.ref('reserve/' + key).remove();
            else localStorage.setItem('reserve', JSON.stringify(reserveData));
            updateReserve();
            updateAllViews();
        }

        function reserveSet(teacher, kind, key, who) {
            const rec = reserveData[teacher];
            if (!rec) return;
            rec[kind] = { ...(rec[kind] || {}), [key]: who || null };
            reserveSave(teacher, rec);
        }

        function reserveRebuild(teacher) {
            const rec = reserveData[teacher];
            if (!rec) return;
            if (!confirm('לחשב מחדש את החלוקה? שינויים ידניים יידרסו.')) return;
            const r = buildReservePlan(teacher, rec.subs || []);
            reserveSave(teacher, { ...rec, lessons: r.lessons, duties: r.duties_plan });
        }

        // מי מכסה שיעור של מלמד במילואים (לשימוש שאר המסכים)
        function reserveCoverFor(teacher, day, hour) {
            const rec = reserveData[teacher];
            return rec && rec.lessons ? (rec.lessons[day + '|' + hour] || null) : null;
        }
        function reserveDutyCoverFor(dutyKey) {
            const t = YARD_DUTY[dutyKey];
            const rec = t && reserveData[t];
            return rec && rec.duties ? (rec.duties[dutyKey] || null) : null;
        }

        // ---------- תצוגה ----------
        function resSelect(teacher, kind, key, who, able) {
            const opts = ['<option value="">— לא שובץ —</option>']
                .concat(able.map(c => `<option value="${c}"${c === who ? ' selected' : ''}>${c}</option>`));
            const stale = who && !able.includes(who)
                ? `<option value="${who}" selected>${who} — לא פנוי</option>` : '';
            const t = teacher.replace(/'/g, "\\'");
            return `<select onchange="reserveSet('${t}','${kind}','${key}',this.value)">${stale}${opts.join('')}</select>`;
        }

        function updateReserve() {
            const el = document.getElementById('reserve-list');
            if (!el) return;
            const names = Object.keys(reserveData);
            if (!names.length) {
                el.innerHTML = '<div class="empty-state">אין כרגע אף מלמד במילואים.</div>';
                return;
            }
            el.innerHTML = names.map(teacher => {
                const rec = reserveData[teacher];
                const subs = rec.subs || [];
                const slots = reserveSlots(teacher);
                const duties = reserveDuties(teacher);
                const L = rec.lessons || {}, Dt = rec.duties || {};
                const cnt = {};
                subs.forEach(s => cnt[s] = { l: 0, d: 0 });
                Object.values(L).forEach(s => { if (cnt[s]) cnt[s].l++; });
                Object.values(Dt).forEach(s => { if (cnt[s]) cnt[s].d++; });

                const lessonRows = slots.map(s => {
                    const able = subs.filter(x => freeAt(x, s.day, s.hour));
                    return `<tr class="${L[s.key] ? '' : 'res-gap'}">
                        <td>${dayNames[s.day]}</td><td>שעה ${s.hour}</td><td><strong>${s.cls}</strong></td>
                        <td>${resSelect(teacher, 'lessons', s.key, L[s.key], able)}</td>
                        <td>${able.length ? '' : '<span class="res-none">אף ממלא אינו פנוי</span>'}</td>
                    </tr>`;
                }).join('');

                const dutyRows = duties.map(d => {
                    const able = subs.filter(x => canTakeDuty(x, d.key));
                    const others = dutyCandidates(d.key).filter(c => !subs.includes(c));
                    return `<tr class="${Dt[d.key] ? '' : 'res-gap'}">
                        <td>${d.day}</td><td>${d.slot}</td><td>${d.post}</td>
                        <td>${resSelect(teacher, 'duties', d.key, Dt[d.key], able)}</td>
                        <td>${able.length ? '' :
                            `<span class="res-none">אף ממלא אינו יכול</span>${others.length ?
                            `<div class="res-alt">אפשריים: ${others.slice(0, 4).join(' · ')}</div>` : ''}`}</td>
                    </tr>`;
                }).join('');

                const gapsL = slots.filter(s => !L[s.key]).length;
                const gapsD = duties.filter(d => !Dt[d.key]).length;
                const t = teacher.replace(/'/g, "\\'");

                return `<div class="res-box">
                    <div class="res-head">
                        <div><strong>${teacher}</strong> <span class="muted">במילואים מאז ${rec.since || '—'}</span></div>
                        <div style="display:flex; gap:6px;">
                            <button class="btn btn-sm" onclick="reserveRebuild('${t}')">🔄 חשב מחדש</button>
                            <button class="btn btn-sm" onclick="reserveRemove('${t}')">↩️ חזר — החזר שיבוץ מקורי</button>
                        </div>
                    </div>
                    <div class="res-load">${subs.map(s =>
                        `<span class="res-chip"><strong>${s}</strong> — ${cnt[s].l} שיעורים · ${cnt[s].d} תורנויות</span>`).join(' ')}</div>

                    <div class="res-sum">
                        <span><strong>${slots.length}</strong> שיעורים</span>
                        ${gapsL ? `<span class="res-none"><strong>${gapsL}</strong> ללא ממלא</span>` : '<span class="res-ok">כל השיעורים מכוסים ✓</span>'}
                    </div>
                    <table class="res-tbl"><thead><tr>
                        <th>יום</th><th>שעה</th><th>כיתה</th><th>ממלא מקום</th><th></th>
                    </tr></thead><tbody>${lessonRows}</tbody></table>

                    <div class="res-sum" style="margin-top:14px;">
                        <span><strong>${duties.length}</strong> תורנויות חצר</span>
                        ${gapsD ? `<span class="res-none"><strong>${gapsD}</strong> ללא ממלא</span>` : '<span class="res-ok">כל התורנויות מכוסות ✓</span>'}
                    </div>
                    ${duties.length ? `<table class="res-tbl"><thead><tr>
                        <th>יום</th><th>שעה</th><th>עמדה</th><th>ממלא מקום</th><th></th>
                    </tr></thead><tbody>${dutyRows}</tbody></table>`
                    : '<div class="muted">אין לו תורנויות חצר.</div>'}
                </div>`;
            }).join('');
        }

        function populateReserveSelect() {
            const sel = document.getElementById('reserve-teacher');
            const box = document.getElementById('reserve-subs');
            if (!sel || !box) return;
            const cur = sel.value;
            sel.innerHTML = '<option value="">— מי יוצא למילואים —</option>' +
                allTeachers.filter(t => !isOnReserve(t))
                    .map(t => `<option value="${t}">${t}</option>`).join('');
            if (cur) sel.value = cur;
            box.innerHTML = allTeachers.filter(t => !isOnReserve(t) && t !== sel.value)
                .map(t => `<label class="res-pick"><input type="checkbox" value="${t}"> ${t}</label>`).join('');
        }
