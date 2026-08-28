const requestForm = document.getElementById("requestForm");
const submitButton = document.getElementById("submitButton");
const errorMessage = document.getElementById("errorMessage");
const successMessage = document.getElementById("successMessage");

const pathParts = window.location.pathname
  .split("/")
  .filter(Boolean);

const tenantSlug =
  pathParts[0] === "request" && pathParts[1]
    ? pathParts[1]
    : null;

function showError(message) {
  errorMessage.textContent = message;
  errorMessage.style.display = "block";
  successMessage.style.display = "none";
}

function showSuccess(message) {
  successMessage.textContent = message;
  successMessage.style.display = "block";
  errorMessage.style.display = "none";
}

if (!tenantSlug) {
  requestForm.style.display = "none";
  showError("This request page is not available.");
}

requestForm.addEventListener("submit", async event => {
  event.preventDefault();

  if (!tenantSlug) {
    return;
  }

  submitButton.disabled = true;
  submitButton.textContent = "Submitting...";

  try {
    const response = await fetch(
      `/api/v1/public/tenants/${encodeURIComponent(tenantSlug)}/requests`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          name: document.getElementById("customerName").value,
          phone:
            document.getElementById("customerPhone").value || null,
          email:
            document.getElementById("customerEmail").value || null,
          address:
            document.getElementById("customerAddress").value || null,
          project_title:
            document.getElementById("projectTitle").value,
          project_description:
            document.getElementById("projectDescription").value || null
        })
      }
    );

    let body = {};

    try {
      body = await response.json();
    } catch {
      // Keep fallback error handling below.
    }

    if (!response.ok) {
      throw new Error(
        body.detail || `Request failed (${response.status})`
      );
    }

    requestForm.reset();

    showSuccess(
      `Request #${body.request_id} received. ` +
      "The service provider can now review your project."
    );

  } catch (error) {
    showError(error.message);

  } finally {
    submitButton.disabled = false;
    submitButton.textContent = "Submit Request";
  }
});
