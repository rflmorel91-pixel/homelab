const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const app = path.resolve(__dirname, '../../app');
const html = fs.readFileSync(path.join(app, 'fieldnest-workspace.html'), 'utf8');
const source = fs.readFileSync(path.join(app, html.match(/assets\/fieldnest-workspace-[a-f0-9]+\.js/)[0]), 'utf8');
function block(start, end) {
  const a = source.indexOf(start), b = source.indexOf(end, a);
  assert.ok(a >= 0 && b > a); return source.slice(a, b);
}
class Clock extends Date {
  constructor(...args) {super(...(args.length ? args : ['2026-11-16T01:00:00Z']));}
}
const nodes = new Map();
const get = id => {if (!nodes.has(id)) nodes.set(id, {value: ''}); return nodes.get(id);};
const vendors = [
  {id: 1, name: '<Acme>', trade: 'Plumbing & heating', email: '<private@example.test>', insurance_expires: '2026-11-15'},
  {id: 2, name: 'Due today', trade: 'Electrical', insurance_expires: '2026-11-16'},
  {id: 3, name: 'Soon', trade: 'HVAC', insurance_expires: '2026-12-16'},
  {id: 4, name: 'Later', trade: 'Roofing', insurance_expires: '2026-12-17'},
  {id: 5, name: 'No date', trade: 'General', insurance_expires: null},
];
const state = {tenantId: 1, vendors, clients: [], properties: [], orders: [], residents: [], plans: [], occurrences: []};
const context = vm.createContext({state, Date: Clock, $: get, workOrderListMarkup: () => '',
  orderedWorkOrderList: orders => orders,
  request() {throw new Error('Expiry labels must not make requests');},
});
vm.runInContext(block('  const esc =', '  const msg =') +
  block('  function renderWorkOrderPropertyFilter(', '  function workOrderListMarkup(') +
  block('  function render() {', '  $("maintenanceForm").addEventListener'), context);
const status = (expiry, today = '2026-11-16') => context.vendorInsuranceStatus({insurance_expires: expiry}, today);
for (const [expiry, expected] of [['2026-11-15','past'], ['2026-11-16','today'], ['2026-11-17','soon'], ['2026-12-16','soon'], ['2026-12-17','recorded'], [null,'missing'], [undefined,'missing'], ['','missing']]) {
  assert.equal(status(expiry).kind, expected);
}
for (const value of ['2026-02-29','2026-02-30','2026-13-01','2026-11-16T23:00:00Z','<img src=x onerror=alert(1)>',7]) assert.equal(status(value).kind, 'unknown');
assert.equal(status('2028-02-29', '2028-02-28').kind, 'soon');
assert.equal(status('2026-03-09', '2026-03-08').kind, 'soon');
assert.equal(status('2026-11-16','invalid').kind, 'unknown');
assert.equal(status('2026-12-16').text, 'Expiry within 30 days · 2026-12-16 (UTC)');
const before = JSON.stringify(state);
context.render();
assert.match(get('vendors').innerHTML, /Expiry passed · 2026-11-15 \(UTC\)/);
assert.match(get('vendors').innerHTML, /Expiry today · 2026-11-16 \(UTC\)/);
assert.match(get('vendors').innerHTML, /Expiry within 30 days · 2026-12-16 \(UTC\)/);
assert.match(get('vendors').innerHTML, /Expiry recorded · 2026-12-17 \(UTC\)/);
assert.match(get('vendors').innerHTML, /No expiry recorded/);
assert.doesNotMatch(get('vendors').innerHTML, /<Acme>|<private@/);
for (const id of ['workVendor', 'maintenanceVendor']) {
  const markup = get(id).innerHTML;
  assert.match(markup, /^<option value="">Unassigned<\/option>/);
  assert.match(markup, /value="1">&lt;Acme&gt; · Plumbing &amp; heating · Expiry passed/);
  assert.match(markup, /No expiry recorded/);
  assert.doesNotMatch(markup, /disabled|selected|private@example/);
}
assert.equal(JSON.stringify(state), before, 'display must not mutate vendor data or assignments');
// Exercise the actual detail editor, including its assignment selector.
const fields = new Map();
get('workOrderDetailForm').reset = () => {};
get('workOrderDetailForm').elements = {namedItem: key => {if (!fields.has(key)) fields.set(key, {}); return fields.get(key);}};
get('workOrderDetailDialog').querySelector = () => ({});
get('workOrderDetailDialog').showModal = () => {};
state.orders = [{id: 9, vendor_id: 1, property_id: 1, title: 'Repair', status: 'open', priority: 'normal'}];
Object.assign(context, {loadManagerPhotos() {}, workOrderDraftSnapshot: () => 'draft', editingOrder: null, workOrderDraftBaseline: null});
vm.runInContext(block('  function openWorkOrder(', '  document.addEventListener("click", event => { const row'), context);
context.openWorkOrder(9);
assert.equal(fields.get('vendor_id').value, '1', 'recorded past expiry does not silently unassign a vendor');
assert.match(fields.get('vendor_id').innerHTML, /Expiry passed/);
state.vendors = [{id: 20, name: 'Other workspace', trade: 'General', insurance_expires: null}];
context.render(); assert.doesNotMatch(get('workVendor').innerHTML, /Acme|value="1"/);
state.vendors = []; context.render();
assert.equal(get('workVendor').innerHTML, '<option value="">Unassigned</option>');
assert.equal(get('maintenanceVendor').innerHTML, '<option value="">Unassigned</option>');
assert.match(html, /Insurance expiry labels use recorded dates \(UTC\)\. Coverage has not been verified\./);
console.log('FieldNest vendor expiry: UTC boundaries, 30-day window, leap/invalid dates, escaped list/options, assignment retention, refresh, and no side effects passed');
