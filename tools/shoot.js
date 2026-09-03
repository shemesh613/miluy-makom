// מצלם כל דף כ-A3 לרוחב מדויק, ומכוונן את הזום כך שהתוכן ימלא את העמוד
// בלי לגלוש — כך הכתב גדול ככל האפשר ושום תא לא נחתך.
const puppeteer = require('C:/Users/user/node_modules/puppeteer');
const path = require('path');

const W = 1587, H = 1123, SCALE = 2;   // A3 לרוחב ב-96dpi, ×2 לחדות

const PAGES = [
  ['chart_classes.html', 'maarechet-by-class-A3.png'],
  ['chart_teachers_1.html', 'maarechet-by-teacher-A3-p1.png'],
  ['chart_teachers_2.html', 'maarechet-by-teacher-A3-p2.png'],
];

(async () => {
  const b = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox', '--font-render-hinting=none'] });
  for (const [src, out] of PAGES) {
    const p = await b.newPage();
    await p.setViewport({ width: W, height: H, deviceScaleFactor: SCALE });
    await p.goto('file:///' + path.resolve(__dirname, src).split(path.sep).join('/'),
                 { waitUntil: 'networkidle0', timeout: 60000 });

    // התכנסות: כל סבב מודד מחדש, כי הזום משנה את אריזת העמודות
    let zoom = 1;
    for (let i = 0; i < 8; i++) {
      const h = await p.evaluate(z => {
        document.body.style.zoom = z;
        return document.documentElement.scrollHeight;
      }, zoom);
      const ratio = (H - 4) / h;
      if (ratio > 0.99 && ratio <= 1.0) break;
      zoom = Math.max(0.4, Math.min(1.8, zoom * ratio));
    }
    const final = await p.evaluate(() => document.documentElement.scrollHeight);
    console.log(`${src}: זום ${zoom.toFixed(3)} → ${final}px מתוך ${H}px ${final <= H ? '✓' : '⚠️'}`);

    await p.screenshot({ path: out, clip: { x: 0, y: 0, width: W, height: H } });
    await p.close();
  }
  await b.close();
})();
