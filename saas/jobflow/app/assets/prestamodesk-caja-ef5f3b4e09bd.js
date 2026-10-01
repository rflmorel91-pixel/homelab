const API_BASE = "/api/v1";
const PRODUCT_BASE = "/products/prestamodesk";
const TENANT_STORAGE_KEY =
  "prestamodesk_cashier_tenant_id";

let tenantId = localStorage.getItem(
  TENANT_STORAGE_KEY
);
let selectedLoanId = null;
let selectedLoan = null;

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
  errorMessage.textContent = message;
  errorMessage.hidden = false;
  successMessage.hidden = true;
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

    throw new Error(detail);
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

  tenantId = String(client.tenant_id);
  localStorage.setItem(
    TENANT_STORAGE_KEY,
    tenantId
  );

  const roleLabel = (
    client.role === "owner"
      ? "Administrador"
      : "Cajero"
  );

  clientContext.textContent =
    `Cliente #${client.client_number} · `
    + `${client.name} · ${roleLabel}`;
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
          <th>Saldo</th>
          <th>Estado</th>
          <th>Acción</th>
        </tr>
      </thead>
      <tbody>
        ${loans.map(loan => `
          <tr>
            <td>#${loan.id}</td>
            <td>
              ${escapeHtml(
                loan.borrower_full_name
              )}
            </td>
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
  const suffix = normalized
    ? `?query=${encodeURIComponent(normalized)}`
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
          <th>Total</th>
          <th>Pagado</th>
          <th>Saldo</th>
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
            <td>
              ${formatMoney(installmentBalance(item))}
            </td>
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
  ).disabled = false;

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
  const loan = await apiRequest(
    `${PRODUCT_BASE}/cashier/loans/${loanId}`
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
      <strong>Total:</strong>
      ${formatMoney(loan.total_due)}
      · <strong>Pagado:</strong>
      ${formatMoney(loan.paid_amount)}
      · <strong>Saldo:</strong>
      ${formatMoney(loan.balance_due)}
    </p>
    <p>
      <strong>Estado:</strong>
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


paymentForm.addEventListener(
  "submit",
  async event => {
    event.preventDefault();
    clearMessages();

    try {
      const paymentMethod =
        document.getElementById(
          "paymentMethod"
        ).value;
      const reference =
        document.getElementById(
          "paymentReference"
        ).value.trim() || null;

      const receipt = await apiRequest(
        `${PRODUCT_BASE}/payments`,
        {
          method: "POST",
          body: JSON.stringify({
            installment_id: Number(
              paymentInstallment.value
            ),
            amount: paymentAmount.value,
            payment_method: paymentMethod,
            reference,
            paid_at: paymentDate.value
              ? `${paymentDate.value}T12:00:00Z`
              : null
          })
        }
      );

      receiptContent.innerHTML = `
        <p>
          <strong>${escapeHtml(
            receipt.receipt_number
          )}</strong>
        </p>
        <p>
          Préstamo:
          <strong>#${selectedLoanId}</strong>
        </p>
        <p>
          Cliente:
          <strong>${escapeHtml(
            selectedLoan.borrower_full_name
          )}</strong>
        </p>
        <p>
          Fecha:
          ${escapeHtml(paymentDate.value)}
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

      receiptPanel.hidden = false;
      paymentForm.reset();
      setDefaultPaymentDate();

      await openLoan(selectedLoanId);
      receiptPanel.hidden = false;
      await searchLoans(loanSearchQuery.value);

      showSuccess("Pago registrado.");
    } catch (error) {
      showError(error.message);
    }
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
    setAuthenticatedUI(true);
  } catch {
    tenantId = null;
    localStorage.removeItem(TENANT_STORAGE_KEY);
    setAuthenticatedUI(false);
  }
}


initialize();
