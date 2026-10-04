(() => {
  "use strict";
  const panel = document.getElementById("administrationPanel");
  const message = document.getElementById("administrationMessage");
  const base = "/api/v1/products/prestamodesk/administration";
  let client = null;
  let team = null;
  const labels = {owner: "Propietario", administrator: "Administrador", supervisor: "Supervisor", collector: "Cobrador", cashier: "Cajero", member: "Miembro (caja existente)"};
  const permissions = {operations: "Prestatarios, préstamos, solicitudes y configuración", loan_read: "Consultar préstamos", payments: "Consultar caja y registrar pagos", collections: "Cartera completa y gestiones", assignments: "Asignar y liberar carteras", supervision: "Supervisión y exportación", team: "Equipo operativo e invitaciones", privileged_roles: "Propietarios y administradores", assigned_collections: "Solo su cartera asignada", own_cash_closing: "Cierre de su propia caja"};
  const actions = {"client_team.role_changed": "Cambio de rol", "client_team.status_changed": "Cambio de acceso", "client_team.member_removed": "Integrante retirado", "client_user.invitation_created": "Invitación creada", "client_user.invitation_revoked": "Invitación revocada", "client_user.invitation_accepted": "Invitación aceptada", "collections.assignment_created": "Cartera asignada", "collections.assignment_released": "Cartera liberada"};
  const element = (tag, text) => {const node = document.createElement(tag); if (text !== undefined) node.textContent = text; return node;};
  function notify(text, error = false) {message.textContent = text; message.className = "message " + (error ? "error" : "success"); message.hidden = false;}
  async function request(path, method = "GET", body) {
    const response = await fetch(base + path, {method, credentials: "same-origin", headers: {"Content-Type": "application/json", "X-Tenant-ID": String(client.tenant_id)}, ...(body === undefined ? {} : {body: JSON.stringify(body)})});
    const data = await response.json();
    if (!response.ok) {
      if ([401, 403].includes(response.status)) panel.hidden = true;
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
    node.addEventListener("click", async () => {node.disabled = true; try {await action(); await refresh(); notify("Cambio guardado.");} catch (error) {notify(error.message, true);} finally {node.disabled = false;}});
    return node;
  }
  function renderMembers() {
    const container = document.getElementById("administrationMembers"); container.replaceChildren();
    for (const member of team.members) {
      const row = element("div"); row.className = "panel";
      row.append(element("h4", member.display_name), element("p", member.email + " · " + (member.is_active ? "Activo" : "Suspendido")));
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
  const handleAccess = async event => {
    client = event.detail; panel.hidden = !["owner", "administrator"].includes(client.role);
    document.getElementById("administrationLink").hidden = panel.hidden;
    if (!panel.hidden) {try {await refresh();} catch (error) {notify(error.message, true);}}
  };
  window.addEventListener("prestamodesk-access", handleAccess);
  if (window.prestamodeskAccess) handleAccess({detail: window.prestamodeskAccess});
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
  document.getElementById("logoutButton").addEventListener("click", () => {panel.hidden = true; document.getElementById("administrationLink").hidden = true; client = null; team = null; window.prestamodeskAccess = null; document.getElementById("administrationActivation").replaceChildren();});
})();
