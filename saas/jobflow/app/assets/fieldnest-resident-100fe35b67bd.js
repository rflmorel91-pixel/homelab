(() => {
  const $ = id => document.getElementById(id);
  const token = location.hash.slice(1);
  const api = "/api/v1/products/fieldnest/public/resident";
  const urls = [];
  const clearPhotos = () => { urls.splice(0).forEach(URL.revokeObjectURL); $("trackingPhotos").replaceChildren(); };
  async function post(path) {
    const response = await fetch(api + path, {method: "POST", credentials: "omit", cache: "no-store",
      headers: {"Content-Type": "application/json"}, body: JSON.stringify({token})});
    if (!response.ok) {
      if (response.status === 429) throw new Error("Please wait a moment before refreshing again.");
      let data = {}; try { data = await response.json(); } catch (_) {}
      throw new Error(typeof data.detail === "string" ? data.detail : "Unable to load your request. Please try again.");
    }
    return response;
  }
  let busy = false;
  async function refresh() {
    if (busy) return;
    busy = true; $("refreshTracking").disabled = true;
    $("trackingMessage").textContent = "Checking progress…";
    try {
      if (!/^[A-Za-z0-9_-]{43}$/.test(token)) throw new Error("Open the private tracking link saved after your report, or ask your property manager for a replacement.");
      const data = await (await post("/context")).json();
      $("trackingTitle").textContent = data.title;
      $("trackingReference").textContent = data.reference + (data.unit ? " · Unit " + data.unit : "");
      const labels = {open: "Received", scheduled: "Scheduled", in_progress: "In progress", waiting: "Waiting for follow-up", completed: "Completed", cancelled: "Cancelled"};
      $("trackingStatus").textContent = labels[data.status] || "Contact your property manager";
      $("trackingCreated").textContent = new Date(data.received_at).toLocaleString();
      $("trackingUpdated").textContent = new Date(data.updated_at).toLocaleString();
      $("trackingExplanation").textContent = data.status === "completed" ? "The property team has marked this request completed. Contact them if the issue continues." : "This shows the latest status recorded by your property team. Contact your manager for visit times or urgent changes.";
      $("trackingContent").hidden = false; $("trackingMessage").textContent = "";
      clearPhotos(); $("photoMessage").textContent = "";
      $("trackingPhotosSection").hidden = !data.photos.length;
      for (const photo of data.photos) {
        try {
          const blob = await (await post("/photos/" + encodeURIComponent(photo.id))).blob();
          const url = URL.createObjectURL(blob); urls.push(url);
          const image = document.createElement("img"); image.src = url;
          image.alt = "Photo supplied with this maintenance report";
          $("trackingPhotos").append(image);
        } catch (_) { $("photoMessage").textContent = "A photo could not be loaded. Try refreshing progress."; }
      }
    } catch (error) {
      $("trackingContent").hidden = true; clearPhotos();
      $("trackingMessage").textContent = error.message;
    } finally { busy = false; $("refreshTracking").disabled = false; }
  }
  $("refreshTracking").addEventListener("click", refresh);
  window.addEventListener("pagehide", clearPhotos);
  refresh();
})();
