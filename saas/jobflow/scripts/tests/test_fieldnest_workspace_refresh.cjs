const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const app = path.resolve(__dirname, '../../app');
const html = fs.readFileSync(path.join(app, 'fieldnest-workspace.html'), 'utf8');
const asset = html.match(/src="\/(assets\/fieldnest-workspace-[a-f0-9]+\.js)"/)[1];
const source = fs.readFileSync(path.join(app, asset), 'utf8');
assert.match(html, /<button id="refreshWorkspaceButton" type="button"/);
function block(start, end) {
  const a = source.indexOf(start), b = source.indexOf(end, a);
  assert.ok(a >= 0 && b > a);
  return source.slice(a, b);
}
function setup() {
  const nodes = {tenantLabel: {}, refreshWorkspaceButton: {addEventListener(_type, handler) {this.click = handler;}}};
  // Model select behavior: replacing its options discards a missing selection.
  nodes.workOrderPropertyFilter = {_value: '7', _html: '',
    get value() {return this._value;},
    set value(value) {this._value = this._html.includes(`value="${value}"`) ? value : '';},
    get innerHTML() {return this._html;},
    set innerHTML(value) {this._html = value; if (!value.includes(`value="${this._value}"`)) this._value = '';},
  };
  nodes.workOrderFilter = {value: 'open'};
  const search = {value: 'faucet'};
  const state = {tenantId: 1, loadVersion: 0, clients: [{tenant_id: 1, name: 'Company A'}], properties: [{id: 7, name: 'A'}], residents: [], vendors: [], orders: [], plans: [], occurrences: []};
  const messages = [], requests = [], applied = [];
  let pending = null, failure = false;
  const context = vm.createContext({state, $: id => nodes[id],
    localStorage: {setItem() {}},
    render: () => context.renderWorkOrderPropertyFilter(), renderOverview() {},
    applySearch: () => applied.push(nodes.workOrderPropertyFilter.value),
    msg: (_id, text, good) => messages.push({text, good}),
    request: async (url, options) => {
      requests.push({url, options});
      if (pending) await pending;
      if (failure) throw new Error('Connection lost');
      if (url.endsWith('/properties')) return [{id: 7, name: 'A'}];
      if (url.endsWith('/work-orders')) return [{id: 42, title: 'New resident request'}];
      return [];
    },
  });
  vm.runInContext(block('  const esc =', '  const msg =') +
    block('  async function loadAll()', '  function renderWorkOrderPropertyFilter(') +
    block('  function renderWorkOrderPropertyFilter(', '  function workOrderListMarkup(') +
    block('  let refreshBusy =', '  $("tenantSelect").addEventListener('), context);
  return {nodes, state, context, messages, requests, applied, search,
    fail() {failure = true;}, recover() {failure = false;},
    hold() {let release; pending = new Promise(resolve => {release = resolve;}); return release;},
  };
}
(async () => {
  let s = setup();
  const release = s.hold();
  const first = s.nodes.refreshWorkspaceButton.click();
  assert.equal(s.nodes.refreshWorkspaceButton.disabled, true);
  await s.nodes.refreshWorkspaceButton.click();
  assert.equal(s.requests.length, 6, 'duplicate click must not start more requests');
  assert.equal(s.state.orders.length, 0, 'do not display stale records as current');
  release(); await first;
  assert.equal(s.state.orders[0].id, 42);
  assert.equal(s.nodes.workOrderPropertyFilter.value, '7', 'restore the property after the loading render clears options');
  assert.equal(s.applied.at(-1), '7');
  assert.equal(s.nodes.workOrderFilter.value, 'open');
  assert.equal(s.search.value, 'faucet');
  assert.equal(s.messages.at(-1).text, 'Workspace refreshed.');
  assert.equal(s.nodes.refreshWorkspaceButton.disabled, false);
  assert.equal(s.nodes.refreshWorkspaceButton.textContent, 'Refresh workspace');
  assert.ok(s.requests.every(({options}) => !options.method && options.headers['X-Tenant-ID'] === '1'));

  s = setup(); s.fail(); await s.nodes.refreshWorkspaceButton.click();
  assert.match(s.messages.at(-1).text, /Could not refresh.*Connection lost/);
  assert.equal(s.messages.some(message => message.text === 'Workspace refreshed.'), false);
  assert.equal(s.nodes.refreshWorkspaceButton.disabled, false);
  s.recover(); await s.nodes.refreshWorkspaceButton.click();
  assert.equal(s.state.orders[0].id, 42);
  assert.equal(s.messages.at(-1).text, 'Workspace refreshed.');

  for (const nextTenant of ['2', null]) {
    s = setup(); const unblock = s.hold();
    const loading = s.nodes.refreshWorkspaceButton.click();
    s.state.tenantId = nextTenant; s.state.loadVersion++;
    const messageCount = s.messages.length;
    unblock(); await loading;
    assert.equal(s.state.orders.length, 0, 'old workspace response must be ignored');
    assert.equal(s.messages.length, messageCount, 'old refresh must not overwrite current messages');
    assert.equal(s.nodes.refreshWorkspaceButton.disabled, false);
  }
  s = setup(); s.state.tenantId = null; await s.nodes.refreshWorkspaceButton.click();
  assert.equal(s.requests.length, 0);
  console.log('FieldNest refresh: new records, duplicate guard, filter preservation, read-only requests, failure/retry, workspace switch, and sign-out races passed');
})().catch(error => {console.error(error); process.exitCode = 1;});
