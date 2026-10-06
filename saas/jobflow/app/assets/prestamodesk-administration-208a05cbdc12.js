(() => {
  "use strict";
  const panel = document.getElementById("administrationPanel");
  const message = document.getElementById("administrationMessage");
  const base = "/api/v1/products/prestamodesk/administration";
  let client = null;
  let team = null;
  const labels = {owner: "Propietario", administrator: "Administrador", supervisor: "Supervisor", collector: "Cobrador", cashier: "Cajero", member: "Miembro (caja existente)"};
  const permissions = {operations: "Prestatarios, préstamos, solicitudes y configuración", loan_read: "Consultar préstamos", payments: "Consultar caja y registrar pagos", collections: "Cartera completa y gestiones", assignments: "Asignar y liberar carteras", supervision: "Supervisión y exportación", team: "Equipo operativo e invitaciones", privileged_roles: "Propietarios y administradores", assigned_collections: "Solo su cartera asignada", own_cash_closing: "Cierre de su propia caja"};
  const actions = {"client_team.profile_changed": "Perfil actualizado", "client_team.password_reset_requested": "Recuperación solicitada","customer_data.exported": "Datos del cliente exportados","payments.voided": "Pago anulado","client_team.role_changed": "Cambio de rol", "client_team.status_changed": "Cambio de acceso", "client_team.member_removed": "Integrante retirado", "client_user.invitation_created": "Invitación creada", "client_user.invitation_revoked": "Invitación revocada", "client_user.invitation_accepted": "Invitación aceptada", "collections.assignment_created": "Cartera asignada", "collections.assignment_released": "Cartera liberada"};
  const element = (tag, text) => {const node = document.createElement(tag); if (text !== undefined) node.textContent = text; return node;};
  function notify(text, error = false) {message.textContent = text; message.className = "message " + (error ? "error" : "success"); message.hidden = false;}
  async function request(path, method = "GET", body) {
    if (!client) throw new Error("Sesión no disponible.");
    const selectedTenant = client.tenant_id;
    const response = await fetch(base + path, {method, credentials: "same-origin", headers: {"Content-Type": "application/json", "X-Tenant-ID": String(client.tenant_id)}, ...(body === undefined ? {} : {body: JSON.stringify(body)})});
    const data = await response.json();
    if (!client || client.tenant_id !== selectedTenant) throw new Error("El cliente cambió. Abra nuevamente el detalle.");
    if (!response.ok) {
      if ([401, 403].includes(response.status)) {clearMemberDetail(); panel.hidden = true;}
      const translations = {"Release collector assignments before changing or suspending this membership": "Libere las carteras asignadas antes de cambiar el rol o suspender este integrante.", "Client must retain at least one owner": "El cliente debe conservar al menos un propietario.", "You cannot suspend your own membership": "No puede suspender su propio acceso.", "Only the owner may manage owners and administrators": "Solo el propietario puede administrar estos roles."};
      throw new Error(translations[data.detail] || (typeof data.detail === "string" ? data.detail : "Revise los datos e intente nuevamente."));
    }
    return data;
  }
  function roleSelect(roles, current) {
    const select = element("select");
    for (const role of roles) {const option = element("option", labels[role] || role); option.value = role; select.append(option);}
    select.value = current;
    return select;
  }
  function button(text, action) {
    const node = element("button", text); node.type = "button"; node.className = "secondary";
    node.addEventListener("click", async () => {node.disabled = true; try {await action(); await refresh(); if (memberDetail) await loadMemberDetail(memberDetail.membership_id, false); notify("Cambio guardado.");} catch (error) {notify(error.message, true);} finally {node.disabled = false;}});
    return node;
  }
  function renderMembers() {
    const container = document.getElementById("administrationMembers"); container.replaceChildren();
    for (const member of team.members) {
      const row = element("div"); row.className = "panel";
      row.append(element("h4", member.display_name), element("p", member.email + " · " + (member.is_active ? "Activo" : "Suspendido")));
      const detail = element("button", "Ver detalle"); detail.type = "button"; detail.className = "secondary";
      detail.addEventListener("click", async () => {
        if (detailBusy) return;
        clearMemberDetail(); detail.disabled = true;
        try {await loadMemberDetail(member.membership_id);} catch (error) {notify(error.message, true);} finally {detail.disabled = false;}
      });
      row.append(detail);
      const editable = client.role === "owner" || !["owner", "administrator"].includes(member.role);
      if (editable) {
        const select = roleSelect(team.assignable_roles, member.role); select.setAttribute("aria-label", "Rol de " + member.display_name); row.append(select);
        row.append(button("Guardar rol", async () => {
          if (select.value !== member.role && confirm("¿Cambiar el rol de " + member.display_name + "?")) await request("/memberships/" + member.membership_id + "/role", "PUT", {role: select.value});
        }));
        if (member.membership_id !== team.current_membership_id) row.append(button(member.membership_active ? "Suspender acceso" : "Reactivar acceso", async () => {
          if (confirm("¿Cambiar el acceso de " + member.display_name + " a este cliente?")) await request("/memberships/" + member.membership_id + "/status", "PUT", {is_active: !member.membership_active});
        }));
      } else row.append(element("p", labels[member.role]));
      if (!member.account_active) row.append(element("p", "La cuenta está desactivada en la plataforma; reactivar esta membresía no reactiva la cuenta."));
      container.append(row);
    }
  }
  async function refresh() {
    const [newTeam, invitations, audit] = await Promise.all([request("/team"), request("/invitations"), request("/audit")]);
    team = newTeam; renderMembers();
    const inviteRole = document.getElementById("administrationInviteRole"); inviteRole.replaceChildren(...roleSelect(team.assignable_roles, "collector").children);
    const matrix = document.getElementById("administrationPermissions"); matrix.replaceChildren();
    for (const role of team.roles) matrix.append(element("p", role.label + ": " + role.permissions.map(permission => permissions[permission]).join("; ") + "."));
    const list = document.getElementById("administrationInvitations"); list.replaceChildren();
    for (const invitation of invitations.invitations) {
      const row = element("p", invitation.display_name + " · " + invitation.email + " · " + labels[invitation.role] + " · " + invitation.status);
      if (invitation.status === "pending" && (client.role === "owner" || !["owner", "administrator"].includes(invitation.role))) row.append(button("Revocar", async () => {if (confirm("¿Revocar esta invitación?")) await request("/invitations/" + invitation.id + "/revoke", "POST");}));
      list.append(row);
    }
    if (!invitations.invitations.length) list.append(element("p", "Sin invitaciones."));
    const history = document.getElementById("administrationAudit"); history.replaceChildren();
    for (const event of audit) history.append(element("p", new Date(event.created_at + (event.created_at.endsWith("Z") ? "" : "Z")).toLocaleString("es-DO") + " · " + (actions[event.action] || event.action) + " · Usuario #" + event.actor_user_id + " · Registro #" + event.target_id + " · " + JSON.stringify(event.after || event.before || {})));
    if (!audit.length) history.append(element("p", "Sin cambios registrados."));
  }
  let memberDetail = null;
  let detailGeneration = 0;
  let detailBusy = false;
  const detailPanel = document.getElementById("administrationMemberDetail");
  const profileForm = document.getElementById("memberProfileForm");
  function detailNotify(text, error = false) {
    const box = document.getElementById("administrationMemberMessage");
    box.textContent = text; box.className = "message " + (error ? "error" : "success"); box.hidden = false;
  }
  function selectMemberTab(id) {
    for (const tab of document.querySelectorAll("[data-member-tab]")) {
      const active = tab.dataset.memberTab === id;
      tab.setAttribute("aria-selected", String(active)); tab.tabIndex = active ? 0 : -1;
      document.getElementById(tab.dataset.memberTab).hidden = !active;
    }
  }
  function clearMemberDetail() {
    detailGeneration += 1; memberDetail = null; detailPanel.hidden = true; profileForm.reset();
    for (const id of ["memberAccountInfo", "memberAccountActions", "memberPermissions", "memberAssignments", "memberHistory"]) document.getElementById(id).replaceChildren();
    document.getElementById("administrationMemberMessage").hidden = true;
  }
  function setDetailBusy(active) {
    detailBusy = active;
    detailPanel.setAttribute("aria-busy", String(active));
    detailPanel.querySelectorAll("input, select, textarea, button").forEach(control => {control.disabled = active;});
    profileForm.querySelectorAll("input, select, textarea, button").forEach(control => {control.disabled = active || !memberDetail?.editable;});
  }
  function dateLabel(raw) {
    if (!raw) return "Sin fecha";
    const date = new Date(/[zZ]$|[+-]\d{2}:\d{2}$/.test(raw) ? raw : raw + "Z");
    return date.toLocaleString("es-DO");
  }
  function detailAction(text, callback) {
    const node = element("button", text); node.type = "button"; node.className = "secondary";
    node.addEventListener("click", async () => {
      if (detailBusy || !memberDetail) return;
      const selected = memberDetail.membership_id, generation = detailGeneration;
      setDetailBusy(true);
      try {
        const notice = await callback();
        if (generation !== detailGeneration) return;
        await refresh(); await loadMemberDetail(selected, false);
        detailNotify(notice || "Cambio guardado.");
      } catch (error) {if (memberDetail?.membership_id === selected) detailNotify(error.message, true);}
      finally {setDetailBusy(false);}
    });
    return node;
  }
  function renderMemberDetail() {
    const detail = memberDetail;
    document.getElementById("administrationMemberTitle").textContent = "Integrante · " + detail.display_name;
    const account = document.getElementById("memberAccountInfo"); account.replaceChildren();
    for (const text of ["Nombre de cuenta: " + detail.display_name, "Correo de acceso: " + detail.login_email,
      "Rol: " + (labels[detail.role] || detail.role), "Acceso a este cliente: " + (detail.membership_active ? "Activo" : "Suspendido"),
      "Cuenta en la plataforma: " + (detail.account_active ? "Activa" : "Desactivada")]) account.append(element("p", text));
    const controls = document.getElementById("memberAccountActions"); controls.replaceChildren();
    if (detail.editable) {
      const select = roleSelect(detail.assignable_roles, detail.role); select.setAttribute("aria-label", "Rol del integrante"); controls.append(select);
      controls.append(detailAction("Guardar rol", async () => {
        if (select.value === detail.role || !confirm("¿Cambiar el rol de " + detail.display_name + "?")) return "Sin cambios.";
        await request("/memberships/" + detail.membership_id + "/role", "PUT", {role: select.value});
      }));
      if (detail.can_change_status) controls.append(detailAction(detail.membership_active ? "Suspender acceso" : "Reactivar acceso", async () => {
        if (!confirm("¿Cambiar el acceso de este integrante a este cliente?")) return "Sin cambios.";
        await request("/memberships/" + detail.membership_id + "/status", "PUT", {is_active: !detail.membership_active});
      }));
      if (detail.membership_active && detail.account_active) controls.append(detailAction("Solicitar recuperación de contraseña", async () => {
        if (!confirm("¿Solicitar recuperación al correo de acceso " + detail.login_email + "? La contraseña pertenece a toda la cuenta.")) return "Solicitud cancelada.";
        await request("/memberships/" + detail.membership_id + "/password-reset", "POST");
        return "Solicitud procesada. Si corresponde, el usuario recibirá instrucciones en su correo de acceso.";
      }));
    }
    for (const [name, value] of Object.entries(detail.profile)) profileForm.elements.namedItem(name).value = value || "";
    document.getElementById("memberProfileRestriction").hidden = detail.editable;
    const permissionList = document.getElementById("memberPermissions"); permissionList.replaceChildren();
    for (const permission of detail.permissions) permissionList.append(element("p", permissions[permission] || permission));
    const assigned = document.getElementById("memberAssignments"); assigned.replaceChildren();
    for (const assignment of detail.assignments) assigned.append(element("p", "Préstamo #" + assignment.loan_id + " · " + assignment.borrower_name + " · " + (assignment.loan_type === "vehicle" ? "Vehículo" : "Personal") + " · " + assignment.loan_status + " · Asignado " + dateLabel(assignment.assigned_at) + " por usuario #" + assignment.assigned_by_user_id));
    if (!detail.assignments.length) assigned.append(element("p", "Sin préstamos asignados directamente."));
    if (detail.more_assignments) assigned.append(element("p", "Se muestran las 100 asignaciones más recientes. Consulte Asignar carteras para continuar."));
    const history = document.getElementById("memberHistory"); history.replaceChildren();
    for (const event of detail.history) history.append(element("p", dateLabel(event.created_at) + " · " + (actions[event.action] || event.action) + " · Usuario #" + event.actor_user_id + " · " + JSON.stringify(event.after || event.before || {})));
    if (!detail.history.length) history.append(element("p", "Sin cambios registrados para este integrante."));
    if (detail.more_history) history.append(element("p", "Se muestran los 50 eventos más recientes."));
    detailPanel.hidden = false;
    setDetailBusy(detailBusy);
  }
  async function loadMemberDetail(id, resetTab = true) {
    const generation = ++detailGeneration;
    const detail = await request("/memberships/" + id);
    if (generation !== detailGeneration) return;
    memberDetail = detail; renderMemberDetail();
    if (resetTab) {selectMemberTab("memberAccountPanel"); document.getElementById("memberAccountTab").focus();}
  }
  document.getElementById("administrationMemberClose").addEventListener("click", clearMemberDetail);
  document.getElementById("administrationMemberTabs").addEventListener("click", event => {
    const tab = event.target.closest("[data-member-tab]"); if (tab) selectMemberTab(tab.dataset.memberTab);
  });
  document.getElementById("administrationMemberTabs").addEventListener("keydown", event => {
    if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
    const tabs = [...document.querySelectorAll("[data-member-tab]")]; const index = tabs.indexOf(document.activeElement);
    if (index < 0) return;
    event.preventDefault();
    const next = event.key === "Home" ? 0 : event.key === "End" ? tabs.length - 1 : (index + (event.key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length;
    selectMemberTab(tabs[next].dataset.memberTab); tabs[next].focus();
  });
  profileForm.addEventListener("submit", async event => {
    event.preventDefault(); if (detailBusy || !memberDetail?.editable || !profileForm.reportValidity()) return;
    const selected = memberDetail.membership_id, generation = detailGeneration;
    const body = Object.fromEntries(new FormData(profileForm));
    setDetailBusy(true);
    try {
      await request("/memberships/" + selected + "/profile", "PUT", body);
      if (generation !== detailGeneration) return;
      await loadMemberDetail(selected, false); await refresh(); detailNotify("Perfil guardado para este cliente.");
    } catch (error) {if (memberDetail?.membership_id === selected) detailNotify(error.message, true);}
    finally {setDetailBusy(false);}
  });

  const handleAccess = async event => {
    clearMemberDetail();
    client = event.detail; panel.hidden = !["owner", "administrator"].includes(client.role);
    document.getElementById("administrationLink").hidden = panel.hidden;
    if (!panel.hidden) {try {await refresh();} catch (error) {notify(error.message, true);}}
  };
  window.addEventListener("prestamodesk-access", handleAccess);
  if (window.prestamodeskAccess) handleAccess({detail: window.prestamodeskAccess});
  document.getElementById("customerExport").addEventListener("click", async event => {
    if (!client || !confirm("¿Descargar los datos de este cliente? El archivo contiene información personal y financiera.")) return;
    const selected = client.tenant_id; const button = event.currentTarget; button.disabled = true;
    try {
      const response = await fetch(base + "/export.zip", {method: "POST", credentials: "same-origin", headers: {"X-Tenant-ID": String(selected)}});
      if (!response.ok) {
        if ([401, 403].includes(response.status)) panel.hidden = true;
        throw new Error(response.status === 413 ? "El archivo supera el límite. Solicite una exportación asistida." : "No se pudo exportar. Revise su acceso e intente nuevamente.");
      }
      const blob = await response.blob();
      if (!client || client.tenant_id !== selected) return;
      const url = URL.createObjectURL(blob); const link = element("a"); link.href = url;
      link.download = "prestamodesk-cliente-" + selected + ".zip"; document.body.append(link); link.click(); link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 10000);
      notify("Archivo descargado. Guárdelo en un lugar seguro.");
      try {await refresh();} catch (_) {notify("Archivo descargado; actualice el historial para ver el registro de exportación.");}
    } catch (error) {notify(error.message, true);} finally {button.disabled = false;}
  });
  document.getElementById("administrationRefresh").addEventListener("click", async () => {try {await refresh();} catch (error) {notify(error.message, true);}});
  document.getElementById("administrationInvite").addEventListener("submit", async event => {
    event.preventDefault(); const form = event.currentTarget; const submit = form.querySelector("button"); submit.disabled = true;
    try {
      const result = await request("/invitations", "POST", Object.fromEntries(new FormData(form)));
      const activation = document.getElementById("administrationActivation"); activation.replaceChildren(element("span", "Comparta este enlace únicamente con la persona invitada (vence en 72 horas): "));
      const link = element("a", "Activar cuenta"); link.href = result.activation_path; activation.append(link); activation.hidden = false;
      form.reset(); await refresh(); notify("Invitación creada. El correo no se envía automáticamente.");
    } catch (error) {notify(error.message, true);} finally {submit.disabled = false;}
  });
  document.getElementById("logoutButton").addEventListener("click", () => {clearMemberDetail(); panel.hidden = true; document.getElementById("administrationLink").hidden = true; client = null; team = null; window.prestamodeskAccess = null; document.getElementById("administrationActivation").replaceChildren();});
})();
