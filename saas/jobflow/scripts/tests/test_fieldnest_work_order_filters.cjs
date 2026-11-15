const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const app = path.resolve(__dirname, '../../app');
const html = fs.readFileSync(path.join(app, 'fieldnest-workspace.html'), 'utf8');
const asset = html.match(/src="\/(assets\/fieldnest-workspace-[a-f0-9]+\.js)"/)[1];
const source = fs.readFileSync(path.join(app, asset), 'utf8');
const select = html.match(/<select id="workOrderFilter">([\s\S]*?)<\/select>/)[1];
for (const value of ['all', 'open', 'overdue', 'unassigned', 'closed']) assert.ok(select.includes(`value="${value}"`));
assert.match(html, /id="workOrderFilterCount" role="status"/);
assert.ok(source.includes('$("workOrderFilter")?.addEventListener("change", applySearch)'));
assert.match(html, /<button id="clearWorkOrderFilters" type="button"[^>]*disabled>Clear filters<\/button>/);

const today = '2026-11-14';
const orders = [
  {id: 1, status: 'open', target_date: '2026-11-13', vendor_id: null},
  {id: 2, status: 'scheduled', target_date: today, vendor_id: 3},
  {id: 3, status: 'waiting', target_date: '2026-12-01', vendor_id: null},
  {id: 4, status: 'in_progress', target_date: null, vendor_id: 3},
  {id: 5, status: 'completed', target_date: '2026-11-01', vendor_id: null},
  {id: 6, status: 'cancelled', target_date: '2026-11-01', vendor_id: null},
];
const original = JSON.stringify(orders);
const rows = orders.map(order => ({dataset: {orderId: String(order.id)}, textContent: order.id === 1 ? 'Faucet Building A' : 'Light Building B', hidden: false}));
const propertyRow = {textContent: 'Building A', hidden: false, dataset: {}};
function list(records) {
  return {records, note: null, querySelectorAll: () => records,
    querySelector() { return this.note; }, append(note) { this.note = note; }};
}
const nodes = {workOrderFilter: {value: 'all'}, workOrderPropertyFilter: {value: ''}, workOrderSort: {value: 'attention'}, clearWorkOrderFilters: {addEventListener(_type, handler) {this.click = handler;}}, workOrderFilterCount: {}, workOrders: list(rows), properties: list([propertyRow])};
const search = {value: '', dataset: {search: 'workOrders'}};
const propertySearch = {value: '', dataset: {search: 'properties'}};
const state = {orders};
const context = vm.createContext({state, $: id => nodes[id], document: {
  querySelectorAll: () => [search, propertySearch], createElement: () => ({}),
  querySelector: selector => { assert.equal(selector, '[data-search="workOrders"]'); return search; },
}});
const start = source.indexOf('  function workOrderMatchesFilter(');
const end = source.indexOf('  function orderedOpenWorkOrders(', start);
assert.ok(start >= 0 && end > start);
vm.runInContext(source.slice(start, end), context);
const matching = filter => orders.filter(order => context.workOrderMatchesFilter(order, filter, today)).map(order => order.id);
assert.deepEqual(matching('all'), [1,2,3,4,5,6]);
assert.deepEqual(matching('open'), [1,2,3,4]);
assert.deepEqual(matching('overdue'), [1]);
assert.deepEqual(matching('unassigned'), [1,3]);
assert.deepEqual(matching('closed'), [5,6]);
assert.deepEqual(matching('unknown'), [1,2,3,4,5,6]);
context.applySearch();
assert.equal(nodes.clearWorkOrderFilters.disabled, true);

nodes.workOrderFilter.value = 'unassigned';
search.value = '  FAUCET  ';
context.applySearch();
assert.deepEqual(rows.filter(row => !row.hidden).map(row => row.dataset.orderId), ['1']);
assert.equal(nodes.workOrderFilterCount.textContent, '1 of 6 work orders shown');
assert.equal(propertyRow.hidden, false, 'work order filter must not affect property search');
assert.equal(nodes.clearWorkOrderFilters.disabled, false);
search.value = 'missing'; context.applySearch();
assert.equal(nodes.workOrders.note.hidden, false);
assert.match(nodes.workOrders.note.textContent, /another filter/);
search.value = ''; nodes.workOrderFilter.value = 'all'; context.applySearch();
assert.equal(rows.filter(row => !row.hidden).length, 6);
assert.equal(nodes.workOrders.note.hidden, true);
assert.equal(nodes.clearWorkOrderFilters.disabled, true);

// Exercise the shipped button binding with all three filters active.
const clearListener = source.split('\n').find(line => line.startsWith('  $("clearWorkOrderFilters")?.addEventListener('));
assert.ok(clearListener); vm.runInContext(clearListener, context);
nodes.workOrderFilter.value = 'closed';
nodes.workOrderPropertyFilter.value = '99';
search.value = 'missing'; propertySearch.value = 'building';
context.applySearch();
assert.equal(rows.filter(row => !row.hidden).length, 0);
assert.equal(nodes.workOrders.note.hidden, false);
const rowOrder = rows.map(row => row.dataset.orderId);
nodes.clearWorkOrderFilters.click();
assert.equal(nodes.workOrderFilter.value, 'all');
assert.equal(nodes.workOrderPropertyFilter.value, '');
assert.equal(search.value, '');
assert.equal(propertySearch.value, 'building', 'other view searches must remain unchanged');
assert.equal(nodes.workOrderSort.value, 'attention', 'keep the selected sort');
assert.deepEqual(rows.map(row => row.dataset.orderId), rowOrder);
assert.equal(rows.filter(row => !row.hidden).length, 6);
assert.equal(nodes.workOrderFilterCount.textContent, '6 of 6 work orders shown');
assert.equal(nodes.workOrders.note.hidden, true);
assert.equal(nodes.clearWorkOrderFilters.disabled, true);
search.value = '   '; context.applySearch();
assert.equal(nodes.clearWorkOrderFilters.disabled, false, 'whitespace in the search can still be cleared');
nodes.clearWorkOrderFilters.click(); assert.equal(search.value, '');
nodes.workOrderFilter.value = 'closed';
orders[0].status = 'completed'; context.applySearch();
assert.equal(rows[0].hidden, false, 'filter must use current state after status changes');
orders[0].status = 'open';
assert.equal(JSON.stringify(orders), original);
state.orders = []; nodes.workOrders.records.length = 0; context.applySearch();
assert.equal(nodes.workOrderFilterCount.textContent, '0 of 0 work orders shown');
assert.equal(nodes.workOrders.note.hidden, true, 'leave the original empty-workspace message visible');
search.value = 'missing'; context.applySearch(); nodes.clearWorkOrderFilters.click();
assert.equal(nodes.clearWorkOrderFilters.disabled, true);
assert.equal(nodes.workOrderFilterCount.textContent, '0 of 0 work orders shown');
console.log('FieldNest work-order filters: statuses, UTC dates, search, counts, clear action, sort preservation, empty state, updates, and immutability passed');
