// אימות עדכון 14.8 מול הישן: זמינות, הדרכה/גנים, ותורנות
const puppeteer = require('C:/Users/user/node_modules/puppeteer');
const path = require('path');
const FILE = 'file:///' + path.resolve(__dirname, 'miluy-makom/index.html').split(path.sep).join('/');
const D = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי'];

(async () => {
  const b = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox'] });
  const p = await b.newPage();
  const errs = [];
  p.on('pageerror', e => errs.push('PAGEERROR: ' + e.message));
  await p.goto(FILE, { waitUntil: 'networkidle2', timeout: 60000 });
  await new Promise(r => setTimeout(r, 2500));

  const r = await p.evaluate(() => {
    const has = (t, d, h) => {
      const s = teacherSchedule[t];
      return !!(s && s.dayHours && s.dayHours[d] && s.dayHours[d].includes(h));
    };
    const cls = (t, d, h) => (dayHourClassesData[t] && dayHourClassesData[t][d]) ? (dayHourClassesData[t][d][h] || null) : null;
    const days = t => (teacherSchedule[t] || {}).days || [];
    return {
      stamp: new Date(BUILTIN_SCHEDULE_STAMP).toISOString().slice(0, 10),
      // 1. שרה תורג'מן — לא בביה"ס בראשון
      saraDays: days("שרה תורג'מן"),
      saraSun: has("שרה תורג'מן", 0, '5'),
      saraThu5: has("שרה תורג'מן", 4, '5'),
      // 2. שלומי — גנים שעה 6 כל יום: תפוס אך בלי כיתה
      shlomi6: [0, 1, 2, 3, 4].map(d => ({ d, busy: has('הרב שלומי', d, '6'), cls: cls('הרב שלומי', d, '6') })),
      // 3. הדרכה שני שעה 4 — אביגדור, בישמוט, משה
      hadracha4: ['הרב אביגדור', 'הרב בישמוט', 'הרב משה']
        .map(t => ({ t, busy: has(t, 1, '4'), cls: cls(t, 1, '4') })),
      // 4. הדרכה ראשון שעה 6 — אביגדור, נריה, ינון, חגי
      hadracha6: ['הרב אביגדור', 'הרב נריה', 'הרב ינון', 'הרב חגי']
        .map(t => ({ t, busy: has(t, 0, '6'), cls: cls(t, 0, '6') })),
      // 5. תורנות: שתי השורות שהשתנו
      duty: {
        saraSun1210: YARD_DUTY['12:10|ראשון|מסדרון ונספחיו'],
        saraThu1210corr: YARD_DUTY['12:10|חמישי|מסדרון ונספחיו'],
        saraThu1210yard: YARD_DUTY['12:10|חמישי|חצר'],
      },
      // 6. שינויי כיתות שהוזכרו
      avigdorSun5: cls('הרב אביגדור', 0, '5'),        // נביא ב1 עבר לראשון שעה 5
      bishmutSun6: cls('הרב בישמוט', 0, '6'),         // טבע ו2 ראשון שעה 6
      yuvalWed6: cls('הרב יובל', 3, '6'),             // התעמלות ה2 רביעי שעה 6
      inonWed7: cls('הרב ינון', 3, '7'),              // עברית ו2 רביעי שעה 7
      totalTeachers: Object.keys(teacherSchedule).length,
    };
  });

  const yn = v => v ? '✓' : '✗';
  console.log('חותמת מערכת מובנית:', r.stamp, '| מלמדים:', r.totalTeachers);
  console.log("\n1. שרה תורג'מן — ימים:", r.saraDays.map(d => D[d]).join(','),
    '| ראשון שעה 5:', yn(!r.saraSun) + ' (צריך: לא)',
    '| חמישי שעה 5:', yn(r.saraThu5) + ' (צריך: כן)');
  console.log('\n2. הרב שלומי — גנים שעה 6 (צריך: תפוס, בלי כיתה):');
  r.shlomi6.forEach(x => console.log(`   ${D[x.d]}: תפוס=${yn(x.busy)} כיתה=${x.cls || '— ✓'}`));
  console.log('\n3. הדרכה שני שעה 4 (צריך: תפוס, בלי כיתה):');
  r.hadracha4.forEach(x => console.log(`   ${x.t}: תפוס=${yn(x.busy)} כיתה=${x.cls || '— ✓'}`));
  console.log('\n4. הדרכה ראשון שעה 6 (צריך: תפוס, בלי כיתה):');
  r.hadracha6.forEach(x => console.log(`   ${x.t}: תפוס=${yn(x.busy)} כיתה=${x.cls || '— ✓'}`));
  console.log('\n5. תורנות שהשתנו:');
  console.log("   ראשון 12:10 מסדרון:", r.duty.saraSun1210, '(צריך: לאה)');
  console.log("   חמישי 12:10 מסדרון:", r.duty.saraThu1210corr, "(צריך: שרה תורג'מן)");
  console.log('   חמישי 12:10 חצר:', r.duty.saraThu1210yard);
  console.log('\n6. שיעורים שזזו:');
  console.log('   אביגדור ראשון 5 =', r.avigdorSun5, '(צריך ב1)');
  console.log('   בישמוט ראשון 6 =', r.bishmutSun6, '(צריך ו2)');
  console.log('   יובל רביעי 6 =', r.yuvalWed6, '(צריך ה2)');
  console.log('   ינון רביעי 7 =', r.inonWed7, '(צריך ו2)');
  console.log('\nשגיאות:', errs.length ? errs.join('\n') : 'אין ✓');
  await b.close();
})();
