(() => {
  const API = "/api/v1";
  const $ = (id) => document.getElementById(id);
  const state = { tenantId: null, loadVersion: 0, clients: [], properties: [], residents: [], vendors: [], orders: [] };
  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const msg = (id, text, good = false) => { const el = $(id); el.textContent = text; el.classList.toggle("success", good); };

  async function request(path, options = {}) {
    const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
    if (state.tenantId && !headers["X-Tenant-ID"]) headers["X-Tenant-ID"] = String(state.tenantId);
    const response = await fetch(`${API}${path}`, { credentials: "same-origin", ...options, headers });
    if (!response.ok) {
      let detail = `Request failed (${response.status})`;
      try { const body = await response.json(); detail = body.detail || detail; } catch (_) {}
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    return response.status === 204 ? null : response.json();
  }

  function showLogin() { document.querySelectorAll("dialog[open]").forEach(d => d.close()); $("loginPanel").hidden = false; $("appPanel").hidden = true; $("logoutButton").hidden = true; $("tenantLabel").textContent = ""; }
  function showApp() { route(); $("loginPanel").hidden = true; $("appPanel").hidden = false; $("logoutButton").hidden = false; }

  async function discover() {
    const access = await request("/auth/products/fieldnest/access");
    state.clients = access.clients || [];
    if (!state.clients.length) throw new Error("No active FieldNest company workspace is connected to this account yet.");
    const select = $("tenantSelect");
    select.innerHTML = state.clients.map(c => `<option value="${esc(c.tenant_id)}">${esc(c.name)} · ${esc(c.role)}</option>`).join("");
    const saved = localStorage.getItem("fieldnest_tenant_id");
    state.tenantId = state.clients.some(c => String(c.tenant_id) === saved) ? saved : String(state.clients[0].tenant_id);
    select.value = state.tenantId;
    await loadAll();
  }

  async function loadAll() {
    const tenantId = String(state.tenantId);
    const version = ++state.loadVersion;
    const isCurrent = () => version === state.loadVersion && tenantId === String(state.tenantId);
    const client = state.clients.find(c => String(c.tenant_id) === tenantId);
    $("tenantLabel").textContent = client ? client.name : "";
    localStorage.setItem("fieldnest_tenant_id", tenantId);
    // Remove the previous company's records before awaiting the next response.
    Object.assign(state, { properties: [], residents: [], vendors: [], orders: [] });
    render(); renderOverview(); applySearch();
    msg("appMessage", "Loading workspace…", true);
    try {
      const options = { headers: { "X-Tenant-ID": tenantId } };
      const [properties, residents, vendors, orders] = await Promise.all([
        request("/products/fieldnest/properties", options), request("/products/fieldnest/residents", options),
        request("/products/fieldnest/vendors", options), request("/products/fieldnest/work-orders", options)
      ]);
      if (!isCurrent()) return;
      Object.assign(state, { properties, residents, vendors, orders });
      render(); renderOverview(); applySearch();
      msg("appMessage", "", true);
    } catch (error) {
      if (isCurrent()) throw error;
    }
  }

  function render() {
    $("propertyCount").textContent = state.properties.length;
    $("residentCount").textContent = state.residents.length;
    $("vendorCount").textContent = state.vendors.length;
    $("openCount").textContent = state.orders.filter(x => !["completed", "cancelled"].includes(x.status)).length;
    $("properties").innerHTML = state.properties.length ? state.properties.map(p => `<div class="record"><span><strong>${esc(p.name)}</strong><small>${esc(p.address)} · ${esc(p.total_units)} units</small></span><span class="badge">${esc(p.property_type)}</span>${state.clients.find(c => String(c.tenant_id) === String(state.tenantId))?.role === "owner" ? `<button type="button" class="button secondary" data-resident-link="${esc(p.id)}">Resident request link</button>` : ""}</div>`).join("") : `<div class="empty-state">Add your first property to start organizing work.</div>`;
    $("vendors").innerHTML = state.vendors.length ? state.vendors.map(v => `<div class="record"><span><strong>${esc(v.name)}</strong><small>${esc(v.trade)}${v.email ? ` · ${esc(v.email)}` : ""}</small></span><span class="badge">${v.insurance_expires ? `Ins. ${esc(v.insurance_expires)}` : "Vendor"}</span></div>`).join("") : `<div class="empty-state">Your trusted service contacts will appear here.</div>`;
    $("residents").innerHTML = state.residents.length ? state.residents.map(r => { const p = state.properties.find(x => x.id === r.property_id); return `<div class="record"><span><strong>${esc(r.name)}</strong><small>${esc(p?.name || "Property")} · Unit ${esc(r.unit)}${r.email ? ` · ${esc(r.email)}` : ""}</small></span></div>`; }).join("") : `<div class="empty-state">Add residents to connect people with the properties they call home.</div>`;
    $("workOrders").innerHTML = state.orders.length ? state.orders.map(w => { const p = state.properties.find(x => x.id === w.property_id); return `<button type="button" class="record work-order-row" data-order-id="${esc(w.id)}"><span><strong>${esc(w.title)}</strong><small>${esc(p?.name || "Property")} ${w.unit ? `· Unit ${esc(w.unit)}` : ""} · ${esc(w.priority)} priority</small></span><span class="badge">${esc(w.status.replaceAll("_", " "))}</span></button>`; }).join("") : `<div class="empty-state">No work orders yet. Add the next maintenance item above.</div>`;
    const pOpts = state.properties.map(p => `<option value="${esc(p.id)}">${esc(p.name)}</option>`).join("");
    $("workProperty").innerHTML = pOpts || `<option value="">Add a property first</option>`;
    $("residentProperty").innerHTML = pOpts || `<option value="">Add a property first</option>`;
  }

  function payload(form) { return Object.fromEntries(new FormData(form).entries()); }
  $("loginForm").addEventListener("submit", async (event) => {
    event.preventDefault(); const form = event.currentTarget; if (form.dataset.busy) return; form.dataset.busy = "1"; form.querySelector("button[type=submit], button").disabled = true; msg("loginMessage", "Signing in…", true);
    try {
      const data = payload(form);
      await request("/auth/login", { method: "POST", body: JSON.stringify(data) });
      form.reset(); await discover(); showApp();
    } catch (error) { msg("loginMessage", error.message); } finally { releaseForm(form); }
  });
  $("tenantSelect").addEventListener("change", async (event) => { document.querySelectorAll("dialog[open]").forEach(d => d.close()); state.tenantId = event.target.value; try { await loadAll(); } catch (e) { msg("appMessage", e.message); } });
  $("logoutButton").addEventListener("click", async () => { try { await request("/auth/logout", { method: "POST" }); } finally { state.loadVersion++; state.tenantId = null; Object.assign(state, { properties: [], residents: [], vendors: [], orders: [] }); showLogin(); msg("loginMessage", "You have signed out.", true); } });
  $("propertyForm").addEventListener("submit", async (event) => { event.preventDefault(); const form = event.currentTarget; if (form.dataset.busy) return; form.dataset.busy = "1"; form.querySelector("button[type=submit], button").disabled = true; try { const d = payload(form); d.total_units = Number(d.total_units); d.property_type = "residential"; await request("/products/fieldnest/properties", { method: "POST", body: JSON.stringify(d) }); form.reset(); form.total_units.value = "1"; form.closest("dialog")?.close(); await loadAll(); } catch (e) { reportError(form, e); } finally { releaseForm(form); } });
  $("vendorForm").addEventListener("submit", async (event) => { event.preventDefault(); const form = event.currentTarget; if (form.dataset.busy) return; form.dataset.busy = "1"; form.querySelector("button[type=submit], button").disabled = true; try { const d = payload(form); d.email ||= null; d.insurance_expires ||= null; d.phone = null; await request("/products/fieldnest/vendors", { method: "POST", body: JSON.stringify(d) }); form.reset(); form.closest("dialog")?.close(); await loadAll(); } catch (e) { reportError(form, e); } finally { releaseForm(form); } });
  $("residentForm").addEventListener("submit", async (event) => { event.preventDefault(); const form = event.currentTarget; if (form.dataset.busy) return; form.dataset.busy = "1"; form.querySelector("button[type=submit], button").disabled = true; try { if (!state.properties.length) throw new Error("Add a property before adding residents."); const d = payload(form); d.property_id = Number(d.property_id); d.email ||= null; await request("/products/fieldnest/residents", { method: "POST", body: JSON.stringify(d) }); form.reset(); form.closest("dialog")?.close(); await loadAll(); } catch (e) { reportError(form, e); } finally { releaseForm(form); } });
  $("workOrderForm").addEventListener("submit", async (event) => { event.preventDefault(); const form = event.currentTarget; if (form.dataset.busy) return; form.dataset.busy = "1"; form.querySelector("button[type=submit], button").disabled = true; try { if (!state.properties.length) throw new Error("Add a property before creating a work order."); const d = payload(form); d.property_id = Number(d.property_id); d.resident_id = null; d.vendor_id = null; d.unit ||= ""; d.description ||= null; d.target_date = null; await request("/products/fieldnest/work-orders", { method: "POST", body: JSON.stringify(d) }); form.reset(); form.closest("dialog")?.close(); await loadAll(); } catch (e) { reportError(form, e); } finally { releaseForm(form); } });


  function releaseForm(form) { delete form.dataset.busy; form.querySelector("button[type=submit], button").disabled = false; }
  function reportError(form, error) { const el = form.closest("dialog")?.querySelector(".dialog-message"); if (el) el.textContent = error.message; else msg("appMessage", error.message); }
  function route() {
    const allowed = ["overview", "work-orders", "properties", "residents", "vendors"];
    const key = allowed.includes(location.hash.slice(1)) ? location.hash.slice(1) : "overview";
    document.querySelectorAll("[data-view]").forEach(el => el.hidden = el.dataset.view !== key);
    document.querySelectorAll("[data-nav]").forEach(el => { el.classList.toggle("active", el.dataset.nav === key); if (el.dataset.nav === key) el.setAttribute("aria-current", "page"); else el.removeAttribute("aria-current"); });
    $("currentView").textContent = key === "work-orders" ? "Work orders" : key[0].toUpperCase() + key.slice(1);
  }
  function applySearch() { document.querySelectorAll("[data-search]").forEach(input => { const term = input.value.trim().toLowerCase(); const rows = Array.from($(input.dataset.search).querySelectorAll(".record")); rows.forEach(row => row.hidden = !row.textContent.toLowerCase().includes(term)); let note = $(input.dataset.search).querySelector(".search-empty"); if (!note) { note = document.createElement("div"); note.className = "empty-state search-empty"; note.textContent = "No matching records. Try a different search."; $(input.dataset.search).append(note); } note.hidden = !rows.length || rows.some(row => !row.hidden); }); }
  function renderOverview() {
    const active = state.orders.filter(x => !["completed", "cancelled"].includes(x.status));
    $("recentOrders").innerHTML = active.length ? active.slice().sort((a,b) => b.id-a.id).slice(0,5).map(w => { const p = state.properties.find(p => p.id === w.property_id); return `<button type="button" class="record work-order-row" data-order-id="${esc(w.id)}"><span><strong>${esc(w.title)}</strong><small>${esc(p?.name || "Property")} · ${esc(w.priority)} priority</small></span><span class="badge">${esc(w.status.replaceAll("_", " "))}</span></button>`; }).join("") : `<div class="empty-state"><strong>Room for a fresh start.</strong><span>Your open maintenance requests will appear here.<br>Create a work order when the next maintenance request comes in.</span></div>`;
    const hasProperty = state.properties.length > 0;
    $("nextStep").textContent = hasProperty ? "Your portfolio is taking shape. Capture a maintenance request and keep the next repair moving." : "Start with a property, then bring your people and maintenance together.";
    $("nextStepButton").dataset.open = hasProperty ? "workOrderFormDialog" : "propertyFormDialog";
    $("nextStepButton").textContent = hasProperty ? "Add a work order →" : "Add a property →";
  }
  window.addEventListener("hashchange", route);
  document.addEventListener("click", event => { const opener = event.target.closest("[data-open]"); if (opener) { const dialog = $(opener.dataset.open); dialog.querySelector(".dialog-message").textContent = ""; dialog.showModal(); } const closer = event.target.closest("[data-close]"); if (closer) closer.closest("dialog").close(); });
  document.querySelectorAll("[data-search]").forEach(el => el.addEventListener("input", applySearch));
  route();


  let editingOrder = null;
  function openWorkOrder(id) {
    const order = state.orders.find(w => String(w.id) === String(id));
    if (!order) { msg("appMessage", "This work order is no longer available. Refresh the workspace."); return; }
    editingOrder = { id: order.id, tenantId: String(state.tenantId) };
    const form = $("workOrderDetailForm"); form.reset();
    const property = state.properties.find(p => p.id === order.property_id);
    $("detailContext").textContent = `${property?.name || "Property"} · Work order #${order.id}`;
    for (const key of ["title", "unit", "description", "priority", "status", "target_date"]) form.elements.namedItem(key).value = order[key] ?? "";
    form.elements.namedItem("vendor_id").innerHTML = '<option value="">Unassigned</option>' + state.vendors.map(v => `<option value="${esc(v.id)}">${esc(v.name)} · ${esc(v.trade)}</option>`).join("");
    form.elements.namedItem("vendor_id").value = order.vendor_id == null ? "" : String(order.vendor_id);
    form.elements.namedItem("resident_id").innerHTML = '<option value="">No resident linked</option>' + state.residents.filter(r => r.property_id === order.property_id).map(r => `<option value="${esc(r.id)}">${esc(r.name)} · Unit ${esc(r.unit)}</option>`).join("");
    form.elements.namedItem("resident_id").value = order.resident_id == null ? "" : String(order.resident_id);
    $("completeOrderButton").hidden = order.status === "completed";
    $("workOrderDetailDialog").querySelector(".dialog-message").textContent = "";
    $("workOrderDetailDialog").showModal();
  }
  document.addEventListener("click", event => { const row = event.target.closest("[data-order-id]"); if (row) openWorkOrder(row.dataset.orderId); });
  $("completeOrderButton").addEventListener("click", () => { const form = $("workOrderDetailForm"); form.elements.namedItem("status").value = "completed"; form.requestSubmit(); });
  $("workOrderDetailForm").addEventListener("submit", async event => {
    event.preventDefault(); const form = event.currentTarget;
    if (form.dataset.busy) return;
    if (!editingOrder || editingOrder.tenantId !== String(state.tenantId)) { reportError(form, new Error("The workspace changed. Close and reopen this work order.")); return; }
    const selection = { ...editingOrder }; const data = payload(form);
    data.vendor_id = data.vendor_id ? Number(data.vendor_id) : null;
    data.resident_id = data.resident_id ? Number(data.resident_id) : null;
    data.description ||= null; data.target_date ||= null;
    const buttons = Array.from(form.querySelectorAll("button")); buttons.forEach(b => b.disabled = true); form.dataset.busy = "1";
    form.closest("dialog").querySelector(".dialog-message").textContent = "Saving changes…";
    try {
      const updated = await request(`/products/fieldnest/work-orders/${selection.id}`, { method: "PATCH", body: JSON.stringify(data) });
      if (selection.tenantId !== String(state.tenantId)) return;
      state.orders = state.orders.map(w => w.id === updated.id ? updated : w);
      render(); renderOverview(); applySearch();
      form.closest("dialog").close(); editingOrder = null;
      msg("appMessage", updated.status === "completed" ? "Work order completed." : "Work order updated.", true);
    } catch (error) { reportError(form, error); }
    finally { delete form.dataset.busy; buttons.forEach(b => b.disabled = false); }
  });


  let linkProperty = null;
  const linkDialog = $("residentLinkDialog");
  document.addEventListener("click", event => {
    const opener = event.target.closest("[data-resident-link]");
    if (!opener) return;
    const prop = state.properties.find(p => String(p.id) === opener.dataset.residentLink);
    if (!prop) return;
    linkProperty = {id: prop.id, tenantId: String(state.tenantId)};
    $("residentLinkProperty").textContent = prop.name;
    $("residentLinkValue").value = ""; $("residentLinkExpiry").textContent = "";
    $("copyResidentLink").disabled = true;
    linkDialog.querySelector(".dialog-message").textContent = "";
    linkDialog.showModal();
  });
  async function changeResidentLink(method) {
    if (!linkProperty || linkProperty.tenantId !== String(state.tenantId)) return;
    const selected = {...linkProperty};
    const buttons = Array.from(linkDialog.querySelectorAll("button"));
    buttons.forEach(b => b.disabled = true);
    linkDialog.querySelector(".dialog-message").textContent = "Updating link…";
    try {
      const result = await request(`/products/fieldnest/properties/${selected.id}/request-link`, {method});
      if (!linkProperty || selected.tenantId !== String(state.tenantId) || selected.id !== linkProperty.id) return;
      $("residentLinkValue").value = result ? location.origin + result.path : "";
      $("residentLinkExpiry").textContent = result ? "Expires: " + new Date(result.expires_at).toLocaleDateString() : "";
      linkDialog.querySelector(".dialog-message").textContent = result ? "Link created. Share it with residents of this property." : "Link disabled. Existing copies can no longer submit requests.";
    } catch (error) { reportError($("residentLinkValue"), error); }
    finally { buttons.forEach(b => b.disabled = false); $("copyResidentLink").disabled = !$("residentLinkValue").value; }
  }
  $("generateResidentLink").addEventListener("click", () => changeResidentLink("POST"));
  $("revokeResidentLink").addEventListener("click", () => changeResidentLink("DELETE"));
  $("copyResidentLink").addEventListener("click", async () => {
    try { await navigator.clipboard.writeText($("residentLinkValue").value); linkDialog.querySelector(".dialog-message").textContent = "Link copied."; }
    catch (_) { $("residentLinkValue").select(); linkDialog.querySelector(".dialog-message").textContent = "Select and copy the link above."; }
  });

  (async () => { try { await discover(); showApp(); } catch (error) { showLogin(); if (!/401|Authentication/i.test(error.message)) msg("loginMessage", error.message); } })();
})();
