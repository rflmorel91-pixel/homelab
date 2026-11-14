const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '../..');
const html = fs.readFileSync(path.join(root, 'app/fieldnest-workspace.html'), 'utf8');
const source = fs.readFileSync(path.join(root, 'app', html.match(/assets\/fieldnest-workspace-[a-f0-9]+\.js/)[0]), 'utf8');
const block = source.slice(source.indexOf('  let logoutBusy'), source.indexOf('\n  $("propertyForm")'));
function harness() {
  const pending = [], elements = new Map();
  const state = {loadVersion: 4, tenantId: '12', clients: [{tenant_id: 12}], orders: [{id: 1}]};
  const $ = id => {
    if (!elements.has(id)) elements.set(id, {hidden: false, disabled: false, resetCount: 0, reset() {this.resetCount++;}, addEventListener(type, handler) {this[type] = handler;}});
    return elements.get(id);
  };
  const context = vm.createContext({state, $, showLogin() {$('appPanel').hidden = true;}, render() {}, renderOverview() {}, applySearch() {},
    msg(id, text, good = false) {Object.assign($(id), {text, good});},
    request(url, options) {assert.equal(url, '/auth/logout'); assert.equal(options.method, 'POST'); return new Promise((resolve, reject) => pending.push({resolve, reject}));}
  });
  vm.runInContext(block + '\nglobalThis.signOut = signOut;', context);
  return {state, $, pending, signOut: context.signOut};
}
(async () => {
  // Hide private workspace and invalidate old loads immediately; no premature success.
  const h = harness();
  let run = h.$('logoutButton').click();
  assert.equal(h.state.tenantId, null); assert.equal(h.state.loadVersion, 5);
  assert.equal(h.state.clients.length, 0); assert.equal(h.state.orders.length, 0);
  assert(h.$('appPanel').hidden); assert(h.$('loginForm').hidden);
  assert.equal(h.$('loginForm').resetCount, 1);
  assert.equal(h.$('loginMessage').good, false);
  await h.signOut(); assert.equal(h.pending.length, 1); // duplicate click is ignored
  // Failed/timed-out logout gives a retry, never a success or a new login form.
  h.pending.shift().reject(new Error('timeout')); await run;
  assert.match(h.$('loginMessage').text, /session may still be active/);
  assert.equal(h.$('loginMessage').good, false);
  assert(h.$('loginForm').hidden); assert.equal(h.$('retryLogoutButton').hidden, false);
  assert.equal(h.$('retryLogoutButton').disabled, false);
  // Retry must obtain the server's explicit signed_out response.
  run = h.$('retryLogoutButton').click();
  h.pending.shift().resolve({status: 'unexpected'}); await run;
  assert.equal(h.$('loginMessage').good, false);
  assert.equal(h.$('retryLogoutButton').hidden, false);
  run = h.$('retryLogoutButton').click();
  h.pending.shift().resolve({status: 'signed_out'}); await run;
  assert.equal(h.$('loginMessage').text, 'You have signed out.');
  assert.equal(h.$('loginMessage').good, true);
  assert.equal(h.$('loginForm').hidden, false); assert(h.$('retryLogoutButton').hidden);
  assert.match(html, /id="retryLogoutButton"[^>]*hidden/);
  console.log('FieldNest logout: immediate privacy, duplicate guard, failure, unconfirmed response, and retry passed');
})().catch(error => {console.error(error); process.exitCode = 1;});
