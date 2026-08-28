const form =
  document.getElementById("quoteForm");

const formStatus =
  document.getElementById("formStatus");

form.addEventListener(
  "submit",
  async event => {
    event.preventDefault();

    const submitButton =
      form.querySelector('button[type="submit"]');

    const values =
      Object.fromEntries(new FormData(form));

    const payload = {
      business_name:
        values.business_name.trim(),
      contact_name:
        values.contact_name.trim(),
      email:
        values.email.trim(),
      phone:
        values.phone.trim() || null,
      service_type:
        values.service_type.trim(),
      message:
        values.message.trim()
    };

    formStatus.textContent =
      "Submitting your request...";
    formStatus.className = "full";
    submitButton.disabled = true;

    try {
      const response = await fetch(
        "/api/v1/public/products/"
        + "workflow-automation/leads",
        {
          method: "POST",
          credentials: "same-origin",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify(payload)
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail
            || `Request failed (${response.status})`
        );
      }

      form.reset();

      formStatus.textContent =
        `Thanks! Assessment request #${data.lead_id} `
        + "was received. FieldLookers will review "
        + "the workflow before proposing a quote.";

      formStatus.className =
        "full success";

    } catch (error) {
      formStatus.textContent =
        error.message
        || "The request could not be submitted.";

      formStatus.className =
        "full error";

    } finally {
      submitButton.disabled = false;
    }
  }
);
