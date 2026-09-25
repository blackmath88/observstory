// Connector readability check (issue: dense real repos). Usage: node prototypes/project-map/measure-wires.js page.html ...
// For each page: how many connectors are drawn, how many share an endpoint with another at the same point (fans),
// and how many edges end on a collapsed card. Fails on console errors.
const path = require('path');
let chromium; try { ({ chromium } = require('playwright')); } catch { ({ chromium } = require('/opt/node22/lib/node_modules/playwright')); }
(async () => {
  const b = await chromium.launch(); const out = {};
  for (const f of process.argv.slice(2)) {
    const p = await b.newPage({ viewport: { width: 1440, height: 900 } }); const errors = [];
    p.on('pageerror', e => errors.push(String(e)));
    await p.goto('file://' + path.resolve(f)); await p.waitForTimeout(250);
    out[path.basename(f)] = await p.evaluate(() => {
      const paths = [...document.querySelectorAll('#wires g[data-id] path.wire, #wires g[data-bundle] path.wire')];
      const starts = {}; for (const q of paths) { const d = q.getAttribute('d'); const pts = d.match(/-?[\d.]+,-?[\d.]+/g); for (const pt of [pts[0], pts[pts.length-1]]) { const k = pt.split(',').map(v => Math.round(+v / 4)).join(','); starts[k] = (starts[k] || 0) + 1; } }
      const maxFan = Math.max(0, ...Object.values(starts));
      const scene = JSON.parse(document.getElementById('scene').textContent);
      const hidden = id => { const e = document.getElementById('n-' + id); return !e || !!e.closest('details:not([open])'); };
      const toHidden = scene.edges.filter(e => hidden(e.from) || hidden(e.to)).length;
      return {edges: scene.edges.length, drawn: paths.length, max_fan: maxFan, edges_to_collapsed: toHidden,
              bundles: document.querySelectorAll('#wires g[data-bundle]').length};
    });
    out[path.basename(f)].errors = errors.length; await p.close();
  }
  console.log(JSON.stringify(out, null, 0).replace(/},/g, '},\n')); await b.close();
})();
