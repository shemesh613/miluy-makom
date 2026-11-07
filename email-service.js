/**
 * Email service for מילוי מקום
 * Checks Firebase for pending email requests and sends via Gmail
 * Runs every 5 minutes via Windows Task Scheduler
 */

const https = require('https');
const nodemailer = require('nodemailer');

// Config
const FIREBASE_URL = 'https://moria-1d5c0-default-rtdb.europe-west1.firebasedatabase.app';
const ADMIN_EMAIL = 'shemesh613@gmail.com';
const GMAIL_APP_PASSWORD = process.env.GMAIL_APP_PASSWORD || '';
const DAY_NAMES = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי', 'שבת'];

// Gmail transporter
const transporter = nodemailer.createTransport({
    service: 'gmail',
    auth: {
        user: ADMIN_EMAIL,
        pass: GMAIL_APP_PASSWORD
    }
});

function firebaseGet(path) {
    return new Promise((resolve, reject) => {
        https.get(`${FIREBASE_URL}${path}.json`, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try { resolve(JSON.parse(data)); } catch (e) { resolve(null); }
            });
        }).on('error', reject);
    });
}

function firebaseDelete(path) {
    return new Promise((resolve, reject) => {
        const url = new URL(`${path}.json`, FIREBASE_URL);
        const req = https.request(url, { method: 'DELETE' }, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => resolve(data));
        });
        req.on('error', reject);
        req.end();
    });
}

async function sendEmail(to, subject, body) {
    return transporter.sendMail({
        from: `"מערכת מילוי מקום" <${ADMIN_EMAIL}>`,
        to,
        subject,
        text: body
    });
}

async function processPendingEmails() {
    const pending = await firebaseGet('/pendingEmails');
    if (!pending) {
        console.log('No pending emails.');
        return;
    }

    const keys = Object.keys(pending);
    console.log(`Processing ${keys.length} pending email(s)...`);

    for (const key of keys) {
        const data = pending[key];
        try {
            // Check if this is a daily summary email (has subject field)
            if (data.subject) {
                await sendEmail(
                    data.email || ADMIN_EMAIL,
                    data.subject,
                    `${data.reason}\n---\nמערכת מילוי מקום`
                );
                console.log(`✅ Sent summary to: ${data.email || ADMIN_EMAIL}`);
            } else {
                // Regular absence email
                const dayName = DAY_NAMES[data.day] || '?';
                const body = `מורה: ${data.teacher}\nיום: ${dayName}\nשעות: ${data.hours}\nסיבה: ${data.reason || 'לא צוינה'}\nתאריך: ${new Date().toLocaleDateString('he-IL')}\n---\nמערכת מילוי מקום`;

                // Send to teacher
                if (data.email) {
                    await sendEmail(
                        data.email,
                        `אישור דיווח היעדרות - ${data.teacher} - יום ${dayName}`,
                        `שלום ${data.teacher},\n\nהיעדרותך נקלטה במערכת:\n\n${body}`
                    );
                    console.log(`✅ Sent to teacher: ${data.email}`);
                }

                // Send to admin (fixed subject for threading)
                await sendEmail(
                    ADMIN_EMAIL,
                    'דיווחי היעדרות - מערכת מילוי מקום',
                    `📋 דיווח חדש:\n\n${body}`
                );
                console.log(`✅ Sent to admin: ${ADMIN_EMAIL}`);
            }

            // Delete processed
            await firebaseDelete(`/pendingEmails/${key}`);
            console.log(`🗑️ Deleted: ${key}`);

        } catch (err) {
            console.error(`❌ Error processing ${key}:`, err.message);
        }
    }
}

// ============ Daily WhatsApp Summary (runs from GitHub Actions) ============

const GREEN_API_URL = 'https://7103.api.greenapi.com';
const GREEN_API_INSTANCE = '7103493878';
const GREEN_API_TOKEN = process.env.GREEN_API_TOKEN || '';
const ADMIN_PHONE = '972526953500';

function sendWhatsApp(phone, message) {
    return new Promise((resolve, reject) => {
        const url = `${GREEN_API_URL}/waInstance${GREEN_API_INSTANCE}/sendMessage/${GREEN_API_TOKEN}`;
        const postData = JSON.stringify({ chatId: `${phone}@c.us`, message });
        const urlObj = new URL(url);
        const req = https.request(urlObj, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(postData, 'utf8') }
        }, res => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => resolve(data));
        });
        req.on('error', reject);
        req.write(postData, 'utf8');
        req.end();
    });
}

function firebasePut(path, data) {
    return new Promise((resolve, reject) => {
        const putData = JSON.stringify(data);
        const url = new URL(`${path}.json`, FIREBASE_URL);
        const req = https.request(url, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(putData, 'utf8') }
        }, res => {
            let d = '';
            res.on('data', chunk => d += chunk);
            res.on('end', () => resolve(d));
        });
        req.on('error', reject);
        req.write(putData, 'utf8');
        req.end();
    });
}

async function checkAndSendDailySummary() {
    const now = new Date();

    // Proper Israel time (handles DST UTC+2 winter / UTC+3 summer)
    const fmt = new Intl.DateTimeFormat('en-GB', {
        timeZone: 'Asia/Jerusalem', hour12: false,
        year: 'numeric', month: '2-digit', day: '2-digit',
        hour: '2-digit', weekday: 'short'
    });
    const parts = Object.fromEntries(fmt.formatToParts(now).map(p => [p.type, p.value]));
    const israelHour = parseInt(parts.hour, 10);
    const today = `${parts.year}-${parts.month}-${parts.day}`;
    const israelDay = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'].indexOf(parts.weekday);

    // Only send after 22:00 Israel time
    if (israelHour < 22) return;

    // הסיכום נשלח ב-22:00, אבל דיווחים ממשיכים להגיע גם אחריו. במקום לחסום
    // לגמרי אחרי השליחה הראשונה, שומרים חתימה של התוכן: אם משהו השתנה
    // בהמשך הערב — נשלח עדכון. בלי זה, מי שדיווח ב-22:22 לא הופיע בשום מייל.
    const sentFlag = await firebaseGet('/summaryFlags/' + today);
    const isUpdate = !!sentFlag;

    const tomorrow = (israelDay + 1) % 7;
    const targetDay = tomorrow;
    const label = 'למחר';

    // Skip if tomorrow is Shabbat (no school on Saturday)
    if (targetDay === 6) {
        console.log('Tomorrow is Shabbat, skipping summary');
        return;
    }
    // NOTE: Saturday night (after Shabbat ends, 22:00+) DOES send Sunday's summary.

    console.log(`Sending daily summary ${label} (day ${targetDay})...`);

    if (!GREEN_API_TOKEN) {
        console.log('No GREEN_API_TOKEN, skipping WhatsApp');
    }

    const absences = await firebaseGet('/absences');
    const dayName = DAY_NAMES[targetDay];

    // Trip classes for the target day - absences of a class that is on a trip
    // don't need a substitute and must NOT be counted as "לא שובצו"
    const allTrips = await firebaseGet('/tripClasses');
    const dayTrips = (allTrips && allTrips[targetDay]) || [];
    const tripClassNames = (Array.isArray(dayTrips) ? dayTrips : Object.values(dayTrips))
        .map(t => (t && typeof t === 'object') ? t.class : t)
        .filter(Boolean);
    const isClassOnTrip = cls => {
        if (!cls || tripClassNames.length === 0) return false;
        if (tripClassNames.includes(cls)) return true;
        return tripClassNames.includes(String(cls).replace(/[12]/g, ''));
    };

    const assigned = [], unassigned = [], merged = [];
    if (absences) {
        for (const key in absences) {
            const a = absences[key];
            if (a.day !== targetDay) continue;
            if (a.forNextWeek) continue; // report for NEXT week's occurrence - not tomorrow
            if (a.classAtHour && isClassOnTrip(a.classAtHour)) continue; // class on trip - no substitute needed
            if (a.merged) merged.push({ teacher: a.teacher, hour: a.hour });
            else if (a.substitute && a.substitute !== '') assigned.push({ teacher: a.teacher, hour: a.hour, substitute: a.substitute });
            else unassigned.push({ teacher: a.teacher, hour: a.hour });
        }
    }

    const total = assigned.length + unassigned.length + merged.length;

    // חתימת תוכן — כדי לזהות שינוי אחרי שהסיכום כבר נשלח
    const sig = JSON.stringify({
        d: targetDay,
        a: assigned.map(i => `${i.teacher}|${i.hour}|${i.substitute}`).sort(),
        u: unassigned.map(i => `${i.teacher}|${i.hour}`).sort(),
        m: merged.map(i => `${i.teacher}|${i.hour}`).sort(),
    });
    if (isUpdate && sentFlag.sig === sig) {
        console.log('Daily summary already sent and nothing changed');
        return;
    }
    if (isUpdate) console.log('Summary changed since it was sent — sending an update');

    const head = isUpdate ? `🔄 עדכון לסיכום ${label}` : `📊 סיכום ${label}`;
    let message;

    if (total === 0) {
        message = `${head} - יום ${dayName}\n\n✅ אין היעדרויות ${label}!`;
    } else {
        message = `${head} - יום ${dayName}\n`;
        message += '━━━━━━━━━━━━━━━\n\n';
        message += `📌 סה"כ היעדרויות: ${total}\n`;
        message += `✅ שובצו: ${assigned.length}\n`;
        message += `❌ לא שובצו: ${unassigned.length}\n`;
        message += `🔗 אוחדו: ${merged.length}\n\n`;
        if (assigned.length > 0) {
            message += '✅ *שובצו:*\n';
            assigned.forEach(i => { message += `  ${i.teacher} שעה ${i.hour} ← ${i.substitute}\n`; });
            message += '\n';
        }
        if (unassigned.length > 0) {
            message += '❌ *לא שובצו:*\n';
            unassigned.forEach(i => { message += `  ${i.teacher} שעה ${i.hour}\n`; });
            message += '\n';
        }
        if (merged.length > 0) {
            message += '🔗 *אוחדו:*\n';
            merged.forEach(i => { message += `  ${i.teacher} שעה ${i.hour}\n`; });
        }
    }

    // Send WhatsApp
    if (GREEN_API_TOKEN) {
        await sendWhatsApp(ADMIN_PHONE, message);
        console.log('WhatsApp summary sent');
    }

    // Queue email summary
    const emailKey = 'summary_' + Date.now();
    await firebasePut(`/pendingEmails/${emailKey}`, {
        email: ADMIN_EMAIL,
        subject: `${isUpdate ? '🔄 עדכון לסיכום' : '📊 סיכום'} מילוי מקום ${label} - יום ${dayName}`,
        reason: message,
        createdAt: Date.now()
    });
    console.log('Email summary queued');

    // נשמרת גם החתימה, כדי שרק שינוי אמיתי יפיק עדכון נוסף
    await firebasePut(`/summaryFlags/${today}`, { sent: true, time: now.toISOString(), sig });
    console.log('Daily summary completed');
}

// ============ Weekly Cleanup (Friday noon Israel time) ============

// Israel wall-clock parts (handles summer/winter time, unlike a fixed +2)
function israelParts(d) {
    const f = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Jerusalem', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', hour12: false, weekday: 'short' });
    const o = {}; for (const x of f.formatToParts(d)) o[x.type] = x.value;
    const wd = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'].indexOf(o.weekday);
    return { date: `${o.year}-${o.month}-${o.day}`, day: wd, hour: parseInt(o.hour, 10) % 24 };
}

// Most recent Friday 12:00 (Israel) that is <= now, as { weekKey, ts }
function lastFridayNoon(now) {
    for (let back = 0; back < 8; back++) {
        const cand = new Date(now.getTime() - back * 86400000);
        const p = israelParts(cand);
        if (p.day !== 5) continue;
        if (back === 0 && p.hour < 12) continue;
        // find the exact UTC ms of 12:00 Israel on that date
        let t = Date.UTC(+p.date.slice(0,4), +p.date.slice(5,7)-1, +p.date.slice(8,10), 9);
        while (israelParts(new Date(t)).hour !== 12) t += 3600000;
        return { weekKey: p.date, ts: t };
    }
    return null;
}

// GitHub's "every 5 min" cron really fires every few hours, so a narrow
// Friday window gets missed (6.11.26: runs at 11:28 and 18:53, nothing in 12-14).
// Instead: catch up any time after Friday noon until the week's cleanup is done.
// Reports created AFTER Friday noon belong to the new week and are kept.
async function checkAndRunWeeklyCleanup() {
    const now = new Date();
    const fri = lastFridayNoon(now);
    if (!fri) return;
    const weekKey = fri.weekKey;
    const cleanupFlag = await firebaseGet('/cleanupFlags/' + weekKey);
    if (cleanupFlag) return;

    console.log('Running weekly cleanup...');

    // Archive current data
    const absences = await firebaseGet('/absences');
    const tripClasses = await firebaseGet('/tripClasses');
    // new-week reports (made after Friday noon) are not part of the week being archived
    const toArchive = {};
    for (const k in (absences || {})) if ((absences[k].createdAt || 0) < fri.ts) toArchive[k] = absences[k];
    if (Object.keys(toArchive).length) await firebasePut(`/archived/${weekKey}/absences`, toArchive);
    if (tripClasses) await firebasePut(`/archived/${weekKey}/tripClasses`, tripClasses);
    console.log('Archived data');

    // Delete current data
    await firebaseDelete('/absences');
    await firebaseDelete('/tripClasses');
    await firebaseDelete('/tripExemptions');
    await firebaseDelete('/reminderDismissed');
    await firebaseDelete('/summaryFlags');
    console.log('Deleted old data');

    // Restore reports made for NEXT week - they become current-week reports
    if (absences) {
        for (const key in absences) {
            const a = absences[key];
            const newWeek = (a.createdAt || 0) >= fri.ts;
            if (!a.forNextWeek && !newWeek) continue;
            const restored = { ...a };
            delete restored.forNextWeek;
            await firebasePut(`/absences/${key}`, restored);
            console.log(`Restored next-week report: ${a.teacher} day ${a.day} hour ${a.hour}`);
        }
    }

    // Restore permanent absences
    const perms = await firebaseGet('/permanentAbsences');
    if (perms) {
        for (const key in perms) {
            const p = perms[key];
            const absKey = 'perm_' + p.teacher.replace(/\s/g, '_') + '_' + p.day + '_' + p.hour;
            await firebasePut(`/absences/${absKey}`, {
                teacher: p.teacher, day: p.day, hour: p.hour,
                reason: p.reason || 'היעדרות קבועה',
                permanent: true, reportedToMoshe: true,
                substitute: '', createdAt: Date.now()
            });
            console.log(`Restored permanent: ${p.teacher}`);
        }
    }

    // Mark cleanup as done
    await firebasePut(`/cleanupFlags/${weekKey}`, { done: true, time: now.toISOString() });
    console.log('Weekly cleanup completed!');
}

function firebaseDelete(path) {
    return new Promise((resolve, reject) => {
        const url = new URL(`${path}.json`, FIREBASE_URL);
        const req = https.request(url, { method: 'DELETE' }, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => resolve(data));
        });
        req.on('error', reject);
        req.end();
    });
}

// ============ Main ============

if (GMAIL_APP_PASSWORD === 'REPLACE_WITH_APP_PASSWORD') {
    console.error('❌ Set GMAIL_APP_PASSWORD first!');
    process.exit(1);
}

async function main() {
    await processPendingEmails();
    await checkAndSendDailySummary();
    await checkAndRunWeeklyCleanup();
    console.log('Done.');
}

main().then(() => process.exit(0)).catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
});
