/**
 * Daily Summary for GitHub Actions
 * Sends WhatsApp + Email summary of tomorrow's absences
 */

const https = require('https');
const nodemailer = require('nodemailer');

const FIREBASE_URL = 'https://moria-1d5c0-default-rtdb.europe-west1.firebasedatabase.app';
const GREEN_API_URL = 'https://7103.api.greenapi.com';
const GREEN_API_INSTANCE = '7103493878';
const GREEN_API_TOKEN = process.env.GREEN_API_TOKEN || '';
const ADMIN_PHONE = '972526953500';
const ADMIN_EMAIL = 'shemesh613@gmail.com';
const GMAIL_APP_PASSWORD = process.env.GMAIL_APP_PASSWORD || '';
const DAY_NAMES = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי', 'שבת'];

function httpGet(url) {
  return new Promise((resolve, reject) => {
    https.get(url, res => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try { resolve(JSON.parse(data)); } catch (e) { resolve(null); }
      });
    }).on('error', reject);
  });
}

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

async function sendEmail(subject, body) {
  if (!GMAIL_APP_PASSWORD) { console.log('No Gmail password, skipping email'); return; }
  const transporter = nodemailer.createTransport({
    service: 'gmail',
    auth: { user: ADMIN_EMAIL, pass: GMAIL_APP_PASSWORD }
  });
  await transporter.sendMail({
    from: `"מערכת מילוי מקום" <${ADMIN_EMAIL}>`,
    to: ADMIN_EMAIL,
    subject,
    text: body
  });
}

async function main() {
  const now = new Date();
  const today = now.getDay();
  // In Israel it's UTC+2/+3, cron runs at 19:30 UTC = 22:30 Israel
  // Calculate tomorrow based on Israel time
  const israelHour = now.getUTCHours() + 2; // IST approximate
  const tomorrow = (today + (israelHour >= 22 ? 1 : 0)) % 7;
  // Actually, since cron runs at 19:30 UTC = ~22:30 Israel, today in UTC might be same day
  // The cron only runs Sun-Thu (0-4 UTC), matching Israel Sun-Thu evenings
  const actualTomorrow = (today + 1) % 7;

  console.log(`Running daily summary. UTC day: ${today}, tomorrow: ${actualTomorrow}`);

  if (actualTomorrow === 6) {
    console.log('Tomorrow is Shabbat, skipping');
    return;
  }

  const absences = await httpGet(`${FIREBASE_URL}/absences.json`);
  const dayName = DAY_NAMES[actualTomorrow];

  if (!absences) {
    const msg = `📊 סיכום למחר - יום ${dayName}\n\nאין היעדרויות במערכת למחר.`;
    await sendWhatsApp(ADMIN_PHONE, msg);
    await sendEmail(`📊 סיכום מילוי מקום - יום ${dayName}`, msg);
    console.log('No absences, sent notification');
    return;
  }

  const assigned = [], unassigned = [], merged = [];
  for (const key in absences) {
    const a = absences[key];
    if (a.day !== actualTomorrow) continue;
    if (a.merged) merged.push({ teacher: a.teacher, hour: a.hour });
    else if (a.substitute && a.substitute !== '') assigned.push({ teacher: a.teacher, hour: a.hour, substitute: a.substitute });
    else unassigned.push({ teacher: a.teacher, hour: a.hour });
  }

  const total = assigned.length + unassigned.length + merged.length;

  if (total === 0) {
    const msg = `📊 סיכום למחר - יום ${dayName}\n\n✅ אין היעדרויות למחר!`;
    await sendWhatsApp(ADMIN_PHONE, msg);
    await sendEmail(`✅ סיכום מילוי מקום - יום ${dayName}`, msg);
    console.log('No absences for tomorrow');
    return;
  }

  let message = `📊 סיכום למחר - יום ${dayName}\n`;
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

  await sendWhatsApp(ADMIN_PHONE, message);

  // Email summary
  let emailBody = `סה"כ היעדרויות: ${total}\n`;
  emailBody += `✅ שובצו: ${assigned.length}\n❌ לא שובצו: ${unassigned.length}\n🔗 אוחדו: ${merged.length}\n\n`;
  if (unassigned.length > 0) {
    emailBody += 'לא שובצו:\n';
    unassigned.forEach(i => { emailBody += `• ${i.teacher} שעה ${i.hour}\n`; });
    emailBody += '\n';
  }
  if (assigned.length > 0) {
    emailBody += 'שובצו:\n';
    assigned.forEach(i => { emailBody += `• ${i.teacher} שעה ${i.hour} ← ${i.substitute}\n`; });
  }
  await sendEmail(`📊 סיכום מילוי מקום למחר - יום ${dayName}`, emailBody + '\n---\nמערכת מילוי מקום');

  console.log(`Summary sent: ${total} absences (WhatsApp + Email)`);
}

main().then(() => process.exit(0)).catch(err => { console.error('Error:', err); process.exit(1); });
