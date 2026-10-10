const API_BASE = "/api/v1";
const PRODUCT_BASE = "/products/prestamodesk";

let tenantId =
  localStorage.getItem("prestamodesk_tenant_id");

let selectedLoanId = null;
let paymentSubmitting = false;
let paymentNeedsReview = false;
let borrowers = [];
let loanBorrowerNames = new Map();
let loanBorrowerDocuments = new Map();
let loans = [];
let loanDetails = [];
let prospects = [];
let applications = [];
let prospectPage = null;
let lateFeePolicy = null;

const authPanel = document.getElementById("authPanel");
const workspace = document.getElementById("workspace");
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
const logoutButton = document.getElementById("logoutButton");
const clientContext = document.getElementById("clientContext");
const healthStatus = document.getElementById("healthStatus");
const errorMessage = document.getElementById("errorMessage");
const successMessage = document.getElementById("successMessage");
const borrowerForm = document.getElementById("borrowerForm");
const loanForm = document.getElementById("loanForm");
const loanLateFeeEnabled =
  document.getElementById("loanLateFeeEnabled");
const loanType = document.getElementById("loanType");
const loanPrincipal =
  document.getElementById("loanPrincipal");
const vehicleLoanFields =
  document.getElementById("vehicleLoanFields");
const vehicleCashPrice =
  document.getElementById("vehicleCashPrice");
const vehicleDownPayment =
  document.getElementById("vehicleDownPayment");
const paymentForm = document.getElementById("paymentForm");
const borrowerList = document.getElementById("borrowerList");
const loanList = document.getElementById("loanList");
const applicationList =
  document.getElementById("applicationList");
const prospectList =
  document.getElementById("prospectList");
const publicProspectPageLink =
  document.getElementById("publicProspectPageLink");
const loanBorrower = document.getElementById("loanBorrower");
const loanBorrowerSearch = document.getElementById("loanBorrowerSearch");
const loanBorrowerSearchClear = document.getElementById("loanBorrowerSearchClear");
const loanBorrowerSearchStatus = document.getElementById("loanBorrowerSearchStatus");
let borrowerOptionsTenantId = null;
const loanDetailPanel =
  document.getElementById("loanDetailPanel");
const loanDetailTitle =
  document.getElementById("loanDetailTitle");
const loanDetailSummary =
  document.getElementById("loanDetailSummary");
const loanLateFeeForm =
  document.getElementById("loanLateFeeForm");
const loanLateFeeSelected =
  document.getElementById("loanLateFeeSelected");
const installmentList =
  document.getElementById("installmentList");
const paymentPanel =
  document.getElementById("paymentPanel");
const paymentInstallment =
  document.getElementById("paymentInstallment");
const receiptPanel =
  document.getElementById("receiptPanel");
const receiptContent =
  document.getElementById("receiptContent");
const lateFeePolicyForm =
  document.getElementById("lateFeePolicyForm");
const lateFeeEnabled =
  document.getElementById("lateFeeEnabled");
const lateFeeDailyRate =
  document.getElementById("lateFeeDailyRate");
const lateFeeGraceDays =
  document.getElementById("lateFeeGraceDays");
const lateFeeCapPercent =
  document.getElementById("lateFeeCapPercent");
const lateFeeEffectiveDate =
  document.getElementById("lateFeeEffectiveDate");
const lateFeePolicyStatus =
  document.getElementById("lateFeePolicyStatus");


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
    inactive: "Inactivo",
    paid: "Pagado",
    cancelled: "Cancelado",
    pending: "Pendiente",
    partial: "Parcial",
    overdue: "Vencida",
    new: "Nueva",
    reviewing: "En revisión",
    approved: "Aprobada",
    contacted: "Contactado",
    qualified: "Calificado",
    rejected: "Rechazado",
    converted: "Convertido"
  };

  return labels[value] || value;
}


function setAuthenticatedUI(authenticated) {
  authPanel.hidden = authenticated;
  workspace.hidden = !authenticated;
  logoutButton.hidden = !authenticated;
  clientContext.hidden = !authenticated;
}


function optionalInputValue(elementId) {
  return (
    document.getElementById(elementId).value.trim()
    || null
  );
}


function updateVehicleFinancedAmount() {
  if (loanType.value !== "vehicle") {
    return;
  }

  const cashPrice = Number(vehicleCashPrice.value);
  const downPayment = Number(
    vehicleDownPayment.value || 0
  );

  if (
    !Number.isFinite(cashPrice)
    || cashPrice <= 0
    || !Number.isFinite(downPayment)
    || downPayment < 0
    || downPayment > cashPrice
  ) {
    loanPrincipal.value = "";
    return;
  }

  loanPrincipal.value = (
    cashPrice - downPayment
  ).toFixed(2);
}


function updateVehicleLoanFields() {
  const isVehicle = loanType.value === "vehicle";

  vehicleLoanFields.hidden = !isVehicle;
  loanPrincipal.readOnly = isVehicle;

  for (const element of vehicleLoanFields.querySelectorAll(
    "input"
  )) {
    element.required = false;
  }

  if (!isVehicle) {
    loanPrincipal.value = "";
    return;
  }

  for (const elementId of (
    "vehicleCashPrice",
    "vehicleDownPayment",
    "vehicleMake",
    "vehicleModel",
    "vehicleYear"
  )) {
    document.getElementById(elementId).required = true;
  }

  updateVehicleFinancedAmount();
}


function buildLoanPayload() {
  const payload = {
    borrower_id: Number(loanBorrower.value),
    loan_type: loanType.value,
    principal_amount: loanPrincipal.value,
    flat_interest_rate_percent:
      document.getElementById("loanRate").value,
    installment_count: Number(
      document.getElementById(
        "loanInstallments"
      ).value
    ),
    payment_frequency:
      document.getElementById("loanFrequency").value,
    start_date:
      document.getElementById("loanStartDate").value,
    first_payment_date:
      document.getElementById(
        "loanFirstPaymentDate"
      ).value,
    late_fee_enabled: loanLateFeeEnabled.checked
  };

  if (loanType.value === "vehicle") {
    Object.assign(
      payload,
      {
        vehicle_cash_price: vehicleCashPrice.value,
        vehicle_down_payment:
          vehicleDownPayment.value,
        vehicle_make:
          optionalInputValue("vehicleMake"),
        vehicle_model:
          optionalInputValue("vehicleModel"),
        vehicle_year: Number(
          document.getElementById(
            "vehicleYear"
          ).value
        ),
        vehicle_color:
          optionalInputValue("vehicleColor"),
        vehicle_vin:
          optionalInputValue("vehicleVin"),
        vehicle_license_plate:
          optionalInputValue("vehicleLicensePlate"),
        vehicle_seller:
          optionalInputValue("vehicleSeller"),
        vehicle_notes:
          optionalInputValue("vehicleNotes")
      }
    );
  }

  return payload;
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
    let detail = `Solicitud fallida (${response.status})`;

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
  if (client.role === "cashier") {
    window.location.replace("/prestamodesk/caja");
    return;
  }
  tenantId = String(client.tenant_id);
  window.prestamodeskAccess = client;
  window.dispatchEvent(new CustomEvent("prestamodesk-access", {detail: client}));

  localStorage.setItem(
    "prestamodesk_tenant_id",
    tenantId
  );

  clientContext.textContent =
    `Cliente #${client.client_number} · `
    + `${client.name} · ${client.role}`;
}


function canManageLoans() {
  return ["owner", "administrator"].includes(window.prestamodeskAccess?.role);
}

function applyLoanAccess() {
  const manage = canManageLoans();
  for (const id of ["borrowerForm", "loanForm", "applicationList", "prospectList", "borrowerList", "lateFeePolicyForm"]) {
    const panel = document.getElementById(id).closest("section");
    panel.hidden = !manage;
    if (!manage) for (const control of panel.querySelectorAll("input, select, textarea, button")) control.disabled = true;
  }
  for (const id of ["openApplicationCount", "borrowerCount"]) document.getElementById(id).closest("article").hidden = !manage;
  loanLateFeeForm.hidden = !manage;
  loanLateFeeForm.nextElementSibling.hidden = !manage;
  if (!manage) for (const control of loanLateFeeForm.querySelectorAll("input, button")) control.disabled = true;
}

function borrowerNameForLoan(loan) {
  return borrowers.find(item => item.id === loan.borrower_id)?.full_name
    || loanBorrowerNames.get(loan.id)
    || `Prestatario #${loan.borrower_id}`;
}


function renderBorrowerOptions() {
  if (borrowerOptionsTenantId !== tenantId) {
    borrowerOptionsTenantId = tenantId;
    loanBorrowerSearch.value = "";
    loanBorrower.value = "";
  }
  const manage = canManageLoans();
  const active = manage ? borrowers.filter(item => item.status === "active") : [];
  const selected = active.find(item => String(item.id) === loanBorrower.value);
  const query = normalizeLoanSearch(loanBorrowerSearch.value);
  const compactQuery = query.replace(/[^a-z0-9]/g, "");
  const matches = active.filter(item => {
    if (!query) return true;
    const name = normalizeLoanSearch(item.full_name);
    const documentNumber = normalizeLoanSearch(item.document_number);
    return name.includes(query) || documentNumber.includes(query)
      || Boolean(compactQuery && documentNumber.replace(/[^a-z0-9]/g, "").includes(compactQuery));
  });
  const outsideSearch = selected && !matches.some(item => item.id === selected.id);
  const options = outsideSearch ? [selected, ...matches] : matches;
  const placeholder = document.createElement("option");
  placeholder.value = "";
  placeholder.textContent = active.length ? "Seleccione…" : "No hay prestatarios activos";
  loanBorrower.replaceChildren(placeholder);
  for (const item of options) {
    const option = document.createElement("option");
    option.value = String(item.id);
    option.textContent = item.full_name + (item.document_number ? " · " + item.document_number : "")
      + (outsideSearch && item.id === selected.id ? " · Selección actual" : "");
    loanBorrower.append(option);
  }
  loanBorrower.value = selected ? String(selected.id) : "";
  loanBorrower.disabled = active.length === 0;
  loanBorrowerSearch.disabled = !manage || active.length === 0;
  loanBorrowerSearchClear.disabled = !manage || !loanBorrowerSearch.value;
  loanBorrowerSearchStatus.textContent = !manage ? "" : active.length === 0
    ? "No hay prestatarios activos. Cree o active un prestatario antes de crear el préstamo."
    : matches.length + " coincidencias de " + active.length + " prestatarios activos."
      + (outsideSearch ? " Se conserva el prestatario seleccionado, aunque no coincide con la búsqueda." : "");
}

loanBorrowerSearch.addEventListener("input", renderBorrowerOptions);
loanBorrowerSearch.addEventListener("keydown", event => {
  if (event.key === "Enter") event.preventDefault();
});
loanBorrowerSearchClear.addEventListener("click", () => {
  loanBorrowerSearch.value = "";
  renderBorrowerOptions();
  loanBorrowerSearch.focus();
});
loanBorrower.addEventListener("change", renderBorrowerOptions);


function renderApplications() {
  document.getElementById(
    "applicationResultCount"
  ).textContent = String(applications.length);

  if (applications.length === 0) {
    applicationList.innerHTML = `
      <p class="notice">
        No hay solicitudes de préstamo.
      </p>
    `;
    return;
  }

  applicationList.innerHTML = applications
    .map(application => {
      let actions = "";

      if (application.status === "new") {
        actions = `
          <button
            type="button"
            data-application-status="reviewing"
            data-application-id="${application.id}"
          >
            Iniciar revisión
          </button>
        `;
      } else if (application.status === "reviewing") {
        actions = `
          <button
            type="button"
            data-application-status="approved"
            data-application-id="${application.id}"
          >
            Aprobar
          </button>
          <button
            type="button"
            class="secondary"
            data-application-status="rejected"
            data-application-id="${application.id}"
          >
            Rechazar
          </button>
        `;
      } else if (application.status === "approved") {
        actions = `
          <button
            type="button"
            data-convert-application="${application.id}"
          >
            Convertir en préstamo
          </button>
        `;
      } else if (
        application.status === "converted"
        && application.converted_loan_id
      ) {
        actions = `
          <button
            type="button"
            data-application-loan="${
              application.converted_loan_id
            }"
          >
            Ver préstamo
          </button>
        `;
      }

      const contact = [
        application.phone,
        application.email
      ].filter(Boolean).join(" · ");

      const vehicle = [
        application.vehicle_make,
        application.vehicle_model,
        application.vehicle_year
      ].filter(Boolean).join(" ");

      return `
        <article class="item-card">
          <div class="section-heading">
            <h3>
              Solicitud #${application.id}
              · ${escapeHtml(application.full_name)}
            </h3>
            <span class="badge">
              ${escapeHtml(
                formatStatus(application.status)
              )}
            </span>
          </div>

          <div class="item-meta">
            <span>
              ${escapeHtml(
                application.document_type
              )}:
              ${escapeHtml(
                application.document_number || "No indicado"
              )}
            </span>
            ${
              contact
                ? `<span>${escapeHtml(contact)}</span>`
                : ""
            }
            <span>Tipo: ${application.loan_type === "vehicle" ? "Vehículo" : "Personal"}</span>
            ${application.source_prospect_id ? `<span>Prospecto #${application.source_prospect_id}</span>` : ""}
            ${application.loan_type === "vehicle" ? `
            <span>Vehículo: ${escapeHtml(vehicle)}</span>
            <span>Precio: ${formatMoney(application.vehicle_cash_price)}</span>
            <span>Inicial: ${formatMoney(application.vehicle_down_payment)}</span>
            ` : ""}
            <span>
              Financiado: ${formatMoney(
                application.principal_amount
              )}
            </span>
            <span>
              Interés: ${formatMoney(
                application.total_interest
              )}
            </span>
            <span>
              Total: ${formatMoney(
                application.total_due
              )}
            </span>
            <span>
              Cuotas: ${application.installment_count}
            </span>
          </div>

          <div class="item-actions">
            ${actions}
          </div>
        </article>
      `;
    })
    .join("");
}


document.getElementById("borrowerFilterForm").addEventListener("submit", event => event.preventDefault());
document.getElementById("borrowerSearchQuery").addEventListener("input", renderBorrowers);
document.getElementById("borrowerStatusFilter").addEventListener("change", renderBorrowers);
document.getElementById("borrowerFilterClear").addEventListener("click", () => {
  document.getElementById("borrowerSearchQuery").value = "";
  document.getElementById("borrowerStatusFilter").value = "all";
  renderBorrowers();
  document.getElementById("borrowerSearchQuery").focus();
});
let borrowerFilterTenantId = null;
function renderBorrowers() {
  const search = document.getElementById("borrowerSearchQuery");
  const status = document.getElementById("borrowerStatusFilter");
  if (borrowerFilterTenantId !== tenantId) {
    borrowerFilterTenantId = tenantId;
    search.value = "";
    status.value = "all";
  }
  const query = normalizeLoanSearch(search.value);
  const compactQuery = query.replace(/[^a-z0-9]/g, "");
  const matches = borrowers.filter(item => {
    if (status.value !== "all" && item.status !== status.value) return false;
    const name = normalizeLoanSearch(item.full_name);
    const number = normalizeLoanSearch(item.document_number);
    return !query || name.includes(query) || number.includes(query)
      || Boolean(compactQuery && number.replace(/[^a-z0-9]/g, "").includes(compactQuery));
  });
  document.getElementById("borrowerFilterResult").textContent =
    `Mostrando ${matches.length} de ${borrowers.length} prestatarios.`;
  document.getElementById(
    "borrowerCount"
  ).textContent = String(borrowers.length);

  document.getElementById(
    "borrowerResultCount"
  ).textContent = String(matches.length);

  if (borrowers.length === 0) {
    borrowerList.innerHTML =
      '<p>No hay prestatarios registrados.</p>';
    return;
  }

  if (matches.length === 0) {
    borrowerList.innerHTML = '<p>No hay prestatarios que coincidan con los filtros.</p>';
    return;
  }
  borrowerList.innerHTML = matches
    .map(item => `
      <article class="item-card">
        <h3>${escapeHtml(item.full_name)}</h3>
        <div class="item-meta">
          <span>${escapeHtml(
            formatStatus(item.status)
          )}</span>
          ${
            item.document_number
              ? `<span>Documento: ${
                  escapeHtml(item.document_number)
                }</span>`
              : ""
          }
          ${
            item.phone
              ? `<span>Teléfono: ${
                  escapeHtml(item.phone)
                }</span>`
              : ""
          }
          ${
            item.province
              ? `<span>Provincia: ${
                  escapeHtml(item.province)
                }</span>`
              : ""
          }
        </div>
        <div class="item-actions"><button type="button" class="secondary" data-view-borrower="${Number(item.id)}">Ver detalle</button></div>
      </article>
    `)
    .join("");

}


let selectedBorrowerId = null;
let borrowerDetailTenantId = null;
function clearBorrowerDetail() {
  selectedBorrowerId = null;
  borrowerDetailTenantId = null;
  document.getElementById("borrowerDetailPanel").hidden = true;
  for (const id of ["borrowerDetailTitle", "borrowerContactDetails", "borrowerBalanceSummary", "borrowerLoanList"]) document.getElementById(id).replaceChildren();
}
function renderBorrowerDetail() {
  const borrower = borrowers.find(item => item.id === selectedBorrowerId);
  if (!canManageLoans() || borrowerDetailTenantId !== tenantId || !borrower) {
    clearBorrowerDetail(); return;
  }
  const title = document.getElementById("borrowerDetailTitle");
  title.textContent = borrower.full_name;
  const contact = document.getElementById("borrowerContactDetails");
  contact.replaceChildren();
  const labels = {cedula:"Cédula", passport:"Pasaporte", other:"Otro"};
  for (const [label,value] of [
    ["Estado",formatStatus(borrower.status)],
    ["Tipo de documento",labels[borrower.document_type] || borrower.document_type],
    ["Documento",borrower.document_number],["Teléfono",borrower.phone],
    ["Correo",borrower.email],["Dirección",borrower.address],
    ["Municipio",borrower.municipality],["Provincia",borrower.province],
    ["Observaciones",borrower.notes]
  ]) {
    const field = document.createElement("span");
    field.textContent = label + ": " + (value || "No registrado");
    contact.append(field);
  }
  const linked = loanDetails.filter(loan => loan.borrower_id === borrower.id);
  const balance = loan => loan.installments.reduce((sum,item) => sum + Math.max(0,Number(item.total_due)-Number(item.paid_amount)),0);
  const active = linked.filter(loan => loan.status === "active");
  document.getElementById("borrowerBalanceSummary").textContent =
    `Préstamos: ${linked.length} · Activos: ${active.length} · Saldo ordinario pendiente: ${formatMoney(active.reduce((sum,loan)=>sum+balance(loan),0))}`;
  const list = document.getElementById("borrowerLoanList");
  list.replaceChildren();
  if (!linked.length) {
    const empty = document.createElement("p"); empty.textContent = "No hay préstamos para este prestatario."; list.append(empty);
  }
  for (const loan of linked) {
    const card = document.createElement("article"); card.className = "item-card";
    const heading = document.createElement("h4"); heading.textContent = "Préstamo #" + loan.id;
    const info = document.createElement("p");
    info.textContent = `${loan.loan_type === "vehicle" ? "Vehículo" : "Personal"} · ${formatStatus(loan.status)} · Financiado: ${formatMoney(loan.principal_amount)}`
      + (loan.status === "cancelled" ? "" : ` · Saldo ordinario: ${formatMoney(balance(loan))}`);
    const button = document.createElement("button"); button.type = "button"; button.className = "secondary";
    button.dataset.borrowerLoan = String(loan.id); button.textContent = "Ver préstamo";
    card.append(heading,info,button); list.append(card);
  }
  document.getElementById("borrowerDetailPanel").hidden = false;
}
borrowerList.addEventListener("click", event => {
  const button = event.target.closest("button[data-view-borrower]");
  if (!button || !canManageLoans()) return;
  selectedBorrowerId = Number(button.dataset.viewBorrower); borrowerDetailTenantId = tenantId;
  renderBorrowerDetail();
  if (!document.getElementById("borrowerDetailPanel").hidden) document.getElementById("borrowerDetailTitle").focus();
});
document.getElementById("closeBorrowerDetail").addEventListener("click", () => {
  const button = [...borrowerList.querySelectorAll("[data-view-borrower]")].find(item => Number(item.dataset.viewBorrower) === selectedBorrowerId);
  clearBorrowerDetail();
  (button || document.getElementById("borrowerSearchQuery")).focus();
});
document.getElementById("borrowerLoanList").addEventListener("click", async event => {
  const button = event.target.closest("button[data-borrower-loan]");
  if (!button || !canManageLoans() || borrowerDetailTenantId !== tenantId) return;
  const id = Number(button.dataset.borrowerLoan);
  if (!loanDetails.some(loan=>loan.id===id && loan.borrower_id===selectedBorrowerId)) return;
  await openLoan(id);
});

function renderProspects() {
  document.getElementById(
    "prospectResultCount"
  ).textContent = String(prospects.length);

  if (prospectPage) {
    publicProspectPageLink.href =
      `/prestamodesk/solicitar/${
        encodeURIComponent(prospectPage.tenant_slug)
      }`;
    publicProspectPageLink.hidden = false;
  } else {
    publicProspectPageLink.hidden = true;
  }

  if (prospects.length === 0) {
    prospectList.innerHTML =
      "<p>No hay prospectos registrados.</p>";
    return;
  }

  prospectList.innerHTML = prospects
    .map(item => {
      const actions = [];
      const linked = applications.find(application => application.source_prospect_id === item.id);

      if (
        !linked && (item.status === "new"
        || item.status === "contacted")
      ) {
        actions.push(`
          <button
            type="button"
            class="secondary"
            data-prospect-id="${item.id}"
            data-prospect-status="qualified"
          >
            Calificar
          </button>
        `);
      }

      if (!linked && item.status === "new") {
        actions.push(`
          <button
            type="button"
            class="secondary"
            data-prospect-id="${item.id}"
            data-prospect-status="contacted"
          >
            Marcar contactado
          </button>
        `);
      }

      if (
        !linked && item.status !== "rejected"
        && item.status !== "converted"
      ) {
        actions.push(`
          <button
            type="button"
            class="secondary"
            data-prospect-id="${item.id}"
            data-prospect-status="rejected"
          >
            Rechazar
          </button>
        `);
      }

      if (!linked && item.status === "qualified") {
        actions.push(`
          <button
            type="button"
            data-start-prospect-application="${item.id}"
          >
            Seleccionar tipo y preparar solicitud
          </button>
        `);
      }

      if (linked) {
        actions.push(`<span class="notice">Solicitud #${linked.id} · ${linked.loan_type === "vehicle" ? "Vehículo" : "Personal"} · ${escapeHtml(formatStatus(linked.status))}. Continúe en Solicitudes de préstamo.</span>`);
      }
      return `
        <article class="item-card">
          <h3>${escapeHtml(item.full_name)}</h3>
          <div class="item-meta">
            <span>
              ${escapeHtml(formatStatus(item.status))}
            </span>
            <span>
              Monto solicitado:
              ${formatMoney(item.requested_amount)}
            </span>
            <span>
              Teléfono: ${escapeHtml(item.phone)}
            </span>
            ${
              item.email
                ? `<span>Correo: ${
                    escapeHtml(item.email)
                  }</span>`
                : ""
            }
            ${
              item.province
                ? `<span>Provincia: ${
                    escapeHtml(item.province)
                  }</span>`
                : ""
            }
            <span>
              Contacto preferido:
              ${escapeHtml(item.preferred_contact)}
            </span>
          </div>
          ${
            item.message
              ? `<p>${escapeHtml(item.message)}</p>`
              : ""
          }
          <div class="item-actions">
            ${actions.join("")}
          </div>
        </article>
      `;
    })
    .join("");
}


function loanPortfolioToday() {
  const parts = new Intl.DateTimeFormat("en", {timeZone: "America/Santo_Domingo", year: "numeric", month: "2-digit", day: "2-digit"}).formatToParts(new Date());
  return ["year", "month", "day"].map(type => parts.find(part => part.type === type).value).join("-");
}

function normalizeLoanSearch(value) {
  return String(value || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("es-DO").replace(/\s+/g, " ").trim();
}

function filteredLoans() {
  const query = normalizeLoanSearch(document.getElementById("loanSearchQuery").value);
  const compactQuery = query.replace(/[^a-z0-9]/g, "");
  const status = document.getElementById("loanStatusFilter").value;
  const today = loanPortfolioToday();
  const overdueIds = new Set(loanDetails.filter(detail => detail.status === "active" && detail.installments.some(item =>
    item.due_date < today && Number(item.total_due) - Number(item.paid_amount) > 0
  )).map(detail => detail.id));
  return loans.filter(loan => {
    if (status === "overdue" ? !overdueIds.has(loan.id) : status !== "all" && loan.status !== status) return false;
    if (!query) return true;
    const borrower = borrowers.find(item => item.id === loan.borrower_id);
    const documentNumber = borrower?.document_number || loanBorrowerDocuments.get(loan.id) || "";
    const searchable = normalizeLoanSearch(`${loan.id} #${loan.id} Préstamo #${loan.id} ${borrowerNameForLoan(loan)} ${documentNumber}`);
    return searchable.includes(query) || Boolean(compactQuery && normalizeLoanSearch(documentNumber).replace(/[^a-z0-9]/g, "").includes(compactQuery));
  });
}

function renderLoans() {
  const visibleLoans = filteredLoans();
  document.getElementById("loanFilterResult").textContent = `Mostrando ${visibleLoans.length} de ${loans.length} préstamos.`;
  document.getElementById(
    "loanResultCount"
  ).textContent = String(visibleLoans.length);

  const activeLoans = loans.filter(
    loan => loan.status === "active"
  );

  document.getElementById(
    "activeLoanCount"
  ).textContent = String(activeLoans.length);

  if (visibleLoans.length === 0) {
    loanList.innerHTML =
      loans.length === 0 ? '<p>No hay préstamos registrados.</p>' : '<p>No hay préstamos que coincidan con los filtros.</p>';
    return;
  }

  loanList.innerHTML = visibleLoans
    .map(loan => {

      const vehicleDescription = (
        loan.loan_type === "vehicle"
          ? `
            <span>
              Vehículo:
              ${escapeHtml(loan.vehicle_make)}
              ${escapeHtml(loan.vehicle_model)}
              ${escapeHtml(loan.vehicle_year)}
            </span>
          `
          : ""
      );

      return `
        <article class="item-card">
          <h3>
            Préstamo #${loan.id}
            · ${escapeHtml(
              borrowerNameForLoan(loan)
            )}
          </h3>
          <div class="item-meta">
            <span>
              Tipo: ${
                loan.loan_type === "vehicle"
                  ? "Vehículo"
                  : "Personal"
              }
            </span>
            ${vehicleDescription}
            <span>
              Financiado: ${formatMoney(
                loan.principal_amount
              )}
            </span>
            <span>
              Total: ${formatMoney(loan.total_due)}
            </span>
            <span>
              ${loan.installment_count} cuotas
            </span>
            <span>
              ${escapeHtml(
                formatStatus(loan.status)
              )}
            </span>
            <span>
              Mora: ${
                loan.late_fee_enabled
                  ? "Activada"
                  : "No activada"
              }
            </span>
          </div>
          <div class="item-actions">
            <button
              type="button"
              data-view-loan="${loan.id}"
            >
              Ver préstamo
            </button>
          </div>
        </article>
      `;
    })
    .join("");
}


const loanFilterForm = document.getElementById("loanFilterForm");
loanFilterForm.addEventListener("submit", event => {event.preventDefault(); renderLoans();});
document.getElementById("loanSearchQuery").addEventListener("input", renderLoans);
document.getElementById("loanStatusFilter").addEventListener("change", renderLoans);
document.getElementById("loanFilterClear").addEventListener("click", () => {
  loanFilterForm.reset(); renderLoans(); document.getElementById("loanSearchQuery").focus();
});


function updatePortfolioSummary() {
  const today = loanPortfolioToday();

  document.getElementById(
    "openApplicationCount"
  ).textContent = String(
    applications.filter(
      item => !["rejected", "converted"].includes(
        item.status
      )
    ).length
  );

  let outstanding = 0;
  let overdue = 0;

  for (const detail of loanDetails) {
    for (const item of detail.installments) {
      const balance =
        Number(item.total_due)
        - Number(item.paid_amount);

      outstanding += balance;

      if (
        balance > 0
        && item.due_date < today
      ) {
        overdue += 1;
      }
    }
  }

  document.getElementById(
    "outstandingBalance"
  ).textContent = formatMoney(outstanding);

  document.getElementById(
    "overdueCount"
  ).textContent = String(overdue);
}


function setDefaultLateFeePolicy() {
  lateFeePolicy = null;
  lateFeeEnabled.checked = false;
  lateFeeDailyRate.value = "0.1000";
  lateFeeGraceDays.value = "5";
  lateFeeCapPercent.value = "25.0000";

  if (!lateFeeEffectiveDate.value) {
    lateFeeEffectiveDate.value =
      new Date().toISOString().slice(0, 10);
  }

  lateFeePolicyStatus.textContent =
    "No configurada. Guarde para crear la política.";
}


function renderLateFeePolicy(policy) {
  lateFeePolicy = policy;
  lateFeeEnabled.checked = policy.enabled;
  lateFeeDailyRate.value = policy.daily_rate_percent;
  lateFeeGraceDays.value = policy.grace_days;
  lateFeeCapPercent.value = policy.cap_percent;
  lateFeeEffectiveDate.value = policy.effective_date;

  lateFeePolicyStatus.textContent = policy.enabled
    ? (
      "Mora activa desde "
      + policy.effective_date
      + "."
    )
    : "Política guardada, pero la mora está desactivada.";
}


async function loadLateFeePolicy() {
  try {
    const policy = await apiRequest(
      `${PRODUCT_BASE}/late-fee-policy`
    );
    renderLateFeePolicy(policy);
  } catch (error) {
    if (error.status === 404) {
      setDefaultLateFeePolicy();
      return;
    }

    throw error;
  }
}


async function loadDashboard() {
  if (borrowerDetailTenantId !== tenantId || !canManageLoans()) clearBorrowerDetail();
  applyLoanAccess();
  loanBorrowerNames = new Map();
  loanBorrowerDocuments = new Map();
  if (canManageLoans()) {
    [borrowers, loans, prospects, applications, prospectPage] = await Promise.all([
      apiRequest(`${PRODUCT_BASE}/borrowers`),
      apiRequest(`${PRODUCT_BASE}/loans`),
      apiRequest(`${PRODUCT_BASE}/prospects`),
      apiRequest(`${PRODUCT_BASE}/applications`),
      apiRequest(`${PRODUCT_BASE}/prospects/public-page`)
    ]);
    await loadLateFeePolicy();
  } else {
    borrowers = []; prospects = []; applications = []; prospectPage = null; lateFeePolicy = null;
    const [readableLoans, cashierLoans] = await Promise.all([
      apiRequest(`${PRODUCT_BASE}/loans`),
      apiRequest(`${PRODUCT_BASE}/cashier/loans`)
    ]);
    loans = readableLoans;
    loanBorrowerNames = new Map(cashierLoans.map(loan => [loan.id, loan.borrower_full_name]));
    loanBorrowerDocuments = new Map(cashierLoans.map(loan => [loan.id, loan.borrower_document_number || ""]));
  }

  loanDetails = await Promise.all(
    loans.map(
      loan => apiRequest(
        `${PRODUCT_BASE}/loans/${loan.id}`
      )
    )
  );

  renderApplications();
  renderProspects();
  renderBorrowers();
  renderBorrowerOptions();
  renderLoans();
  updatePortfolioSummary();
  renderBorrowerDetail();
}


function renderLoanDetail(detail) {

  loanDetailTitle.textContent =
    `Préstamo #${detail.id} · `
    + borrowerNameForLoan(detail);

  const outstanding = detail.installments.reduce(
    (total, item) => (
      total
      + Number(item.total_due)
      - Number(item.paid_amount)
    ),
    0
  );

  const vehicleSummary = (
    detail.loan_type === "vehicle"
      ? `
        <h3>Vehículo financiado</h3>
        <div class="item-meta">
          <span>
            ${escapeHtml(detail.vehicle_make)}
            ${escapeHtml(detail.vehicle_model)}
            ${escapeHtml(detail.vehicle_year)}
          </span>
          <span>
            Precio: ${formatMoney(
              detail.vehicle_cash_price
            )}
          </span>
          <span>
            Inicial: ${formatMoney(
              detail.vehicle_down_payment
            )}
          </span>
          ${
            detail.vehicle_color
              ? `<span>Color: ${
                  escapeHtml(detail.vehicle_color)
                }</span>`
              : ""
          }
          ${
            detail.vehicle_vin
              ? `<span>VIN/chasis: ${
                  escapeHtml(detail.vehicle_vin)
                }</span>`
              : ""
          }
          ${
            detail.vehicle_license_plate
              ? `<span>Placa: ${
                  escapeHtml(
                    detail.vehicle_license_plate
                  )
                }</span>`
              : ""
          }
          ${
            detail.vehicle_seller
              ? `<span>Vendedor: ${
                  escapeHtml(detail.vehicle_seller)
                }</span>`
              : ""
          }
        </div>
        ${
          detail.vehicle_notes
            ? `<p>${escapeHtml(
                detail.vehicle_notes
              )}</p>`
            : ""
        }
      `
      : ""
  );

  loanDetailSummary.innerHTML = `
    <div class="item-meta">
      <span>
        Tipo: ${
          detail.loan_type === "vehicle"
            ? "Vehículo"
            : "Personal"
        }
      </span>
      <span>
        Financiado: ${formatMoney(
          detail.principal_amount
        )}
      </span>
      <span>
        Interés: ${formatMoney(detail.total_interest)}
      </span>
      <span>
        Total: ${formatMoney(detail.total_due)}
      </span>
      <span>
        Saldo: ${formatMoney(outstanding)}
      </span>
      <span>
        Estado: ${escapeHtml(
          formatStatus(detail.status)
        )}
      </span>
      <span>
        Mora: ${
          detail.late_fee_enabled
            ? "Activada"
            : "No activada"
        }
      </span>
    </div>
    ${vehicleSummary}
  `;

  loanLateFeeSelected.checked = (
    detail.late_fee_enabled
  );

  installmentList.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Cuota</th>
          <th>Vence</th>
          <th>Total</th>
          <th>Pagado</th>
          <th>Saldo</th>
          <th>Estado</th>
        </tr>
      </thead>
      <tbody>
        ${detail.installments.map(item => `
          <tr>
            <td>${item.sequence_number}</td>
            <td>${escapeHtml(item.due_date)}</td>
            <td>${formatMoney(item.total_due)}</td>
            <td>${formatMoney(item.paid_amount)}</td>
            <td>${formatMoney(
              Number(item.total_due)
              - Number(item.paid_amount)
            )}</td>
            <td>${escapeHtml(
              formatStatus(item.status)
            )}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;

  const payable = detail.installments.filter(
    item => (
      Number(item.total_due)
      > Number(item.paid_amount)
    )
  );

  paymentInstallment.innerHTML = payable
    .map(item => `
      <option
        value="${item.id}"
        data-balance="${
          Number(item.total_due)
          - Number(item.paid_amount)
        }"
      >
        Cuota ${item.sequence_number}
        · vence ${escapeHtml(item.due_date)}
        · ${formatMoney(
          Number(item.total_due)
          - Number(item.paid_amount)
        )}
      </option>
    `)
    .join("");

  loanDetailPanel.hidden = false;
  paymentPanel.hidden = (
    detail.status !== "active"
    || payable.length === 0
  );
  receiptPanel.hidden = true;
}


async function openLoan(loanId) {
  const detail = await apiRequest(
    `${PRODUCT_BASE}/loans/${loanId}`
  );

  selectedLoanId = loanId;
  renderLoanDetail(detail);
  await window.prestamodeskPaymentHistory?.load(loanId, window.prestamodeskAccess?.role);
  loanDetailPanel.scrollIntoView({
    behavior: "smooth",
    block: "start"
  });
}


loanLateFeeForm.addEventListener(
  "submit",
  async event => {
    event.preventDefault();
    clearMessages();

    if (!selectedLoanId) {
      showError("Seleccione un préstamo.");
      return;
    }

    const loanId = selectedLoanId;

    try {
      await apiRequest(
        `${PRODUCT_BASE}/loans/${loanId}/late-fee`,
        {
          method: "PUT",
          body: JSON.stringify({
            late_fee_enabled:
              loanLateFeeSelected.checked
          })
        }
      );

      await loadDashboard();
      await openLoan(loanId);
      showSuccess(
        "Selección de mora del préstamo guardada."
      );
    } catch (error) {
      showError(error.message);
    }
  }
);


lateFeePolicyForm.addEventListener(
  "submit",
  async event => {
    event.preventDefault();
    clearMessages();

    try {
      const policy = await apiRequest(
        `${PRODUCT_BASE}/late-fee-policy`,
        {
          method: "PUT",
          body: JSON.stringify({
            enabled: lateFeeEnabled.checked,
            daily_rate_percent:
              lateFeeDailyRate.value,
            grace_days: Number(
              lateFeeGraceDays.value
            ),
            cap_percent:
              lateFeeCapPercent.value,
            effective_date:
              lateFeeEffectiveDate.value
          })
        }
      );

      renderLateFeePolicy(policy);
      showSuccess("Política de mora guardada.");
    } catch (error) {
      showError(error.message);
    }
  }
);


borrowerForm.addEventListener(
  "submit",
  async event => {
    event.preventDefault();

    try {
      await apiRequest(
        `${PRODUCT_BASE}/borrowers`,
        {
          method: "POST",
          body: JSON.stringify({
            full_name:
              document.getElementById(
                "borrowerName"
              ).value.trim(),
            document_type:
              document.getElementById(
                "borrowerDocumentType"
              ).value,
            document_number:
              document.getElementById(
                "borrowerDocumentNumber"
              ).value.trim() || null,
            phone:
              document.getElementById(
                "borrowerPhone"
              ).value.trim() || null,
            municipality:
              document.getElementById(
                "borrowerMunicipality"
              ).value.trim() || null,
            province:
              document.getElementById(
                "borrowerProvince"
              ).value.trim() || null
          })
        }
      );

      borrowerForm.reset();
      await loadDashboard();
      showSuccess("Prestatario guardado.");
    } catch (error) {
      showError(error.message);
    }
  }
);


loanForm.addEventListener(
  "submit",
  async event => {
    event.preventDefault();

    try {
      const detail = await apiRequest(
        `${PRODUCT_BASE}/loans`,
        {
          method: "POST",
          body: JSON.stringify(
            buildLoanPayload()
          )
        }
      );

      loanForm.reset();
      updateVehicleLoanFields();
      await loadDashboard();
      showSuccess("Préstamo creado.");
      await openLoan(detail.id);
    } catch (error) {
      showError(error.message);
    }
  }
);


loanType.addEventListener(
  "change",
  updateVehicleLoanFields
);

vehicleCashPrice.addEventListener(
  "input",
  updateVehicleFinancedAmount
);

vehicleDownPayment.addEventListener(
  "input",
  updateVehicleFinancedAmount
);


const paymentDate = document.getElementById(
  "paymentDate"
);

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

setDefaultPaymentDate();
window.addEventListener("beforeunload", event => {
  if (paymentSubmitting || paymentNeedsReview) {
    event.preventDefault();
    event.returnValue = "";
  }
});


paymentForm.addEventListener(
  "submit",
  async event => {
    event.preventDefault();

    if (paymentSubmitting || paymentNeedsReview || !selectedLoanId || !paymentInstallment.value) return;
    paymentSubmitting = true;
    const loanId = selectedLoanId;
    const submitButton = paymentForm.querySelector('button[type="submit"]');
    const originalLabel = submitButton.textContent;
    const controls = Array.from(workspace.querySelectorAll("button, input, select, textarea"));
    const disabledBefore = controls.map(control => control.disabled);
    controls.forEach(control => { control.disabled = true; });
    submitButton.textContent = "Registrando…";
    let paymentSaved = false;
    let requestStorageKey = null;

    try {
      const paymentPayload = {
        installment_id: Number(paymentInstallment.value),
        amount: Number(document.getElementById("paymentAmount").value).toFixed(2),
        payment_method: document.getElementById("paymentMethod").value,
        reference: document.getElementById("paymentReference").value.trim() || null,
        paid_at: paymentDate.value ? `${paymentDate.value}T12:00:00Z` : null
      };
      requestStorageKey = "prestamodesk-payment-request:" + tenantId + ":" + JSON.stringify(paymentPayload);
      const requestKey = sessionStorage.getItem(requestStorageKey) || crypto.randomUUID();
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
        <p>Monto: ${formatMoney(receipt.amount)}</p>
        <p>
          Saldo de cuota:
          ${formatMoney(receipt.installment_balance)}
        </p>
        <p>
          Saldo del préstamo:
          ${formatMoney(receipt.loan_balance)}
        </p>
        <p>
          Registrado por usuario #${
            receipt.recorded_by_user_id
          }
        </p>
      `;

      paymentForm.reset();
      setDefaultPaymentDate();
      receiptPanel.hidden = false;
      try {
        await loadDashboard();
        await openLoan(loanId);
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
        showError("No se pudo confirmar el resultado del pago. No lo repita: recargue y revise Pagos y correcciones en Caja antes de continuar.");
      } else {
        if (requestStorageKey && error.status !== 409) sessionStorage.removeItem(requestStorageKey);
        showError(error.message);
      }
    } finally {
      paymentSubmitting = false;
      controls.forEach((control, index) => { control.disabled = disabledBefore[index]; });
      submitButton.textContent = originalLabel;
      submitButton.disabled = paymentNeedsReview || !paymentInstallment.value;
    }
  }
);

applicationList.addEventListener(
  "click",
  async event => {
    const statusButton = event.target.closest(
      "button[data-application-status]"
    );
    const convertButton = event.target.closest(
      "button[data-convert-application]"
    );
    const loanButton = event.target.closest(
      "button[data-application-loan]"
    );

    try {
      if (statusButton) {
        const nextStatus =
          statusButton.dataset.applicationStatus;

        await apiRequest(
          `${PRODUCT_BASE}/applications/${
            statusButton.dataset.applicationId
          }`,
          {
            method: "PUT",
            body: JSON.stringify({
              status: nextStatus
            })
          }
        );

        await loadDashboard();
        showSuccess(
          nextStatus === "reviewing"
            ? "Solicitud puesta en revisión."
            : nextStatus === "approved"
              ? "Solicitud aprobada."
              : "Solicitud rechazada."
        );
        return;
      }

      if (convertButton) {
        const confirmed = window.confirm(
          "Esta acción creará el prestatario, "
          + "el préstamo activo y todas sus cuotas. "
          + "¿Desea continuar?"
        );

        if (!confirmed) {
          return;
        }

        const result = await apiRequest(
          `${PRODUCT_BASE}/applications/${
            convertButton.dataset.convertApplication
          }/convert`,
          {
            method: "POST"
          }
        );

        await loadDashboard();
        showSuccess(
          "Solicitud convertida en préstamo."
        );
        await openLoan(result.loan_id);
        return;
      }

      if (loanButton) {
        await openLoan(
          Number(loanButton.dataset.applicationLoan)
        );
      }
    } catch (error) {
      showError(error.message);
    }
  }
);


prospectList.addEventListener(
  "click",
  async event => {
    const statusButton = event.target.closest(
      "button[data-prospect-status]"
    );
    const convertButton = event.target.closest(
      "button[data-convert-prospect]"
    );

    try {
      if (statusButton) {
        await apiRequest(
          `${PRODUCT_BASE}/prospects/${
            statusButton.dataset.prospectId
          }`,
          {
            method: "PUT",
            body: JSON.stringify({
              status:
                statusButton.dataset.prospectStatus
            })
          }
        );

        await loadDashboard();
        showSuccess("Prospecto actualizado.");
        if (statusButton.dataset.prospectStatus === "qualified") {
          openProspectApplication(Number(statusButton.dataset.prospectId));
        }
        return;
      }

      if (convertButton) {
        await apiRequest(
          `${PRODUCT_BASE}/prospects/${
            convertButton.dataset.convertProspect
          }/convert`,
          {
            method: "POST"
          }
        );

        await loadDashboard();
        showSuccess(
          "Prospecto convertido en prestatario."
        );
      }
    } catch (error) {
      showError(error.message);
    }
  }
);


loanList.addEventListener(
  "click",
  async event => {
    const button = event.target.closest(
      "button[data-view-loan]"
    );

    if (!button) {
      return;
    }

    await openLoan(
      Number(button.dataset.viewLoan)
    );
  }
);


document.getElementById(
  "closeLoanDetail"
).addEventListener(
  "click",
  () => {
    selectedLoanId = null;
    loanDetailPanel.hidden = true;
    paymentPanel.hidden = true;
  }
);


document.getElementById(
  "printReceiptButton"
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
      loginEmail.focus();
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
            email:
              document.getElementById(
                "loginEmail"
              ).value,
            password:
              document.getElementById(
                "loginPassword"
              ).value
          })
        }
      );

      await discoverAccess();
      await loadDashboard();
      loginForm.reset();
      setAuthenticatedUI(true);
      showSuccess("Sesión iniciada.");
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
    localStorage.removeItem(
      "prestamodesk_tenant_id"
    );
    location.reload();
  }
);


async function initialize() {
  await checkHealth();

  const today = new Date().toISOString().slice(0, 10);
  document.getElementById(
    "loanStartDate"
  ).value = today;
  lateFeeEffectiveDate.value = today;

  updateVehicleLoanFields();

  if (!tenantId) {
    setAuthenticatedUI(false);
    return;
  }

  try {
    await discoverAccess();
    await loadDashboard();
    setAuthenticatedUI(true);
  } catch {
    tenantId = null;
    localStorage.removeItem(
      "prestamodesk_tenant_id"
    );
    setAuthenticatedUI(false);
  }
}


initialize();
