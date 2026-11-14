const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const app = path.resolve(__dirname, '../../app');
const html = fs.readFileSync(path.join(app, 'fieldnest-workspace.html'), 'utf8');
const script = html.match(/src="\/(assets\/fieldnest-workspace-[a-f0-9]+\.js)"/)[1];
const source = fs.readFileSync(path.join(app, script), 'utf8');
const formMarkup = html.match(/<form[^>]*id="workOrderForm"[^>]*>([\s\S]*?)<\/form>/)[1];
assert.match(formMarkup, /Target date \(optional, UTC\)/);
const input = formMarkup.match(/<input[^>]*name="target_date"[^>]*>/)[0];
assert.match(input, /type="date"/);
assert.doesNotMatch(input, /required|min=/);

// Exercise the shipped submit handler, including its async success/failure paths.
const start = source.indexOf('  $("workOrderForm").addEventListener("submit",');
const end = source.indexOf('\n', start);
assert.ok(start >= 0 && end > start);
let submit;
let fail = false;
let pending = null;
const requests = [];
let reloads = 0;
let errors = [];
const form = {
  dataset: {}, button: {disabled: false}, values: {}, resets: 0, closes: 0,
  addEventListener(type, handler) { assert.equal(type, 'submit'); submit = handler; },
  querySelector() { return this.button; },
  closest() { return {close: () => this.closes++}; },
  reset() { this.resets++; this.values = {}; },
};
vm.runInNewContext(source.slice(start, end), {
  $: () => form,
  state: {properties: [{id: 7}]},
  payload: f => ({...f.values}),
  request: async (url, options) => {
    requests.push({url, options, data: JSON.parse(options.body)});
    if (pending) await pending;
    if (fail) throw new Error('Connection lost');
    return {};
  },
  loadAll: async () => { reloads++; },
  reportError: (_form, error) => errors.push(error.message),
  releaseForm: f => { delete f.dataset.busy; f.button.disabled = false; },
});
const event = {currentTarget: form, preventDefault() {}};
const fields = date => ({title: 'Repair light', property_id: '7', priority: 'normal', unit: '', description: '', target_date: date});

(async () => {
  for (const date of ['2026-11-13', '2026-11-14', '2026-12-01', '']) {
    form.values = fields(date);
    await submit(event);
    assert.equal(requests.at(-1).url, '/products/fieldnest/work-orders');
    assert.equal(requests.at(-1).options.method, 'POST');
    assert.equal(requests.at(-1).data.target_date, date || null);
    assert.equal(requests.at(-1).data.property_id, 7);
    assert.equal(form.button.disabled, false);
  }
  assert.equal(reloads, 4);
  assert.equal(form.closes, 4);
  fail = true;
  form.values = fields('2026-12-01');
  await submit(event);
  assert.equal(form.values.target_date, '2026-12-01');
  assert.equal(form.closes, 4);
  assert.deepEqual(errors, ['Connection lost']);
  assert.equal(form.button.disabled, false);
  fail = false;
  let release;
  pending = new Promise(resolve => { release = resolve; });
  const saving = submit(event);
  const count = requests.length;
  await submit(event);
  assert.equal(requests.length, count, 'duplicate submit must not create another request');
  release(); await saving;
  assert.equal(form.dataset.busy, undefined);
  console.log('FieldNest creation target date: past, today, future, optional, failure retention, and duplicate guard passed');
})().catch(error => { console.error(error); process.exitCode = 1; });
