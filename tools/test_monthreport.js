// דוח חודשי: שחזור תאריך (מקרי קצה), בורר חודש, והפקה מול נתונים אמיתיים
const puppeteer = require('C:/Users/user/node_modules/puppeteer');
const path = require('path');
const FILE = 'file:///' + path.resolve(__dirname, '..', 'index.html').split(path.sep).join('/');

(async () => {
  const b = await puppeteer.launch({
    headless: 'new',
    userDataDir: path.join(process.env.TEMP, 'pptr-mr-' + Date.now()),
    args: ['--no-sandbox', '--disable-gpu', '--allow-file-access-from-files'],
    timeout: 90000
  });
  const p = await b.newPage();
  const errs = [];
  p.on('pageerror', e => errs.push(e.message));
  await p.goto(FILE, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await new Promise(r => setTimeout(r, 3000));

  const r = await p.evaluate(() => {
    const out = {};

    // --- שחזור תאריך: מקרי הקצה שתוארו בהערת הקוד
    const mk = (y, m, d, h) => new Date(y, m - 1, d, h, 0, 0).getTime();
    const cases = [
      // דווח ראשון (0) על רביעי (3) אותו שבוע — בלי forNextWeek, +3 ימים
      { createdAt: mk(2026, 10, 25, 10), day: 3, forNextWeek: false,
        expect: '2026-10-28' },
      // דווח חמישי (4) על שני (1) שכבר עבר — forNextWeek=true, קופץ לשבוע הבא
      { createdAt: mk(2026, 10, 22, 10), day: 1, forNextWeek: true,
        expect: '2026-10-26' },
      // דווח שלישי (2) על שלישי עצמו (היום), לפני שעת הנעילה — ללא קפיצה
      { createdAt: mk(2026, 10, 20, 10), day: 2, forNextWeek: false,
        expect: '2026-10-20' },
      // דווח שלישי (2) על שלישי עצמו, אחרי שעת הנעילה — forNextWeek=true, +7
      { createdAt: mk(2026, 10, 20, 23), day: 2, forNextWeek: true,
        expect: '2026-10-27' },
    ];
    out.recon = cases.map(c => {
      const dt = reconstructAbsenceDate({ createdAt: c.createdAt, day: c.day, forNextWeek: c.forNextWeek });
      const got = dt ? `${dt.getFullYear()}-${String(dt.getMonth() + 1).padStart(2, '0')}-${String(dt.getDate()).padStart(2, '0')}` : null;
      return { ...c, got, ok: got === c.expect };
    });

    // --- בורר החודש: ניווט קדימה ואחורה
    navigateToPage('settings');
    renderMonthlyReportPicker();
    const label1 = document.querySelector('#monthly-report-picker strong').textContent;
    shiftMonthlyReport(-1);
    const label2 = document.querySelector('#monthly-report-picker strong').textContent;
    shiftMonthlyReport(1);
    const label3 = document.querySelector('#monthly-report-picker strong').textContent;
    out.picker = { label1, label2, label3, backToSame: label1 === label3, changed: label1 !== label2 };

    return out;
  });

  // --- הפקה בפועל מול הנתונים האמיתיים ב-Firebase (אוקטובר 2026)
  let liveReport = null, liveErr = null;
  try {
    liveReport = await p.evaluate(async () => {
      monthlyReportYM = { year: 2026, month: 10 };
      await buildMonthlyReport();
      const rowCount = document.querySelectorAll('#monthly-report-result tbody tr').length;
      const summary = document.querySelector('#monthly-report-result p')?.textContent || '';
      const hasCopyBtn = !!document.querySelector('#monthly-report-result button');
      const textLines = (monthlyReportText || '').split('\n').filter(Boolean).length;
      // כל שורה בטבלה חייבת תאריך בפורמט DD/MM
      const badDates = [...document.querySelectorAll('#monthly-report-result tbody tr td:first-child')]
        .map(td => td.textContent).filter(t => !/^\d{2}\/\d{2}$/.test(t));
      return { rowCount, summary, hasCopyBtn, textLines, badDates };
    });
  } catch (e) { liveErr = e.message; }

  const bad = [];
  r.recon.forEach(c => {
    if (!c.ok) bad.push(`שחזור תאריך שגוי: צפוי ${c.expect}, התקבל ${c.got} (day=${c.day}, fnw=${c.forNextWeek})`);
  });
  if (!r.picker.changed) bad.push('הבורר לא זז בלחיצת "חודש קודם"');
  if (!r.picker.backToSame) bad.push('הבורר לא חזר למקור אחרי קדימה-אחורה');
  if (liveErr) bad.push('הפקת דוח אמיתי נכשלה: ' + liveErr);
  else {
    if (!liveReport.rowCount) bad.push('אין שום שורה בדוח אוקטובר האמיתי — צפויות עשרות');
    else if (liveReport.rowCount < 50) bad.push('רק ' + liveReport.rowCount + ' שורות באוקטובר — פחות מהצפוי (93+)');
    if (!liveReport.hasCopyBtn) bad.push('אין כפתור העתקה');
    if (liveReport.badDates && liveReport.badDates.length)
      bad.push('תאריכים בפורמט שגוי: ' + liveReport.badDates.slice(0, 3).join(', '));
  }
  if (errs.length) bad.push('שגיאות דף: ' + errs.slice(0, 3).join(' | '));

  console.log('— שחזור תאריך —');
  r.recon.forEach(c => console.log('  ' + (c.ok ? '✓' : '✗') + ' day=' + c.day +
    ' fnw=' + c.forNextWeek + ' → ' + c.got + ' (צפוי ' + c.expect + ')'));
  console.log('\n— בורר חודש —');
  console.log('  ' + r.picker.label1 + ' → (קודם) ' + r.picker.label2 + ' → (הבא) ' + r.picker.label3);
  console.log('\n— דוח אוקטובר 2026 מול Firebase אמיתי —');
  if (liveErr) console.log('  נכשל: ' + liveErr);
  else console.log('  ' + liveReport.summary + ' | שורות בטבלה: ' + liveReport.rowCount +
    ' | שורות טקסט להעתקה: ' + liveReport.textLines);

  console.log('\n' + (bad.length ? '✗ כשלים:\n  · ' + bad.join('\n  · ') : '✓ כל הבדיקות עברו'));

  await b.close();
  process.exit(bad.length ? 1 : 0);
})();
