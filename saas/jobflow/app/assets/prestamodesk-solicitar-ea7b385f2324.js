const pageStatus = document.getElementById("pageStatus");
const requestPanel = document.getElementById("requestPanel");
const businessIntroduction = document.getElementById(
  "businessIntroduction"
);
const prospectForm = document.getElementById("prospectForm");
const submitButton = document.getElementById("submitButton");
const errorMessage = document.getElementById("errorMessage");
const successMessage = document.getElementById("successMessage");

const pathParts = window.location.pathname
  .split("/")
  .filter(Boolean);

const tenantSlug =
  pathParts[0] === "prestamodesk" &&
  pathParts[1] === "solicitar" &&
  pathParts[2]
    ? pathParts[2]
    : null;

const publicBase =
  "/api/v1/products/prestamodesk/public/tenants";

function readableError(body, fallback) {
  if (typeof body.detail === "string") {
    return body.detail;
  }

  if (Array.isArray(body.detail)) {
    return body.detail
      .map(item => item.msg || "Dato inválido")
      .join(". ");
  }

  return fallback;
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
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  let body = {};

  try {
    body = await response.json();
  } catch {
    // Use the status-based fallback below.
  }

  if (!response.ok) {
    throw new Error(
      readableError(
        body,
        `La solicitud falló (${response.status}).`
      )
    );
  }

  return body;
}

async function initializePage() {
  if (!tenantSlug) {
    pageStatus.textContent =
      "Esta página de solicitud no está disponible.";
    return;
  }

  try {
    const tenant = await requestJson(
      `${publicBase}/${encodeURIComponent(tenantSlug)}`
    );

    document.title =
      `Solicitar información | ${tenant.business_name}`;

    businessIntroduction.textContent =
      `${tenant.business_name} revisará su información ` +
      "y podrá comunicarse con usted para explicar los próximos pasos.";

    pageStatus.textContent =
      `Cliente PréstamoDesk #${tenant.client_number}`;

    requestPanel.hidden = false;
  } catch (error) {
    pageStatus.textContent = error.message;
  }
}

prospectForm.addEventListener("submit", async event => {
  event.preventDefault();

  if (!tenantSlug) {
    return;
  }

  submitButton.disabled = true;
  submitButton.textContent = "Enviando…";
  errorMessage.hidden = true;
  successMessage.hidden = true;

  try {
    const result = await requestJson(
      (
        `${publicBase}/${encodeURIComponent(tenantSlug)}` +
        "/prospects"
      ),
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          full_name:
            document.getElementById("fullName").value,
          phone:
            document.getElementById("phone").value,
          email:
            document.getElementById("email").value || null,
          municipality:
            document.getElementById("municipality").value || null,
          province:
            document.getElementById("province").value || null,
          requested_amount:
            document.getElementById("requestedAmount").value,
          preferred_contact:
            document.getElementById("preferredContact").value,
          message:
            document.getElementById("message").value || null,
          consent_to_contact:
            document.getElementById("contactConsent").checked
        })
      }
    );

    prospectForm.reset();

    showSuccess(
      `Solicitud #${result.prospect_id} recibida. ` +
      "El prestamista podrá comunicarse con usted."
    );
  } catch (error) {
    showError(error.message);
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = "Enviar solicitud";
  }
});

initializePage();
