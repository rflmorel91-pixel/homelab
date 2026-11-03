(() => {
  const form = document.getElementById("leadForm");
  if (!form) return;
  const submit = document.getElementById("leadSubmit");
  const status = document.getElementById("leadMessageStatus");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (submit.disabled) return;
    const values = Object.fromEntries(new FormData(form).entries());
    const payload = {
      business_name: values.business_name,
      contact_name: values.contact_name,
      email: values.email,
      phone: values.phone || null,
      service_type: `FieldNest demo request · ${values.service_type}`,
      message: values.message || null
    };
    submit.disabled = true;
    status.classList.remove("success");
    status.textContent = "Sending your request…";
    try {
      const response = await fetch("/api/v1/public/products/fieldnest/leads", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await response.json();
      if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Unable to send your request. Please try again.");
      form.reset();
      status.classList.add("success");
      status.textContent = "Thanks — your demo request was received. We’ll follow up about FieldNest.";
    } catch (error) {
      status.textContent = error.message || "Unable to send your request. Please try again.";
    } finally {
      submit.disabled = false;
    }
  });
})();
