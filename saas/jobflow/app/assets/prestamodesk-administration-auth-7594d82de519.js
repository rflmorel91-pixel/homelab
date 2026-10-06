(() => {
  "use strict";
  const auth = document.getElementById("authPanel"), message = document.getElementById("pageMessage"), login = document.getElementById("loginForm");
  let generation = 0;
  const note = text => {message.textContent = text; message.hidden = false;};
  async function request(path, options = {}) {
    const response = await fetch("/api/v1" + path, {credentials: "same-origin", ...options, headers: {"Content-Type": "application/json", ...(options.headers || {})}});
    const data = response.status === 204 ? null : await response.json();
    if (!response.ok) {const error = new Error(typeof data?.detail === "string" ? data.detail : "No se pudo completar la solicitud."); error.status = response.status; throw error;}
    return data;
  }
  async function access() {
    const current = ++generation;
    const result = await request("/auth/products/prestamodesk/access");
    if (current !== generation) return;
    const clients = result.clients || [], selected = localStorage.getItem("prestamodesk_tenant_id");
    const client = clients.find(item => String(item.tenant_id) === selected) || (clients.length === 1 ? clients[0] : null);
    auth.hidden = true; document.getElementById("logoutButton").hidden = false;
    if (!client) {note(clients.length ? "Seleccione su cliente desde el espacio de préstamos." : "Su cuenta no tiene acceso activo a PréstamoDesk.");return;}
    document.getElementById("clientContext").textContent = `Cliente #${client.client_number} · ${client.name}`;document.getElementById("clientContext").hidden = false;
    if (!["owner", "administrator"].includes(client.role)) {note("La administración requiere acceso de propietario o administrador.");return;}
    localStorage.setItem("prestamodesk_tenant_id",String(client.tenant_id));
    message.hidden = true;window.prestamodeskAccess = client;window.dispatchEvent(new CustomEvent("prestamodesk-access",{detail:client}));
  }
  login.addEventListener("submit",async event => {
    event.preventDefault();const button=login.querySelector("button");button.disabled=true;
    try {await request("/auth/login",{method:"POST",body:JSON.stringify({email:document.getElementById("loginEmail").value,password:document.getElementById("loginPassword").value})});login.reset();await access();}
    catch(error){note(error.status===401 ? "Correo o contraseña incorrectos." : error.message);}finally{button.disabled=false;}
  });
  document.getElementById("logoutButton").addEventListener("click",async () => {
    generation++;window.prestamodeskAccess=null;localStorage.removeItem("prestamodesk_tenant_id");
    document.getElementById("administrationPanel").hidden=true;document.getElementById("clientContext").hidden=true;document.getElementById("logoutButton").hidden=true;document.getElementById("administrationLink").hidden=true;
    try{await request("/auth/logout",{method:"POST"});}catch{note("No se pudo cerrar la sesión en el servidor. Intente nuevamente.");document.getElementById("logoutButton").hidden=false;}
    auth.hidden=false;
  });
  request("/health").then(data=>{document.getElementById("healthStatus").textContent="API: "+data.status;}).catch(()=>{document.getElementById("healthStatus").textContent="API no disponible";});
  access().catch(error=>{auth.hidden=false;if(error.status!==401)note(error.message);});
})();
