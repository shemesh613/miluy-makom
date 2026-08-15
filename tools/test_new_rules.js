// בדיקת שני הכללים החדשים: חסימה אישית (הרב ינון) וכלל ההצלבה
const puppeteer = require('C:/Users/user/node_modules/puppeteer');
const path = require('path');
const FILE = 'file:///' + path.resolve(__dirname, 'miluy-makom/index.html').split(path.sep).join('/');
const D = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי'];

(async () => {
  const b = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox'] });
  const p = await b.newPage();
  const errs = [];
  p.on('pageerror', e => errs.push(e.message));
  await p.goto(FILE, { waitUntil: 'networkidle2', timeout: 60000 });
  await new Promise(r => setTimeout(r, 2500));

  const r = await p.evaluate(() => {
    const t = teacherSchedule['הרב ינון'];
    const blocked = t.days.map(d => ({
      day: d, h4: t.dayHours[d].includes('4'), h5: t.dayHours[d].includes('5'),
      cls4: (dayHourClassesData['הרב ינון'][d] || {})['4'] || null,
    }));

    // האם ינון עדיין מוצע כפנוי בשעות 4/5?
    const freeSomewhere = t.days.filter(d =>
      !t.dayHours[d].includes('4') || !t.dayHours[d].includes('5'));

    // כלל הצלבה: ינון נעדר בראשון, והמחליף שנבחר לתורנות שלו
    // כבר שובץ למלא מקום בשעה צמודה
    currentDay = 0;
    absencesData = {
      a1: { teacher: 'הרב ינון', day: 0, hour: 'בוקר', reason: 'מחלה', substitute: '' },
    };
    const before = yardCoverPlan(0).find(x => x.status !== 'ok');
    const chosen = before && before.cover;

    // עכשיו אותו אדם משובץ למלא מקום בשעה 'בוקר' (צמודה ל-10:05)
    absencesData.a2 = { teacher: 'הרב פורת', day: 0, hour: 'בוקר', reason: 'מחלה', substitute: chosen };
    const after = yardCoverPlan(0).find(x => x.status !== 'ok' && x.toran === 'הרב ינון');

    absencesData = {};
    return {
      blocked, freeSomewhere,
      chosenBefore: chosen,
      chosenAfter: after && after.cover,
      changed: chosen !== (after && after.cover),
      personalReason: personalBlockReason('הרב ינון', '4'),
    };
  });

  console.log('=== 3. חסימה אישית — הרב ינון שעות 4–5 ===');
  console.log('   סיבה בקוד:', r.personalReason);
  r.blocked.forEach(x => console.log(
    `   ${D[x.day].padEnd(7)} שעה4 תפוס=${x.h4 ? '✓' : '✗'}  שעה5 תפוס=${x.h5 ? '✓' : '✗'}  (שיעור בשעה4: ${x.cls4 || '—'})`));
  console.log('   ימים שבהם עדיין פנוי ב-4 או 5 (צריך: אין):', r.freeSomewhere.length ? r.freeSomewhere.map(d => D[d]) : 'אין ✓');

  console.log('\n=== 7. כלל הצלבה ===');
  console.log('   מחליף שנבחר לתורנות:', r.chosenBefore);
  console.log('   אחרי שאותו אדם שובץ למלא מקום בשעה צמודה →', r.chosenAfter);
  console.log('  ', r.changed ? '✓ המערכת בחרה מישהו אחר' : '✗ נשאר אותו אדם — כשל');
  console.log('\nשגיאות:', errs.length ? errs.join('\n') : 'אין ✓');
  await b.close();
})();
