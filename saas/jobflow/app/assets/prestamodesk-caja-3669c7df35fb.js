const API_BASE = "/api/v1";
const PRODUCT_BASE = "/products/prestamodesk";
const TENANT_STORAGE_KEY =
  "prestamodesk_cashier_tenant_id";

let tenantId = localStorage.getItem(
  TENANT_STORAGE_KEY
);
let selectedLoanId = null;
let selectedLoan = null;
let currentRole = null;
let paymentSubmitting = false;
let paymentNeedsReview = false;

const authPanel = document.getElementById("authPanel");
const cashierWorkspace =
  document.getElementById("cashierWorkspace");
const loginForm = document.getElementById("loginForm");
const loginEmail = document.getElementById("loginEmail");
const forgotPasswordButton =
  document.getElementById("forgotPasswordButton");
const passwordResetRequestForm =
  document.getElementById("passwordResetRequestForm");
const passwordResetEmail =
  document.getElementById("passwordResetEmail");
const passwordResetRequestButton =
  document.getElementById("passwordResetRequestButton");
const backToSignInButton =
  document.getElementById("backToSignInButton");
const logoutButton =
  document.getElementById("logoutButton");
const clientContext =
  document.getElementById("clientContext");
const healthStatus =
  document.getElementById("healthStatus");
const errorMessage =
  document.getElementById("errorMessage");
const successMessage =
  document.getElementById("successMessage");
const loanSearchForm =
  document.getElementById("loanSearchForm");
const loanSearchQuery =
  document.getElementById("loanSearchQuery");
const cashierLoanList =
  document.getElementById("cashierLoanList");
const loanResultCount =
  document.getElementById("loanResultCount");
const loanDetailPanel =
  document.getElementById("loanDetailPanel");
const loanDetailTitle =
  document.getElementById("loanDetailTitle");
const loanDetailSummary =
  document.getElementById("loanDetailSummary");
const installmentList =
  document.getElementById("installmentList");
const paymentPanel =
  document.getElementById("paymentPanel");
const paymentForm =
  document.getElementById("paymentForm");
const paymentInstallment =
  document.getElementById("paymentInstallment");
const paymentAmount =
  document.getElementById("paymentAmount");
const paymentDate =
  document.getElementById("paymentDate");
const receiptPanel =
  document.getElementById("receiptPanel");
const receiptContent =
  document.getElementById("receiptContent");
const cashClosingPanel =
  document.getElementById("cashClosingPanel");
const cashClosingPreview =
  document.getElementById("cashClosingPreview");
const cashClosingForm =
  document.getElementById("cashClosingForm");
const cashCounted =
  document.getElementById("cashCounted");
const cashClosingNotes =
  document.getElementById("cashClosingNotes");
const cashClosingReceipt =
  document.getElementById("cashClosingReceipt");
const cashClosingReceiptContent =
  document.getElementById(
    "cashClosingReceiptContent"
  );
const cashClosingHistoryPanel =
  document.getElementById(
    "cashClosingHistoryPanel"
  );
const cashClosingHistory =
  document.getElementById("cashClosingHistory");


function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}


function formatMoney(value) {
  return new Intl.NumberFormat(
    "es-DO",
    {
      style: "currency",
      currency: "DOP"
    }
  ).format(Number(value || 0));
}


function formatStatus(value) {
  const labels = {
    active: "Activo",
    paid: "Pagado",
    cancelled: "Cancelado",
    pending: "Pendiente",
    partial: "Parcial",
    overdue: "Vencida"
  };

  return labels[value] || value;
}


function formatDateTime(value) {
  return new Intl.DateTimeFormat(
    "es-DO",
    {
      dateStyle: "medium",
      timeStyle: "short"
    }
  ).format(new Date(value));
}


function formatPaymentMethod(value) {
  const labels = {
    cash: "Efectivo",
    bank_transfer: "Transferencia bancaria",
    card: "Tarjeta",
    other: "Otro"
  };

  return labels[value] || value;
}


function installmentBalance(installment) {
  if (installment.total_balance !== undefined) {
    return Number(installment.total_balance);
  }

  return (
    Number(installment.total_due)
    - Number(installment.paid_amount)
  );
}


function setAuthenticatedUI(authenticated) {
  authPanel.hidden = authenticated;
  cashierWorkspace.hidden = !authenticated;
  logoutButton.hidden = !authenticated;
  clientContext.hidden = !authenticated;
}


function showError(message) {
  errorMessage.textContent = "";
  errorMessage.hidden = false;
  errorMessage.textContent = message;
  successMessage.hidden = true;
  if (errorMessage.isConnected && !errorMessage.closest("[hidden]")) {
    errorMessage.scrollIntoView?.({behavior: "instant", block: "center", inline: "nearest"});
  }
}


function showSuccess(message) {
  successMessage.textContent = message;
  successMessage.hidden = false;
  errorMessage.hidden = true;

  window.setTimeout(() => {
    successMessage.hidden = true;
  }, 3500);
}


function clearMessages() {
  errorMessage.hidden = true;
  successMessage.hidden = true;
}


async function apiRequest(path, options = {}) {
  const response = await fetch(
    `${API_BASE}${path}`,
    {
      headers: {
        "Content-Type": "application/json",
        ...(tenantId
          ? {"X-Tenant-ID": tenantId}
          : {}),
        ...(options.headers || {})
      },
      ...options
    }
  );

  if (!response.ok) {
    let detail =
      `Solicitud fallida (${response.status})`;

    try {
      const body = await response.json();

      if (typeof body.detail === "string") {
        detail = body.detail;
      }
    } catch {
      // Preserve the safe default.
    }

    function spanishApiError(detail, status) {
      const translations = {
  "Configure and enable the tenant late-fee policy first": "Configure y active la política de mora antes de crear o modificar un préstamo con mora.",
  "Late-fee policy not configured": "Configure la política de mora en la sección Préstamos.",
  "First payment date cannot be before the loan start date": "La primera cuota debe vencer en la fecha del préstamo o después. Revise ambas fechas.",
  "Borrower not found": "No se encontró el prestatario en este negocio. Actualice la lista y selecciónelo nuevamente.",
  "Borrower is inactive": "El prestatario está inactivo. Revise su estado antes de crear el préstamo.",
  "Loan not found": "No se encontró el préstamo en este negocio. Actualice la lista y selecciónelo nuevamente.",
  "Loan is not active": "El préstamo no está activo. Revise su estado antes de registrar un pago.",
  "Installment not found": "No se encontró la cuota. Actualice el préstamo y selecciónela nuevamente.",
  "Payment not found": "No se encontró el pago. Actualice el historial del préstamo.",
  "Payment date cannot be in the future": "La fecha del pago no puede ser futura. Revise la fecha indicada.",
  "Payment date precedes an existing late-fee assessment": "La fecha del pago es anterior a la mora ya calculada. Revise la fecha y el historial antes de continuar.",
  "Payment amount must be greater than zero": "El monto del pago debe ser mayor que cero.",
  "Payment exceeds installment balance": "El pago supera el saldo de la cuota. Actualice el saldo y revise el monto.",
  "Collectors cannot record payments": "El rol Cobrador no permite registrar pagos. Solicite acceso de caja al propietario o administrador.",
  "Payment operation access required": "Su rol no permite esta operación de pago. Consulte al propietario o administrador.",
  "Payment request belongs to another operator": "Esta solicitud de pago pertenece a otro operador. Revise el historial con el propietario o administrador antes de continuar.",
  "Payment request key was used with different details": "Esta solicitud ya se usó con otros datos de pago. Revise el historial antes de volver a cobrar.",
  "Original payment was voided; use a new request key": "El pago original fue anulado. Revise su recibo y la anulación antes de iniciar otro pago.",
  "Original receipt unavailable; review payment history": "El recibo original no está disponible. Revise el historial antes de volver a cobrar.",
  "Projection date cannot be in the future": "La fecha de consulta no puede ser futura.",
  "Payment is already voided; the original reason cannot be changed": "El pago ya fue anulado. No se puede cambiar el motivo original.",
  "Payment belongs to a cash closing; a reconciled adjustment is required": "El pago pertenece a un cierre de caja. Solicite un ajuste conciliado al propietario o administrador.",
  "Payment predates correction snapshots; a reconciled adjustment is required": "Este pago requiere un ajuste conciliado. Consulte al propietario o administrador.",
  "Only the latest recorded payment on the loan may be voided": "Solo puede anular el último pago registrado del préstamo. Revise el historial.",
  "Payment ledger is incomplete; reconciliation is required": "El registro del pago está incompleto. Solicite una conciliación antes de continuar.",
  "Loan status does not allow payment correction": "El estado del préstamo no permite anular este pago.",
  "Installment changed after payment; reconciliation is required": "La cuota cambió después del pago. Solicite una conciliación antes de continuar.",
  "Promise allocation requires reconciliation": "La aplicación del pago a las promesas requiere conciliación. Consulte al propietario o administrador.",
  "Release collector assignments before changing or suspending this membership": "Libere las carteras asignadas antes de cambiar el rol o suspender este integrante.",
  "Client must retain at least one owner": "El negocio debe conservar al menos un propietario.",
  "Client must retain at least one active owner": "El negocio debe conservar al menos un propietario activo.",
  "You cannot suspend your own membership": "No puede suspender su propio acceso.",
  "Only the owner may manage owners and administrators": "Solo el propietario puede administrar propietarios y administradores.",
  "Administration access required": "Su rol no permite administrar el equipo. Consulte al propietario o administrador.",
  "Reactivate access before requesting password recovery": "Reactive el acceso del integrante antes de solicitar la recuperación de contraseña.",
  "Membership not found": "No se encontró el integrante en este negocio. Actualice el equipo.",
  "Invitation not found": "No se encontró la invitación. Actualice la lista.",
  "Client invitation not found": "No se encontró la invitación en este negocio. Actualice la lista.",
  "An active invitation already exists for this client and email": "Ya existe una invitación pendiente para este correo. Revísela en Invitaciones; si perdió el enlace, revoque la invitación antes de crear otra.",
  "A user with this email already exists": "Ya existe una cuenta con este correo. Revise el equipo o use otro correo para la invitación.",
  "A platform user with this email already exists": "Ya existe una cuenta de plataforma con este correo. Revise el equipo antes de invitarla.",
  "Only pending client invitations can be revoked": "Solo puede revocar invitaciones pendientes. Actualice la lista para revisar su estado.",
  "Role is not available for this product": "El rol seleccionado no está disponible para este negocio. Seleccione un rol permitido.",
  "Client must be active": "El negocio debe estar activo para crear invitaciones.",
  "Client not found": "No se encontró el negocio. Actualice su acceso y selecciónelo nuevamente.",
  "Client product is unavailable": "PréstamoDesk no está disponible para este negocio. Consulte al administrador.",
  "Authentication required": "Su sesión no está disponible. Inicie sesión nuevamente.",
  "Invalid email or password": "El correo o la contraseña no son correctos. Revise sus datos.",
  "Tenant context required": "Seleccione un negocio antes de continuar.",
  "User is not a member of this tenant": "No tiene acceso a este negocio. Actualice su acceso o consulte al propietario.",
  "Tenant is suspended": "El negocio está suspendido. Consulte al administrador.",
  "Tenant owner access required": "Esta operación requiere el rol Propietario.",
  "Role does not permit this operation": "Su rol no permite esta operación. Consulte al propietario o administrador.",
  "Cashier membership required": "Su rol no permite cerrar caja. Consulte al propietario o administrador."
};
      if (status >= 500) return "No se pudo completar la solicitud por un problema del servidor. Si estaba registrando un pago, revise el historial antes de volver a cobrar.";
      if (typeof detail === "string" && Object.hasOwn(translations, detail)) return translations[detail];
      const fallback = {
        400: "No se pudo completar la solicitud. Revise los datos indicados.",
        401: "Su sesión no está disponible. Inicie sesión nuevamente.",
        403: "No tiene permiso para esta operación. Consulte al propietario o administrador.",
        404: "No se encontró el registro en este negocio. Actualice la sección.",
        409: "No se pudo completar la operación por un conflicto con el estado actual. Actualice la sección y revise el registro antes de continuar.",
        422: "Revise los campos obligatorios, los montos y las fechas antes de continuar.",
        429: "Se realizaron demasiadas solicitudes. Espere un momento antes de continuar."
      };
      return fallback[status] || "No se pudo completar la solicitud. Actualice la sección y revise los datos antes de continuar.";
    }
    const error = new Error(spanishApiError(detail, response.status));
    error.status = response.status;
    throw error;
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}


async function checkHealth() {
  try {
    const health = await apiRequest("/health");
    healthStatus.textContent = `API: ${health.status}`;
  } catch {
    healthStatus.textContent = "API no disponible";
  }
}


async function discoverAccess() {
  const access = await apiRequest(
    "/auth/products/prestamodesk/access"
  );

  if (access.clients.length === 0) {
    throw new Error(
      "Su cuenta no tiene acceso activo a PréstamoDesk."
    );
  }

  if (access.clients.length > 1) {
    throw new Error(
      "Su cuenta tiene varios clientes. "
      + "La selección de cliente aún no está disponible."
    );
  }

  const client = access.clients[0];

  if (client.role === "collector") {
    window.location.replace(
      "/prestamodesk/cobros"
    );
    return;
  }

  if (client.role === "supervisor") {
    window.location.replace("/prestamodesk/cobros/supervision");
    return;
  }
  tenantId = String(client.tenant_id);
  localStorage.setItem(
    TENANT_STORAGE_KEY,
    tenantId
  );

  const roleLabel = (
    ["owner", "administrator"].includes(client.role)
      ? "Administrador"
      : "Cajero"
  );

  currentRole = client.role;
  cashClosingPanel.hidden = !["member", "cashier"].includes(currentRole);
  cashClosingHistoryPanel.hidden =
    !["member", "cashier"].includes(currentRole);

  clientContext.textContent =
    `Cliente #${client.client_number} · `
    + `${client.name} · ${roleLabel}`;
}


function renderClosingPreview(preview) {
  cashClosingPreview.innerHTML = `
    <div class="summary-grid">
      <p>
        Pagos pendientes de cierre:
        <strong>${preview.payment_count}</strong>
      </p>
      <p>
        Total cobrado:
        <strong>${
          formatMoney(preview.total_collected)
        }</strong>
      </p>
      <p>
        Efectivo esperado:
        <strong>${
          formatMoney(preview.cash_expected)
        }</strong>
      </p>
      <p>
        Transferencias:
        ${formatMoney(preview.bank_transfer_total)}
      </p>
      <p>Tarjetas: ${formatMoney(preview.card_total)}</p>
      <p>Otros: ${formatMoney(preview.other_total)}</p>
      <p>
        Período iniciado:
        ${escapeHtml(formatDateTime(preview.opened_at))}
      </p>
    </div>
  `;

  cashCounted.value = Number(
    preview.cash_expected
  ).toFixed(2);
}


function renderClosingHistory(closings) {
  if (closings.length === 0) {
    cashClosingHistory.innerHTML = `
      <p class="notice">No hay cierres registrados.</p>
    `;
    return;
  }

  cashClosingHistory.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Cierre</th>
          <th>Fecha</th>
          <th>Pagos</th>
          <th>Total</th>
          <th>Efectivo esperado</th>
          <th>Efectivo contado</th>
          <th>Diferencia</th>
        </tr>
      </thead>
      <tbody>
        ${closings.map(closing => `
          <tr>
            <td>#${closing.id}</td>
            <td>${escapeHtml(
              formatDateTime(closing.closed_at)
            )}</td>
            <td>${closing.payment_count}</td>
            <td>${formatMoney(
              closing.total_collected
            )}</td>
            <td>${formatMoney(
              closing.cash_expected
            )}</td>
            <td>${formatMoney(
              closing.cash_counted
            )}</td>
            <td>${formatMoney(
              closing.cash_difference
            )}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}


async function loadCashClosing() {
  if (!["member", "cashier"].includes(currentRole)) {
    return;
  }

  const [preview, history] = await Promise.all([
    apiRequest(
      `${PRODUCT_BASE}/cashier/closing-preview`
    ),
    apiRequest(
      `${PRODUCT_BASE}/cashier/closings`
    )
  ]);

  renderClosingPreview(preview);
  renderClosingHistory(history);
}


function renderLoans(loans) {
  loanResultCount.textContent = String(loans.length);

  if (loans.length === 0) {
    cashierLoanList.innerHTML = `
      <p class="notice">
        No se encontraron préstamos.
      </p>
    `;
    return;
  }

  cashierLoanList.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Préstamo</th>
          <th>Cliente</th>
          <th>Documento</th>
          <th>Vehículo</th>
          <th>Saldo ordinario</th>
          <th>Mora</th>
          <th>Total exigible</th>
          <th>Estado</th>
          <th>Acción</th>
        </tr>
      </thead>
      <tbody>
        ${loans.map(loan => `
          <tr>
            <td>#${loan.id}</td>
            <td>${escapeHtml(loan.borrower_full_name)}</td>
            <td>
              ${escapeHtml(
                loan.borrower_document_number || "—"
              )}
            </td>
            <td>
              ${escapeHtml(
                [
                  loan.vehicle_make,
                  loan.vehicle_model,
                  loan.vehicle_year
                ].filter(Boolean).join(" ") || "—"
              )}
            </td>
            <td>
              ${formatMoney(loan.ordinary_balance_due)}
            </td>
            <td>
              ${formatMoney(loan.late_fee_balance_due)}
            </td>
            <td>${formatMoney(loan.balance_due)}</td>
            <td>${formatStatus(loan.status)}</td>
            <td>
              <button
                type="button"
                data-open-loan="${loan.id}"
              >
                Cobrar
              </button>
            </td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}


async function searchLoans(query = "") {
  clearMessages();

  const normalized = query.trim();
  const params = new URLSearchParams();

  if (normalized) {
    params.set("query", normalized);
  }

  if (paymentDate.value) {
    params.set("as_of", paymentDate.value);
  }

  const suffix = params.toString()
    ? `?${params.toString()}`
    : "";

  const loans = await apiRequest(
    `${PRODUCT_BASE}/cashier/loans${suffix}`
  );

  renderLoans(loans);
}


function renderInstallments(installments) {
  installmentList.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Cuota</th>
          <th>Vence</th>
          <th>Total de cuota</th>
          <th>Pagado</th>
          <th>Saldo ordinario</th>
          <th>Mora</th>
          <th>Total exigible</th>
          <th>Estado</th>
        </tr>
      </thead>
      <tbody>
        ${installments.map(item => `
          <tr>
            <td>${item.sequence_number}</td>
            <td>${escapeHtml(item.due_date)}</td>
            <td>${formatMoney(item.total_due)}</td>
            <td>${formatMoney(item.paid_amount)}</td>
            <td>${formatMoney(item.ordinary_balance)}</td>
            <td>${formatMoney(item.late_fee_balance)}</td>
            <td>${formatMoney(item.total_balance)}</td>
            <td>${formatStatus(item.status)}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}


function renderPaymentOptions(installments) {
  const payable = installments.filter(
    item => (
      item.status !== "paid"
      && installmentBalance(item) > 0
    )
  );

  if (payable.length === 0) {
    paymentInstallment.innerHTML =
      '<option value="">No hay cuotas pendientes</option>';
    paymentInstallment.disabled = true;
    paymentAmount.disabled = true;
    paymentForm.querySelector(
      'button[type="submit"]'
    ).disabled = true;
    return;
  }

  paymentInstallment.disabled = false;
  paymentAmount.disabled = false;
  paymentForm.querySelector(
    'button[type="submit"]'
  ).disabled = paymentSubmitting || paymentNeedsReview;

  paymentInstallment.innerHTML = payable
    .map(item => `
      <option
        value="${item.id}"
        data-balance="${installmentBalance(item)}"
      >
        Cuota ${item.sequence_number}
        · vence ${escapeHtml(item.due_date)}
        · ${formatMoney(installmentBalance(item))}
      </option>
    `)
    .join("");

  updatePaymentLimit();
}


function updatePaymentLimit() {
  const option =
    paymentInstallment.selectedOptions[0];

  if (!option || !option.dataset.balance) {
    paymentAmount.value = "";
    paymentAmount.removeAttribute("max");
    return;
  }

  const balance = Number(option.dataset.balance);
  paymentAmount.max = balance.toFixed(2);
  paymentAmount.value = balance.toFixed(2);
}


async function openLoan(loanId) {
  const params = new URLSearchParams();

  if (paymentDate.value) {
    params.set("as_of", paymentDate.value);
  }

  const suffix = params.toString()
    ? `?${params.toString()}`
    : "";

  const loan = await apiRequest(
    `${PRODUCT_BASE}/cashier/loans/${loanId}${suffix}`
  );

  selectedLoanId = loan.id;
  selectedLoan = loan;

  loanDetailTitle.textContent =
    `Préstamo #${loan.id} · `
    + loan.borrower_full_name;

  loanDetailSummary.innerHTML = `
    <p>
      <strong>Documento:</strong>
      ${escapeHtml(
        loan.borrower_document_number || "No registrado"
      )}
    </p>
    <p>
      <strong>Vehículo:</strong>
      ${escapeHtml(
        [
          loan.vehicle_make,
          loan.vehicle_model,
          loan.vehicle_year
        ].filter(Boolean).join(" ") || "No registrado"
      )}
    </p>
    <p>
      <strong>Total contractual:</strong>
      ${formatMoney(loan.total_due)}
      · <strong>Pagado:</strong>
      ${formatMoney(loan.paid_amount)}
    </p>
    <p>
      <strong>Saldo ordinario:</strong>
      ${formatMoney(loan.ordinary_balance_due)}
      · <strong>Mora:</strong>
      ${formatMoney(loan.late_fee_balance_due)}
      · <strong>Total exigible:</strong>
      ${formatMoney(loan.balance_due)}
    </p>
    <p>
      <strong>Calculado al:</strong>
      ${escapeHtml(loan.projected_through)}
      · <strong>Estado:</strong>
      ${formatStatus(loan.status)}
    </p>
  `;


  renderInstallments(loan.installments);
  renderPaymentOptions(loan.installments);

  loanDetailPanel.hidden = false;
  paymentPanel.hidden = (
    loan.status !== "active"
  );
  receiptPanel.hidden = true;
  await window.prestamodeskPaymentHistory?.load(loan.id, currentRole);
}


function setDefaultPaymentDate() {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(
    today.getMonth() + 1
  ).padStart(2, "0");
  const day = String(
    today.getDate()
  ).padStart(2, "0");

  paymentDate.value = `${year}-${month}-${day}`;
}


loanSearchForm.addEventListener(
  "submit",
  async event => {
    event.preventDefault();

    try {
      await searchLoans(loanSearchQuery.value);
    } catch (error) {
      showError(error.message);
    }
  }
);


document.getElementById(
  "showAllLoansButton"
).addEventListener(
  "click",
  async () => {
    loanSearchQuery.value = "";

    try {
      await searchLoans();
    } catch (error) {
      showError(error.message);
    }
  }
);


cashierLoanList.addEventListener(
  "click",
  async event => {
    const button = event.target.closest(
      "button[data-open-loan]"
    );

    if (!button) {
      return;
    }

    try {
      await openLoan(
        Number(button.dataset.openLoan)
      );
    } catch (error) {
      showError(error.message);
    }
  }
);


document.getElementById(
  "closeLoanDetail"
).addEventListener(
  "click",
  () => {
    selectedLoanId = null;
    selectedLoan = null;
    loanDetailPanel.hidden = true;
    paymentPanel.hidden = true;
    receiptPanel.hidden = true;
  }
);


paymentInstallment.addEventListener(
  "change",
  updatePaymentLimit
);


paymentDate.addEventListener(
  "change",
  async () => {
    clearMessages();

    try {
      await searchLoans(loanSearchQuery.value);

      if (selectedLoanId) {
        await openLoan(selectedLoanId);
      }
    } catch (error) {
      showError(error.message);
    }
  }
);


paymentForm.addEventListener(
  "submit",
  async event => {
    event.preventDefault();
    if (paymentSubmitting || paymentNeedsReview || !selectedLoanId || !selectedLoan) return;
    paymentSubmitting = true;
    clearMessages();
    const loanId = selectedLoanId;
    const borrowerName = selectedLoan.borrower_full_name;
    const paidDate = paymentDate.value;
    const submitButton = paymentForm.querySelector('button[type="submit"]');
    const originalLabel = submitButton.textContent;
    const controls = Array.from(cashierWorkspace.querySelectorAll("button, input, select, textarea"));
    const disabledBefore = controls.map(control => control.disabled);
    controls.forEach(control => { control.disabled = true; });
    submitButton.textContent = "Registrando…";
    let paymentSaved = false;
    let requestStorageKey = null;

    try {
      const paymentMethod =
        document.getElementById(
          "paymentMethod"
        ).value;
      const reference =
        document.getElementById(
          "paymentReference"
        ).value.trim() || null;

      const paymentPayload = {
        installment_id: Number(paymentInstallment.value),
        amount: Number(paymentAmount.value).toFixed(2),
        payment_method: paymentMethod,
        reference,
        paid_at: paidDate ? `${paidDate}T12:00:00Z` : null
      };
      requestStorageKey = "prestamodesk-payment-request:" + tenantId
        + ":" + JSON.stringify(paymentPayload);
      const requestKey = sessionStorage.getItem(requestStorageKey)
        || crypto.randomUUID();
      sessionStorage.setItem(requestStorageKey, requestKey);
      const receipt = await apiRequest(
        `${PRODUCT_BASE}/payments`,
        {
          method: "POST",
          body: JSON.stringify({...paymentPayload, idempotency_key: requestKey})
        }
      );

      paymentSaved = true;
      sessionStorage.removeItem(requestStorageKey);
      receiptContent.innerHTML = `
        <p>
          <strong>${escapeHtml(
            receipt.receipt_number
          )}</strong>
        </p>
        <p>
          Préstamo:
          <strong>#${loanId}</strong>
        </p>
        <p>
          Cliente:
          <strong>${escapeHtml(
            borrowerName
          )}</strong>
        </p>
        <p>
          Fecha:
          ${escapeHtml(paidDate)}
        </p>
        <p>
          Método:
          ${escapeHtml(
            formatPaymentMethod(paymentMethod)
          )}
        </p>
        <p>
          Referencia:
          ${escapeHtml(reference || "—")}
        </p>
        <p>
          Monto:
          <strong>${formatMoney(receipt.amount)}</strong>
        </p>
        <p>
          Aplicado a mora:
          ${formatMoney(receipt.late_fee_amount)}
        </p>
        <p>
          Aplicado a interés:
          ${formatMoney(receipt.interest_amount)}
        </p>
        <p>
          Aplicado a principal:
          ${formatMoney(receipt.principal_amount)}
        </p>
        <p>
          Saldo ordinario de cuota:
          ${formatMoney(
            receipt.installment_ordinary_balance
          )}
        </p>
        <p>
          Mora pendiente:
          ${formatMoney(
            receipt.installment_late_fee_balance
          )}
        </p>
        <p>
          Total pendiente de cuota:
          ${formatMoney(receipt.installment_balance)}
        </p>
        <p>
          Saldo total del préstamo:
          ${formatMoney(receipt.loan_balance)}
        </p>
        <p>
          Registrado por usuario #${
            receipt.recorded_by_user_id
          }
        </p>
      `;

      receiptPanel.hidden = false;
      paymentForm.reset();
      setDefaultPaymentDate();

      try {
        await openLoan(loanId);
        await searchLoans(loanSearchQuery.value);
        await loadCashClosing();
        showSuccess("Pago registrado.");
      } catch {
        paymentNeedsReview = true;
        showError("Pago registrado. No se pudo actualizar la pantalla. Conserve el recibo y recargue para consultar el saldo antes de registrar otro pago.");
      } finally {
        receiptPanel.hidden = false;
      }
    } catch (error) {
      if (paymentSaved || !error.status || error.status >= 500) {
        paymentNeedsReview = true;
        showError("No se pudo confirmar el resultado del pago. No lo repita: recargue y revise Pagos y correcciones antes de continuar.");
      } else {
        // Keep keys for conflicts: changing operator or a voided payment
        // must not turn a retry into a new payment.
        if (requestStorageKey && error.status !== 409) {
          sessionStorage.removeItem(requestStorageKey);
        }
        showError(error.message);
      }
    } finally {
      paymentSubmitting = false;
      controls.forEach((control, index) => { control.disabled = disabledBefore[index]; });
      submitButton.textContent = originalLabel;
      submitButton.disabled = paymentNeedsReview
        || !paymentInstallment.value
        || Number(paymentInstallment.selectedOptions[0]?.dataset.balance || 0) <= 0;
    }
  }
);


document.getElementById(
  "printReceiptButton"
).addEventListener(
  "click",
  () => window.print()
);


cashClosingForm.addEventListener(
  "submit",
  async event => {
    event.preventDefault();
    clearMessages();

    try {
      const closing = await apiRequest(
        `${PRODUCT_BASE}/cashier/closings`,
        {
          method: "POST",
          body: JSON.stringify({
            cash_counted: cashCounted.value,
            notes:
              cashClosingNotes.value.trim()
              || null
          })
        }
      );

      cashClosingReceiptContent.innerHTML = `
        <p>
          <strong>Cierre #${closing.id}</strong>
        </p>
        <p>
          Cerrado:
          ${escapeHtml(
            formatDateTime(closing.closed_at)
          )}
        </p>
        <p>Pagos: ${closing.payment_count}</p>
        <p>
          Total cobrado:
          <strong>${
            formatMoney(closing.total_collected)
          }</strong>
        </p>
        <p>
          Efectivo esperado:
          ${formatMoney(closing.cash_expected)}
        </p>
        <p>
          Efectivo contado:
          ${formatMoney(closing.cash_counted)}
        </p>
        <p>
          Diferencia:
          <strong>${
            formatMoney(closing.cash_difference)
          }</strong>
        </p>
        <p>
          Transferencias:
          ${formatMoney(
            closing.bank_transfer_total
          )}
        </p>
        <p>
          Tarjetas:
          ${formatMoney(closing.card_total)}
        </p>
        <p>
          Otros:
          ${formatMoney(closing.other_total)}
        </p>
        <p>
          Observaciones:
          ${escapeHtml(closing.notes || "—")}
        </p>
      `;

      cashClosingReceipt.hidden = false;
      cashClosingForm.reset();
      await loadCashClosing();
      showSuccess("Caja cerrada correctamente.");
    } catch (error) {
      showError(error.message);
    }
  }
);


document.getElementById(
  "printCashClosingButton"
).addEventListener(
  "click",
  () => window.print()
);


forgotPasswordButton.addEventListener(
  "click",
  () => {
    passwordResetEmail.value = loginEmail.value;
    loginForm.hidden = true;
    passwordResetRequestForm.hidden = false;
    passwordResetEmail.focus();
  }
);


backToSignInButton.addEventListener(
  "click",
  () => {
    passwordResetRequestForm.hidden = true;
    loginForm.hidden = false;
    loginEmail.focus();
  }
);


passwordResetRequestForm.addEventListener(
  "submit",
  async event => {
    event.preventDefault();

    passwordResetRequestButton.disabled = true;
    passwordResetRequestButton.textContent =
      "Enviando…";

    try {
      const result = await apiRequest(
        "/auth/password-reset/request",
        {
          method: "POST",
          body: JSON.stringify({
            email: passwordResetEmail.value,
            product_slug: "prestamodesk"
          })
        }
      );

      passwordResetRequestForm.reset();
      passwordResetRequestForm.hidden = true;
      loginForm.hidden = false;
      showSuccess(result.message);
    } catch (error) {
      showError(error.message);
    } finally {
      passwordResetRequestButton.disabled = false;
      passwordResetRequestButton.textContent =
        "Enviar enlace";
    }
  }
);


loginForm.addEventListener(
  "submit",
  async event => {
    event.preventDefault();

    try {
      await apiRequest(
        "/auth/login",
        {
          method: "POST",
          body: JSON.stringify({
            email: loginEmail.value,
            password:
              document.getElementById(
                "loginPassword"
              ).value
          })
        }
      );

      await discoverAccess();
      await searchLoans();
      await loadCashClosing();
      loginForm.reset();
      setAuthenticatedUI(true);
      showSuccess("Sesión de caja iniciada.");
    } catch (error) {
      showError(error.message);
    }
  }
);


logoutButton.addEventListener(
  "click",
  async () => {
    try {
      await apiRequest(
        "/auth/logout",
        {method: "POST"}
      );
    } catch {
      // Continue local sign-out.
    }

    tenantId = null;
    localStorage.removeItem(TENANT_STORAGE_KEY);
    location.reload();
  }
);


async function initialize() {
  await checkHealth();
  setDefaultPaymentDate();

  if (!tenantId) {
    setAuthenticatedUI(false);
    return;
  }

  try {
    await discoverAccess();
    await searchLoans();
    await loadCashClosing();
    setAuthenticatedUI(true);
  } catch {
    tenantId = null;
    localStorage.removeItem(TENANT_STORAGE_KEY);
    setAuthenticatedUI(false);
  }
}


initialize();
