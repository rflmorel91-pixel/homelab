const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const app = path.resolve(__dirname, '../../app');
const html = fs.readFileSync(path.join(app, 'fieldnest-workspace.html'), 'utf8');
const asset = html.match(/src="\/(assets\/fieldnest-workspace-[a-f0-9]+\.js)"/)[1];
const source = fs.readFileSync(path.join(app, asset), 'utf8');
const select = html.match(/<select id="workOrderSort">([\s\S]*?)<\/select>/)[1];
assert.match(select, /^<option value="newest">Newest first/);
assert.match(select, /value="attention">Needs attention first/);
function block(start, end) {
  const a = source.indexOf(start), b = source.indexOf(end, a);
  assert.ok(a >= 0 && b > a);
  return source.slice(a, b);
}
const today = '2026-11-15';
const orders = [
  {id: 1, priority: 'emergency', status: 'open', property_id: 10, title: 'Pump emergency'},
  {id: 2, priority: 'low', status: 'waiting', target_date: '2026-11-01', property_id: 10, title: 'Pump overdue'},
  {id: 3, priority: 'high', status: 'open', target_date: '2026-11-20', property_id: 20, title: 'Light'},
  {id: 4, priority: 'normal', status: 'scheduled', target_date: today, property_id: 10, title: 'Pump today'},
  {id: 5, priority: 'normal', status: 'open', property_id: 20, title: 'Light'},
  {id: 6, priority: 'emergency', status: 'completed', target_date: '2026-11-01', property_id: 10, title: 'Old pump'},
  {id: 7, priority: 'emergency', status: 'cancelled', target_date: '2026-11-01', property_id: 10, title: 'Old pump'},
  {id: 8, priority: 'low', status: 'in_progress', target_date: '2026-11-01', property_id: 10, title: 'Pump overdue'},
  {id: 9, priority: 'emergency', status: 'open', target_date: '2026-12-01', property_id: 20, title: 'Light emergency'},
];
orders.forEach(Object.freeze); Object.freeze(orders);
const snapshot = JSON.stringify(orders);
class FixedDate extends Date {constructor(...args) {super(...(args.length ? args : ['2026-11-15T12:00:00Z']));}}
const nodes = new Map();
const get = id => {if (!nodes.has(id)) nodes.set(id, {}); return nodes.get(id);};
nodes.set('workOrderSort', {value: 'newest', addEventListener(_type, handler) {this.change = handler;}});
nodes.set('workOrderPropertyFilter', {value: ''});
nodes.set('workOrderFilter', {value: 'all'});
const list = {rows: [], note: null,
  set innerHTML(value) {
    this.rows = [...value.matchAll(/<button[^>]*data-order-id="([^"]+)"[^>]*>([\s\S]*?)<\/button>/g)].map(match => ({dataset: {orderId: match[1]}, textContent: match[2].replace(/<[^>]+>/g, ' '), hidden: false}));
    this.note = null;
  },
  querySelectorAll: () => list.rows,
  querySelector: () => list.note,
  append: note => {list.note = note;},
};
nodes.set('workOrders', list);
const search = {value: '', dataset: {search: 'workOrders'}};
const state = {orders, properties: [{id: 10, name: 'Building A'}, {id: 20, name: 'Building B'}], vendors: [], residents: [], clients: []};
const context = vm.createContext({state, $: get, Date: FixedDate, renderMaintenance() {}, document: {
  querySelectorAll: () => [search], createElement: () => ({}),
}});
vm.runInContext(block('  const esc =', '  const msg =') +
  block('  function renderWorkOrderPropertyFilter(', '  function renderMaintenance()') +
  block('  function workOrderMatchesFilter(', '  function renderOverview('), context);
const ids = (mode, items = orders) => Array.from(context.orderedWorkOrderList(items, mode, today), order => order.id);
assert.deepEqual(ids('newest'), [9,8,7,6,5,4,3,2,1]);
assert.deepEqual(ids('attention'), [9,1,8,2,3,4,5,7,6]);
assert.deepEqual(ids('unknown'), ids('newest'));
assert.deepEqual(ids('attention', []), []);
assert.equal(ids('attention').length, orders.length, 'list must not inherit overview top-five limit');
assert.equal(JSON.stringify(orders), snapshot);

const listener = source.split('\n').find(line => line.startsWith('  $("workOrderSort")?.addEventListener('));
assert.ok(listener); vm.runInContext(listener, context);
get('workOrderSort').change();
assert.deepEqual(list.rows.map(row => row.dataset.orderId), ['9','8','7','6','5','4','3','2','1']);
get('workOrderSort').value = 'attention';
get('workOrderPropertyFilter').value = '10';
get('workOrderFilter').value = 'open';
search.value = 'pump'; get('workOrderSort').change();
assert.deepEqual(list.rows.filter(row => !row.hidden).map(row => row.dataset.orderId), ['1','8','2','4']);
assert.equal(get('workOrderFilterCount').textContent, '4 of 9 work orders shown');
assert.equal(get('workOrderPropertyFilter').value, '10');
assert.equal(get('workOrderFilter').value, 'open');
assert.equal(search.value, 'pump');
state.orders = orders.map(order => order.id === 1 ? {...order, status: 'completed'} : order);
get('workOrderSort').change();
assert.deepEqual(list.rows.filter(row => !row.hidden).map(row => row.dataset.orderId), ['8','2','4']);
get('workOrderSort').value = 'newest'; get('workOrderSort').change();
assert.deepEqual(list.rows.filter(row => !row.hidden).map(row => row.dataset.orderId), ['8','4','2']);
assert.equal(JSON.stringify(orders), snapshot);
console.log('FieldNest work-order sort: newest, urgency groups, UTC dates, ties, closed retention, all rows, filter/search intersection, counts, updates, and immutability passed');
