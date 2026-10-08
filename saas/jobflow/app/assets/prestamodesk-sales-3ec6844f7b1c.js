"use strict";
const demoViews = [
  `<span class="pill">Cartera de ejemplo</span><h3>Una vista clara de sus préstamos</h3><p>Consulte el saldo y abra el préstamo que necesita cobrar.</p><table><thead><tr><th>Cliente ficticio</th><th>Saldo</th><th>Estado</th></tr></thead><tbody><tr><td>Ana · ejemplo</td><td>RD$30,400.00</td><td>Activo</td></tr><tr><td>Luis · ejemplo</td><td>RD$39,600.00</td><td>Activo</td></tr></tbody></table>`,
  `<span class="pill">Préstamo de ejemplo</span><h3>Las cuotas, sin perder el detalle</h3><p>RD$30,000.00 financiados + RD$2,400.00 de interés fijo total = RD$32,400.00.</p><table><thead><tr><th>Cuota</th><th>Total</th><th>Pagado</th><th>Saldo</th></tr></thead><tbody><tr><td>1 · parcial</td><td>RD$5,400.00</td><td>RD$2,000.00</td><td>RD$3,400.00</td></tr><tr><td>2 · pendiente</td><td>RD$5,400.00</td><td>RD$0.00</td><td>RD$5,400.00</td></tr></tbody></table><p class="small">Seis cuotas de RD$5,400.00. El interés mostrado es fijo total, no una tasa APR.</p>`,
  `<span class="pill">Pago parcial de ejemplo</span><h3>Cada abono queda registrado</h3><p>Un pago ficticio de RD$2,000.00 reduce la primera cuota a RD$3,400.00 y el préstamo a RD$30,400.00.</p><div class="amount">RD$2,000.00</div><p>En el producto, Caja registra el método, la fecha y el operador. Esta demostración no registra pagos.</p>`,
  `<span class="pill">Recibo de ejemplo · DEMO-001</span><h3>Un comprobante con el saldo restante</h3><div class="amount">RD$2,000.00</div><p>Saldo de cuota: <strong>RD$3,400.00</strong><br>Saldo del préstamo: <strong>RD$30,400.00</strong><br>Operador: usuario ficticio</p><p class="small">Ejemplo ilustrativo. Los recibos del producto se pueden imprimir.</p>`
];
const demoScreen = document.getElementById("demoScreen");
document.querySelectorAll("[data-demo-step]").forEach(button => {
  button.addEventListener("click", () => {
    document.querySelectorAll("[data-demo-step]").forEach(item => item.setAttribute("aria-pressed", String(item === button)));
    demoScreen.innerHTML = demoViews[Number(button.dataset.demoStep)];
  });
});
const form = document.getElementById("demoRequestForm");
const status = document.getElementById("requestStatus");
const requestType = document.getElementById("requestType");
const pilotFeedback = document.getElementById("pilotFeedback");
const pilotFeedbackLabel = document.getElementById("pilotFeedbackLabel");
function updateRequestType() {
  const pilot = requestType.value === "pilot";
  pilotFeedbackLabel.hidden = !pilot;
  pilotFeedback.required = pilot;
  if (!pilot) pilotFeedback.checked = false;
}
requestType.addEventListener("change", updateRequestType);
updateRequestType();
let submitting = false;
form.addEventListener("submit", async event => {
  event.preventDefault();
  if (submitting || !form.reportValidity()) return;
  submitting = true;
  const button = form.querySelector('button[type="submit"]');
  button.disabled = true;
  status.className = "small";
  status.textContent = "Enviando solicitud…";
  const values = Object.fromEntries(new FormData(form));
  const payload = {
    business_name: values.business_name.trim(),
    contact_name: values.contact_name.trim(),
    email: values.email.trim(),
    phone: values.phone.trim() || null,
    service_type: "PréstamoDesk — " + (values.request_type === "pilot" ? "piloto gratuito de 30 días para " : "demostración para ") + values.business_type,
    message: "Préstamos activos: " + values.portfolio_size + "\nNecesidad: " + (values.message.trim() || "No indicada") + "\nTipo de solicitud: " + (values.request_type === "pilot" ? "Piloto gratuito de 30 días" : "Demostración") + (values.request_type === "pilot" ? "\nAceptó comentarios semanales y revisión final. Inicio y alcance sujetos a acuerdo." : "") + "\nAutorizó contacto sobre su solicitud. Aviso: 2026-10-08."
  };
  let received = false;
  try {
    const response = await fetch("/api/v1/public/products/prestamodesk/leads", {
      method:"POST", credentials:"same-origin", headers:{"Content-Type":"application/json"}, body:JSON.stringify(payload)
    });
    if (!response.ok) {
      status.className = "small error";
      status.textContent = response.status === 429
        ? "Hay demasiadas solicitudes. Espere unos minutos antes de intentarlo nuevamente."
        : "No se recibió una confirmación. Revise su conexión antes de intentarlo nuevamente.";
      return;
    }
    // A successful response means the request was accepted, even if its body cannot be read.
    received = true;
    const data = await response.json().catch(() => null);
    form.reset();
    updateRequestType();
    status.className = "small success";
    status.textContent = "Solicitud recibida" + (data && Number.isInteger(data.lead_id) ? " · #" + data.lead_id : "") + ". FieldLookers revisará su solicitud para coordinar los próximos pasos. El envío no confirma el inicio de un piloto.";
  } catch {
    status.className = "small error";
    status.textContent = "No pudimos confirmar el envío. La solicitud podría haberse recibido; no la repita de inmediato.";
  } finally {
    submitting = false;
    button.disabled = received;
    if (received) button.textContent = "Solicitud recibida";
  }
});
