// Screenshot helper for build.py: node shot.js page.html out.png width height [clickSelector]
// Fails on any console error, so a broken page never ships a screenshot.
const path = require('path');
let chromium;
try { ({ chromium } = require('playwright')); } catch { ({ chromium } = require('/opt/node22/lib/node_modules/playwright')); }
(async () => {
  const [page_, out, w, h, click] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: +w, height: +h }, deviceScaleFactor: 2 });
  const errors = [];
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('pageerror', e => errors.push(String(e)));
  await page.goto('file://' + path.resolve(page_));
  await page.waitForTimeout(300);
  if (click) { await page.click(click); await page.waitForTimeout(250); }
  await page.screenshot({ path: out });
  await browser.close();
  if (errors.length) { console.error(errors.join('\n')); process.exit(1); }
  console.log('shot', path.basename(out));
})();
