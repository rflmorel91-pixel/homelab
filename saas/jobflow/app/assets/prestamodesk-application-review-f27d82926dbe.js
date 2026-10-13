(() => {
  if (window.__prestamodeskApplicationReviewInstalled) return;
  window.__prestamodeskApplicationReviewInstalled = true;
  const base = "/api/v1/products/prestamodesk/applications";
  const escape = value => String(value ?? "").replace(/[&<>"']/g, char => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[char]);

  async function request(path, options = {}) {
    const response = await fetch(`${base}${path}`, {
      headers: {
        "Content-Type": "application/json",
        "X-Tenant-ID": localStorage.getItem("prestamodesk_tenant_id") || "",
        ...(options.headers || {})
      },
      ...options
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      const detail = body.detail;
      throw new Error(typeof detail === "string" ? detail : detail?.gaps
        ? `${detail.message}: ${detail.gaps.join("; ")}`
        : "No se pudo guardar la revisión.");
    }
    return body;
  }

  const localDateTime = value => value ? String(value).slice(0, 16) : "";
  const textField = (label, name, value = "", type = "text", attrs = "") => `
    <label>${label}<input name="${name}" type="${type}" value="${escape(value)}" ${attrs}></label>`;
  const textArea = (label, name, value = "", attrs = "") => `
    <label>${label}<textarea name="${name}" ${attrs}>${escape(value)}</textarea></label>`;
  const selectField = (label, name, values, selected) => `
    <label>${label}<select name="${name}">${values.map(([value, title]) =>
      `<option value="${value}" ${value === selected ? "selected" : ""}>${title}</option>`
    ).join("")}</select></label>`;

  function ensureDialog() {
    if (document.getElementById("applicationReviewDialog")) return;
    document.body.insertAdjacentHTML("beforeend", `
      <dialog class="application-review-dialog" id="applicationReviewDialog" aria-labelledby="applicationReviewTitle">
        <div class="application-review-heading">
          <div><p class="eyebrow">Expediente de crédito</p><h2 id="applicationReviewTitle">Revisión de solicitud</h2></div>
          <button type="button" class="secondary" data-review-close aria-label="Cerrar revisión">Cerrar</button>
        </div>
        <p class="notice">Los documentos deben estar en almacenamiento privado. Registre aquí solo su UUID de referencia; no pegue enlaces públicos ni rutas locales.</p>
        <div class="notice" data-review-message role="status" hidden></div>
        <form id="applicationReviewForm">
          <fieldset data-review-evidence>
            <legend>Inspección del vehículo</legend>
            <div class="form-grid">
              <label>Resultado<select name="inspection_status"><option value="pending">Pendiente</option><option value="passed">Aprobada</option><option value="failed">No aprobada</option></select></label>
              <label>Inspector<input name="inspector_name" maxlength="160"></label>
              <label>Fecha y hora<input name="inspected_at" type="datetime-local"></label>
              <label class="review-wide">Hallazgos<textarea name="inspection_findings" maxlength="4000"></textarea></label>
            </div>
          </fieldset>
          <fieldset data-review-evidence>
            <legend>Documentos de soporte</legend>
            <div class="review-documents" data-review-documents></div>
          </fieldset>
          <fieldset data-review-evidence>
            <legend>Referencia</legend>
            <div class="form-grid">
              <label>Nombre<input name="reference_name" maxlength="160"></label>
              <label>Relación<input name="reference_relationship" maxlength="80"></label>
              <label>Teléfono<input name="reference_phone" maxlength="40"></label>
              <label>Resultado<select name="reference_status"><option value="pending">Pendiente</option><option value="contacted">Contactada</option><option value="unreachable">No localizada</option></select></label>
              <label class="review-wide">Notas de contacto<textarea name="reference_notes" maxlength="2000"></textarea></label>
            </div>
          </fieldset>
          <fieldset data-review-evidence>
            <legend>Evaluación de capacidad de pago</legend>
            <div class="form-grid">
              <label>Fuente de ingresos<input name="income_source" maxlength="160"></label>
              <label>Ingreso neto mensual (DOP)<input name="monthly_net_income" inputmode="decimal" type="number" min="0.01" step="0.01"></label>
              <label>Obligaciones mensuales (DOP)<input name="monthly_obligations" inputmode="decimal" type="number" min="0" step="0.01"></label>
              <label>Recomendación<select name="recommendation"><option value="approve">Recomendar aprobación</option><option value="decline">Recomendar rechazo</option></select></label>
              <label class="review-wide">Resumen y análisis<textarea name="affordability_summary" minlength="10" maxlength="4000"></textarea></label>
            </div>
          </fieldset>
          <fieldset>
            <legend>Formalización del contrato</legend>
            <div class="form-grid">
              <label>Estado<select name="contract_status"><option value="draft">Borrador</option><option value="prepared">Preparado</option><option value="signed">Firmado</option></select></label>
              <label>Versión de plantilla<input name="template_version" maxlength="80"></label>
              <label>Fecha de firma<input name="signed_at" type="datetime-local"></label>
              <label>UUID de copia privada firmada<input name="signed_copy_ref" inputmode="text"></label>
            </div>
          </fieldset>
          <label>Motivo documentado de la decisión<textarea name="decision_reason" maxlength="2000"></textarea></label>
          <div class="application-review-actions">
            <button type="submit" name="review_action" value="save">Guardar expediente</button>
            <button type="submit" name="review_action" value="approve">Aprobar</button>
            <button type="submit" name="review_action" value="reject" class="secondary">Rechazar</button>
          </div>
        </form>
      </dialog>`);
    const dialog = document.getElementById("applicationReviewDialog");
    dialog.addEventListener("click", event => {
      if (event.target === dialog || event.target.closest("[data-review-close]")) dialog.close();
    });
    document.getElementById("applicationReviewForm").addEventListener("submit", saveReview);
  }

  function populateDocumentFields(application, packet) {
    const names = ["identity", "income"];
    if (application.loan_type === "vehicle") names.push("vehicle_registration");
    const docs = new Map((packet.documents || []).map(item => [item.document_type, item]));
    const labels = { identity: "Identidad", income: "Ingresos", vehicle_registration: "Matrícula / propiedad" };
    document.querySelector("[data-review-documents]").innerHTML = names.map(name => {
      const doc = docs.get(name) || {};
      return `<div class="review-document-row"><strong>${labels[name]}</strong>
        ${selectField("Estado", `doc_${name}_status`, [["pending", "Pendiente"], ["received", "Recibido"], ["verified", "Verificado"], ["rejected", "Rechazado"]], doc.status || "pending")}
        ${textField("UUID privado", `doc_${name}_ref`, doc.storage_ref || "", "text", 'inputmode="text"')}
        ${textArea("Notas", `doc_${name}_notes`, doc.notes || "")}</div>`;
    }).join("");
  }

  function populateForm(application) {
    const form = document.getElementById("applicationReviewForm");
    const packet = application.review_packet || {};
    const inspection = packet.inspection || {};
    const reference = (packet.references || [])[0] || {};
    const assessment = packet.assessment || {};
    const contract = packet.contract || {};
    form.elements.inspection_status.value = inspection.status || "pending";
    form.elements.inspector_name.value = inspection.inspector_name || "";
    form.elements.inspected_at.value = localDateTime(inspection.inspected_at);
    form.elements.inspection_findings.value = inspection.findings || "";
    form.elements.reference_name.value = reference.full_name || "";
    form.elements.reference_relationship.value = reference.relationship || "";
    form.elements.reference_phone.value = reference.phone || "";
    form.elements.reference_status.value = reference.status || "pending";
    form.elements.reference_notes.value = reference.outcome_notes || "";
    form.elements.income_source.value = assessment.income_source || "";
    form.elements.monthly_net_income.value = assessment.monthly_net_income || "";
    form.elements.monthly_obligations.value = assessment.monthly_obligations || "";
    form.elements.affordability_summary.value = assessment.affordability_summary || "";
    form.elements.recommendation.value = assessment.recommendation || "approve";
    form.elements.contract_status.value = contract.status || "draft";
    form.elements.template_version.value = contract.template_version || "";
    form.elements.signed_at.value = localDateTime(contract.signed_at);
    form.elements.signed_copy_ref.value = contract.signed_copy_ref || "";
    form.elements.decision_reason.value = application.decision_reason || "";
    const evidenceLocked = application.status === "approved" && Boolean(application.review_packet);
    populateDocumentFields(application, packet);
    for (const fieldset of form.querySelectorAll("[data-review-evidence]")) {
      fieldset.disabled = evidenceLocked;
    }
    form.elements.decision_reason.disabled = application.status === "approved";
    for (const button of form.querySelectorAll('[name="review_action"]')) {
      button.hidden = application.status === "approved" && button.value !== "save";
    }
  }

  async function openReview(applicationId, button) {
    ensureDialog();
    const dialog = document.getElementById("applicationReviewDialog");
    const message = dialog.querySelector("[data-review-message]");
    message.hidden = false;
    message.textContent = "Cargando expediente…";
    dialog.dataset.applicationId = applicationId;
    button.disabled = true;
    try {
      const application = await request(`/${applicationId}`);
      dialog.querySelector("h2").textContent = `Solicitud #${application.id} · ${application.full_name}`;
      populateForm(application);
      message.hidden = true;
      dialog.showModal();
    } catch (error) {
      message.textContent = error.message;
      dialog.showModal();
    } finally {
      button.disabled = false;
    }
  }

  function formPacket(form, application) {
    const fields = new FormData(form);
    const asDate = name => fields.get(name) ? new Date(fields.get(name)).toISOString() : null;
    const documentTypes = ["identity", "income"];
    if (application.loan_type === "vehicle") documentTypes.push("vehicle_registration");
    const documents = documentTypes.map(type => ({
      document_type: type,
      status: fields.get(`doc_${type}_status`) || "pending",
      storage_ref: fields.get(`doc_${type}_ref`) || null,
      checked_at: fields.get(`doc_${type}_status`) === "verified" ? new Date().toISOString() : null,
      notes: fields.get(`doc_${type}_notes`) || null
    }));
    const name = fields.get("reference_name");
    const existingReferences = application.review_packet?.references || [];
    const references = name ? [{
      full_name: name,
      relationship: fields.get("reference_relationship"),
      phone: fields.get("reference_phone"),
      status: fields.get("reference_status"),
      outcome_notes: fields.get("reference_notes") || null
    }, ...existingReferences.slice(1)] : existingReferences;
    const contractStatus = fields.get("contract_status");
    return {
      inspection: {
        status: fields.get("inspection_status"),
        inspector_name: fields.get("inspector_name") || null,
        inspected_at: asDate("inspected_at"),
        findings: fields.get("inspection_findings") || null
      },
      documents,
      references,
      assessment: fields.get("income_source") ? {
        income_source: fields.get("income_source"),
        monthly_net_income: fields.get("monthly_net_income"),
        monthly_obligations: fields.get("monthly_obligations") || "0",
        affordability_summary: fields.get("affordability_summary"),
        recommendation: fields.get("recommendation")
      } : null,
      contract: {
        status: contractStatus,
        template_version: fields.get("template_version") || null,
        signed_at: asDate("signed_at"),
        signed_copy_ref: fields.get("signed_copy_ref") || null
      }
    };
  }

  async function saveReview(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const action = event.submitter?.value || "save";
    const dialog = document.getElementById("applicationReviewDialog");
    const message = dialog.querySelector("[data-review-message]");
    const id = dialog.dataset.applicationId;
    const submitters = [...form.querySelectorAll('[name="review_action"]')];
    submitters.forEach(button => { button.disabled = true; });
    message.hidden = false;
    message.textContent = "Guardando…";
    try {
      const application = await request(`/${id}`);
      const packet = application.status === "approved" && application.review_packet
        ? { ...application.review_packet }
        : formPacket(form, application);
      if (application.status === "approved" && application.review_packet) {
        const fields = new FormData(form);
        const asDate = name => fields.get(name) ? new Date(fields.get(name)).toISOString() : null;
        packet.contract = {
          status: fields.get("contract_status"),
          template_version: fields.get("template_version") || null,
          signed_at: asDate("signed_at"),
          signed_copy_ref: fields.get("signed_copy_ref") || null
        };
      }
      await request(`/${id}/review-packet`, { method: "PUT", body: JSON.stringify(packet) });
      if (action === "approve" || action === "reject") {
        await request(`/${id}`, {
          method: "PUT",
          body: JSON.stringify({
            status: action === "approve" ? "approved" : "rejected",
            decision_reason: form.elements.decision_reason.value
          })
        });
      }
      message.textContent = action === "save" ? "Expediente guardado." : "Decisión guardada.";
      window.setTimeout(() => window.location.reload(), 600);
    } catch (error) {
      message.textContent = error.message;
      submitters.forEach(button => { button.disabled = false; });
    }
  }

  function addReviewButtons() {
    const list = document.getElementById("applicationList");
    if (!list) return;
    for (const card of list.querySelectorAll(".item-card")) {
      const controls = card.querySelector(".item-actions");
      for (const button of controls?.querySelectorAll("[data-application-status]") || []) {
        if (["approved", "rejected"].includes(button.dataset.applicationStatus)) button.hidden = true;
      }
      const action = controls?.querySelector("[data-application-id], [data-convert-application]");
      if (!controls || !action || controls.querySelector("[data-review-application]")) continue;
      const button = document.createElement("button");
      button.type = "button";
      button.className = "secondary";
      button.dataset.reviewApplication = action.dataset.applicationId || action.dataset.convertApplication;
      button.textContent = "Abrir expediente";
      controls.prepend(button);
    }
  }

  document.addEventListener("click", event => {
    const button = event.target.closest("[data-review-application]");
    if (!button) return;
    openReview(button.dataset.reviewApplication, button);
  });
  const list = document.getElementById("applicationList");
  if (list) {
    new MutationObserver(addReviewButtons).observe(list, { childList: true, subtree: true });
    addReviewButtons();
  }
})();
