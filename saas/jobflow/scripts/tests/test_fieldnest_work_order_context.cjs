const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const app = path.resolve(__dirname, '../../app');
const html = fs.readFileSync(path.join(app, 'fieldnest-workspace.html'), 'utf8');
const asset = html.match(/src="\/(assets\/fieldnest-workspace-[a-f0-9]+\.js)"/)[1];
const source = fs.readFileSync(path.join(app, asset), 'utf8');
function between(start, end) {
  const first = source.indexOf(start), last = source.indexOf(end, first);
  assert.ok(first >= 0 && last > first);
  return source.slice(first, last);
}
const context = vm.createContext({});
vm.runInContext(between('  const esc =', '  const msg =') +
  between('  function workOrderTargetLabel(', '  function renderOverview(') +
  between('  function workOrderListMarkup(', '  function render()'), context);
const properties = [{id: 2, name: 'Building A'}];
const vendors = [{id: 3, name: 'Smith Plumbing'}];
const order = {id: 9, property_id: 2, vendor_id: 3, title: 'Leaking faucet', unit: '4B', priority: 'high', status: 'open', target_date: '2026-11-13'};
const today = '2026-11-14';
const render = item => context.workOrderListMarkup([item], properties, vendors, today);
const original = JSON.stringify({order, properties, vendors});
let output = render(order);
assert.match(output, /data-order-id="9"/);
assert.match(output, /Building A · Unit 4B · high priority/);
assert.match(output, /Overdue · Target 2026-11-13 \(UTC\) · Vendor: Smith Plumbing/);
assert.match(render({...order, target_date: today}), /Due today \(UTC\)/);
assert.match(render({...order, target_date: '2026-12-01'}), /Target 2026-12-01 \(UTC\)/);
assert.match(render({...order, target_date: null}), /No target date/);
assert.match(render({...order, vendor_id: null}), /Unassigned vendor/);
output = render({...order, vendor_id: 999});
assert.match(output, /Assigned vendor unavailable/);
assert.doesNotMatch(output, /Unassigned vendor/);
for (const status of ['completed', 'cancelled']) {
  output = render({...order, status});
  assert.match(output, /Target 2026-11-13 \(UTC\)/);
  assert.doesNotMatch(output, /Overdue|Due today/);
  output = render({...order, status, target_date: today});
  assert.doesNotMatch(output, /Overdue|Due today/);
}
assert.match(render({...order, property_id: 999, unit: ''}), /Property · high priority/);
assert.match(context.workOrderListMarkup([], properties, vendors, today), /No work orders yet/);
assert.equal(JSON.stringify({order, properties, vendors}), original);

// User-controlled labels must remain text when the renderer uses innerHTML.
output = context.workOrderListMarkup([
  {...order, title: '<img src=x onerror=alert(1)>', unit: '<script>', id: '9" onclick="bad'}
], [{id: 2, name: '<b>Property</b>'}], [{id: 3, name: '<svg onload=bad>'}], today);
assert.doesNotMatch(output, /<img|<script|<svg|<b>Property/);
assert.match(output, /&lt;svg onload=bad&gt;/);
assert.match(output, /data-order-id="9&quot; onclick=&quot;bad"/);

// Exercise the actual workspace render entry point with lightweight DOM stubs.
const nodes = new Map();
const get = id => { if (!nodes.has(id)) nodes.set(id, {}); return nodes.get(id); };
context.$ = get;
context.state = {properties, vendors, orders: [order], residents: [], clients: []};
context.renderMaintenance = () => {};
vm.runInContext(between('  function render() {', '  function renderMaintenance()'), context);
context.render();
assert.match(get('workOrders').innerHTML, /Vendor: Smith Plumbing/);
vendors[0].name = 'New Vendor Name';
context.render();
assert.match(get('workOrders').innerHTML, /Vendor: New Vendor Name/);
vendors[0].name = 'Smith Plumbing';
console.log('FieldNest work-order context: UTC dates, closed-order labels, vendor assignment, fallbacks, escaping, empty state, immutability, and render updates passed');
