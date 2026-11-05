(() => {
  const form = document.getElementById("residentForm");
  const message = document.getElementById("pageMessage");
  const button = document.getElementById("sendButton");
  const success = document.getElementById("successPanel");
  const token = location.hash.slice(1);
  const newSecret = () => btoa(String.fromCharCode(...crypto.getRandomValues(new Uint8Array(32)))).replaceAll("+", "-").replaceAll("/", "_").replaceAll("=", "");
  let trackingSecret = newSecret();
  let submissionId = crypto.randomUUID();
  let busy = false;
  const photoInput = document.getElementById("photoFiles");
  const clearPhotos = document.getElementById("clearPhotoFiles");
  photoInput.addEventListener("change", () => { clearPhotos.hidden = !(photoInput.files || []).length; });
  clearPhotos.addEventListener("click", () => { photoInput.value = ""; clearPhotos.hidden = true; });

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
      values.receipt_email = values.receipt_email?.trim() || null;
      const photos = Array.from(document.getElementById("photoFiles").files || []);
      if (photos.length > 3) throw new Error("Please choose no more than 3 photos.");
      values.photos = await Promise.all(photos.map(file => {
        if (!["image/jpeg", "image/png"].includes(file.type) || file.size > 2 * 1024 * 1024) throw new Error("Use JPEG or PNG photos no larger than 2 MB each.");
        return new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => resolve({data: String(reader.result).split(",")[1]});
          reader.onerror = () => reject(new Error("A photo could not be read. Please choose it again."));
          reader.readAsDataURL(file);
        });
      }));
      values.tracking_secret = trackingSecret;
      const result = await post("", {token, submission_id: submissionId, ...values});
      document.getElementById("reference").textContent = result.reference;
      form.hidden = true; message.textContent = ""; success.hidden = false; success.focus();
      const linkPanel = document.getElementById("trackingLinkPanel");
      linkPanel.hidden = !result.tracking_path;
      if (result.tracking_path) document.getElementById("privateTrackingLink").href = result.tracking_path;
      document.getElementById("trackingLinkMessage").textContent = "";
      form.reset(); clearPhotos.hidden = true;
    } catch (error) { message.textContent = error.message; }
    finally { busy = false; button.disabled = false; }
  });
  document.getElementById("anotherButton").addEventListener("click", () => {
    trackingSecret = newSecret(); submissionId = crypto.randomUUID(); success.hidden = true; form.hidden = false;
    form.elements.namedItem("name").focus();
  });
  document.getElementById("copyTrackingLink").addEventListener("click", async () => {
    const link = document.getElementById("privateTrackingLink");
    try { await navigator.clipboard.writeText(link.href); document.getElementById("trackingLinkMessage").textContent = "Private link copied."; }
    catch (_) { document.getElementById("trackingLinkMessage").textContent = "Use the View request progress link above and save its address."; }
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
