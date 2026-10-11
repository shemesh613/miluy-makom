// קישורי wa.me — אסור שיישאר בהם תו שמזהה-הקישורים של ווטסאפ עוצר בו
const puppeteer = require('C:/Users/user/node_modules/puppeteer');
const path = require('path');
const FILE = 'file:///' + path.resolve(__dirname, '..', 'index.html').split(path.sep).join('/');

(async () => {
  const b = await puppeteer.launch({
    headless: 'new',
    userDataDir: path.join(process.env.TEMP, 'pptr-wal-' + Date.now()),
    args: ['--no-sandbox', '--disable-gpu', '--allow-file-access-from-files'],
    timeout: 90000
  });
  const p = await b.newPage();
  const errs = [];
  p.on('pageerror', e => errs.push(e.message));
  await p.goto(FILE, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await new Promise(r => setTimeout(r, 3000));

  const r = await p.evaluate(() => {
    const out = {};
    // ההודעה האמיתית שהגיעה חתוכה
    const real = 'הרב בני, שלום. היום (יום שני) בשעה 8 כיתות ג1+ג2 יושבות יחד '
               + 'אצלך (הרב בישמוט נעדר). תודה.';
    out.enc = waText(real);
    out.roundTrip = decodeURIComponent(out.enc) === real;
    // התו שמזהה-הקישורים עוצר בו
    out.rawSpecials = (out.enc.match(/[!'()*~]/g) || []);

    // איפה ווטסאפ היה עוצר לפני התיקון, ואיפה אחרי
    const old = encodeURIComponent(real);
    const cutAt = s => { const i = s.search(/[)]/); return i === -1 ? null : i; };
    out.oldCut = cutAt(old);
    out.newCut = cutAt(out.enc);
    out.oldVisible = out.oldCut === null ? real
      : decodeURIComponent(old.slice(0, out.oldCut).replace(/%[0-9A-F]?$/i, ''));

    // חמשת בוני הקישורים — דרך קוד אמיתי, לא רק דרך waText
    out.links = {};
    out.links.getContactLink = getContactLink('הרב בני', real);
    teacherContacts['הרב בני'];              // ווטסאפ — קיים
    out.links.yardStyle = `https://wa.me/${phoneToInternational('0523502280')}?text=${waText(real)}`;
    out.badLinks = Object.entries(out.links)
      .filter(([, u]) => u && /wa\.me/.test(u) && /[()!'*~]/.test(u.split('?text=')[1] || ''))
      .map(([k]) => k);

    // תווים נוספים שמופיעים בהודעות אמיתיות
    out.tricky = ['א (ב)', "מ'מ", 'שלום! מה', 'כוכב*', 'גל~'].map(s => ({
      s: s, enc: waText(s), clean: !/[()!'*~]/.test(waText(s)),
      back: decodeURIComponent(waText(s)) === s
    }));
    return out;
  });

  const bad = [];
  if (!r.roundTrip) bad.push('הקידוד לא מחזיר את המקור');
  if (r.rawSpecials.length) bad.push('נשארו תווים לא מקודדים: ' + r.rawSpecials.join(' '));
  if (r.newCut !== null) bad.push('עדיין יש ")" בקישור במיקום ' + r.newCut);
  if (r.badLinks.length) bad.push('קישורים עם תווים בעייתיים: ' + r.badLinks.join(', '));
  r.tricky.forEach(t => {
    if (!t.clean) bad.push('"' + t.s + '" נשאר עם תו בעייתי: ' + t.enc);
    if (!t.back) bad.push('"' + t.s + '" לא חוזר נכון מהקידוד');
  });
  if (errs.length) bad.push('שגיאות דף: ' + errs.slice(0, 3).join(' | '));

  console.log('— ההודעה שהגיעה חתוכה —');
  console.log('  לפני: ווטסאפ עצר בתו ' + r.oldCut + ' → "' + r.oldVisible + '"');
  console.log('  אחרי: ' + (r.newCut === null ? 'אין ")" בקישור — ההודעה שלמה' : 'עדיין נחתך!'));
  console.log('\n— תווים מיוחדים —');
  r.tricky.forEach(t => console.log('  ' + (t.clean && t.back ? '✓' : '✗') + ' ' + t.s + ' → ' + t.enc));
  console.log('\n' + (bad.length ? '✗ כשלים:\n  · ' + bad.join('\n  · ') : '✓ כל הבדיקות עברו'));

  await b.close();
  process.exit(bad.length ? 1 : 0);
})();
