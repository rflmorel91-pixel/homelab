const form = document.getElementById("pilotForm");
const formStatus = document.getElementById("formStatus");

form.addEventListener("submit", async event => {
  event.preventDefault();

  const submitButton = form.querySelector('button[type="submit"]');
  const values = Object.fromEntries(new FormData(form));
  const details = [
    `Assets to track: ${values.assets.trim()}`,
    `System or workflow: ${values.workflow.trim()}`,
    `Problem to solve: ${values.problem.trim()}`,
    values.start_date
      ? `Preferred start date: ${values.start_date}`
      : "Preferred start date: Not specified"
  ];

  const payload = {
    business_name: values.business_name.trim(),
    contact_name: values.contact_name.trim(),
    email: values.email.trim(),
    phone: null,
    service_type: `AssetTrack pilot — ${values.business_type.trim()}`,
    message: details.join("\n\n")
  };

  formStatus.textContent = "Submitting your application...";
  formStatus.className = "full";
  submitButton.disabled = true;

  try {
    const response = await fetch(
      "/api/v1/public/products/assettrack/leads",
      {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      }
    );
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || `Request failed (${response.status})`);
    }

    form.reset();
    formStatus.textContent =
      `Thanks! Pilot application #${data.lead_id} was received. `
      + "FieldLookers will review the workflow before requesting payment.";
    formStatus.className = "full success";
  } catch (error) {
    formStatus.textContent = error.message || "The application could not be submitted.";
    formStatus.className = "full error";
  } finally {
    submitButton.disabled = false;
  }
});
