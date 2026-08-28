const landingParameters =
  new URLSearchParams(window.location.search);

if (
  landingParameters.get("activated") === "1"
) {
  document.getElementById(
    "activationNotice"
  ).style.display = "block";

  window.history.replaceState(
    null,
    "",
    window.location.pathname
  );
}

const leadForm = document.getElementById("leadForm");
const leadSubmit = document.getElementById("leadSubmit");
const leadMessageStatus =
  document.getElementById("leadMessageStatus");

leadForm.addEventListener("submit", async event => {
  event.preventDefault();

  leadSubmit.disabled = true;
  leadMessageStatus.textContent = "Submitting your request...";

  try {
    const response = await fetch(
      "/api/v1/public/products/renewaldesk/leads",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          business_name:
            document.getElementById(
              "leadBusinessName"
            ).value,
          contact_name:
            document.getElementById(
              "leadContactName"
            ).value,
          email:
            document.getElementById(
              "leadEmail"
            ).value,
          phone:
            document.getElementById(
              "leadPhone"
            ).value || null,
          service_type:
            document.getElementById(
              "leadServiceType"
            ).value,
          message:
            document.getElementById(
              "leadMessage"
            ).value || null
        })
      }
    );

    const data = await response.json();

    if (!response.ok) {
      const detail = typeof data.detail === "string"
        ? data.detail
        : "Unable to submit your request.";

      throw new Error(detail);
    }

    leadForm.reset();

    leadMessageStatus.textContent =
      `Thanks! Your RenewalDesk pilot request #${data.lead_id} was received. We will follow up before any payment or account activation.`;

  } catch (error) {
    leadMessageStatus.textContent =
      error.message || "Unable to submit your request.";

  } finally {
    leadSubmit.disabled = false;
  }
});
