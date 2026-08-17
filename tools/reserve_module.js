
        /* ==================== מצב מילואים ====================
           היעדרות ממושכת שונה מהיעדרות של יום. במקום לחפש מחליף כל בוקר,
           נבנית חלוקה קבועה לכל השיעורים של הנעדר, לפי הכללים:
             · אף אחד לא לוקח יותר ממחצית ממה שהנעדר החזיק
             · תקרה זמנית = חצי, ורק כשאין מועמד מתחתיה מחליטים לפי עומס בלבד
             · מי שמחליף בכיתה מקבל חלק — לא את הכל
             · כשהוא חוזר, מחזירים את השיבוץ המקורי בלחיצה
           ⚠️ זמינות נבדקת בפועל מול המערכת, לא נגזרת מהתפקיד: "מחליף בבקרים"
           לא אומר שהוא פנוי בהפסקות או בשעות אחרות. */

        const ALL_HOURS = ['בוקר', '4', '5', '6', '7', '8', '9', '10', 'סדר ערב'];

        // teacher -> { since, note, cover: { "day|hour": teacherName } }
        let reserveData = {};

        const isOnReserve = t => !!reserveData[t];

        // כל השיעורים שהנעדר מחזיק (רק שעות עם כיתה — שעה בלי כיתה אינה צריכה כיסוי)
        function reserveSlots(teacher) {
            const t = teacherSchedule[teacher];
            if (!t) return [];
            const out = [];
            (t.days || []).forEach(d => {
                (t.dayHours[d] || []).forEach(h => {
                    const cls = (dayHourClassesData[teacher] || {})[d];
                    if (cls && cls[h]) out.push({ day: d, hour: h, cls: cls[h], key: d + '|' + h });
                });
            });
            return out;
        }

        // האם המלמד באמת פנוי אז — לפי המערכת, לא לפי התפקיד
        function freeAt(teacher, day, hour) {
            if (teacher === undefined || isOnReserve(teacher)) return false;
            const t = teacherSchedule[teacher];
            if (!t || !(t.days || []).includes(day)) return false;   // לא בביה"ס באותו יום
            return !(t.dayHours[day] || []).includes(hour);          // שעה תפוסה = לא פנוי
        }

        function weeklyLoad(teacher) {
            const t = teacherSchedule[teacher];
            if (!t) return 0;
            return (t.days || []).reduce((s, d) => s + (t.dayHours[d] || []).length, 0);
        }

        // בונה את החלוקה. preferred = מי שהוגדר כמחליף בכיתה, מקבל עדיפות אך לא הכל.
        function buildReservePlan(teacher, preferred) {
            const slots = reserveSlots(teacher);
            const half = Math.floor(slots.length / 2);      // תקרה: אף אחד לא מעל מחצית
            const count = {};
            const plan = {};
            const pref = (preferred || []).filter(Boolean);

            slots.forEach(s => {
                const avail = allTeachers.filter(c => c !== teacher && freeAt(c, s.day, s.hour));
                if (!avail.length) { plan[s.key] = null; return; }

                const score = c => [
                    pref.includes(c) ? 0 : 1,      // עדיפות למחליף בכיתה
                    count[c] || 0,                  // לפזר
                    weeklyLoad(c),                  // מי שעמוס פחות
                    c,
                ];
                const under = avail.filter(c => (count[c] || 0) < half);
                // כשאין אף מועמד מתחת לתקרה — מחליטים לפי עומס בלבד
                const pool = under.length ? under : avail;
                const cmp = under.length
                    ? (a, b) => String(score(a)) < String(score(b)) ? -1 : 1
                    : (a, b) => (count[a] || 0) - (count[b] || 0) || weeklyLoad(a) - weeklyLoad(b);
                const pick = [...pool].sort(cmp)[0];
                plan[s.key] = pick;
                count[pick] = (count[pick] || 0) + 1;
            });
            return { slots, plan, count, half };
        }

        function reserveAdd() {
            const teacher = document.getElementById('reserve-teacher').value;
            if (!teacher) return;
            const raw = document.getElementById('reserve-preferred').value.trim();
            const preferred = raw ? raw.split(',').map(s => s.trim()).filter(Boolean) : [];
            const { plan } = buildReservePlan(teacher, preferred);
            reserveSave(teacher, {
                since: new Date().toISOString().slice(0, 10),
                preferred, cover: plan,
            });
        }

        function reserveSave(teacher, rec) {
            reserveData[teacher] = rec;
            const key = teacher.replace(/[.#$/\[\]]/g, '_');
            if (isOnline && database) database.ref('reserve/' + key).set(rec);
            else localStorage.setItem('reserve', JSON.stringify(reserveData));
            updateReserve();
            updateAllViews();
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

        function reserveSetCover(teacher, slotKey, who) {
            const rec = reserveData[teacher];
            if (!rec) return;
            rec.cover = { ...rec.cover, [slotKey]: who || null };
            reserveSave(teacher, rec);
        }

        // מי מכסה שיעור מסוים של מלמד במילואים (לשימוש שאר המסכים)
        function reserveCoverFor(teacher, day, hour) {
            const rec = reserveData[teacher];
            return rec && rec.cover ? (rec.cover[day + '|' + hour] || null) : null;
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
                const slots = reserveSlots(teacher);
                const cover = rec.cover || {};
                const count = {};
                Object.values(cover).forEach(c => { if (c) count[c] = (count[c] || 0) + 1; });
                const half = Math.floor(slots.length / 2);
                const gaps = slots.filter(s => !cover[s.key]).length;

                const rows = slots.map(s => {
                    const who = cover[s.key];
                    const avail = allTeachers.filter(c => c !== teacher && freeAt(c, s.day, s.hour));
                    const opts = ['<option value="">— לא שובץ —</option>']
                        .concat(avail.map(c => `<option value="${c}"${c === who ? ' selected' : ''}>${c}${(count[c] || 0) > half ? ' ⚠️' : ''}</option>`))
                        .join('');
                    const stale = who && !avail.includes(who);
                    return `<tr class="${who ? '' : 'res-gap'}">
                        <td>${dayNames[s.day]}</td><td>שעה ${s.hour}</td><td><strong>${s.cls}</strong></td>
                        <td><select onchange="reserveSetCover('${teacher.replace(/'/g, "\\'")}','${s.key}',this.value)">
                            ${stale ? `<option value="${who}" selected>${who} — כבר לא פנוי</option>` : ''}${opts}
                        </select></td>
                        <td>${avail.length ? '' : '<span class="res-none">אין אף מועמד פנוי</span>'}</td>
                    </tr>`;
                }).join('');

                const load = Object.entries(count).sort((a, b) => b[1] - a[1])
                    .map(([c, n]) => `<span class="res-chip${n > half ? ' res-over' : ''}">${c}: ${n}</span>`).join(' ');

                return `<div class="res-box">
                    <div class="res-head">
                        <div><strong>${teacher}</strong> <span class="muted">במילואים מאז ${rec.since || '—'}</span></div>
                        <button class="btn btn-sm" onclick="reserveRemove('${teacher.replace(/'/g, "\\'")}')">↩️ חזר — החזר שיבוץ מקורי</button>
                    </div>
                    <div class="res-sum">
                        <span><strong>${slots.length}</strong> שיעורים לכיסוי</span>
                        <span>תקרה לאדם: <strong>${half}</strong> (מחצית)</span>
                        ${gaps ? `<span class="res-none"><strong>${gaps}</strong> ללא מחליף</span>` : '<span class="res-ok">הכל מכוסה ✓</span>'}
                    </div>
                    <div class="res-load">${load || '<span class="muted">טרם חולק</span>'}</div>
                    <table class="res-tbl"><thead><tr>
                        <th>יום</th><th>שעה</th><th>כיתה</th><th>מחליף</th><th></th>
                    </tr></thead><tbody>${rows}</tbody></table>
                </div>`;
            }).join('');
        }

        function populateReserveSelect() {
            const sel = document.getElementById('reserve-teacher');
            if (!sel) return;
            const cur = sel.value;
            sel.innerHTML = '<option value="">— בחר מלמד —</option>' +
                allTeachers.filter(t => !isOnReserve(t))
                    .map(t => `<option value="${t}">${t}</option>`).join('');
            if (cur) sel.value = cur;
        }
