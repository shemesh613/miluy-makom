// בדיקת המערכת המעודכנת — ללא שום כתיבה ל-Firebase האמיתי (החיבור נחסם)
const puppeteer = require('C:/Users/user/node_modules/puppeteer');
const path = require('path');

const FILE = 'file:///' + path.resolve(__dirname, 'miluy-makom/index.html').replace(/\\/g, '/');

(async () => {
  const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox', '--lang=he'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 1000 });

  // הערה: הבדיקה קוראת בלבד — אין בה שום קריאה לפונקציית כתיבה,
  // ולכן היא לא נוגעת בנתוני האמת. (חסימת Firebase מפילה את ה-SDK בטעינה.)

  const errors = [];
  page.on('pageerror', e => errors.push('PAGEERROR: ' + e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push('CONSOLE: ' + m.text()); });

  await page.goto(FILE, { waitUntil: 'networkidle2', timeout: 60000 });
  await new Promise(r => setTimeout(r, 2500));

  // ---- בדיקות נתונים ----
  const data = await page.evaluate(() => ({
    teachers: Object.keys(teacherSchedule).length,
    duties: Object.keys(YARD_DUTY).length,
    subs: Object.keys(YARD_SUBS).length,
    mech: classMechanech,
    parallel: parallelClasses,
    year: BUILTIN_SCHEDULE_YEAR,
    override: activeScheduleInfo,
    sampleSchedule: teacherSchedule['הרב אלי'],
    tabs: [...document.querySelectorAll('.nav-tab')].map(b => b.textContent.trim()),
  }));
  console.log('== נתונים ==');
  console.log('מורים:', data.teachers, '| תורנויות:', data.duties, '| מפת מחליפים:', data.subs);
  console.log('שנה:', data.year, '| override פעיל:', data.override);
  console.log('מחנכים:', JSON.stringify(data.mech));
  console.log('מקבילות:', JSON.stringify(data.parallel));
  console.log('לשוניות:', data.tabs.join(' | '));

  // ---- תרחיש: הרב ינון נעדר ביום ראשון (יש לו תורנות 10:05 חצר) ----
  const scenario = await page.evaluate(() => {
    currentDay = 0;
    absencesData = {
      t1: { teacher: 'הרב ינון', day: 0, hour: 'בוקר', reason: 'מחלה', substitute: 'הרב צביקה' },
      t2: { teacher: 'הרב ינון', day: 0, hour: '4', reason: 'מחלה', substitute: 'הרב צביקה' },
    };
    const before = yardCoverPlan(0).filter(p => p.status !== 'ok')
      .map(p => ({ slot: p.slot, post: p.post, toran: p.toran, cover: p.cover, repay: p.repay, status: p.status }));

    // עכשיו גם המחליף הראשון נעדר — צריך ליפול למועמד הבא
    const first = before[0] && before[0].cover;
    if (first) {
      absencesData.t3 = { teacher: first, day: 0, hour: 'בוקר', reason: 'מחלה' };
      absencesData.t4 = { teacher: first, day: 0, hour: '4', reason: 'מחלה' };
    }
    const after = yardCoverPlan(0).filter(p => p.status !== 'ok')
      .map(p => ({ slot: p.slot, post: p.post, toran: p.toran, cover: p.cover, status: p.status }));

    // תרחיש קיצון: כל המועמדים נעדרים -> נפילה לממלא המקום
    const key = '10:05|ראשון|מגרש (למעלה)';
    const all = (YARD_SUBS[key].cands || []).map(c => c.name);
    all.forEach((nm, i) => {
      absencesData['x' + i] = { teacher: nm, day: 0, hour: 'בוקר' };
      absencesData['y' + i] = { teacher: nm, day: 0, hour: '4' };
    });
    const extreme = yardCoverPlan(0).find(p => p.key === key);

    absencesData = { t1: { teacher: 'הרב ינון', day: 0, hour: 'בוקר', reason: 'מחלה', substitute: 'הרב צביקה' },
                     t2: { teacher: 'הרב ינון', day: 0, hour: '4', reason: 'מחלה', substitute: 'הרב צביקה' } };
    updateAllViews();
    return { before, after, firstCand: first, allCands: all,
             extreme: { status: extreme.status, cover: extreme.cover } };
  });

  console.log('\n== תרחיש: הרב ינון נעדר ביום ראשון ==');
  console.log('דורש החלפה:', JSON.stringify(scenario.before, null, 1));
  console.log('\nכשגם', scenario.firstCand, 'נעדר →', JSON.stringify(scenario.after));
  console.log('\nכשכל המועמדים נעדרים (' + scenario.allCands.join(', ') + '):', JSON.stringify(scenario.extreme));

  await page.evaluate(() => document.querySelector('.nav-tab[data-page="yard"]').click());
  await new Promise(r => setTimeout(r, 600));
  await page.screenshot({ path: 'shot-yard.png', fullPage: true });

  await page.evaluate(() => document.querySelector('.nav-tab[data-page="substitute"]').click());
  await new Promise(r => setTimeout(r, 600));
  await page.screenshot({ path: 'shot-substitute.png', fullPage: true });

  console.log('\n== שגיאות ==');
  console.log(errors.length ? errors.slice(0, 12).join('\n') : 'אין ✓');
  await browser.close();
})();
