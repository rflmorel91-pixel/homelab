"use strict";

const prospectApplicationPanel = document.getElementById("prospectApplicationPanel");
const prospectApplicationForm = document.getElementById("prospectApplicationForm");
const prospectApplicationQuote = document.getElementById("prospectApplicationQuote");
const prospectApplicationError = document.getElementById("prospectApplicationError");
const prospectApplicationSave = document.getElementById("prospectApplicationSave");
const prospectApplicationVehicle = document.getElementById("prospectApplicationVehicle");
let routedProspectId = null;
let routedTenantId = null;
let routedQuote = null;
let routingBusy = false;
let routingGeneration = 0;
const routeField = name => prospectApplicationForm.elements.namedItem(name);
const routeValue = name => routeField(name).value.trim();

function clearRouteQuote() {
  routedQuote = null;
  prospectApplicationQuote.hidden = true;
  prospectApplicationSave.disabled = true;
}

function updateProspectRoute() {
  const vehicle = routeValue("loan_type") === "vehicle";
  prospectApplicationVehicle.hidden = !vehicle;
  prospectApplicationVehicle.querySelectorAll("input").forEach(input => {
    input.disabled = !vehicle || routingBusy;
    input.required = vehicle && ["vehicle_make", "vehicle_model", "vehicle_year", "vehicle_cash_price", "vehicle_down_payment"].includes(input.name);
  });
  routeField("principal_amount").readOnly = vehicle;
  if (vehicle) {
    try {
      const financed = routeCents("vehicle_cash_price") - routeCents("vehicle_down_payment");
      routeField("principal_amount").value = financed > 0 ? (financed / 100).toFixed(2) : "";
    } catch {
      routeField("principal_amount").value = "";
    }
  }
}

function setRoutingBusy(active) {
  routingBusy = active;
  prospectApplicationForm.setAttribute("aria-busy", String(active));
  prospectApplicationForm.querySelectorAll("input, select, textarea, button").forEach(control => { control.disabled = active; });
  updateProspectRoute();
  prospectApplicationSave.disabled = active || !routedQuote;
}

function closeProspectApplication() {
  routingGeneration += 1;
  routedProspectId = null;
  routedTenantId = null;
  clearRouteQuote();
  prospectApplicationForm.reset();
  prospectApplicationError.hidden = true;
  prospectApplicationPanel.hidden = true;
}

function openProspectApplication(prospectId) {
  if (routingBusy) return;
  const prospect = prospects.find(item => item.id === prospectId);
  if (!prospect || prospect.status !== "qualified") {
    showError("Califique el prospecto antes de preparar una solicitud.");
    return;
  }
  if (applications.some(item => item.source_prospect_id === prospectId)) {
    showError("Este prospecto ya tiene una solicitud. Revísela en Solicitudes de préstamo.");
    return;
  }
  closeProspectApplication();
  routedProspectId = prospectId;
  routedTenantId = String(tenantId);
  document.getElementById("prospectApplicationTitle").textContent = `Preparar solicitud · ${prospect.full_name}`;
  document.getElementById("prospectApplicationContact").textContent = [prospect.phone, prospect.email].filter(Boolean).join(" · ");
  routeField("principal_amount").value = prospect.requested_amount;
  routeField("vehicle_down_payment").value = "0";
  routeField("notes").value = prospect.message || "";
  updateProspectRoute();
  prospectApplicationPanel.hidden = false;
  routeField("loan_type").focus();
}

function routeCents(name) {
  const raw = routeValue(name);
  if (!/^\d+(?:\.\d{1,2})?$/.test(raw)) throw new Error("Ingrese montos con hasta dos decimales.");
  const [whole, fraction = ""] = raw.split(".");
  const cents = Number(whole) * 100 + Number(fraction.padEnd(2, "0"));
  if (!Number.isSafeInteger(cents)) throw new Error("Monto fuera de rango.");
  return cents;
}

function prospectRouteTerms() {
  if (!routedProspectId || String(tenantId) !== routedTenantId) throw new Error("El cliente cambió. Abra nuevamente el prospecto.");
  const payload = {
    loan_type: routeValue("loan_type"),
    principal_amount: (routeCents("principal_amount") / 100).toFixed(2),
    flat_interest_rate_percent: routeValue("flat_interest_rate_percent"),
    installment_count: Number(routeValue("installment_count")),
    payment_frequency: routeValue("payment_frequency"),
    start_date: routeValue("start_date"),
    first_payment_date: routeValue("first_payment_date"),
    notes: routeValue("notes") || null
  };
  if (payload.first_payment_date < payload.start_date) throw new Error("La primera cuota no puede ser anterior al préstamo.");
  if (payload.loan_type === "vehicle") {
    const price = routeCents("vehicle_cash_price");
    const down = routeCents("vehicle_down_payment");
    if (down >= price) throw new Error("La inicial debe ser menor que el precio del vehículo.");
    payload.vehicle_cash_price = (price / 100).toFixed(2);
    payload.vehicle_down_payment = (down / 100).toFixed(2);
    payload.principal_amount = ((price - down) / 100).toFixed(2);
    payload.vehicle_make = routeValue("vehicle_make");
    payload.vehicle_model = routeValue("vehicle_model");
    payload.vehicle_year = Number(routeValue("vehicle_year"));
    for (const name of ["vehicle_color", "vehicle_vin", "vehicle_license_plate", "vehicle_seller"]) payload[name] = routeValue(name) || null;
  }
  return payload;
}

function routeError(message) {
  prospectApplicationError.textContent = message;
  prospectApplicationError.hidden = false;
}

prospectApplicationForm.addEventListener("input", () => { clearRouteQuote(); updateProspectRoute(); });
prospectApplicationForm.addEventListener("change", () => { clearRouteQuote(); updateProspectRoute(); });
document.getElementById("prospectApplicationCancel").addEventListener("click", closeProspectApplication);
logoutButton.addEventListener("click", closeProspectApplication);
prospectList.addEventListener("click", event => {
  const button = event.target.closest("button[data-start-prospect-application]");
  if (button) openProspectApplication(Number(button.dataset.startProspectApplication));
});

document.getElementById("prospectApplicationCalculate").addEventListener("click", async () => {
  if (routingBusy || !prospectApplicationForm.reportValidity()) return;
  prospectApplicationError.hidden = true;
  clearRouteQuote();
  let payload;
  try { payload = prospectRouteTerms(); } catch (error) { routeError(error.message); return; }
  const generation = routingGeneration;
  setRoutingBusy(true);
  try {
    const quote = await apiRequest(`${PRODUCT_BASE}/applications/quote`, { method: "POST", body: JSON.stringify(payload) });
    if (generation !== routingGeneration || String(tenantId) !== routedTenantId) return;
    if (quote.currency !== "DOP" || !Array.isArray(quote.installments) || quote.installments.length !== payload.installment_count) throw new Error("Cotización incompleta. Vuelva a calcular.");
    prospectApplicationQuote.replaceChildren();
    for (const [label, amount] of [["Monto financiado", quote.principal_amount], ["Interés total", quote.total_interest], ["Total a pagar", quote.total_due]]) {
      const paragraph = document.createElement("p");
      paragraph.textContent = `${label}: ${formatMoney(amount)}`;
      prospectApplicationQuote.append(paragraph);
    }
    const details = document.createElement("details");
    const summary = document.createElement("summary");
    summary.textContent = `Calendario de ${quote.installments.length} cuotas`;
    details.append(summary);
    const list = document.createElement("ol");
    for (const item of quote.installments) {
      const row = document.createElement("li");
      row.textContent = `Cuota ${item.sequence_number} · ${item.due_date} · ${formatMoney(item.total_due)}`;
      list.append(row);
    }
    details.append(list);
    prospectApplicationQuote.append(details);
    routedQuote = JSON.stringify(payload);
    prospectApplicationQuote.hidden = false;
  } catch (error) { if (generation === routingGeneration) routeError(error.message); }
  finally { setRoutingBusy(false); }
});

prospectApplicationForm.addEventListener("submit", async event => {
  event.preventDefault();
  if (routingBusy || !prospectApplicationForm.reportValidity()) return;
  let payload;
  try { payload = prospectRouteTerms(); } catch (error) { routeError(error.message); return; }
  if (!routedQuote || routedQuote !== JSON.stringify(payload)) { routeError("Calcule y revise las cuotas antes de guardar."); return; }
  prospectApplicationError.hidden = true;
  const generation = routingGeneration;
  setRoutingBusy(true);
  let saved = false;
  try {
    const application = await apiRequest(`${PRODUCT_BASE}/prospects/${routedProspectId}/application`, { method: "POST", body: JSON.stringify(payload) });
    if (generation !== routingGeneration || String(tenantId) !== routedTenantId) return;
    saved = true;
    closeProspectApplication();
    showSuccess(`Solicitud #${application.id} guardada. Continúe con revisión, aprobación y conversión.`);
    await loadDashboard();
  } catch (error) {
    if (saved) showError("La solicitud se guardó, pero no se pudo actualizar la pantalla. Recargue antes de continuar.");
    else if (generation === routingGeneration) routeError(error.message);
  } finally { setRoutingBusy(false); }
});
