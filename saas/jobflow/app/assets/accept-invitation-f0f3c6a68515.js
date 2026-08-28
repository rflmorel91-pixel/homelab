"use strict";

const API_BASE = "/api/v1";
const hash = new URLSearchParams(
  window.location.hash.slice(1)
);
const invitationToken = hash.get("token") || "";

window.history.replaceState(
  null,
  "",
  window.location.pathname
);

const form =
  document.getElementById("activationForm");

const statusElement =
  document.getElementById("activationStatus");

const activateButton =
  document.getElementById("activateButton");

const continueLink =
  document.getElementById("continueLink");


function showStatus(message, type) {
  statusElement.textContent = message;
  statusElement.className =
    `status visible ${type}`;
}


if (!invitationToken) {
  form.classList.add("hidden");

  showStatus(
    "This invitation link is missing or invalid. Request a new invitation.",
    "error"
  );
}


form.addEventListener(
  "submit",
  async event => {
    event.preventDefault();

    const password =
      document.getElementById("password").value;

    const confirmation =
      document.getElementById(
        "passwordConfirmation"
      ).value;

    if (password !== confirmation) {
      showStatus(
        "Passwords do not match.",
        "error"
      );
      return;
    }

    activateButton.disabled = true;
    activateButton.textContent = "Activating...";

    try {
      const response = await fetch(
        `${API_BASE}/auth/invitations/accept`,
        {
          method: "POST",
          credentials: "same-origin",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            token: invitationToken,
            password,
          }),
        }
      );

      if (!response.ok) {
        let detail =
          `Activation failed (${response.status})`;

        try {
          const payload = await response.json();

          if (payload.detail) {
            detail = payload.detail;
          }
        } catch {
          // Keep fallback error.
        }

        throw new Error(detail);
      }

      const payload =
        await response.json();

      form.reset();
      form.classList.add("hidden");

      const workspaceUrl =
        `${payload.product.workspace_route}?activated=1`;

      continueLink.href = workspaceUrl;

      continueLink.textContent =
        `Continue to ${payload.product.name} Sign In`;

      continueLink.classList.add("visible");

      showStatus(
        `Your account is active. Redirecting to ${payload.product.name} sign in...`,
        "success"
      );

      window.setTimeout(
        () => window.location.assign(workspaceUrl),
        1200
      );

    } catch (error) {
      showStatus(
        error.message,
        "error"
      );

      activateButton.disabled = false;
      activateButton.textContent = "Activate Account";
    }
  }
);
