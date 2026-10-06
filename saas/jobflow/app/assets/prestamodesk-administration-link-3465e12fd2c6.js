(() => {"use strict"; const link = document.getElementById("administrationLink");
 const show = client => {link.hidden = !client || !["owner", "administrator"].includes(client.role);};
 window.addEventListener("prestamodesk-access", event => show(event.detail));
 document.getElementById("logoutButton").addEventListener("click", () => show(null));
 show(window.prestamodeskAccess);
})();
