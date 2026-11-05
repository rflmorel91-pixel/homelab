const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const crypto = require("node:crypto");
const root = path.resolve(__dirname, "../..");
const html = fs.readFileSync(path.join(root, "app/fieldnest-report.html"), "utf8");
const asset = html.match(/assets\/fieldnest-report-[a-f0-9]+\.js/)[0];
const source = fs.readFileSync(path.join(root, "app", asset), "utf8");
const tick = () => new Promise(resolve => setImmediate(resolve));
function harness(token, failOnce = false, receiptEmail = "") {
  const elements = new Map(), calls = [];
  const element = id => {
    if (!elements.has(id)) elements.set(id, {
      hidden: ["residentForm", "successPanel"].includes(id), disabled: false,
      textContent: "", events: {}, addEventListener(name, fn) {this.events[name] = fn;},
      reset() {this.wasReset = true;}, focus() {this.wasFocused = true;},
      elements: {namedItem() { return {focus() {}}; }}
    });
    return elements.get(id);
  };
  let postCount = 0;
  vm.runInNewContext(source, {
    document: {getElementById: element}, location: {hash: token ? "#" + token : ""},
    crypto: {randomUUID: () => crypto.randomUUID(), getRandomValues: bytes => crypto.randomFillSync(bytes)},
    btoa: value => Buffer.from(value, "binary").toString("base64"),
    FormData: class {entries() {return Object.entries({
      name: "Demo", contact: "demo@example.test", unit: "3B", receipt_email: receiptEmail,
      title: "Slow sink", description: "Synthetic maintenance issue."
    });}},
    async fetch(url, options) {
      const payload = JSON.parse(options.body); calls.push({url, payload, options});
      if (url.endsWith("/context")) return {ok: true, status: 200, json: async () => ({property_name: "Maple Court"})};
      if (failOnce && ++postCount === 1) throw new Error("Network interrupted");
      return {ok: true, status: 201, json: async () => ({reference: "FN-24", status: "received", tracking_path: "/fieldnest/resident#" + payload.tracking_secret})};
    }
  });
  return {element, calls};
}
(async () => {
  const invalid = harness(""); await tick();
  assert.equal(invalid.calls.length, 0);
  assert.equal(invalid.element("residentForm").hidden, true);
  const h = harness("a".repeat(43), true); await tick();
  assert.equal(h.element("residentForm").hidden, false);
  assert.equal(h.element("propertyName").textContent, "Maple Court");
  const submit = () => h.element("residentForm").events.submit({preventDefault() {}});
  await submit();
  assert.equal(h.element("residentForm").wasReset, undefined);
  assert.match(h.element("pageMessage").textContent, /Network interrupted/);
  await submit();
  assert.equal(h.calls[1].payload.submission_id, h.calls[2].payload.submission_id);
  assert.equal(h.element("reference").textContent, "FN-24");
  assert.equal(h.element("trackingLinkPanel").hidden, false);
  assert.match(h.calls[1].payload.tracking_secret, /^[A-Za-z0-9_-]{43}$/);
  assert.equal(h.calls[1].payload.tracking_secret, h.calls[2].payload.tracking_secret);
  assert.equal(h.element("successPanel").hidden, false);
  assert.equal(h.element("residentForm").hidden, true);
  h.element("anotherButton").events.click();
  await submit();
  assert.notEqual(h.calls[2].payload.submission_id, h.calls[3].payload.submission_id);
  assert.notEqual(h.calls[2].payload.tracking_secret, h.calls[3].payload.tracking_secret);
  assert.equal(h.calls[1].payload.receipt_email, null);
  const optedIn = harness("a".repeat(43), false, "receipt@example.test"); await tick();
  await optedIn.element("residentForm").events.submit({preventDefault() {}});
  assert.equal(optedIn.calls[1].payload.receipt_email, "receipt@example.test");
  assert(h.calls.every(c => c.options.credentials === "omit"));
  assert(h.calls.every(c => !c.url.includes("a".repeat(43))));
  console.log("Resident form checks passed: missing link, context, retry, confirmation, new report, token privacy.");
})().catch(error => {console.error(error); process.exitCode = 1;});
