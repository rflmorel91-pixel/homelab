const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const app = path.resolve(__dirname, '../../app');
const html = fs.readFileSync(path.join(app, 'fieldnest-workspace.html'), 'utf8');
const asset = html.match(/assets\/fieldnest-workspace-[a-f0-9]+\.js/)[0];
const source = fs.readFileSync(path.join(app, asset), 'utf8');
const code = source.slice(source.indexOf('  let editingVendor = null;'), source.indexOf('  let editingProperty = null;'));
function setup() {
  const fields = Object.fromEntries(['name', 'trade', 'phone', 'email', 'insurance_expires'].map(key => [key, {value: ''}]));
  const handlers = {}, clicks = [], requests = [], messages = [], pending = [];
  const button = {disabled: false}, message = {textContent: ''};
  const controls = [button, ...Object.values(fields)];
  const form = {dataset: {}, elements: {namedItem: key => fields[key]}, reset() {}, querySelectorAll: () => controls, addEventListener: (name, fn) => handlers[name] = fn};
  const dialog = {open: false, querySelector: () => message, showModal() {this.open = true;}, close() {this.open = false; handlers.close();}, addEventListener: (name, fn) => handlers[name] = fn};
  const state = {tenantId: 7, vendors: [{id: 1, name: 'Oak', trade: 'Plumbing', phone: '555-0100', email: 'vendor@example.test', insurance_expires: '2026-12-01'}], orders: [{id: 2, vendor_id: 1}]};
  let confirm = false, renders = 0;
  const context = vm.createContext({state, $: id => ({vendorEditForm: form, vendorEditDialog: dialog})[id],
    document: {addEventListener: (name, fn) => clicks.push(fn)}, window: {confirm: () => confirm},
    msg: (...args) => messages.push(args), reportError: (_, error) => message.textContent = error.message,
    payload: () => Object.fromEntries(Object.entries(fields).map(([key, field]) => [key, String(field.value)])),
    render: () => renders++, renderOverview() {}, applySearch() {},
    request: (url, options) => {requests.push({url, options}); return new Promise((resolve, reject) => pending.push({resolve, reject}));}});
  vm.runInContext(code, context);
  return {fields, form, dialog, state, message, button, requests, pending, messages, handlers,
    open: () => clicks[0]({target: {closest: () => ({dataset: {editVendor: '1'}})}}),
    submit: () => handlers.submit({preventDefault() {}, currentTarget: form}),
    canClose: () => vm.runInContext('canCloseVendorEdit()', context),
    confirm: value => confirm = value, renders: () => renders};
}
(async () => {
  let s = setup(); s.open();
  assert.equal(s.fields.name.value, 'Oak'); assert.equal(s.canClose(), true);
  s.fields.name.value = ' New Oak ';
  assert.equal(s.canClose(), false); s.confirm(true); assert.equal(s.canClose(), true);
  let prevented = false; s.confirm(false); s.handlers.cancel({preventDefault() {prevented = true;}}); assert.equal(prevented, true);
  const save = s.submit(); await s.submit();
  assert.equal(s.requests.length, 1); assert.equal(s.canClose(), false); assert.equal(s.button.disabled, true);
  assert.ok(Object.values(s.fields).every(field => field.disabled));
  assert.equal(s.requests[0].url, '/products/fieldnest/vendors/1');
  assert.equal(s.requests[0].options.method, 'PATCH'); assert.equal(s.requests[0].options.headers['X-Tenant-ID'], '7');
  assert.deepEqual(JSON.parse(s.requests[0].options.body), {name: 'New Oak', trade: 'Plumbing', phone: '555-0100', email: 'vendor@example.test', insurance_expires: '2026-12-01'});
  s.pending[0].resolve({id: 1, name: 'New Oak', trade: 'Plumbing', phone: '555-0100', email: 'vendor@example.test', insurance_expires: '2026-12-01'}); await save;
  assert.equal(s.state.vendors[0].name, 'New Oak'); assert.equal(s.state.orders[0].vendor_id, 1); assert.equal(s.renders(), 1); assert.equal(s.dialog.open, false);
  s = setup(); s.open(); s.fields.name.value = 'Draft'; const failure = s.submit(); s.pending[0].reject(new Error('Save failed')); await failure;
  assert.equal(s.fields.name.value, 'Draft'); assert.equal(s.dialog.open, true); assert.equal(s.button.disabled, false); assert.equal(s.message.textContent, 'Save failed'); assert.equal(s.state.vendors[0].name, 'Oak');
  s.fields.name.value = ' '; await s.submit(); assert.equal(s.requests.length, 1);
  s = setup(); s.open(); const stale = s.submit(); s.dialog.close(); s.state.tenantId = 8; s.state.vendors = [{id: 1, name: 'Other', trade: 'Electrical', phone: null, email: null, insurance_expires: null}]; s.open();
  const fresh = s.submit(); s.pending[0].resolve({id: 1, name: 'Stale'}); await stale;
  assert.equal(s.state.vendors[0].name, 'Other'); assert.equal(s.form.dataset.busy, '1'); assert.equal(s.button.disabled, true);
  s.pending[1].resolve({...s.state.vendors[0], name: 'Current'}); await fresh; assert.equal(s.state.vendors[0].name, 'Current');
  s = setup(); s.open(); s.fields.phone.value = ' '; s.fields.email.value = ''; s.fields.insurance_expires.value = '';
  const clear = s.submit(); const cleared = JSON.parse(s.requests[0].options.body);
  for (const key of ['phone','email','insurance_expires']) assert.equal(cleared[key], null);
  s.pending[0].reject(new Error('Try again')); await clear;
  assert.equal(s.fields.phone.value, ' '); assert.ok(Object.values(s.fields).every(field => !field.disabled));
  const retry = s.submit(); assert.equal(s.requests.length, 2);
  s.pending[1].resolve({...s.state.vendors[0], phone: null, email: null, insurance_expires: null}); await retry;
  assert.equal(s.state.vendors[0].insurance_expires, null);
  s = setup(); s.open(); s.state.tenantId = 9; await s.submit(); assert.equal(s.requests.length, 0);
  assert.match(html, /id="vendorEditDialog" aria-labelledby="vendorEditTitle"/);
  assert.match(source, /data-edit-vendor="\$\{esc\(v.id\)\}"/);
  assert.match(source, /dialog.id !== "vendorEditDialog" \|\| canCloseVendorEdit\(\)/);
  console.log('FieldNest vendor edit: prefill, optional contact and expiry payload, duplicate guard, failure retention, unsaved dismissal, workspace races, and linked identity passed');
})().catch(error => {console.error(error); process.exitCode = 1;});
