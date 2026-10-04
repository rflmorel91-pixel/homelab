(() => {
  "use strict";
  const panel = document.getElementById("paymentCorrectionPanel");
  const list = document.getElementById("paymentCorrectionList");
  const message = document.getElementById("paymentCorrectionMessage");
  let generation = 0;
  let busy = false;
  const currency = new Intl.NumberFormat("es-DO", {style: "currency", currency: "DOP"});
  const text = (tag, contents) => { const node = document.createElement(tag); node.textContent = contents; return node; };
  const errors = {
    "Only the latest recorded payment on the loan may be voided": "Solo puede anular el último pago registrado del préstamo.",
    "Payment belongs to a cash closing; a reconciled adjustment is required": "Este pago pertenece a un cierre de caja y requiere conciliación.",
    "Payment predates correction snapshots; a reconciled adjustment is required": "Este pago es anterior a la función de corrección y requiere conciliación.",
    "Installment changed after payment; reconciliation is required": "La cuota cambió después del pago y requiere conciliación.",
    "Payment operation access required": "Su cuenta ya no tiene permiso para corregir pagos."
  };
  function notify(contents, failed = false) {
    message.textContent = contents;
    message.className = "message " + (failed ? "error" : "success");
    message.hidden = false;
  }
  function clear() { generation++; panel.hidden = true; list.replaceChildren(); message.hidden = true; }
  async function load(loanId, role) {
    const request = ++generation;
    list.replaceChildren();
    message.hidden = true;
    panel.hidden = !["owner", "administrator"].includes(role);
    if (panel.hidden) return;
    try {
      const payments = await apiRequest(`${PRODUCT_BASE}/payments/loan/${loanId}`);
      if (request !== generation) return;
      const latest = Math.max(0, ...payments.filter(p => !p.voided_at).map(p => p.id));
      if (!payments.length) { list.append(text("p", "No hay pagos registrados.")); return; }
      for (const payment of [...payments].sort((a, b) => b.id - a.id)) {
        const row = document.createElement("article");
        row.append(text("h4", `PM-${String(payment.id).padStart(8, "0")} · ${currency.format(Number(payment.amount))}`));
        row.append(text("p", `Registrado por usuario #${payment.recorded_by_user_id} · ${payment.paid_at}`));
        if (payment.voided_at) {
          row.append(text("p", `Anulado · ${payment.void_reason} · Usuario #${payment.voided_by_user_id}`));
        } else if (payment.cash_closing_id) {
          row.append(text("p", "Incluido en un cierre de caja. Requiere conciliación para ajustar."));
        } else if (!payment.correction_supported) {
          row.append(text("p", "Pago anterior a la función de corrección. Requiere conciliación para ajustar."));
        } else if (payment.id !== latest) {
          row.append(text("p", "Hay un pago posterior en este préstamo."));
        } else {
          const button = text("button", "Anular pago por error");
          button.type = "button";
          button.className = "secondary";
          button.addEventListener("click", async () => {
            if (busy) return;
            const entered = window.prompt("Explique el error de este pago (mínimo 5 caracteres):");
            if (entered === null) return;
            const reason = entered.trim();
            if (reason.length < 5 || reason.length > 1000) { notify("Indique un motivo de entre 5 y 1000 caracteres.", true); return; }
            if (!window.confirm(`¿Anular PM-${String(payment.id).padStart(8, "0")} por ${currency.format(Number(payment.amount))}? El recibo original se conservará como anulado. Motivo: ${reason}`)) return;
            busy = true;
            button.disabled = true;
            let corrected = false;
            try {
              await apiRequest(`${PRODUCT_BASE}/payments/${payment.id}/void`, {method: "POST", body: JSON.stringify({reason})});
              corrected = true;
              if (request !== generation) return;
              await openLoan(loanId);
              // Refresh the relevant summary after the loan balances are refreshed.
              if (typeof loadDashboard === "function") await loadDashboard();
              if (typeof searchLoans === "function") await searchLoans();
              notify("Pago anulado. El registro original se conserva. Registre el pago correcto si corresponde.");
            } catch (cause) {
              if (request === generation || corrected) {
                notify(corrected ? "El pago fue anulado, pero no se pudo actualizar la pantalla. Actualice la página antes de continuar." : (errors[cause.message] || cause.message), true);
              }
            } finally { busy = false; button.disabled = false; }
          });
          row.append(button);
        }
        list.append(row);
      }
    } catch (cause) {
      if (request !== generation) return;
      if ([401, 403].includes(cause.status)) panel.hidden = true;
      notify(errors[cause.message] || cause.message, true);
    }
  }
  window.prestamodeskPaymentHistory = {load, clear};
  document.getElementById("logoutButton").addEventListener("click", clear);
  document.getElementById("closeLoanDetail").addEventListener("click", clear);
})();
