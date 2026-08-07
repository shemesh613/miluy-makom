// האם באמת אף מחנך אינו פנוי בשעת ישיבת המחנכים (שלישי שעה 7)?
const puppeteer = require('C:/Users/user/node_modules/puppeteer');
const path = require('path');
const FILE = 'file:///' + path.resolve(__dirname, 'miluy-makom/index.html').split(path.sep).join('/');

(async () => {
  const b = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox'] });
  const p = await b.newPage();
  await p.goto(FILE, { waitUntil: 'networkidle2', timeout: 60000 });
  await new Promise(r => setTimeout(r, 2500));

  const res = await p.evaluate(() => {
    const mech = [...new Set(Object.values(classMechanech))];
    const busyAt = (t, d, h) => {
      const s = teacherSchedule[t];
      return !!(s && s.dayHours && s.dayHours[d] && s.dayHours[d].includes(h));
    };
    const worksOn = (t, d) => {
      const s = teacherSchedule[t];
      return !!(s && s.days && s.days.includes(d));
    };
    // שלישי = יום 2
    const atMeeting = mech.map(t => ({
      name: t, day2: worksOn(t, 2),
      h7: busyAt(t, 2, '7'), h8: busyAt(t, 2, '8'),
      class7: (dayHourClassesData[t] && dayHourClassesData[t][2]) ? dayHourClassesData[t][2]['7'] || null : null,
    }));

    // מי בכלל פנוי בשלישי שעה 7 (מתוך כל הצוות)
    const freeAt7 = Object.keys(teacherSchedule)
      .filter(t => worksOn(t, 2) && !busyAt(t, 2, '7'))
      .map(t => ({ name: t, isMechanech: mech.includes(t) }));

    // תורנויות של שלישי שהתורן בהן הוא מחנך
    const tueDuties = Object.keys(YARD_DUTY).filter(k => k.split('|')[1] === 'שלישי')
      .map(k => ({ key: k, toran: YARD_DUTY[k], isMechanech: mech.includes(YARD_DUTY[k]) }));

    return { mechCount: mech.length, atMeeting, freeAt7, tueDuties };
  });

  console.log('=== 13 המחנכים בשלישי ===');
  res.atMeeting.forEach(m => console.log(
    `  ${m.name.padEnd(20)} עובד:${m.day2 ? 'כן' : 'לא'}  תפוס ב-7:${m.h7 ? 'כן' : 'לא '}  תפוס ב-8:${m.h8 ? 'כן' : 'לא '}  כיתה ב-7:${m.class7 || '—'}`));
  console.log('\n=== פנויים בשלישי שעה 7 ===');
  res.freeAt7.forEach(f => console.log(`  ${f.name}${f.isMechanech ? '   ⚠️ מחנך!' : ''}`));
  console.log('\n=== תורנויות שלישי ===');
  res.tueDuties.forEach(d => console.log(`  ${d.key.padEnd(30)} ${d.toran}${d.isMechanech ? '  (מחנך)' : ''}`));
  await b.close();
})();

// בדיקת רשת הביטחון: מערכת שהועלתה שבה מחנך "שכח" את שעת הישיבה
(async () => {
  const b = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox'] });
  const p = await b.newPage();
  await p.goto(FILE, { waitUntil: 'networkidle2', timeout: 60000 });
  await new Promise(r => setTimeout(r, 2500));
  const r = await p.evaluate(() => {
    const victim = 'הרב שלומי';
    const fake = JSON.parse(JSON.stringify(builtinTeacherSchedule));
    fake[victim].dayHours[2] = fake[victim].dayHours[2].filter(h => h !== '7');
    const before = [...fake[victim].dayHours[2]];
    applyScheduleOverride({ teacherSchedule: fake, dayHourClasses: builtinDayHourClasses,
                            classMechanech: builtinClassMechanech,
                            fileName: 'בדיקה.xlsx', updatedAt: Date.now() });
    const after = [...teacherSchedule[victim].dayHours[2]];
    applyScheduleOverride(null);
    return { before, after, restored: teacherSchedule[victim].dayHours[2].includes('7') };
  });
  console.log('\n=== רשת ביטחון: מחנך שנשמט מהישיבה בקובץ שהועלה ===');
  console.log('  לפני האכיפה:', r.before.join(','));
  console.log('  אחרי האכיפה:', r.after.join(','), r.after.includes('7') ? '✅ שעה 7 הוחזרה' : '❌ נכשל');
  console.log('  אחרי חזרה למובנית:', r.restored ? '✅ תקין' : '❌ נכשל');
  await b.close();
})();
