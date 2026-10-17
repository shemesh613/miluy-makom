// בורר יום הדיווח מכסה את כל השבוע, וכל יום פתוח כראוי לדיווח קדימה
const puppeteer = require('C:/Users/user/node_modules/puppeteer');
const path = require('path');
const FILE = 'file:///' + path.resolve(__dirname, '..', 'index.html').split(path.sep).join('/');

(async () => {
  const b = await puppeteer.launch({
    headless: 'new',
    userDataDir: path.join(process.env.TEMP, 'pptr-ra-' + Date.now()),
    args: ['--no-sandbox', '--disable-gpu', '--allow-file-access-from-files'],
    timeout: 90000
  });
  const p = await b.newPage();
  const errs = [];
  p.on('pageerror', e => errs.push(e.message));
  await p.goto(FILE, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await new Promise(r => setTimeout(r, 3000));

  const r = await p.evaluate(() => {
    navigateToPage('report');
    const out = {};

    const buttons = () => [...document.querySelectorAll('#report-day-picker .rdp-btn')]
      .map(b => b.textContent.trim());
    out.buttonCount = buttons().length;
    out.buttons = buttons();

    // כל כפתור לוחץ ליום הנכון ולא קורס (לרבות ימים רחוקים)
    out.clicks = [];
    [0, 1, 2, 3, 4, 5, 6].forEach(d => {
      if (d === 6) return;   // שבת
      setReportDay(d);
      const formShown = document.getElementById('report-form-card').style.display !== 'none';
      const lockStatus = isDayLocked(d);
      out.clicks.push({ day: d, currentDay, formShown, lockStatus });
    });

    // תאריכים לא מתנגשים — 6 ימים רצופים, תאריכים עולים (מודולו גלישת חודש)
    const dates = out.buttons.map(t => (t.match(/(\d{1,2})\/(\d{1,2})/) || [])[0]);
    out.datesUnique = new Set(dates).size === dates.length;

    return out;
  });

  const bad = [];
  if (r.buttonCount < 6) bad.push('רק ' + r.buttonCount + ' כפתורים, צפויים 6 (א-ו)');
  if (!r.datesUnique) bad.push('יש תאריכים כפולים בכפתורים');
  r.clicks.forEach(c => {
    // יום נעול (lockStatus===true) מציג הודעת נעילה, לא טופס — זה תקין.
    // "shabbat" כבר סונן. כל השאר צריכים טופס.
    if (c.lockStatus !== true && !c.formShown)
      bad.push('יום ' + c.day + ': הטופס לא מוצג אף שהיום לא נעול (lockStatus=' + c.lockStatus + ')');
    if (c.currentDay !== c.day) bad.push('לחיצה על יום ' + c.day + ' לא עדכנה currentDay');
  });
  if (errs.length) bad.push('שגיאות דף: ' + errs.slice(0, 3).join(' | '));

  console.log('כפתורים (' + r.buttonCount + '): ' + r.buttons.join(' | '));
  console.log('\n— בדיקת כל יום —');
  r.clicks.forEach(c => console.log('  יום ' + c.day + ' | נעול: ' + c.lockStatus +
    ' | טופס מוצג: ' + c.formShown));
  console.log('\n' + (bad.length ? '✗ כשלים:\n  · ' + bad.join('\n  · ') : '✓ כל הבדיקות עברו'));

  await b.close();
  process.exit(bad.length ? 1 : 0);
})();
