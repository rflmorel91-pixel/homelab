(() => {
  "use strict";
  const panel = document.getElementById("administrationPanel");
  const message = document.getElementById("administrationMessage");
  const base = "/api/v1/products/prestamodesk/administration";
  let client = null;
  let team = null;
  let activationRecord = null;
  let invitationViewActive = true;
  const activation = document.getElementById("administrationActivation");
  const invitationLeaveMessage = "Copie o guarde el enlace de invitación antes de salir de Administración.";
  function clearActivation() {activationRecord = null; activation.replaceChildren(); activation.hidden = true;}
  function invitationCanLeave() {return !activationRecord || activationRecord.saved && !activationRecord.copying;}
  function confirmInvitationLeave() {
    if (invitationCanLeave()) return true;
    if (activationRecord.copying) return false;
    return window.confirm("El enlace de invitación aún no se ha copiado o guardado. Si sale, no podrá recuperarlo desde la lista; tendrá que revocar y crear otra invitación. ¿Desea salir y perder el enlace?");
  }
  window.prestamodeskInvitationSharing = {canLeave: invitationCanLeave, confirmLeave: confirmInvitationLeave, leaveMessage: invitationLeaveMessage};
  window.addEventListener("beforeunload", event => {if (!invitationCanLeave()) {event.preventDefault(); event.returnValue = "";}});
  window.addEventListener("pd-dispose", () => {invitationViewActive = false; clearActivation();});
  function showActivation(result) {
    const url = new URL(result.activation_path, document.baseURI);
    if (url.origin !== new URL(document.baseURI).origin || url.pathname !== "/accept-invitation" || !url.hash.startsWith("#token=")) throw new Error("No se recibió un enlace de activación válido.");
    const record = {id: result.id, tenantId: client.tenant_id, url: url.href, saved: false, copying: false};
    activationRecord = record;
    const title = element("h3", "Invitación creada: guarde el enlace"), recipient = element("p", "Para: " + result.email);
    const notice = element("p", "El correo no se envía automáticamente. Comparta este enlace privado únicamente con la persona invitada. Al salir de esta sección, el enlace dejará de estar disponible.");
    const expiry = element("p", result.expires_at ? "Vence: " + new Date(result.expires_at.endsWith("Z") ? result.expires_at : result.expires_at + "Z").toLocaleString("es-DO", {timeZone: "America/Santo_Domingo"}) + " (República Dominicana)." : "El enlace vence en 72 horas.");
    const label = element("label", "Enlace privado de activación"), field = element("input"); field.type = "text"; field.readOnly = true; field.value = record.url; label.append(field);
    const copy = element("button", "Copiar enlace"); copy.type = "button";
    const saved = element("button", "Ya guardé o compartí el enlace"); saved.type = "button"; saved.className = "secondary";
    const link = element("a", "Activar cuenta"); link.href = record.url; link.target = "_blank"; link.rel = "noopener noreferrer";
    const status = element("p", "Pendiente de copiar o guardar."); status.setAttribute("role", "status"); status.setAttribute("aria-live", "polite");
    copy.addEventListener("click", async () => {
      if (activationRecord !== record || record.copying) return;
      record.copying = true; copy.disabled = true; saved.disabled = true;
      try {
        if (!navigator.clipboard?.writeText) throw new Error("Clipboard unavailable");
        await navigator.clipboard.writeText(record.url);
        if (!invitationViewActive || activationRecord !== record || client?.tenant_id !== record.tenantId) return;
        record.saved = true; status.textContent = "Enlace copiado. Compártalo únicamente con " + result.email + ".";
      } catch {
        if (!invitationViewActive || activationRecord !== record) return;
        record.saved = false; status.textContent = "No se pudo copiar automáticamente. Seleccione el enlace, cópielo manualmente y pulse «Ya guardé o compartí el enlace».";
        field.focus(); field.select();
      } finally {record.copying = false; copy.disabled = false; saved.disabled = false;}
    });
    saved.addEventListener("click", () => {if (activationRecord === record && !record.copying) {record.saved = true; status.textContent = "Enlace guardado o compartido. Puede salir de esta sección.";}});
    activation.replaceChildren(title, recipient, notice, expiry, label, copy, saved, link, status); activation.hidden = false;
    activation.scrollIntoView({behavior: "smooth", block: "center"}); copy.focus();
  }
  const labels = {owner: "Propietario", administrator: "Administrador", supervisor: "Supervisor", collector: "Cobrador", cashier: "Cajero", member: "Miembro (caja existente)"};
  const permissions = {operations: "Prestatarios, préstamos, solicitudes y configuración", loan_read: "Consultar préstamos", payments: "Consultar caja y registrar pagos", collections: "Cartera completa y gestiones", assignments: "Asignar y liberar carteras", supervision: "Supervisión y exportación", team: "Equipo operativo e invitaciones", privileged_roles: "Propietarios y administradores", assigned_collections: "Solo su cartera asignada", own_cash_closing: "Cierre de su propia caja"};
  const actions = {"client_team.profile_changed": "Perfil actualizado", "client_team.password_reset_requested": "Recuperación solicitada","customer_data.exported": "Datos del cliente exportados","payments.voided": "Pago anulado","client_team.role_changed": "Cambio de rol", "client_team.status_changed": "Cambio de acceso", "client_team.member_removed": "Integrante retirado", "client_user.invitation_created": "Invitación creada", "client_user.invitation_revoked": "Invitación revocada", "client_user.invitation_accepted": "Invitación aceptada", "collections.assignment_created": "Cartera asignada", "collections.assignment_released": "Cartera liberada"};
  const element = (tag, text) => {const node = document.createElement(tag); if (text !== undefined) node.textContent = text; return node;};
  function notify(text, error = false) {
    message.setAttribute("role", error ? "alert" : "status");
    message.setAttribute("aria-atomic", "true");
    message.textContent = "";
    message.className = "message " + (error ? "error" : "success"); message.hidden = false;
    message.textContent = text;
    if (error && message.isConnected && !message.closest("[hidden]")) {
      message.scrollIntoView?.({behavior: "instant", block: "center", inline: "nearest"});
    }
  }
  async function request(path, method = "GET", body) {
    if (!client) throw new Error("Sesión no disponible.");
    const selectedTenant = client.tenant_id;
    const response = await fetch(base + path, {method, credentials: "same-origin", headers: {"Content-Type": "application/json", "X-Tenant-ID": String(client.tenant_id)}, ...(body === undefined ? {} : {body: JSON.stringify(body)})});
    const data = response.ok ? await response.json() : await response.json().catch(() => ({}));
    if (!client || client.tenant_id !== selectedTenant) throw new Error("El cliente cambió. Abra nuevamente el detalle.");
    if (!response.ok) {
      if ([401, 403].includes(response.status)) {clearActivation(); clearMemberDetail(); panel.hidden = true; document.getElementById("administrationLink").hidden = true;}
    function spanishApiError(detail, status) {
      const translations = {
  "Configure and enable the tenant late-fee policy first": "Configure y active la política de mora antes de crear o modificar un préstamo con mora.",
  "Late-fee policy not configured": "Configure la política de mora en la sección Préstamos.",
  "First payment date cannot be before the loan start date": "La primera cuota debe vencer en la fecha del préstamo o después. Revise ambas fechas.",
  "Borrower not found": "No se encontró el prestatario en este negocio. Actualice la lista y selecciónelo nuevamente.",
  "Borrower is inactive": "El prestatario está inactivo. Revise su estado antes de crear el préstamo.",
  "Loan not found": "No se encontró el préstamo en este negocio. Actualice la lista y selecciónelo nuevamente.",
  "Loan is not active": "El préstamo no está activo. Revise su estado antes de registrar un pago.",
  "Installment not found": "No se encontró la cuota. Actualice el préstamo y selecciónela nuevamente.",
  "Payment not found": "No se encontró el pago. Actualice el historial del préstamo.",
  "Payment date cannot be in the future": "La fecha del pago no puede ser futura. Revise la fecha indicada.",
  "Payment date precedes an existing late-fee assessment": "La fecha del pago es anterior a la mora ya calculada. Revise la fecha y el historial antes de continuar.",
  "Payment amount must be greater than zero": "El monto del pago debe ser mayor que cero.",
  "Payment exceeds installment balance": "El pago supera el saldo de la cuota. Actualice el saldo y revise el monto.",
  "Collectors cannot record payments": "El rol Cobrador no permite registrar pagos. Solicite acceso de caja al propietario o administrador.",
  "Payment operation access required": "Su rol no permite esta operación de pago. Consulte al propietario o administrador.",
  "Payment request belongs to another operator": "Esta solicitud de pago pertenece a otro operador. Revise el historial con el propietario o administrador antes de continuar.",
  "Payment request key was used with different details": "Esta solicitud ya se usó con otros datos de pago. Revise el historial antes de volver a cobrar.",
  "Original payment was voided; use a new request key": "El pago original fue anulado. Revise su recibo y la anulación antes de iniciar otro pago.",
  "Original receipt unavailable; review payment history": "El recibo original no está disponible. Revise el historial antes de volver a cobrar.",
  "Projection date cannot be in the future": "La fecha de consulta no puede ser futura.",
  "Payment is already voided; the original reason cannot be changed": "El pago ya fue anulado. No se puede cambiar el motivo original.",
  "Payment belongs to a cash closing; a reconciled adjustment is required": "El pago pertenece a un cierre de caja. Solicite un ajuste conciliado al propietario o administrador.",
  "Payment predates correction snapshots; a reconciled adjustment is required": "Este pago requiere un ajuste conciliado. Consulte al propietario o administrador.",
  "Only the latest recorded payment on the loan may be voided": "Solo puede anular el último pago registrado del préstamo. Revise el historial.",
  "Payment ledger is incomplete; reconciliation is required": "El registro del pago está incompleto. Solicite una conciliación antes de continuar.",
  "Loan status does not allow payment correction": "El estado del préstamo no permite anular este pago.",
  "Installment changed after payment; reconciliation is required": "La cuota cambió después del pago. Solicite una conciliación antes de continuar.",
  "Promise allocation requires reconciliation": "La aplicación del pago a las promesas requiere conciliación. Consulte al propietario o administrador.",
  "Release collector assignments before changing or suspending this membership": "Libere las carteras asignadas antes de cambiar el rol o suspender este integrante.",
  "Client must retain at least one owner": "El negocio debe conservar al menos un propietario.",
  "Client must retain at least one active owner": "El negocio debe conservar al menos un propietario activo.",
  "You cannot suspend your own membership": "No puede suspender su propio acceso.",
  "Only the owner may manage owners and administrators": "Solo el propietario puede administrar propietarios y administradores.",
  "Administration access required": "Su rol no permite administrar el equipo. Consulte al propietario o administrador.",
  "Reactivate access before requesting password recovery": "Reactive el acceso del integrante antes de solicitar la recuperación de contraseña.",
  "Membership not found": "No se encontró el integrante en este negocio. Actualice el equipo.",
  "Invitation not found": "No se encontró la invitación. Actualice la lista.",
  "Client invitation not found": "No se encontró la invitación en este negocio. Actualice la lista.",
  "An active invitation already exists for this client and email": "Ya existe una invitación pendiente para este correo. Revísela en Invitaciones; si perdió el enlace, revoque la invitación antes de crear otra.",
  "A user with this email already exists": "Ya existe una cuenta con este correo. Revise el equipo o use otro correo para la invitación.",
  "A platform user with this email already exists": "Ya existe una cuenta de plataforma con este correo. Revise el equipo antes de invitarla.",
  "Only pending client invitations can be revoked": "Solo puede revocar invitaciones pendientes. Actualice la lista para revisar su estado.",
  "Role is not available for this product": "El rol seleccionado no está disponible para este negocio. Seleccione un rol permitido.",
  "Client must be active": "El negocio debe estar activo para crear invitaciones.",
  "Client not found": "No se encontró el negocio. Actualice su acceso y selecciónelo nuevamente.",
  "Client product is unavailable": "PréstamoDesk no está disponible para este negocio. Consulte al administrador.",
  "Authentication required": "Su sesión no está disponible. Inicie sesión nuevamente.",
  "Invalid email or password": "El correo o la contraseña no son correctos. Revise sus datos.",
  "Tenant context required": "Seleccione un negocio antes de continuar.",
  "User is not a member of this tenant": "No tiene acceso a este negocio. Actualice su acceso o consulte al propietario.",
  "Tenant is suspended": "El negocio está suspendido. Consulte al administrador.",
  "Tenant owner access required": "Esta operación requiere el rol Propietario.",
  "Role does not permit this operation": "Su rol no permite esta operación. Consulte al propietario o administrador.",
  "Cashier membership required": "Su rol no permite cerrar caja. Consulte al propietario o administrador."
};
      if (status >= 500) return "No se pudo completar la solicitud por un problema del servidor. Si estaba registrando un pago, revise el historial antes de volver a cobrar.";
      if (typeof detail === "string" && Object.hasOwn(translations, detail)) return translations[detail];
      const fallback = {
        400: "No se pudo completar la solicitud. Revise los datos indicados.",
        401: "Su sesión no está disponible. Inicie sesión nuevamente.",
        403: "No tiene permiso para esta operación. Consulte al propietario o administrador.",
        404: "No se encontró el registro en este negocio. Actualice la sección.",
        409: "No se pudo completar la operación por un conflicto con el estado actual. Actualice la sección y revise el registro antes de continuar.",
        422: "Revise los campos obligatorios, los montos y las fechas antes de continuar.",
        429: "Se realizaron demasiadas solicitudes. Espere un momento antes de continuar."
      };
      return fallback[status] || "No se pudo completar la solicitud. Actualice la sección y revise los datos antes de continuar.";
    }
      const error = new Error(spanishApiError(data.detail, response.status));
      error.status = response.status;
      throw error;
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
  let selectedMemberButton = null;
  function renderMembers() {
    const container = document.getElementById("administrationMembers"); container.replaceChildren();
    document.getElementById("teamCount").textContent = String(team.members.length);
    for (const member of team.members) {
      const row = element("tr"); row.dataset.membershipId = String(member.membership_id); row.dataset.selected = String(memberDetail?.membership_id === member.membership_id);
      const name = element("td"); name.dataset.initials = member.display_name.trim().split(/\s+/u).filter(Boolean).slice(0,2).map(part => Array.from(part)[0]).join("").toLocaleUpperCase("es-DO"); name.append(element("strong", member.display_name), element("span", member.email));
      const role = element("td"), roleBadge = element("span", labels[member.role] || member.role); roleBadge.className = "role-pill"; role.append(roleBadge);
      const status = element("td"); const badge = element("span", member.is_active ? "Activo" : "Suspendido"); badge.className = "status " + (member.is_active ? "active" : "inactive"); status.append(badge);
      if (!member.account_active) status.append(element("small", "Cuenta desactivada"));
      const action = element("td"), detail = element("button", "Ver detalle"); detail.type = "button"; detail.className = "secondary"; detail.setAttribute("aria-label", "Ver detalle de " + member.display_name);
      detail.addEventListener("click", async () => {
        if (detailBusy) return;
        clearMemberDetail(); selectedMemberButton = detail; detail.disabled = true;
        try {await loadMemberDetail(member.membership_id);} catch (error) {notify(error.message, true);} finally {detail.disabled = false;}
      });
      action.append(detail); row.append(name,role,status,action); container.append(row);
    }
    if (!team.members.length) {const row = element("tr"), cell = element("td", "Sin integrantes."); cell.colSpan = 4; row.append(cell); container.append(row);}
  }
  async function refresh() {
    const [newTeam, invitations, audit] = await Promise.all([request("/team"), request("/invitations"), request("/audit")]);
    team = newTeam; renderMembers();
    if (activationRecord && invitations.invitations.some(item => item.id === activationRecord.id && item.status !== "pending")) clearActivation();
    const inviteRole = document.getElementById("administrationInviteRole"); inviteRole.replaceChildren(...roleSelect(team.assignable_roles, "collector").children);
    const list = document.getElementById("administrationInvitations"); list.replaceChildren();
    for (const invitation of invitations.invitations) {
      const row = element("p", invitation.display_name + " · " + invitation.email + " · " + labels[invitation.role] + " · " + invitation.status);
      if (invitation.status === "pending" && (client.role === "owner" || !["owner", "administrator"].includes(invitation.role))) row.append(button("Revocar", async () => {if (confirm("¿Revocar esta invitación?")) await request("/invitations/" + invitation.id + "/revoke", "POST");}));
      list.append(row);
    }
    if (!invitations.invitations.length) list.append(element("p", "Sin invitaciones."));
    const history = document.getElementById("administrationAudit"); history.replaceChildren();
    for (const event of audit) history.append(element("p", new Date(event.created_at + (event.created_at.endsWith("Z") ? "" : "Z")).toLocaleString("es-DO") + " · " + (actions[event.action] || event.action) + " · Usuario #" + event.actor_user_id + " · Registro #" + event.target_id));
    if (!audit.length) history.append(element("p", "Sin cambios registrados."));
  }
  let memberDetail = null;
  let detailGeneration = 0;
  let detailBusy = false;
  const detailPanel = document.getElementById("administrationMemberDetail");
  const profileForm = document.getElementById("memberProfileForm");
  function detailNotify(text, error = false) {
    const box = document.getElementById("administrationMemberMessage");
    if (!box) return;
    box.setAttribute("role", error ? "alert" : "status");
    box.setAttribute("aria-atomic", "true");
    box.textContent = "";
    box.className = "message " + (error ? "error" : "success"); box.hidden = false;
    box.textContent = text;
    if (error && box.isConnected && !box.closest("[hidden]")) {
      box.scrollIntoView?.({behavior: "instant", block: "center", inline: "nearest"});
    }
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
    document.querySelectorAll("#administrationMembers tr[data-membership-id]").forEach(row => {row.dataset.selected = "false";});
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
    document.querySelectorAll("#administrationMembers tr[data-membership-id]").forEach(row => {row.dataset.selected = String(row.dataset.membershipId === String(detail.membership_id));});
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
    for (const event of detail.history) history.append(element("p", dateLabel(event.created_at) + " · " + (actions[event.action] || event.action) + " · Usuario #" + event.actor_user_id));
    if (!detail.history.length) history.append(element("p", "Sin cambios registrados para este integrante."));
    if (detail.more_history) history.append(element("p", "Se muestran los 50 eventos más recientes."));
    detailPanel.hidden = false;
    if (window.matchMedia?.("(max-width: 1050px)").matches) detailPanel.scrollIntoView?.({behavior: "smooth", block: "start"});
    setDetailBusy(detailBusy);
  }
  async function loadMemberDetail(id, resetTab = true) {
    const generation = ++detailGeneration;
    const detail = await request("/memberships/" + id);
    if (generation !== detailGeneration) return;
    memberDetail = detail; renderMemberDetail();
    if (resetTab) {selectMemberTab("memberAccountPanel"); document.getElementById("memberAccountTab").focus();}
  }
  document.getElementById("administrationMemberClose").addEventListener("click", () => {clearMemberDetail(); if (selectedMemberButton?.isConnected) selectedMemberButton.focus(); else document.getElementById("teamTab").focus();});
  document.addEventListener("keydown", event => {if (event.key === "Escape" && !detailPanel.hidden && !detailBusy) document.getElementById("administrationMemberClose").click();});
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

  function selectSection(id) {
    for (const tab of document.querySelectorAll("[data-admin-tab]")) {
      const active = tab.dataset.adminTab === id; tab.setAttribute("aria-selected", String(active)); tab.tabIndex = active ? 0 : -1;
      document.getElementById(tab.dataset.adminTab).hidden = !active;
    }
  }
  document.getElementById("administrationSections").addEventListener("click", event => {const tab = event.target.closest("[data-admin-tab]"); if (tab) selectSection(tab.dataset.adminTab);});
  document.getElementById("administrationSections").addEventListener("keydown", event => {
    if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
    const tabs = [...document.querySelectorAll("[data-admin-tab]")], index = tabs.indexOf(document.activeElement); if (index < 0) return;
    event.preventDefault(); const next = event.key === "Home" ? 0 : event.key === "End" ? tabs.length - 1 : (index + (event.key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length;
    selectSection(tabs[next].dataset.adminTab); tabs[next].focus();
  });
  document.getElementById("inviteMemberButton").addEventListener("click", () => {selectSection("invitationsSection"); document.querySelector("#administrationInvite input").focus();});
  const handleAccess = async event => {
    clearMemberDetail();
    if (activationRecord && (activationRecord.tenantId !== event.detail.tenant_id || !["owner", "administrator"].includes(event.detail.role))) clearActivation();
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
        if ([401, 403].includes(response.status)) {clearActivation(); clearMemberDetail(); panel.hidden = true;}
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
    event.preventDefault(); if (!confirmInvitationLeave()) return; const form = event.currentTarget; const submit = form.querySelector("button"); if (submit.disabled) return; submit.disabled = true;
    try {
      const result = await request("/invitations", "POST", Object.fromEntries(new FormData(form)));
      showActivation(result); form.reset();
      try {await refresh(); notify("Invitación creada. Copie el enlace privado para compartirlo.");}
      catch {notify("Invitación creada. Guarde el enlace; no se pudo actualizar la lista.", true);}
    } catch (error) {notify(error.message, true);} finally {submit.disabled = false;}
  });
  document.getElementById("logoutButton").addEventListener("click", event => {if (!confirmInvitationLeave()) {event.preventDefault(); event.stopImmediatePropagation();}}, true);
  document.getElementById("logoutButton").addEventListener("click", () => {clearMemberDetail(); panel.hidden = true; document.getElementById("administrationLink").hidden = true; client = null; team = null; window.prestamodeskAccess = null; clearActivation();});
})();
