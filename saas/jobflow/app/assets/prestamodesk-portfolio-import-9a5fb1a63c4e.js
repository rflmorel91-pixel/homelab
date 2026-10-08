(() => {
  "use strict";
  const $ = id => document.getElementById(id);
  let client = null, reviewed = null, report = null, busy = false, generation = 0;
  const base = "/api/v1/products/prestamodesk/administration/imports";
  function note(text) { $("importMessage").textContent = text; $("importMessage").hidden = false; }
  function reset() {
    generation++; reviewed = null; report = null;
    $("importPreview").hidden = true; $("importSave").disabled = true;
    $("importConfirm").checked = false; $("importDownloadReport").hidden = true;
    $("importRows").replaceChildren(); $("importErrors").replaceChildren();
    $("importTotals").textContent = ""; $("importMessage").hidden = true;
  }
  function controls(active) {
    busy = active;
    for (const id of ["importFile", "importCutoff", "importPreviewButton", "importTemplate", "importConfirm", "importReportId"])
      $(id).disabled = active;
    $("importSave").disabled = active || !reviewed?.valid || !$("importConfirm").checked;
  }
  async function request(path, options = {}, selected = client) {
    if (!selected) throw new Error("Inicie sesión como propietario o administrador.");
    const response = await fetch(base + path, {credentials: "same-origin", ...options,
      headers: {"Content-Type": "application/json", "X-Tenant-ID": String(selected.tenant_id), ...(options.headers || {})}});
    if (!response.ok) {
      const data = await response.json();
      throw new Error(typeof data.detail === "string" ? data.detail : "La cartera cambió o contiene errores. Genere otra vista previa.");
    }
    return response;
  }
  function download(blob, name) {
    const url = URL.createObjectURL(blob), link = document.createElement("a");
    link.href = url; link.download = name; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  function render(data) {
    $("importRows").replaceChildren(); $("importErrors").replaceChildren();
    for (const loan of data.loans) {
      const row = document.createElement("tr");
      for (const value of [loan.reference, loan.borrower, loan.borrower_action, loan.total_due, loan.historical_paid, loan.opening_balance]) {
        const cell = document.createElement("td"); cell.textContent = value; row.append(cell);
      }
      $("importRows").append(row);
    }
    for (const error of data.errors) {
      const item = document.createElement("li"); item.textContent = `Fila ${error.row}: ${error.message}`; $("importErrors").append(item);
    }
    $("importTotals").textContent = `${data.loan_count} préstamos · ${data.installment_count} cuotas · Corte ${data.cutoff_date} · Saldo inicial RD$${data.opening_balance} · Abonos históricos RD$${data.historical_paid}`;
    $("importPreview").hidden = false;
  }
  window.addEventListener("prestamodesk-access", event => {reset(); client = ["owner", "administrator"].includes(event.detail.role) ? event.detail : null;});
  if (window.prestamodeskAccess) client = window.prestamodeskAccess;
  $("logoutButton").addEventListener("click", () => {client = null; reset(); $("portfolioImportForm").reset();});
  for (const id of ["importFile", "importCutoff"]) $(id).addEventListener("change", reset);
  $("importTemplate").addEventListener("click", async () => {
    if (busy) return; controls(true); const current = generation;
    try {const response = await request("/template"); const blob = await response.blob(); if (current === generation) download(blob, "prestamodesk-import-template.csv");}
    catch (error) {if (current === generation) note(error.message);} finally {controls(false);}
  });
  $("portfolioImportForm").addEventListener("submit", async event => {
    event.preventDefault(); if (busy) return; reset(); controls(true); const current = generation;
    try {
      const file = $("importFile").files[0]; if (!file || file.size > 1_000_000) throw new Error("Seleccione un CSV de máximo 1 MB.");
      const payload = {csv_text: await file.text(), cutoff_date: $("importCutoff").value};
      if (current !== generation) return;
      const response = await request("/preview", {method: "POST", body: JSON.stringify(payload)});
      const data = await response.json(); if (current !== generation) return;
      reviewed = {...data, payload}; render(data); note(data.valid ? "Revise los saldos y confirme antes de guardar." : "Corrija los errores del archivo y vuelva a validar.");
    } catch (error) {if (current === generation) note(error.message);} finally {controls(false);}
  });
  $("importConfirm").addEventListener("change", () => controls(busy));
  $("importSave").addEventListener("click", async () => {
    if (busy || !reviewed?.valid || !$("importConfirm").checked) return;
    controls(true); const current = generation;
    try {
      const payload = {...reviewed.payload, fingerprint: reviewed.fingerprint, confirm_balances: true};
      const response = await request("", {method: "POST", body: JSON.stringify(payload)});
      const data = await response.json(); if (current !== generation) return;
      report = data; reviewed = null; $("importDownloadReport").hidden = false;
      note(`Importación #${data.import_id} ${data.replayed ? "ya confirmada" : "guardada"}. Saldo inicial RD$${data.opening_balance}. No se generaron cobros de Caja. Descargue el informe.`);
    } catch (error) {
      if (current === generation) note(error.message + " Si la conexión falló, reintente con esta misma vista previa: la solicitud evita duplicados.");
    } finally {controls(false);}
  });
  $("importDownloadReport").addEventListener("click", () => {
    if (report) download(new Blob([JSON.stringify(report, null, 2)], {type: "application/json"}), `prestamodesk-import-${report.import_id}.json`);
  });
  $("importReportForm").addEventListener("submit", async event => {
    event.preventDefault(); if (busy) return; controls(true); const current = generation;
    try {
      const response = await request("/" + encodeURIComponent($("importReportId").value));
      const data = await response.json(); if (current !== generation) return;
      report = data; $("importDownloadReport").hidden = false; note(`Informe de importación #${data.import_id} disponible para descargar.`);
    } catch (error) {if (current === generation) note(error.message);} finally {controls(false);}
  });
})();
