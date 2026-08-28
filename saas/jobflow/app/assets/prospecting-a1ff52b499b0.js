  const API_BASE =
    "/api/v1/products/workflow-automation/prospecting";

  const statusElement =
    document.getElementById("agentStatus");

  const campaignList =
    document.getElementById("campaignList");

  const candidateList =
    document.getElementById("candidateList");

  const dueFollowUpList =
    document.getElementById("dueFollowUpList");

  const reviewFilter =
    document.getElementById("reviewFilter");

  const manualCampaignSelect =
    document.getElementById("manualCampaignId");


  async function apiRequest(path, options = {}) {
    const response = await fetch(
      `${API_BASE}${path}`,
      {
        ...options,
        credentials: "same-origin",
        headers: {
          ...(options.body
            ? {"Content-Type": "application/json"}
            : {}),
          ...(options.headers || {})
        }
      }
    );

    if (!response.ok) {
      let detail = `Request failed (${response.status})`;

      try {
        const data = await response.json();
        detail = data.detail || detail;
      } catch {
        // Keep the default detail.
      }

      if (response.status === 401) {
        window.location.href =
          "/admin?return=%2Fprospecting";
      }

      throw new Error(detail);
    }

    return response.json();
  }


  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }


  function label(value) {
    return String(value)
      .replaceAll("_", " ")
      .replace(
        /\b\w/g,
        character => character.toUpperCase()
      );
  }


  function setStatus(message, className = "meta") {
    statusElement.textContent = message;
    statusElement.className = className;
  }


  async function loadCampaigns() {
    const campaigns = await apiRequest("/campaigns");

    const selectedCampaignId =
      manualCampaignSelect.value;

    manualCampaignSelect.innerHTML = [
      '<option value="">Select a campaign</option>',
      ...campaigns
        .filter(
          campaign =>
            campaign.segments.includes(
              "small_it_provider"
            )
        )
        .map(
          campaign => `
            <option value="${campaign.id}">
              ${escapeHtml(campaign.name)}
              · ${escapeHtml(label(campaign.status))}
              · score ${campaign.minimum_score}+
            </option>
          `
        )
    ].join("");

    if (
      selectedCampaignId
      && campaigns.some(
        campaign =>
          String(campaign.id)
          === selectedCampaignId
      )
    ) {
      manualCampaignSelect.value =
        selectedCampaignId;
    }

    if (campaigns.length === 0) {
      campaignList.innerHTML =
        '<p class="meta">No campaigns yet.</p>';
      return;
    }

    campaignList.innerHTML = campaigns.map(campaign => `
      <div class="card">
        <div class="card-heading">
          <div>
            <strong>${escapeHtml(campaign.name)}</strong>
            <div class="meta">
              ${escapeHtml(campaign.geography)}
              · ${campaign.max_candidates} maximum
              · score ${campaign.minimum_score}+
            </div>
            <div class="meta">
              Segments:
              ${campaign.segments.map(label).join(", ")}
            </div>
            <div class="meta">
              Model: ${escapeHtml(campaign.model)}
            </div>
          </div>

          <span class="status">
            ${escapeHtml(label(campaign.status))}
          </span>
        </div>

        ${
          campaign.error_message
            ? `<p class="error">${
                escapeHtml(campaign.error_message)
              }</p>`
            : ""
        }

        ${
          campaign.status === "draft"
            ? `
              <div class="actions">
                <button
                  data-prospect-action="run" data-record-id="${campaign.id}"
                >
                  Run Agent
                </button>
              </div>
            `
            : ""
        }
      </div>
    `).join("");
  }


  async function loadCandidates() {
    const query = reviewFilter.value
      ? `?review_status=${
          encodeURIComponent(reviewFilter.value)
        }`
      : "";

    const [
      candidates,
      dueFollowUps,
    ] = await Promise.all([
      apiRequest(`/candidates${query}`),
      apiRequest("/follow-ups/due"),
    ]);

    renderDueFollowUps(dueFollowUps);

    if (candidates.length === 0) {
      candidateList.innerHTML =
        '<p class="meta">No matching candidates.</p>';
      return;
    }

    candidateList.innerHTML = candidates.map(candidate => {
      const evidence = candidate.evidence.map(item => `
        <li>
          ${escapeHtml(item.fact)}
          —
          <a
            href="${escapeHtml(item.url)}"
            target="_blank"
            rel="noopener noreferrer"
          >
            source
          </a>
        </li>
      `).join("");

      const reasons = candidate.score_reasons.map(
        reason => `<li>${escapeHtml(reason)}</li>`
      ).join("");

      return `
        <div
          class="card"
          id="candidate-${candidate.id}"
        >
          <div class="card-heading">
            <div>
              <h3>${escapeHtml(candidate.business_name)}</h3>
              <div class="meta">
                ${escapeHtml(label(candidate.segment))}
                · ${escapeHtml(candidate.location)}
              </div>
            </div>

            <span class="score">
              Fit ${candidate.fit_score}/100
            </span>
          </div>

          <p>
            <a
              href="${escapeHtml(candidate.website_url)}"
              target="_blank"
              rel="noopener noreferrer"

             class="candidate-website">
              ${escapeHtml(candidate.normalized_domain)}
            </a>
          </p>

          <div>
            Email: ${escapeHtml(candidate.email)}
          </div>

          ${
            candidate.phone
              ? `<div>Phone: ${
                  escapeHtml(candidate.phone)
                }</div>`
              : ""
          }

          <strong>Fit reasons</strong>
          <ul>${reasons}</ul>

          <strong>Evidence</strong>
          <ul class="evidence">${evidence}</ul>

          <label for="subject-${candidate.id}">
            Draft subject
          </label>
          <input
            id="subject-${candidate.id}"
            value="${
              escapeHtml(candidate.outreach_subject)
            }"
            ${candidate.review_status !== "pending"
              ? "disabled"
              : ""}
          >

          <label
            for="body-${candidate.id}"

           class="draft-spacing">
            Draft message
          </label>
          <textarea
            id="body-${candidate.id}"
            ${candidate.review_status !== "pending"
              ? "disabled"
              : ""}
          >${escapeHtml(candidate.outreach_body)}</textarea>

          <div class="actions">
            <span class="status">
              ${escapeHtml(label(candidate.review_status))}
            </span>

            ${
              candidate.review_status === "pending"
                ? `
                  <button
                    data-prospect-action="review" data-record-id="${candidate.id}" data-decision="approved"
                  >
                    Approve Draft
                  </button>

                  <button
                    class="button-danger"
                    data-prospect-action="review" data-record-id="${candidate.id}" data-decision="rejected"
                  >
                    Reject Candidate
                  </button>
                `
                : ""
            }
          </div>

          ${renderOutreachControls(candidate)}

          ${
            candidate.lead_id
              ? `
                <div class="meta pipeline-spacing">
                  Workflow Automation Package pipeline lead:
                  #${candidate.lead_id}
                </div>
              `
              : ""
          }
        </div>
      `;
    }).join("");
  }


  function parseActivityDate(value) {
    if (!value) {
      return null;
    }

    const hasTimezone = (
      value.endsWith("Z")
      || /[+-]\d{2}:\d{2}$/.test(value)
    );

    return new Date(
      hasTimezone ? value : `${value}Z`
    );
  }


  function formatActivityDate(value) {
    const date = parseActivityDate(value);

    return date
      ? date.toLocaleString()
      : "";
  }


  function renderDueFollowUps(items) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    const groups = [
      {
        title: "Overdue",
        items: items.filter(
          item =>
            parseActivityDate(item.follow_up_due_at)
            < today
        ),
      },
      {
        title: "Due Today",
        items: items.filter(item => {
          const due = parseActivityDate(
            item.follow_up_due_at
          );

          return due >= today && due < tomorrow;
        }),
      },
      {
        title: "Upcoming",
        items: items.filter(
          item =>
            parseActivityDate(item.follow_up_due_at)
            >= tomorrow
        ),
      },
    ];

    dueFollowUpList.innerHTML = groups.map(group => `
      <div class="card">
        <div class="card-heading">
          <h3>${escapeHtml(group.title)}</h3>
          <span class="status">
            ${group.items.length}
          </span>
        </div>

        ${
          group.items.length
            ? group.items.map(item => `
              <div class="card">
                <strong>
                  ${escapeHtml(item.business_name)}
                </strong>

                <div class="meta">
                  Due:
                  ${escapeHtml(
                    formatActivityDate(
                      item.follow_up_due_at
                    )
                  )}
                </div>

                ${
                  item.contact_name
                    ? `
                      <div class="meta">
                        Contact:
                        ${escapeHtml(item.contact_name)}
                      </div>
                    `
                    : ""
                }

                ${
                  item.email
                    ? `
                      <div class="meta">
                        Email:
                        ${escapeHtml(item.email)}
                      </div>
                    `
                    : ""
                }

                <div class="actions">
                  <a
                    class="button button-light"
                    href="#candidate-${item.candidate_id}"
                    data-prospect-action="show" data-record-id="${item.candidate_id}"
                  >
                    Candidate #${item.candidate_id}
                  </a>

                  <a
                    class="button button-light"
                    href="/commercialization#lead-${item.lead_id}"
                  >
                    Pipeline Lead #${item.lead_id}
                  </a>

                  <button
                    data-prospect-action="follow-up" data-record-id="${item.candidate_id}"
                  >
                    Record Follow-Up
                  </button>
                </div>
              </div>
            `).join("")
            : '<p class="meta">No follow-ups.</p>'
        }
      </div>
    `).join("");
  }


  async function showCandidate(candidateId) {
    reviewFilter.value = "approved";
    await loadCandidates();

    const candidate = document.getElementById(
      `candidate-${candidateId}`
    );

    if (candidate) {
      candidate.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }
  }


  function renderOutreachControls(candidate) {
    const details = [];

    if (candidate.outreach_sent_at) {
      details.push(
        `Sent by ${escapeHtml(
          label(candidate.outreach_channel)
        )} on ${escapeHtml(
          formatActivityDate(
            candidate.outreach_sent_at
          )
        )}`
      );
    } else {
      details.push("Not recorded as sent");
    }

    if (candidate.follow_up_due_at) {
      details.push(
        `Follow-up due: ${escapeHtml(
          formatActivityDate(
            candidate.follow_up_due_at
          )
        )}`
      );
    }

    if (candidate.follow_up_completed_at) {
      details.push(
        `Follow-up completed: ${escapeHtml(
          formatActivityDate(
            candidate.follow_up_completed_at
          )
        )}`
      );
    }

    if (candidate.reply_received_at) {
      details.push(
        `Reply: ${escapeHtml(
          label(candidate.reply_outcome)
        )} on ${escapeHtml(
          formatActivityDate(
            candidate.reply_received_at
          )
        )}`
      );
    }

    if (candidate.suppressed_at) {
      details.push(
        `Do Not Contact: ${escapeHtml(
          candidate.suppression_reason
        )}`
      );
    }

    const buttons = [];

    if (
      candidate.review_status === "approved"
      && !candidate.outreach_sent_at
      && !candidate.suppressed_at
    ) {
      buttons.push(`
        <button
          data-prospect-action="sent" data-record-id="${candidate.id}"
        >
          Mark Sent
        </button>
      `);
    }

    if (
      candidate.outreach_sent_at
      && !candidate.follow_up_completed_at
      && !candidate.reply_received_at
      && !candidate.suppressed_at
    ) {
      buttons.push(`
        <button
          class="button-light"
          data-prospect-action="follow-up" data-record-id="${candidate.id}"
        >
          Record Follow-Up
        </button>
      `);
    }

    if (
      candidate.outreach_sent_at
      && !candidate.reply_received_at
    ) {
      buttons.push(`
        <button
          class="button-light"
          data-prospect-action="reply" data-record-id="${candidate.id}"
        >
          Record Reply
        </button>
      `);
    }

    if (!candidate.suppressed_at) {
      buttons.push(`
        <button
          class="button-danger"
          data-prospect-action="suppress" data-record-id="${candidate.id}"
        >
          Do Not Contact
        </button>
      `);
    }

    return `
      <div

       class="outreach-activity">
        <strong>Outreach activity</strong>

        <ul class="meta">
          ${details.map(
            detail => `<li>${detail}</li>`
          ).join("")}
        </ul>

        ${
          candidate.operator_notes
            ? `
              <div class="meta">
                Notes:
                ${escapeHtml(
                  candidate.operator_notes
                )}
              </div>
            `
            : ""
        }

        <div class="actions">
          ${buttons.join("")}
        </div>
      </div>
    `;
  }


  async function waitForCampaign(campaignId) {
    for (let attempt = 0; attempt < 100; attempt += 1) {
      await new Promise(resolve => {
        window.setTimeout(resolve, 3000);
      });

      const campaigns = await apiRequest(
        "/campaigns"
      );

      const campaign = campaigns.find(
        item => item.id === campaignId
      );

      await loadCampaigns();

      if (!campaign) {
        throw new Error(
          "Queued campaign could not be found."
        );
      }

      if (campaign.status === "completed") {
        return campaign;
      }

      if (campaign.status === "failed") {
        throw new Error(
          campaign.error_message
          || "Prospect discovery failed."
        );
      }

      setStatus(
        `Prospect discovery is ${
          campaign.status
        }...`
      );
    }

    throw new Error(
      "Campaign is still running. Refresh later "
      + "to view its persisted status."
    );
  }


  async function runCampaign(campaignId, button) {
    if (
      !window.confirm(
        "Run public web discovery for this campaign?"
      )
    ) {
      return;
    }

    button.disabled = true;
    setStatus("Queueing prospect discovery...");

    try {
      await apiRequest(
        `/campaigns/${campaignId}/run`,
        {method: "POST"}
      );

      setStatus(
        "Campaign queued. Waiting for results..."
      );

      await loadCampaigns();
      await waitForCampaign(campaignId);
      await loadCandidates();

      setStatus(
        "Campaign completed. Review any saved "
        + "candidates below.",
        "success"
      );
    } catch (error) {
      setStatus(error.message, "error");
      button.disabled = false;
      await loadCampaigns();
    }
  }


  async function reviewCandidate(
    candidateId,
    decision,
    button
  ) {
    const action =
      decision === "approved" ? "approve" : "reject";

    if (
      !window.confirm(
        `Are you sure you want to ${action} this draft?`
      )
    ) {
      return;
    }

    button.disabled = true;

    try {
      const subject = document.getElementById(
        `subject-${candidateId}`
      ).value;

      const body = document.getElementById(
        `body-${candidateId}`
      ).value;

      await apiRequest(
        `/candidates/${candidateId}/review`,
        {
          method: "PUT",
          body: JSON.stringify({
            decision,
            outreach_subject: subject,
            outreach_body: body
          })
        }
      );

      setStatus(
        decision === "approved"
          ? "Draft approved. No message was sent."
          : "Candidate rejected.",
        "success"
      );

      await loadCandidates();
    } catch (error) {
      setStatus(error.message, "error");
      button.disabled = false;
    }
  }


  async function recordOutreachSent(
    candidateId,
    button
  ) {
    const channel = window.prompt(
      "Channel: email, contact_form, phone, or other",
      "email"
    );

    if (channel === null) {
      return;
    }

    const allowedChannels = [
      "email",
      "contact_form",
      "phone",
      "other"
    ];

    if (!allowedChannels.includes(channel)) {
      setStatus("Unsupported outreach channel.", "error");
      return;
    }

    const sentAt = window.prompt(
      "Sent timestamp",
      new Date().toISOString()
    );

    if (sentAt === null) {
      return;
    }

    const followUpDueAt = window.prompt(
      "Follow-up due timestamp, or leave blank",
      ""
    );

    if (followUpDueAt === null) {
      return;
    }

    const notes = window.prompt(
      "Operator notes, or leave blank",
      "Manually sent by operator."
    );

    if (notes === null) {
      return;
    }

    button.disabled = true;

    try {
      await apiRequest(
        `/candidates/${candidateId}/outreach/sent`,
        {
          method: "POST",
          body: JSON.stringify({
            channel,
            sent_at: sentAt,
            follow_up_due_at:
              followUpDueAt || null,
            notes: notes || null
          })
        }
      );

      setStatus(
        "Manual outreach recorded as sent.",
        "success"
      );
      await loadCandidates();
    } catch (error) {
      setStatus(error.message, "error");
      button.disabled = false;
    }
  }


  async function recordFollowUp(
    candidateId,
    button
  ) {
    const completedAt = window.prompt(
      "Follow-up completion timestamp",
      new Date().toISOString()
    );

    if (completedAt === null) {
      return;
    }

    const notes = window.prompt(
      "Operator notes, or leave blank",
      "One manual follow-up completed."
    );

    if (notes === null) {
      return;
    }

    button.disabled = true;

    try {
      await apiRequest(
        `/candidates/${candidateId}/outreach/follow-up`,
        {
          method: "POST",
          body: JSON.stringify({
            completed_at: completedAt,
            notes: notes || null
          })
        }
      );

      setStatus(
        "Follow-up recorded.",
        "success"
      );
      await loadCandidates();
    } catch (error) {
      setStatus(error.message, "error");
      button.disabled = false;
    }
  }


  async function recordReply(
    candidateId,
    button
  ) {
    const outcome = window.prompt(
      "Outcome: interested, not_interested, "
      + "needs_follow_up, unsubscribe, or other",
      "interested"
    );

    if (outcome === null) {
      return;
    }

    const allowedOutcomes = [
      "interested",
      "not_interested",
      "needs_follow_up",
      "unsubscribe",
      "other"
    ];

    if (!allowedOutcomes.includes(outcome)) {
      setStatus("Unsupported reply outcome.", "error");
      return;
    }

    if (
      outcome === "unsubscribe"
      && !window.confirm(
        "This permanently suppresses the candidate. Continue?"
      )
    ) {
      return;
    }

    const receivedAt = window.prompt(
      "Reply timestamp",
      new Date().toISOString()
    );

    if (receivedAt === null) {
      return;
    }

    const notes = window.prompt(
      "Operator notes, or leave blank",
      ""
    );

    if (notes === null) {
      return;
    }

    button.disabled = true;

    try {
      await apiRequest(
        `/candidates/${candidateId}/outreach/reply`,
        {
          method: "POST",
          body: JSON.stringify({
            received_at: receivedAt,
            outcome,
            notes: notes || null
          })
        }
      );

      setStatus(
        outcome === "unsubscribe"
          ? "Reply recorded and candidate suppressed."
          : "Reply recorded.",
        "success"
      );
      await loadCandidates();
    } catch (error) {
      setStatus(error.message, "error");
      button.disabled = false;
    }
  }


  async function recordSuppression(
    candidateId,
    button
  ) {
    const reason = window.prompt(
      "Do Not Contact reason",
      "Unsubscribe or suppression request"
    );

    if (reason === null) {
      return;
    }

    if (!reason.trim()) {
      setStatus(
        "A suppression reason is required.",
        "error"
      );
      return;
    }

    if (
      !window.confirm(
        "Permanently mark this candidate Do Not Contact?"
      )
    ) {
      return;
    }

    button.disabled = true;

    try {
      await apiRequest(
        `/candidates/${candidateId}/outreach/suppression`,
        {
          method: "POST",
          body: JSON.stringify({
            suppressed_at:
              new Date().toISOString(),
            reason,
            notes: "Recorded by operator."
          })
        }
      );

      setStatus(
        "Candidate marked Do Not Contact.",
        "success"
      );
      await loadCandidates();
    } catch (error) {
      setStatus(error.message, "error");
      button.disabled = false;
    }
  }


  document.getElementById(
    "campaignForm"
  ).addEventListener("submit", async event => {
    event.preventDefault();

    const segments = [];

    if (document.getElementById("segmentIt").checked) {
      segments.push("small_it_provider");
    }

    if (segments.length === 0) {
      setStatus(
        "Select at least one target segment.",
        "error"
      );
      return;
    }

    const button =
      document.getElementById("createButton");

    button.disabled = true;

    try {
      await apiRequest("/campaigns", {
        method: "POST",
        body: JSON.stringify({
          name: document.getElementById(
            "campaignName"
          ).value,
          geography: document.getElementById(
            "geography"
          ).value,
          segments,
          max_candidates: Number(
            document.getElementById(
              "maxCandidates"
            ).value
          ),
          minimum_score: Number(
            document.getElementById(
              "minimumScore"
            ).value
          )
        })
      });

      setStatus(
        "Campaign created. Review it below, then run the agent.",
        "success"
      );

      await loadCampaigns();
    } catch (error) {
      setStatus(error.message, "error");
    } finally {
      button.disabled = false;
    }
  });


  document.getElementById(
    "manualCandidateForm"
  ).addEventListener("submit", async event => {
    event.preventDefault();

    const button = document.getElementById(
      "saveManualCandidateButton"
    );

    const scoreReasons = document.getElementById(
      "manualScoreReasons"
    ).value
      .split("\n")
      .map(reason => reason.trim())
      .filter(Boolean);

    if (scoreReasons.length === 0) {
      setStatus(
        "Enter at least one fit reason.",
        "error"
      );
      return;
    }

    button.disabled = true;
    button.textContent = "Adding...";

    try {
      await apiRequest("/candidates", {
        method: "POST",
        body: JSON.stringify({
          campaign_id: Number(
            manualCampaignSelect.value
          ),
          business_name: document.getElementById(
            "manualBusinessName"
          ).value.trim(),
          website_url: document.getElementById(
            "manualWebsiteUrl"
          ).value.trim(),
          segment: "small_it_provider",
          location: document.getElementById(
            "manualLocation"
          ).value.trim(),
          contact_name:
            document.getElementById(
              "manualContactName"
            ).value.trim() || null,
          email: document.getElementById(
            "manualEmail"
          ).value.trim().toLowerCase(),
          phone:
            document.getElementById(
              "manualPhone"
            ).value.trim() || null,
          evidence: [
            {
              url: document.getElementById(
                "manualEvidenceUrl"
              ).value.trim(),
              fact: document.getElementById(
                "manualEvidenceFact"
              ).value.trim()
            }
          ],
          fit_score: Number(
            document.getElementById(
              "manualFitScore"
            ).value
          ),
          score_reasons: scoreReasons,
          disqualifiers: [],
          outreach_subject:
            document.getElementById(
              "manualOutreachSubject"
            ).value.trim(),
          outreach_body:
            document.getElementById(
              "manualOutreachBody"
            ).value.trim()
        })
      });

      setStatus(
        "Candidate added for review. "
        + "No message was sent.",
        "success"
      );

      event.target.reset();
      document.getElementById(
        "manualFitScore"
      ).value = "85";

      reviewFilter.value = "pending";
      await loadCandidates();
    } catch (error) {
      setStatus(error.message, "error");
    } finally {
      button.disabled = false;
      button.textContent = "Add to Review Queue";
    }
  });


  reviewFilter.addEventListener(
    "change",
    () => {
      loadCandidates().catch(error => {
        setStatus(error.message, "error");
      });
    }
  );


  async function initialize() {
    try {
      await Promise.all([
        loadCampaigns(),
        loadCandidates()
      ]);

      setStatus(
        "Operator access confirmed. No outreach is sent automatically."
      );
    } catch (error) {
      setStatus(error.message, "error");
    }
  }

  function bindProspectActions(container) {
    container.addEventListener("click", async (event) => {
      const control = event.target.closest("[data-prospect-action]");

      if (!control || !container.contains(control) || control.disabled) {
        return;
      }

      if (control.dataset.prospectAction === "show") {
        event.preventDefault();
      }

      const recordId = Number(control.dataset.recordId);
      if (!Number.isSafeInteger(recordId) || recordId <= 0) {
        return;
      }

      try {
        switch (control.dataset.prospectAction) {
          case "run":
            await runCampaign(recordId, control);
            break;
          case "review":
            if (!["approved", "rejected"].includes(control.dataset.decision)) {
              return;
            }
            await reviewCandidate(recordId, control.dataset.decision, control);
            break;
          case "show":
            await showCandidate(recordId);
            break;
          case "follow-up":
            await recordFollowUp(recordId, control);
            break;
          case "sent":
            await recordOutreachSent(recordId, control);
            break;
          case "reply":
            await recordReply(recordId, control);
            break;
          case "suppress":
            await recordSuppression(recordId, control);
            break;
        }
      } catch (error) {
        setStatus(error.message, "error");
      }
    });
  }

  bindProspectActions(campaignList);
  bindProspectActions(candidateList);
  bindProspectActions(dueFollowUpList);

  initialize();
