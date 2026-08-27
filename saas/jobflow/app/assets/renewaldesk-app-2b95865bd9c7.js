const API_BASE = "/api/v1";
  const PRODUCT_BASE =
    "/products/renewaldesk";

  let clientRole = null;

  let tenantId =
    localStorage.getItem(
      "renewaldesk_tenant_id"
    );

  const loginForm =
    document.getElementById("loginForm");

  const loginEmail =
    document.getElementById("loginEmail");

  const loginPassword =
    document.getElementById("loginPassword");

  const forgotPasswordButton =
    document.getElementById(
      "forgotPasswordButton"
    );

  const passwordResetRequestForm =
    document.getElementById(
      "passwordResetRequestForm"
    );

  const passwordResetEmail =
    document.getElementById(
      "passwordResetEmail"
    );

  const backToSignInButton =
    document.getElementById(
      "backToSignInButton"
    );

  const passwordResetRequestButton =
    document.getElementById(
      "passwordResetRequestButton"
    );

  const logoutButton =
    document.getElementById("logoutButton");

  const workspace =
    document.getElementById("workspace");

  const authPanel =
    document.getElementById("authPanel");

  const healthStatus =
    document.getElementById("healthStatus");

  const clientContext =
    document.getElementById("clientContext");

  const teamPanel =
    document.getElementById("teamPanel");

  const teamInvitationForm =
    document.getElementById(
      "teamInvitationForm"
    );

  const teamDisplayName =
    document.getElementById("teamDisplayName");

  const teamEmail =
    document.getElementById("teamEmail");

  const teamRole =
    document.getElementById("teamRole");

  const teamMemberList =
    document.getElementById("teamMemberList");

  const teamInvitationList =
    document.getElementById(
      "teamInvitationList"
    );

  const teamActivationPanel =
    document.getElementById(
      "teamActivationPanel"
    );

  const teamActivationLink =
    document.getElementById(
      "teamActivationLink"
    );

  const copyTeamActivationLink =
    document.getElementById(
      "copyTeamActivationLink"
    );

  const errorMessage =
    document.getElementById("errorMessage");

  const successMessage =
    document.getElementById("successMessage");

  const renewalForm =
    document.getElementById("renewalForm");

  const renewalEditId =
    document.getElementById("renewalEditId");

  const renewalSubmitButton =
    document.getElementById(
      "renewalSubmitButton"
    );

  const cancelEditButton =
    document.getElementById(
      "cancelEditButton"
    );

  const renewalList =
    document.getElementById("renewalList");

  const renewalSearch =
    document.getElementById(
      "renewalSearch"
    );

  const renewalStatusFilter =
    document.getElementById(
      "renewalStatusFilter"
    );

  const renewalUrgencyFilter =
    document.getElementById(
      "renewalUrgencyFilter"
    );

  const renewalResultCount =
    document.getElementById(
      "renewalResultCount"
    );

  const expiredCount =
    document.getElementById("expiredCount");

  const dueSoonCount =
    document.getElementById("dueSoonCount");

  const upcomingCount =
    document.getElementById("upcomingCount");

  const inactiveCount =
    document.getElementById("inactiveCount");


  function setAuthenticatedUI(
    isAuthenticated
  ) {
    authPanel.style.display =
      isAuthenticated ? "none" : "block";

    workspace.style.display =
      isAuthenticated ? "block" : "none";

    logoutButton.style.display =
      isAuthenticated ? "block" : "none";

    clientContext.style.display =
      (
        isAuthenticated
        && clientContext.textContent
      )
        ? "inline-block"
        : "none";
  }


  function showError(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = "block";
    successMessage.style.display = "none";
  }


  function showSuccess(message) {
    successMessage.textContent = message;
    successMessage.style.display = "block";
    errorMessage.style.display = "none";

    setTimeout(() => {
      successMessage.style.display = "none";
    }, 3000);
  }


  async function apiRequest(
    path,
    options = {}
  ) {
    const response = await fetch(
      `${API_BASE}${path}`,
      {
        headers: {
          "Content-Type": "application/json",
          ...(tenantId
            ? {
                "X-Tenant-ID": tenantId
              }
            : {}),
          ...(options.headers || {})
        },
        ...options
      }
    );

    if (!response.ok) {
      let detail =
        `Request failed (${response.status})`;

      try {
        const body = await response.json();

        if (body.detail) {
          detail = body.detail;
        }
      } catch {
        // Keep default message.
      }

      throw new Error(detail);
    }

    if (response.status === 204) {
      return null;
    }

    return response.json();
  }


  async function checkHealth() {
    try {
      const data =
        await apiRequest("/health");

      healthStatus.textContent =
        `API: ${data.status}`;

      healthStatus.style.color =
        "#166534";
    } catch {
      healthStatus.textContent =
        "API unavailable";

      healthStatus.style.color =
        "#991b1b";
    }
  }


  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }


  function formatState(state) {
    const labels = {
      expired: "Expired",
      due_soon: "Due Soon",
      upcoming: "Upcoming",
      inactive: "Inactive"
    };

    return labels[state] || state;
  }


  function formatDays(days) {
    if (days < 0) {
      return `${Math.abs(days)} day(s) overdue`;
    }

    if (days === 0) {
      return "Due today";
    }

    return `${days} day(s) remaining`;
  }


  function renderRenewals(items) {
    if (items.length === 0) {
      renewalList.innerHTML =
        '<p class="empty">No matching renewals.</p>';

      return;
    }

    renewalList.innerHTML =
      '<div class="renewal-list">' +
      items.map(item => `
        <article class="renewal-card">
          <h3>${escapeHtml(item.name)}</h3>

          <span class="badge">
            ${escapeHtml(
              formatState(item.renewal_state)
            )}
          </span>

          <div class="renewal-meta">
            <span>
              ${escapeHtml(item.category)}
            </span>

            <span>
              Renewal:
              ${escapeHtml(item.renewal_date)}
            </span>

            <span>
              ${escapeHtml(
                formatDays(
                  item.days_until_renewal
                )
              )}
            </span>

            ${
              item.owner_name
                ? `<span>Owner:
                    ${escapeHtml(
                      item.owner_name
                    )}
                   </span>`
                : ""
            }

            ${
              item.owner_email
                ? `<span>Email:
                    ${escapeHtml(
                      item.owner_email
                    )}
                   </span>`
                : ""
            }
          </div>

          ${
            item.notes
              ? `<p>${escapeHtml(item.notes)}</p>`
              : ""
          }

          <div class="actions">
            <button
              type="button"
              class="secondary"
              data-edit-renewal="${item.id}"
            >
              Edit
            </button>

            ${
              clientRole === "owner"
                ? `
                  <button
                    type="button"
                    class="danger"
                    data-delete-renewal="${item.id}"
                  >
                    Delete
                  </button>
                `
                : ""
            }
          </div>
        </article>
      `).join("") +
      "</div>";
  }


  let dashboardItems = [];


  function applyRenewalFilters() {
    const query =
      renewalSearch.value
        .trim()
        .toLowerCase();

    const status =
      renewalStatusFilter.value;

    const urgency =
      renewalUrgencyFilter.value;

    const filteredItems =
      dashboardItems.filter(item => {
        const searchableText = [
          item.name,
          item.category,
          item.owner_name,
          item.owner_email,
          item.notes
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();

        const matchesSearch =
          !query ||
          searchableText.includes(query);

        const matchesStatus =
          !status ||
          item.status === status;

        const matchesUrgency =
          !urgency ||
          item.renewal_state === urgency;

        return (
          matchesSearch &&
          matchesStatus &&
          matchesUrgency
        );
      });

    renewalResultCount.textContent =
      `${filteredItems.length} of ` +
      `${dashboardItems.length} renewal(s)`;

    document.querySelectorAll(
      ".summary-card[data-urgency]"
    ).forEach(card => {
      card.classList.toggle(
        "active",
        Boolean(urgency) &&
        card.dataset.urgency === urgency
      );
    });

    renderRenewals(filteredItems);
  }


  renewalSearch.addEventListener(
    "input",
    applyRenewalFilters
  );

  renewalStatusFilter.addEventListener(
    "change",
    applyRenewalFilters
  );

  renewalUrgencyFilter.addEventListener(
    "change",
    applyRenewalFilters
  );


  document.querySelectorAll(
    ".summary-card[data-urgency]"
  ).forEach(card => {
    card.addEventListener(
      "click",
      () => {
        const urgency =
          card.dataset.urgency;

        renewalUrgencyFilter.value =
          renewalUrgencyFilter.value === urgency
            ? ""
            : urgency;

        applyRenewalFilters();
      }
    );
  });


  async function loadDashboard() {
    const data = await apiRequest(
      `${PRODUCT_BASE}/dashboard`
    );

    dashboardItems = data.items;

    expiredCount.textContent =
      data.expired;

    dueSoonCount.textContent =
      data.due_soon;

    upcomingCount.textContent =
      data.upcoming;

    inactiveCount.textContent =
      data.inactive;

    applyRenewalFilters();
  }


  function resetRenewalForm() {
    renewalForm.reset();
    renewalEditId.value = "";

    document.getElementById(
      "reminderDays"
    ).value = "30";

    document.getElementById(
      "renewalCategory"
    ).value = "other";

    document.getElementById(
      "renewalStatus"
    ).value = "active";

    renewalSubmitButton.textContent =
      "Add Renewal";

    cancelEditButton.style.display =
      "none";
  }


  function beginEditRenewal(itemId) {
    const item = dashboardItems.find(
      candidate => candidate.id === itemId
    );

    if (!item) {
      showError("Renewal item not found.");
      return;
    }

    renewalEditId.value =
      String(item.id);

    document.getElementById(
      "renewalName"
    ).value = item.name;

    document.getElementById(
      "renewalCategory"
    ).value = item.category;

    document.getElementById(
      "renewalDate"
    ).value = item.renewal_date;

    document.getElementById(
      "renewalStatus"
    ).value = item.status;

    document.getElementById(
      "renewalOwner"
    ).value = item.owner_name || "";

    document.getElementById(
      "renewalOwnerEmail"
    ).value = item.owner_email || "";

    document.getElementById(
      "reminderDays"
    ).value = String(
      item.reminder_days
    );

    document.getElementById(
      "renewalNotes"
    ).value = item.notes || "";

    renewalSubmitButton.textContent =
      "Save Renewal";

    cancelEditButton.style.display =
      "block";

    renewalForm.scrollIntoView({
      behavior: "smooth",
      block: "start"
    });
  }


  cancelEditButton.addEventListener(
    "click",
    resetRenewalForm
  );


  async function deleteRenewal(itemId) {
    if (!confirm(
      "Delete this renewal?"
    )) {
      return;
    }

    try {
      await apiRequest(
        `${PRODUCT_BASE}/items/${itemId}`,
        {
          method: "DELETE"
        }
      );

      await loadDashboard();
      showSuccess("Renewal deleted.");
    } catch (error) {
      showError(error.message);
    }
  }


  function renderTeamMembers(
    members,
    currentMembershipId
  ) {
    teamMemberList.innerHTML = members.length
      ? members.map(member => `
          <article class="renewal-card">
            <h3>
              ${escapeHtml(member.display_name)}
            </h3>

            <div class="renewal-meta">
              <span>${escapeHtml(member.email)}</span>
              <span>
                ${member.is_active ? "Active" : "Inactive"}
              </span>

              <span>
                ${escapeHtml(member.role)}
                ${
                  member.membership_id
                    === currentMembershipId
                    ? " · You"
                    : ""
                }
              </span>
            </div>

            <div
              ${
                member.membership_id
                  === currentMembershipId
                  ? "hidden"
                  : ""
              }
              class="actions rd-static-4"

            >
              <label>
                Role

                <select
                  id="team-role-${member.membership_id}"
                >
                  <option
                    value="member"
                    ${
                      member.role === "member"
                        ? "selected"
                        : ""
                    }
                  >
                    Member
                  </option>

                  <option
                    value="owner"
                    ${
                      member.role === "owner"
                        ? "selected"
                        : ""
                    }
                  >
                    Owner
                  </option>
                </select>
              </label>

              <button
                type="button"
                class="secondary"
                data-save-team-role="${member.membership_id}"
              >
                Save Role
              </button>

              <button
                type="button"
                class="danger"
                data-remove-team-member="${member.membership_id}"
              >
                Remove
              </button>
            </div>
          </article>
        `).join("")
      : '<p class="empty">No team members.</p>';
  }


  async function saveTeamMemberRole(
    membershipId
  ) {
    const role = document.getElementById(
      `team-role-${membershipId}`
    ).value;

    try {
      await apiRequest(
        `/client/team/memberships/${membershipId}`,
        {
          method: "PUT",
          body: JSON.stringify({
            role
          })
        }
      );

      showSuccess("Team member role updated.");

      location.reload();

    } catch (error) {
      showError(error.message);
      await loadClientTeam();
    }
  }


  async function removeTeamMember(
    membershipId
  ) {
    if (
      !window.confirm(
        "Remove this person from the client workspace?"
      )
    ) {
      return;
    }

    try {
      await apiRequest(
        `/client/team/memberships/${membershipId}`,
        {
          method: "DELETE"
        }
      );

      showSuccess("Team member removed.");

      location.reload();

    } catch (error) {
      showError(error.message);
      await loadClientTeam();
    }
  }


  function renderTeamInvitations(invitations) {
    teamInvitationList.innerHTML = invitations.length
      ? invitations.map(invitation => `
          <article class="renewal-card">
            <h3>
              ${escapeHtml(invitation.display_name)}
            </h3>

            <div class="renewal-meta">
              <span>${escapeHtml(invitation.email)}</span>
              <span>${escapeHtml(invitation.role)}</span>
              <span>${escapeHtml(invitation.status)}</span>
            </div>

            ${
              invitation.status === "pending"
                ? `
                  <button
                    type="button"
                    class="danger"
                    data-revoke-team-invitation="${invitation.id}"
                  >
                    Revoke
                  </button>
                `
                : ""
            }
          </article>
        `).join("")
      : '<p class="empty">No client invitations.</p>';
  }


  async function loadClientTeam() {
    if (clientRole !== "owner") {
      teamPanel.style.display = "none";
      return;
    }

    const [
      team,
      invitationData
    ] = await Promise.all([
      apiRequest("/client/team"),
      apiRequest("/client/user-invitations")
    ]);

    renderTeamMembers(
      team.members,
      team.current_membership_id
    );
    renderTeamInvitations(
      invitationData.invitations
    );

    teamPanel.style.display = "block";
  }


  async function revokeTeamInvitation(
    invitationId
  ) {
    if (
      !window.confirm(
        "Revoke this pending client invitation?"
      )
    ) {
      return;
    }

    try {
      await apiRequest(
        `/client/user-invitations/${
          invitationId
        }/revoke`,
        {
          method: "POST"
        }
      );

      showSuccess(
        "Client invitation revoked."
      );

      await loadClientTeam();

    } catch (error) {
      showError(error.message);
    }
  }


  async function discoverRenewalDeskAccess() {
    const access = await apiRequest(
      "/auth/products/renewaldesk/access"
    );

    if (access.clients.length === 0) {
      throw new Error(
        "Your account does not have active RenewalDesk client access."
      );
    }

    if (access.clients.length > 1) {
      throw new Error(
        "Your account has access to multiple RenewalDesk clients. Client selection is required."
      );
    }

    const client =
      access.clients[0];

    tenantId =
      String(client.tenant_id);

    localStorage.setItem(
      "renewaldesk_tenant_id",
      tenantId
    );

    clientRole =
      client.role;

    clientContext.textContent =
      `Client #${client.client_number} · ${client.name} · ${client.role}`;

    await loadClientTeam();

    return client;
  }


  forgotPasswordButton.addEventListener(
    "click",
    () => {
      passwordResetEmail.value =
        loginEmail.value;

      loginForm.hidden = true;
      passwordResetRequestForm.hidden = false;
      passwordResetEmail.focus();
    }
  );


  backToSignInButton.addEventListener(
    "click",
    () => {
      passwordResetRequestForm.hidden = true;
      loginForm.hidden = false;
      loginEmail.focus();
    }
  );


  passwordResetRequestForm.addEventListener(
    "submit",
    async event => {
      event.preventDefault();

      passwordResetRequestButton.disabled = true;
      passwordResetRequestButton.textContent =
        "Sending...";

      try {
        const result = await apiRequest(
          "/auth/password-reset/request",
          {
            method: "POST",
            body: JSON.stringify({
              email: passwordResetEmail.value,
              product_slug: "renewaldesk"
            })
          }
        );

        passwordResetRequestForm.reset();
        passwordResetRequestForm.hidden = true;
        loginForm.hidden = false;

        passwordResetRequestButton.disabled = false;
        passwordResetRequestButton.textContent =
          "Send Reset Link";

        showSuccess(result.message);
        loginEmail.focus();

      } catch (error) {
        passwordResetRequestButton.disabled = false;
        passwordResetRequestButton.textContent =
          "Send Reset Link";

        showError(error.message);
      }
    }
  );


  loginForm.addEventListener(
    "submit",
    async event => {
      event.preventDefault();

      try {
        await apiRequest(
          "/auth/login",
          {
            method: "POST",
            body: JSON.stringify({
              email: loginEmail.value,
              password: loginPassword.value
            })
          }
        );

        await discoverRenewalDeskAccess();
        await loadDashboard();

        loginForm.reset();
        setAuthenticatedUI(true);

        showSuccess("Signed in.");

      } catch (error) {
        showError(error.message);
      }
    }
  );


  logoutButton.addEventListener(
    "click",
    async () => {
      try {
        await apiRequest(
          "/auth/logout",
          {
            method: "POST"
          }
        );
      } catch {
        // Continue local sign-out.
      }

      tenantId = null;
      clientRole = null;
      clientContext.textContent = "";

      localStorage.removeItem(
        "renewaldesk_tenant_id"
      );

      location.reload();
    }
  );


  renewalForm.addEventListener(
    "submit",
    async event => {
      event.preventDefault();

      const editId =
        renewalEditId.value.trim();

      const payload = {
        name:
          document.getElementById(
            "renewalName"
          ).value,

        category:
          document.getElementById(
            "renewalCategory"
          ).value,

        renewal_date:
          document.getElementById(
            "renewalDate"
          ).value,

        status:
          document.getElementById(
            "renewalStatus"
          ).value,

        owner_name:
          document.getElementById(
            "renewalOwner"
          ).value || null,

        owner_email:
          document.getElementById(
            "renewalOwnerEmail"
          ).value || null,

        reminder_days:
          Number(
            document.getElementById(
              "reminderDays"
            ).value
          ),

        notes:
          document.getElementById(
            "renewalNotes"
          ).value || null
      };

      try {
        if (editId) {
          await apiRequest(
            `${PRODUCT_BASE}/items/${editId}`,
            {
              method: "PUT",
              body: JSON.stringify(payload)
            }
          );
        } else {
          await apiRequest(
            `${PRODUCT_BASE}/items`,
            {
              method: "POST",
              body: JSON.stringify(payload)
            }
          );
        }

        const message = editId
          ? "Renewal updated."
          : "Renewal added.";

        resetRenewalForm();
        await loadDashboard();

        showSuccess(message);

      } catch (error) {
        showError(error.message);
      }
    }
  );


  async function initialize() {
    await checkHealth();

    if (!tenantId) {
      setAuthenticatedUI(false);
      return;
    }

    try {
      await discoverRenewalDeskAccess();
      await loadDashboard();
      setAuthenticatedUI(true);
    } catch {
      tenantId = null;
      clientRole = null;

      localStorage.removeItem(
        "renewaldesk_tenant_id"
      );

      setAuthenticatedUI(false);
    }
  }


  teamInvitationForm.addEventListener(
    "submit",
    async event => {
      event.preventDefault();

      try {
        teamActivationPanel.style.display =
          "none";

        const invitation = await apiRequest(
          "/client/user-invitations",
          {
            method: "POST",
            body: JSON.stringify({
              display_name:
                teamDisplayName.value.trim(),
              email:
                teamEmail.value.trim(),
              role:
                teamRole.value
            })
          }
        );

        teamActivationLink.value =
          `${window.location.origin}${
            invitation.activation_path
          }`;

        teamActivationPanel.style.display =
          "block";

        teamInvitationForm.reset();

        showSuccess(
          "Client invitation created."
        );

        await loadClientTeam();

      } catch (error) {
        showError(error.message);
      }
    }
  );


  copyTeamActivationLink.addEventListener(
    "click",
    async () => {
      await navigator.clipboard.writeText(
        teamActivationLink.value
      );

      showSuccess(
        "Activation link copied."
      );
    }
  );



  renewalList.addEventListener("click", event => {
    const button = event.target.closest("button[data-edit-renewal]");
    if (!button || !renewalList.contains(button) || button.disabled) return;
    const id = Number(button.getAttribute("data-edit-renewal"));
    if (!Number.isSafeInteger(id) || id <= 0) return;
    beginEditRenewal(id);
  });

  renewalList.addEventListener("click", event => {
    const button = event.target.closest("button[data-delete-renewal]");
    if (!button || !renewalList.contains(button) || button.disabled) return;
    const id = Number(button.getAttribute("data-delete-renewal"));
    if (!Number.isSafeInteger(id) || id <= 0) return;
    deleteRenewal(id);
  });

  teamMemberList.addEventListener("click", event => {
    const button = event.target.closest("button[data-save-team-role]");
    if (!button || !teamMemberList.contains(button) || button.disabled) return;
    const id = Number(button.getAttribute("data-save-team-role"));
    if (!Number.isSafeInteger(id) || id <= 0) return;
    saveTeamMemberRole(id);
  });

  teamMemberList.addEventListener("click", event => {
    const button = event.target.closest("button[data-remove-team-member]");
    if (!button || !teamMemberList.contains(button) || button.disabled) return;
    const id = Number(button.getAttribute("data-remove-team-member"));
    if (!Number.isSafeInteger(id) || id <= 0) return;
    removeTeamMember(id);
  });

  teamInvitationList.addEventListener("click", event => {
    const button = event.target.closest("button[data-revoke-team-invitation]");
    if (!button || !teamInvitationList.contains(button) || button.disabled) return;
    const id = Number(button.getAttribute("data-revoke-team-invitation"));
    if (!Number.isSafeInteger(id) || id <= 0) return;
    revokeTeamInvitation(id);
  });

  initialize();
