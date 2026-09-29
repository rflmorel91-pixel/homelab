const API_BASE = "/api/v1";
const PRODUCT_BASE = "/products/prestamodesk";

let tenantId =
  localStorage.getItem("prestamodesk_tenant_id");

let selectedLoanId = null;
let borrowers = [];
let loans = [];
let loanDetails = [];
let prospects = [];
let prospectPage = null;

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
const paymentForm = document.getElementById("paymentForm");
const borrowerList = document.getElementById("borrowerList");
const loanList = document.getElementById("loanList");
const prospectList =
  document.getElementById("prospectList");
const publicProspectPageLink =
  document.getElementById("publicProspectPageLink");
const loanBorrower = document.getElementById("loanBorrower");
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
const paymentInstallment =
  document.getElementById("paymentInstallment");
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
    inactive: "Inactivo",
    paid: "Pagado",
    cancelled: "Cancelado",
    pending: "Pendiente",
    partial: "Parcial",
    overdue: "Vencida",
    new: "Nuevo",
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
    "prestamodesk_tenant_id",
    tenantId
  );

  clientContext.textContent =
    `Cliente #${client.client_number} · `
    + `${client.name} · ${client.role}`;
}


function renderBorrowerOptions() {
  if (borrowers.length === 0) {
    loanBorrower.innerHTML =
      '<option value="">Cree un prestatario primero</option>';
    loanBorrower.disabled = true;
    return;
  }

  loanBorrower.disabled = false;
  loanBorrower.innerHTML =
    '<option value="">Seleccione…</option>'
    + borrowers
      .filter(item => item.status === "active")
      .map(item => `
        <option value="${item.id}">
          ${escapeHtml(item.full_name)}
        </option>
      `)
      .join("");
}


function renderBorrowers() {
  document.getElementById(
    "borrowerCount"
  ).textContent = String(borrowers.length);

  document.getElementById(
    "borrowerResultCount"
  ).textContent = String(borrowers.length);

  if (borrowers.length === 0) {
    borrowerList.innerHTML =
      '<p>No hay prestatarios registrados.</p>';
    renderBorrowerOptions();
    return;
  }

  borrowerList.innerHTML = borrowers
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
      </article>
    `)
    .join("");

  renderBorrowerOptions();
}


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

      if (
        item.status === "new"
        || item.status === "contacted"
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

      if (item.status === "new") {
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
        item.status !== "rejected"
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

      if (item.status === "qualified") {
        actions.push(`
          <button
            type="button"
            data-convert-prospect="${item.id}"
          >
            Convertir en prestatario
          </button>
        `);
      }

      return `
        <article class="item-card">
          <h3>${escapeHtml(item.full_name)}</h3>
          <div class="item-meta">
            <span>
              ${escapeHtml(formatStatus(item.status))}
            </span>
            <span>
              Monto de interés:
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


function renderLoans() {
  document.getElementById(
    "loanResultCount"
  ).textContent = String(loans.length);

  const activeLoans = loans.filter(
    loan => loan.status === "active"
  );

  document.getElementById(
    "activeLoanCount"
  ).textContent = String(activeLoans.length);

  if (loans.length === 0) {
    loanList.innerHTML =
      '<p>No hay préstamos registrados.</p>';
    return;
  }

  loanList.innerHTML = loans
    .map(loan => {
      const borrower = borrowers.find(
        item => item.id === loan.borrower_id
      );

      return `
        <article class="item-card">
          <h3>
            Préstamo #${loan.id}
            · ${escapeHtml(
              borrower?.full_name || "Prestatario"
            )}
          </h3>
          <div class="item-meta">
            <span>
              Principal: ${formatMoney(
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


function updatePortfolioSummary() {
  const today = new Date().toISOString().slice(0, 10);

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


async function loadDashboard() {
  [
    borrowers,
    loans,
    prospects,
    prospectPage
  ] = await Promise.all([
    apiRequest(`${PRODUCT_BASE}/borrowers`),
    apiRequest(`${PRODUCT_BASE}/loans`),
    apiRequest(`${PRODUCT_BASE}/prospects`),
    apiRequest(`${PRODUCT_BASE}/prospects/public-page`)
  ]);

  loanDetails = await Promise.all(
    loans.map(
      loan => apiRequest(
        `${PRODUCT_BASE}/loans/${loan.id}`
      )
    )
  );

  renderProspects();
  renderBorrowers();
  renderLoans();
  updatePortfolioSummary();
}


function renderLoanDetail(detail) {
  const borrower = borrowers.find(
    item => item.id === detail.borrower_id
  );

  loanDetailTitle.textContent =
    `Préstamo #${detail.id} · `
    + (borrower?.full_name || "Prestatario");

  const outstanding = detail.installments.reduce(
    (total, item) => (
      total
      + Number(item.total_due)
      - Number(item.paid_amount)
    ),
    0
  );

  loanDetailSummary.innerHTML = `
    <div class="item-meta">
      <span>
        Principal: ${formatMoney(detail.principal_amount)}
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
    </div>
  `;

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
  loanDetailPanel.scrollIntoView({
    behavior: "smooth",
    block: "start"
  });
}


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
          body: JSON.stringify({
            borrower_id: Number(
              loanBorrower.value
            ),
            principal_amount:
              document.getElementById(
                "loanPrincipal"
              ).value,
            flat_interest_rate_percent:
              document.getElementById(
                "loanRate"
              ).value,
            installment_count: Number(
              document.getElementById(
                "loanInstallments"
              ).value
            ),
            payment_frequency:
              document.getElementById(
                "loanFrequency"
              ).value,
            start_date:
              document.getElementById(
                "loanStartDate"
              ).value,
            first_payment_date:
              document.getElementById(
                "loanFirstPaymentDate"
              ).value
          })
        }
      );

      loanForm.reset();
      await loadDashboard();
      showSuccess("Préstamo creado.");
      await openLoan(detail.id);
    } catch (error) {
      showError(error.message);
    }
  }
);


paymentForm.addEventListener(
  "submit",
  async event => {
    event.preventDefault();

    try {
      const receipt = await apiRequest(
        `${PRODUCT_BASE}/payments`,
        {
          method: "POST",
          body: JSON.stringify({
            installment_id: Number(
              paymentInstallment.value
            ),
            amount:
              document.getElementById(
                "paymentAmount"
              ).value,
            payment_method:
              document.getElementById(
                "paymentMethod"
              ).value,
            reference:
              document.getElementById(
                "paymentReference"
              ).value.trim() || null
          })
        }
      );

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
      receiptPanel.hidden = false;
      await loadDashboard();

      if (selectedLoanId) {
        await openLoan(selectedLoanId);
        receiptPanel.hidden = false;
      }

      showSuccess("Pago registrado.");
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
