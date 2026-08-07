// בדיקה שערוצי הקשר המוגבלים מכובדים, ושמחנכי ז/ח לא שובצו לישיבת מחנכים
const puppeteer = require('C:/Users/user/node_modules/puppeteer');
const path = require('path');
const FILE = 'file:///' + path.resolve(__dirname, 'miluy-makom/index.html').split(path.sep).join('/');

(async () => {
  const b = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox'] });
  const p = await b.newPage();
  await p.goto(FILE, { waitUntil: 'networkidle2', timeout: 60000 });
  await new Promise(r => setTimeout(r, 2500));

  const res = await p.evaluate(() => {
    const chan = h => ({
      wa: h.includes('contact-whatsapp'), sms: h.includes('contact-sms'),
      call: h.includes('contact-call'), mail: h.includes('mailto:'),
    });
    const who = ['הרב ליאור (סייע)', 'הרב אורי אסייג (סייע)', 'הרב אביגדור',
                 'הרב חגי', 'הרב משה חיים נתן', 'המורה רבקי', 'הרב אלי'];
    const contacts = {};
    who.forEach(t => { contacts[t] = teacherContacts[t] ? chan(getContactButtonsHTML(t, 'x')) : 'אין פרטי קשר'; });

    // מחנכי ז/ח — האם ישיבת מחנכים (שלישי) נשארה בלי כיתה?
    const zc = dayHourClassesData['הרב אבי'], hc = dayHourClassesData['הרב יעקב'];
    return {
      contacts,
      missing: allTeachers.filter(t => !teacherContacts[t]),
      avi: { hours: teacherSchedule['הרב אבי'].dayHours[2], classes: zc[2] },
      yaakov: { hours: teacherSchedule['הרב יעקב'].dayHours[2], classes: hc[2] },
      aviClassesAllDays: teacherSchedule['הרב אבי'].dayClasses,
      // מי מלמד ח בשעה 5 ביום ראשון — נדרש להצעת איחוד ז+ח
      teacherOfHet: getTeacherOfClassAtHour('ח', 0, '5'),
      teacherOfZayin: getTeacherOfClassAtHour('ז', 0, '5'),
    };
  });
  console.log(JSON.stringify(res, null, 1));
  await b.close();
})();
