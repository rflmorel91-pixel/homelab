const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const root = path.resolve(__dirname, "../..");
const html = fs.readFileSync(path.join(root, "app/fieldnest-resident.html"), "utf8");
const asset = html.match(/assets\/fieldnest-resident-[a-f0-9]+\.js/)[0];
const source = fs.readFileSync(path.join(root, "app", asset), "utf8");
const tick = () => new Promise(resolve => setImmediate(resolve));
function harness(token) {
  const h = {calls: [], status: "scheduled", unavailable: false, revoked: []};
  const elements = new Map();
  h.element = id => {
    if (!elements.has(id)) elements.set(id, {
      hidden: id === "trackingContent", children: [], textContent: "", events: {},
      addEventListener(event, fn) {this.events[event] = fn;},
      replaceChildren() {this.children = [];},
      append(child) {this.children.push(child);}
    });
    return elements.get(id);
  };
  vm.runInNewContext(source, {
    document: {getElementById: h.element, createElement: () => ({})},
    window: {addEventListener() {}},
    location: {hash: token ? "#" + token : ""},
    URL: {createObjectURL: () => "blob:private-photo", revokeObjectURL: url => h.revoked.push(url)},
    async fetch(url, options) {
      h.calls.push({url, options});
      if (h.unavailable) return {ok: false, status: 404, json: async () => ({detail: "Private link unavailable"})};
      if (url.endsWith("/context")) return {ok: true, json: async () => ({
        title: "Kitchen sink", reference: "FN-6", unit: "3B", status: h.status,
        received_at: "2026-11-04T12:00:00Z", updated_at: "2026-11-04T13:00:00Z",
        photos: [{id: "photo-1"}]
      })};
      return {ok: true, blob: async () => ({})};
    }
  });
  return h;
}
(async () => {
  const missing = harness(""); await tick();
  assert.equal(missing.calls.length, 0);
  assert.equal(missing.element("trackingContent").hidden, true);
  const token = "a".repeat(43), h = harness(token); await tick(); await tick();
  assert.equal(h.element("trackingStatus").textContent, "Scheduled");
  assert.equal(h.element("trackingPhotos").children.length, 1);
  assert.equal(h.element("trackingPhotos").children[0].src, "blob:private-photo");
  assert(h.calls.every(c => c.options.credentials === "omit"));
  assert(h.calls.every(c => !c.url.includes(token) && JSON.parse(c.options.body).token === token));
  h.status = "completed";
  await h.element("refreshTracking").events.click();
  assert.equal(h.element("trackingStatus").textContent, "Completed");
  assert(h.revoked.length > 0);
  h.unavailable = true;
  await h.element("refreshTracking").events.click();
  assert.equal(h.element("trackingContent").hidden, true);
  assert.equal(h.element("trackingPhotos").children.length, 0);
  assert.match(h.element("trackingMessage").textContent, /unavailable/);
  console.log("Resident tracking page checks passed: private link, photos, live status, revocation and cleanup.");
})().catch(error => {console.error(error); process.exitCode = 1;});
