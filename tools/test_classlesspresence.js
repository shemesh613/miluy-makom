// שעות הדרכה (בלי כיתה) לא נשמרות כהיעדרות; הרב אורי פ. זמין ביום ראשון
const puppeteer = require('C:/Users/user/node_modules/puppeteer');
const path = require('path');
const FILE = 'file:///' + path.resolve(__dirname, '..', 'index.html').split(path.sep).join('/');

(async () => {
  const b = await puppeteer.launch({
    headless: 'new',
    userDataDir: path.join(process.env.TEMP, 'pptr-cp-' + Date.now()),
    args: ['--no-sandbox', '--disable-gpu', '--allow-file-access-from-files'],
    timeout: 90000
  });
  const p = await b.newPage();
  const errs = [];
  const dialogs = [];
  p.on('pageerror', e => errs.push(e.message));
  p.on('dialog', d => { dialogs.push(d.message()); d.dismiss().catch(() => {}); });
  await p.goto(FILE, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await new Promise(r => setTimeout(r, 3000));

  const r = await p.evaluate(() => {
    const out = {};

    // --- חגי, יום ראשון: שעה 6 אין לה כיתה, שעות 4/5/7/8/9 כן
    currentDay = 0;
    out.chagaiHour6Class = getTeacherClassAtHour('הרב חגי', 0, '6');
    out.chagaiHour4Class = getTeacherClassAtHour('הרב חגי', 0, '4');

    // --- כפתור "כל היום" מסנן את שעה 6 החוצה
    navigateToPage('report');
    document.getElementById('teacher-select').value = 'הרב חגי';
    document.getElementById('all-day-btn').click();
    const selected = [...document.querySelectorAll('.hour-btn.selected')].map(b => b.dataset.hour);
    out.allDaySelected = selected;
    out.allDayExcludesHour6 = !selected.includes('6');
    out.allDayIncludesHour4 = selected.includes('4');

    // --- שמירה ידנית: גם אם שעה 6 נבחרת ידנית, לא נשמרת
    document.querySelectorAll('.hour-btn').forEach(btn => btn.classList.remove('selected'));
    document.querySelector('.hour-btn[data-hour="6"]').classList.add('selected');
    document.querySelector('.hour-btn[data-hour="7"]').classList.add('selected');
    const sel2 = getSelectedHours();
    const filtered = sel2.filter(h => getTeacherClassAtHour('הרב חגי', 0, h));
    const classless = sel2.filter(h => !filtered.includes(h));
    out.manualFilter = { selected: sel2, kept: filtered, dropped: classless };

    // --- הרב אורי פ.: זמין ביום ראשון, כל השעות, בלי לפגוע בשאר השבוע
    out.uriDay0 = {
      worksToday: (teacherSchedule['הרב אורי פ.'].days || []).includes(0),
      hours0: teacherSchedule['הרב אורי פ.'].dayHours[0],
    };
    currentDay = 0;
    // מנקים היעדרויות אמיתיות שסונכרנו מ-Firebase — הבדיקה הזו בודקת את
    // המערכת הבסיסית שלו, לא את מצב הכיסוי הנוכחי בפועל.
    absencesData = {};
    const avail0 = getTeachersAvailableAtHour('5').map(t => t.name);
    out.uriAvailableSunday = avail0.includes('הרב אורי פ.');
    // כל 9 השעות פתוחות לו ביום ראשון
    const allHours = ['בוקר', '4', '5', '6', '7', '8', '9', '10', 'סדר ערב'];
    out.uriAllHoursSunday = allHours.every(h => getTeachersAvailableAtHour(h).map(t => t.name).includes('הרב אורי פ.'));

    // שאר השבוע שלו לא נפגע — שני עדיין אמור להראות כיתה אמיתית בשעה 4
    out.uriMondayIntact = (teacherSchedule['הרב אורי פ.'].dayHours[1] || []).includes('4') &&
      getTeacherClassAtHour('הרב אורי פ.', 1, '4') === 'ו';

    // נעדר בעצמו ביום ראשון -> לא אמור להיות מוצע (הגנה בסיסית, עדיין תקפה)
    currentDay = 0;
    absencesData = { z: { teacher: 'הרב אורי פ.', day: 0, hour: '5', reason: 'בדיקה', substitute: '' } };
    out.uriBlockedWhenAbsentSunday = !getTeachersAvailableAtHour('5').map(t => t.name).includes('הרב אורי פ.');
    absencesData = {};

    return out;
  });

  const bad = [];
  if (r.chagaiHour6Class) bad.push('לחגי בטעות יש כיתה בשעה 6: ' + r.chagaiHour6Class);
  if (!r.chagaiHour4Class) bad.push('לחגי חסרה כיתה אמיתית בשעה 4');
  if (!r.allDayExcludesHour6) bad.push('"כל היום" עדיין בוחר שעה 6 (הדרכה)');
  if (!r.allDayIncludesHour4) bad.push('"כל היום" לא בוחר שעה 4 (שיעור אמיתי)');
  if (r.manualFilter.kept.includes('6')) bad.push('בחירה ידנית: שעה 6 לא סוננה');
  if (!r.manualFilter.kept.includes('7')) bad.push('בחירה ידנית: שעה 7 (אמיתית) נמחקה בטעות');
  if (!r.uriDay0.worksToday) bad.push('אורי פ. עדיין לא מופיע כעובד ביום ראשון');
  if ((r.uriDay0.hours0 || []).length) bad.push('לאורי פ. יש "שיעורים" מדומים ביום ראשון: ' + JSON.stringify(r.uriDay0.hours0));
  if (!r.uriAvailableSunday) bad.push('אורי פ. לא מופיע כזמין ביום ראשון שעה 5');
  if (!r.uriAllHoursSunday) bad.push('אורי פ. לא זמין בכל 9 השעות ביום ראשון');
  if (!r.uriMondayIntact) bad.push('המערכת האמיתית של אורי פ. בשני נפגעה');
  if (!r.uriBlockedWhenAbsentSunday) bad.push('אורי פ. מוצע גם כשהוא עצמו נעדר ביום ראשון');
  if (errs.length) bad.push('שגיאות דף: ' + errs.slice(0, 3).join(' | '));

  console.log('— חגי, שעה 6 (הדרכה) מול שעה 4 (שיעור) —');
  console.log('  שעה 6: ' + (r.chagaiHour6Class || '(אין כיתה — נכון)'));
  console.log('  שעה 4: ' + r.chagaiHour4Class);
  console.log('\n— "כל היום" —');
  console.log('  נבחרו: ' + r.allDaySelected.join(', '));
  console.log('\n— בחירה ידנית —');
  console.log('  נבחרו: ' + r.manualFilter.selected.join(', ') +
    ' | נשמרות: ' + r.manualFilter.kept.join(', ') + ' | סוננו: ' + r.manualFilter.dropped.join(', '));
  console.log('\n— הרב אורי פ. ביום ראשון —');
  console.log('  עובד: ' + r.uriDay0.worksToday + ' | שעות הוראה: ' + JSON.stringify(r.uriDay0.hours0) +
    ' | זמין בכל השעות: ' + r.uriAllHoursSunday + ' | שני תקין: ' + r.uriMondayIntact);

  console.log('\n' + (bad.length ? '✗ כשלים:\n  · ' + bad.join('\n  · ') : '✓ כל הבדיקות עברו'));

  await b.close();
  process.exit(bad.length ? 1 : 0);
})();
