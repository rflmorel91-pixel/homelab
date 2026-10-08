const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm'), assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../..');
const html = fs.readFileSync(path.join(root, 'app/prestamodesk-administracion.html'), 'utf8');
const filename = html.match(/src="\/assets\/(prestamodesk-portfolio-import-[a-f0-9]+\.js)"/)[1];
const source = fs.readFileSync(path.join(root, 'app/assets', filename), 'utf8');
function setup(fetch) {
  const elements = new Map(), events = new Map();
  function node() {return {listeners: {}, children: [], hidden: false, disabled: false, checked: false, value: '', files: [], addEventListener(k, fn) {this.listeners[k] = fn;}, replaceChildren(...v) {this.children = v;}, append(v) {this.children.push(v);}, click() {}, reset() {}};}
  const get = id => {if (!elements.has(id)) elements.set(id, node()); return elements.get(id);};
  const client = {tenant_id: 4, role: 'owner'};
  const context = {document: {getElementById: get, createElement: node}, window: {prestamodeskAccess: client, addEventListener: (key, fn) => events.set(key, fn)}, fetch, URL: {createObjectURL: () => 'blob:fake', revokeObjectURL() {}}, Blob, setTimeout: fn => fn(), encodeURIComponent};
  vm.createContext(context); vm.runInContext(source, context);
  get('importFile').files = [{size: 100, text: async () => 'example CSV'}]; get('importCutoff').value = '2026-10-08';
  return {get, events, submit: () => get('portfolioImportForm').listeners.submit({preventDefault() {}}), save: () => get('importSave').listeners.click()};
}
const review = {valid: true, fingerprint: 'f'.repeat(64), cutoff_date: '2026-10-08', loan_count: 1, installment_count: 2, opening_balance: '9900.00', historical_paid: '1100.00', loans: [{reference: '<script>unsafe</script>', borrower: 'Ana', borrower_action: 'Crear prestatario', total_due: '11000', historical_paid: '1100', opening_balance: '9900'}], errors: []};
const okay = data => ({ok: true, json: async () => data});
(async () => {
  let calls = 0, saved;
  const a = setup(async (url, options) => {calls++; assert.equal(options.headers['X-Tenant-ID'], '4'); if (url.endsWith('/preview')) return okay(review); saved = JSON.parse(options.body); return okay({...review, import_id: 1, replayed: false});});
  await a.submit(); assert.equal(calls, 1); assert.equal(a.get('importSave').disabled, true);
  assert.equal(a.get('importRows').children[0].children[0].textContent, '<script>unsafe</script>');
  await a.save(); assert.equal(calls, 1);
  a.get('importConfirm').checked = true; a.get('importConfirm').listeners.change(); await a.save();
  assert.equal(calls, 2); assert.equal(saved.confirm_balances, true); assert.equal(saved.csv_text, 'example CSV'); assert.equal(saved.fingerprint, review.fingerprint); assert.equal(a.get('importSave').disabled, true);
  let submits = 0, resolve;
  const b = setup(async url => {if (url.endsWith('/preview')) return okay(review); submits++; return new Promise(r => {resolve = r;});});
  await b.submit(); b.get('importConfirm').checked = true; const first = b.save(); await b.save(); assert.equal(submits, 1);
  resolve(okay({...review, import_id: 2})); await first;
  let payloads = [];
  const c = setup(async (url, options) => {if (url.endsWith('/preview')) return okay(review); payloads.push(options.body); if (payloads.length === 1) throw Error('offline'); return okay({...review, import_id: 3, replayed: true});});
  await c.submit(); c.get('importConfirm').checked = true; await c.save(); assert.match(c.get('importMessage').textContent, /reintente/); await c.save(); assert.equal(payloads[0], payloads[1]);
  const d = setup(async () => okay({...review, valid: false, errors: [{row: 2, message: 'bad balance'}]}));
  await d.submit(); d.get('importConfirm').checked = true; d.get('importConfirm').listeners.change(); assert.equal(d.get('importSave').disabled, true);
  const e = setup(async () => okay(review)); await e.submit(); e.get('importFile').listeners.change(); e.get('importConfirm').checked = true; await e.save(); assert.equal(e.get('importPreview').hidden, true);
  let finish;
  const f = setup(() => new Promise(r => {finish = r;})); const pending = f.submit(); for (let i=0; i<10 && !finish; i++) await Promise.resolve();
  f.get('logoutButton').listeners.click(); finish(okay(review)); await pending; assert.equal(f.get('importPreview').hidden, true); assert.equal(f.get('importSave').disabled, true);
  assert(!/<script[^>]*>[^<]+|onclick=|<style|style=/.test(html));
  console.log('6 import UI scenarios passed; no real requests sent.');
})().catch(error => {console.error(error); process.exitCode = 1;});
