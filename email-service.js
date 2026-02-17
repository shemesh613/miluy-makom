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

// Run
if (GMAIL_APP_PASSWORD === 'REPLACE_WITH_APP_PASSWORD') {
    console.error('❌ Set GMAIL_APP_PASSWORD first!');
    console.log('1. Go to: https://myaccount.google.com/apppasswords');
    console.log('2. Create app password for "Mail"');
    console.log('3. Replace REPLACE_WITH_APP_PASSWORD in this file');
    process.exit(1);
}

processPendingEmails().then(() => {
    console.log('Done.');
    process.exit(0);
}).catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
});
