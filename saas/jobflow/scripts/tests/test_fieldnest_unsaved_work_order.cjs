const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const app = path.resolve(__dirname, '../../app');
const html = fs.readFileSync(path.join(app, 'fieldnest-workspace.html'), 'utf8');
const asset = html.match(/src="\/(assets\/fieldnest-workspace-[a-f0-9]+\.js)"/)[1];
const source = fs.readFileSync(path.join(app, asset), 'utf8');
function block(start, end) {
  const a = source.indexOf(start), b = source.indexOf(end, a);
  assert.ok(a >= 0 && b > a);
  return source.slice(a, b);
}
const fields = Object.fromEntries(['title','status','priority','vendor_id','resident_id','unit','target_date','description'].map(key => [key, {value: ''}]));
const nodes = new Map();
const get = id => {if (!nodes.has(id)) nodes.set(id, {addEventListener() {}}); return nodes.get(id);};
const dialog = {id: 'workOrderDetailDialog', open: false, events: {}, message: {},
  addEventListener(type, handler) {(this.events[type] ||= []).push(handler);},
  querySelector() {return this.message;},
  showModal() {this.open = true;},
  close() {this.open = false; for (const handler of this.events.close || []) handler();},
};
nodes.set(dialog.id, dialog);
const form = {dataset: {}, events: {}, elements: {namedItem: key => fields[key]},
  reset() {for (const field of Object.values(fields)) field.value = '';},
  addEventListener(type, handler) {this.events[type] = handler;},
  querySelectorAll: () => [], closest: () => dialog,
};
nodes.set('workOrderDetailForm', form);
const order = {id: 1, property_id: 2, title: 'Repair light', status: 'open', priority: 'normal', vendor_id: null, resident_id: null, unit: '', target_date: null, description: null};
const state = {tenantId: 3, orders: [order], properties: [{id: 2, name: 'Building A'}], vendors: [], residents: [], clients: []};
let confirmed = false, prompts = 0, fail = false, pending = null, requests = 0;
const messages = [];
const clicks = [];
const context = vm.createContext({state, $: get,
  window: {confirm: () => {prompts++; return confirmed;}},
  document: {addEventListener: (type, handler) => {if (type === 'click') clicks.push(handler);}},
  loadManagerPhotos() {}, render() {}, renderOverview() {}, applySearch() {},
  msg: (_id, message) => messages.push(message),
  payload: () => Object.fromEntries(Object.entries(fields).map(([key, field]) => [key, field.value])),
  request: async (_url, options) => {
    requests++; if (pending) await pending;
    if (fail) throw new Error('Save failed');
    return {...order, ...JSON.parse(options.body)};
  },
  reportError: (_form, error) => {dialog.message.textContent = error.message;},
});
vm.runInContext(block('  const esc =', '  const msg =') + block('  function vendorInsuranceStatus(', '  function workOrderListMarkup(') +
  block('  let workOrderDraftBaseline =', '  let linkProperty ='), context);
const closer = source.split('\n').find(line => line.includes('const opener = event.target.closest("[data-open]")'));
assert.ok(closer); vm.runInContext(closer, context);
const clickClose = () => clicks.forEach(handler => handler({target: {closest: selector => selector === '[data-close]' ? {closest: () => dialog} : null}}));
const escape = () => {
  const event = {prevented: false, preventDefault() {this.prevented = true;}};
  for (const handler of dialog.events.cancel) handler(event);
  if (!event.prevented) dialog.close();
  return event.prevented;
};
const submit = () => form.events.submit({preventDefault() {}, currentTarget: form});
(async () => {
  context.openWorkOrder(1); clickClose();
  assert.equal(dialog.open, false); assert.equal(prompts, 0);
  context.openWorkOrder(1);
  for (const [name, field] of Object.entries(fields)) {
    const before = field.value; field.value = before + 'changed';
    assert.equal(context.canCloseWorkOrder(), false, name + ' must count as an edit');
    field.value = before;
    const count = prompts;
    assert.equal(context.canCloseWorkOrder(), true);
    assert.equal(prompts, count, 'reverted changes must not prompt');
  }
  get('managerTrackingLink').value = 'https://example.test/private-link';
  const count = prompts;
  assert.equal(context.canCloseWorkOrder(), true);
  assert.equal(prompts, count, 'readonly tracking results must not mark editable work dirty');
  fields.title.value = 'Changed title'; clickClose();
  assert.equal(dialog.open, true); assert.equal(fields.title.value, 'Changed title');
  assert.equal(escape(), true); assert.equal(dialog.open, true);
  confirmed = true; clickClose(); assert.equal(dialog.open, false);
  context.openWorkOrder(1); assert.equal(fields.title.value, 'Repair light');
  assert.equal(escape(), false); assert.equal(dialog.open, false);

  context.openWorkOrder(1); fields.description.value = 'Keep this draft';
  fail = true; await submit();
  assert.equal(dialog.open, true); assert.equal(fields.description.value, 'Keep this draft');
  confirmed = false; clickClose(); assert.equal(dialog.open, true);
  fail = false; let release;
  pending = new Promise(resolve => {release = resolve;});
  const saving = submit(); const beforeSavingPrompt = prompts;
  clickClose(); assert.equal(dialog.open, true);
  assert.equal(escape(), true); assert.equal(prompts, beforeSavingPrompt);
  assert.match(dialog.message.textContent, /Please wait/);
  release(); await saving;
  assert.equal(dialog.open, false);
  assert.equal(prompts, beforeSavingPrompt, 'successful save closes without discard confirmation');
  assert.equal(state.orders[0].description, 'Keep this draft');
  assert.equal(requests, 2); assert.equal(form.dataset.busy, undefined);

  context.openWorkOrder(1); fields.title.value = 'Private unsaved text';
  const beforeForcedClose = prompts;
  dialog.close(); // Workspace switching and sign-out close dialogs programmatically.
  assert.equal(prompts, beforeForcedClose);
  context.openWorkOrder(1); assert.equal(context.canCloseWorkOrder(), true);
  const otherDialog = {id: 'propertyFormDialog', close() {this.closed = true;}};
  clicks.forEach(handler => handler({target: {closest: selector => selector === '[data-close]' ? {closest: () => otherDialog} : null}}));
  assert.equal(otherDialog.closed, true);
  console.log('FieldNest unsaved edits: close/Escape, discard/cancel, all editable fields, reverted/readonly values, save failure/success, busy guard, and forced close passed');
})().catch(error => {console.error(error); process.exitCode = 1;});
