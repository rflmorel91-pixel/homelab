  const API_BASE = "/api/v1";

  const tenantId =
    localStorage.getItem("jobflow_tenant_id");

  const operatorStatus =
    document.getElementById("operatorStatus");

  const leadList =
    document.getElementById("leadList");

  const productFilter =
    document.getElementById("productFilter");

  let provisioningOwners = [];
  let operatorLeads = [];


  async function apiRequest(path, options = {}) {
    const headers = {
      ...(options.headers || {})
    };

    if (tenantId) {
      headers["X-Tenant-ID"] = tenantId;
    }

    const response = await fetch(
      `${API_BASE}${path}`,
      {
        ...options,
        credentials: "same-origin",
        headers
      }
    );

    if (!response.ok) {
      let detail = `Request failed (${response.status})`;

      try {
        const data = await response.json();

        if (data.detail) {
          detail = data.detail;
        }
      } catch {
        // Keep default error.
      }

      if (response.status === 401) {
        const returnTo =
          encodeURIComponent("/commercialization");

        window.location.href =
          `/admin?return=${returnTo}`;

        throw new Error(
          "Session expired. Sign in again to continue."
        );
      }

      throw new Error(detail);
    }

    return response.json();
  }


  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }


  function slugify(value) {
    return String(value)
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
  }


  function formatStatus(status) {
    const labels = {
      new: "New",
      contacted: "Contacted",
      qualified: "Qualified",
      quoted: "Quoted",
      won: "Won",
      converted: "Converted",
      closed: "Closed"
    };

    return labels[status] || status;
  }


  function renderLeads(leads) {
    if (leads.length === 0) {
      leadList.innerHTML =
        '<p class="empty">No leads yet.</p>';
      return;
    }

    leadList.innerHTML = leads.map(lead => {
      const submitted =
        new Date(lead.created_at).toLocaleString();

      const saasActions = {
        new: [
          ["contacted", "Mark Contacted"],
          ["closed", "Close Lead"]
        ],
        contacted: [
          ["qualified", "Mark Qualified"],
          ["closed", "Close Lead"]
        ],
        qualified: [
          ["closed", "Close Lead"]
        ],
        converted: [],
        closed: []
      };

      const serviceActions = {
        new: [
          ["contacted", "Mark Contacted"],
          ["closed", "Close Lead"]
        ],
        contacted: [
          ["qualified", "Mark Qualified"],
          ["closed", "Close Lead"]
        ],
        qualified: [
          ["quoted", "Mark Quoted"],
          ["closed", "Close Lead"]
        ],
        quoted: [
          ["won", "Mark Won"],
          ["closed", "Close Lead"]
        ],
        won: [],
        closed: []
      };

      const actions = (
        lead.offering_type === "service"
          ? serviceActions
          : saasActions
      )[lead.status] || [];

      const actionButtons = actions.map(
        ([status, label]) => `
          <button
            data-lead-action="status"
            data-lead-id="${lead.id}"
            data-status="${status}"
          >
            ${label}
          </button>
        `
      ).join("");

      const acceptedOwner =
        provisioningOwners.find(
          owner => owner.lead_id === lead.id
        );

      const provisioning =
        (
          lead.status === "qualified"
          && lead.offering_type !== "service"
        )
          ? `
            <div class="lead-actions">
              <strong>Provision Client</strong>

              ${
                acceptedOwner
                  ? `
                    <div class="lead-detail">
                      <strong>Accepted Owner</strong>

                      <div>
                        ${escapeHtml(
                          acceptedOwner.display_name
                        )}
                        ·
                        ${escapeHtml(
                          acceptedOwner.email
                        )}
                      </div>
                    </div>

                    <div class="lead-detail">
                      <input
                        id="slug-${lead.id}"
                        type="text"
                        value="${escapeHtml(
                          slugify(lead.business_name)
                        )}"
                        placeholder="client-workspace-slug"
                      >
                    </div>

                    <div class="lead-detail">
                      <button
                        data-lead-action="provision"
                        data-lead-id="${lead.id}"
                      >
                        Provision Client
                      </button>
                    </div>
                  `
                  : `
                    <div class="meta lead-detail">
                      Awaiting owner activation. Create and
                      accept the lead invitation before
                      provisioning this client.
                    </div>
                  `
              }
            </div>
          `
          : "";

      const legacyConverted =
        lead.status === "converted"
        && !lead.converted_tenant_id
          ? `
            <div class="lead-actions">
              <strong>
                Legacy conversion requires reconciliation
              </strong>

              <div class="meta">
                This lead was marked converted before tenant
                provisioning was enforced.
              </div>

              <div class="lead-detail">
                <button
                  data-lead-action="reopen"
                  data-lead-id="${lead.id}"
                >
                  Reopen for Provisioning
                </button>
              </div>
            </div>
          `
          : "";

      const converted =
        lead.status === "converted"
        && lead.converted_tenant_id
          ? `
            <div class="lead-actions">
              <strong>
                ${
                  lead.converted_client_number
                    ? `Client #${lead.converted_client_number}`
                    : "Validation Workspace"
                }
              </strong>

              <div>
                ${escapeHtml(lead.business_name)}
              </div>

              <div class="meta">
                ${
                  lead.converted_client_number
                    ? `${escapeHtml(lead.product_name)} client`
                    : `Internal Workspace #${lead.converted_tenant_id}`
                }
              </div>

              ${
                lead.converted_at
                  ? `
                    <div class="meta">
                      Provisioned:
                      ${escapeHtml(
                        new Date(
                          lead.converted_at
                        ).toLocaleString()
                      )}
                    </div>
                  `
                  : ""
              }

              <div class="lead-detail">
                <a
                  href="/admin?tenant=${lead.converted_tenant_id}"
                >
                  ${
                    lead.converted_client_number
                      ? "Manage Client"
                      : "Manage Workspace"
                  }
                </a>
              </div>
            </div>
          `
          : "";

      return `
        <div
          class="card"
          id="lead-${lead.id}"
        >
          <strong>${escapeHtml(lead.business_name)}</strong>

          <div class="meta">
            Product:
            ${escapeHtml(lead.product_name)}
            (${escapeHtml(lead.product_slug)})
          </div>

          <div>
            Contact: ${escapeHtml(lead.contact_name)}
          </div>

          <div>
            Email: ${escapeHtml(lead.email)}
          </div>

          ${
            lead.phone
              ? `<div>Phone: ${escapeHtml(lead.phone)}</div>`
              : ""
          }

          <div>
            Service: ${escapeHtml(lead.service_type)}
          </div>

          ${
            lead.message
              ? `<div>${escapeHtml(lead.message)}</div>`
              : ""
          }

          <div class="meta">
            Submitted: ${escapeHtml(submitted)}
          </div>

          <span class="status">
            ${escapeHtml(formatStatus(lead.status))}
          </span>

          ${
            actionButtons
              ? `<div class="lead-actions">${actionButtons}</div>`
              : ""
          }

          ${provisioning}
          ${legacyConverted}
          ${converted}
        </div>
      `;
    }).join("");
  }


  async function updateLeadStatus(
    leadId,
    newStatus
  ) {
    try {
      await apiRequest(`/leads/${leadId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          status: newStatus
        })
      });

      await loadOperatorLeads();

    } catch (error) {
      operatorStatus.textContent = error.message;
      operatorStatus.className = "error";
    }
  }


  async function reopenLegacyConversion(leadId) {
    if (
      !window.confirm(
        "Reopen this legacy converted lead for proper tenant provisioning?"
      )
    ) {
      return;
    }

    try {
      operatorStatus.textContent =
        "Reopening legacy conversion...";

      await apiRequest(
        `/leads/${leadId}/reopen-conversion`,
        {
          method: "POST"
        }
      );

      operatorStatus.textContent =
        "Lead reopened for provisioning.";

      operatorStatus.className = "";

      await loadOperatorLeads();

    } catch (error) {
      operatorStatus.textContent = error.message;
      operatorStatus.className = "error";
    }
  }


  async function provisionLead(leadId) {
    const acceptedOwner =
      provisioningOwners.find(
        owner => owner.lead_id === leadId
      );

    const slugInput =
      document.getElementById(`slug-${leadId}`);

    if (!acceptedOwner) {
      operatorStatus.textContent =
        "The lead owner must activate their account before provisioning.";

      operatorStatus.className = "error";
      return;
    }

    if (!slugInput) {
      operatorStatus.textContent =
        "Client provisioning is unavailable.";

      operatorStatus.className = "error";
      return;
    }

    const tenantSlug =
      slugInput.value.trim();

    if (!tenantSlug) {
      operatorStatus.textContent =
        "Client workspace slug is required.";

      operatorStatus.className = "error";
      return;
    }

    if (
      !window.confirm(
        "Provision this qualified lead as a client?"
      )
    ) {
      return;
    }

    try {
      operatorStatus.textContent =
        "Provisioning client...";

      await apiRequest(
        `/leads/${leadId}/provision`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            owner_user_id:
              acceptedOwner.user_id,
            tenant_slug: tenantSlug
          })
        }
      );

      operatorStatus.textContent =
        "Client provisioned successfully.";

      operatorStatus.className = "";

      await loadOperatorLeads();

    } catch (error) {
      operatorStatus.textContent = error.message;
      operatorStatus.className = "error";
    }
  }


  async function loadOperatorLeads() {
    try {
      const [
        leads,
        provisioningOptions
      ] = await Promise.all([
        apiRequest("/leads/"),
        apiRequest("/leads/provisioning-options")
      ]);

      provisioningOwners =
        provisioningOptions.owners;

      operatorLeads = leads;

      const products = Array.from(
        new Map(
          leads.map(lead => [
            lead.product_slug,
            lead.product_name
          ])
        ).entries()
      ).sort(
        (a, b) => a[1].localeCompare(b[1])
      );

      productFilter.innerHTML = `
        <option value="">All Products</option>
        ${
          products.map(([slug, name]) => `
            <option value="${escapeHtml(slug)}">
              ${escapeHtml(name)}
            </option>
          `).join("")
        }
      `;

      operatorStatus.textContent =
        "Platform operator access verified.";

      renderLeads(operatorLeads);

    } catch (error) {
      operatorStatus.textContent = error.message;
      operatorStatus.className = "error";

      leadList.innerHTML =
        '<p class="empty">Lead data is unavailable.</p>';
    }
  }


  productFilter.addEventListener(
    "change",
    () => {
      const selected = productFilter.value;

      renderLeads(
        selected
          ? operatorLeads.filter(
              lead => lead.product_slug === selected
            )
          : operatorLeads
      );
    }
  );


  leadList.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-lead-action]");

    if (!button || !leadList.contains(button)) {
      return;
    }

    const leadId = Number(button.dataset.leadId);

    if (!Number.isSafeInteger(leadId) || leadId <= 0) {
      return;
    }

    switch (button.dataset.leadAction) {
      case "status":
        updateLeadStatus(leadId, button.dataset.status);
        break;
      case "provision":
        provisionLead(leadId);
        break;
      case "reopen":
        reopenLegacyConversion(leadId);
        break;
    }
  });


  loadOperatorLeads();
