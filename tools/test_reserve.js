// מילואים: הרב נריה, עם משה חיים נתן + אלי כממלאים קבועים
const puppeteer = require('C:/Users/user/node_modules/puppeteer');
const path = require('path');
const FILE = 'file:///' + path.resolve(__dirname, 'miluy-makom/index.html').split(path.sep).join('/');
const D = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי'];

(async () => {
  const b = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox'] });
  const p = await b.newPage();
  await p.setViewport({ width: 1280, height: 1200 });
  const errs = [];
  p.on('pageerror', e => errs.push(e.message));
  await p.goto(FILE, { waitUntil: 'networkidle2', timeout: 60000 });
  await new Promise(r => setTimeout(r, 2500));

  const r = await p.evaluate(() => {
    const T = 'הרב נריה';
    const SUBS = ['הרב משה חיים נתן', 'הרב אלי'];
    const plan = buildReservePlan(T, SUBS);
    // הזרקה בזיכרון בלבד — בלי כתיבה ל-Firebase
    reserveData = { [T]: { since: '2026-08-17', subs: SUBS,
                           lessons: plan.lessons, duties: plan.duties_plan } };
    populateReserveSelect(); updateReserve();
    document.querySelector('.nav-tab[data-page="reserve"]').click();
    return {
      lessons: plan.slots.map(s => ({ d: s.day, h: s.hour, cls: s.cls, who: plan.lessons[s.key] })),
      duties: plan.duties.map(x => ({ k: x.key, who: plan.duties_plan[x.key],
        able: SUBS.filter(s => canTakeDuty(s, x.key)),
        others: dutyCandidates(x.key).filter(c => !SUBS.includes(c)).slice(0, 3) })),
      lessonCount: plan.lessonCount, dutyCount: plan.dutyCount,
    };
  });

  console.log('=== שיעורים ===');
  r.lessons.forEach(x => console.log(`   ${D[x.d].padEnd(7)} שעה ${String(x.h).padEnd(5)} ${x.cls} → ${x.who || '❗ אף ממלא אינו פנוי'}`));
  console.log('   חלוקה:', JSON.stringify(r.lessonCount));
  console.log('\n=== תורנויות חצר ===');
  r.duties.forEach(x => console.log(`   ${x.k.padEnd(30)} → ${x.who || '❗ אף ממלא אינו יכול' + (x.others.length ? '  (אפשריים: ' + x.others.join(', ') + ')' : '')}`));
  console.log('   חלוקה:', JSON.stringify(r.dutyCount));
  await new Promise(r2 => setTimeout(r2, 600));
  await p.screenshot({ path: 'shot-reserve.png', fullPage: true });
  console.log('\nשגיאות:', errs.length ? errs.join('\n') : 'אין ✓');
  await b.close();
})();
