const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const app = path.resolve(__dirname, '../../app');
const html = fs.readFileSync(path.join(app, 'fieldnest-workspace.html'), 'utf8');
const asset = html.match(/assets\/fieldnest-workspace-[a-f0-9]+\.js/)[0];
const source = fs.readFileSync(path.join(app, asset), 'utf8');
const code = source.slice(source.indexOf('  let editingProperty = null;'), source.indexOf('  function workOrderSummaryText('));
function setup() {
  const fields = Object.fromEntries(['name', 'address', 'total_units', 'property_type'].map(key => [key, {value: ''}]));
  const handlers = {}, clicks = [], requests = [], messages = [], pending = [];
  const button = {disabled: false}, message = {textContent: ''};
  const form = {dataset: {}, elements: {namedItem: key => fields[key]}, reset() {}, querySelectorAll: () => [button], addEventListener: (name, fn) => handlers[name] = fn};
  const dialog = {open: false, querySelector: () => message, showModal() {this.open = true;}, close() {this.open = false; handlers.close();}, addEventListener: (name, fn) => handlers[name] = fn};
  const state = {tenantId: 7, properties: [{id: 1, name: 'Oak', address: '10 Main', total_units: 4, property_type: 'residential'}], orders: [{id: 2, property_id: 1}]};
  let confirm = false, renders = 0;
  const context = vm.createContext({state, $: id => ({propertyEditForm: form, propertyEditDialog: dialog})[id],
    document: {addEventListener: (name, fn) => clicks.push(fn)}, window: {confirm: () => confirm},
    msg: (...args) => messages.push(args), reportError: (_, error) => message.textContent = error.message,
    payload: () => Object.fromEntries(Object.entries(fields).map(([key, field]) => [key, String(field.value)])),
    render: () => renders++, renderOverview() {}, applySearch() {},
    request: (url, options) => {requests.push({url, options}); return new Promise((resolve, reject) => pending.push({resolve, reject}));}});
  vm.runInContext(code, context);
  return {fields, form, dialog, state, message, button, requests, pending, messages, handlers,
    open: () => clicks[0]({target: {closest: () => ({dataset: {editProperty: '1'}})}}),
    submit: () => handlers.submit({preventDefault() {}, currentTarget: form}),
    canClose: () => vm.runInContext('canClosePropertyEdit()', context),
    confirm: value => confirm = value, renders: () => renders};
}
(async () => {
  let s = setup(); s.open();
  assert.equal(s.fields.name.value, 'Oak'); assert.equal(s.canClose(), true);
  s.fields.name.value = ' New Oak '; s.fields.total_units.value = '8';
  assert.equal(s.canClose(), false); s.confirm(true); assert.equal(s.canClose(), true);
  let prevented = false; s.confirm(false); s.handlers.cancel({preventDefault() {prevented = true;}}); assert.equal(prevented, true);
  const save = s.submit(); await s.submit();
  assert.equal(s.requests.length, 1); assert.equal(s.canClose(), false); assert.equal(s.button.disabled, true);
  assert.equal(s.requests[0].url, '/products/fieldnest/properties/1');
  assert.equal(s.requests[0].options.method, 'PATCH'); assert.equal(s.requests[0].options.headers['X-Tenant-ID'], '7');
  assert.deepEqual(JSON.parse(s.requests[0].options.body), {name: 'New Oak', address: '10 Main', total_units: 8, property_type: 'residential'});
  s.pending[0].resolve({id: 1, name: 'New Oak', address: '10 Main', total_units: 8, property_type: 'residential'}); await save;
  assert.equal(s.state.properties[0].name, 'New Oak'); assert.equal(s.state.orders[0].property_id, 1); assert.equal(s.renders(), 1); assert.equal(s.dialog.open, false);
  s = setup(); s.open(); s.fields.name.value = 'Draft'; const failure = s.submit(); s.pending[0].reject(new Error('Save failed')); await failure;
  assert.equal(s.fields.name.value, 'Draft'); assert.equal(s.dialog.open, true); assert.equal(s.button.disabled, false); assert.equal(s.message.textContent, 'Save failed'); assert.equal(s.state.properties[0].name, 'Oak');
  s.fields.name.value = ' '; await s.submit(); assert.equal(s.requests.length, 1);
  s = setup(); s.open(); const stale = s.submit(); s.dialog.close(); s.state.tenantId = 8; s.state.properties = [{id: 1, name: 'Other', address: 'Elsewhere', total_units: 2, property_type: 'commercial'}]; s.open();
  const fresh = s.submit(); s.pending[0].resolve({id: 1, name: 'Stale'}); await stale;
  assert.equal(s.state.properties[0].name, 'Other'); assert.equal(s.form.dataset.busy, '1'); assert.equal(s.button.disabled, true);
  s.pending[1].resolve({...s.state.properties[0], name: 'Current'}); await fresh; assert.equal(s.state.properties[0].name, 'Current');
  s = setup(); s.open(); s.state.tenantId = 9; await s.submit(); assert.equal(s.requests.length, 0);
  assert.match(html, /id="propertyEditDialog" aria-labelledby="propertyEditTitle"/);
  assert.match(source, /data-edit-property="\$\{esc\(p.id\)\}"/);
  assert.match(source, /dialog.id !== "propertyEditDialog" \|\| canClosePropertyEdit\(\)/);
  console.log('FieldNest property edit: prefill, partial ownership, numeric payload, duplicate guard, failure retention, unsaved dismissal, workspace races, and linked identity passed');
})().catch(error => {console.error(error); process.exitCode = 1;});
