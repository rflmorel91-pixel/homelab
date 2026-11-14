const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const app = path.resolve(__dirname, '../../app');
const html = fs.readFileSync(path.join(app, 'fieldnest-workspace.html'), 'utf8');
const asset = html.match(/src="\/(assets\/fieldnest-workspace-[a-f0-9]+\.js)"/)[1];
const source = fs.readFileSync(path.join(app, asset), 'utf8');
assert.match(html, /<label>Property<select id="workOrderPropertyFilter">/);
assert.ok(source.includes('$("workOrderPropertyFilter")?.addEventListener("change", applySearch)'));
function block(start, end) {
  const a = source.indexOf(start), b = source.indexOf(end, a);
  assert.ok(a >= 0 && b > a);
  return source.slice(a, b);
}
const orders = [
  {id: 1, property_id: 10, status: 'open', vendor_id: null},
  {id: 2, property_id: 20, status: 'open', vendor_id: null},
  {id: 3, property_id: 10, status: 'completed', vendor_id: 7},
];
const original = JSON.stringify(orders);
const rows = orders.map(order => ({dataset: {orderId: String(order.id)}, textContent: order.id === 1 ? 'Faucet Smith' : 'Light Jones', hidden: false}));
const otherRow = {dataset: {}, textContent: 'Property name', hidden: false};
function list(records) { return {querySelectorAll: () => records, note: null,
  querySelector() {return this.note;}, append(note) {this.note = note;}}; }
const nodes = {workOrderPropertyFilter: {value: ''}, workOrderFilter: {value: 'all'}, workOrderFilterCount: {}, workOrders: list(rows), properties: list([otherRow]), tenantSelect: {addEventListener(_type, handler) {this.change = handler;}}};
const search = {value: '', dataset: {search: 'workOrders'}};
const otherSearch = {value: '', dataset: {search: 'properties'}};
const state = {orders, properties: [{id: 10, name: '<Building A>'}, {id: 20, name: 'Building B'}]};
let reloads = 0;
const context = vm.createContext({state, $: id => nodes[id], document: {
  querySelectorAll: selector => selector === '[data-search]' ? [search, otherSearch] : [],
  createElement: () => ({}),
}, loadAll: async () => {reloads++;}, msg() {}});
vm.runInContext(block('  const esc =', '  const msg =') +
  block('  function renderWorkOrderPropertyFilter(', '  function workOrderListMarkup(') +
  block('  function workOrderMatchesFilter(', '  function orderedOpenWorkOrders('), context);
context.renderWorkOrderPropertyFilter();
assert.match(nodes.workOrderPropertyFilter.innerHTML, /All properties/);
assert.match(nodes.workOrderPropertyFilter.innerHTML, /&lt;Building A&gt;/);
context.applySearch();
assert.equal(rows.filter(row => !row.hidden).length, 3);
nodes.workOrderPropertyFilter.value = '10';
context.applySearch();
assert.deepEqual(rows.filter(row => !row.hidden).map(row => row.dataset.orderId), ['1', '3']);
assert.equal(nodes.workOrderFilterCount.textContent, '2 of 3 work orders shown');
nodes.workOrderFilter.value = 'open'; search.value = ' SMITH ';
context.applySearch();
assert.deepEqual(rows.filter(row => !row.hidden).map(row => row.dataset.orderId), ['1']);
assert.equal(otherRow.hidden, false);
nodes.workOrderPropertyFilter.value = '20'; context.applySearch();
assert.equal(nodes.workOrders.note.hidden, false);
search.value = ''; context.applySearch();
assert.deepEqual(rows.filter(row => !row.hidden).map(row => row.dataset.orderId), ['2']);
context.renderWorkOrderPropertyFilter();
assert.equal(nodes.workOrderPropertyFilter.value, '20', 'keep a valid selection during reload');
state.properties = [{id: 10, name: 'Building A'}]; context.renderWorkOrderPropertyFilter();
assert.equal(nodes.workOrderPropertyFilter.value, '', 'reset a removed property');
assert.doesNotMatch(nodes.workOrderPropertyFilter.innerHTML, /Building B/);
state.properties = []; context.renderWorkOrderPropertyFilter();
assert.equal(nodes.workOrderPropertyFilter.innerHTML, '<option value="">All properties</option>');
const tenantListener = source.split('\n').find(line => line.startsWith('  $("tenantSelect").addEventListener("change",'));
assert.ok(tenantListener);
vm.runInContext(tenantListener, context);
(async () => {
  nodes.workOrderPropertyFilter.value = '10';
  await nodes.tenantSelect.change({target: {value: 'new-workspace'}});
  assert.equal(nodes.workOrderPropertyFilter.value, '');
  assert.equal(state.tenantId, 'new-workspace');
  assert.equal(reloads, 1);
  assert.equal(JSON.stringify(orders), original);
  console.log('FieldNest property filter: combined filters/search, counts, escaped options, selection refresh, removed/empty properties, and workspace reset passed');
})().catch(error => {console.error(error); process.exitCode = 1;});
