// שני ש7 — אליהו שמשון מלמד ח. ובנוסף: חסימות אישיות שורדות העלאת קובץ.
const puppeteer = require('C:/Users/user/node_modules/puppeteer');
const path = require('path');
const FILE = 'file:///' + path.resolve(__dirname, '..', 'index.html').split(path.sep).join('/');

(async () => {
  const b = await puppeteer.launch({
    headless: 'new',
    userDataDir: path.join(process.env.TEMP, 'pptr-sf-' + Date.now()),
    args: ['--no-sandbox', '--disable-gpu', '--allow-file-access-from-files'],
    timeout: 90000
  });
  const p = await b.newPage();
  const errs = [];
  p.on('pageerror', e => errs.push(e.message));
  await p.goto(FILE, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await new Promise(r => setTimeout(r, 3000));

  const r = await p.evaluate(() => {
    const T = 'הרב אליהו שמשון', DAY = 1, H = '7';
    const out = {};

    out.cls = ((dayHourClassesData[T] || {})[DAY] || {})[H] || null;
    out.inHours = (teacherSchedule[T].dayHours[DAY] || []).includes(H);
    out.inDayClasses = (teacherSchedule[T].dayClasses[DAY] || []).includes('ח');
    out.viaApi = getTeacherClassAtHour(T, DAY, H);

    // אף שעה אחרת שלו לא נשארה בלי כיתה
    out.stillClassless = [];
    [0, 1, 2, 3, 4].forEach(function (d) {
      const cc = (dayHourClassesData[T] || {})[d] || {};
      (teacherSchedule[T].dayHours[d] || []).forEach(function (h) {
        if (!cc[h]) out.stillClassless.push(d + '/' + h);
      });
    });

    // אף אחד אחר לא על ח באותה שעה
    out.clash = Object.entries(dayHourClassesData)
      .filter(([t, days]) => t !== T && ((days || {})[DAY] || {})[H] === 'ח')
      .map(([t]) => t);

    // כשהוא נעדר שם — יש מה לכסות, והכיתה מופיעה
    currentDay = DAY;
    absencesData = { s1: { teacher: T, day: DAY, hour: H, reason: 'בדיקה', substitute: '' } };
    out.absenceClass = getTeacherClassAtHour(T, DAY, H);
    out.candidates = getTeachersAvailableAtHour(H).length;
    absencesData = {};

    // 🔴 החסימות האישיות אחרי החלת קובץ שהועלה
    const blocksBefore = ['הרב ינון', 'הרב פורת', 'הרב שלומי'].map(n => ({
      t: n, h: JSON.stringify(teacherSchedule[n].dayHours) }));
    // מדמים העלאה: אותה מערכת בדיוק, דרך המסלול של הקובץ
    applyScheduleOverride({
      fileName: 'בדיקה.xlsx', updatedAt: Date.now(),
      teacherSchedule: JSON.parse(JSON.stringify(builtinTeacherSchedule)),
      dayHourClasses: JSON.parse(JSON.stringify(builtinDayHourClasses)),
      classMechanech: JSON.parse(JSON.stringify(builtinClassMechanech))
    });
    out.afterUpload = {
      fixKept: ((dayHourClassesData[T] || {})[DAY] || {})[H] || null,
      yinon4: (teacherSchedule['הרב ינון'].dayHours[0] || []).includes('4'),
      yinon5: (teacherSchedule['הרב ינון'].dayHours[0] || []).includes('5'),
      shlomi7: (teacherSchedule['הרב שלומי'].dayHours[0] || []).includes('7'),
      poratBoker: (teacherSchedule['הרב פורת'].dayHours[0] || []).includes('בוקר')
    };
    out.blocksBefore = blocksBefore.length;
    return out;
  });

  const bad = [];
  if (r.cls !== 'ח') bad.push('שני ש7 אינו ח אלא ' + r.cls);
  if (!r.inHours) bad.push('שעה 7 אינה ברשימת השעות של שני');
  if (!r.inDayClasses) bad.push('ח אינה ב-dayClasses של שני');
  if (r.viaApi !== 'ח') bad.push('getTeacherClassAtHour מחזיר ' + r.viaApi);
  if (r.stillClassless.length) bad.push('נשארו שעות בלי כיתה: ' + r.stillClassless.join(', '));
  if (r.clash.length) bad.push('מלמד נוסף על ח באותה שעה: ' + r.clash.join(', '));
  if (r.absenceClass !== 'ח') bad.push('בהיעדרות הכיתה אינה מזוהה');
  if (!r.candidates) bad.push('אין מועמדים לכיסוי שני ש7');
  if (r.afterUpload.fixKept !== 'ח') bad.push('התיקון נמחק אחרי העלאת קובץ');
  if (!r.afterUpload.yinon4 || !r.afterUpload.yinon5)
    bad.push('חסימת ינון 4–5 נמחקה אחרי העלאת קובץ');
  if (!r.afterUpload.shlomi7) bad.push('חסימת שלומי שעה 7 נמחקה אחרי העלאת קובץ');
  if (!r.afterUpload.poratBoker) bad.push('חסימת פורת בוקר נמחקה אחרי העלאת קובץ');
  if (errs.length) bad.push('שגיאות דף: ' + errs.slice(0, 3).join(' | '));

  console.log('— שני שעה 7, הרב אליהו שמשון —');
  console.log('  כיתה: ' + r.cls + ' | בשעות: ' + r.inHours +
              ' | ב-dayClasses: ' + r.inDayClasses + ' | מועמדים לכיסוי: ' + r.candidates);
  console.log('  שעות שנשארו בלי כיתה בכל השבוע: ' +
              (r.stillClassless.length ? r.stillClassless.join(', ') : 'אין'));
  console.log('  התנגשות עם מלמד אחר: ' + (r.clash.length ? r.clash.join(', ') : 'אין'));
  console.log('\n— אחרי העלאת קובץ מערכת —');
  console.log('  התיקון נשמר: ' + (r.afterUpload.fixKept === 'ח' ? '✓' : '✗'));
  console.log('  ינון 4–5 חסום: ' + (r.afterUpload.yinon4 && r.afterUpload.yinon5 ? '✓' : '✗'));
  console.log('  שלומי ש7 חסום: ' + (r.afterUpload.shlomi7 ? '✓' : '✗'));
  console.log('  פורת בוקר חסום: ' + (r.afterUpload.poratBoker ? '✓' : '✗'));
  console.log('\n' + (bad.length ? '✗ כשלים:\n  · ' + bad.join('\n  · ') : '✓ כל הבדיקות עברו'));

  await b.close();
  process.exit(bad.length ? 1 : 0);
})();
