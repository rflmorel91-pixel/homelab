const API_BASE = "/api/v1";
const PRODUCT_BASE = "/products/prestamodesk";
const TENANT_STORAGE_KEY =
  "prestamodesk_collections_tenant_id";

let tenantId = localStorage.getItem(
  TENANT_STORAGE_KEY
);
let selectedPortfolioItem = null;
let currentRole = null;
let availableCollectors = [];

const authPanel = document.getElementById("authPanel");
const collectionsWorkspace =
  document.getElementById("collectionsWorkspace");
const loginForm = document.getElementById("loginForm");
const loginEmail = document.getElementById("loginEmail");
const loginPassword =
  document.getElementById("loginPassword");
const logoutButton =
  document.getElementById("logoutButton");
const clientContext =
  document.getElementById("clientContext");
const supervisionLink =
  document.getElementById("supervisionLink");
const healthStatus =
  document.getElementById("healthStatus");
const errorMessage =
  document.getElementById("errorMessage");
const successMessage =
  document.getElementById("successMessage");
const portfolioFilterForm =
  document.getElementById("portfolioFilterForm");
const portfolioAsOf =
  document.getElementById("portfolioAsOf");
const portfolioCount =
  document.getElementById("portfolioCount");
const portfolioList =
  document.getElementById("portfolioList");
const collectionDetailPanel =
  document.getElementById("collectionDetailPanel");
const collectionDetailTitle =
  document.getElementById("collectionDetailTitle");
const collectionDetailSummary =
  document.getElementById("collectionDetailSummary");
const activityForm =
  document.getElementById("activityForm");
const activityChannel =
  document.getElementById("activityChannel");
const activityOutcome =
  document.getElementById("activityOutcome");
const activityContactedAt =
  document.getElementById("activityContactedAt");
const activityNextFollowUpAt =
  document.getElementById(
    "activityNextFollowUpAt"
  );
const activityNotes =
  document.getElementById("activityNotes");
const promiseForm =
  document.getElementById("promiseForm");
const promiseAmount =
  document.getElementById("promiseAmount");
const promiseDueDate =
  document.getElementById("promiseDueDate");
const promiseNotes =
  document.getElementById("promiseNotes");
const collectionActivityHistory =
  document.getElementById(
    "collectionActivityHistory"
  );
const paymentPromiseHistory =
  document.getElementById(
    "paymentPromiseHistory"
  );
const overduePromiseList =
  document.getElementById("overduePromiseList");
const portfolioTitle =
  document.getElementById("portfolioTitle");
const portfolioNotice =
  document.getElementById("portfolioNotice");
const assignmentStatusField =
  document.getElementById("assignmentStatusField");
const assignmentStatus =
  document.getElementById("assignmentStatus");
const collectorAssignmentPanel =
  document.getElementById("collectorAssignmentPanel");
const collectorAssignmentForm =
  document.getElementById("collectorAssignmentForm");
const collectorAssignmentUser =
  document.getElementById("collectorAssignmentUser");
const releaseCollectorAssignment =
  document.getElementById(
    "releaseCollectorAssignment"
  );
const collectorAssignmentHistory =
  document.getElementById(
    "collectorAssignmentHistory"
  );


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


function formatDate(value) {
  if (!value) {
    return "—";
  }

  return new Intl.DateTimeFormat(
    "es-DO",
    {dateStyle: "medium"}
  ).format(
    new Date(`${value}T12:00:00`)
  );
}


function formatDateTime(value) {
  if (!value) {
    return "—";
  }

  return new Intl.DateTimeFormat(
    "es-DO",
    {
      dateStyle: "medium",
      timeStyle: "short"
    }
  ).format(new Date(value));
}


function formatRole(value) {
  const labels = {
    owner: "Propietario",
    administrator: "Administrador",
    supervisor: "Supervisor",
    collector: "Cobrador"
  };

  return labels[value] || value;
}


function formatPromiseStatus(value) {
  const labels = {
    pending: "Pendiente",
    partial: "Parcial",
    fulfilled: "Cumplida",
    cancelled: "Cancelada"
  };

  return labels[value] || value;
}


function formatChannel(value) {
  const labels = {
    phone: "Llamada",
    whatsapp: "WhatsApp",
    sms: "SMS",
    email: "Correo",
    visit: "Visita",
    other: "Otro"
  };

  return labels[value] || value;
}


function localDateValue(date = new Date()) {
  const year = date.getFullYear();
  const month = String(
    date.getMonth() + 1
  ).padStart(2, "0");
  const day = String(
    date.getDate()
  ).padStart(2, "0");

  return `${year}-${month}-${day}`;
}


function localDateTimeValue(date = new Date()) {
  const hours = String(
    date.getHours()
  ).padStart(2, "0");
  const minutes = String(
    date.getMinutes()
  ).padStart(2, "0");

  return `${localDateValue(date)}T${hours}:${minutes}`;
}


function setDefaults() {
  portfolioAsOf.value = localDateValue();
  activityContactedAt.value =
    localDateTimeValue();
  promiseDueDate.value = localDateValue();
}


function setAuthenticatedUI(authenticated) {
  authPanel.hidden = authenticated;
  collectionsWorkspace.hidden = !authenticated;
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

  if (!["owner", "administrator", "supervisor", "collector"].includes(client.role)) {
    throw new Error(
      "Esta cuenta no tiene acceso a gestión de cobros."
    );
  }

  currentRole = client.role;
  tenantId = String(client.tenant_id);
  localStorage.setItem(
    TENANT_STORAGE_KEY,
    tenantId
  );

  clientContext.textContent =
    `Cliente #${client.client_number} · `
    + `${client.name} · ${formatRole(client.role)}`;

  supervisionLink.hidden =
    !["owner", "administrator", "supervisor"].includes(client.role);

  const isOwner = ["owner", "administrator", "supervisor"].includes(client.role);

  assignmentStatusField.hidden = !isOwner;
  collectorAssignmentPanel.hidden = !isOwner;

  if (isOwner) {
    portfolioTitle.textContent = "Cartera vencida";
    portfolioNotice.textContent =
      "Incluye todos los préstamos vencidos del cliente. "
      + "Puede filtrar y administrar sus asignaciones.";
  } else {
    portfolioTitle.textContent = "Mi cartera";
    portfolioNotice.textContent =
      "Muestra solamente los préstamos vencidos "
      + "asignados a su usuario.";
  }
}


function renderCollectorOptions() {
  collectorAssignmentUser.innerHTML = `
    <option value="">Seleccione un cobrador</option>
    ${availableCollectors.map(collector => `
      <option value="${collector.user_id}">
        ${escapeHtml(collector.display_name)}
        · ${escapeHtml(collector.email)}
      </option>
    `).join("")}
  `;
}


async function loadCollectors() {
  if (!["owner", "administrator", "supervisor"].includes(currentRole)) {
    availableCollectors = [];
    return;
  }

  availableCollectors = await apiRequest(
    `${PRODUCT_BASE}/collections/collectors`
  );
  renderCollectorOptions();
}


function renderAssignments(items) {
  const active = items.find(item => item.is_active);

  releaseCollectorAssignment.hidden = !active;

  if (active) {
    collectorAssignmentUser.value =
      String(active.collector_user_id);
  } else {
    collectorAssignmentUser.value = "";
  }

  if (items.length === 0) {
    collectorAssignmentHistory.innerHTML =
      '<p class="empty">No hay asignaciones registradas.</p>';
    return;
  }

  collectorAssignmentHistory.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Cobrador</th>
          <th>Asignada</th>
          <th>Liberada</th>
          <th>Estado</th>
          <th>Motivo</th>
        </tr>
      </thead>
      <tbody>
        ${items.map(item => `
          <tr>
            <td>
              <strong>${escapeHtml(
                item.collector_display_name
              )}</strong><br>
              ${escapeHtml(item.collector_email)}
            </td>
            <td>${formatDateTime(item.assigned_at)}</td>
            <td>${formatDateTime(item.released_at)}</td>
            <td>
              ${item.is_active ? "Activa" : "Finalizada"}
            </td>
            <td>
              ${escapeHtml(item.release_reason || "—")}
            </td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}


function renderPortfolio(items) {
  portfolioCount.textContent = String(items.length);

  if (items.length === 0) {
    portfolioList.innerHTML =
      '<p class="empty">No hay cartera vencida.</p>';
    return;
  }

  portfolioList.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Préstamo</th>
          <th>Cliente</th>
          <th>Contacto</th>
          <th>Vencimiento más antiguo</th>
          <th>Días vencidos</th>
          <th>Cuotas</th>
          <th>Saldo vencido</th>
          <th>Cobrador asignado</th>
          <th>Acción</th>
        </tr>
      </thead>
      <tbody>
        ${items.map(item => `
          <tr>
            <td>#${item.loan_id}</td>
            <td>
              <strong>${escapeHtml(
                item.borrower_full_name
              )}</strong><br>
              ${escapeHtml(
                item.borrower_document_number || "—"
              )}
            </td>
            <td>
              ${escapeHtml(
                item.borrower_phone || "—"
              )}<br>
              ${escapeHtml(
                item.borrower_email || "—"
              )}
            </td>
            <td>${formatDate(
              item.oldest_due_date
            )}</td>
            <td>${item.days_overdue}</td>
            <td>${item.overdue_installment_count}</td>
            <td>
              <strong>${formatMoney(
                item.total_balance_due
              )}</strong>
            </td>
            <td>
              ${escapeHtml(
                item.assigned_collector_display_name
                || "Sin asignar"
              )}
            </td>
            <td>
              <button
                type="button"
                class="secondary"
                data-manage-loan="${item.loan_id}"
              >
                Gestionar
              </button>
            </td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}


async function loadPortfolio() {
  clearMessages();

  const params = new URLSearchParams({
    as_of: portfolioAsOf.value
  });

  if (["owner", "administrator", "supervisor"].includes(currentRole)) {
    params.set(
      "assignment_status",
      assignmentStatus.value
    );
  }
  const items = await apiRequest(
    `${PRODUCT_BASE}/collections/portfolio?${params}`
  );

  renderPortfolio(items);
  return items;
}


function renderActivities(items) {
  if (items.length === 0) {
    collectionActivityHistory.innerHTML =
      '<p class="empty">No hay gestiones registradas.</p>';
    return;
  }

  collectionActivityHistory.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Contacto</th>
          <th>Canal</th>
          <th>Resultado</th>
          <th>Seguimiento</th>
          <th>Notas</th>
        </tr>
      </thead>
      <tbody>
        ${items.map(item => `
          <tr>
            <td>${formatDateTime(
              item.contacted_at
            )}</td>
            <td>${escapeHtml(
              formatChannel(item.channel)
            )}</td>
            <td>${escapeHtml(item.outcome)}</td>
            <td>${formatDateTime(
              item.next_follow_up_at
            )}</td>
            <td>${escapeHtml(item.notes || "—")}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}


function renderPromises(items) {
  if (items.length === 0) {
    paymentPromiseHistory.innerHTML =
      '<p class="empty">No hay promesas registradas.</p>';
    return;
  }

  paymentPromiseHistory.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Fecha prometida</th>
          <th>Prometido</th>
          <th>Cumplido</th>
          <th>Pendiente</th>
          <th>Estado</th>
          <th>Notas</th>
          <th>Acción</th>
        </tr>
      </thead>
      <tbody>
        ${items.map(item => `
          <tr>
            <td>${formatDate(item.due_date)}</td>
            <td>${formatMoney(
              item.promised_amount
            )}</td>
            <td>${formatMoney(
              item.fulfilled_amount
            )}</td>
            <td>${formatMoney(
              item.remaining_amount
            )}</td>
            <td>
              ${escapeHtml(
                formatPromiseStatus(item.status)
              )}
              ${item.is_overdue ? " · Vencida" : ""}
            </td>
            <td>${escapeHtml(item.notes || "—")}</td>
            <td>
              ${["pending", "partial"].includes(
                item.status
              ) ? `
                <button
                  type="button"
                  class="secondary"
                  data-cancel-promise="${item.id}"
                >
                  Cancelar
                </button>
              ` : "—"}
            </td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}


function renderOverduePromises(items) {
  if (items.length === 0) {
    overduePromiseList.innerHTML =
      '<p class="empty">No hay promesas vencidas.</p>';
    return;
  }

  overduePromiseList.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Préstamo</th>
          <th>Fecha</th>
          <th>Prometido</th>
          <th>Cumplido</th>
          <th>Pendiente</th>
          <th>Estado</th>
        </tr>
      </thead>
      <tbody>
        ${items.map(item => `
          <tr>
            <td>#${item.loan_id}</td>
            <td>${formatDate(item.due_date)}</td>
            <td>${formatMoney(
              item.promised_amount
            )}</td>
            <td>${formatMoney(
              item.fulfilled_amount
            )}</td>
            <td>
              <strong>${formatMoney(
                item.remaining_amount
              )}</strong>
            </td>
            <td>${escapeHtml(
              formatPromiseStatus(item.status)
            )}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}


async function loadLoanHistory() {
  if (!selectedPortfolioItem) {
    return;
  }

  const loanId = selectedPortfolioItem.loan_id;
  const requests = [
    apiRequest(
      `${PRODUCT_BASE}/collections/loans/`
      + `${loanId}/activities`
    ),
    apiRequest(
      `${PRODUCT_BASE}/collections/loans/`
      + `${loanId}/promises`
    )
  ];

  if (["owner", "administrator", "supervisor"].includes(currentRole)) {
    requests.push(
      apiRequest(
        `${PRODUCT_BASE}/collections/loans/`
        + `${loanId}/assignments`
      )
    );
  }

  const [activities, promises, assignments] =
    await Promise.all(requests);

  renderActivities(activities);
  renderPromises(promises);

  if (["owner", "administrator", "supervisor"].includes(currentRole)) {
    renderAssignments(assignments);
  }
}


async function loadOverduePromises() {
  const params = new URLSearchParams({
    overdue_only: "true",
    as_of: portfolioAsOf.value
  });
  const promises = await apiRequest(
    `${PRODUCT_BASE}/collections/promises?${params}`
  );

  renderOverduePromises(promises);
}


async function openLoan(item) {
  selectedPortfolioItem = item;

  collectionDetailTitle.textContent =
    `Préstamo #${item.loan_id} · `
    + item.borrower_full_name;

  collectionDetailSummary.innerHTML = `
    <p>
      Documento:
      <strong>${escapeHtml(
        item.borrower_document_number || "—"
      )}</strong>
    </p>
    <p>
      Teléfono:
      <strong>${escapeHtml(
        item.borrower_phone || "—"
      )}</strong>
    </p>
    <p>
      Correo:
      <strong>${escapeHtml(
        item.borrower_email || "—"
      )}</strong>
    </p>
    <p>
      Saldo vencido:
      <strong>${formatMoney(
        item.total_balance_due
      )}</strong>
    </p>
    <p>
      Cobrador asignado:
      <strong>${escapeHtml(
        item.assigned_collector_display_name
        || "Sin asignar"
      )}</strong>
    </p>
  `;

  promiseAmount.max = item.total_balance_due;
  collectionDetailPanel.hidden = false;
  await loadLoanHistory();
}


portfolioFilterForm.addEventListener(
  "submit",
  async event => {
    event.preventDefault();

    try {
      await Promise.all([
        loadPortfolio(),
        loadOverduePromises()
      ]);
    } catch (error) {
      showError(error.message);
    }
  }
);


document.getElementById(
  "refreshPortfolioButton"
).addEventListener(
  "click",
  async () => {
    try {
      await Promise.all([
        loadPortfolio(),
        loadOverduePromises()
      ]);
    } catch (error) {
      showError(error.message);
    }
  }
);


document.getElementById(
  "refreshOverduePromisesButton"
).addEventListener(
  "click",
  async () => {
    try {
      await loadOverduePromises();
    } catch (error) {
      showError(error.message);
    }
  }
);


portfolioList.addEventListener(
  "click",
  async event => {
    const button = event.target.closest(
      "[data-manage-loan]"
    );

    if (!button) {
      return;
    }

    try {
      const items = await loadPortfolio();
      const item = items.find(
        candidate =>
          candidate.loan_id
          === Number(button.dataset.manageLoan)
      );

      if (item) {
        await openLoan(item);
      }
    } catch (error) {
      showError(error.message);
    }
  }
);


document.getElementById(
  "closeCollectionDetail"
).addEventListener(
  "click",
  () => {
    selectedPortfolioItem = null;
    collectionDetailPanel.hidden = true;
  }
);


activityForm.addEventListener(
  "submit",
  async event => {
    event.preventDefault();
    clearMessages();

    if (!selectedPortfolioItem) {
      return;
    }

    try {
      await apiRequest(
        `${PRODUCT_BASE}/collections/loans/`
        + `${selectedPortfolioItem.loan_id}/activities`,
        {
          method: "POST",
          body: JSON.stringify({
            channel: activityChannel.value,
            outcome: activityOutcome.value.trim(),
            notes:
              activityNotes.value.trim() || null,
            contacted_at: new Date(
              activityContactedAt.value
            ).toISOString(),
            next_follow_up_at:
              activityNextFollowUpAt.value
                ? new Date(
                    activityNextFollowUpAt.value
                  ).toISOString()
                : null
          })
        }
      );

      activityForm.reset();
      activityContactedAt.value =
        localDateTimeValue();
      await loadLoanHistory();
      showSuccess("Gestión registrada.");
    } catch (error) {
      showError(error.message);
    }
  }
);


collectorAssignmentForm.addEventListener(
  "submit",
  async event => {
    event.preventDefault();
    clearMessages();

    if (
      !["owner", "administrator", "supervisor"].includes(currentRole)
      || !selectedPortfolioItem
    ) {
      return;
    }

    try {
      await apiRequest(
        `${PRODUCT_BASE}/collections/loans/`
        + `${selectedPortfolioItem.loan_id}/assignment`,
        {
          method: "POST",
          body: JSON.stringify({
            collector_user_id: Number(
              collectorAssignmentUser.value
            )
          })
        }
      );

      const refreshedItems = await loadPortfolio();
      selectedPortfolioItem = refreshedItems.find(
        item =>
          item.loan_id === selectedPortfolioItem.loan_id
      ) || selectedPortfolioItem;

      await loadLoanHistory();
      showSuccess("Cobrador asignado.");
    } catch (error) {
      showError(error.message);
    }
  }
);


releaseCollectorAssignment.addEventListener(
  "click",
  async () => {
    clearMessages();

    if (
      !["owner", "administrator", "supervisor"].includes(currentRole)
      || !selectedPortfolioItem
    ) {
      return;
    }

    const confirmed = window.confirm(
      "¿Desea liberar esta asignación?"
    );

    if (!confirmed) {
      return;
    }

    try {
      await apiRequest(
        `${PRODUCT_BASE}/collections/loans/`
        + `${selectedPortfolioItem.loan_id}`
        + "/assignment/release",
        {
          method: "POST",
          body: JSON.stringify({
            reason: "Liberada desde gestión de cobros"
          })
        }
      );

      const refreshedItems = await loadPortfolio();
      selectedPortfolioItem = refreshedItems.find(
        item =>
          item.loan_id === selectedPortfolioItem.loan_id
      ) || {
        ...selectedPortfolioItem,
        assigned_collector_user_id: null,
        assigned_collector_display_name: null
      };

      await loadLoanHistory();
      showSuccess("Asignación liberada.");
    } catch (error) {
      showError(error.message);
    }
  }
);


promiseForm.addEventListener(
  "submit",
  async event => {
    event.preventDefault();
    clearMessages();

    if (!selectedPortfolioItem) {
      return;
    }

    try {
      await apiRequest(
        `${PRODUCT_BASE}/collections/loans/`
        + `${selectedPortfolioItem.loan_id}/promises`,
        {
          method: "POST",
          body: JSON.stringify({
            promised_amount: promiseAmount.value,
            due_date: promiseDueDate.value,
            notes:
              promiseNotes.value.trim() || null
          })
        }
      );

      promiseForm.reset();
      promiseDueDate.value = localDateValue();
      await Promise.all([
        loadLoanHistory(),
        loadOverduePromises()
      ]);
      showSuccess("Promesa de pago registrada.");
    } catch (error) {
      showError(error.message);
    }
  }
);


paymentPromiseHistory.addEventListener(
  "click",
  async event => {
    const button = event.target.closest(
      "[data-cancel-promise]"
    );

    if (!button) {
      return;
    }

    try {
      await apiRequest(
        `${PRODUCT_BASE}/collections/promises/`
        + `${button.dataset.cancelPromise}/cancel`,
        {
          method: "POST",
          body: JSON.stringify({notes: null})
        }
      );

      await Promise.all([
        loadLoanHistory(),
        loadOverduePromises()
      ]);
      showSuccess("Promesa cancelada.");
    } catch (error) {
      showError(error.message);
    }
  }
);


loginForm.addEventListener(
  "submit",
  async event => {
    event.preventDefault();
    clearMessages();

    try {
      await apiRequest(
        "/auth/login",
        {
          method: "POST",
          body: JSON.stringify({
            email: loginEmail.value,
            password: loginPassword.value
          })
        }
      );

      await discoverAccess();
      await loadCollectors();
      await Promise.all([
        loadPortfolio(),
        loadOverduePromises()
      ]);
      loginForm.reset();
      setAuthenticatedUI(true);
      showSuccess("Sesión de cobros iniciada.");
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
  setDefaults();

  if (!tenantId) {
    setAuthenticatedUI(false);
    return;
  }

  try {
    await discoverAccess();
    await loadCollectors();
    await Promise.all([
      loadPortfolio(),
      loadOverduePromises()
    ]);
    setAuthenticatedUI(true);
  } catch {
    tenantId = null;
    localStorage.removeItem(TENANT_STORAGE_KEY);
    setAuthenticatedUI(false);
  }
}


initialize();
