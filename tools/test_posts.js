const puppeteer=require('C:/Users/user/node_modules/puppeteer');const path=require('path');
const FILE='file:///'+path.resolve(__dirname,'miluy-makom/index.html').split(path.sep).join('/');
(async()=>{const b=await puppeteer.launch({headless:'new',args:['--no-sandbox']});const p=await b.newPage();
const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.goto(FILE,{waitUntil:'networkidle2',timeout:60000});await new Promise(r=>setTimeout(r,2500));
const r=await p.evaluate(()=>{
  const posts=[...new Set(Object.keys(YARD_DUTY).map(k=>k.split('|')[2]))];
  const check=[
    ['10:20|שני|דשא (למטה)','הרב בישמוט'],['12:10|שלישי|דשא (למטה)','הרב בישמוט'],
    ['11:20|רביעי|דשא (למטה)','הרב בישמוט'],['10:20|שלישי|דשא (למטה)','הרב צבי'],
    ['10:20|רביעי|דשא (למטה)','הרב צבי'],['10:20|חמישי|דשא (למטה)','הרב צבי'],
    ['10:20|שישי|דשא (למטה)','הרב צבי'],['12:10|ראשון|דשא (למטה)','לאה'],
    ['12:10|חמישי|מגרש (למעלה)',"שרה תורג'מן"]];
  // האם מישהו מהם עדיין מופיע במגרש?
  const stray=Object.entries(YARD_DUTY).filter(([k,v])=>
    ['הרב צבי','הרב בישמוט'].includes(v)&&k.split('|')[2]==='מגרש (למעלה)');
  return {posts,
    rows:check.map(([k,want])=>({k,got:YARD_DUTY[k]||'—',ok:YARD_DUTY[k]===want})),
    stray, total:Object.keys(YARD_DUTY).length};});
console.log('עמדות:',r.posts.join(' | '),'| תורנויות:',r.total);
console.log('\n=== 9 השינויים ===');
r.rows.forEach(x=>console.log(` ${x.ok?'✓':'✗'} ${x.k} → ${x.got}`));
console.log('\nצבי/בישמוט שנשארו במגרש (צריך 0):',r.stray.length, r.stray.map(s=>s[0]).join(', '));
console.log('שגיאות:',errs.length?errs.join('\n'):'אין ✓');
await b.close()})();
