// בדיקת שני השינויים של 11.10:
//   1. תורנויות החצר יצאו מחישוב מילוי המקום (תקרה, חובות, הודעות)
//   2. המורה נועה והמורה טובי מוצעות תמיד, בכל שעה
const puppeteer = require('C:/Users/user/node_modules/puppeteer');
const path = require('path');
const FILE = 'file:///' + path.resolve(__dirname, '..', 'index.html').split(path.sep).join('/');

(async () => {
  // userDataDir טרי — פרופיל נעול מכשיל את ההרצה עם TimeoutError
  const b = await puppeteer.launch({
    headless: 'new',
    userDataDir: path.join(process.env.TEMP, 'pptr-focus-mm-' + Date.now()),
    args: ['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu',
           '--allow-file-access-from-files'],
    timeout: 90000
  });
  const p = await b.newPage();
  const errs = [];
  p.on('pageerror', e => errs.push(e.message));
  p.on('console', m => { if (m.type() === 'error') errs.push('console: ' + m.text()); });
  await p.goto(FILE, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await new Promise(r => setTimeout(r, 3000));

  const r = await p.evaluate(() => {
    const out = {};

    // --- התקרה: אף אחד לא על 0 בגלל תורנויות, והטקסט לא מזכיר חצר
    out.caps = allTeachers.map(t => {
      const n = capacityNote(t);
      return { t: t, cap: substCap(t), hours: weeklyHours(t),
               duties: yardDutyCount(t), text: n.text };
    });
    out.zeroCaps = out.caps.filter(c => c.cap === 0).map(c => c.t);
    out.yardInText = out.caps.filter(c => /תורנות|תורנויות|חצר/.test(c.text))
                             .map(c => c.t + ': ' + c.text);
    out.totalCapacity = out.caps.reduce((s, c) => s + (c.cap === null ? 0 : c.cap), 0);

    // הדוגמה שנבדקה קודם: צביקה, 3 תורנויות — עכשיו אמור לקבל מכסה מלאה
    out.zvika = out.caps.find(c => c.t === 'הרב צביקה');

    // --- החובות: הכיסוי נספר בלי תורנויות
    currentDay = 0;
    absencesData = {};
    const pairs = [['הרב אלי', 'הרב בני'], ['הרב נריה', 'הרב צביקה'],
                   ['הרב שמשון', 'הרב יעקב']];
    out.debts = pairs.map(function (pr) {
      const d = debtStatus(pr[0], pr[1]);
      return { pair: pr.join(' ← '), text: d ? d.text : null, owed: d ? d.owed : null };
    });
    out.yardInDebt = out.debts.filter(d => d.text && /תורנות|חצר/.test(d.text));

    // --- ההודעה למחליף
    out.msg = coverMessageWithDebt('הרב בני', 'הרב אלי', 0, '5', 'ד');
    out.yardInMsg = /תורנות|חצר/.test(out.msg);

    // --- נועה וטובי: מוצעות בכל שעה, בכל יום
    const hours = ['בוקר', '4', '5', '6', '7', '8', '9', '10', 'סדר ערב'];
    const miss = [];
    [0, 1, 2, 3, 4].forEach(function (day) {
      currentDay = day;
      hours.forEach(function (h) {
        const names = getTeachersAvailableAtHour(h).map(x => x.name);
        ['המורה נועה', 'המורה טובי'].forEach(function (n) {
          if (!names.includes(n)) miss.push(n + ' ' + day + '/' + h);
        });
      });
    });
    out.missingSlots = miss;
    out.inStaff = ['המורה נועה', 'המורה טובי'].filter(n => allTeachers.includes(n));

    // נעדרת בעצמה -> לא מוצעת (הגנה בסיסית)
    currentDay = 0;
    absencesData = { z: { teacher: 'המורה טובי', day: 0, hour: '5', reason: 'מחלה', substitute: '' } };
    out.toviBlockedWhenAbsent =
      !getTeachersAvailableAtHour('5').map(x => x.name).includes('המורה טובי');
    absencesData = {};

    // --- אין אזהרת "לוודא" על נועה
    out.noaPartialNag = isPartialData('המורה נועה');
    out.contactHtml = {
      noa: getContactButtonsHTML('המורה נועה', 'בדיקה'),
      tovi: getContactButtonsHTML('המורה טובי', 'בדיקה'),
      beni: getContactButtonsHTML('הרב בני', 'בדיקה').slice(0, 60)
    };
    // שיחות בלבד — אין להן הודעות כלל, לא SMS ולא ווטסאפ
    out.callOnly = ['המורה נועה', 'המורה טובי'].map(function (n) {
      const h = getContactButtonsHTML(n, 'בדיקה');
      return { t: n, phone: (teacherContacts[n] || {}).phone || null,
               call: /href="tel:/.test(h), sms: /href="sms:/.test(h),
               wa: /sendWaLinkToAdmin/.test(h) };
    });
    return out;
  });

  const bad = [];
  if (r.zeroCaps.length) bad.push('תקרה 0: ' + r.zeroCaps.join(', '));
  if (r.yardInText.length) bad.push('חצר בטקסט התקרה: ' + r.yardInText.join(' | '));
  if (r.yardInDebt.length) bad.push('חצר בחובות: ' + JSON.stringify(r.yardInDebt));
  if (r.yardInMsg) bad.push('חצר בהודעה: ' + r.msg);
  if (r.missingSlots.length) bad.push('חסרות במשבצות: ' + r.missingSlots.slice(0, 8).join(', '));
  if (r.inStaff.length !== 2) bad.push('לא בצוות: ' + JSON.stringify(r.inStaff));
  if (!r.toviBlockedWhenAbsent) bad.push('טובי מוצעת גם כשהיא נעדרת');
  if (r.noaPartialNag) bad.push('נועה עדיין מקפיצה אזהרת "לוודא"');
  r.callOnly.forEach(function (c) {
    if (!c.phone) bad.push(c.t + ': אין טלפון');
    if (!c.call) bad.push(c.t + ': אין כפתור שיחה');
    if (c.sms || c.wa) bad.push(c.t + ': מוצגת אפשרות הודעה (SMS/ווטסאפ) — אסור');
  });
  if (errs.length) bad.push('שגיאות דף: ' + errs.slice(0, 3).join(' | '));

  console.log('— תקרות —');
  r.caps.forEach(c => console.log('  ' + c.t + ' | ' + c.hours + ' ש"ש | ' +
    c.duties + ' תורנ׳ | תקרה ' + c.cap + ' | ' + c.text));
  console.log('סך יכולת מ"מ שבועית: ' + r.totalCapacity);
  console.log('צביקה: ' + JSON.stringify(r.zvika));
  console.log('\n— חובות —');
  r.debts.forEach(d => console.log('  ' + d.pair + ' → ' + d.text));
  console.log('\nהודעה: ' + r.msg);
  console.log('\nפרטי קשר נועה: ' + r.contactHtml.noa);
  console.log('פרטי קשר טובי: ' + r.contactHtml.tovi);
  console.log('פרטי קשר בני (ביקורת): ' + r.contactHtml.beni + '...');
  console.log('\n— ערוצי קשר (שיחות בלבד) —');
  r.callOnly.forEach(c => console.log('  ' + c.t + ' | ' + c.phone +
    ' | שיחה ' + (c.call ? '✓' : '✗') +
    ' | SMS ' + (c.sms ? '✗ מוצג!' : 'חסום ✓') +
    ' | ווטסאפ ' + (c.wa ? '✗ מוצג!' : 'חסום ✓')));
  console.log('\n' + (bad.length ? '✗ כשלים:\n  · ' + bad.join('\n  · ') : '✓ כל הבדיקות עברו'));

  await b.close();
  process.exit(bad.length ? 1 : 0);
})();
