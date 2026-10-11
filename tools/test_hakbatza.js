// בדיקת ההקבצות: אליהו שמשון ⇄ סימון בז׳ ובח׳
const puppeteer = require('C:/Users/user/node_modules/puppeteer');
const path = require('path');
const FILE = 'file:///' + path.resolve(__dirname, '..', 'index.html').split(path.sep).join('/');
const D = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי'];

(async () => {
  const b = await puppeteer.launch({
    headless: 'new',
    userDataDir: path.join(process.env.TEMP, 'pptr-hak-t-' + Date.now()),
    args: ['--no-sandbox', '--disable-gpu', '--allow-file-access-from-files'],
    timeout: 90000
  });
  const p = await b.newPage();
  const errs = [];
  p.on('pageerror', e => errs.push(e.message));
  await p.goto(FILE, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await new Promise(r => setTimeout(r, 3000));

  const r = await p.evaluate(() => {
    const D_ = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי'];
    const out = { slots: [], cases: [] };

    // כל המשבצות שבהן השניים על אותה כיתה בו-זמנית
    const pair = ['הרב אליהו שמשון', 'הרב סימון'];
    [0, 1, 2, 3, 4].forEach(function (d) {
      ['בוקר', '4', '5', '6', '7', '8', '9', '10', 'סדר ערב'].forEach(function (h) {
        const hk = hakbatzaPartner(pair[0], d, h);
        if (hk) out.slots.push({ day: d, hour: h, cls: hk.cls, partner: hk.teacher });
      });
    });

    // לכל משבצת: מדווחים על אחד מהם ובודקים מה המערכת מציעה
    out.slots.forEach(function (s) {
      pair.forEach(function (absent) {
        currentDay = s.day;
        const id = 'test1';
        absencesData = {};
        absencesData[id] = { teacher: absent, day: s.day, hour: s.hour,
                             reason: 'בדיקה', substitute: '', classAtHour: s.cls };
        updateMergeSuggestions();
        const el = document.getElementById('merge-suggestions-scroll');
        const txt = el ? el.innerText.replace(/\s+/g, ' ').trim() : '';
        const other = pair.find(t => t !== absent);
        out.cases.push({
          when: D_[s.day] + ' ש' + s.hour + ' ' + s.cls, absent: absent,
          expectHost: other,
          hasHakbatza: /שתי ההקבצות/.test(txt),
          namesOther: txt.indexOf(other) > -1,
          adjacentNoise: /מצטרפת לכיתה|כיתות ו|כיתות ח \+/.test(txt),
          cards: el ? el.querySelectorAll('.merge-card').length : 0,
          txt: txt.slice(0, 190)
        });
      });
    });

    // ההודעה שנשלחת בפועל
    const s0 = out.slots[0];
    currentDay = s0.day;
    out.msg = mergeMessages({ teacher: 'הרב אליהו שמשון', hour: s0.hour,
                              absentClass: s0.cls, parallelClass: s0.cls,
                              coveringTeacher: 'הרב סימון', isHakbatza: true }).host;

    // התווית אחרי אישור
    out.label = mergedLabel({ merged: true, mergedClass: 'ז', hakbatza: true });
    out.labelPlain = mergedLabel({ merged: true, mergedClass: 'ג' });

    // שעה שבה הם *לא* באותה הקבצה — אסור שתוצע
    out.notPartner = hakbatzaPartner('הרב אליהו שמשון', 1, '9');   // ו מול ה1

    absencesData = {};
    return out;
  });

  const bad = [];
  if (r.slots.length !== 8) bad.push('צפויות 8 משבצות הקבצה, נמצאו ' + r.slots.length);
  if (r.notPartner) bad.push('שני ש9 (ו מול ה1) זוהה בטעות כהקבצה');
  r.cases.forEach(function (c) {
    if (!c.hasHakbatza) bad.push(c.when + ' / ' + c.absent + ': אין הצעת הקבצה — ' + c.txt);
    else if (!c.namesOther) bad.push(c.when + ' / ' + c.absent + ': ההצעה לא נוקבת ב' + c.expectHost);
    if (c.adjacentNoise) bad.push(c.when + ' / ' + c.absent + ': נשאר רעש של כיתה סמוכה');
  });
  if (!/שתי ההקבצות/.test((r.msg || {}).msg || '')) bad.push('ההודעה אינה מדברת על הקבצות');
  if (r.label !== 'שתי ההקבצות של ז') bad.push('תווית שגויה: ' + r.label);
  if (r.labelPlain !== 'ג1+ג2') bad.push('תווית רגילה נשברה: ' + r.labelPlain);
  if (errs.length) bad.push('שגיאות דף: ' + errs.slice(0, 3).join(' | '));

  console.log('— משבצות הקבצה (' + r.slots.length + ') —');
  r.slots.forEach(s => console.log('  ' + D[s.day] + ' שעה ' + s.hour + ' · כיתה ' + s.cls));
  console.log('\n— מה המערכת מציעה —');
  r.cases.forEach(c => console.log('  ' + (c.hasHakbatza ? '✓' : '✗') + ' ' + c.when +
    ' | נעדר ' + c.absent + ' → ' + c.cards + ' הצעות | ' + c.txt.slice(0, 110)));
  console.log('\nהודעה: ' + ((r.msg || {}).msg || '—'));
  console.log('תווית: ' + r.label + '   |   תווית רגילה: ' + r.labelPlain);
  console.log('\n' + (bad.length ? '✗ כשלים:\n  · ' + bad.slice(0, 10).join('\n  · ')
                                 : '✓ כל הבדיקות עברו'));

  await b.close();
  process.exit(bad.length ? 1 : 0);
})();
