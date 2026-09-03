// שלוש התוספות: עדיפות שעות חלון · מעבר ליום הבא אחרי 22:30 · סרגל מתכווץ
const puppeteer = require('C:/Users/user/node_modules/puppeteer');
const path = require('path');
const FILE = 'file:///' + path.resolve(__dirname, 'miluy-makom/index.html').split(path.sep).join('/');
const D = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי', 'שבת'];

async function open(browser, fakeHour) {
  const p = await browser.newPage();
  await p.setViewport({ width: 1280, height: 900 });
  if (fakeHour !== undefined) {
    // מזייפים את שעון ישראל כדי לבדוק את חוק ה-22:30
    await p.evaluateOnNewDocument(h => {
      const R = Intl.DateTimeFormat;
      Intl.DateTimeFormat = function (loc, opt) {
        const f = new R(loc, opt);
        if (opt && opt.timeZone === 'Asia/Jerusalem') {
          const orig = f.formatToParts.bind(f);
          f.formatToParts = d => orig(d).map(p =>
            p.type === 'hour' ? { ...p, value: String(h).padStart(2, '0') }
            : p.type === 'minute' ? { ...p, value: '45' } : p);
        }
        return f;
      };
      Intl.DateTimeFormat.supportedLocalesOf = R.supportedLocalesOf;
    }, fakeHour);
  }
  const errs = [];
  p.on('pageerror', e => errs.push(e.message));
  await p.goto(FILE, { waitUntil: 'networkidle2', timeout: 60000 });
  await new Promise(r => setTimeout(r, 2200));
  return { p, errs };
}

(async () => {
  const b = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox'] });

  // ---- 1. עדיפות שעות חלון ----
  {
    const { p, errs } = await open(b);
    const r = await p.evaluate(() => {
      const out = {};
      [0, 1, 2, 3, 4].forEach(d => out[d] = windowHours('הרב אליהו שמשון', d));
      currentDay = 3; updateAllViews();
      const { optional } = calculateAvailableTeachers();
      const idx = optional.findIndex(o => o.name === 'הרב אליהו שמשון');
      return { windows: out, idx, total: optional.length,
               entry: optional[idx], first3: optional.slice(0, 3).map(o => o.name) };
    });
    console.log('=== 1. הרב אליהו שמשון — שעות חלון ===');
    Object.entries(r.windows).forEach(([d, w]) => console.log(`   ${D[d].padEnd(7)} ${w.length ? w.join(', ') : '— אין חלון'}`));
    console.log(`   ברביעי: מקום ${r.idx + 1} מתוך ${r.total} · ${r.entry ? r.entry.reason : '—'} · שעות ${r.entry ? r.entry.hours.join(',') : ''}`);
    console.log('   שלושת הראשונים:', r.first3.join(' · '));
    console.log('   שגיאות:', errs.length ? errs.join('; ') : 'אין ✓');
    await p.close();
  }

  // ---- 2. מעבר ליום הבא ----
  for (const [h, label] of [[20, 'לפני 22:30'], [23, 'אחרי 22:30']]) {
    const { p, errs } = await open(b, h);
    const r = await p.evaluate(() => {
      const info = activeDayInfo();
      const notice = document.getElementById('auto-day-notice');
      return { current: currentDay, advanced: autoDayAdvanced, infoDay: info.day,
               notice: notice.style.display !== 'none' ? notice.textContent.trim().slice(0, 70) : '(מוסתר)',
               flashing: !!document.querySelector('.day-btn.day-flash') };
    });
    console.log(`\n=== 2. שעה ${h}:45 (${label}) ===`);
    console.log(`   יום פעיל: ${D[r.current]} | עבר אוטומטית: ${r.advanced ? 'כן' : 'לא'} | מהבהב: ${r.flashing ? 'כן' : 'לא'}`);
    console.log(`   הודעה: ${r.notice}`);
    console.log('   שגיאות:', errs.length ? errs.join('; ') : 'אין ✓');
    await p.close();
  }

  // ---- 3. סרגל מתכווץ ----
  {
    const { p, errs } = await open(b);
    const r = await p.evaluate(async () => {
      const bar = document.querySelector('.top-bar');
      const before = bar.getBoundingClientRect().height;
      window.scrollTo(0, 400); window.dispatchEvent(new Event('scroll'));
      await new Promise(r => setTimeout(r, 400));
      const scrolled = bar.getBoundingClientRect().height;
      toggleDock();                       // חזרה למצב מלא ידנית
      await new Promise(r => setTimeout(r, 400));
      const manual = bar.getBoundingClientRect().height;
      return { before: Math.round(before), scrolled: Math.round(scrolled),
               manual: Math.round(manual), saved: localStorage.getItem('dockState') };
    });
    console.log('\n=== 3. הסרגל הצף ===');
    console.log(`   גובה בראש הדף: ${r.before}px`);
    console.log(`   אחרי גלילה:    ${r.scrolled}px  ${r.scrolled < r.before ? '✓ התכווץ' : '✗ לא התכווץ'}`);
    console.log(`   אחרי לחיצה:    ${r.manual}px  (נשמר: ${r.saved})`);
    console.log('   שגיאות:', errs.length ? errs.join('; ') : 'אין ✓');
    await p.close();
  }

  await b.close();
})();
