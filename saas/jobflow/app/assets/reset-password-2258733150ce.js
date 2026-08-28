"use strict";

const API_BASE = "/api/v1";
const hash = new URLSearchParams(
  window.location.hash.slice(1)
);
const resetToken = hash.get("token") || "";

window.history.replaceState(
  null,
  "",
  window.location.pathname
);

const form =
  document.getElementById("resetForm");

const statusElement =
  document.getElementById("resetStatus");

const resetButton =
  document.getElementById("resetButton");

const continueLink =
  document.getElementById("continueLink");


function showStatus(message, type) {
  statusElement.textContent = message;
  statusElement.className =
    `status visible ${type}`;
}


if (!resetToken) {
  form.classList.add("hidden");

  showStatus(
    "This reset link is missing or invalid. Request a new link.",
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

    resetButton.disabled = true;
    resetButton.textContent = "Resetting...";

    try {
      const response = await fetch(
        `${API_BASE}/auth/password-reset/confirm`,
        {
          method: "POST",
          credentials: "same-origin",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            token: resetToken,
            password,
          }),
        }
      );

      if (!response.ok) {
        let detail =
          `Password reset failed (${response.status})`;

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
        `${payload.product.workspace_route}?password_reset=1`;

      continueLink.href = workspaceUrl;

      continueLink.textContent =
        `Continue to Sign In`;

      continueLink.classList.add("visible");

      showStatus(
        `Password updated. Redirecting to ${payload.product.name} sign in...`,
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

      resetButton.disabled = false;
      resetButton.textContent = "Reset Password";
    }
  }
);
