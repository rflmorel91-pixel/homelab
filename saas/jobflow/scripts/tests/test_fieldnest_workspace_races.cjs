const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const root = path.resolve(__dirname, "../..");
const html = fs.readFileSync(path.join(root, "app/fieldnest-workspace.html"), "utf8");
const asset = html.match(/assets\/fieldnest-workspace-[a-f0-9]+\.js/)[0];
const source = fs.readFileSync(path.join(root, "app", asset), "utf8");
const prefix = source.slice(source.indexOf("  const API"), source.indexOf("  function render()"));

function harness() {
  const pending = [];
  const elements = new Map();
  const context = vm.createContext({
    document: {getElementById(id) {
      if (!elements.has(id)) elements.set(id, {textContent: "", classList: {toggle() {}}});
      return elements.get(id);
    }},
    localStorage: {setItem() {}},
    fetch(url, options) {
      return new Promise((resolve, reject) => pending.push({
        tenant: options.headers["X-Tenant-ID"], resolve, reject
      }));
    }
  });
  vm.runInContext(prefix + `
    function render() {}
    function renderOverview() {}
    function applySearch() {}
    globalThis.test = {state, loadAll};
  `, context);
  const {state, loadAll} = context.test;
  state.clients = [{tenant_id: 1, name: "A"}, {tenant_id: 2, name: "B"}];
  const resolve = (batch, name) => batch.forEach(p => p.resolve({
    ok: true, status: 200, json: async () => [{name}]
  }));
  return {state, loadAll, pending, resolve};
}

(async () => {
  // A slower previous-company response cannot replace the current selection.
  {
    const h = harness();
    h.state.tenantId = "1";
    const a = h.loadAll(), first = h.pending.splice(0);
    h.state.tenantId = "2";
    const b = h.loadAll(), second = h.pending.splice(0);
    assert(first.every(p => p.tenant === "1"));
    assert(second.every(p => p.tenant === "2"));
    h.resolve(second, "B"); await b;
    h.resolve(first, "A"); await a;
    assert.equal(h.state.properties[0].name, "B");
  }
  // Failed switch clears the prior portfolio; it cannot remain actionable.
  {
    const h = harness();
    h.state.tenantId = "2";
    h.state.properties = [{name: "A"}]; h.state.orders = [{id: 1}];
    const load = h.loadAll();
    assert.equal(h.state.properties.length, 0);
    assert.equal(h.state.orders.length, 0);
    h.pending.forEach(p => p.reject(new Error("offline")));
    await assert.rejects(load, /offline/);
    assert.equal(h.state.properties.length, 0);
  }
  // Older errors are ignored after a newer selection succeeds.
  {
    const h = harness();
    h.state.tenantId = "1"; const a = h.loadAll(), first = h.pending.splice(0);
    h.state.tenantId = "2"; const b = h.loadAll(), second = h.pending.splice(0);
    h.resolve(second, "B"); await b;
    first.forEach(p => p.reject(new Error("old error"))); await a;
    assert.equal(h.state.orders[0].name, "B");
  }
  // Two refreshes for the same tenant must also respect request order.
  {
    const h = harness();
    h.state.tenantId = "1"; const a = h.loadAll(), first = h.pending.splice(0);
    const b = h.loadAll(), second = h.pending.splice(0);
    h.resolve(second, "new"); await b;
    h.resolve(first, "old"); await a;
    assert.equal(h.state.properties[0].name, "new");
  }
  console.log("Workspace race checks: 4 passed");
})().catch(error => { console.error(error); process.exitCode = 1; });
