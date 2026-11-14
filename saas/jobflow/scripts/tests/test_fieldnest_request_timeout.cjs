const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '../..');
const html = fs.readFileSync(path.join(root, 'app/fieldnest-workspace.html'), 'utf8');
const source = fs.readFileSync(path.join(root, 'app', html.match(/assets\/fieldnest-workspace-[a-f0-9]+\.js/)[0]), 'utf8');
function harness(fetch) {
  let callback, cleared = 0;
  const context = vm.createContext({AbortController, fetch,
    document: {}, setTimeout(fn, delay) {assert.equal(delay, 30000); callback = fn; return 7;},
    clearTimeout(id) {assert.equal(id, 7); cleared++;}
  });
  vm.runInContext(source.slice(source.indexOf('  const API'), source.indexOf('  function showLogin')) + '\nglobalThis.test = {request, state};', context);
  context.test.state.tenantId = '12';
  return {...context.test, expire: () => callback(), cleared: () => cleared};
}
(async () => {
  // A stalled read is bounded even when fetch ignores cancellation.
  let signal, calls = 0;
  let h = harness((url, options) => {calls++; signal = options.signal; assert.equal(options.headers['X-Tenant-ID'], '12'); return new Promise(() => {});});
  let result = h.request('/products/fieldnest/properties'); h.expire();
  await assert.rejects(result, /timed out.*Check your connection/);
  assert(signal.aborted); assert.equal(h.cleared(), 1); assert.equal(calls, 1);
  // A write is never automatically retried or reported as definitely unsaved.
  h = harness(() => new Promise(() => {}));
  result = h.request('/products/fieldnest/work-orders', {method: 'POST'}); h.expire();
  await assert.rejects(result, /may have been saved.*check before trying again/);
  // The deadline includes stalled response-body reads.
  h = harness(async () => ({ok: true, status: 200, json: () => new Promise(() => {})}));
  result = h.request('/properties'); await Promise.resolve(); h.expire();
  await assert.rejects(result, /timed out/);
  // Successful JSON, no-content, and API errors retain their contract and clear timers.
  h = harness(async () => ({ok: true, status: 200, json: async () => ({id: 4})}));
  assert.equal((await h.request('/properties')).id, 4); assert.equal(h.cleared(), 1);
  h = harness(async () => ({ok: true, status: 204}));
  assert.equal(await h.request('/properties'), null); assert.equal(h.cleared(), 1);
  h = harness(async () => ({ok: false, status: 403, json: async () => ({detail: 'Access denied'})}));
  await assert.rejects(h.request('/properties'), /Access denied/); assert.equal(h.cleared(), 1);
  console.log('FieldNest request deadlines: 6 scenarios passed');
})().catch(error => {console.error(error); process.exitCode = 1;});
