const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const app = path.resolve(__dirname, '../../app');
const html = fs.readFileSync(path.join(app, 'fieldnest-workspace.html'), 'utf8');
const asset = html.match(/src="\/(assets\/fieldnest-workspace-[a-f0-9]+\.js)"/)[1];
const source = fs.readFileSync(path.join(app, asset), 'utf8');
assert.match(html, /type="button"[^>]*id="copyWorkOrderSummary">Copy summary/);
const textarea = html.match(/<textarea id="workOrderSummaryText"[^>]*>/)[0];
assert.match(textarea, /readonly/); assert.doesNotMatch(textarea, /name=/);
function block(start, end) {
  const a = source.indexOf(start), b = source.indexOf(end, a);
  assert.ok(a >= 0 && b > a); return source.slice(a, b);
}
function setup() {
  const nodes = new Map();
  const get = id => {if (!nodes.has(id)) nodes.set(id, {value: '', addEventListener(type, handler) {this[type] = handler;}, focus() {this.focused = true;}, select() {this.selected = true;}}); return nodes.get(id);};
  const dialog = {open: true, message: {}, events: {},
    querySelector() {return this.message;},
    addEventListener(type, handler) {(this.events[type] ||= []).push(handler);},
    showModal() {this.open = true;},
    close() {this.open = false; for (const handler of this.events.close || []) handler();},
  };
  nodes.set('workOrderDetailDialog', dialog);
  const fields = new Map();
  const form = {dataset: {}, reset() {}, elements: {namedItem: key => {if (!fields.has(key)) fields.set(key, {}); return fields.get(key);}}};
  nodes.set('workOrderDetailForm', form);
  const order = {id: 1, property_id: 2, vendor_id: 3, title: 'Repair pump', unit: '4B', status: 'in_progress', priority: 'high', target_date: '2026-11-20', description: 'Inspect seal.\nReplace if necessary.', resident_email: 'private@example.test', tracking_path: '/resident/secret-token'};
  const state = {tenantId: 7, orders: [order], properties: [{id: 2, name: 'Building A'}], vendors: [{id: 3, name: 'Acme Repairs'}], residents: [], clients: []};
  const copied = []; let pending = null, failure = false;
  const context = vm.createContext({state, $: get, editingOrder: {id: 1, tenantId: '7'}, workOrderDraftBaseline: 'saved',
    workOrderDraftSnapshot: () => context.draft,
    draft: 'saved', loadManagerPhotos() {}, msg() {},
    navigator: {clipboard: {writeText: async text => {copied.push(text); if (pending) await pending; if (failure) throw new Error('Permission denied');}}},
  });
  vm.runInContext(block('  const esc =', '  const msg =') + block('  function vendorInsuranceStatus(', '  function workOrderListMarkup(') + block('  function workOrderSummaryText(', '  let workOrderDraftBaseline ='), context);
  const openStart = source.indexOf('  function openWorkOrder(');
  const openEnd = source.indexOf('  document.addEventListener("click", event => { const row', openStart);
  assert.ok(openStart >= 0 && openEnd > openStart);
  vm.runInContext(source.slice(openStart, openEnd), context);
  return {context, nodes, get, dialog, form, state, order, copied,
    fail() {failure = true;}, recover() {failure = false;},
    hold() {let release; pending = new Promise(resolve => {release = resolve;}); return release;},
  };
}
(async () => {
  let s = setup();
  await s.get('copyWorkOrderSummary').click();
  assert.equal(s.copied.length, 1);
  const text = s.copied[0];
  for (const value of ['#1', 'Repair pump', 'Building A', '4B', 'in progress', 'high', '2026-11-20 (UTC)', 'Acme Repairs', 'Inspect seal.\nReplace if necessary.']) assert.ok(text.includes(value));
  assert.doesNotMatch(text, /private@example|secret-token/);
  assert.equal(s.dialog.message.textContent, 'Saved work-order summary copied.');
  assert.equal(s.get('copyWorkOrderSummary').disabled, false);
  assert.match(s.context.workOrderSummaryText({...s.order, vendor_id: null, target_date: null, unit: '', description: ''}), /Target date: Not set\nVendor: Unassigned/);
  assert.match(s.context.workOrderSummaryText(s.order), /Assigned vendor unavailable/);
  assert.equal(s.state.orders[0], s.order);

  s = setup(); s.context.draft = 'edited'; await s.get('copyWorkOrderSummary').click();
  assert.equal(s.copied.length, 0); assert.match(s.dialog.message.textContent, /Save your changes/);
  s.context.draft = 'saved'; s.form.dataset.busy = '1'; await s.get('copyWorkOrderSummary').click();
  assert.equal(s.copied.length, 0); assert.match(s.dialog.message.textContent, /Wait for the save/);
  delete s.form.dataset.busy; s.state.tenantId = 8; await s.get('copyWorkOrderSummary').click();
  assert.equal(s.copied.length, 0);

  s = setup(); s.fail(); await s.get('copyWorkOrderSummary').click();
  assert.equal(s.get('workOrderSummaryFallback').hidden, false);
  assert.equal(s.get('workOrderSummaryText').value, s.copied[0]);
  assert.equal(s.get('workOrderSummaryText').selected, true);
  s.recover(); await s.get('copyWorkOrderSummary').click();
  assert.equal(s.get('workOrderSummaryFallback').hidden, true);
  assert.equal(s.get('workOrderSummaryText').value, '');
  assert.equal(s.dialog.message.textContent, 'Saved work-order summary copied.');
  s = setup(); s.context.navigator.clipboard = undefined;
  await s.get('copyWorkOrderSummary').click();
  assert.equal(s.get('workOrderSummaryFallback').hidden, false);
  assert.equal(s.copied.length, 0);
  s.dialog.close(); assert.equal(s.get('workOrderSummaryText').value, '');
  assert.equal(s.get('workOrderSummaryFallback').hidden, true);

  for (const change of ['close', 'workspace', 'reopen']) {
    s = setup(); s.fail(); const release = s.hold();
    const copying = s.get('copyWorkOrderSummary').click();
    await s.get('copyWorkOrderSummary').click(); assert.equal(s.copied.length, 1);
    if (change === 'close') s.dialog.close();
    if (change === 'workspace') {s.state.tenantId = 8; s.dialog.close();}
    if (change === 'reopen') {s.dialog.close(); s.context.openWorkOrder(1);}
    const message = s.dialog.message.textContent;
    release(); await copying;
    assert.equal(s.dialog.message.textContent, message);
    assert.equal(s.get('workOrderSummaryText').value, '');
    assert.equal(s.get('workOrderSummaryFallback').hidden, true);
    assert.equal(s.get('copyWorkOrderSummary').disabled, false);
  }
  console.log('FieldNest summary: saved fields, omitted contact/link fields, draft/save guards, clipboard fallback/retry, duplicates, close/workspace/reopen races passed');
})().catch(error => {console.error(error); process.exitCode = 1;});
