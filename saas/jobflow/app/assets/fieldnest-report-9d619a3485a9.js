(() => {
  const form = document.getElementById("residentForm");
  const message = document.getElementById("pageMessage");
  const button = document.getElementById("sendButton");
  const success = document.getElementById("successPanel");
  const token = location.hash.slice(1);
  let submissionId = crypto.randomUUID();
  let busy = false;
  async function post(suffix, payload) {
    const response = await fetch("/api/v1/products/fieldnest/public/maintenance" + suffix, {
      method: "POST", credentials: "omit", cache: "no-store",
      headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload)
    });
    let data = {};
    try { data = await response.json(); } catch (_) {}
    if (!response.ok) {
      if (response.status === 429) throw new Error("Too many requests. Please wait a few minutes and try again.");
      throw new Error(typeof data.detail === "string" ? data.detail : "We couldn’t send your report. Check your details and try again.");
    }
    return data;
  }
  form.addEventListener("submit", async event => {
    event.preventDefault();
    if (busy) return;
    busy = true; button.disabled = true; message.textContent = "Sending your report…";
    try {
      const values = Object.fromEntries(new FormData(form).entries());
      const result = await post("", {token, submission_id: submissionId, ...values});
      document.getElementById("reference").textContent = result.reference;
      form.hidden = true; message.textContent = ""; success.hidden = false; success.focus();
      form.reset();
    } catch (error) { message.textContent = error.message; }
    finally { busy = false; button.disabled = false; }
  });
  document.getElementById("anotherButton").addEventListener("click", () => {
    submissionId = crypto.randomUUID(); success.hidden = true; form.hidden = false;
    form.elements.namedItem("name").focus();
  });
  (async () => {
    if (!/^[A-Za-z0-9_-]{43}$/.test(token)) {
      document.getElementById("propertyName").textContent = "";
      message.textContent = "Ask your property manager for your property’s maintenance request link.";
      return;
    }
    try {
      const context = await post("/context", {token});
      document.getElementById("propertyName").textContent = context.property_name;
      form.hidden = false;
    } catch (error) {
      document.getElementById("propertyName").textContent = "";
      message.textContent = error.message;
    }
  })();
})();
