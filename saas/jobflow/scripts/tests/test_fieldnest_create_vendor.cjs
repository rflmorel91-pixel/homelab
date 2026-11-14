const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const app = path.resolve(__dirname, '../../app');
const html = fs.readFileSync(path.join(app, 'fieldnest-workspace.html'), 'utf8');
const asset = html.match(/src="\/(assets\/fieldnest-workspace-[a-f0-9]+\.js)"/)[1];
const source = fs.readFileSync(path.join(app, asset), 'utf8');
const markup = html.match(/<form[^>]*id="workOrderForm"[^>]*>([\s\S]*?)<\/form>/)[1];
assert.match(markup, /Assigned vendor \(optional\)/);
const select = markup.match(/<select id="workVendor"[^>]*>/)[0];
assert.match(select, /name="vendor_id"/);
assert.doesNotMatch(select, /required/);
const nodes = new Map();
const get = id => { if (!nodes.has(id)) nodes.set(id, {}); return nodes.get(id); };
const state = {properties: [{id: 7, name: 'Building A'}], vendors: [{id: 11, name: '<Acme>', trade: 'Plumbing & heating'}], orders: [], residents: [], clients: []};
function block(start, end) {
  const a = source.indexOf(start), b = source.indexOf(end, a);
  assert.ok(a >= 0 && b > a);
  return source.slice(a, b);
}
const context = vm.createContext({state, $: get, renderMaintenance() {}, workOrderListMarkup: () => ''});
vm.runInContext(block('  const esc =', '  const msg =') + block('  function render() {', '  function renderMaintenance()'), context);
context.render();
assert.match(get('workVendor').innerHTML, /^<option value="">Unassigned<\/option>/);
assert.match(get('workVendor').innerHTML, /value="11">&lt;Acme&gt; · Plumbing &amp; heating/);
assert.doesNotMatch(get('workVendor').innerHTML, /<Acme>/);
state.vendors = [];
context.render();
assert.equal(get('workVendor').innerHTML, '<option value="">Unassigned</option>', 'a refreshed workspace must not retain prior vendor options');
state.vendors = [{id: 22, name: 'New Company Vendor', trade: 'Electrical'}];
context.render();
assert.match(get('workVendor').innerHTML, /value="22"/);
assert.doesNotMatch(get('workVendor').innerHTML, /value="11"/);

let submit;
let fail = false;
const requests = [];
const errors = [];
let reloads = 0;
const form = {dataset: {}, button: {}, values: {}, resets: 0, closes: 0,
  addEventListener(_type, handler) { submit = handler; },
  querySelector() { return this.button; },
  closest() { return {close: () => this.closes++}; },
  reset() { this.values = {}; this.resets++; },
};
const handler = source.split('\n').find(line => line.startsWith('  $("workOrderForm").addEventListener("submit",'));
assert.ok(handler);
vm.runInNewContext(handler, {
  state, $: () => form, payload: f => ({...f.values}),
  request: async (url, options) => {
    requests.push({url, options, data: JSON.parse(options.body)});
    if (fail) throw new Error('Vendor not found');
  },
  loadAll: async () => { reloads++; },
  reportError: (_form, error) => errors.push(error.message),
  releaseForm: f => { delete f.dataset.busy; f.button.disabled = false; },
});
const event = {currentTarget: form, preventDefault() {}};
const fields = vendor => ({title: 'Repair light', property_id: '7', vendor_id: vendor, priority: 'normal', target_date: '2026-12-01'});
(async () => {
  for (const vendor of ['22', '']) {
    form.values = fields(vendor); await submit(event);
    const sent = requests.at(-1);
    assert.equal(sent.url, '/products/fieldnest/work-orders');
    assert.equal(sent.options.method, 'POST');
    assert.equal(sent.data.vendor_id, vendor ? 22 : null);
    assert.equal(sent.data.target_date, '2026-12-01');
    assert.equal(sent.data.property_id, 7);
  }
  fail = true; form.values = fields('22'); await submit(event);
  assert.equal(form.values.vendor_id, '22', 'retain selection when the API rejects the assignment');
  assert.equal(form.values.target_date, '2026-12-01');
  assert.equal(form.resets, 2);
  assert.equal(form.closes, 2);
  assert.equal(reloads, 2);
  assert.deepEqual(errors, ['Vendor not found']);
  assert.equal(form.button.disabled, false);
  assert.equal(form.dataset.busy, undefined);
  console.log('FieldNest creation vendor: optional assignment, numeric payload, target date retention, escaped options, workspace refresh, and failure recovery passed');
})().catch(error => { console.error(error); process.exitCode = 1; });
