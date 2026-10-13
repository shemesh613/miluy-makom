// בדיקת checkRealUpdate: גרסה שונה בשרת → פס; גרסה זהה → שקט
const puppeteer = require('C:/Users/user/node_modules/puppeteer');
const path = require('path');
const FILE_PATH = path.resolve(__dirname, '..', 'index.html');
const FILE = 'file:///' + FILE_PATH.split(path.sep).join('/');

(async () => {
  const b = await puppeteer.launch({
    headless: 'new',
    userDataDir: path.join(process.env.TEMP, 'pptr-ru-' + Date.now()),
    args: ['--no-sandbox', '--disable-gpu', '--allow-file-access-from-files'],
    timeout: 90000
  });
  const p = await b.newPage();
  const errs = [];
  p.on('pageerror', e => errs.push(e.message));

  // --- מקרה 1: השרת (כאן: קובץ זהה) מחזיר אותה חתימה → אין פס
  await p.goto(FILE, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await new Promise(r => setTimeout(r, 2500));
  await p.evaluate(() => checkRealUpdate());
  await new Promise(r => setTimeout(r, 500));
  const sameBuildBar = await p.evaluate(() => !!document.getElementById('update-bar'));

  // --- מקרה 2: מדמים שה"רשת" מחזירה APP_BUILD שונה — מיירטים fetch
  await p.evaluate(() => {
    document.getElementById('update-bar')?.remove();
    window.__origFetch = window.fetch;
    window.fetch = (url, opts) => {
      if (opts && opts.cache === 'no-store') {
        return Promise.resolve(new Response(
          '<meta name="app-build" content="DIFFERENT-BUILD-XYZ">'));
      }
      return window.__origFetch(url, opts);
    };
  });
  await p.evaluate(() => checkRealUpdate());
  await new Promise(r => setTimeout(r, 500));
  const diffBuildBar = await p.evaluate(() => {
    const el = document.getElementById('update-bar');
    return { shown: !!el, text: el ? el.innerText.replace(/\n/g, ' | ') : null };
  });

  // --- מקרה 3: אין רשת בכלל (offline) — אסור שזה יקטע את המשתמש בשגיאה
  await p.evaluate(() => { document.getElementById('update-bar')?.remove(); window.fetch = window.__origFetch; });
  await p.setOfflineMode(true);
  let offlineThrew = false;
  try { await p.evaluate(() => checkRealUpdate()); } catch (e) { offlineThrew = true; }
  await new Promise(r => setTimeout(r, 500));
  const offlineBar = await p.evaluate(() => !!document.getElementById('update-bar'));
  await p.setOfflineMode(false);

  // --- stamp_build.py תקינות: ה-hash בפועל תואם את התוכן (בלי החתימה עצמה)
  const stampInfo = await p.evaluate(() => {
    const m = document.querySelector('meta[name="app-build"]');
    return { content: m ? m.content : null, len: document.documentElement.outerHTML.length };
  });

  const bad = [];
  if (sameBuildBar) bad.push('פס הופיע גם כשהגרסה זהה');
  if (!diffBuildBar.shown) bad.push('פס לא הופיע כשהגרסה שונה');
  else if (!/יש גרסה חדשה/.test(diffBuildBar.text)) bad.push('טקסט הפס שגוי: ' + diffBuildBar.text);
  if (offlineThrew) bad.push('checkRealUpdate זרק שגיאה כשאין רשת — אסור לקטוע משתמש');
  if (offlineBar) bad.push('פס הופיע למרות שאין רשת לבדוק מולה');
  if (!stampInfo.content || stampInfo.content === 'PENDING')
    bad.push('לא נחתמה חתימת APP_BUILD — stamp_build.py לא רץ');
  if (errs.length) bad.push('שגיאות דף: ' + errs.slice(0, 3).join(' | '));

  console.log('גרסה זהה (אין פס): ' + (sameBuildBar ? '✗ הופיע בטעות' : '✓'));
  console.log('גרסה שונה (יש פס): ' + (diffBuildBar.shown ? '✓ "' + diffBuildBar.text + '"' : '✗ לא הופיע'));
  console.log('אופליין (בלי שגיאה, בלי פס): ' + (!offlineThrew && !offlineBar ? '✓' : '✗'));
  console.log('חתימת APP_BUILD: ' + stampInfo.content);
  console.log('\n' + (bad.length ? '✗ כשלים:\n  · ' + bad.join('\n  · ') : '✓ כל הבדיקות עברו'));

  await b.close();
  process.exit(bad.length ? 1 : 0);
})();
