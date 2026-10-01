const API_BASE = "/api/v1";
const PRODUCT_BASE = "/products/prestamodesk";

let tenantId =
  localStorage.getItem("prestamodesk_tenant_id");

let selectedLoanId = null;
let borrowers = [];
let loans = [];
let loanDetails = [];
let prospects = [];
let applications = [];
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
      ).value
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
            <span>
              Vehículo: ${escapeHtml(vehicle)}
            </span>
            <span>
              Precio: ${formatMoney(
                application.vehicle_cash_price
              )}
            </span>
            <span>
              Inicial: ${formatMoney(
                application.vehicle_down_payment
              )}
            </span>
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
              borrower?.full_name || "Prestatario"
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


async function loadDashboard() {
  [
    borrowers,
    loans,
    prospects,
    applications,
    prospectPage
  ] = await Promise.all([
    apiRequest(`${PRODUCT_BASE}/borrowers`),
    apiRequest(`${PRODUCT_BASE}/loans`),
    apiRequest(`${PRODUCT_BASE}/prospects`),
    apiRequest(`${PRODUCT_BASE}/applications`),
    apiRequest(`${PRODUCT_BASE}/prospects/public-page`)
  ]);

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
    </div>
    ${vehicleSummary}
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
              ).value.trim() || null,
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
