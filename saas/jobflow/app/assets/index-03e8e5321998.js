const leadForm = document.getElementById("leadForm");
const leadMessageStatus =
  document.getElementById("leadMessageStatus");

leadForm.addEventListener("submit", async event => {
  event.preventDefault();

  leadMessageStatus.textContent = "Submitting...";

  try {
    const response = await fetch("/api/v1/public/products/jobflow/leads", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        business_name:
          document.getElementById("leadBusinessName").value,
        contact_name:
          document.getElementById("leadContactName").value,
        email:
          document.getElementById("leadEmail").value,
        phone:
          document.getElementById("leadPhone").value || null,
        service_type:
          document.getElementById("leadServiceType").value,
        message:
          document.getElementById("leadMessage").value || null
      })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail || "Unable to submit your request."
      );
    }

    leadForm.reset();

    leadMessageStatus.textContent =
      `Thanks! Your pilot request #${data.lead_id} was received.`;

  } catch (error) {
    leadMessageStatus.textContent =
      error.message || "Unable to submit your request.";
  }
});
