const API_BASE = "/api/v1";
const PRODUCT_BASE = "/products/prestamodesk";
const TENANT_STORAGE_KEY =
  "prestamodesk_collections_tenant_id";

let tenantId = localStorage.getItem(
  TENANT_STORAGE_KEY
);

const authPanel = document.getElementById("authPanel");
const supervisionWorkspace =
  document.getElementById("supervisionWorkspace");
const loginForm = document.getElementById("loginForm");
const loginEmail = document.getElementById("loginEmail");
const loginPassword =
  document.getElementById("loginPassword");
const logoutButton =
  document.getElementById("logoutButton");
const clientContext =
  document.getElementById("clientContext");
const healthStatus =
  document.getElementById("healthStatus");
const errorMessage =
  document.getElementById("errorMessage");
const supervisionFilterForm =
  document.getElementById("supervisionFilterForm");
const supervisionAsOf =
  document.getElementById("supervisionAsOf");
const exportSupervisionButton =
  document.getElementById(
    "exportSupervisionButton"
  );
const refreshSupervisionButton =
  document.getElementById(
    "refreshSupervisionButton"
  );
const generalSummary =
  document.getElementById("generalSummary");
const dailyOperationsSummary =
  document.getElementById("dailyOperationsSummary");
const agingSummary =
  document.getElementById("agingSummary");
const promiseSummary =
  document.getElementById("promiseSummary");
const collectorPerformance =
  document.getElementById("collectorPerformance");


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


function formatPercent(value) {
  return new Intl.NumberFormat(
    "es-DO",
    {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }
  ).format(Number(value || 0)) + "%";
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


function setAuthenticatedUI(authenticated) {
  authPanel.hidden = authenticated;
  supervisionWorkspace.hidden = !authenticated;
  logoutButton.hidden = !authenticated;
  clientContext.hidden = !authenticated;
}


function showError(message) {
  errorMessage.textContent = message;
  errorMessage.hidden = false;
}


function clearError() {
  errorMessage.hidden = true;
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

  if (client.role === "collector") {
    window.location.replace(
      "/prestamodesk/cobros"
    );
    return false;
  }

  if (!["owner", "administrator", "supervisor"].includes(client.role)) {
    throw new Error(
      "La supervisión requiere rol de propietario, administrador o supervisor."
    );
  }

  tenantId = String(client.tenant_id);
  localStorage.setItem(
    TENANT_STORAGE_KEY,
    tenantId
  );

  clientContext.textContent =
    `Cliente #${client.client_number} · `
    + `${client.name} · ${client.role}`;

  return true;
}


function metric(label, value) {
  return `
    <section>
      <span class="eyebrow">${escapeHtml(label)}</span>
      <h3>${escapeHtml(value)}</h3>
    </section>
  `;
}


function renderGeneralSummary(data) {
  generalSummary.innerHTML = [
    metric(
      "Préstamos vencidos",
      data.overdue_loan_count
    ),
    metric(
      "Saldo vencido",
      formatMoney(data.overdue_balance)
    ),
    metric(
      "Préstamos asignados",
      data.assigned_overdue_loan_count
    ),
    metric(
      "Saldo asignado",
      formatMoney(data.assigned_overdue_balance)
    ),
    metric(
      "Préstamos sin asignar",
      data.unassigned_overdue_loan_count
    ),
    metric(
      "Saldo sin asignar",
      formatMoney(data.unassigned_overdue_balance)
    ),
    metric(
      "Total recuperado",
      formatMoney(data.total_recovered)
    ),
    metric(
      "Gestiones registradas",
      data.activity_count
    ),
    metric(
      "Promesas registradas",
      data.promise_count
    ),
    metric(
      "Promesas vencidas",
      data.overdue_promise_count
    )
  ].join("");
}


function renderDailyOperations(data) {
  dailyOperationsSummary.innerHTML = [
    metric(
      "Promesas para hoy",
      data.promises_due_today_count
    ),
    metric(
      "Seguimientos para hoy",
      data.follow_ups_due_today_count
    ),
    metric(
      "Seguimientos vencidos",
      data.overdue_follow_up_count
    ),
    metric(
      "Promesas vencidas",
      data.overdue_promise_count
    ),
  ].join("");
}

function renderAgingSummary(buckets) {
  agingSummary.innerHTML = buckets.map((bucket) => (
    metric(
      bucket.label,
      `${bucket.loan_count} · ${
        formatMoney(bucket.balance)
      }`
    )
  )).join("");
}

function renderPromiseSummary(data) {
  promiseSummary.innerHTML = [
    metric(
      "Pendientes",
      data.pending_promise_count
    ),
    metric(
      "Parciales",
      data.partial_promise_count
    ),
    metric(
      "Cumplidas",
      data.fulfilled_promise_count
    ),
    metric(
      "Canceladas",
      data.cancelled_promise_count
    ),
    metric(
      "Monto prometido",
      formatMoney(data.promised_amount)
    ),
    metric(
      "Monto cumplido",
      formatMoney(data.fulfilled_amount)
    ),
    metric(
      "Cumplimiento por cantidad",
      formatPercent(
        data.promise_count_fulfillment_percent
      )
    ),
    metric(
      "Cumplimiento por monto",
      formatPercent(
        data.promise_amount_fulfillment_percent
      )
    )
  ].join("");
}


function renderCollectorPerformance(collectors) {
  if (collectors.length === 0) {
    collectorPerformance.innerHTML =
      '<p class="empty">No hay cobradores activos.</p>';
    return;
  }

  const rows = collectors.map(collector => `
    <tr>
      <td>
        <strong>
          ${escapeHtml(collector.display_name)}
        </strong>
        <br>
        <span>
          ${escapeHtml(collector.email)}
        </span>
      </td>
      <td>${collector.active_overdue_loan_count}</td>
      <td>${formatMoney(
        collector.active_overdue_balance
      )}</td>
      <td>${collector.activity_count}</td>
      <td>${collector.promise_count}</td>
      <td>${collector.pending_promise_count}</td>
      <td>${collector.partial_promise_count}</td>
      <td>${collector.fulfilled_promise_count}</td>
      <td>${collector.cancelled_promise_count}</td>
      <td>${collector.overdue_promise_count}</td>
      <td>${formatMoney(collector.promised_amount)}</td>
      <td>${formatMoney(collector.fulfilled_amount)}</td>
      <td>
        ${formatPercent(
          collector.promise_count_fulfillment_percent
        )}
      </td>
      <td>
        ${formatPercent(
          collector.promise_amount_fulfillment_percent
        )}
      </td>
    </tr>
  `).join("");

  collectorPerformance.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Cobrador</th>
          <th>Préstamos asignados</th>
          <th>Saldo asignado</th>
          <th>Gestiones</th>
          <th>Promesas</th>
          <th>Pendientes</th>
          <th>Parciales</th>
          <th>Cumplidas</th>
          <th>Canceladas</th>
          <th>Vencidas</th>
          <th>Prometido</th>
          <th>Cumplido</th>
          <th>Cumplimiento por cantidad</th>
          <th>Cumplimiento por monto</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}


async function exportSupervision() {
  clearError();
  exportSupervisionButton.disabled = true;

  try {
    const params = new URLSearchParams({
      as_of: supervisionAsOf.value
    });
    const response = await fetch(
      `${API_BASE}${PRODUCT_BASE}` +
        `/collections/supervision/export.csv?${params}`,
      {
        headers: {
          "Accept": "text/csv",
          "X-Tenant-ID": tenantId
        }
      }
    );

    if (!response.ok) {
      let message = "No se pudo exportar el reporte.";

      try {
        const error = await response.json();
        message = error.detail || message;
      } catch {
        // Preserve the default export error.
      }

      throw new Error(message);
    }

    const blob = await response.blob();
    const downloadUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = downloadUrl;
    link.download =
      `prestamodesk-cartera-vencida-` +
      `${supervisionAsOf.value}.csv`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(downloadUrl);
  } finally {
    exportSupervisionButton.disabled = false;
  }
}


async function loadSupervision() {
  clearError();

  const params = new URLSearchParams({
    as_of: supervisionAsOf.value
  });
  const data = await apiRequest(
    `${PRODUCT_BASE}/collections/supervision?${params}`
  );

  renderGeneralSummary(data);
  renderDailyOperations(data);
  renderAgingSummary(data.aging_buckets);
  renderPromiseSummary(data);
  renderCollectorPerformance(data.collectors);
}


supervisionFilterForm.addEventListener(
  "submit",
  async event => {
    event.preventDefault();

    try {
      await loadSupervision();
    } catch (error) {
      showError(error.message);
    }
  }
);


exportSupervisionButton.addEventListener(
  "click",
  async () => {
    try {
      await exportSupervision();
    } catch (error) {
      showError(error.message);
    }
  }
);


refreshSupervisionButton.addEventListener(
  "click",
  async () => {
    try {
      await loadSupervision();
    } catch (error) {
      showError(error.message);
    }
  }
);


loginForm.addEventListener(
  "submit",
  async event => {
    event.preventDefault();
    clearError();

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

      const accessGranted = await discoverAccess();

      if (!accessGranted) {
        return;
      }

      await loadSupervision();
      loginForm.reset();
      setAuthenticatedUI(true);
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
  supervisionAsOf.value = localDateValue();

  if (!tenantId) {
    setAuthenticatedUI(false);
    return;
  }

  try {
    const accessGranted = await discoverAccess();

    if (!accessGranted) {
      return;
    }

    await loadSupervision();
    setAuthenticatedUI(true);
  } catch {
    tenantId = null;
    localStorage.removeItem(TENANT_STORAGE_KEY);
    setAuthenticatedUI(false);
  }
}


initialize();
