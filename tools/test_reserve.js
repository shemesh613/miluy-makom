// מצב מילואים — המקרה האמיתי של הרב נריה
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
    const T = 'הרב נריה';
    const slots = reserveSlots(T);
    const res = buildReservePlan(T, ['הרב משה חיים נתן', 'הרב אלי']);
    // האם משה חיים בכלל פנוי באיזו מהמשבצות של נריה?
    const mhAvail = slots.filter(s => freeAt('הרב משה חיים נתן', s.day, s.hour));
    const eliAvail = slots.filter(s => freeAt('הרב אלי', s.day, s.hour));
    return {
      total: slots.length, half: res.half, count: res.count,
      rows: slots.map(s => ({ d: s.day, h: s.hour, cls: s.cls, who: res.plan[s.key] })),
      mhAvail: mhAvail.map(s => D_[s.day] + ' ' + s.hour),
      eliAvail: eliAvail.map(s => D_[s.day] + ' ' + s.hour),
      gaps: slots.filter(s => !res.plan[s.key]).length,
    };
    function D_(i) { return ['ראשון','שני','שלישי','רביעי','חמישי','שישי'][i]; }
  }).catch(async e => {
    // D_ hoisting inside evaluate — fall back to a simpler probe
    return p.evaluate(() => {
      const T = 'הרב נריה';
      const DD = ['ראשון','שני','שלישי','רביעי','חמישי','שישי'];
      const slots = reserveSlots(T);
      const res = buildReservePlan(T, ['הרב משה חיים נתן', 'הרב אלי']);
      return {
        total: slots.length, half: res.half, count: res.count,
        rows: slots.map(s => ({ d: s.day, h: s.hour, cls: s.cls, who: res.plan[s.key] })),
        mhAvail: slots.filter(s => freeAt('הרב משה חיים נתן', s.day, s.hour)).map(s => DD[s.day] + ' ' + s.hour),
        eliAvail: slots.filter(s => freeAt('הרב אלי', s.day, s.hour)).map(s => DD[s.day] + ' ' + s.hour),
        gaps: slots.filter(s => !res.plan[s.key]).length,
      };
    });
  });

  console.log(`הרב נריה — ${r.total} שיעורים לכיסוי · תקרה לאדם: ${r.half} (מחצית)\n`);
  r.rows.forEach(x => console.log(`   ${D[x.d].padEnd(7)} שעה ${String(x.h).padEnd(5)} ${x.cls.padEnd(4)} → ${x.who || '❗ אין מועמד'}`));
  console.log('\nחלוקת העומס:', JSON.stringify(r.count, null, 0));
  console.log('משבצות ללא מחליף:', r.gaps);
  console.log('\nזמינות בפועל:');
  console.log('   הרב משה חיים נתן פנוי ב:', r.mhAvail.length ? r.mhAvail.join(' · ') : 'אף אחת ❗');
  console.log('   הרב אלי פנוי ב:', r.eliAvail.length ? r.eliAvail.join(' · ') : 'אף אחת');
  console.log('\nשגיאות:', errs.length ? errs.join('\n') : 'אין ✓');
  await b.close();
})();
