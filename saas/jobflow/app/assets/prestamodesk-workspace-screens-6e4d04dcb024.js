/* Generated from existing screens; regenerate using scripts/build-prestamodesk-workspace.py. */
window.PrestamoDeskScreens = {
"loans": {html:"\n  <header class=\"app-header\">\n    <div>\n      <span class=\"eyebrow\">FieldLookers</span>\n      <h1>PréstamoDesk</h1>\n      <p>Administración de préstamos en DOP</p>\n    </div>\n\n    <div class=\"header-actions\"><a href=\"/prestamodesk/workspace\">Mi espacio · Todas las secciones</a>\n      <span id=\"clientContext\" class=\"badge\" hidden></span>\n      <a id=\"administrationLink\" href=\"/prestamodesk-administracion.html\" hidden>Administración</a>\n      <span id=\"healthStatus\">Comprobando API…</span>\n      <button id=\"logoutButton\" class=\"secondary\" hidden>\n        Cerrar sesión\n      </button>\n    </div>\n  </header>\n\n  <main>\n    <div id=\"errorMessage\" class=\"message error\" role=\"alert\" aria-atomic=\"true\" hidden></div>\n    <div id=\"successMessage\" class=\"message success\" hidden></div>\n\n    <section id=\"authPanel\" class=\"panel auth-panel\">\n      <h2>Iniciar sesión</h2>\n\n      <form id=\"loginForm\" class=\"form-grid\">\n        <label>\n          Correo electrónico\n          <input\n            id=\"loginEmail\"\n            type=\"email\"\n            autocomplete=\"username\"\n            required\n          >\n        </label>\n\n        <label>\n          Contraseña\n          <input\n            id=\"loginPassword\"\n            type=\"password\"\n            autocomplete=\"current-password\"\n            required\n          >\n        </label>\n\n        <button type=\"submit\">Iniciar sesión</button>\n\n        <button\n          id=\"forgotPasswordButton\"\n          type=\"button\"\n          class=\"secondary\"\n        >\n          ¿Olvidó su contraseña?\n        </button>\n      </form>\n\n      <form\n        id=\"passwordResetRequestForm\"\n        class=\"form-grid\"\n        hidden\n      >\n        <p>\n          Ingrese el correo de su cuenta. Si la cuenta es\n          elegible, enviaremos un enlace seguro.\n        </p>\n\n        <label>\n          Correo electrónico\n          <input\n            id=\"passwordResetEmail\"\n            type=\"email\"\n            autocomplete=\"email\"\n            required\n          >\n        </label>\n\n        <button\n          id=\"passwordResetRequestButton\"\n          type=\"submit\"\n        >\n          Enviar enlace\n        </button>\n\n        <button\n          id=\"backToSignInButton\"\n          type=\"button\"\n          class=\"secondary\"\n        >\n          Volver a iniciar sesión\n        </button>\n      </form>\n    </section>\n\n    <div id=\"workspace\" data-loan-task=\"loans\" hidden>\n      <div id=\"compactLoanToolbar\" class=\"compact-toolbar\">\n        <nav aria-label=\"Tareas de préstamos\" class=\"compact-tabs\">\n          <button type=\"button\" data-loan-tab=\"loans\" aria-pressed=\"true\" aria-controls=\"compactLoans\">Préstamos <span id=\"compactLoanCount\" class=\"badge\">0</span></button>\n          <button type=\"button\" data-loan-tab=\"borrowers\" aria-pressed=\"false\" aria-controls=\"compactBorrowers\" data-loan-manager>Prestatarios <span id=\"compactBorrowerCount\" class=\"badge\">0</span></button>\n          <button type=\"button\" data-loan-tab=\"applications\" aria-pressed=\"false\" aria-controls=\"compactApplications compactProspects\" data-loan-manager>Solicitudes <span id=\"compactApplicationCount\" class=\"badge\">0</span></button>\n        </nav>\n        <div class=\"compact-actions\">\n          <button type=\"button\" data-loan-form=\"compactLoanForm\" aria-expanded=\"false\" aria-controls=\"compactLoanForm\" data-loan-manager>Nuevo préstamo</button>\n          <button type=\"button\" data-loan-form=\"compactBorrowerForm\" aria-expanded=\"false\" aria-controls=\"compactBorrowerForm\" data-loan-manager>Nuevo prestatario</button>\n          <button type=\"button\" data-loan-tab=\"settings\" aria-expanded=\"false\" aria-controls=\"compactSettings\" data-loan-manager>Configuración de mora</button>\n        </div>\n        <p class=\"compact-hint\">Los datos de los formularios se conservan al cambiar de tarea dentro de esta sección.</p>\n      </div>\n\n      <section class=\"summary-grid\">\n        <article class=\"summary-card\">\n          <span>Solicitudes abiertas</span>\n          <strong id=\"openApplicationCount\">0</strong>\n        </article>\n\n        <article class=\"summary-card\">\n          <span>Prestatarios</span>\n          <strong id=\"borrowerCount\">0</strong>\n        </article>\n\n        <article class=\"summary-card\">\n          <span>Préstamos activos</span>\n          <strong id=\"activeLoanCount\">0</strong>\n        </article>\n\n        <article class=\"summary-card\">\n          <span>Saldo pendiente</span>\n          <strong id=\"outstandingBalance\">RD$0.00</strong>\n        </article>\n\n        <article class=\"summary-card\">\n          <span>Cuotas vencidas</span>\n          <strong id=\"overdueCount\">0</strong>\n        </article>\n      </section>\n\n      <div class=\"workspace-grid\">\n        <section class=\"panel\" id=\"compactBorrowerForm\" data-compact-panel=\"form\">\n          <div class=\"section-heading\"><h2>Nuevo prestatario</h2><button type=\"button\" class=\"secondary\" data-loan-close=\"compactBorrowerForm\">Ocultar formulario</button></div>\n\n          <form id=\"borrowerForm\" class=\"form-grid\">\n            <label>\n              Nombre completo\n              <input id=\"borrowerName\" maxlength=\"200\" required>\n            </label>\n\n            <label>\n              Tipo de documento\n              <select id=\"borrowerDocumentType\">\n                <option value=\"cedula\">Cédula</option>\n                <option value=\"passport\">Pasaporte</option>\n                <option value=\"other\">Otro</option>\n              </select>\n            </label>\n\n            <label>\n              Número de documento\n              <input id=\"borrowerDocumentNumber\" maxlength=\"50\">\n            </label>\n\n            <label>\n              Teléfono\n              <input id=\"borrowerPhone\" maxlength=\"40\">\n            </label>\n\n            <label>\n              Municipio\n              <input id=\"borrowerMunicipality\" maxlength=\"120\">\n            </label>\n\n            <label>\n              Provincia\n              <input id=\"borrowerProvince\" maxlength=\"120\">\n            </label>\n\n            <button type=\"submit\">Guardar prestatario</button>\n          </form>\n        </section>\n\n        <section class=\"panel\" id=\"compactLoanForm\" data-compact-panel=\"form\">\n          <div class=\"section-heading\"><h2>Nuevo préstamo</h2><button type=\"button\" class=\"secondary\" data-loan-close=\"compactLoanForm\">Ocultar formulario</button></div>\n\n          <div class=\"form-grid\">\n            <label>\n              Buscar prestatario\n              <input id=\"loanBorrowerSearch\" type=\"search\" autocomplete=\"off\"\n                placeholder=\"Nombre o documento\" aria-controls=\"loanBorrower\"\n                aria-describedby=\"loanBorrowerSearchStatus\">\n            </label>\n            <button id=\"loanBorrowerSearchClear\" type=\"button\" class=\"secondary\">Limpiar búsqueda</button>\n          </div>\n          <p id=\"loanBorrowerSearchStatus\" class=\"notice\" role=\"status\" aria-atomic=\"true\"></p>\n\n          <p id=\"loanCreationNotice\" class=\"notice\" role=\"status\" hidden></p>\n          <button id=\"loanCreationRetry\" type=\"button\" class=\"secondary\" hidden>Confirmar o recuperar el préstamo</button>\n          <form id=\"loanForm\" class=\"form-grid\">\n            <label>\n              Prestatario\n              <select id=\"loanBorrower\" aria-describedby=\"loanBorrowerSearchStatus\" required></select>\n            </label>\n\n            <label>\n              Tipo de préstamo\n              <select id=\"loanType\">\n                <option value=\"personal\">Personal</option>\n                <option value=\"vehicle\">Vehículo</option>\n              </select>\n            </label>\n\n            <fieldset\n              id=\"vehicleLoanFields\"\n              class=\"vehicle-fields\"\n              hidden\n            >\n              <legend>Información del vehículo</legend>\n\n              <label>\n                Precio de contado (DOP)\n                <input\n                  id=\"vehicleCashPrice\"\n                  type=\"number\"\n                  min=\"0.01\"\n                  step=\"0.01\"\n                >\n              </label>\n\n              <label>\n                Inicial (DOP)\n                <input\n                  id=\"vehicleDownPayment\"\n                  type=\"number\"\n                  min=\"0\"\n                  step=\"0.01\"\n                  value=\"0.00\"\n                >\n              </label>\n\n              <label>\n                Marca\n                <input id=\"vehicleMake\" maxlength=\"100\">\n              </label>\n\n              <label>\n                Modelo\n                <input id=\"vehicleModel\" maxlength=\"100\">\n              </label>\n\n              <label>\n                Año\n                <input\n                  id=\"vehicleYear\"\n                  type=\"number\"\n                  min=\"1886\"\n                  max=\"2100\"\n                >\n              </label>\n\n              <label>\n                Color\n                <input id=\"vehicleColor\" maxlength=\"50\">\n              </label>\n\n              <label>\n                VIN o chasis\n                <input id=\"vehicleVin\" maxlength=\"50\">\n              </label>\n\n              <label>\n                Placa\n                <input\n                  id=\"vehicleLicensePlate\"\n                  maxlength=\"30\"\n                >\n              </label>\n\n              <label>\n                Vendedor o concesionario\n                <input id=\"vehicleSeller\" maxlength=\"200\">\n              </label>\n\n              <label>\n                Notas del vehículo\n                <input id=\"vehicleNotes\">\n              </label>\n            </fieldset>\n\n            <label>\n              Monto financiado (DOP)\n              <input\n                id=\"loanPrincipal\"\n                type=\"number\"\n                min=\"0.01\"\n                step=\"0.01\"\n                required\n              >\n            </label>\n\n            <label>\n              Interés total fijo (%)\n              <input\n                id=\"loanRate\"\n                type=\"number\"\n                min=\"0\"\n                max=\"1000\"\n                step=\"0.0001\"\n                required\n              >\n            </label>\n\n            <label>\n              Cantidad de cuotas\n              <input\n                id=\"loanInstallments\"\n                type=\"number\"\n                min=\"1\"\n                max=\"3660\"\n                required\n              >\n            </label>\n\n            <label>\n              Frecuencia\n              <select id=\"loanFrequency\">\n                <option value=\"daily\">Diaria</option>\n                <option value=\"weekly\">Semanal</option>\n                <option value=\"biweekly\">Quincenal</option>\n                <option value=\"monthly\">Mensual</option>\n              </select>\n            </label>\n\n            <label>\n              Fecha del préstamo\n              <input id=\"loanStartDate\" type=\"date\" required>\n            </label>\n\n            <label>\n              Primera cuota\n              <input\n                id=\"loanFirstPaymentDate\"\n                type=\"date\"\n                required\n              >\n            </label>\n\n            <label>\n              <input\n                id=\"loanLateFeeEnabled\"\n                type=\"checkbox\"\n              >\n              Cobrar mora en este préstamo\n            </label>\n\n            <button id=\"loanPreviewButton\" type=\"button\" class=\"secondary\">Vista previa del préstamo</button>\n            <button type=\"submit\">Crear préstamo</button>\n          </form>\n\n          <section id=\"loanPreview\" class=\"panel\" aria-label=\"Vista previa del préstamo\" hidden></section>\n          <p id=\"loanPreviewStatus\" class=\"notice\" role=\"status\" hidden></p>\n\n          <p class=\"notice\">\n            El porcentaje indicado es interés fijo total del\n            préstamo; no representa una tasa APR.\n          </p>\n        </section>\n      </div>\n\n      <section class=\"panel\" id=\"compactApplications\" data-compact-panel=\"applications\">\n        <div class=\"section-heading\">\n          <h2>Solicitudes de préstamo</h2>\n          <span id=\"applicationResultCount\" class=\"badge\">0</span>\n        </div>\n\n        <p>\n          Revise, apruebe o rechace las solicitudes recibidas.\n          Una solicitud aprobada puede convertirse en prestatario,\n          préstamo personal o vehicular y calendario de cuotas.\n        </p>\n\n        <div id=\"applicationList\" class=\"card-list\"></div>\n      </section>\n\n        <section class=\"panel\" id=\"compactProspects\" data-compact-panel=\"applications\">\n          <div class=\"section-heading\">\n            <h2>Prospectos</h2>\n            <span id=\"prospectResultCount\" class=\"badge\">0</span>\n          </div>\n\n          <p>\n            Comparta su página pública para recibir solicitudes\n            preliminares de posibles prestatarios.\n          </p>\n\n          <div class=\"item-actions\">\n            <a\n              id=\"publicProspectPageLink\"\n              class=\"button-link\"\n              href=\"#\"\n              target=\"_blank\"\n              rel=\"noopener\"\n            >\n              Abrir página pública\n            </a>\n          </div>\n\n          <div id=\"prospectList\" class=\"card-list\"></div>\n          <section id=\"prospectApplicationPanel\" class=\"panel\" hidden aria-labelledby=\"prospectApplicationTitle\">\n            <div class=\"section-heading\">\n              <h3 id=\"prospectApplicationTitle\">Preparar solicitud</h3>\n              <button id=\"prospectApplicationCancel\" type=\"button\" class=\"secondary\">Cerrar</button>\n            </div>\n            <p id=\"prospectApplicationContact\"></p>\n            <p>Seleccione el tipo de préstamo y confirme los términos con el prospecto. Guardar una solicitud no crea un prestatario ni un préstamo; requiere revisión y aprobación.</p>\n            <div id=\"prospectApplicationError\" class=\"notice\" role=\"alert\" hidden></div>\n            <form id=\"prospectApplicationForm\" class=\"form-grid\">\n              <label>Tipo de préstamo\n                <select name=\"loan_type\" required>\n                  <option value=\"\">Seleccione una ruta</option>\n                  <option value=\"vehicle\">Vehículo</option>\n                  <option value=\"personal\">Personal</option>\n                </select>\n              </label>\n              <fieldset id=\"prospectApplicationVehicle\" hidden>\n                <legend>Vehículo financiado</legend>\n                <div class=\"form-grid\">\n                  <label>Marca<input name=\"vehicle_make\" maxlength=\"100\"></label>\n                  <label>Modelo<input name=\"vehicle_model\" maxlength=\"100\"></label>\n                  <label>Año<input name=\"vehicle_year\" type=\"number\" min=\"1886\" max=\"2100\" step=\"1\"></label>\n                  <label>Precio del vehículo (DOP)<input name=\"vehicle_cash_price\" type=\"number\" min=\"0.01\" max=\"999999999999.99\" step=\"0.01\" inputmode=\"decimal\"></label>\n                  <label>Inicial (DOP)<input name=\"vehicle_down_payment\" type=\"number\" min=\"0\" max=\"999999999999.99\" step=\"0.01\" inputmode=\"decimal\"></label>\n                  <label>Color (opcional)<input name=\"vehicle_color\" maxlength=\"50\"></label>\n                  <label>VIN/chasis (opcional)<input name=\"vehicle_vin\" maxlength=\"50\"></label>\n                  <label>Placa (opcional)<input name=\"vehicle_license_plate\" maxlength=\"30\"></label>\n                  <label>Vendedor (opcional)<input name=\"vehicle_seller\" maxlength=\"200\"></label>\n                </div>\n              </fieldset>\n              <label>Monto financiado (DOP)<input name=\"principal_amount\" type=\"number\" min=\"0.01\" max=\"999999999999.99\" step=\"0.01\" inputmode=\"decimal\" required></label>\n              <label>Interés total fijo (%)<input name=\"flat_interest_rate_percent\" type=\"number\" min=\"0\" max=\"1000\" step=\"0.0001\" inputmode=\"decimal\" required></label>\n              <label>Número de cuotas<input name=\"installment_count\" type=\"number\" min=\"1\" max=\"3660\" step=\"1\" required></label>\n              <label>Frecuencia\n                <select name=\"payment_frequency\" required>\n                  <option value=\"monthly\">Mensual</option>\n                  <option value=\"biweekly\">Quincenal</option>\n                  <option value=\"weekly\">Semanal</option>\n                </select>\n              </label>\n              <label>Fecha del préstamo<input name=\"start_date\" type=\"date\" required></label>\n              <label>Primera cuota<input name=\"first_payment_date\" type=\"date\" required></label>\n              <label>Notas (opcional)<textarea name=\"notes\" maxlength=\"2000\" rows=\"3\"></textarea></label>\n              <p class=\"notice\">Interés fijo total del préstamo; no representa una tasa APR. Revise el calendario antes de guardar.</p>\n              <div id=\"prospectApplicationQuote\" hidden aria-live=\"polite\"></div>\n              <div class=\"item-actions\">\n                <button id=\"prospectApplicationCalculate\" type=\"button\">Calcular y revisar cuotas</button>\n                <button id=\"prospectApplicationSave\" type=\"submit\" disabled>Guardar solicitud para revisión</button>\n              </div>\n            </form>\n          </section>\n\n        </section>\n\n      <section class=\"panel\" id=\"compactBorrowers\" data-compact-panel=\"borrowers\">\n        <div class=\"section-heading\">\n          <h2>Prestatarios</h2>\n          <span id=\"borrowerResultCount\" class=\"badge\">0</span>\n        </div>\n        <form id=\"borrowerFilterForm\" class=\"form-grid\">\n          <label>Buscar prestatario\n            <input id=\"borrowerSearchQuery\" type=\"search\" autocomplete=\"off\" placeholder=\"Nombre o documento\" aria-controls=\"borrowerList\" aria-describedby=\"borrowerFilterResult\">\n          </label>\n          <label>Estado\n            <select id=\"borrowerStatusFilter\" aria-controls=\"borrowerList\">\n              <option value=\"all\">Todos</option>\n              <option value=\"active\">Activos</option>\n              <option value=\"inactive\">Inactivos</option>\n            </select>\n          </label>\n          <button id=\"borrowerFilterClear\" type=\"button\" class=\"secondary\">Limpiar filtros</button>\n        </form>\n        <p id=\"borrowerFilterResult\" class=\"notice\" role=\"status\" aria-atomic=\"true\"></p>\n        <div id=\"borrowerList\" class=\"card-list\"></div>\n        <section id=\"borrowerDetailPanel\" class=\"panel\" hidden aria-labelledby=\"borrowerDetailTitle\">\n          <div class=\"section-heading\">\n            <h3 id=\"borrowerDetailTitle\" tabindex=\"-1\"></h3>\n            <button id=\"closeBorrowerDetail\" type=\"button\" class=\"secondary\">Cerrar detalle</button>\n          </div>\n          <div id=\"borrowerContactDetails\" class=\"item-meta\"></div>\n          <button id=\"borrowerNewLoan\" type=\"button\" class=\"secondary\" hidden>Nuevo préstamo</button>\n          <button id=\"openBorrowerStatement\" type=\"button\" class=\"secondary\">Estado de cuenta</button>\n          <button id=\"editBorrowerContact\" type=\"button\" class=\"secondary\">Editar contacto</button>\n          <p id=\"borrowerContactMessage\" class=\"notice\" hidden aria-atomic=\"true\"></p>\n          <form id=\"borrowerContactForm\" class=\"form-grid\" hidden>\n            <label>Teléfono<input id=\"borrowerContactPhone\" type=\"tel\" maxlength=\"40\"></label>\n            <label>Correo electrónico<input id=\"borrowerContactEmail\" type=\"email\" maxlength=\"320\"></label>\n            <label>Dirección<textarea id=\"borrowerContactAddress\" maxlength=\"2000\"></textarea></label>\n            <label>Municipio<input id=\"borrowerContactMunicipality\" maxlength=\"120\"></label>\n            <label>Provincia<input id=\"borrowerContactProvince\" maxlength=\"120\"></label>\n            <label>Observaciones<textarea id=\"borrowerContactNotes\" maxlength=\"5000\"></textarea></label>\n            <button id=\"saveBorrowerContact\" type=\"submit\">Guardar contacto</button>\n            <button id=\"cancelBorrowerContact\" type=\"button\" class=\"secondary\">Cancelar edición</button>\n            <button id=\"refreshBorrowerContact\" type=\"button\" class=\"secondary\">Actualizar datos</button>\n          </form>\n          <p id=\"borrowerBalanceSummary\" class=\"notice\"></p>\n          <p>El saldo ordinario corresponde a las cuotas pendientes de los préstamos activos; no incluye mora. Abra cada préstamo para revisar sus cuotas y pagos.</p>\n          <div id=\"borrowerLoanList\" class=\"card-list\"></div>\n        </section>\n      </section>\n\n      <section class=\"panel\" id=\"compactLoans\" data-compact-panel=\"loans\">\n        <div class=\"section-heading\">\n          <h2>Préstamos</h2>\n          <span id=\"loanResultCount\" class=\"badge\">0</span>\n        </div>\n        <form id=\"loanFilterForm\" class=\"form-grid\" role=\"search\" aria-label=\"Buscar préstamos\">\n          <label>Buscar préstamo\n            <input id=\"loanSearchQuery\" type=\"search\" maxlength=\"200\" placeholder=\"Nombre, documento o número de préstamo\" aria-describedby=\"loanSearchHelp\">\n          </label>\n          <label>Estado\n            <select id=\"loanStatusFilter\">\n              <option value=\"all\">Todos</option>\n              <option value=\"active\">Activos</option>\n              <option value=\"paid\">Pagados</option>\n              <option value=\"overdue\">Con cuotas vencidas</option>\n              <option value=\"cancelled\">Cancelados</option>\n            </select>\n          </label>\n          <button type=\"submit\">Buscar</button>\n          <button id=\"loanFilterClear\" type=\"button\" class=\"secondary\">Limpiar filtros</button>\n        </form>\n        <details class=\"compact-help\"><summary>Acerca de las cuotas vencidas</summary><p id=\"loanSearchHelp\" class=\"notice\">Las cuotas vencidas tienen saldo pendiente y una fecha de vencimiento anterior a hoy en República Dominicana. El resumen general conserva los totales de toda la cartera.</p></details>\n        <p id=\"loanFilterResult\" role=\"status\" aria-live=\"polite\"></p>\n        <div id=\"loanList\" class=\"card-list\"></div>\n      </section>\n\n      <section class=\"panel\" id=\"compactSettings\" data-compact-panel=\"settings\">\n        <h2>Política de mora</h2>\n        <p>\n          Configure los valores predeterminados de mora del\n          cliente. La mora solo se aplica a los préstamos donde\n          se marque expresamente la opción correspondiente. Los\n          pagos se aplican primero a mora, luego a interés y\n          finalmente a principal.\n        </p>\n\n        <form id=\"lateFeePolicyForm\" class=\"form-grid\">\n          <label>\n            <input\n              id=\"lateFeeEnabled\"\n              type=\"checkbox\"\n            >\n            Cobrar mora en cuotas vencidas\n          </label>\n\n          <label>\n            Tasa diaria (%)\n            <input\n              id=\"lateFeeDailyRate\"\n              type=\"number\"\n              min=\"0\"\n              max=\"100\"\n              step=\"0.0001\"\n              value=\"0.1000\"\n              required\n            >\n          </label>\n\n          <label>\n            Días completos de gracia\n            <input\n              id=\"lateFeeGraceDays\"\n              type=\"number\"\n              min=\"0\"\n              max=\"365\"\n              step=\"1\"\n              value=\"5\"\n              required\n            >\n          </label>\n\n          <label>\n            Tope sobre la cuota original (%)\n            <input\n              id=\"lateFeeCapPercent\"\n              type=\"number\"\n              min=\"0\"\n              max=\"1000\"\n              step=\"0.0001\"\n              value=\"25.0000\"\n              required\n            >\n          </label>\n\n          <label>\n            Fecha efectiva\n            <input\n              id=\"lateFeeEffectiveDate\"\n              type=\"date\"\n              required\n            >\n          </label>\n\n          <button type=\"submit\">\n            Guardar política de mora\n          </button>\n        </form>\n\n        <p id=\"lateFeePolicyStatus\" class=\"notice\">\n          Política aún no consultada.\n        </p>\n      </section>\n\n      <section id=\"loanDetailPanel\" class=\"panel\" hidden>\n        <div class=\"section-heading\">\n          <h2 id=\"loanDetailTitle\">Detalle del préstamo</h2>\n          <button\n            id=\"closeLoanDetail\"\n            class=\"secondary\"\n            type=\"button\"\n          >\n            Cerrar\n          </button>\n        </div>\n\n        <div id=\"loanDetailSummary\"></div>\n        <section id=\"paymentCorrectionPanel\" hidden aria-labelledby=\"paymentCorrectionTitle\">\n          <h3 id=\"paymentCorrectionTitle\">Pagos y correcciones</h3>\n          <p>Solo el propietario o administrador puede anular el último pago registrado antes de su cierre de caja. El recibo se conserva con el motivo de anulación. Los pagos anteriores a esta función requieren conciliación.</p>\n          <div id=\"paymentCorrectionMessage\" class=\"message\" role=\"status\" hidden></div>\n          <div id=\"paymentCorrectionList\"></div>\n        </section>\n\n\n        <form id=\"loanLateFeeForm\" class=\"form-grid\">\n          <label>\n            <input\n              id=\"loanLateFeeSelected\"\n              type=\"checkbox\"\n            >\n            Cobrar mora en este préstamo\n          </label>\n\n          <button type=\"submit\">\n            Guardar selección de mora\n          </button>\n        </form>\n\n        <p class=\"notice\">\n          Cuando está activada, usa la tasa, los días de gracia,\n          el tope y la fecha efectiva de la política del cliente.\n        </p>\n\n        <h3>Calendario de cuotas</h3>\n        <div id=\"installmentList\" class=\"table-wrap\"></div>\n      </section>\n\n      <section id=\"paymentPanel\" class=\"panel\" hidden>\n        <h2>Registrar pago</h2>\n\n        <form id=\"paymentForm\" class=\"form-grid\">\n          <label>\n            Cuota\n            <select id=\"paymentInstallment\" required></select>\n          </label>\n\n          <label>\n            Monto (DOP)\n            <input\n              id=\"paymentAmount\"\n              type=\"number\"\n              min=\"0.01\"\n              step=\"0.01\"\n              required\n            >\n          </label>\n\n          <label>\n            Fecha del pago\n            <input\n              id=\"paymentDate\"\n              type=\"date\"\n              required\n            >\n          </label>\n\n          <label>\n            Método\n            <select id=\"paymentMethod\">\n              <option value=\"cash\">Efectivo</option>\n              <option value=\"bank_transfer\">\n                Transferencia bancaria\n              </option>\n              <option value=\"card\">Tarjeta</option>\n              <option value=\"other\">Otro</option>\n            </select>\n          </label>\n\n          <label>\n            Referencia\n            <input id=\"paymentReference\" maxlength=\"200\">\n          </label>\n\n          <button type=\"submit\">Registrar pago</button>\n        </form>\n\n        <article id=\"receiptPanel\" class=\"receipt\" hidden>\n          <h3>Recibo de pago</h3>\n          <div id=\"receiptContent\"></div>\n          <button\n            id=\"printReceiptButton\"\n            type=\"button\"\n            class=\"secondary\"\n          >\n            Imprimir\n          </button>\n        </article>\n      </section>\n    </div>\n\n\n    <section id=\"borrowerStatementPanel\" class=\"panel\" hidden aria-labelledby=\"borrowerStatementTitle\">\n      <div class=\"section-heading statement-actions\">\n        <button id=\"printBorrowerStatement\" type=\"button\">Imprimir estado de cuenta</button>\n        <button id=\"closeBorrowerStatement\" type=\"button\" class=\"secondary\">Cerrar estado de cuenta</button>\n      </div>\n      <div id=\"borrowerStatementContent\"></div>\n    </section>\n    <section id=\"loanPreviewPrintPanel\" hidden aria-label=\"Vista previa para imprimir\"></section>\n  </main>\n\n  <footer>\n    PréstamoDesk · FieldLookers\n  </footer>\n\n  \n  \n  \n  \n", start: function(document, window, fetch, localStorage, location, setTimeout, clearTimeout) {
const API_BASE = "/api/v1";
const PRODUCT_BASE = "/products/prestamodesk";

let tenantId =
  localStorage.getItem("prestamodesk_tenant_id");

let selectedLoanId = null;
let paymentSubmitting = false;
let paymentNeedsReview = false;
let borrowers = [];
let loanBorrowerNames = new Map();
let loanBorrowerDocuments = new Map();
let loans = [];
let loanDetails = [];
let prospects = [];
let applications = [];
let prospectPage = null;
let lateFeePolicy = null;

const authPanel = document.getElementById("authPanel");
const workspace = document.getElementById("workspace");
const loginForm = document.getElementById("loginForm");
const loginEmail = document.getElementById("loginEmail");
const forgotPasswordButton =
  document.getElementById("forgotPasswordButton");
const passwordResetRequestForm =
  document.getElementById("passwordResetRequestForm");
const passwordResetEmail =
  document.getElementById("passwordResetEmail");
const passwordResetRequestButton =
  document.getElementById("passwordResetRequestButton");
const backToSignInButton =
  document.getElementById("backToSignInButton");
const logoutButton = document.getElementById("logoutButton");
const clientContext = document.getElementById("clientContext");
const healthStatus = document.getElementById("healthStatus");
const errorMessage = document.getElementById("errorMessage");
const successMessage = document.getElementById("successMessage");
const borrowerForm = document.getElementById("borrowerForm");
const loanForm = document.getElementById("loanForm");
const loanLateFeeEnabled =
  document.getElementById("loanLateFeeEnabled");
const loanType = document.getElementById("loanType");
const loanPrincipal =
  document.getElementById("loanPrincipal");
const vehicleLoanFields =
  document.getElementById("vehicleLoanFields");
const vehicleCashPrice =
  document.getElementById("vehicleCashPrice");
const vehicleDownPayment =
  document.getElementById("vehicleDownPayment");
const paymentForm = document.getElementById("paymentForm");
const borrowerList = document.getElementById("borrowerList");
const loanList = document.getElementById("loanList");
const applicationList =
  document.getElementById("applicationList");
const prospectList =
  document.getElementById("prospectList");
const publicProspectPageLink =
  document.getElementById("publicProspectPageLink");
const loanBorrower = document.getElementById("loanBorrower");
const loanBorrowerSearch = document.getElementById("loanBorrowerSearch");
const loanBorrowerSearchClear = document.getElementById("loanBorrowerSearchClear");
const loanBorrowerSearchStatus = document.getElementById("loanBorrowerSearchStatus");
let borrowerOptionsTenantId = null;
const loanDetailPanel =
  document.getElementById("loanDetailPanel");
const loanDetailTitle =
  document.getElementById("loanDetailTitle");
const loanDetailSummary =
  document.getElementById("loanDetailSummary");
const loanLateFeeForm =
  document.getElementById("loanLateFeeForm");
const loanLateFeeSelected =
  document.getElementById("loanLateFeeSelected");
const installmentList =
  document.getElementById("installmentList");
const paymentPanel =
  document.getElementById("paymentPanel");
const paymentInstallment =
  document.getElementById("paymentInstallment");
const receiptPanel =
  document.getElementById("receiptPanel");
const receiptContent =
  document.getElementById("receiptContent");
const lateFeePolicyForm =
  document.getElementById("lateFeePolicyForm");
const lateFeeEnabled =
  document.getElementById("lateFeeEnabled");
const lateFeeDailyRate =
  document.getElementById("lateFeeDailyRate");
const lateFeeGraceDays =
  document.getElementById("lateFeeGraceDays");
const lateFeeCapPercent =
  document.getElementById("lateFeeCapPercent");
const lateFeeEffectiveDate =
  document.getElementById("lateFeeEffectiveDate");
const lateFeePolicyStatus =
  document.getElementById("lateFeePolicyStatus");


function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}


function formatMoney(value) {
  return new Intl.NumberFormat(
    "es-DO",
    {
      style: "currency",
      currency: "DOP"
    }
  ).format(Number(value || 0));
}


function formatStatus(value) {
  const labels = {
    active: "Activo",
    inactive: "Inactivo",
    paid: "Pagado",
    cancelled: "Cancelado",
    pending: "Pendiente",
    partial: "Parcial",
    overdue: "Vencida",
    new: "Nueva",
    reviewing: "En revisión",
    approved: "Aprobada",
    contacted: "Contactado",
    qualified: "Calificado",
    rejected: "Rechazado",
    converted: "Convertido"
  };

  return labels[value] || value;
}


function setAuthenticatedUI(authenticated) {
  authPanel.hidden = authenticated;
  workspace.hidden = !authenticated;
  logoutButton.hidden = !authenticated;
  clientContext.hidden = !authenticated;
}


function optionalInputValue(elementId) {
  return (
    document.getElementById(elementId).value.trim()
    || null
  );
}


function updateVehicleFinancedAmount() {
  if (loanType.value !== "vehicle") {
    return;
  }

  const cashPrice = Number(vehicleCashPrice.value);
  const downPayment = Number(
    vehicleDownPayment.value || 0
  );

  if (
    !Number.isFinite(cashPrice)
    || cashPrice <= 0
    || !Number.isFinite(downPayment)
    || downPayment < 0
    || downPayment > cashPrice
  ) {
    loanPrincipal.value = "";
    return;
  }

  loanPrincipal.value = (
    cashPrice - downPayment
  ).toFixed(2);
}


function updateVehicleLoanFields() {
  const isVehicle = loanType.value === "vehicle";

  vehicleLoanFields.hidden = !isVehicle;
  loanPrincipal.readOnly = isVehicle;

  for (const element of vehicleLoanFields.querySelectorAll(
    "input"
  )) {
    element.required = false;
  }

  if (!isVehicle) {
    loanPrincipal.value = "";
    return;
  }

  for (const elementId of (
    "vehicleCashPrice",
    "vehicleDownPayment",
    "vehicleMake",
    "vehicleModel",
    "vehicleYear"
  )) {
    document.getElementById(elementId).required = true;
  }

  updateVehicleFinancedAmount();
}


function buildLoanPayload() {
  const payload = {
    borrower_id: Number(loanBorrower.value),
    loan_type: loanType.value,
    principal_amount: loanPrincipal.value,
    flat_interest_rate_percent:
      document.getElementById("loanRate").value,
    installment_count: Number(
      document.getElementById(
        "loanInstallments"
      ).value
    ),
    payment_frequency:
      document.getElementById("loanFrequency").value,
    start_date:
      document.getElementById("loanStartDate").value,
    first_payment_date:
      document.getElementById(
        "loanFirstPaymentDate"
      ).value,
    late_fee_enabled: loanLateFeeEnabled.checked
  };

  if (loanType.value === "vehicle") {
    Object.assign(
      payload,
      {
        vehicle_cash_price: vehicleCashPrice.value,
        vehicle_down_payment:
          vehicleDownPayment.value,
        vehicle_make:
          optionalInputValue("vehicleMake"),
        vehicle_model:
          optionalInputValue("vehicleModel"),
        vehicle_year: Number(
          document.getElementById(
            "vehicleYear"
          ).value
        ),
        vehicle_color:
          optionalInputValue("vehicleColor"),
        vehicle_vin:
          optionalInputValue("vehicleVin"),
        vehicle_license_plate:
          optionalInputValue("vehicleLicensePlate"),
        vehicle_seller:
          optionalInputValue("vehicleSeller"),
        vehicle_notes:
          optionalInputValue("vehicleNotes")
      }
    );
  }

  return payload;
}


function showError(message) {
  errorMessage.textContent = "";
  errorMessage.hidden = false;
  errorMessage.textContent = message;
  successMessage.hidden = true;
  if (errorMessage.isConnected && !errorMessage.closest("[hidden]")) {
    errorMessage.scrollIntoView?.({behavior: "instant", block: "center", inline: "nearest"});
  }
}


function showSuccess(message) {
  successMessage.textContent = message;
  successMessage.hidden = false;
  errorMessage.hidden = true;

  window.setTimeout(() => {
    successMessage.hidden = true;
  }, 3500);
}


async function apiRequest(path, options = {}) {
  const response = await fetch(
    `${API_BASE}${path}`,
    {
      headers: {
        "Content-Type": "application/json",
        ...(tenantId
          ? {"X-Tenant-ID": tenantId}
          : {}),
        ...(options.headers || {})
      },
      ...options
    }
  );

  if (!response.ok) {
    let detail = `Solicitud fallida (${response.status})`;

    try {
      const body = await response.json();

      if (typeof body.detail === "string") {
        detail = body.detail;
      }
    } catch {
      // Preserve the safe default.
    }

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
    const error = new Error(spanishApiError(detail, response.status));
    error.status = response.status;
    error.detail = detail;
    throw error;
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}


async function checkHealth() {
  try {
    const health = await apiRequest("/health");
    healthStatus.textContent = `API: ${health.status}`;
  } catch {
    healthStatus.textContent = "API no disponible";
  }
}


async function discoverAccess() {
  const access = await apiRequest(
    "/auth/products/prestamodesk/access"
  );

  if (access.clients.length === 0) {
    throw new Error(
      "Su cuenta no tiene acceso activo a PréstamoDesk."
    );
  }

  if (access.clients.length > 1) {
    throw new Error(
      "Su cuenta tiene varios clientes. "
      + "La selección de cliente aún no está disponible."
    );
  }

  const client = access.clients[0];

  if (client.role === "collector") {
    window.location.replace(
      "/prestamodesk/cobros"
    );
    return;
  }
  if (client.role === "supervisor") {
    window.location.replace("/prestamodesk/cobros/supervision");
    return;
  }
  if (client.role === "cashier") {
    window.location.replace("/prestamodesk/caja");
    return;
  }
  tenantId = String(client.tenant_id);
  window.prestamodeskAccess = client;
  window.dispatchEvent(new CustomEvent("prestamodesk-access", {detail: client}));

  localStorage.setItem(
    "prestamodesk_tenant_id",
    tenantId
  );

  clientContext.textContent =
    `Cliente #${client.client_number} · `
    + `${client.name} · ${client.role}`;
}


function canManageLoans() {
  return ["owner", "administrator"].includes(window.prestamodeskAccess?.role);
}

function applyLoanAccess() {
  const manage = canManageLoans();
  for (const id of ["borrowerForm", "loanForm", "applicationList", "prospectList", "borrowerList", "lateFeePolicyForm"]) {
    const panel = document.getElementById(id).closest("section");
    panel.hidden = !manage;
    if (!manage) for (const control of panel.querySelectorAll("input, select, textarea, button")) control.disabled = true;
  }
  for (const id of ["openApplicationCount", "borrowerCount"]) document.getElementById(id).closest("article").hidden = !manage;
  applyCompactAccess(manage);
  loanLateFeeForm.hidden = !manage;
  loanLateFeeForm.nextElementSibling.hidden = !manage;
  if (!manage) for (const control of loanLateFeeForm.querySelectorAll("input, button")) control.disabled = true;
}

function borrowerNameForLoan(loan) {
  return borrowers.find(item => item.id === loan.borrower_id)?.full_name
    || loanBorrowerNames.get(loan.id)
    || `Prestatario #${loan.borrower_id}`;
}


function renderBorrowerOptions() {
  if (borrowerOptionsTenantId !== tenantId) {
    borrowerOptionsTenantId = tenantId;
    loanBorrowerSearch.value = "";
    loanBorrower.value = "";
  }
  const manage = canManageLoans();
  const active = manage ? borrowers.filter(item => item.status === "active") : [];
  const selected = active.find(item => String(item.id) === loanBorrower.value);
  const query = normalizeLoanSearch(loanBorrowerSearch.value);
  const compactQuery = query.replace(/[^a-z0-9]/g, "");
  const matches = active.filter(item => {
    if (!query) return true;
    const name = normalizeLoanSearch(item.full_name);
    const documentNumber = normalizeLoanSearch(item.document_number);
    return name.includes(query) || documentNumber.includes(query)
      || Boolean(compactQuery && documentNumber.replace(/[^a-z0-9]/g, "").includes(compactQuery));
  });
  const outsideSearch = selected && !matches.some(item => item.id === selected.id);
  const options = outsideSearch ? [selected, ...matches] : matches;
  const placeholder = document.createElement("option");
  placeholder.value = "";
  placeholder.textContent = active.length ? "Seleccione…" : "No hay prestatarios activos";
  loanBorrower.replaceChildren(placeholder);
  for (const item of options) {
    const option = document.createElement("option");
    option.value = String(item.id);
    option.textContent = item.full_name + (item.document_number ? " · " + item.document_number : "")
      + (outsideSearch && item.id === selected.id ? " · Selección actual" : "");
    loanBorrower.append(option);
  }
  loanBorrower.value = selected ? String(selected.id) : "";
  loanBorrower.disabled = active.length === 0;
  loanBorrowerSearch.disabled = !manage || active.length === 0;
  loanBorrowerSearchClear.disabled = !manage || !loanBorrowerSearch.value;
  loanBorrowerSearchStatus.textContent = !manage ? "" : active.length === 0
    ? "No hay prestatarios activos. Cree o active un prestatario antes de crear el préstamo."
    : matches.length + " coincidencias de " + active.length + " prestatarios activos."
      + (outsideSearch ? " Se conserva el prestatario seleccionado, aunque no coincide con la búsqueda." : "");
}

loanBorrowerSearch.addEventListener("input", renderBorrowerOptions);
loanBorrowerSearch.addEventListener("keydown", event => {
  if (event.key === "Enter") event.preventDefault();
});
loanBorrowerSearchClear.addEventListener("click", () => {
  loanBorrowerSearch.value = "";
  renderBorrowerOptions();
  loanBorrowerSearch.focus();
});
loanBorrower.addEventListener("change", renderBorrowerOptions);


function renderApplications() {
  document.getElementById(
    "applicationResultCount"
  ).textContent = String(applications.length);

  if (applications.length === 0) {
    applicationList.innerHTML = `
      <p class="notice">
        No hay solicitudes de préstamo.
      </p>
    `;
    return;
  }

  applicationList.innerHTML = applications
    .map(application => {
      let actions = "";

      if (application.status === "new") {
        actions = `
          <button
            type="button"
            data-application-status="reviewing"
            data-application-id="${application.id}"
          >
            Iniciar revisión
          </button>
        `;
      } else if (application.status === "reviewing") {
        actions = `
          <button
            type="button"
            data-application-status="approved"
            data-application-id="${application.id}"
          >
            Aprobar
          </button>
          <button
            type="button"
            class="secondary"
            data-application-status="rejected"
            data-application-id="${application.id}"
          >
            Rechazar
          </button>
        `;
      } else if (application.status === "approved") {
        actions = `
          <button
            type="button"
            data-convert-application="${application.id}"
          >
            Convertir en préstamo
          </button>
        `;
      } else if (
        application.status === "converted"
        && application.converted_loan_id
      ) {
        actions = `
          <button
            type="button"
            data-application-loan="${
              application.converted_loan_id
            }"
          >
            Ver préstamo
          </button>
        `;
      }

      const contact = [
        application.phone,
        application.email
      ].filter(Boolean).join(" · ");

      const vehicle = [
        application.vehicle_make,
        application.vehicle_model,
        application.vehicle_year
      ].filter(Boolean).join(" ");

      return `
        <article class="item-card">
          <div class="section-heading">
            <h3>
              Solicitud #${application.id}
              · ${escapeHtml(application.full_name)}
            </h3>
            <span class="badge">
              ${escapeHtml(
                formatStatus(application.status)
              )}
            </span>
          </div>

          <div class="item-meta">
            <span>
              ${escapeHtml(
                application.document_type
              )}:
              ${escapeHtml(
                application.document_number || "No indicado"
              )}
            </span>
            ${
              contact
                ? `<span>${escapeHtml(contact)}</span>`
                : ""
            }
            <span>Tipo: ${application.loan_type === "vehicle" ? "Vehículo" : "Personal"}</span>
            ${application.source_prospect_id ? `<span>Prospecto #${application.source_prospect_id}</span>` : ""}
            ${application.loan_type === "vehicle" ? `
            <span>Vehículo: ${escapeHtml(vehicle)}</span>
            <span>Precio: ${formatMoney(application.vehicle_cash_price)}</span>
            <span>Inicial: ${formatMoney(application.vehicle_down_payment)}</span>
            ` : ""}
            <span>
              Financiado: ${formatMoney(
                application.principal_amount
              )}
            </span>
            <span>
              Interés: ${formatMoney(
                application.total_interest
              )}
            </span>
            <span>
              Total: ${formatMoney(
                application.total_due
              )}
            </span>
            <span>
              Cuotas: ${application.installment_count}
            </span>
          </div>

          <div class="item-actions">
            ${actions}
          </div>
        </article>
      `;
    })
    .join("");
}


document.getElementById("borrowerFilterForm").addEventListener("submit", event => event.preventDefault());
document.getElementById("borrowerSearchQuery").addEventListener("input", renderBorrowers);
document.getElementById("borrowerStatusFilter").addEventListener("change", renderBorrowers);
document.getElementById("borrowerFilterClear").addEventListener("click", () => {
  document.getElementById("borrowerSearchQuery").value = "";
  document.getElementById("borrowerStatusFilter").value = "all";
  renderBorrowers();
  document.getElementById("borrowerSearchQuery").focus();
});
let borrowerFilterTenantId = null;
function renderBorrowers() {
  const search = document.getElementById("borrowerSearchQuery");
  const status = document.getElementById("borrowerStatusFilter");
  if (borrowerFilterTenantId !== tenantId) {
    borrowerFilterTenantId = tenantId;
    search.value = "";
    status.value = "all";
  }
  const query = normalizeLoanSearch(search.value);
  const compactQuery = query.replace(/[^a-z0-9]/g, "");
  const matches = borrowers.filter(item => {
    if (status.value !== "all" && item.status !== status.value) return false;
    const name = normalizeLoanSearch(item.full_name);
    const number = normalizeLoanSearch(item.document_number);
    return !query || name.includes(query) || number.includes(query)
      || Boolean(compactQuery && number.replace(/[^a-z0-9]/g, "").includes(compactQuery));
  });
  document.getElementById("borrowerFilterResult").textContent =
    `Mostrando ${matches.length} de ${borrowers.length} prestatarios.`;
  document.getElementById(
    "borrowerCount"
  ).textContent = String(borrowers.length);

  document.getElementById(
    "borrowerResultCount"
  ).textContent = String(matches.length);

  if (borrowers.length === 0) {
    borrowerList.innerHTML =
      '<p>No hay prestatarios registrados.</p>';
    return;
  }

  if (matches.length === 0) {
    borrowerList.innerHTML = '<p>No hay prestatarios que coincidan con los filtros.</p>';
    return;
  }
  borrowerList.innerHTML = matches
    .map(item => `
      <article class="item-card">
        <h3>${escapeHtml(item.full_name)}</h3>
        <div class="item-meta">
          <span>${escapeHtml(
            formatStatus(item.status)
          )}</span>
          ${
            item.document_number
              ? `<span>Documento: ${
                  escapeHtml(item.document_number)
                }</span>`
              : ""
          }
          ${
            item.phone
              ? `<span>Teléfono: ${
                  escapeHtml(item.phone)
                }</span>`
              : ""
          }
          ${
            item.province
              ? `<span>Provincia: ${
                  escapeHtml(item.province)
                }</span>`
              : ""
          }
        </div>
        <div class="item-actions"><button type="button" class="secondary" data-view-borrower="${Number(item.id)}">Ver detalle</button></div>
      </article>
    `)
    .join("");

}


const contactFields = {phone:"Phone",email:"Email",address:"Address",municipality:"Municipality",province:"Province",notes:"Notes"};
const contactForm = document.getElementById("borrowerContactForm");
let contactSnapshot = null, contactBusy = false, contactDisposed = false;
function contactValues() {
  return Object.fromEntries(Object.entries(contactFields).map(([key,suffix]) => [key,document.getElementById("borrowerContact"+suffix).value.trim() || null]));
}
function contactDirty() {
  return !contactForm.hidden && contactSnapshot && JSON.stringify(contactValues()) !== JSON.stringify(contactSnapshot.values);
}
function contactMessage(text, error=false) {
  const box=document.getElementById("borrowerContactMessage");
  box.textContent="";box.setAttribute("role",error?"alert":"status");box.textContent=text;box.hidden=!text;
  if(error&&box.isConnected&&!box.closest("[hidden]"))box.scrollIntoView?.({behavior:"instant",block:"center"});
}
function contactControls() {
  for(const control of contactForm.elements) control.disabled=contactBusy;
  document.getElementById("editBorrowerContact").disabled=contactBusy;
}
function resetContactEditor() {
  contactSnapshot=null;contactForm.reset();contactForm.hidden=true;contactMessage("");
}
function leaveContact() {
  if(contactBusy){contactMessage("Espere la confirmación antes de salir de la edición.",true);return false;}
  if(contactDirty()&&!window.confirm("Hay cambios de contacto sin guardar. ¿Desea descartarlos?"))return false;
  resetContactEditor();return true;
}
window.prestamodeskBorrowerContact={
  canLeave:()=>!contactBusy&&!contactDirty(),
  confirmLeave:()=>leaveContact(),
  leaveMessage:"Guarde o descarte los cambios de contacto antes de cambiar de sección."
};
window.addEventListener("beforeunload",event=>{if(contactBusy||contactDirty()){event.preventDefault();event.returnValue="";}});
window.addEventListener("pd-dispose",()=>{contactDisposed=true;resetContactEditor();});
async function startContactEditor() {
  if(!canManageLoans()||!selectedBorrowerId||borrowerDetailTenantId!==tenantId||!leaveContact())return;
  const id=selectedBorrowerId,tenant=tenantId;
  contactBusy=true;contactControls();
  try {
    const record=await apiRequest(`${PRODUCT_BASE}/borrowers/${id}`);
    if(contactDisposed||tenant!==tenantId||id!==selectedBorrowerId||!canManageLoans())return;
    borrowers=borrowers.map(item=>item.id===id?record:item);renderBorrowerDetail();
    for(const [key,suffix] of Object.entries(contactFields))document.getElementById("borrowerContact"+suffix).value=record[key]||"";
    contactSnapshot={id,tenant,updated_at:record.updated_at,values:contactValues()};
    contactForm.hidden=false;document.getElementById("borrowerContactPhone").focus();
  } catch(error) {
    if(!contactDisposed&&tenant===tenantId)contactMessage(error.message||"No se pudo cargar el contacto.",true);
  } finally {contactBusy=false;contactControls();}
}
document.getElementById("editBorrowerContact").addEventListener("click",startContactEditor);
document.getElementById("refreshBorrowerContact").addEventListener("click",startContactEditor);
document.getElementById("cancelBorrowerContact").addEventListener("click",()=>{if(leaveContact())document.getElementById("editBorrowerContact").focus();});
contactForm.addEventListener("submit",async event=>{
  event.preventDefault();
  if(contactBusy||!contactSnapshot||!canManageLoans()||contactSnapshot.tenant!==tenantId||contactSnapshot.id!==selectedBorrowerId)return;
  if(!contactForm.reportValidity())return;
  if(!contactDirty()){contactMessage("No hay cambios de contacto para guardar.");return;}
  const snapshot=contactSnapshot;
  contactBusy=true;contactControls();contactMessage("");
  try {
    const record=await apiRequest(`${PRODUCT_BASE}/borrowers/${snapshot.id}/contact`,{method:"PATCH",body:JSON.stringify({expected_updated_at:snapshot.updated_at,...contactValues()})});
    if(contactDisposed||snapshot.tenant!==tenantId||snapshot.id!==selectedBorrowerId)return;
    borrowers=borrowers.map(item=>item.id===snapshot.id?record:item);resetContactEditor();renderBorrowers();renderBorrowerDetail();
    contactMessage("Contacto guardado.");document.getElementById("editBorrowerContact").focus();
  } catch(error) {
    if(!contactDisposed&&snapshot.tenant===tenantId)contactMessage(error.status===409
      ? "El prestatario cambió desde que abrió la edición. Sus cambios se conservan. Use Actualizar datos para revisar la versión actual antes de guardar."
      : error.status ? error.message : "No se pudo confirmar el guardado. Sus cambios se conservan. Actualice los datos para comprobar el resultado antes de volver a guardar.",true);
  } finally {contactBusy=false;contactControls();}
});

let borrowerStatementLoadedAt = null;
function clearBorrowerStatement() {
  document.body.classList.remove("pd-borrower-print");
  document.getElementById("borrowerStatementPanel").hidden=true;
  document.getElementById("borrowerStatementContent").replaceChildren();
}
function statementCents(value) {
  const text=String(value);
  if(!/^\d+(?:\.\d{1,2})?$/.test(text))throw new Error("No se pudo preparar el estado de cuenta: revise los importes del préstamo.");
  const [whole,fraction=""]=text.split(".");const cents=Number(whole)*100+Number(fraction.padEnd(2,"0"));
  if(!Number.isSafeInteger(cents))throw new Error("El importe supera el límite del estado de cuenta.");return cents;
}
function statementSum(values) {
  const total=values.reduce((sum,value)=>sum+value,0);
  if(!Number.isSafeInteger(total))throw new Error("El total supera el límite del estado de cuenta.");return total;
}
function buildBorrowerStatement() {
  if(!canManageLoans()||borrowerDetailTenantId!==tenantId)return;
  if(contactBusy||contactDirty()){contactMessage("Guarde o descarte los cambios de contacto antes de preparar el estado de cuenta.",true);return;}
  const borrower=borrowers.find(item=>item.id===selectedBorrowerId);if(!borrower)return;
  const today=loanPortfolioToday(), client=window.prestamodeskAccess;
  const linked=loanDetails.filter(loan=>loan.borrower_id===borrower.id).sort((a,b)=>a.id-b.id);
  try {
    const rows=linked.map(loan=>{
      const amounts=loan.installments.map(item=>({due:statementCents(item.total_due),paid:statementCents(item.paid_amount),date:item.due_date}));
      if(amounts.some(item=>item.paid>item.due))throw new Error("No se pudo preparar el estado de cuenta: revise los saldos de las cuotas.");
      return {loan,total:statementSum(amounts.map(item=>item.due)),paid:statementSum(amounts.map(item=>item.paid)),
        balance:statementSum(amounts.map(item=>item.due-item.paid)),overdue:loan.status==='active'?statementSum(amounts.filter(item=>item.date<today).map(item=>item.due-item.paid)):0};
    });
    const active=rows.filter(row=>row.loan.status==='active');
    const ordinary=rows.filter(row=>row.loan.status!=='cancelled');
    const money=cents=>formatMoney(cents/100);
    const escape=escapeHtml;
    document.getElementById("borrowerStatementContent").innerHTML=`
      <p>PréstamoDesk · by FieldLookers</p>
      <h2 id="borrowerStatementTitle" tabindex="-1">Estado de cuenta</h2>
      <p>${escape(client.name)} · Cliente #${escape(String(client.client_number))}</p>
      <h3>${escape(borrower.full_name)}</h3>
      <p>Documento: ${escape(borrower.document_number||"No registrado")} · Teléfono: ${escape(borrower.phone||"No registrado")}</p>
      <p>Correo: ${escape(borrower.email||"No registrado")}</p>
      <p>Fecha de consulta: ${escape(today)} · República Dominicana · DOP</p>
      <p>Datos cargados: ${escape(borrowerStatementLoadedAt||"No disponible")} (UTC). Actualice la sección para consultar cambios posteriores.</p>
      <p><strong>Saldo ordinario pendiente (préstamos activos): ${money(statementSum(active.map(row=>row.balance)))}</strong></p>
      <p>Saldo ordinario vencido: ${money(statementSum(active.map(row=>row.overdue)))} · Pagado a cuotas (sin préstamos cancelados): ${money(statementSum(ordinary.map(row=>row.paid)))}</p>
      <p>Los importes no incluyen mora. Pagado a cuotas corresponde al capital e interés aplicado, no al total de recibos. Los préstamos cancelados se muestran como referencia y se excluyen de los totales.</p>
      ${rows.length?`<div class="table-wrap"><table><thead><tr><th>Préstamo</th><th>Estado</th><th>Total cuotas</th><th>Pagado a cuotas</th><th>Saldo ordinario</th></tr></thead><tbody>${rows.map(row=>`<tr><td>#${row.loan.id} · ${row.loan.loan_type==='vehicle'?'Vehículo':'Personal'}</td><td>${escape(formatStatus(row.loan.status))}</td><td>${money(row.total)}</td><td>${row.loan.status==='cancelled'?'—':money(row.paid)}</td><td>${row.loan.status==='cancelled'?'—':money(row.balance)}</td></tr>`).join('')}</tbody></table></div>`:'<p>No hay préstamos para este prestatario.</p>'}
      <p>Préstamos: ${rows.length} · Activos: ${active.length}</p>`;
    document.getElementById("borrowerStatementPanel").hidden=false;
    document.getElementById("borrowerStatementTitle").focus();
  }catch(error){clearBorrowerStatement();showError(error.message);}
}
document.getElementById("openBorrowerStatement").addEventListener("click",buildBorrowerStatement);
document.getElementById("closeBorrowerStatement").addEventListener("click",()=>{clearBorrowerStatement();document.getElementById("openBorrowerStatement").focus();});
document.getElementById("printBorrowerStatement").addEventListener("click",()=>{
  if(!canManageLoans()||borrowerDetailTenantId!==tenantId||contactBusy||contactDirty()||document.getElementById("borrowerStatementPanel").hidden)return;
  document.body.classList.add("pd-borrower-print");
  try{window.print();}finally{document.body.classList.remove("pd-borrower-print");}
});
window.addEventListener("afterprint",()=>document.body.classList.remove("pd-borrower-print"));

let selectedBorrowerId = null;
let borrowerDetailTenantId = null;
function clearBorrowerDetail() {
  clearBorrowerStatement();
  resetContactEditor();
  selectedBorrowerId = null;
  borrowerDetailTenantId = null;
  document.getElementById("borrowerDetailPanel").hidden = true;
  for (const id of ["borrowerDetailTitle", "borrowerContactDetails", "borrowerBalanceSummary", "borrowerLoanList"]) document.getElementById(id).replaceChildren();
}
let loanCreationPending = false;
let loanCreationRequest = null;
let loanCreationStorageBlocked = false;
let loanCreationDisabled = null;
function loanCreationStorageKey(){return "prestamodesk_loan_creation_v1:"+tenantId;}
function loanCreationControls(){
  const blocked = loanCreationPending || !!loanCreationRequest || loanCreationStorageBlocked;
  if (blocked && canManageLoans()) openCompactForm("compactLoanForm");
  const fields = [...loanForm.querySelectorAll("button,input,select,textarea")];
  if(blocked && !loanCreationDisabled) loanCreationDisabled = fields.map(field=>[field,field.disabled]);
  if(blocked) fields.forEach(field=>{field.disabled=true;});
  else if(loanCreationDisabled){loanCreationDisabled.forEach(([field,disabled])=>{field.disabled=disabled;});loanCreationDisabled=null;}
  const notice=document.getElementById("loanCreationNotice");
  notice.hidden=!blocked;
  notice.textContent=loanCreationStorageBlocked ? "No se pudo leer la solicitud pendiente. No cree otro préstamo; revise esta sesión antes de continuar." : loanCreationPending ? "Creando o confirmando el préstamo. Espere el resultado." : loanCreationRequest ? "Hay una solicitud de préstamo sin confirmar. No cree otra: use Confirmar o recuperar el préstamo para consultar el resultado con la misma solicitud." : "";
  const retry=document.getElementById("loanCreationRetry");retry.hidden=!loanCreationRequest;retry.disabled=loanCreationPending;
}
function restoreLoanCreation(){
  if(!loanCreationRequest && tenantId){
    try{
      const raw=sessionStorage.getItem(loanCreationStorageKey());
      if(raw){const request=JSON.parse(raw);if(typeof request.key!=="string" || !/^[a-f0-9-]{36}$/i.test(request.key) || !request.payload || typeof request.payload!=="object")throw new Error();loanCreationRequest=request;}
    }catch{loanCreationStorageBlocked=true;showError("No se pudo leer la solicitud de préstamo pendiente. No cree otro préstamo hasta revisar el almacenamiento de esta sesión.");}
  }
  loanCreationControls();
}
window.prestamodeskLoanCreation={canLeave:()=>!loanCreationPending&&!loanCreationRequest&&!loanCreationStorageBlocked,confirmLeave:()=>false,leaveMessage:"Confirme el resultado del préstamo pendiente antes de cambiar de sección."};
window.addEventListener("beforeunload",event=>{if(loanCreationPending||loanCreationRequest){event.preventDefault();event.returnValue="";}});

document.getElementById("borrowerNewLoan").addEventListener("click", () => {
  const borrower = borrowers.find(item => item.id === selectedBorrowerId);
  if (!canManageLoans() || borrowerDetailTenantId !== tenantId || !borrower || borrower.status !== "active" || loanCreationPending || loanCreationRequest) return;
  const previous = loanBorrower.value;
  if (previous && previous !== String(borrower.id) && !window.confirm("El formulario tiene otro prestatario seleccionado. ¿Desea cambiarlo? Los demás datos del préstamo se conservarán.")) return;
  if (!leaveContact()) return;
  clearBorrowerStatement();
  loanBorrowerSearch.value = "";
  renderBorrowerOptions();
  loanBorrower.value = String(borrower.id);
  renderBorrowerOptions();
  if (previous !== loanBorrower.value) loanBorrower.dispatchEvent(new Event("change", {bubbles:true}));
  openCompactForm("compactLoanForm");
  loanForm.scrollIntoView?.({behavior:"instant",block:"start"});
  loanBorrower.focus();
});
function renderBorrowerDetail() {
  clearBorrowerStatement();
  const borrower = borrowers.find(item => item.id === selectedBorrowerId);
  if (!canManageLoans() || borrowerDetailTenantId !== tenantId || !borrower) {
    clearBorrowerDetail(); return;
  }
  document.getElementById("borrowerNewLoan").hidden = borrower.status !== "active";
  const title = document.getElementById("borrowerDetailTitle");
  title.textContent = borrower.full_name;
  const contact = document.getElementById("borrowerContactDetails");
  contact.replaceChildren();
  const labels = {cedula:"Cédula", passport:"Pasaporte", other:"Otro"};
  for (const [label,value] of [
    ["Estado",formatStatus(borrower.status)],
    ["Tipo de documento",labels[borrower.document_type] || borrower.document_type],
    ["Documento",borrower.document_number],["Teléfono",borrower.phone],
    ["Correo",borrower.email],["Dirección",borrower.address],
    ["Municipio",borrower.municipality],["Provincia",borrower.province],
    ["Observaciones",borrower.notes]
  ]) {
    const field = document.createElement("span");
    field.textContent = label + ": " + (value || "No registrado");
    contact.append(field);
  }
  const linked = loanDetails.filter(loan => loan.borrower_id === borrower.id);
  const balance = loan => loan.installments.reduce((sum,item) => sum + Math.max(0,Number(item.total_due)-Number(item.paid_amount)),0);
  const active = linked.filter(loan => loan.status === "active");
  document.getElementById("borrowerBalanceSummary").textContent =
    `Préstamos: ${linked.length} · Activos: ${active.length} · Saldo ordinario pendiente: ${formatMoney(active.reduce((sum,loan)=>sum+balance(loan),0))}`;
  const list = document.getElementById("borrowerLoanList");
  list.replaceChildren();
  if (!linked.length) {
    const empty = document.createElement("p"); empty.textContent = "No hay préstamos para este prestatario."; list.append(empty);
  }
  for (const loan of linked) {
    const card = document.createElement("article"); card.className = "item-card";
    const heading = document.createElement("h4"); heading.textContent = "Préstamo #" + loan.id;
    const info = document.createElement("p");
    info.textContent = `${loan.loan_type === "vehicle" ? "Vehículo" : "Personal"} · ${formatStatus(loan.status)} · Financiado: ${formatMoney(loan.principal_amount)}`
      + (loan.status === "cancelled" ? "" : ` · Saldo ordinario: ${formatMoney(balance(loan))}`);
    const button = document.createElement("button"); button.type = "button"; button.className = "secondary";
    button.dataset.borrowerLoan = String(loan.id); button.textContent = "Ver préstamo";
    card.append(heading,info,button); list.append(card);
  }
  document.getElementById("borrowerDetailPanel").hidden = false;
}
borrowerList.addEventListener("click", event => {
  const button = event.target.closest("button[data-view-borrower]");
  if (!button || !canManageLoans() || !leaveContact()) return;
  selectedBorrowerId = Number(button.dataset.viewBorrower); borrowerDetailTenantId = tenantId;
  renderBorrowerDetail();
  if (!document.getElementById("borrowerDetailPanel").hidden) document.getElementById("borrowerDetailTitle").focus();
});
document.getElementById("closeBorrowerDetail").addEventListener("click", () => {
  if(!leaveContact())return;
  const button = [...borrowerList.querySelectorAll("[data-view-borrower]")].find(item => Number(item.dataset.viewBorrower) === selectedBorrowerId);
  clearBorrowerDetail();
  (button || document.getElementById("borrowerSearchQuery")).focus();
});
document.getElementById("borrowerLoanList").addEventListener("click", async event => {
  const button = event.target.closest("button[data-borrower-loan]");
  if (!button || !canManageLoans() || borrowerDetailTenantId !== tenantId) return;
  const id = Number(button.dataset.borrowerLoan);
  if (!loanDetails.some(loan=>loan.id===id && loan.borrower_id===selectedBorrowerId)) return;
  if(!leaveContact())return;
  await openLoan(id);
});

function renderProspects() {
  document.getElementById(
    "prospectResultCount"
  ).textContent = String(prospects.length);

  if (prospectPage) {
    publicProspectPageLink.href =
      `/prestamodesk/solicitar/${
        encodeURIComponent(prospectPage.tenant_slug)
      }`;
    publicProspectPageLink.hidden = false;
  } else {
    publicProspectPageLink.hidden = true;
  }

  if (prospects.length === 0) {
    prospectList.innerHTML =
      "<p>No hay prospectos registrados.</p>";
    return;
  }

  prospectList.innerHTML = prospects
    .map(item => {
      const actions = [];
      const linked = applications.find(application => application.source_prospect_id === item.id);

      if (
        !linked && (item.status === "new"
        || item.status === "contacted")
      ) {
        actions.push(`
          <button
            type="button"
            class="secondary"
            data-prospect-id="${item.id}"
            data-prospect-status="qualified"
          >
            Calificar
          </button>
        `);
      }

      if (!linked && item.status === "new") {
        actions.push(`
          <button
            type="button"
            class="secondary"
            data-prospect-id="${item.id}"
            data-prospect-status="contacted"
          >
            Marcar contactado
          </button>
        `);
      }

      if (
        !linked && item.status !== "rejected"
        && item.status !== "converted"
      ) {
        actions.push(`
          <button
            type="button"
            class="secondary"
            data-prospect-id="${item.id}"
            data-prospect-status="rejected"
          >
            Rechazar
          </button>
        `);
      }

      if (!linked && item.status === "qualified") {
        actions.push(`
          <button
            type="button"
            data-start-prospect-application="${item.id}"
          >
            Seleccionar tipo y preparar solicitud
          </button>
        `);
      }

      if (linked) {
        actions.push(`<span class="notice">Solicitud #${linked.id} · ${linked.loan_type === "vehicle" ? "Vehículo" : "Personal"} · ${escapeHtml(formatStatus(linked.status))}. Continúe en Solicitudes de préstamo.</span>`);
      }
      return `
        <article class="item-card">
          <h3>${escapeHtml(item.full_name)}</h3>
          <div class="item-meta">
            <span>
              ${escapeHtml(formatStatus(item.status))}
            </span>
            <span>
              Monto solicitado:
              ${formatMoney(item.requested_amount)}
            </span>
            <span>
              Teléfono: ${escapeHtml(item.phone)}
            </span>
            ${
              item.email
                ? `<span>Correo: ${
                    escapeHtml(item.email)
                  }</span>`
                : ""
            }
            ${
              item.province
                ? `<span>Provincia: ${
                    escapeHtml(item.province)
                  }</span>`
                : ""
            }
            <span>
              Contacto preferido:
              ${escapeHtml(item.preferred_contact)}
            </span>
          </div>
          ${
            item.message
              ? `<p>${escapeHtml(item.message)}</p>`
              : ""
          }
          <div class="item-actions">
            ${actions.join("")}
          </div>
        </article>
      `;
    })
    .join("");
}


function loanPortfolioToday() {
  const parts = new Intl.DateTimeFormat("en", {timeZone: "America/Santo_Domingo", year: "numeric", month: "2-digit", day: "2-digit"}).formatToParts(new Date());
  return ["year", "month", "day"].map(type => parts.find(part => part.type === type).value).join("-");
}

function normalizeLoanSearch(value) {
  return String(value || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("es-DO").replace(/\s+/g, " ").trim();
}

function filteredLoans() {
  const query = normalizeLoanSearch(document.getElementById("loanSearchQuery").value);
  const compactQuery = query.replace(/[^a-z0-9]/g, "");
  const status = document.getElementById("loanStatusFilter").value;
  const today = loanPortfolioToday();
  const overdueIds = new Set(loanDetails.filter(detail => detail.status === "active" && detail.installments.some(item =>
    item.due_date < today && Number(item.total_due) - Number(item.paid_amount) > 0
  )).map(detail => detail.id));
  return loans.filter(loan => {
    if (status === "overdue" ? !overdueIds.has(loan.id) : status !== "all" && loan.status !== status) return false;
    if (!query) return true;
    const borrower = borrowers.find(item => item.id === loan.borrower_id);
    const documentNumber = borrower?.document_number || loanBorrowerDocuments.get(loan.id) || "";
    const searchable = normalizeLoanSearch(`${loan.id} #${loan.id} Préstamo #${loan.id} ${borrowerNameForLoan(loan)} ${documentNumber}`);
    return searchable.includes(query) || Boolean(compactQuery && normalizeLoanSearch(documentNumber).replace(/[^a-z0-9]/g, "").includes(compactQuery));
  });
}

function renderLoans() {
  const visibleLoans = filteredLoans();
  document.getElementById("loanFilterResult").textContent = `Mostrando ${visibleLoans.length} de ${loans.length} préstamos.`;
  document.getElementById(
    "loanResultCount"
  ).textContent = String(visibleLoans.length);

  const activeLoans = loans.filter(
    loan => loan.status === "active"
  );

  document.getElementById(
    "activeLoanCount"
  ).textContent = String(activeLoans.length);

  if (visibleLoans.length === 0) {
    loanList.innerHTML =
      loans.length === 0 ? '<p>No hay préstamos registrados.</p>' : '<p>No hay préstamos que coincidan con los filtros.</p>';
    return;
  }

  loanList.innerHTML = visibleLoans
    .map(loan => {

      const vehicleDescription = (
        loan.loan_type === "vehicle"
          ? `
            <span>
              Vehículo:
              ${escapeHtml(loan.vehicle_make)}
              ${escapeHtml(loan.vehicle_model)}
              ${escapeHtml(loan.vehicle_year)}
            </span>
          `
          : ""
      );

      return `
        <article class="item-card">
          <h3>
            Préstamo #${loan.id}
            · ${escapeHtml(
              borrowerNameForLoan(loan)
            )}
          </h3>
          <div class="item-meta">
            <span>
              Tipo: ${
                loan.loan_type === "vehicle"
                  ? "Vehículo"
                  : "Personal"
              }
            </span>
            ${vehicleDescription}
            <span>
              Financiado: ${formatMoney(
                loan.principal_amount
              )}
            </span>
            <span>
              Total: ${formatMoney(loan.total_due)}
            </span>
            <span>
              ${loan.installment_count} cuotas
            </span>
            <span>
              ${escapeHtml(
                formatStatus(loan.status)
              )}
            </span>
            <span>
              Mora: ${
                loan.late_fee_enabled
                  ? "Activada"
                  : "No activada"
              }
            </span>
          </div>
          <div class="item-actions">
            <button
              type="button"
              data-view-loan="${loan.id}"
            >
              Ver préstamo
            </button>
          </div>
        </article>
      `;
    })
    .join("");
}


const loanFilterForm = document.getElementById("loanFilterForm");
loanFilterForm.addEventListener("submit", event => {event.preventDefault(); renderLoans();});
document.getElementById("loanSearchQuery").addEventListener("input", renderLoans);
document.getElementById("loanStatusFilter").addEventListener("change", renderLoans);
document.getElementById("loanFilterClear").addEventListener("click", () => {
  loanFilterForm.reset(); renderLoans(); document.getElementById("loanSearchQuery").focus();
});


function updatePortfolioSummary() {
  const today = loanPortfolioToday();

  document.getElementById(
    "openApplicationCount"
  ).textContent = String(
    applications.filter(
      item => !["rejected", "converted"].includes(
        item.status
      )
    ).length
  );

  let outstanding = 0;
  let overdue = 0;

  for (const detail of loanDetails) {
    for (const item of detail.installments) {
      const balance =
        Number(item.total_due)
        - Number(item.paid_amount);

      outstanding += balance;

      if (
        balance > 0
        && item.due_date < today
      ) {
        overdue += 1;
      }
    }
  }

  document.getElementById(
    "outstandingBalance"
  ).textContent = formatMoney(outstanding);

  document.getElementById(
    "overdueCount"
  ).textContent = String(overdue);
}


function setDefaultLateFeePolicy() {
  lateFeePolicy = null;
  lateFeeEnabled.checked = false;
  lateFeeDailyRate.value = "0.1000";
  lateFeeGraceDays.value = "5";
  lateFeeCapPercent.value = "25.0000";

  if (!lateFeeEffectiveDate.value) {
    lateFeeEffectiveDate.value =
      new Date().toISOString().slice(0, 10);
  }

  lateFeePolicyStatus.textContent =
    "No configurada. Guarde para crear la política.";
}


function renderLateFeePolicy(policy) {
  lateFeePolicy = policy;
  lateFeeEnabled.checked = policy.enabled;
  lateFeeDailyRate.value = policy.daily_rate_percent;
  lateFeeGraceDays.value = policy.grace_days;
  lateFeeCapPercent.value = policy.cap_percent;
  lateFeeEffectiveDate.value = policy.effective_date;

  lateFeePolicyStatus.textContent = policy.enabled
    ? (
      "Mora activa desde "
      + policy.effective_date
      + "."
    )
    : "Política guardada, pero la mora está desactivada.";
}


async function loadLateFeePolicy() {
  try {
    const policy = await apiRequest(
      `${PRODUCT_BASE}/late-fee-policy`
    );
    renderLateFeePolicy(policy);
  } catch (error) {
    if (error.status === 404) {
      setDefaultLateFeePolicy();
      return;
    }

    throw error;
  }
}


async function loadDashboard() {
  invalidateLoanPreview();
  if (borrowerDetailTenantId !== tenantId || !canManageLoans()) clearBorrowerDetail();
  applyLoanAccess();
  loanBorrowerNames = new Map();
  loanBorrowerDocuments = new Map();
  if (canManageLoans()) {
    [borrowers, loans, prospects, applications, prospectPage] = await Promise.all([
      apiRequest(`${PRODUCT_BASE}/borrowers`),
      apiRequest(`${PRODUCT_BASE}/loans`),
      apiRequest(`${PRODUCT_BASE}/prospects`),
      apiRequest(`${PRODUCT_BASE}/applications`),
      apiRequest(`${PRODUCT_BASE}/prospects/public-page`)
    ]);
    await loadLateFeePolicy();
  } else {
    borrowers = []; prospects = []; applications = []; prospectPage = null; lateFeePolicy = null;
    const [readableLoans, cashierLoans] = await Promise.all([
      apiRequest(`${PRODUCT_BASE}/loans`),
      apiRequest(`${PRODUCT_BASE}/cashier/loans`)
    ]);
    loans = readableLoans;
    loanBorrowerNames = new Map(cashierLoans.map(loan => [loan.id, loan.borrower_full_name]));
    loanBorrowerDocuments = new Map(cashierLoans.map(loan => [loan.id, loan.borrower_document_number || ""]));
  }

  loanDetails = await Promise.all(
    loans.map(
      loan => apiRequest(
        `${PRODUCT_BASE}/loans/${loan.id}`
      )
    )
  );

  renderApplications();
  renderProspects();
  renderBorrowers();
  renderBorrowerOptions();
  renderLoans();
  document.getElementById("compactLoanCount").textContent = String(loans.length);
  document.getElementById("compactBorrowerCount").textContent = String(borrowers.length);
  document.getElementById("compactApplicationCount").textContent = String(applications.filter(item => !["rejected", "converted"].includes(item.status)).length);
  updatePortfolioSummary();
  borrowerStatementLoadedAt = new Date().toISOString();
  renderBorrowerDetail();
  restoreLoanCreation();
}


function renderLoanDetail(detail) {

  loanDetailTitle.textContent =
    `Préstamo #${detail.id} · `
    + borrowerNameForLoan(detail);

  const outstanding = detail.installments.reduce(
    (total, item) => (
      total
      + Number(item.total_due)
      - Number(item.paid_amount)
    ),
    0
  );

  const vehicleSummary = (
    detail.loan_type === "vehicle"
      ? `
        <h3>Vehículo financiado</h3>
        <div class="item-meta">
          <span>
            ${escapeHtml(detail.vehicle_make)}
            ${escapeHtml(detail.vehicle_model)}
            ${escapeHtml(detail.vehicle_year)}
          </span>
          <span>
            Precio: ${formatMoney(
              detail.vehicle_cash_price
            )}
          </span>
          <span>
            Inicial: ${formatMoney(
              detail.vehicle_down_payment
            )}
          </span>
          ${
            detail.vehicle_color
              ? `<span>Color: ${
                  escapeHtml(detail.vehicle_color)
                }</span>`
              : ""
          }
          ${
            detail.vehicle_vin
              ? `<span>VIN/chasis: ${
                  escapeHtml(detail.vehicle_vin)
                }</span>`
              : ""
          }
          ${
            detail.vehicle_license_plate
              ? `<span>Placa: ${
                  escapeHtml(
                    detail.vehicle_license_plate
                  )
                }</span>`
              : ""
          }
          ${
            detail.vehicle_seller
              ? `<span>Vendedor: ${
                  escapeHtml(detail.vehicle_seller)
                }</span>`
              : ""
          }
        </div>
        ${
          detail.vehicle_notes
            ? `<p>${escapeHtml(
                detail.vehicle_notes
              )}</p>`
            : ""
        }
      `
      : ""
  );

  loanDetailSummary.innerHTML = `
    <div class="item-meta">
      <span>
        Tipo: ${
          detail.loan_type === "vehicle"
            ? "Vehículo"
            : "Personal"
        }
      </span>
      <span>
        Financiado: ${formatMoney(
          detail.principal_amount
        )}
      </span>
      <span>
        Interés: ${formatMoney(detail.total_interest)}
      </span>
      <span>
        Total: ${formatMoney(detail.total_due)}
      </span>
      <span>
        Saldo: ${formatMoney(outstanding)}
      </span>
      <span>
        Estado: ${escapeHtml(
          formatStatus(detail.status)
        )}
      </span>
      <span>
        Mora: ${
          detail.late_fee_enabled
            ? "Activada"
            : "No activada"
        }
      </span>
    </div>
    ${vehicleSummary}
  `;

  loanLateFeeSelected.checked = (
    detail.late_fee_enabled
  );

  installmentList.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Cuota</th>
          <th>Vence</th>
          <th>Total</th>
          <th>Pagado</th>
          <th>Saldo</th>
          <th>Estado</th>
        </tr>
      </thead>
      <tbody>
        ${detail.installments.map(item => `
          <tr>
            <td>${item.sequence_number}</td>
            <td>${escapeHtml(item.due_date)}</td>
            <td>${formatMoney(item.total_due)}</td>
            <td>${formatMoney(item.paid_amount)}</td>
            <td>${formatMoney(
              Number(item.total_due)
              - Number(item.paid_amount)
            )}</td>
            <td>${escapeHtml(
              formatStatus(item.status)
            )}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;

  const payable = detail.installments.filter(
    item => (
      Number(item.total_due)
      > Number(item.paid_amount)
    )
  );

  paymentInstallment.innerHTML = payable
    .map(item => `
      <option
        value="${item.id}"
        data-balance="${
          Number(item.total_due)
          - Number(item.paid_amount)
        }"
      >
        Cuota ${item.sequence_number}
        · vence ${escapeHtml(item.due_date)}
        · ${formatMoney(
          Number(item.total_due)
          - Number(item.paid_amount)
        )}
      </option>
    `)
    .join("");

  setCompactTask("loans");
  loanDetailPanel.hidden = false;
  paymentPanel.hidden = (
    detail.status !== "active"
    || payable.length === 0
  );
  receiptPanel.hidden = true;
}


async function openLoan(loanId) {
  const detail = await apiRequest(
    `${PRODUCT_BASE}/loans/${loanId}`
  );

  selectedLoanId = loanId;
  renderLoanDetail(detail);
  await window.prestamodeskPaymentHistory?.load(loanId, window.prestamodeskAccess?.role);
  loanDetailPanel.scrollIntoView({
    behavior: "smooth",
    block: "start"
  });
}


loanLateFeeForm.addEventListener(
  "submit",
  async event => {
    event.preventDefault();
    clearMessages();

    if (!selectedLoanId) {
      showError("Seleccione un préstamo.");
      return;
    }

    const loanId = selectedLoanId;

    try {
      await apiRequest(
        `${PRODUCT_BASE}/loans/${loanId}/late-fee`,
        {
          method: "PUT",
          body: JSON.stringify({
            late_fee_enabled:
              loanLateFeeSelected.checked
          })
        }
      );

      await loadDashboard();
      await openLoan(loanId);
      showSuccess(
        "Selección de mora del préstamo guardada."
      );
    } catch (error) {
      showError(error.message);
    }
  }
);


lateFeePolicyForm.addEventListener(
  "submit",
  async event => {
    event.preventDefault();
    clearMessages();

    try {
      const policy = await apiRequest(
        `${PRODUCT_BASE}/late-fee-policy`,
        {
          method: "PUT",
          body: JSON.stringify({
            enabled: lateFeeEnabled.checked,
            daily_rate_percent:
              lateFeeDailyRate.value,
            grace_days: Number(
              lateFeeGraceDays.value
            ),
            cap_percent:
              lateFeeCapPercent.value,
            effective_date:
              lateFeeEffectiveDate.value
          })
        }
      );

      renderLateFeePolicy(policy);
      showSuccess("Política de mora guardada.");
    } catch (error) {
      showError(error.message);
    }
  }
);


borrowerForm.addEventListener(
  "submit",
  async event => {
    event.preventDefault();

    try {
      await apiRequest(
        `${PRODUCT_BASE}/borrowers`,
        {
          method: "POST",
          body: JSON.stringify({
            full_name:
              document.getElementById(
                "borrowerName"
              ).value.trim(),
            document_type:
              document.getElementById(
                "borrowerDocumentType"
              ).value,
            document_number:
              document.getElementById(
                "borrowerDocumentNumber"
              ).value.trim() || null,
            phone:
              document.getElementById(
                "borrowerPhone"
              ).value.trim() || null,
            municipality:
              document.getElementById(
                "borrowerMunicipality"
              ).value.trim() || null,
            province:
              document.getElementById(
                "borrowerProvince"
              ).value.trim() || null
          })
        }
      );

      borrowerForm.reset();
      await loadDashboard();
      showSuccess("Prestatario guardado.");
    } catch (error) {
      showError(error.message);
    }
  }
);


const loanPreviewButton = document.getElementById("loanPreviewButton");
const loanPreviewBox = document.getElementById("loanPreview");
const loanPreviewStatus = document.getElementById("loanPreviewStatus");
let loanPreviewVersion = 0;
let loanPreviewPrintSnapshot = null;
const loanPreviewPrintPanel = document.getElementById("loanPreviewPrintPanel");
function clearLoanPreviewPrint() {
  document.body.classList.remove("pd-loan-preview-print");
  loanPreviewPrintPanel.hidden = true;
  loanPreviewPrintPanel.replaceChildren();
}
function printLoanPreview() {
  if (!canManageLoans() || loanCreationPending || loanCreationRequest || loanCreationStorageBlocked || loanPreviewBox.hidden || !loanPreviewPrintSnapshot) return;
  if (loanPreviewPrintSnapshot.tenant !== tenantId || loanPreviewPrintSnapshot.payload !== JSON.stringify(buildLoanPayload())) {invalidateLoanPreview();return;}
  clearLoanPreviewPrint();
  const heading=document.createElement("h1");heading.textContent="PréstamoDesk · Propuesta de préstamo";loanPreviewPrintPanel.append(heading);
  const business=document.createElement("p");business.textContent=`Cliente #${window.prestamodeskAccess?.client_number || ""} · ${window.prestamodeskAccess?.name || clientContext.textContent}`;loanPreviewPrintPanel.append(business);
  const date=document.createElement("p");date.textContent="Vista previa calculada: " + loanPreviewPrintSnapshot.calculatedAt + " (República Dominicana).";loanPreviewPrintPanel.append(date);
  for (const child of loanPreviewBox.children) if (!child.classList.contains("loan-preview-actions") && !child.textContent.startsWith("Esta vista previa no crea")) loanPreviewPrintPanel.append(child.cloneNode(true));
  const note=document.createElement("p");note.textContent="Propuesta sin guardar. No es un contrato ni un recibo. Interés fijo total; no representa una tasa APR. No incluye mora acumulada. Los datos se validan nuevamente al crear el préstamo.";loanPreviewPrintPanel.append(note);
  loanPreviewPrintPanel.hidden=false;
  document.body.classList.remove("pd-borrower-print");
  document.body.classList.add("pd-loan-preview-print");
  try {window.print();} catch {showError("No se pudo abrir la impresión. Intente de nuevo.");} finally {clearLoanPreviewPrint();}
}
window.addEventListener("afterprint", clearLoanPreviewPrint);
function invalidateLoanPreview() {
  loanPreviewVersion++;
  loanPreviewPrintSnapshot=null;clearLoanPreviewPrint();
  loanPreviewBox.hidden = true;
  loanPreviewBox.replaceChildren();
  loanPreviewStatus.hidden = true;
}
loanForm.addEventListener("input", invalidateLoanPreview);
loanForm.addEventListener("change", invalidateLoanPreview);
loanForm.addEventListener("reset", invalidateLoanPreview);
loanPreviewButton.addEventListener("click", async () => {
  if (!canManageLoans() || loanCreationRequest || loanCreationPending || loanCreationStorageBlocked) return;
  if (!loanForm.reportValidity()) return;
  invalidateLoanPreview();
  const version = loanPreviewVersion;
  const payload = buildLoanPayload();
  const snapshot = JSON.stringify(payload);
  const tenant = tenantId;
  loanPreviewButton.disabled = true;
  loanPreviewStatus.textContent = "Calculando vista previa…";
  loanPreviewStatus.hidden = false;
  try {
    const preview = await apiRequest(`${PRODUCT_BASE}/loans/preview`, {method:"POST",body:snapshot});
    if (version !== loanPreviewVersion || tenant !== tenantId || !canManageLoans() || loanCreationRequest || snapshot !== JSON.stringify(buildLoanPayload())) return;
    if (preview.borrower_id !== payload.borrower_id || preview.currency !== "DOP" || !Array.isArray(preview.installments) || preview.installments.length !== payload.installment_count) throw new Error("No se pudo verificar la vista previa. Intente de nuevo.");
    const add = (tag, text, parent=loanPreviewBox) => {const element=document.createElement(tag);element.textContent=text;parent.append(element);return element;};
    add("h3", "Vista previa del préstamo");
    add("p", preview.borrower_name);
    add("p", `Tipo: ${payload.loan_type === "vehicle" ? "Vehículo" : "Personal"} · Frecuencia: ${{daily:"Diaria",weekly:"Semanal",biweekly:"Quincenal",monthly:"Mensual"}[payload.payment_frequency]} · Fecha del préstamo: ${payload.start_date}`);
    if (payload.loan_type === "vehicle") add("p", `Precio: ${formatMoney(payload.vehicle_cash_price)} · Inicial: ${formatMoney(payload.vehicle_down_payment)} · ${payload.vehicle_make} ${payload.vehicle_model} ${payload.vehicle_year}`);
    add("p", `Financiado: ${formatMoney(preview.principal_amount)} · Interés total: ${formatMoney(preview.total_interest)} · Total: ${formatMoney(preview.total_due)}`);
    add("p", `Interés fijo total: ${payload.flat_interest_rate_percent}% · Mora: ${payload.late_fee_enabled ? "Activada según la política del negocio; no incluida en estos importes" : "No activada"}`);
    add("p", "Esta vista previa no crea ni reserva un préstamo. Revise los datos y pulse Crear préstamo para guardarlo. Los datos se validan nuevamente al crear.");
    const table=add("table", ""), head=add("thead", "", table), row=add("tr", "", head);
    for (const label of ["Cuota", "Vence", "Principal", "Interés", "Total"]) {const th=add("th",label,row);th.scope="col";}
    const body=add("tbody", "", table);
    for (const item of preview.installments) {const tr=add("tr", "", body);for (const value of [item.sequence_number,item.due_date,formatMoney(item.principal_due),formatMoney(item.interest_due),formatMoney(item.total_due)]) add("td",String(value),tr);}
    loanPreviewPrintSnapshot={tenant:tenantId,payload:snapshot,calculatedAt:new Date().toLocaleString("es-DO",{timeZone:"America/Santo_Domingo"})};
    const actions=add("div", "");actions.className="loan-preview-actions";
    const printButton=add("button", "Imprimir vista previa", actions);printButton.id="printLoanPreviewButton";printButton.type="button";printButton.addEventListener("click",printLoanPreview);
    loanPreviewBox.hidden=false;
    loanPreviewStatus.textContent="Vista previa calculada. El préstamo todavía no se ha creado.";
    loanPreviewBox.scrollIntoView?.({behavior:"instant",block:"start"});
  } catch (error) {
    if (version === loanPreviewVersion && tenant === tenantId) {loanPreviewStatus.textContent="No se pudo calcular la vista previa. Revise los datos e intente de nuevo.";showError(error.message);}
  } finally {
    if (!loanCreationRequest && !loanCreationPending && !loanCreationStorageBlocked) loanPreviewButton.disabled=false;
  }
});

async function submitLoanCreation(){
  if(loanCreationPending || loanCreationStorageBlocked || !canManageLoans())return;
  if(!loanCreationRequest){
    try{
      const request={key:crypto.randomUUID(),payload:buildLoanPayload()};
      sessionStorage.setItem(loanCreationStorageKey(),JSON.stringify(request));
      loanCreationRequest=request;
    }catch{showError("No se pudo conservar la solicitud para un reintento seguro. El préstamo no se envió.");return;}
  }
  invalidateLoanPreview();loanPreviewButton.disabled=false;
  loanCreationPending=true;loanCreationControls();
  let confirmed=false;
  try{
    const detail=await apiRequest(`${PRODUCT_BASE}/loans`,{method:"POST",body:JSON.stringify({...loanCreationRequest.payload,idempotency_key:loanCreationRequest.key})});
    if(!detail || !Number.isInteger(detail.id) || !Array.isArray(detail.installments))throw new Error("Invalid loan confirmation");
    confirmed=true;
    sessionStorage.removeItem(loanCreationStorageKey());loanCreationRequest=null;
    loanForm.reset();updateVehicleLoanFields();
    try{await loadDashboard();await openLoan(detail.id);showSuccess(`Préstamo #${detail.id} confirmado.`);}
    catch{showError(`Préstamo #${detail.id} confirmado. No se pudo actualizar la pantalla; recargue para consultar sus cuotas.`);}
  }catch(error){
    if(!confirmed && ([400,404,422].includes(error.status) || (error.status===409 && ["Borrower is inactive", "Configure and enable the tenant late-fee policy first"].includes(error.detail)))){
      try{sessionStorage.removeItem(loanCreationStorageKey());loanCreationRequest=null;showError(error.message);}
      catch{showError("No se pudo actualizar la solicitud pendiente en esta sesión. No cree otro préstamo.");}
    }else{showError("No se pudo confirmar el resultado del préstamo. Sus datos y la solicitud se conservan; use Confirmar o recuperar el préstamo. No cree otro préstamo.");}
  }finally{loanCreationPending=false;loanCreationControls();}
}
loanForm.addEventListener("submit",event=>{event.preventDefault();submitLoanCreation();});
document.getElementById("loanCreationRetry").addEventListener("click",submitLoanCreation);


loanType.addEventListener(
  "change",
  updateVehicleLoanFields
);

vehicleCashPrice.addEventListener(
  "input",
  updateVehicleFinancedAmount
);

vehicleDownPayment.addEventListener(
  "input",
  updateVehicleFinancedAmount
);


const paymentDate = document.getElementById(
  "paymentDate"
);

function setDefaultPaymentDate() {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(
    today.getMonth() + 1
  ).padStart(2, "0");
  const day = String(
    today.getDate()
  ).padStart(2, "0");

  paymentDate.value = `${year}-${month}-${day}`;
}

setDefaultPaymentDate();
window.addEventListener("beforeunload", event => {
  if (paymentSubmitting || paymentNeedsReview) {
    event.preventDefault();
    event.returnValue = "";
  }
});


paymentForm.addEventListener(
  "submit",
  async event => {
    event.preventDefault();

    if (paymentSubmitting || paymentNeedsReview || !selectedLoanId || !paymentInstallment.value) return;
    paymentSubmitting = true;
    const loanId = selectedLoanId;
    const submitButton = paymentForm.querySelector('button[type="submit"]');
    const originalLabel = submitButton.textContent;
    const controls = Array.from(workspace.querySelectorAll("button, input, select, textarea"));
    const disabledBefore = controls.map(control => control.disabled);
    controls.forEach(control => { control.disabled = true; });
    submitButton.textContent = "Registrando…";
    let paymentSaved = false;
    let requestStorageKey = null;

    try {
      const paymentPayload = {
        installment_id: Number(paymentInstallment.value),
        amount: Number(document.getElementById("paymentAmount").value).toFixed(2),
        payment_method: document.getElementById("paymentMethod").value,
        reference: document.getElementById("paymentReference").value.trim() || null,
        paid_at: paymentDate.value ? `${paymentDate.value}T12:00:00Z` : null
      };
      requestStorageKey = "prestamodesk-payment-request:" + tenantId + ":" + JSON.stringify(paymentPayload);
      const requestKey = sessionStorage.getItem(requestStorageKey) || crypto.randomUUID();
      sessionStorage.setItem(requestStorageKey, requestKey);
      const receipt = await apiRequest(
        `${PRODUCT_BASE}/payments`,
        {
          method: "POST",
          body: JSON.stringify({...paymentPayload, idempotency_key: requestKey})
        }
      );

      paymentSaved = true;
      sessionStorage.removeItem(requestStorageKey);
      receiptContent.innerHTML = `
        <p>
          <strong>${escapeHtml(
            receipt.receipt_number
          )}</strong>
        </p>
        <p>Monto: ${formatMoney(receipt.amount)}</p>
        <p>
          Saldo de cuota:
          ${formatMoney(receipt.installment_balance)}
        </p>
        <p>
          Saldo del préstamo:
          ${formatMoney(receipt.loan_balance)}
        </p>
        <p>
          Registrado por usuario #${
            receipt.recorded_by_user_id
          }
        </p>
      `;

      paymentForm.reset();
      setDefaultPaymentDate();
      receiptPanel.hidden = false;
      try {
        await loadDashboard();
        await openLoan(loanId);
        showSuccess("Pago registrado.");
      } catch {
        paymentNeedsReview = true;
        showError("Pago registrado. No se pudo actualizar la pantalla. Conserve el recibo y recargue para consultar el saldo antes de registrar otro pago.");
      } finally {
        receiptPanel.hidden = false;
      }
    } catch (error) {
      if (paymentSaved || !error.status || error.status >= 500) {
        paymentNeedsReview = true;
        showError("No se pudo confirmar el resultado del pago. No lo repita: recargue y revise Pagos y correcciones en Caja antes de continuar.");
      } else {
        if (requestStorageKey && error.status !== 409) sessionStorage.removeItem(requestStorageKey);
        showError(error.message);
      }
    } finally {
      paymentSubmitting = false;
      controls.forEach((control, index) => { control.disabled = disabledBefore[index]; });
      submitButton.textContent = originalLabel;
      submitButton.disabled = paymentNeedsReview || !paymentInstallment.value;
    }
  }
);

applicationList.addEventListener(
  "click",
  async event => {
    const statusButton = event.target.closest(
      "button[data-application-status]"
    );
    const convertButton = event.target.closest(
      "button[data-convert-application]"
    );
    const loanButton = event.target.closest(
      "button[data-application-loan]"
    );

    try {
      if (statusButton) {
        const nextStatus =
          statusButton.dataset.applicationStatus;

        await apiRequest(
          `${PRODUCT_BASE}/applications/${
            statusButton.dataset.applicationId
          }`,
          {
            method: "PUT",
            body: JSON.stringify({
              status: nextStatus
            })
          }
        );

        await loadDashboard();
        showSuccess(
          nextStatus === "reviewing"
            ? "Solicitud puesta en revisión."
            : nextStatus === "approved"
              ? "Solicitud aprobada."
              : "Solicitud rechazada."
        );
        return;
      }

      if (convertButton) {
        const confirmed = window.confirm(
          "Esta acción creará el prestatario, "
          + "el préstamo activo y todas sus cuotas. "
          + "¿Desea continuar?"
        );

        if (!confirmed) {
          return;
        }

        const result = await apiRequest(
          `${PRODUCT_BASE}/applications/${
            convertButton.dataset.convertApplication
          }/convert`,
          {
            method: "POST"
          }
        );

        await loadDashboard();
        showSuccess(
          "Solicitud convertida en préstamo."
        );
        await openLoan(result.loan_id);
        return;
      }

      if (loanButton) {
        await openLoan(
          Number(loanButton.dataset.applicationLoan)
        );
      }
    } catch (error) {
      showError(error.message);
    }
  }
);


prospectList.addEventListener(
  "click",
  async event => {
    const statusButton = event.target.closest(
      "button[data-prospect-status]"
    );
    const convertButton = event.target.closest(
      "button[data-convert-prospect]"
    );

    try {
      if (statusButton) {
        await apiRequest(
          `${PRODUCT_BASE}/prospects/${
            statusButton.dataset.prospectId
          }`,
          {
            method: "PUT",
            body: JSON.stringify({
              status:
                statusButton.dataset.prospectStatus
            })
          }
        );

        await loadDashboard();
        showSuccess("Prospecto actualizado.");
        if (statusButton.dataset.prospectStatus === "qualified") {
          openProspectApplication(Number(statusButton.dataset.prospectId));
        }
        return;
      }

      if (convertButton) {
        await apiRequest(
          `${PRODUCT_BASE}/prospects/${
            convertButton.dataset.convertProspect
          }/convert`,
          {
            method: "POST"
          }
        );

        await loadDashboard();
        showSuccess(
          "Prospecto convertido en prestatario."
        );
      }
    } catch (error) {
      showError(error.message);
    }
  }
);


loanList.addEventListener(
  "click",
  async event => {
    const button = event.target.closest(
      "button[data-view-loan]"
    );

    if (!button) {
      return;
    }

    await openLoan(
      Number(button.dataset.viewLoan)
    );
  }
);


document.getElementById(
  "closeLoanDetail"
).addEventListener(
  "click",
  () => {
    selectedLoanId = null;
    loanDetailPanel.hidden = true;
    paymentPanel.hidden = true;
  }
);


document.getElementById(
  "printReceiptButton"
).addEventListener(
  "click",
  () => window.print()
);


forgotPasswordButton.addEventListener(
  "click",
  () => {
    passwordResetEmail.value = loginEmail.value;
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
      "Enviando…";

    try {
      const result = await apiRequest(
        "/auth/password-reset/request",
        {
          method: "POST",
          body: JSON.stringify({
            email: passwordResetEmail.value,
            product_slug: "prestamodesk"
          })
        }
      );

      passwordResetRequestForm.reset();
      passwordResetRequestForm.hidden = true;
      loginForm.hidden = false;

      showSuccess(result.message);
      loginEmail.focus();
    } catch (error) {
      showError(error.message);
    } finally {
      passwordResetRequestButton.disabled = false;
      passwordResetRequestButton.textContent =
        "Enviar enlace";
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
            email:
              document.getElementById(
                "loginEmail"
              ).value,
            password:
              document.getElementById(
                "loginPassword"
              ).value
          })
        }
      );

      await discoverAccess();
      await loadDashboard();
      loginForm.reset();
      setAuthenticatedUI(true);
      showSuccess("Sesión iniciada.");
    } catch (error) {
      showError(error.message);
    }
  }
);


logoutButton.addEventListener(
  "click",
  async () => {
    if(loanCreationPending||loanCreationRequest||loanCreationStorageBlocked){showError(window.prestamodeskLoanCreation.leaveMessage);return;}
    if(!leaveContact())return;
    try {
      await apiRequest(
        "/auth/logout",
        {method: "POST"}
      );
    } catch {
      // Continue local sign-out.
    }

    tenantId = null;
    localStorage.removeItem(
      "prestamodesk_tenant_id"
    );
    location.reload();
  }
);


async function initialize() {
  await checkHealth();

  const today = new Date().toISOString().slice(0, 10);
  document.getElementById(
    "loanStartDate"
  ).value = today;
  lateFeeEffectiveDate.value = today;

  updateVehicleLoanFields();

  if (!tenantId) {
    setAuthenticatedUI(false);
    return;
  }

  try {
    await discoverAccess();
    await loadDashboard();
    setAuthenticatedUI(true);
  } catch {
    tenantId = null;
    localStorage.removeItem(
      "prestamodesk_tenant_id"
    );
    setAuthenticatedUI(false);
  }
}


initialize();

// Task changes keep the same form nodes, values and request-key state.
function applyCompactAccess(manage) {
  for (const button of document.querySelectorAll("[data-loan-manager]")) button.hidden = !manage;
  if (!manage) document.getElementById("workspace").dataset.loanTask = "loans";
}
function openCompactForm(id) {
  if (!canManageLoans()) return;
  if ((id !== "compactLoanForm" && (loanCreationPending || loanCreationRequest || loanCreationStorageBlocked)) || paymentSubmitting || paymentNeedsReview) {showError("Confirme el resultado de la operación pendiente antes de abrir otro formulario.");return;}
  const panel = document.getElementById(id);
  document.getElementById("workspace").dataset.activeForm = id;
  for (const button of document.querySelectorAll("[data-loan-form]")) button.setAttribute("aria-expanded", String(button.dataset.loanForm === id));
  panel.dataset.expanded = "true";
  document.querySelector('[data-loan-form="'+id+'"]')?.setAttribute("aria-expanded", "true");
}
for (const button of document.querySelectorAll("[data-loan-form]")) {
  button.addEventListener("click", () => {
    if (!canManageLoans()) return;
    openCompactForm(button.dataset.loanForm);
    document.getElementById(button.dataset.loanForm).querySelector("input,select")?.focus();
  });
}
for (const button of document.querySelectorAll("[data-loan-tab]")) {
  button.addEventListener("click", () => {
    const task = button.dataset.loanTab;
    if (task !== "loans" && !canManageLoans()) return;
    if (loanCreationPending || loanCreationRequest || loanCreationStorageBlocked || paymentSubmitting || paymentNeedsReview) {
      showError("Confirme el resultado de la operación pendiente antes de cambiar de tarea.");return;
    }
    const box = document.getElementById("workspace");
    delete box.dataset.activeForm;
    for (const formButton of document.querySelectorAll("[data-loan-form]")) formButton.setAttribute("aria-expanded", "false");
    setCompactTask(task === "settings" && box.dataset.loanTask === "settings" ? "loans" : task);
    for (const tab of document.querySelectorAll("[data-loan-tab]")) {
      tab.setAttribute(tab.dataset.loanTab === "settings" ? "aria-expanded" : "aria-pressed", String(tab.dataset.loanTab === box.dataset.loanTask));
    }
  });
}

function setCompactTask(task) {
  document.getElementById("workspace").dataset.loanTask = task;
  for (const tab of document.querySelectorAll("[data-loan-tab]")) tab.setAttribute(tab.dataset.loanTab === "settings" ? "aria-expanded" : "aria-pressed", String(tab.dataset.loanTab === task));
}
for (const button of document.querySelectorAll("[data-loan-close]")) button.addEventListener("click", () => {
  if (loanCreationPending || loanCreationRequest || loanCreationStorageBlocked) {showError("Confirme el resultado del préstamo pendiente antes de ocultar el formulario.");return;}
  delete document.getElementById("workspace").dataset.activeForm;
  document.querySelector('[data-loan-form="'+button.dataset.loanClose+'"]')?.setAttribute("aria-expanded", "false");
  document.querySelector('[data-loan-form="'+button.dataset.loanClose+'"]')?.focus();
});

(() => {"use strict"; const link = document.getElementById("administrationLink");
 const show = client => {link.hidden = !client || !["owner", "administrator"].includes(client.role);};
 window.addEventListener("prestamodesk-access", event => show(event.detail));
 document.getElementById("logoutButton").addEventListener("click", () => show(null));
 show(window.prestamodeskAccess);
})();

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

"use strict";

const prospectApplicationPanel = document.getElementById("prospectApplicationPanel");
const prospectApplicationForm = document.getElementById("prospectApplicationForm");
const prospectApplicationQuote = document.getElementById("prospectApplicationQuote");
const prospectApplicationError = document.getElementById("prospectApplicationError");
const prospectApplicationSave = document.getElementById("prospectApplicationSave");
const prospectApplicationVehicle = document.getElementById("prospectApplicationVehicle");
let routedProspectId = null;
let routedTenantId = null;
let routedQuote = null;
let routingBusy = false;
let routingGeneration = 0;
const routeField = name => prospectApplicationForm.elements.namedItem(name);
const routeValue = name => routeField(name).value.trim();

function clearRouteQuote() {
  routedQuote = null;
  prospectApplicationQuote.hidden = true;
  prospectApplicationSave.disabled = true;
}

function updateProspectRoute() {
  const vehicle = routeValue("loan_type") === "vehicle";
  prospectApplicationVehicle.hidden = !vehicle;
  prospectApplicationVehicle.querySelectorAll("input").forEach(input => {
    input.disabled = !vehicle || routingBusy;
    input.required = vehicle && ["vehicle_make", "vehicle_model", "vehicle_year", "vehicle_cash_price", "vehicle_down_payment"].includes(input.name);
  });
  routeField("principal_amount").readOnly = vehicle;
  if (vehicle) {
    try {
      const financed = routeCents("vehicle_cash_price") - routeCents("vehicle_down_payment");
      routeField("principal_amount").value = financed > 0 ? (financed / 100).toFixed(2) : "";
    } catch {
      routeField("principal_amount").value = "";
    }
  }
}

function setRoutingBusy(active) {
  routingBusy = active;
  prospectApplicationForm.setAttribute("aria-busy", String(active));
  prospectApplicationForm.querySelectorAll("input, select, textarea, button").forEach(control => { control.disabled = active; });
  updateProspectRoute();
  prospectApplicationSave.disabled = active || !routedQuote;
}

function closeProspectApplication() {
  routingGeneration += 1;
  routedProspectId = null;
  routedTenantId = null;
  clearRouteQuote();
  prospectApplicationForm.reset();
  prospectApplicationError.hidden = true;
  prospectApplicationPanel.hidden = true;
}

function openProspectApplication(prospectId) {
  if (routingBusy) return;
  const prospect = prospects.find(item => item.id === prospectId);
  if (!prospect || prospect.status !== "qualified") {
    showError("Califique el prospecto antes de preparar una solicitud.");
    return;
  }
  if (applications.some(item => item.source_prospect_id === prospectId)) {
    showError("Este prospecto ya tiene una solicitud. Revísela en Solicitudes de préstamo.");
    return;
  }
  closeProspectApplication();
  routedProspectId = prospectId;
  routedTenantId = String(tenantId);
  document.getElementById("prospectApplicationTitle").textContent = `Preparar solicitud · ${prospect.full_name}`;
  document.getElementById("prospectApplicationContact").textContent = [prospect.phone, prospect.email].filter(Boolean).join(" · ");
  routeField("principal_amount").value = prospect.requested_amount;
  routeField("vehicle_down_payment").value = "0";
  routeField("notes").value = prospect.message || "";
  updateProspectRoute();
  prospectApplicationPanel.hidden = false;
  routeField("loan_type").focus();
}

function routeCents(name) {
  const raw = routeValue(name);
  if (!/^\d+(?:\.\d{1,2})?$/.test(raw)) throw new Error("Ingrese montos con hasta dos decimales.");
  const [whole, fraction = ""] = raw.split(".");
  const cents = Number(whole) * 100 + Number(fraction.padEnd(2, "0"));
  if (!Number.isSafeInteger(cents)) throw new Error("Monto fuera de rango.");
  return cents;
}

function prospectRouteTerms() {
  if (!routedProspectId || String(tenantId) !== routedTenantId) throw new Error("El cliente cambió. Abra nuevamente el prospecto.");
  const payload = {
    loan_type: routeValue("loan_type"),
    principal_amount: (routeCents("principal_amount") / 100).toFixed(2),
    flat_interest_rate_percent: routeValue("flat_interest_rate_percent"),
    installment_count: Number(routeValue("installment_count")),
    payment_frequency: routeValue("payment_frequency"),
    start_date: routeValue("start_date"),
    first_payment_date: routeValue("first_payment_date"),
    notes: routeValue("notes") || null
  };
  if (payload.first_payment_date < payload.start_date) throw new Error("La primera cuota no puede ser anterior al préstamo.");
  if (payload.loan_type === "vehicle") {
    const price = routeCents("vehicle_cash_price");
    const down = routeCents("vehicle_down_payment");
    if (down >= price) throw new Error("La inicial debe ser menor que el precio del vehículo.");
    payload.vehicle_cash_price = (price / 100).toFixed(2);
    payload.vehicle_down_payment = (down / 100).toFixed(2);
    payload.principal_amount = ((price - down) / 100).toFixed(2);
    payload.vehicle_make = routeValue("vehicle_make");
    payload.vehicle_model = routeValue("vehicle_model");
    payload.vehicle_year = Number(routeValue("vehicle_year"));
    for (const name of ["vehicle_color", "vehicle_vin", "vehicle_license_plate", "vehicle_seller"]) payload[name] = routeValue(name) || null;
  }
  return payload;
}

function routeError(message) {
  prospectApplicationError.textContent = message;
  prospectApplicationError.hidden = false;
}

prospectApplicationForm.addEventListener("input", () => { clearRouteQuote(); updateProspectRoute(); });
prospectApplicationForm.addEventListener("change", () => { clearRouteQuote(); updateProspectRoute(); });
document.getElementById("prospectApplicationCancel").addEventListener("click", closeProspectApplication);
logoutButton.addEventListener("click", closeProspectApplication);
prospectList.addEventListener("click", event => {
  const button = event.target.closest("button[data-start-prospect-application]");
  if (button) openProspectApplication(Number(button.dataset.startProspectApplication));
});

document.getElementById("prospectApplicationCalculate").addEventListener("click", async () => {
  if (routingBusy || !prospectApplicationForm.reportValidity()) return;
  prospectApplicationError.hidden = true;
  clearRouteQuote();
  let payload;
  try { payload = prospectRouteTerms(); } catch (error) { routeError(error.message); return; }
  const generation = routingGeneration;
  setRoutingBusy(true);
  try {
    const quote = await apiRequest(`${PRODUCT_BASE}/applications/quote`, { method: "POST", body: JSON.stringify(payload) });
    if (generation !== routingGeneration || String(tenantId) !== routedTenantId) return;
    if (quote.currency !== "DOP" || !Array.isArray(quote.installments) || quote.installments.length !== payload.installment_count) throw new Error("Cotización incompleta. Vuelva a calcular.");
    prospectApplicationQuote.replaceChildren();
    for (const [label, amount] of [["Monto financiado", quote.principal_amount], ["Interés total", quote.total_interest], ["Total a pagar", quote.total_due]]) {
      const paragraph = document.createElement("p");
      paragraph.textContent = `${label}: ${formatMoney(amount)}`;
      prospectApplicationQuote.append(paragraph);
    }
    const details = document.createElement("details");
    const summary = document.createElement("summary");
    summary.textContent = `Calendario de ${quote.installments.length} cuotas`;
    details.append(summary);
    const list = document.createElement("ol");
    for (const item of quote.installments) {
      const row = document.createElement("li");
      row.textContent = `Cuota ${item.sequence_number} · ${item.due_date} · ${formatMoney(item.total_due)}`;
      list.append(row);
    }
    details.append(list);
    prospectApplicationQuote.append(details);
    routedQuote = JSON.stringify(payload);
    prospectApplicationQuote.hidden = false;
  } catch (error) { if (generation === routingGeneration) routeError(error.message); }
  finally { setRoutingBusy(false); }
});

prospectApplicationForm.addEventListener("submit", async event => {
  event.preventDefault();
  if (routingBusy || !prospectApplicationForm.reportValidity()) return;
  let payload;
  try { payload = prospectRouteTerms(); } catch (error) { routeError(error.message); return; }
  if (!routedQuote || routedQuote !== JSON.stringify(payload)) { routeError("Calcule y revise las cuotas antes de guardar."); return; }
  prospectApplicationError.hidden = true;
  const generation = routingGeneration;
  setRoutingBusy(true);
  let saved = false;
  try {
    const application = await apiRequest(`${PRODUCT_BASE}/prospects/${routedProspectId}/application`, { method: "POST", body: JSON.stringify(payload) });
    if (generation !== routingGeneration || String(tenantId) !== routedTenantId) return;
    saved = true;
    closeProspectApplication();
    showSuccess(`Solicitud #${application.id} guardada. Continúe con revisión, aprobación y conversión.`);
    await loadDashboard();
  } catch (error) {
    if (saved) showError("La solicitud se guardó, pero no se pudo actualizar la pantalla. Recargue antes de continuar.");
    else if (generation === routingGeneration) routeError(error.message);
  } finally { setRoutingBusy(false); }
});

return {canLeave: () => !(typeof collectionWritePending !== "undefined" && collectionWritePending) && !(typeof cashClosingSubmitting !== "undefined" && cashClosingSubmitting) && !(typeof paymentSubmitting !== "undefined" && paymentSubmitting) && !(typeof paymentNeedsReview !== "undefined" && paymentNeedsReview) && (!window.prestamodeskInvitationSharing || window.prestamodeskInvitationSharing.canLeave()) && (!window.prestamodeskLoanCreation || window.prestamodeskLoanCreation.canLeave()) && (!window.prestamodeskBorrowerContact || window.prestamodeskBorrowerContact.canLeave()), confirmLeave: () => typeof collectionWritePending !== "undefined" && collectionWritePending ? false : typeof cashClosingSubmitting !== "undefined" && cashClosingSubmitting ? false : window.prestamodeskLoanCreation && !window.prestamodeskLoanCreation.canLeave() ? false : (typeof paymentSubmitting !== "undefined" && paymentSubmitting) || (typeof paymentNeedsReview !== "undefined" && paymentNeedsReview) ? false : window.prestamodeskBorrowerContact && !window.prestamodeskBorrowerContact.canLeave() ? window.prestamodeskBorrowerContact.confirmLeave() : window.prestamodeskInvitationSharing ? window.prestamodeskInvitationSharing.confirmLeave() : false, leaveMessage: () => typeof collectionWritePending !== "undefined" && collectionWritePending ? "Espere la confirmación de la gestión antes de cambiar de sección." : typeof cashClosingSubmitting !== "undefined" && cashClosingSubmitting ? "Espere la confirmación del cierre de caja antes de cambiar de sección." : window.prestamodeskLoanCreation && !window.prestamodeskLoanCreation.canLeave() ? window.prestamodeskLoanCreation.leaveMessage : window.prestamodeskBorrowerContact && !window.prestamodeskBorrowerContact.canLeave() ? window.prestamodeskBorrowerContact.leaveMessage : window.prestamodeskInvitationSharing ? window.prestamodeskInvitationSharing.leaveMessage : "Revise el resultado del pago en Caja antes de cambiar de sección."};
}},
"cashier": {html:"\n  <header class=\"app-header\">\n    <div>\n      <span class=\"eyebrow\">FieldLookers</span>\n      <h1>PréstamoDesk · Caja</h1>\n      <p>Cobros y recibos de préstamos en DOP</p>\n    </div>\n\n    <div class=\"header-actions\"><a href=\"/prestamodesk/workspace\">Mi espacio · Todas las secciones</a>\n      <span id=\"clientContext\" class=\"badge\" hidden></span>\n      <span id=\"healthStatus\">Comprobando API…</span>\n      <button id=\"logoutButton\" class=\"secondary\" hidden>\n        Cerrar sesión\n      </button>\n    </div>\n  </header>\n\n  <main>\n    <div id=\"errorMessage\" class=\"message error\" role=\"alert\" aria-atomic=\"true\" hidden></div>\n    <div id=\"successMessage\" class=\"message success\" hidden></div>\n\n    <section id=\"authPanel\" class=\"panel auth-panel\">\n      <h2>Iniciar sesión en caja</h2>\n\n      <form id=\"loginForm\" class=\"form-grid\">\n        <label>\n          Correo electrónico\n          <input\n            id=\"loginEmail\"\n            type=\"email\"\n            autocomplete=\"username\"\n            required\n          >\n        </label>\n\n        <label>\n          Contraseña\n          <input\n            id=\"loginPassword\"\n            type=\"password\"\n            autocomplete=\"current-password\"\n            required\n          >\n        </label>\n\n        <button type=\"submit\">Iniciar sesión</button>\n\n        <button\n          id=\"forgotPasswordButton\"\n          type=\"button\"\n          class=\"secondary\"\n        >\n          ¿Olvidó su contraseña?\n        </button>\n      </form>\n\n      <form\n        id=\"passwordResetRequestForm\"\n        class=\"form-grid\"\n        hidden\n      >\n        <p>\n          Ingrese el correo de su cuenta para solicitar un\n          enlace seguro.\n        </p>\n\n        <label>\n          Correo electrónico\n          <input\n            id=\"passwordResetEmail\"\n            type=\"email\"\n            autocomplete=\"email\"\n            required\n          >\n        </label>\n\n        <button\n          id=\"passwordResetRequestButton\"\n          type=\"submit\"\n        >\n          Enviar enlace\n        </button>\n\n        <button\n          id=\"backToSignInButton\"\n          type=\"button\"\n          class=\"secondary\"\n        >\n          Volver a iniciar sesión\n        </button>\n      </form>\n    </section>\n\n    <div id=\"cashierWorkspace\" data-cashier-task=\"collect\" hidden>\n      <nav id=\"cashierTaskToolbar\" class=\"cashier-task-toolbar\" aria-label=\"Tareas de Caja\">\n        <button type=\"button\" data-cashier-task=\"collect\" aria-pressed=\"true\" aria-controls=\"cashierSearchPanel loanDetailPanel paymentPanel receiptPanel\">Cobrar</button>\n        <button type=\"button\" data-cashier-task=\"closing\" aria-pressed=\"false\" aria-controls=\"cashClosingPanel cashClosingReceipt\" hidden>Cierre de caja</button>\n        <button type=\"button\" data-cashier-task=\"history\" aria-pressed=\"false\" aria-controls=\"cashClosingHistoryPanel\" hidden>Mis cierres</button>\n      </nav>\n      <section id=\"cashierSearchPanel\" class=\"panel\">\n        <h2>Buscar préstamo</h2>\n        <p class=\"cashier-hint\">\n          Busque por número de préstamo, nombre o documento\n          del cliente.\n        </p>\n\n        <form id=\"loanSearchForm\" class=\"form-grid\">\n          <label>\n            Búsqueda\n            <input\n              id=\"loanSearchQuery\"\n              type=\"search\"\n              maxlength=\"200\"\n              placeholder=\"Ej.: 4, Ana Pérez o 001-...\"\n            >\n          </label>\n\n          <button type=\"submit\">Buscar</button>\n          <button\n            id=\"showAllLoansButton\"\n            type=\"button\"\n            class=\"secondary\"\n          >\n            Mostrar préstamos\n          </button>\n        </form>\n\n        <p>\n          Resultados:\n          <strong id=\"loanResultCount\">0</strong>\n        </p>\n\n        <div id=\"cashierLoanList\" class=\"table-wrap\"></div>\n      </section>\n\n      <section id=\"loanDetailPanel\" class=\"panel\" hidden>\n        <div class=\"header-actions\">\n          <h2 id=\"loanDetailTitle\">Préstamo</h2>\n          <button\n            id=\"closeLoanDetail\"\n            type=\"button\"\n            class=\"secondary\"\n          >\n            Cerrar\n          </button>\n        </div>\n\n        <div id=\"loanDetailSummary\"></div>\n        <section id=\"paymentCorrectionPanel\" hidden aria-labelledby=\"paymentCorrectionTitle\">\n          <h3 id=\"paymentCorrectionTitle\">Pagos y correcciones</h3>\n          <p>Solo el propietario o administrador puede anular el último pago registrado antes de su cierre de caja. El recibo se conserva con el motivo de anulación. Los pagos anteriores a esta función requieren conciliación.</p>\n          <div id=\"paymentCorrectionMessage\" class=\"message\" role=\"status\" hidden></div>\n          <div id=\"paymentCorrectionList\"></div>\n        </section>\n\n\n        <h3>Calendario de cuotas</h3>\n        <div id=\"installmentList\" class=\"table-wrap\"></div>\n      </section>\n\n      <section id=\"paymentPanel\" class=\"panel\" hidden>\n        <h2>Registrar pago</h2>\n\n        <form id=\"paymentForm\" class=\"form-grid\">\n          <label>\n            Cuota\n            <select id=\"paymentInstallment\" required></select>\n          </label>\n\n          <label>\n            Monto (DOP)\n            <input\n              id=\"paymentAmount\"\n              type=\"number\"\n              min=\"0.01\"\n              step=\"0.01\"\n              required\n            >\n          </label>\n\n          <label>\n            Fecha del pago\n            <input\n              id=\"paymentDate\"\n              type=\"date\"\n              required\n            >\n          </label>\n\n          <label>\n            Método\n            <select id=\"paymentMethod\">\n              <option value=\"cash\">Efectivo</option>\n              <option value=\"bank_transfer\">\n                Transferencia bancaria\n              </option>\n              <option value=\"card\">Tarjeta</option>\n              <option value=\"other\">Otro</option>\n            </select>\n          </label>\n\n          <label>\n            Referencia\n            <input id=\"paymentReference\" maxlength=\"200\">\n          </label>\n\n          <button type=\"submit\">Registrar pago</button>\n        </form>\n      </section>\n\n      <article id=\"receiptPanel\" class=\"panel receipt\" hidden>\n        <h2>Recibo de pago</h2>\n        <div id=\"receiptContent\"></div>\n\n        <button\n          id=\"printReceiptButton\"\n          type=\"button\"\n          class=\"secondary\"\n        >\n          Imprimir recibo\n        </button>\n      </article>\n\n      <section id=\"cashClosingPanel\" class=\"panel\" hidden>\n        <h2>Cierre de caja</h2>\n        <p class=\"notice\">\n          El cierre incluye solamente pagos de préstamos\n          registrados por este cajero y que todavía no pertenecen\n          a otro cierre.\n        </p>\n\n        <div id=\"cashClosingPreview\"></div>\n\n        <form id=\"cashClosingForm\" class=\"form-grid\">\n          <label>\n            Efectivo contado (DOP)\n            <input\n              id=\"cashCounted\"\n              type=\"number\"\n              min=\"0\"\n              step=\"0.01\"\n              required\n            >\n          </label>\n\n          <label>\n            Observaciones\n            <textarea\n              id=\"cashClosingNotes\"\n              maxlength=\"1000\"\n              rows=\"3\"\n            ></textarea>\n          </label>\n\n          <button type=\"submit\">Cerrar mi caja</button>\n        </form>\n      </section>\n\n      <article\n        id=\"cashClosingReceipt\"\n        class=\"panel receipt\"\n        hidden\n      >\n        <h2>Comprobante de cierre</h2>\n        <div id=\"cashClosingReceiptContent\"></div>\n        <button\n          id=\"printCashClosingButton\"\n          type=\"button\"\n          class=\"secondary\"\n        >\n          Imprimir cierre\n        </button>\n      </article>\n\n      <section id=\"cashClosingHistoryPanel\" class=\"panel\" hidden>\n        <h2>Mis cierres anteriores</h2>\n        <div id=\"cashClosingHistory\" class=\"table-wrap\"></div>\n      </section>\n    </div>\n  </main>\n\n  \n  \n", start: function(document, window, fetch, localStorage, location, setTimeout, clearTimeout) {
const API_BASE = "/api/v1";
const PRODUCT_BASE = "/products/prestamodesk";
const TENANT_STORAGE_KEY =
  "prestamodesk_cashier_tenant_id";

let tenantId = localStorage.getItem(
  TENANT_STORAGE_KEY
);
let selectedLoanId = null;
let selectedLoan = null;
let currentRole = null;
let paymentSubmitting = false;
let paymentNeedsReview = false;
let cashClosingSubmitting = false;

const authPanel = document.getElementById("authPanel");
const cashierWorkspace =
  document.getElementById("cashierWorkspace");
const loginForm = document.getElementById("loginForm");
const loginEmail = document.getElementById("loginEmail");
const forgotPasswordButton =
  document.getElementById("forgotPasswordButton");
const passwordResetRequestForm =
  document.getElementById("passwordResetRequestForm");
const passwordResetEmail =
  document.getElementById("passwordResetEmail");
const passwordResetRequestButton =
  document.getElementById("passwordResetRequestButton");
const backToSignInButton =
  document.getElementById("backToSignInButton");
const logoutButton =
  document.getElementById("logoutButton");
const clientContext =
  document.getElementById("clientContext");
const healthStatus =
  document.getElementById("healthStatus");
const errorMessage =
  document.getElementById("errorMessage");
const successMessage =
  document.getElementById("successMessage");
const loanSearchForm =
  document.getElementById("loanSearchForm");
const loanSearchQuery =
  document.getElementById("loanSearchQuery");
const cashierLoanList =
  document.getElementById("cashierLoanList");
const loanResultCount =
  document.getElementById("loanResultCount");
const loanDetailPanel =
  document.getElementById("loanDetailPanel");
const loanDetailTitle =
  document.getElementById("loanDetailTitle");
const loanDetailSummary =
  document.getElementById("loanDetailSummary");
const installmentList =
  document.getElementById("installmentList");
const paymentPanel =
  document.getElementById("paymentPanel");
const paymentForm =
  document.getElementById("paymentForm");
const paymentInstallment =
  document.getElementById("paymentInstallment");
const paymentAmount =
  document.getElementById("paymentAmount");
const paymentDate =
  document.getElementById("paymentDate");
const receiptPanel =
  document.getElementById("receiptPanel");
const receiptContent =
  document.getElementById("receiptContent");
const cashClosingPanel =
  document.getElementById("cashClosingPanel");
const cashClosingPreview =
  document.getElementById("cashClosingPreview");
const cashClosingForm =
  document.getElementById("cashClosingForm");
const cashCounted =
  document.getElementById("cashCounted");
const cashClosingNotes =
  document.getElementById("cashClosingNotes");
const cashClosingReceipt =
  document.getElementById("cashClosingReceipt");
const cashClosingReceiptContent =
  document.getElementById(
    "cashClosingReceiptContent"
  );
const cashClosingHistoryPanel =
  document.getElementById(
    "cashClosingHistoryPanel"
  );
const cashClosingHistory =
  document.getElementById("cashClosingHistory");


function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}


function formatMoney(value) {
  return new Intl.NumberFormat(
    "es-DO",
    {
      style: "currency",
      currency: "DOP"
    }
  ).format(Number(value || 0));
}


function formatStatus(value) {
  const labels = {
    active: "Activo",
    paid: "Pagado",
    cancelled: "Cancelado",
    pending: "Pendiente",
    partial: "Parcial",
    overdue: "Vencida"
  };

  return labels[value] || value;
}


function formatDateTime(value) {
  return new Intl.DateTimeFormat(
    "es-DO",
    {
      dateStyle: "medium",
      timeStyle: "short"
    }
  ).format(new Date(value));
}


function formatPaymentMethod(value) {
  const labels = {
    cash: "Efectivo",
    bank_transfer: "Transferencia bancaria",
    card: "Tarjeta",
    other: "Otro"
  };

  return labels[value] || value;
}


function installmentBalance(installment) {
  if (installment.total_balance !== undefined) {
    return Number(installment.total_balance);
  }

  return (
    Number(installment.total_due)
    - Number(installment.paid_amount)
  );
}


function setAuthenticatedUI(authenticated) {
  authPanel.hidden = authenticated;
  cashierWorkspace.hidden = !authenticated;
  logoutButton.hidden = !authenticated;
  clientContext.hidden = !authenticated;
}


function showError(message) {
  errorMessage.textContent = "";
  errorMessage.hidden = false;
  errorMessage.textContent = message;
  successMessage.hidden = true;
  if (errorMessage.isConnected && !errorMessage.closest("[hidden]")) {
    errorMessage.scrollIntoView?.({behavior: "instant", block: "center", inline: "nearest"});
  }
}


function showSuccess(message) {
  successMessage.textContent = message;
  successMessage.hidden = false;
  errorMessage.hidden = true;

  window.setTimeout(() => {
    successMessage.hidden = true;
  }, 3500);
}


function clearMessages() {
  errorMessage.hidden = true;
  successMessage.hidden = true;
}


async function apiRequest(path, options = {}) {
  const response = await fetch(
    `${API_BASE}${path}`,
    {
      headers: {
        "Content-Type": "application/json",
        ...(tenantId
          ? {"X-Tenant-ID": tenantId}
          : {}),
        ...(options.headers || {})
      },
      ...options
    }
  );

  if (!response.ok) {
    let detail =
      `Solicitud fallida (${response.status})`;

    try {
      const body = await response.json();

      if (typeof body.detail === "string") {
        detail = body.detail;
      }
    } catch {
      // Preserve the safe default.
    }

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
    const error = new Error(spanishApiError(detail, response.status));
    error.status = response.status;
    throw error;
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}


async function checkHealth() {
  try {
    const health = await apiRequest("/health");
    healthStatus.textContent = `API: ${health.status}`;
  } catch {
    healthStatus.textContent = "API no disponible";
  }
}


async function discoverAccess() {
  const access = await apiRequest(
    "/auth/products/prestamodesk/access"
  );

  if (access.clients.length === 0) {
    throw new Error(
      "Su cuenta no tiene acceso activo a PréstamoDesk."
    );
  }

  if (access.clients.length > 1) {
    throw new Error(
      "Su cuenta tiene varios clientes. "
      + "La selección de cliente aún no está disponible."
    );
  }

  const client = access.clients[0];

  if (client.role === "collector") {
    window.location.replace(
      "/prestamodesk/cobros"
    );
    return;
  }

  if (client.role === "supervisor") {
    window.location.replace("/prestamodesk/cobros/supervision");
    return;
  }
  tenantId = String(client.tenant_id);
  localStorage.setItem(
    TENANT_STORAGE_KEY,
    tenantId
  );

  const roleLabel = (
    ["owner", "administrator"].includes(client.role)
      ? "Administrador"
      : "Cajero"
  );

  currentRole = client.role;
  for (const button of document.querySelectorAll('[data-cashier-task="closing"],[data-cashier-task="history"]')) button.hidden = !["member", "cashier"].includes(currentRole);
  if (!["member", "cashier"].includes(currentRole)) setCashierTask("collect");
  cashClosingPanel.hidden = !["member", "cashier"].includes(currentRole);
  cashClosingHistoryPanel.hidden =
    !["member", "cashier"].includes(currentRole);

  clientContext.textContent =
    `Cliente #${client.client_number} · `
    + `${client.name} · ${roleLabel}`;
}


function renderClosingPreview(preview) {
  cashClosingPreview.innerHTML = `
    <div class="summary-grid">
      <p>
        Pagos pendientes de cierre:
        <strong>${preview.payment_count}</strong>
      </p>
      <p>
        Total cobrado:
        <strong>${
          formatMoney(preview.total_collected)
        }</strong>
      </p>
      <p>
        Efectivo esperado:
        <strong>${
          formatMoney(preview.cash_expected)
        }</strong>
      </p>
      <p>
        Transferencias:
        ${formatMoney(preview.bank_transfer_total)}
      </p>
      <p>Tarjetas: ${formatMoney(preview.card_total)}</p>
      <p>Otros: ${formatMoney(preview.other_total)}</p>
      <p>
        Período iniciado:
        ${escapeHtml(formatDateTime(preview.opened_at))}
      </p>
    </div>
  `;

  cashCounted.value = Number(
    preview.cash_expected
  ).toFixed(2);
}


function renderClosingHistory(closings) {
  if (closings.length === 0) {
    cashClosingHistory.innerHTML = `
      <p class="notice">No hay cierres registrados.</p>
    `;
    return;
  }

  cashClosingHistory.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Cierre</th>
          <th>Fecha</th>
          <th>Pagos</th>
          <th>Total</th>
          <th>Efectivo esperado</th>
          <th>Efectivo contado</th>
          <th>Diferencia</th>
        </tr>
      </thead>
      <tbody>
        ${closings.map(closing => `
          <tr>
            <td>#${closing.id}</td>
            <td>${escapeHtml(
              formatDateTime(closing.closed_at)
            )}</td>
            <td>${closing.payment_count}</td>
            <td>${formatMoney(
              closing.total_collected
            )}</td>
            <td>${formatMoney(
              closing.cash_expected
            )}</td>
            <td>${formatMoney(
              closing.cash_counted
            )}</td>
            <td>${formatMoney(
              closing.cash_difference
            )}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}


async function loadCashClosing() {
  if (!["member", "cashier"].includes(currentRole)) {
    return;
  }

  const [preview, history] = await Promise.all([
    apiRequest(
      `${PRODUCT_BASE}/cashier/closing-preview`
    ),
    apiRequest(
      `${PRODUCT_BASE}/cashier/closings`
    )
  ]);

  renderClosingPreview(preview);
  renderClosingHistory(history);
}


function renderLoans(loans) {
  loanResultCount.textContent = String(loans.length);

  if (loans.length === 0) {
    cashierLoanList.innerHTML = `
      <p class="notice">
        No se encontraron préstamos.
      </p>
    `;
    return;
  }

  cashierLoanList.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Préstamo</th>
          <th>Cliente</th>
          <th>Documento</th>
          <th>Vehículo</th>
          <th>Saldo ordinario</th>
          <th>Mora</th>
          <th>Total exigible</th>
          <th>Estado</th>
          <th>Acción</th>
        </tr>
      </thead>
      <tbody>
        ${loans.map(loan => `
          <tr>
            <td>#${loan.id}</td>
            <td>${escapeHtml(loan.borrower_full_name)}</td>
            <td>
              ${escapeHtml(
                loan.borrower_document_number || "—"
              )}
            </td>
            <td>
              ${escapeHtml(
                [
                  loan.vehicle_make,
                  loan.vehicle_model,
                  loan.vehicle_year
                ].filter(Boolean).join(" ") || "—"
              )}
            </td>
            <td>
              ${formatMoney(loan.ordinary_balance_due)}
            </td>
            <td>
              ${formatMoney(loan.late_fee_balance_due)}
            </td>
            <td>${formatMoney(loan.balance_due)}</td>
            <td>${formatStatus(loan.status)}</td>
            <td>
              <button
                type="button"
                data-open-loan="${loan.id}"
              >
                Cobrar
              </button>
            </td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}


async function searchLoans(query = "") {
  clearMessages();

  const normalized = query.trim();
  const params = new URLSearchParams();

  if (normalized) {
    params.set("query", normalized);
  }

  if (paymentDate.value) {
    params.set("as_of", paymentDate.value);
  }

  const suffix = params.toString()
    ? `?${params.toString()}`
    : "";

  const loans = await apiRequest(
    `${PRODUCT_BASE}/cashier/loans${suffix}`
  );

  renderLoans(loans);
}


function renderInstallments(installments) {
  installmentList.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Cuota</th>
          <th>Vence</th>
          <th>Total de cuota</th>
          <th>Pagado</th>
          <th>Saldo ordinario</th>
          <th>Mora</th>
          <th>Total exigible</th>
          <th>Estado</th>
        </tr>
      </thead>
      <tbody>
        ${installments.map(item => `
          <tr>
            <td>${item.sequence_number}</td>
            <td>${escapeHtml(item.due_date)}</td>
            <td>${formatMoney(item.total_due)}</td>
            <td>${formatMoney(item.paid_amount)}</td>
            <td>${formatMoney(item.ordinary_balance)}</td>
            <td>${formatMoney(item.late_fee_balance)}</td>
            <td>${formatMoney(item.total_balance)}</td>
            <td>${formatStatus(item.status)}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}


function renderPaymentOptions(installments) {
  const payable = installments.filter(
    item => (
      item.status !== "paid"
      && installmentBalance(item) > 0
    )
  );

  if (payable.length === 0) {
    paymentInstallment.innerHTML =
      '<option value="">No hay cuotas pendientes</option>';
    paymentInstallment.disabled = true;
    paymentAmount.disabled = true;
    paymentForm.querySelector(
      'button[type="submit"]'
    ).disabled = true;
    return;
  }

  paymentInstallment.disabled = false;
  paymentAmount.disabled = false;
  paymentForm.querySelector(
    'button[type="submit"]'
  ).disabled = paymentSubmitting || paymentNeedsReview;

  paymentInstallment.innerHTML = payable
    .map(item => `
      <option
        value="${item.id}"
        data-balance="${installmentBalance(item)}"
      >
        Cuota ${item.sequence_number}
        · vence ${escapeHtml(item.due_date)}
        · ${formatMoney(installmentBalance(item))}
      </option>
    `)
    .join("");

  updatePaymentLimit();
}


function updatePaymentLimit() {
  const option =
    paymentInstallment.selectedOptions[0];

  if (!option || !option.dataset.balance) {
    paymentAmount.value = "";
    paymentAmount.removeAttribute("max");
    return;
  }

  const balance = Number(option.dataset.balance);
  paymentAmount.max = balance.toFixed(2);
  paymentAmount.value = balance.toFixed(2);
}


async function openLoan(loanId) {
  const params = new URLSearchParams();

  if (paymentDate.value) {
    params.set("as_of", paymentDate.value);
  }

  const suffix = params.toString()
    ? `?${params.toString()}`
    : "";

  const loan = await apiRequest(
    `${PRODUCT_BASE}/cashier/loans/${loanId}${suffix}`
  );

  selectedLoanId = loan.id;
  selectedLoan = loan;

  loanDetailTitle.textContent =
    `Préstamo #${loan.id} · `
    + loan.borrower_full_name;

  loanDetailSummary.innerHTML = `
    <p>
      <strong>Documento:</strong>
      ${escapeHtml(
        loan.borrower_document_number || "No registrado"
      )}
    </p>
    <p>
      <strong>Vehículo:</strong>
      ${escapeHtml(
        [
          loan.vehicle_make,
          loan.vehicle_model,
          loan.vehicle_year
        ].filter(Boolean).join(" ") || "No registrado"
      )}
    </p>
    <p>
      <strong>Total contractual:</strong>
      ${formatMoney(loan.total_due)}
      · <strong>Pagado:</strong>
      ${formatMoney(loan.paid_amount)}
    </p>
    <p>
      <strong>Saldo ordinario:</strong>
      ${formatMoney(loan.ordinary_balance_due)}
      · <strong>Mora:</strong>
      ${formatMoney(loan.late_fee_balance_due)}
      · <strong>Total exigible:</strong>
      ${formatMoney(loan.balance_due)}
    </p>
    <p>
      <strong>Calculado al:</strong>
      ${escapeHtml(loan.projected_through)}
      · <strong>Estado:</strong>
      ${formatStatus(loan.status)}
    </p>
  `;


  renderInstallments(loan.installments);
  renderPaymentOptions(loan.installments);

  setCashierTask("collect");
  loanDetailPanel.hidden = false;
  paymentPanel.hidden = (
    loan.status !== "active"
  );
  receiptPanel.hidden = true;
  await window.prestamodeskPaymentHistory?.load(loan.id, currentRole);
}


function setDefaultPaymentDate() {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(
    today.getMonth() + 1
  ).padStart(2, "0");
  const day = String(
    today.getDate()
  ).padStart(2, "0");

  paymentDate.value = `${year}-${month}-${day}`;
}


loanSearchForm.addEventListener(
  "submit",
  async event => {
    event.preventDefault();

    try {
      await searchLoans(loanSearchQuery.value);
    } catch (error) {
      showError(error.message);
    }
  }
);


document.getElementById(
  "showAllLoansButton"
).addEventListener(
  "click",
  async () => {
    loanSearchQuery.value = "";

    try {
      await searchLoans();
    } catch (error) {
      showError(error.message);
    }
  }
);


cashierLoanList.addEventListener(
  "click",
  async event => {
    const button = event.target.closest(
      "button[data-open-loan]"
    );

    if (!button) {
      return;
    }

    try {
      await openLoan(
        Number(button.dataset.openLoan)
      );
    } catch (error) {
      showError(error.message);
    }
  }
);


document.getElementById(
  "closeLoanDetail"
).addEventListener(
  "click",
  () => {
    selectedLoanId = null;
    selectedLoan = null;
    loanDetailPanel.hidden = true;
    paymentPanel.hidden = true;
    receiptPanel.hidden = true;
  }
);


paymentInstallment.addEventListener(
  "change",
  updatePaymentLimit
);


paymentDate.addEventListener(
  "change",
  async () => {
    clearMessages();

    try {
      await searchLoans(loanSearchQuery.value);

      if (selectedLoanId) {
        await openLoan(selectedLoanId);
      }
    } catch (error) {
      showError(error.message);
    }
  }
);


paymentForm.addEventListener(
  "submit",
  async event => {
    event.preventDefault();
    if (paymentSubmitting || paymentNeedsReview || !selectedLoanId || !selectedLoan) return;
    paymentSubmitting = true;
    clearMessages();
    const loanId = selectedLoanId;
    const borrowerName = selectedLoan.borrower_full_name;
    const paidDate = paymentDate.value;
    const submitButton = paymentForm.querySelector('button[type="submit"]');
    const originalLabel = submitButton.textContent;
    const controls = Array.from(cashierWorkspace.querySelectorAll("button, input, select, textarea"));
    const disabledBefore = controls.map(control => control.disabled);
    controls.forEach(control => { control.disabled = true; });
    submitButton.textContent = "Registrando…";
    let paymentSaved = false;
    let requestStorageKey = null;

    try {
      const paymentMethod =
        document.getElementById(
          "paymentMethod"
        ).value;
      const reference =
        document.getElementById(
          "paymentReference"
        ).value.trim() || null;

      const paymentPayload = {
        installment_id: Number(paymentInstallment.value),
        amount: Number(paymentAmount.value).toFixed(2),
        payment_method: paymentMethod,
        reference,
        paid_at: paidDate ? `${paidDate}T12:00:00Z` : null
      };
      requestStorageKey = "prestamodesk-payment-request:" + tenantId
        + ":" + JSON.stringify(paymentPayload);
      const requestKey = sessionStorage.getItem(requestStorageKey)
        || crypto.randomUUID();
      sessionStorage.setItem(requestStorageKey, requestKey);
      const receipt = await apiRequest(
        `${PRODUCT_BASE}/payments`,
        {
          method: "POST",
          body: JSON.stringify({...paymentPayload, idempotency_key: requestKey})
        }
      );

      paymentSaved = true;
      sessionStorage.removeItem(requestStorageKey);
      receiptContent.innerHTML = `
        <p>
          <strong>${escapeHtml(
            receipt.receipt_number
          )}</strong>
        </p>
        <p>
          Préstamo:
          <strong>#${loanId}</strong>
        </p>
        <p>
          Cliente:
          <strong>${escapeHtml(
            borrowerName
          )}</strong>
        </p>
        <p>
          Fecha:
          ${escapeHtml(paidDate)}
        </p>
        <p>
          Método:
          ${escapeHtml(
            formatPaymentMethod(paymentMethod)
          )}
        </p>
        <p>
          Referencia:
          ${escapeHtml(reference || "—")}
        </p>
        <p>
          Monto:
          <strong>${formatMoney(receipt.amount)}</strong>
        </p>
        <p>
          Aplicado a mora:
          ${formatMoney(receipt.late_fee_amount)}
        </p>
        <p>
          Aplicado a interés:
          ${formatMoney(receipt.interest_amount)}
        </p>
        <p>
          Aplicado a principal:
          ${formatMoney(receipt.principal_amount)}
        </p>
        <p>
          Saldo ordinario de cuota:
          ${formatMoney(
            receipt.installment_ordinary_balance
          )}
        </p>
        <p>
          Mora pendiente:
          ${formatMoney(
            receipt.installment_late_fee_balance
          )}
        </p>
        <p>
          Total pendiente de cuota:
          ${formatMoney(receipt.installment_balance)}
        </p>
        <p>
          Saldo total del préstamo:
          ${formatMoney(receipt.loan_balance)}
        </p>
        <p>
          Registrado por usuario #${
            receipt.recorded_by_user_id
          }
        </p>
      `;

      receiptPanel.hidden = false;
      paymentForm.reset();
      setDefaultPaymentDate();

      try {
        await openLoan(loanId);
        await searchLoans(loanSearchQuery.value);
        await loadCashClosing();
        showSuccess("Pago registrado.");
      } catch {
        paymentNeedsReview = true;
        showError("Pago registrado. No se pudo actualizar la pantalla. Conserve el recibo y recargue para consultar el saldo antes de registrar otro pago.");
      } finally {
        receiptPanel.hidden = false;
      }
    } catch (error) {
      if (paymentSaved || !error.status || error.status >= 500) {
        paymentNeedsReview = true;
        showError("No se pudo confirmar el resultado del pago. No lo repita: recargue y revise Pagos y correcciones antes de continuar.");
      } else {
        // Keep keys for conflicts: changing operator or a voided payment
        // must not turn a retry into a new payment.
        if (requestStorageKey && error.status !== 409) {
          sessionStorage.removeItem(requestStorageKey);
        }
        showError(error.message);
      }
    } finally {
      paymentSubmitting = false;
      controls.forEach((control, index) => { control.disabled = disabledBefore[index]; });
      submitButton.textContent = originalLabel;
      submitButton.disabled = paymentNeedsReview
        || !paymentInstallment.value
        || Number(paymentInstallment.selectedOptions[0]?.dataset.balance || 0) <= 0;
    }
  }
);


document.getElementById(
  "printReceiptButton"
).addEventListener(
  "click",
  () => window.print()
);


cashClosingForm.addEventListener(
  "submit",
  async event => {
    event.preventDefault();
    if (cashClosingSubmitting || paymentSubmitting || paymentNeedsReview) {showError("Confirme la operación pendiente antes de cerrar la caja.");return;}
    cashClosingSubmitting = true;
    const closingButton = cashClosingForm.querySelector('button[type="submit"]');
    closingButton.disabled = true;
    clearMessages();

    try {
      const closing = await apiRequest(
        `${PRODUCT_BASE}/cashier/closings`,
        {
          method: "POST",
          body: JSON.stringify({
            cash_counted: cashCounted.value,
            notes:
              cashClosingNotes.value.trim()
              || null
          })
        }
      );

      cashClosingReceiptContent.innerHTML = `
        <p>
          <strong>Cierre #${closing.id}</strong>
        </p>
        <p>
          Cerrado:
          ${escapeHtml(
            formatDateTime(closing.closed_at)
          )}
        </p>
        <p>Pagos: ${closing.payment_count}</p>
        <p>
          Total cobrado:
          <strong>${
            formatMoney(closing.total_collected)
          }</strong>
        </p>
        <p>
          Efectivo esperado:
          ${formatMoney(closing.cash_expected)}
        </p>
        <p>
          Efectivo contado:
          ${formatMoney(closing.cash_counted)}
        </p>
        <p>
          Diferencia:
          <strong>${
            formatMoney(closing.cash_difference)
          }</strong>
        </p>
        <p>
          Transferencias:
          ${formatMoney(
            closing.bank_transfer_total
          )}
        </p>
        <p>
          Tarjetas:
          ${formatMoney(closing.card_total)}
        </p>
        <p>
          Otros:
          ${formatMoney(closing.other_total)}
        </p>
        <p>
          Observaciones:
          ${escapeHtml(closing.notes || "—")}
        </p>
      `;

      cashClosingReceipt.hidden = false;
      cashClosingForm.reset();
      await loadCashClosing();
      showSuccess("Caja cerrada correctamente.");
    } catch (error) {
      showError(error.message);
    } finally {
      cashClosingSubmitting = false;
      closingButton.disabled = false;
    }
  }
);


document.getElementById(
  "printCashClosingButton"
).addEventListener(
  "click",
  () => window.print()
);


forgotPasswordButton.addEventListener(
  "click",
  () => {
    passwordResetEmail.value = loginEmail.value;
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
      "Enviando…";

    try {
      const result = await apiRequest(
        "/auth/password-reset/request",
        {
          method: "POST",
          body: JSON.stringify({
            email: passwordResetEmail.value,
            product_slug: "prestamodesk"
          })
        }
      );

      passwordResetRequestForm.reset();
      passwordResetRequestForm.hidden = true;
      loginForm.hidden = false;
      showSuccess(result.message);
    } catch (error) {
      showError(error.message);
    } finally {
      passwordResetRequestButton.disabled = false;
      passwordResetRequestButton.textContent =
        "Enviar enlace";
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
            password:
              document.getElementById(
                "loginPassword"
              ).value
          })
        }
      );

      await discoverAccess();
      await searchLoans();
      await loadCashClosing();
      loginForm.reset();
      setAuthenticatedUI(true);
      showSuccess("Sesión de caja iniciada.");
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
        {method: "POST"}
      );
    } catch {
      // Continue local sign-out.
    }

    tenantId = null;
    localStorage.removeItem(TENANT_STORAGE_KEY);
    location.reload();
  }
);


async function initialize() {
  await checkHealth();
  setDefaultPaymentDate();

  if (!tenantId) {
    setAuthenticatedUI(false);
    return;
  }

  try {
    await discoverAccess();
    await searchLoans();
    await loadCashClosing();
    setAuthenticatedUI(true);
  } catch {
    tenantId = null;
    localStorage.removeItem(TENANT_STORAGE_KEY);
    setAuthenticatedUI(false);
  }
}


initialize();

function setCashierTask(task) {
  cashierWorkspace.dataset.cashierTask = task;
  for (const button of document.querySelectorAll("button[data-cashier-task]")) button.setAttribute("aria-pressed", String(button.dataset.cashierTask === task));
}
for (const button of document.querySelectorAll("button[data-cashier-task]")) button.addEventListener("click", () => {
  const task = button.dataset.cashierTask;
  if (task !== "collect" && !["member", "cashier"].includes(currentRole)) return;
  if (paymentSubmitting || paymentNeedsReview || cashClosingSubmitting) {showError("Confirme el resultado de la operación pendiente antes de cambiar de tarea.");return;}
  setCashierTask(task);
});

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

return {canLeave: () => !(typeof collectionWritePending !== "undefined" && collectionWritePending) && !(typeof cashClosingSubmitting !== "undefined" && cashClosingSubmitting) && !(typeof paymentSubmitting !== "undefined" && paymentSubmitting) && !(typeof paymentNeedsReview !== "undefined" && paymentNeedsReview) && (!window.prestamodeskInvitationSharing || window.prestamodeskInvitationSharing.canLeave()) && (!window.prestamodeskLoanCreation || window.prestamodeskLoanCreation.canLeave()) && (!window.prestamodeskBorrowerContact || window.prestamodeskBorrowerContact.canLeave()), confirmLeave: () => typeof collectionWritePending !== "undefined" && collectionWritePending ? false : typeof cashClosingSubmitting !== "undefined" && cashClosingSubmitting ? false : window.prestamodeskLoanCreation && !window.prestamodeskLoanCreation.canLeave() ? false : (typeof paymentSubmitting !== "undefined" && paymentSubmitting) || (typeof paymentNeedsReview !== "undefined" && paymentNeedsReview) ? false : window.prestamodeskBorrowerContact && !window.prestamodeskBorrowerContact.canLeave() ? window.prestamodeskBorrowerContact.confirmLeave() : window.prestamodeskInvitationSharing ? window.prestamodeskInvitationSharing.confirmLeave() : false, leaveMessage: () => typeof collectionWritePending !== "undefined" && collectionWritePending ? "Espere la confirmación de la gestión antes de cambiar de sección." : typeof cashClosingSubmitting !== "undefined" && cashClosingSubmitting ? "Espere la confirmación del cierre de caja antes de cambiar de sección." : window.prestamodeskLoanCreation && !window.prestamodeskLoanCreation.canLeave() ? window.prestamodeskLoanCreation.leaveMessage : window.prestamodeskBorrowerContact && !window.prestamodeskBorrowerContact.canLeave() ? window.prestamodeskBorrowerContact.leaveMessage : window.prestamodeskInvitationSharing ? window.prestamodeskInvitationSharing.leaveMessage : "Revise el resultado del pago en Caja antes de cambiar de sección."};
}},
"collections": {html:"\n  <header class=\"app-header\">\n    <div>\n      <span class=\"eyebrow\">FieldLookers</span>\n      <h1>PréstamoDesk · Gestión de cobros</h1>\n      <p>\n        Cartera vencida, seguimiento y promesas de pago\n      </p>\n    </div>\n\n    <div class=\"header-actions\"><a href=\"/prestamodesk/workspace\">Mi espacio · Todas las secciones</a>\n      <a\n        id=\"supervisionLink\"\n        href=\"/prestamodesk/cobros/supervision\"\n        hidden\n      >\n        Supervisión\n      </a>\n      <span id=\"clientContext\" class=\"badge\" hidden></span>\n      <span id=\"healthStatus\">Comprobando API…</span>\n      <button id=\"logoutButton\" class=\"secondary\" hidden>\n        Cerrar sesión\n      </button>\n    </div>\n  </header>\n\n  <main>\n    <div id=\"errorMessage\" class=\"message error\" hidden></div>\n    <div id=\"successMessage\" class=\"message success\" hidden></div>\n\n    <section id=\"authPanel\" class=\"panel auth-panel\">\n      <h2>Iniciar sesión en gestión de cobros</h2>\n\n      <form id=\"loginForm\" class=\"form-grid\">\n        <label>\n          Correo electrónico\n          <input\n            id=\"loginEmail\"\n            type=\"email\"\n            autocomplete=\"username\"\n            required\n          >\n        </label>\n\n        <label>\n          Contraseña\n          <input\n            id=\"loginPassword\"\n            type=\"password\"\n            autocomplete=\"current-password\"\n            required\n          >\n        </label>\n\n        <button type=\"submit\">Iniciar sesión</button>\n      </form>\n    </section>\n\n    <div id=\"collectionsWorkspace\" data-collection-task=\"portfolio\" hidden>\n      <nav id=\"collectionTaskToolbar\" class=\"collection-toolbar\" aria-label=\"Tareas de Cobros\">\n        <button type=\"button\" data-collection-task=\"portfolio\" aria-pressed=\"true\" aria-controls=\"collectionPortfolioPanel collectionDetailPanel\">Cartera</button>\n        <button type=\"button\" data-collection-task=\"overdue\" aria-pressed=\"false\" aria-controls=\"collectionOverduePanel\">Promesas vencidas</button>\n      </nav>\n      <section id=\"collectionPortfolioPanel\" class=\"panel\">\n        <div class=\"panel-heading\">\n          <div>\n            <h2 id=\"portfolioTitle\">Cartera vencida</h2>\n            <p id=\"portfolioNotice\" class=\"collection-hint\">\n              Incluye todos los préstamos con cuotas vencidas\n              y saldo pendiente del cliente seleccionado.\n            </p>\n          </div>\n\n          <button\n            id=\"refreshPortfolioButton\"\n            type=\"button\"\n            class=\"secondary\"\n          >\n            Actualizar\n          </button>\n        </div>\n\n        <form id=\"portfolioFilterForm\" class=\"form-grid\">\n          <label>\n            Fecha de corte\n            <input\n              id=\"portfolioAsOf\"\n              type=\"date\"\n              required\n            >\n          </label>\n\n          <label id=\"assignmentStatusField\" hidden>\n            Asignación\n            <select id=\"assignmentStatus\">\n              <option value=\"all\">Todos</option>\n              <option value=\"assigned\">Asignados</option>\n              <option value=\"unassigned\">Sin asignar</option>\n            </select>\n          </label>\n\n          <button type=\"submit\">Consultar cartera</button>\n        </form>\n\n        <p>\n          Préstamos vencidos:\n          <strong id=\"portfolioCount\">0</strong>\n        </p>\n\n        <div id=\"portfolioList\" class=\"table-wrap\"></div>\n      </section>\n\n      <section id=\"collectionDetailPanel\" class=\"panel\" data-collection-detail=\"activity\" hidden>\n        <div class=\"panel-heading\">\n          <div>\n            <h2 id=\"collectionDetailTitle\">\n              Gestión del préstamo\n            </h2>\n            <div id=\"collectionDetailSummary\"></div>\n          </div>\n\n          <button\n            id=\"closeCollectionDetail\"\n            type=\"button\"\n            class=\"secondary\"\n          >\n            Cerrar\n          </button>\n        </div>\n\n        <nav id=\"collectionDetailToolbar\" class=\"collection-toolbar\" aria-label=\"Tareas del préstamo\">\n          <button type=\"button\" data-collection-detail=\"activity\" aria-pressed=\"true\" aria-controls=\"collectionActivityPanel\">Gestión</button>\n          <button type=\"button\" data-collection-detail=\"promise\" aria-pressed=\"false\" aria-controls=\"collectionPromisePanel\">Promesa</button>\n          <button type=\"button\" data-collection-detail=\"history\" aria-pressed=\"false\" aria-controls=\"collectionActivityPanelHistory collectionPromisePanelHistory\">Historial</button>\n          <button id=\"collectionAssignmentTab\" type=\"button\" data-collection-detail=\"assignment\" aria-pressed=\"false\" aria-controls=\"collectorAssignmentPanel\" hidden>Asignación</button>\n        </nav>\n        <div class=\"collection-forms\">\n          <section id=\"collectionActivityPanel\">\n            <h3>Registrar gestión</h3>\n\n            <form id=\"activityForm\" class=\"form-grid\">\n              <label>\n                Canal\n                <select id=\"activityChannel\" required>\n                  <option value=\"phone\">Llamada</option>\n                  <option value=\"whatsapp\">WhatsApp</option>\n                  <option value=\"sms\">SMS</option>\n                  <option value=\"email\">Correo</option>\n                  <option value=\"visit\">Visita</option>\n                  <option value=\"other\">Otro</option>\n                </select>\n              </label>\n\n              <label>\n                Resultado\n                <input\n                  id=\"activityOutcome\"\n                  maxlength=\"100\"\n                  required\n                >\n              </label>\n\n              <label>\n                Fecha y hora del contacto\n                <input\n                  id=\"activityContactedAt\"\n                  type=\"datetime-local\"\n                  required\n                >\n              </label>\n\n              <label>\n                Próximo seguimiento\n                <input\n                  id=\"activityNextFollowUpAt\"\n                  type=\"datetime-local\"\n                >\n              </label>\n\n              <label>\n                Notas\n                <textarea\n                  id=\"activityNotes\"\n                  maxlength=\"2000\"\n                ></textarea>\n              </label>\n\n              <button type=\"submit\">Guardar gestión</button>\n            </form>\n          </section>\n\n          <section id=\"collectionPromisePanel\">\n            <h3>Registrar promesa de pago</h3>\n\n            <form id=\"promiseForm\" class=\"form-grid\">\n              <label>\n                Monto prometido\n                <input\n                  id=\"promiseAmount\"\n                  type=\"number\"\n                  min=\"0.01\"\n                  step=\"0.01\"\n                  required\n                >\n              </label>\n\n              <label>\n                Fecha prometida\n                <input\n                  id=\"promiseDueDate\"\n                  type=\"date\"\n                  required\n                >\n              </label>\n\n              <label>\n                Notas\n                <textarea\n                  id=\"promiseNotes\"\n                  maxlength=\"2000\"\n                ></textarea>\n              </label>\n\n              <button type=\"submit\">Guardar promesa</button>\n            </form>\n          </section>\n        </div>\n\n        <section id=\"collectorAssignmentPanel\" hidden>\n          <h3>Asignación de cobrador</h3>\n\n          <form id=\"collectorAssignmentForm\" class=\"form-grid\">\n            <label>\n              Cobrador\n              <select id=\"collectorAssignmentUser\" required>\n                <option value=\"\">Seleccione un cobrador</option>\n              </select>\n            </label>\n\n            <button type=\"submit\">\n              Asignar o reasignar\n            </button>\n          </form>\n\n          <button\n            id=\"releaseCollectorAssignment\"\n            type=\"button\"\n            class=\"secondary\"\n            hidden\n          >\n            Liberar asignación\n          </button>\n\n          <div\n            id=\"collectorAssignmentHistory\"\n            class=\"table-wrap\"\n          ></div>\n        </section>\n\n        <section id=\"collectionActivityPanelHistory\">\n          <h3>Historial de gestiones</h3>\n          <div\n            id=\"collectionActivityHistory\"\n            class=\"table-wrap\"\n          ></div>\n        </section>\n\n        <section id=\"collectionPromisePanelHistory\">\n          <h3>Promesas de pago</h3>\n          <div\n            id=\"paymentPromiseHistory\"\n            class=\"table-wrap\"\n          ></div>\n        </section>\n      </section>\n\n      <section id=\"collectionOverduePanel\" class=\"panel\">\n        <div class=\"panel-heading\">\n          <div>\n            <h2>Promesas vencidas</h2>\n            <p class=\"collection-hint\">\n              Promesas pendientes o parciales cuya fecha ya\n              venció.\n            </p>\n          </div>\n\n          <button\n            id=\"refreshOverduePromisesButton\"\n            type=\"button\"\n            class=\"secondary\"\n          >\n            Actualizar\n          </button>\n        </div>\n\n        <div\n          id=\"overduePromiseList\"\n          class=\"table-wrap\"\n        ></div>\n      </section>\n    </div>\n  </main>\n\n  <footer>\n    <span>PréstamoDesk · FieldLookers</span>\n  </footer>\n\n  \n", start: function(document, window, fetch, localStorage, location, setTimeout, clearTimeout) {
const API_BASE = "/api/v1";
const PRODUCT_BASE = "/products/prestamodesk";
const TENANT_STORAGE_KEY =
  "prestamodesk_collections_tenant_id";

let tenantId = localStorage.getItem(
  TENANT_STORAGE_KEY
);
let selectedPortfolioItem = null;
let currentRole = null;
let availableCollectors = [];

const authPanel = document.getElementById("authPanel");
const collectionsWorkspace =
  document.getElementById("collectionsWorkspace");
const loginForm = document.getElementById("loginForm");
const loginEmail = document.getElementById("loginEmail");
const loginPassword =
  document.getElementById("loginPassword");
const logoutButton =
  document.getElementById("logoutButton");
const clientContext =
  document.getElementById("clientContext");
const supervisionLink =
  document.getElementById("supervisionLink");
const healthStatus =
  document.getElementById("healthStatus");
const errorMessage =
  document.getElementById("errorMessage");
const successMessage =
  document.getElementById("successMessage");
const portfolioFilterForm =
  document.getElementById("portfolioFilterForm");
const portfolioAsOf =
  document.getElementById("portfolioAsOf");
const portfolioCount =
  document.getElementById("portfolioCount");
const portfolioList =
  document.getElementById("portfolioList");
const collectionDetailPanel =
  document.getElementById("collectionDetailPanel");
const collectionDetailTitle =
  document.getElementById("collectionDetailTitle");
const collectionDetailSummary =
  document.getElementById("collectionDetailSummary");
const activityForm =
  document.getElementById("activityForm");
const activityChannel =
  document.getElementById("activityChannel");
const activityOutcome =
  document.getElementById("activityOutcome");
const activityContactedAt =
  document.getElementById("activityContactedAt");
const activityNextFollowUpAt =
  document.getElementById(
    "activityNextFollowUpAt"
  );
const activityNotes =
  document.getElementById("activityNotes");
const promiseForm =
  document.getElementById("promiseForm");
const promiseAmount =
  document.getElementById("promiseAmount");
const promiseDueDate =
  document.getElementById("promiseDueDate");
const promiseNotes =
  document.getElementById("promiseNotes");
const collectionActivityHistory =
  document.getElementById(
    "collectionActivityHistory"
  );
const paymentPromiseHistory =
  document.getElementById(
    "paymentPromiseHistory"
  );
const overduePromiseList =
  document.getElementById("overduePromiseList");
const portfolioTitle =
  document.getElementById("portfolioTitle");
const portfolioNotice =
  document.getElementById("portfolioNotice");
const assignmentStatusField =
  document.getElementById("assignmentStatusField");
const assignmentStatus =
  document.getElementById("assignmentStatus");
const collectorAssignmentPanel =
  document.getElementById("collectorAssignmentPanel");
const collectorAssignmentForm =
  document.getElementById("collectorAssignmentForm");
const collectorAssignmentUser =
  document.getElementById("collectorAssignmentUser");
const releaseCollectorAssignment =
  document.getElementById(
    "releaseCollectorAssignment"
  );
const collectorAssignmentHistory =
  document.getElementById(
    "collectorAssignmentHistory"
  );


function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}


function formatMoney(value) {
  return new Intl.NumberFormat(
    "es-DO",
    {
      style: "currency",
      currency: "DOP"
    }
  ).format(Number(value || 0));
}


function formatDate(value) {
  if (!value) {
    return "—";
  }

  return new Intl.DateTimeFormat(
    "es-DO",
    {dateStyle: "medium"}
  ).format(
    new Date(`${value}T12:00:00`)
  );
}


function formatDateTime(value) {
  if (!value) {
    return "—";
  }

  return new Intl.DateTimeFormat(
    "es-DO",
    {
      dateStyle: "medium",
      timeStyle: "short"
    }
  ).format(new Date(value));
}


function formatRole(value) {
  const labels = {
    owner: "Propietario",
    administrator: "Administrador",
    supervisor: "Supervisor",
    collector: "Cobrador"
  };

  return labels[value] || value;
}


function formatPromiseStatus(value) {
  const labels = {
    pending: "Pendiente",
    partial: "Parcial",
    fulfilled: "Cumplida",
    cancelled: "Cancelada"
  };

  return labels[value] || value;
}


function formatChannel(value) {
  const labels = {
    phone: "Llamada",
    whatsapp: "WhatsApp",
    sms: "SMS",
    email: "Correo",
    visit: "Visita",
    other: "Otro"
  };

  return labels[value] || value;
}


function localDateValue(date = new Date()) {
  const year = date.getFullYear();
  const month = String(
    date.getMonth() + 1
  ).padStart(2, "0");
  const day = String(
    date.getDate()
  ).padStart(2, "0");

  return `${year}-${month}-${day}`;
}


function localDateTimeValue(date = new Date()) {
  const hours = String(
    date.getHours()
  ).padStart(2, "0");
  const minutes = String(
    date.getMinutes()
  ).padStart(2, "0");

  return `${localDateValue(date)}T${hours}:${minutes}`;
}


function setDefaults() {
  portfolioAsOf.value = localDateValue();
  activityContactedAt.value =
    localDateTimeValue();
  promiseDueDate.value = localDateValue();
}


function setAuthenticatedUI(authenticated) {
  authPanel.hidden = authenticated;
  collectionsWorkspace.hidden = !authenticated;
  logoutButton.hidden = !authenticated;
  clientContext.hidden = !authenticated;
}


function showError(message) {
  errorMessage.textContent = message;
  errorMessage.hidden = false;
  successMessage.hidden = true;
}


function showSuccess(message) {
  successMessage.textContent = message;
  successMessage.hidden = false;
  errorMessage.hidden = true;

  window.setTimeout(() => {
    successMessage.hidden = true;
  }, 3500);
}


function clearMessages() {
  errorMessage.hidden = true;
  successMessage.hidden = true;
}


let collectionWritePending = 0;
async function apiRequest(path, options = {}) {
  const writing = ["POST", "PATCH", "PUT", "DELETE"].includes(options.method);
  if (writing) collectionWritePending++;
  try { return await collectionRequest(path, options); }
  finally { if (writing) collectionWritePending--; }
}
async function collectionRequest(path, options = {}) {
  const response = await fetch(
    `${API_BASE}${path}`,
    {
      headers: {
        "Content-Type": "application/json",
        ...(tenantId
          ? {"X-Tenant-ID": tenantId}
          : {}),
        ...(options.headers || {})
      },
      ...options
    }
  );

  if (!response.ok) {
    let detail =
      `Solicitud fallida (${response.status})`;

    try {
      const body = await response.json();

      if (typeof body.detail === "string") {
        detail = body.detail;
      }
    } catch {
      // Preserve the safe default.
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
    const health = await apiRequest("/health");
    healthStatus.textContent = `API: ${health.status}`;
  } catch {
    healthStatus.textContent = "API no disponible";
  }
}


async function discoverAccess() {
  const access = await apiRequest(
    "/auth/products/prestamodesk/access"
  );

  if (access.clients.length === 0) {
    throw new Error(
      "Su cuenta no tiene acceso activo a PréstamoDesk."
    );
  }

  if (access.clients.length > 1) {
    throw new Error(
      "Su cuenta tiene varios clientes. "
      + "La selección de cliente aún no está disponible."
    );
  }

  const client = access.clients[0];

  if (!["owner", "administrator", "supervisor", "collector"].includes(client.role)) {
    throw new Error(
      "Esta cuenta no tiene acceso a gestión de cobros."
    );
  }

  currentRole = client.role;
  tenantId = String(client.tenant_id);
  localStorage.setItem(
    TENANT_STORAGE_KEY,
    tenantId
  );

  clientContext.textContent =
    `Cliente #${client.client_number} · `
    + `${client.name} · ${formatRole(client.role)}`;

  supervisionLink.hidden =
    !["owner", "administrator", "supervisor"].includes(client.role);

  const isOwner = ["owner", "administrator", "supervisor"].includes(client.role);

  assignmentStatusField.hidden = !isOwner;
  collectorAssignmentPanel.hidden = !isOwner;
  document.getElementById("collectionAssignmentTab").hidden = !isOwner;
  if (!isOwner && collectionDetailPanel.dataset.collectionDetail === "assignment") setCollectionDetailTask("activity");

  if (isOwner) {
    portfolioTitle.textContent = "Cartera vencida";
    portfolioNotice.textContent =
      "Incluye todos los préstamos vencidos del cliente. "
      + "Puede filtrar y administrar sus asignaciones.";
  } else {
    portfolioTitle.textContent = "Mi cartera";
    portfolioNotice.textContent =
      "Muestra solamente los préstamos vencidos "
      + "asignados a su usuario.";
  }
}


function renderCollectorOptions() {
  collectorAssignmentUser.innerHTML = `
    <option value="">Seleccione un cobrador</option>
    ${availableCollectors.map(collector => `
      <option value="${collector.user_id}">
        ${escapeHtml(collector.display_name)}
        · ${escapeHtml(collector.email)}
      </option>
    `).join("")}
  `;
}


async function loadCollectors() {
  if (!["owner", "administrator", "supervisor"].includes(currentRole)) {
    availableCollectors = [];
    return;
  }

  availableCollectors = await apiRequest(
    `${PRODUCT_BASE}/collections/collectors`
  );
  renderCollectorOptions();
}


function renderAssignments(items) {
  const active = items.find(item => item.is_active);

  releaseCollectorAssignment.hidden = !active;

  if (active) {
    collectorAssignmentUser.value =
      String(active.collector_user_id);
  } else {
    collectorAssignmentUser.value = "";
  }

  if (items.length === 0) {
    collectorAssignmentHistory.innerHTML =
      '<p class="empty">No hay asignaciones registradas.</p>';
    return;
  }

  collectorAssignmentHistory.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Cobrador</th>
          <th>Asignada</th>
          <th>Liberada</th>
          <th>Estado</th>
          <th>Motivo</th>
        </tr>
      </thead>
      <tbody>
        ${items.map(item => `
          <tr>
            <td>
              <strong>${escapeHtml(
                item.collector_display_name
              )}</strong><br>
              ${escapeHtml(item.collector_email)}
            </td>
            <td>${formatDateTime(item.assigned_at)}</td>
            <td>${formatDateTime(item.released_at)}</td>
            <td>
              ${item.is_active ? "Activa" : "Finalizada"}
            </td>
            <td>
              ${escapeHtml(item.release_reason || "—")}
            </td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}


function renderPortfolio(items) {
  portfolioCount.textContent = String(items.length);

  if (items.length === 0) {
    portfolioList.innerHTML =
      '<p class="empty">No hay cartera vencida.</p>';
    return;
  }

  portfolioList.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Préstamo</th>
          <th>Cliente</th>
          <th>Contacto</th>
          <th>Vencimiento más antiguo</th>
          <th>Días vencidos</th>
          <th>Cuotas</th>
          <th>Saldo vencido</th>
          <th>Cobrador asignado</th>
          <th>Acción</th>
        </tr>
      </thead>
      <tbody>
        ${items.map(item => `
          <tr>
            <td>#${item.loan_id}</td>
            <td>
              <strong>${escapeHtml(
                item.borrower_full_name
              )}</strong><br>
              ${escapeHtml(
                item.borrower_document_number || "—"
              )}
            </td>
            <td>
              ${escapeHtml(
                item.borrower_phone || "—"
              )}<br>
              ${escapeHtml(
                item.borrower_email || "—"
              )}
            </td>
            <td>${formatDate(
              item.oldest_due_date
            )}</td>
            <td>${item.days_overdue}</td>
            <td>${item.overdue_installment_count}</td>
            <td>
              <strong>${formatMoney(
                item.total_balance_due
              )}</strong>
            </td>
            <td>
              ${escapeHtml(
                item.assigned_collector_display_name
                || "Sin asignar"
              )}
            </td>
            <td>
              <button
                type="button"
                class="secondary"
                data-manage-loan="${item.loan_id}"
              >
                Gestionar
              </button>
            </td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}


async function loadPortfolio() {
  clearMessages();

  const params = new URLSearchParams({
    as_of: portfolioAsOf.value
  });

  if (["owner", "administrator", "supervisor"].includes(currentRole)) {
    params.set(
      "assignment_status",
      assignmentStatus.value
    );
  }
  const items = await apiRequest(
    `${PRODUCT_BASE}/collections/portfolio?${params}`
  );

  renderPortfolio(items);
  return items;
}


function renderActivities(items) {
  if (items.length === 0) {
    collectionActivityHistory.innerHTML =
      '<p class="empty">No hay gestiones registradas.</p>';
    return;
  }

  collectionActivityHistory.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Contacto</th>
          <th>Canal</th>
          <th>Resultado</th>
          <th>Seguimiento</th>
          <th>Notas</th>
        </tr>
      </thead>
      <tbody>
        ${items.map(item => `
          <tr>
            <td>${formatDateTime(
              item.contacted_at
            )}</td>
            <td>${escapeHtml(
              formatChannel(item.channel)
            )}</td>
            <td>${escapeHtml(item.outcome)}</td>
            <td>${formatDateTime(
              item.next_follow_up_at
            )}</td>
            <td>${escapeHtml(item.notes || "—")}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}


function renderPromises(items) {
  if (items.length === 0) {
    paymentPromiseHistory.innerHTML =
      '<p class="empty">No hay promesas registradas.</p>';
    return;
  }

  paymentPromiseHistory.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Fecha prometida</th>
          <th>Prometido</th>
          <th>Cumplido</th>
          <th>Pendiente</th>
          <th>Estado</th>
          <th>Notas</th>
          <th>Acción</th>
        </tr>
      </thead>
      <tbody>
        ${items.map(item => `
          <tr>
            <td>${formatDate(item.due_date)}</td>
            <td>${formatMoney(
              item.promised_amount
            )}</td>
            <td>${formatMoney(
              item.fulfilled_amount
            )}</td>
            <td>${formatMoney(
              item.remaining_amount
            )}</td>
            <td>
              ${escapeHtml(
                formatPromiseStatus(item.status)
              )}
              ${item.is_overdue ? " · Vencida" : ""}
            </td>
            <td>${escapeHtml(item.notes || "—")}</td>
            <td>
              ${["pending", "partial"].includes(
                item.status
              ) ? `
                <button
                  type="button"
                  class="secondary"
                  data-cancel-promise="${item.id}"
                >
                  Cancelar
                </button>
              ` : "—"}
            </td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}


function renderOverduePromises(items) {
  if (items.length === 0) {
    overduePromiseList.innerHTML =
      '<p class="empty">No hay promesas vencidas.</p>';
    return;
  }

  overduePromiseList.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Préstamo</th>
          <th>Fecha</th>
          <th>Prometido</th>
          <th>Cumplido</th>
          <th>Pendiente</th>
          <th>Estado</th>
        </tr>
      </thead>
      <tbody>
        ${items.map(item => `
          <tr>
            <td>#${item.loan_id}</td>
            <td>${formatDate(item.due_date)}</td>
            <td>${formatMoney(
              item.promised_amount
            )}</td>
            <td>${formatMoney(
              item.fulfilled_amount
            )}</td>
            <td>
              <strong>${formatMoney(
                item.remaining_amount
              )}</strong>
            </td>
            <td>${escapeHtml(
              formatPromiseStatus(item.status)
            )}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}


async function loadLoanHistory() {
  if (!selectedPortfolioItem) {
    return;
  }

  const loanId = selectedPortfolioItem.loan_id;
  const requests = [
    apiRequest(
      `${PRODUCT_BASE}/collections/loans/`
      + `${loanId}/activities`
    ),
    apiRequest(
      `${PRODUCT_BASE}/collections/loans/`
      + `${loanId}/promises`
    )
  ];

  if (["owner", "administrator", "supervisor"].includes(currentRole)) {
    requests.push(
      apiRequest(
        `${PRODUCT_BASE}/collections/loans/`
        + `${loanId}/assignments`
      )
    );
  }

  const [activities, promises, assignments] =
    await Promise.all(requests);

  renderActivities(activities);
  renderPromises(promises);

  if (["owner", "administrator", "supervisor"].includes(currentRole)) {
    renderAssignments(assignments);
  }
}


async function loadOverduePromises() {
  const params = new URLSearchParams({
    overdue_only: "true",
    as_of: portfolioAsOf.value
  });
  const promises = await apiRequest(
    `${PRODUCT_BASE}/collections/promises?${params}`
  );

  renderOverduePromises(promises);
}


function setCollectionTask(task) {
  collectionsWorkspace.dataset.collectionTask = task;
  document.querySelectorAll("button[data-collection-task]").forEach(button => {
    button.setAttribute("aria-pressed", String(button.dataset.collectionTask === task));
  });
}
function setCollectionDetailTask(task) {
  collectionDetailPanel.dataset.collectionDetail = task;
  document.querySelectorAll("button[data-collection-detail]").forEach(button => {
    button.setAttribute("aria-pressed", String(button.dataset.collectionDetail === task));
  });
}
function canSwitchCollectionTask() {
  if (!collectionWritePending) return true;
  showError("Espere la confirmación de la gestión antes de cambiar de tarea.");
  return false;
}
document.getElementById("collectionTaskToolbar").addEventListener("click", event => {
  const button = event.target.closest("button[data-collection-task]");
  if (button && canSwitchCollectionTask()) setCollectionTask(button.dataset.collectionTask);
});
document.getElementById("collectionDetailToolbar").addEventListener("click", event => {
  const button = event.target.closest("button[data-collection-detail]");
  if (!button || button.hidden || !canSwitchCollectionTask()) return;
  if (button.dataset.collectionDetail === "assignment" && !["owner","administrator","supervisor"].includes(currentRole)) return;
  setCollectionDetailTask(button.dataset.collectionDetail);
});

async function openLoan(item) {
  if (!canSwitchCollectionTask()) return;
  setCollectionTask("portfolio");
  setCollectionDetailTask("activity");
  selectedPortfolioItem = item;

  collectionDetailTitle.textContent =
    `Préstamo #${item.loan_id} · `
    + item.borrower_full_name;

  collectionDetailSummary.innerHTML = `
    <p>
      Documento:
      <strong>${escapeHtml(
        item.borrower_document_number || "—"
      )}</strong>
    </p>
    <p>
      Teléfono:
      <strong>${escapeHtml(
        item.borrower_phone || "—"
      )}</strong>
    </p>
    <p>
      Correo:
      <strong>${escapeHtml(
        item.borrower_email || "—"
      )}</strong>
    </p>
    <p>
      Saldo vencido:
      <strong>${formatMoney(
        item.total_balance_due
      )}</strong>
    </p>
    <p>
      Cobrador asignado:
      <strong>${escapeHtml(
        item.assigned_collector_display_name
        || "Sin asignar"
      )}</strong>
    </p>
  `;

  promiseAmount.max = item.total_balance_due;
  collectionDetailPanel.hidden = false;
  await loadLoanHistory();
}


portfolioFilterForm.addEventListener(
  "submit",
  async event => {
    event.preventDefault();

    try {
      await Promise.all([
        loadPortfolio(),
        loadOverduePromises()
      ]);
    } catch (error) {
      showError(error.message);
    }
  }
);


document.getElementById(
  "refreshPortfolioButton"
).addEventListener(
  "click",
  async () => {
    try {
      await Promise.all([
        loadPortfolio(),
        loadOverduePromises()
      ]);
    } catch (error) {
      showError(error.message);
    }
  }
);


document.getElementById(
  "refreshOverduePromisesButton"
).addEventListener(
  "click",
  async () => {
    try {
      await loadOverduePromises();
    } catch (error) {
      showError(error.message);
    }
  }
);


portfolioList.addEventListener(
  "click",
  async event => {
    const button = event.target.closest(
      "[data-manage-loan]"
    );

    if (!button) {
      return;
    }

    try {
      const items = await loadPortfolio();
      const item = items.find(
        candidate =>
          candidate.loan_id
          === Number(button.dataset.manageLoan)
      );

      if (item) {
        await openLoan(item);
      }
    } catch (error) {
      showError(error.message);
    }
  }
);


document.getElementById(
  "closeCollectionDetail"
).addEventListener(
  "click",
  () => {
    if (!canSwitchCollectionTask()) return;
    selectedPortfolioItem = null;
    collectionDetailPanel.hidden = true;
  }
);


activityForm.addEventListener(
  "submit",
  async event => {
    event.preventDefault();
    clearMessages();

    if (!selectedPortfolioItem) {
      return;
    }

    try {
      await apiRequest(
        `${PRODUCT_BASE}/collections/loans/`
        + `${selectedPortfolioItem.loan_id}/activities`,
        {
          method: "POST",
          body: JSON.stringify({
            channel: activityChannel.value,
            outcome: activityOutcome.value.trim(),
            notes:
              activityNotes.value.trim() || null,
            contacted_at: new Date(
              activityContactedAt.value
            ).toISOString(),
            next_follow_up_at:
              activityNextFollowUpAt.value
                ? new Date(
                    activityNextFollowUpAt.value
                  ).toISOString()
                : null
          })
        }
      );

      activityForm.reset();
      activityContactedAt.value =
        localDateTimeValue();
      await loadLoanHistory();
      showSuccess("Gestión registrada.");
    } catch (error) {
      showError(error.message);
    }
  }
);


collectorAssignmentForm.addEventListener(
  "submit",
  async event => {
    event.preventDefault();
    clearMessages();

    if (
      !["owner", "administrator", "supervisor"].includes(currentRole)
      || !selectedPortfolioItem
    ) {
      return;
    }

    try {
      await apiRequest(
        `${PRODUCT_BASE}/collections/loans/`
        + `${selectedPortfolioItem.loan_id}/assignment`,
        {
          method: "POST",
          body: JSON.stringify({
            collector_user_id: Number(
              collectorAssignmentUser.value
            )
          })
        }
      );

      const refreshedItems = await loadPortfolio();
      selectedPortfolioItem = refreshedItems.find(
        item =>
          item.loan_id === selectedPortfolioItem.loan_id
      ) || selectedPortfolioItem;

      await loadLoanHistory();
      showSuccess("Cobrador asignado.");
    } catch (error) {
      showError(error.message);
    }
  }
);


releaseCollectorAssignment.addEventListener(
  "click",
  async () => {
    clearMessages();

    if (
      !["owner", "administrator", "supervisor"].includes(currentRole)
      || !selectedPortfolioItem
    ) {
      return;
    }

    const confirmed = window.confirm(
      "¿Desea liberar esta asignación?"
    );

    if (!confirmed) {
      return;
    }

    try {
      await apiRequest(
        `${PRODUCT_BASE}/collections/loans/`
        + `${selectedPortfolioItem.loan_id}`
        + "/assignment/release",
        {
          method: "POST",
          body: JSON.stringify({
            reason: "Liberada desde gestión de cobros"
          })
        }
      );

      const refreshedItems = await loadPortfolio();
      selectedPortfolioItem = refreshedItems.find(
        item =>
          item.loan_id === selectedPortfolioItem.loan_id
      ) || {
        ...selectedPortfolioItem,
        assigned_collector_user_id: null,
        assigned_collector_display_name: null
      };

      await loadLoanHistory();
      showSuccess("Asignación liberada.");
    } catch (error) {
      showError(error.message);
    }
  }
);


promiseForm.addEventListener(
  "submit",
  async event => {
    event.preventDefault();
    clearMessages();

    if (!selectedPortfolioItem) {
      return;
    }

    try {
      await apiRequest(
        `${PRODUCT_BASE}/collections/loans/`
        + `${selectedPortfolioItem.loan_id}/promises`,
        {
          method: "POST",
          body: JSON.stringify({
            promised_amount: promiseAmount.value,
            due_date: promiseDueDate.value,
            notes:
              promiseNotes.value.trim() || null
          })
        }
      );

      promiseForm.reset();
      promiseDueDate.value = localDateValue();
      await Promise.all([
        loadLoanHistory(),
        loadOverduePromises()
      ]);
      showSuccess("Promesa de pago registrada.");
    } catch (error) {
      showError(error.message);
    }
  }
);


paymentPromiseHistory.addEventListener(
  "click",
  async event => {
    const button = event.target.closest(
      "[data-cancel-promise]"
    );

    if (!button) {
      return;
    }

    try {
      await apiRequest(
        `${PRODUCT_BASE}/collections/promises/`
        + `${button.dataset.cancelPromise}/cancel`,
        {
          method: "POST",
          body: JSON.stringify({notes: null})
        }
      );

      await Promise.all([
        loadLoanHistory(),
        loadOverduePromises()
      ]);
      showSuccess("Promesa cancelada.");
    } catch (error) {
      showError(error.message);
    }
  }
);


loginForm.addEventListener(
  "submit",
  async event => {
    event.preventDefault();
    clearMessages();

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

      await discoverAccess();
      await loadCollectors();
      await Promise.all([
        loadPortfolio(),
        loadOverduePromises()
      ]);
      loginForm.reset();
      setAuthenticatedUI(true);
      showSuccess("Sesión de cobros iniciada.");
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
        {method: "POST"}
      );
    } catch {
      // Continue local sign-out.
    }

    tenantId = null;
    localStorage.removeItem(TENANT_STORAGE_KEY);
    location.reload();
  }
);


async function initialize() {
  await checkHealth();
  setDefaults();

  if (!tenantId) {
    setAuthenticatedUI(false);
    return;
  }

  try {
    await discoverAccess();
    await loadCollectors();
    await Promise.all([
      loadPortfolio(),
      loadOverduePromises()
    ]);
    setAuthenticatedUI(true);
  } catch {
    tenantId = null;
    localStorage.removeItem(TENANT_STORAGE_KEY);
    setAuthenticatedUI(false);
  }
}


initialize();

return {canLeave: () => !(typeof collectionWritePending !== "undefined" && collectionWritePending) && !(typeof cashClosingSubmitting !== "undefined" && cashClosingSubmitting) && !(typeof paymentSubmitting !== "undefined" && paymentSubmitting) && !(typeof paymentNeedsReview !== "undefined" && paymentNeedsReview) && (!window.prestamodeskInvitationSharing || window.prestamodeskInvitationSharing.canLeave()) && (!window.prestamodeskLoanCreation || window.prestamodeskLoanCreation.canLeave()) && (!window.prestamodeskBorrowerContact || window.prestamodeskBorrowerContact.canLeave()), confirmLeave: () => typeof collectionWritePending !== "undefined" && collectionWritePending ? false : typeof cashClosingSubmitting !== "undefined" && cashClosingSubmitting ? false : window.prestamodeskLoanCreation && !window.prestamodeskLoanCreation.canLeave() ? false : (typeof paymentSubmitting !== "undefined" && paymentSubmitting) || (typeof paymentNeedsReview !== "undefined" && paymentNeedsReview) ? false : window.prestamodeskBorrowerContact && !window.prestamodeskBorrowerContact.canLeave() ? window.prestamodeskBorrowerContact.confirmLeave() : window.prestamodeskInvitationSharing ? window.prestamodeskInvitationSharing.confirmLeave() : false, leaveMessage: () => typeof collectionWritePending !== "undefined" && collectionWritePending ? "Espere la confirmación de la gestión antes de cambiar de sección." : typeof cashClosingSubmitting !== "undefined" && cashClosingSubmitting ? "Espere la confirmación del cierre de caja antes de cambiar de sección." : window.prestamodeskLoanCreation && !window.prestamodeskLoanCreation.canLeave() ? window.prestamodeskLoanCreation.leaveMessage : window.prestamodeskBorrowerContact && !window.prestamodeskBorrowerContact.canLeave() ? window.prestamodeskBorrowerContact.leaveMessage : window.prestamodeskInvitationSharing ? window.prestamodeskInvitationSharing.leaveMessage : "Revise el resultado del pago en Caja antes de cambiar de sección."};
}},
"supervision": {html:"\n  <header class=\"app-header\">\n    <div>\n      <span class=\"eyebrow\">FieldLookers</span>\n      <h1>PréstamoDesk · Supervisión de cobros</h1>\n      <p>\n        Resultados generales y desempeño del equipo de cobros\n      </p>\n    </div>\n\n    <div class=\"header-actions\"><a href=\"/prestamodesk/workspace\">Mi espacio · Todas las secciones</a>\n      <a href=\"/prestamodesk/cobros\">\n        Gestión de cobros\n      </a>\n      <span id=\"clientContext\" class=\"badge\" hidden></span>\n      <span id=\"healthStatus\">Comprobando API…</span>\n      <button id=\"logoutButton\" class=\"secondary\" hidden>\n        Cerrar sesión\n      </button>\n    </div>\n  </header>\n\n  <main>\n    <div id=\"errorMessage\" class=\"message error\" hidden></div>\n\n    <section id=\"authPanel\" class=\"panel auth-panel\">\n      <h2>Iniciar sesión en supervisión de cobros</h2>\n      <p class=\"supervision-hint\">\n        Disponible para propietarios, administradores y supervisores.\n      </p>\n\n      <form id=\"loginForm\" class=\"form-grid\">\n        <label>\n          Correo electrónico\n          <input\n            id=\"loginEmail\"\n            type=\"email\"\n            autocomplete=\"username\"\n            required\n          >\n        </label>\n\n        <label>\n          Contraseña\n          <input\n            id=\"loginPassword\"\n            type=\"password\"\n            autocomplete=\"current-password\"\n            required\n          >\n        </label>\n\n        <button type=\"submit\">Iniciar sesión</button>\n      </form>\n    </section>\n\n    <div id=\"supervisionWorkspace\" data-supervision-task=\"overview\" hidden>\n      <section class=\"panel\">\n        <div class=\"panel-heading\">\n          <div>\n            <h2>Supervisión de cobros</h2>\n            <p class=\"supervision-hint\">\n              Las gestiones, promesas y cobros recuperados\n              incluyen todo el historial. La fecha de corte\n              se aplica a la cartera y promesas vencidas.\n            </p>\n          </div>\n\n          <div>\n            <button\n              id=\"exportSupervisionButton\"\n              type=\"button\"\n              class=\"secondary\"\n            >\n              Exportar CSV\n            </button>\n\n            <button\n              id=\"refreshSupervisionButton\"\n              type=\"button\"\n              class=\"secondary\"\n            >\n              Actualizar\n            </button>\n          </div>\n        </div>\n\n        <form id=\"supervisionFilterForm\" class=\"form-grid\">\n          <label>\n            Fecha de corte\n            <input\n              id=\"supervisionAsOf\"\n              type=\"date\"\n              required\n            >\n          </label>\n\n          <button type=\"submit\">Consultar supervisión</button>\n        </form>\n\n              </section>\n      <nav id=\"supervisionTaskToolbar\" class=\"supervision-toolbar\" aria-label=\"Reportes de supervisión\">\n        <button type=\"button\" data-supervision-task=\"overview\" aria-pressed=\"true\" aria-controls=\"supervisionOverviewPanel supervisionDailyPanel\">Resumen</button>\n        <button type=\"button\" data-supervision-task=\"aging\" aria-pressed=\"false\" aria-controls=\"supervisionAgingPanel\">Cartera vencida</button>\n        <button type=\"button\" data-supervision-task=\"promises\" aria-pressed=\"false\" aria-controls=\"supervisionPromisesPanel\">Promesas</button>\n        <button type=\"button\" data-supervision-task=\"team\" aria-pressed=\"false\" aria-controls=\"supervisionTeamPanel\">Equipo</button>\n      </nav>\n      <section id=\"supervisionOverviewPanel\" class=\"panel\" data-supervision-panel=\"overview\">\n        <h2>Resumen general</h2>\n        <div id=\"generalSummary\" class=\"summary-grid\"></div>\n      </section>\n\n      <section id=\"supervisionDailyPanel\" class=\"panel\" data-supervision-panel=\"overview\">\n        <h2>Prioridades del día</h2>\n        <div\n          id=\"dailyOperationsSummary\"\n          class=\"summary-grid\"\n        ></div>\n      </section>\n\n      <section id=\"supervisionAgingPanel\" class=\"panel\" data-supervision-panel=\"aging\">\n        <h2>Antigüedad de la cartera vencida</h2>\n        <div id=\"agingSummary\" class=\"summary-grid\"></div>\n      </section>\n\n      <section id=\"supervisionPromisesPanel\" class=\"panel\" data-supervision-panel=\"promises\">\n        <h2>Promesas de pago</h2>\n        <div id=\"promiseSummary\" class=\"summary-grid\"></div>\n      </section>\n\n      <section id=\"supervisionTeamPanel\" class=\"panel\" data-supervision-panel=\"team\">\n        <div class=\"panel-heading\">\n          <div>\n            <h2>Desempeño por cobrador</h2>\n            <p class=\"supervision-hint\">\n              El monto recuperado se presenta solamente como\n              total general. No se atribuyen pagos a un\n              cobrador individual.\n            </p>\n          </div>\n        </div>\n\n        <div\n          id=\"collectorPerformance\"\n          class=\"table-wrap\"\n        ></div>\n      </section>\n    </div>\n  </main>\n\n  <footer>\n    <span>PréstamoDesk · FieldLookers</span>\n  </footer>\n\n  \n", start: function(document, window, fetch, localStorage, location, setTimeout, clearTimeout) {
const API_BASE = "/api/v1";
const PRODUCT_BASE = "/products/prestamodesk";
const TENANT_STORAGE_KEY =
  "prestamodesk_collections_tenant_id";

let tenantId = localStorage.getItem(
  TENANT_STORAGE_KEY
);

const authPanel = document.getElementById("authPanel");
const supervisionWorkspace =
  document.getElementById("supervisionWorkspace");
const loginForm = document.getElementById("loginForm");
const loginEmail = document.getElementById("loginEmail");
const loginPassword =
  document.getElementById("loginPassword");
const logoutButton =
  document.getElementById("logoutButton");
const clientContext =
  document.getElementById("clientContext");
const healthStatus =
  document.getElementById("healthStatus");
const errorMessage =
  document.getElementById("errorMessage");
const supervisionFilterForm =
  document.getElementById("supervisionFilterForm");
const supervisionAsOf =
  document.getElementById("supervisionAsOf");
const exportSupervisionButton =
  document.getElementById(
    "exportSupervisionButton"
  );
const refreshSupervisionButton =
  document.getElementById(
    "refreshSupervisionButton"
  );
const generalSummary =
  document.getElementById("generalSummary");
const dailyOperationsSummary =
  document.getElementById("dailyOperationsSummary");
const agingSummary =
  document.getElementById("agingSummary");
const promiseSummary =
  document.getElementById("promiseSummary");
const collectorPerformance =
  document.getElementById("collectorPerformance");


function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}


function formatMoney(value) {
  return new Intl.NumberFormat(
    "es-DO",
    {
      style: "currency",
      currency: "DOP"
    }
  ).format(Number(value || 0));
}


function formatPercent(value) {
  return new Intl.NumberFormat(
    "es-DO",
    {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }
  ).format(Number(value || 0)) + "%";
}


function localDateValue(date = new Date()) {
  const year = date.getFullYear();
  const month = String(
    date.getMonth() + 1
  ).padStart(2, "0");
  const day = String(
    date.getDate()
  ).padStart(2, "0");

  return `${year}-${month}-${day}`;
}


function setAuthenticatedUI(authenticated) {
  authPanel.hidden = authenticated;
  supervisionWorkspace.hidden = !authenticated;
  logoutButton.hidden = !authenticated;
  clientContext.hidden = !authenticated;
}


function showError(message) {
  errorMessage.textContent = message;
  errorMessage.hidden = false;
}


function clearError() {
  errorMessage.hidden = true;
}


async function apiRequest(path, options = {}) {
  const response = await fetch(
    `${API_BASE}${path}`,
    {
      headers: {
        "Content-Type": "application/json",
        ...(tenantId
          ? {"X-Tenant-ID": tenantId}
          : {}),
        ...(options.headers || {})
      },
      ...options
    }
  );

  if (!response.ok) {
    let detail =
      `Solicitud fallida (${response.status})`;

    try {
      const body = await response.json();

      if (typeof body.detail === "string") {
        detail = body.detail;
      }
    } catch {
      // Preserve the safe default.
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
    const health = await apiRequest("/health");
    healthStatus.textContent = `API: ${health.status}`;
  } catch {
    healthStatus.textContent = "API no disponible";
  }
}


async function discoverAccess() {
  const access = await apiRequest(
    "/auth/products/prestamodesk/access"
  );

  if (access.clients.length === 0) {
    throw new Error(
      "Su cuenta no tiene acceso activo a PréstamoDesk."
    );
  }

  if (access.clients.length > 1) {
    throw new Error(
      "Su cuenta tiene varios clientes. "
      + "La selección de cliente aún no está disponible."
    );
  }

  const client = access.clients[0];

  if (client.role === "collector") {
    window.location.replace(
      "/prestamodesk/cobros"
    );
    return false;
  }

  if (!["owner", "administrator", "supervisor"].includes(client.role)) {
    throw new Error(
      "La supervisión requiere rol de propietario, administrador o supervisor."
    );
  }

  tenantId = String(client.tenant_id);
  localStorage.setItem(
    TENANT_STORAGE_KEY,
    tenantId
  );

  clientContext.textContent =
    `Cliente #${client.client_number} · `
    + `${client.name} · ${client.role}`;

  return true;
}


function metric(label, value) {
  return `
    <section>
      <span class="eyebrow">${escapeHtml(label)}</span>
      <h3>${escapeHtml(value)}</h3>
    </section>
  `;
}


function renderGeneralSummary(data) {
  generalSummary.innerHTML = [
    metric(
      "Préstamos vencidos",
      data.overdue_loan_count
    ),
    metric(
      "Saldo vencido",
      formatMoney(data.overdue_balance)
    ),
    metric(
      "Préstamos asignados",
      data.assigned_overdue_loan_count
    ),
    metric(
      "Saldo asignado",
      formatMoney(data.assigned_overdue_balance)
    ),
    metric(
      "Préstamos sin asignar",
      data.unassigned_overdue_loan_count
    ),
    metric(
      "Saldo sin asignar",
      formatMoney(data.unassigned_overdue_balance)
    ),
    metric(
      "Total recuperado",
      formatMoney(data.total_recovered)
    ),
    metric(
      "Gestiones registradas",
      data.activity_count
    ),
    metric(
      "Promesas registradas",
      data.promise_count
    ),
    metric(
      "Promesas vencidas",
      data.overdue_promise_count
    )
  ].join("");
}


function renderDailyOperations(data) {
  dailyOperationsSummary.innerHTML = [
    metric(
      "Promesas para hoy",
      data.promises_due_today_count
    ),
    metric(
      "Seguimientos para hoy",
      data.follow_ups_due_today_count
    ),
    metric(
      "Seguimientos vencidos",
      data.overdue_follow_up_count
    ),
    metric(
      "Promesas vencidas",
      data.overdue_promise_count
    ),
  ].join("");
}

function renderAgingSummary(buckets) {
  agingSummary.innerHTML = buckets.map((bucket) => (
    metric(
      bucket.label,
      `${bucket.loan_count} · ${
        formatMoney(bucket.balance)
      }`
    )
  )).join("");
}

function renderPromiseSummary(data) {
  promiseSummary.innerHTML = [
    metric(
      "Pendientes",
      data.pending_promise_count
    ),
    metric(
      "Parciales",
      data.partial_promise_count
    ),
    metric(
      "Cumplidas",
      data.fulfilled_promise_count
    ),
    metric(
      "Canceladas",
      data.cancelled_promise_count
    ),
    metric(
      "Monto prometido",
      formatMoney(data.promised_amount)
    ),
    metric(
      "Monto cumplido",
      formatMoney(data.fulfilled_amount)
    ),
    metric(
      "Cumplimiento por cantidad",
      formatPercent(
        data.promise_count_fulfillment_percent
      )
    ),
    metric(
      "Cumplimiento por monto",
      formatPercent(
        data.promise_amount_fulfillment_percent
      )
    )
  ].join("");
}


function renderCollectorPerformance(collectors) {
  if (collectors.length === 0) {
    collectorPerformance.innerHTML =
      '<p class="empty">No hay cobradores activos.</p>';
    return;
  }

  const rows = collectors.map(collector => `
    <tr>
      <td>
        <strong>
          ${escapeHtml(collector.display_name)}
        </strong>
        <br>
        <span>
          ${escapeHtml(collector.email)}
        </span>
      </td>
      <td>${collector.active_overdue_loan_count}</td>
      <td>${formatMoney(
        collector.active_overdue_balance
      )}</td>
      <td>${collector.activity_count}</td>
      <td>${collector.promise_count}</td>
      <td>${collector.pending_promise_count}</td>
      <td>${collector.partial_promise_count}</td>
      <td>${collector.fulfilled_promise_count}</td>
      <td>${collector.cancelled_promise_count}</td>
      <td>${collector.overdue_promise_count}</td>
      <td>${formatMoney(collector.promised_amount)}</td>
      <td>${formatMoney(collector.fulfilled_amount)}</td>
      <td>
        ${formatPercent(
          collector.promise_count_fulfillment_percent
        )}
      </td>
      <td>
        ${formatPercent(
          collector.promise_amount_fulfillment_percent
        )}
      </td>
    </tr>
  `).join("");

  collectorPerformance.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Cobrador</th>
          <th>Préstamos asignados</th>
          <th>Saldo asignado</th>
          <th>Gestiones</th>
          <th>Promesas</th>
          <th>Pendientes</th>
          <th>Parciales</th>
          <th>Cumplidas</th>
          <th>Canceladas</th>
          <th>Vencidas</th>
          <th>Prometido</th>
          <th>Cumplido</th>
          <th>Cumplimiento por cantidad</th>
          <th>Cumplimiento por monto</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}


async function exportSupervision() {
  clearError();
  exportSupervisionButton.disabled = true;

  try {
    const params = new URLSearchParams({
      as_of: supervisionAsOf.value
    });
    const response = await fetch(
      `${API_BASE}${PRODUCT_BASE}` +
        `/collections/supervision/export.csv?${params}`,
      {
        headers: {
          "Accept": "text/csv",
          "X-Tenant-ID": tenantId
        }
      }
    );

    if (!response.ok) {
      let message = "No se pudo exportar el reporte.";

      try {
        const error = await response.json();
        message = error.detail || message;
      } catch {
        // Preserve the default export error.
      }

      throw new Error(message);
    }

    const blob = await response.blob();
    const downloadUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = downloadUrl;
    link.download =
      `prestamodesk-cartera-vencida-` +
      `${supervisionAsOf.value}.csv`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(downloadUrl);
  } finally {
    exportSupervisionButton.disabled = false;
  }
}


async function loadSupervision() {
  clearError();

  const params = new URLSearchParams({
    as_of: supervisionAsOf.value
  });
  const data = await apiRequest(
    `${PRODUCT_BASE}/collections/supervision?${params}`
  );

  renderGeneralSummary(data);
  renderDailyOperations(data);
  renderAgingSummary(data.aging_buckets);
  renderPromiseSummary(data);
  renderCollectorPerformance(data.collectors);
}


supervisionFilterForm.addEventListener(
  "submit",
  async event => {
    event.preventDefault();

    try {
      await loadSupervision();
    } catch (error) {
      showError(error.message);
    }
  }
);


exportSupervisionButton.addEventListener(
  "click",
  async () => {
    try {
      await exportSupervision();
    } catch (error) {
      showError(error.message);
    }
  }
);


refreshSupervisionButton.addEventListener(
  "click",
  async () => {
    try {
      await loadSupervision();
    } catch (error) {
      showError(error.message);
    }
  }
);


loginForm.addEventListener(
  "submit",
  async event => {
    event.preventDefault();
    clearError();

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

      const accessGranted = await discoverAccess();

      if (!accessGranted) {
        return;
      }

      await loadSupervision();
      loginForm.reset();
      setAuthenticatedUI(true);
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
        {method: "POST"}
      );
    } catch {
      // Continue local sign-out.
    }

    tenantId = null;
    localStorage.removeItem(TENANT_STORAGE_KEY);
    location.reload();
  }
);


async function initialize() {
  await checkHealth();
  supervisionAsOf.value = localDateValue();

  if (!tenantId) {
    setAuthenticatedUI(false);
    return;
  }

  try {
    const accessGranted = await discoverAccess();

    if (!accessGranted) {
      return;
    }

    await loadSupervision();
    setAuthenticatedUI(true);
  } catch {
    tenantId = null;
    localStorage.removeItem(TENANT_STORAGE_KEY);
    setAuthenticatedUI(false);
  }
}


initialize();

// Report switches retain the loaded snapshot and filter, without requests.
document.getElementById("supervisionTaskToolbar").addEventListener("click", event => {
  const button = event.target.closest("button[data-supervision-task]");
  if (!button) return;
  supervisionWorkspace.dataset.supervisionTask = button.dataset.supervisionTask;
  document.querySelectorAll("button[data-supervision-task]").forEach(item => {
    item.setAttribute("aria-pressed", String(item === button));
  });
});

return {canLeave: () => !(typeof collectionWritePending !== "undefined" && collectionWritePending) && !(typeof cashClosingSubmitting !== "undefined" && cashClosingSubmitting) && !(typeof paymentSubmitting !== "undefined" && paymentSubmitting) && !(typeof paymentNeedsReview !== "undefined" && paymentNeedsReview) && (!window.prestamodeskInvitationSharing || window.prestamodeskInvitationSharing.canLeave()) && (!window.prestamodeskLoanCreation || window.prestamodeskLoanCreation.canLeave()) && (!window.prestamodeskBorrowerContact || window.prestamodeskBorrowerContact.canLeave()), confirmLeave: () => typeof collectionWritePending !== "undefined" && collectionWritePending ? false : typeof cashClosingSubmitting !== "undefined" && cashClosingSubmitting ? false : window.prestamodeskLoanCreation && !window.prestamodeskLoanCreation.canLeave() ? false : (typeof paymentSubmitting !== "undefined" && paymentSubmitting) || (typeof paymentNeedsReview !== "undefined" && paymentNeedsReview) ? false : window.prestamodeskBorrowerContact && !window.prestamodeskBorrowerContact.canLeave() ? window.prestamodeskBorrowerContact.confirmLeave() : window.prestamodeskInvitationSharing ? window.prestamodeskInvitationSharing.confirmLeave() : false, leaveMessage: () => typeof collectionWritePending !== "undefined" && collectionWritePending ? "Espere la confirmación de la gestión antes de cambiar de sección." : typeof cashClosingSubmitting !== "undefined" && cashClosingSubmitting ? "Espere la confirmación del cierre de caja antes de cambiar de sección." : window.prestamodeskLoanCreation && !window.prestamodeskLoanCreation.canLeave() ? window.prestamodeskLoanCreation.leaveMessage : window.prestamodeskBorrowerContact && !window.prestamodeskBorrowerContact.canLeave() ? window.prestamodeskBorrowerContact.leaveMessage : window.prestamodeskInvitationSharing ? window.prestamodeskInvitationSharing.leaveMessage : "Revise el resultado del pago en Caja antes de cambiar de sección."};
}},
"administration": {html:"\n<header class=\"app-header\"><div class=\"brand\"><span class=\"brand-mark\" aria-hidden=\"true\">PD</span><div><h1>PréstamoDesk</h1><p>by FieldLookers</p></div></div><div class=\"header-actions\"><a href=\"/prestamodesk/workspace\">Mi espacio · Todas las secciones</a><a href=\"/prestamodesk/app\">Volver a préstamos</a><span id=\"clientContext\" class=\"badge\" hidden></span><span id=\"healthStatus\">Comprobando API…</span><button id=\"logoutButton\" class=\"secondary\" hidden>Cerrar sesión</button><a id=\"administrationLink\" href=\"/prestamodesk-administracion.html\" hidden aria-label=\"Administración actual\" aria-current=\"page\">Administración</a></div></header>\n<main><div id=\"pageMessage\" class=\"message\" role=\"status\" hidden></div><section id=\"authPanel\" class=\"panel auth-panel\" hidden><h2>Iniciar sesión</h2><form id=\"loginForm\" class=\"form-grid\"><label>Correo electrónico<input id=\"loginEmail\" type=\"email\" autocomplete=\"username\" required></label><label>Contraseña<input id=\"loginPassword\" type=\"password\" autocomplete=\"current-password\" required></label><button type=\"submit\">Iniciar sesión</button></form><a href=\"/prestamodesk/app\">Recuperar contraseña</a></section>\n<section id=\"administrationPanel\" hidden><div class=\"admin-top\"><div><span class=\"page-eyebrow\">GESTIÓN DEL EQUIPO</span><h2>Administración</h2><p>Un solo lugar para gestionar personas, permisos y acceso.</p></div><div class=\"toolbar\"><button id=\"inviteMemberButton\" type=\"button\">Invitar integrante</button><button id=\"administrationRefresh\" type=\"button\" class=\"secondary\">Actualizar</button><details><summary>Más opciones</summary><div class=\"export-menu\"><button id=\"customerExport\" type=\"button\" class=\"secondary\">Descargar datos del cliente</button><p>ZIP con CSV y JSON. Incluye información personal y financiera.</p></div></details></div></div>\n<div id=\"administrationMessage\" class=\"message\" role=\"status\" aria-atomic=\"true\" hidden></div><div id=\"administrationSections\" class=\"admin-tabs\" role=\"tablist\" aria-label=\"Administración\"><button id=\"teamTab\" type=\"button\" role=\"tab\" aria-selected=\"true\" aria-controls=\"teamSection\" data-admin-tab=\"teamSection\">Equipo</button><button id=\"invitationsTab\" type=\"button\" role=\"tab\" aria-selected=\"false\" tabindex=\"-1\" aria-controls=\"invitationsSection\" data-admin-tab=\"invitationsSection\">Invitaciones</button><button id=\"activityTab\" type=\"button\" role=\"tab\" aria-selected=\"false\" tabindex=\"-1\" aria-controls=\"activitySection\" data-admin-tab=\"activitySection\">Actividad</button></div>\n<div class=\"admin-grid\"><div><section id=\"teamSection\" class=\"admin-card\" role=\"tabpanel\" aria-labelledby=\"teamTab\"><div class=\"card-heading\"><div><h3>Integrantes <span id=\"teamCount\" class=\"team-count\">0</span></h3><p>Las personas con acceso a este negocio.</p></div><span class=\"card-label\">Equipo de trabajo</span></div><div class=\"table-wrap\"><table><caption class=\"visually-hidden\">Equipo de este cliente</caption><thead><tr><th scope=\"col\">Integrante</th><th scope=\"col\">Rol</th><th scope=\"col\">Acceso</th><th scope=\"col\">Detalle</th></tr></thead><tbody id=\"administrationMembers\"></tbody></table></div><p class=\"context-note\">Solo el propietario administra propietarios y administradores.</p><nav class=\"related-links\" aria-label=\"Herramientas de cobros\"><a href=\"/prestamodesk/cobros\">Asignar carteras <span aria-hidden=\"true\">↗</span></a><a href=\"/prestamodesk/cobros/supervision\">Supervisión <span aria-hidden=\"true\">↗</span></a></nav></section>\n<section id=\"invitationsSection\" class=\"admin-card\" role=\"tabpanel\" aria-labelledby=\"invitationsTab\" hidden><h3>Invitar integrante</h3>      <form id=\"administrationInvite\" class=\"form-grid\">\n        <label>Nombre <input name=\"display_name\" maxlength=\"200\" required></label>\n        <label>Correo electrónico <input name=\"email\" type=\"email\" maxlength=\"320\" required></label>\n        <label>Rol <select name=\"role\" id=\"administrationInviteRole\"></select></label>\n        <button type=\"submit\">Crear invitación</button>\n      </form>\n      <section id=\"administrationActivation\" class=\"panel\" hidden aria-label=\"Enlace privado de invitación\"></section>\n      <h3>Invitaciones</h3>\n      <div id=\"administrationInvitations\"></div>\n</section>\n<section id=\"activitySection\" class=\"admin-card activity\" role=\"tabpanel\" aria-labelledby=\"activityTab\" hidden><h3>Actividad reciente</h3><div id=\"administrationAudit\"></div><p class=\"context-note\">Los detalles completos de auditoría están incluidos en la exportación del cliente.</p></section></div>      <section id=\"administrationMemberDetail\" class=\"panel\" hidden aria-labelledby=\"administrationMemberTitle\">\n        <div class=\"section-heading\">\n          <h3 id=\"administrationMemberTitle\">Detalle del integrante</h3>\n          <button id=\"administrationMemberClose\" type=\"button\" class=\"secondary\">Cerrar detalle</button>\n        </div>\n        <div id=\"administrationMemberMessage\" role=\"status\" aria-atomic=\"true\" hidden></div>\n        <div id=\"administrationMemberTabs\" role=\"tablist\" aria-label=\"Información del integrante\">\n          <button id=\"memberAccountTab\" type=\"button\" role=\"tab\" aria-controls=\"memberAccountPanel\" aria-selected=\"true\" data-member-tab=\"memberAccountPanel\">Cuenta y acceso</button>\n          <button id=\"memberProfileTab\" type=\"button\" role=\"tab\" aria-controls=\"memberProfilePanel\" aria-selected=\"false\" tabindex=\"-1\" data-member-tab=\"memberProfilePanel\">Perfil y contacto</button>\n          <button id=\"memberResponsibilitiesTab\" type=\"button\" role=\"tab\" aria-controls=\"memberResponsibilitiesPanel\" aria-selected=\"false\" tabindex=\"-1\" data-member-tab=\"memberResponsibilitiesPanel\">Responsabilidades</button>\n          <button id=\"memberHistoryTab\" type=\"button\" role=\"tab\" aria-controls=\"memberHistoryPanel\" aria-selected=\"false\" tabindex=\"-1\" data-member-tab=\"memberHistoryPanel\">Historial</button>\n        </div>\n        <section id=\"memberAccountPanel\" role=\"tabpanel\" aria-labelledby=\"memberAccountTab\">\n          <div id=\"memberAccountInfo\"></div>\n          <div id=\"memberAccountActions\" class=\"item-actions\"></div>\n          <p>El nombre y correo de acceso pertenecen a la cuenta compartida entre clientes. La recuperación se envía al correo de acceso; cambiar la contraseña afecta todos los accesos de esa cuenta.</p>\n        </section>\n        <section id=\"memberProfilePanel\" role=\"tabpanel\" aria-labelledby=\"memberProfileTab\" hidden>\n          <p>Estos datos se usan como referencia de contacto en este cliente. No cambian el correo de acceso, el destinatario de recuperación ni configuran envíos automáticos.</p>\n          <form id=\"memberProfileForm\" class=\"form-grid\">\n            <label>Nombre de contacto en este cliente<input name=\"contact_name\" maxlength=\"200\"></label>\n            <label>Teléfono<input name=\"phone\" type=\"tel\" maxlength=\"40\"></label>\n            <label>Correo de correspondencia<input name=\"correspondence_email\" type=\"email\" maxlength=\"320\"></label>\n            <label>Contacto preferido<select name=\"preferred_contact\"><option value=\"email\">Correo electrónico</option><option value=\"phone\">Teléfono</option><option value=\"whatsapp\">WhatsApp</option></select></label>\n            <label>Notas internas<textarea name=\"notes\" maxlength=\"2000\" rows=\"3\"></textarea></label>\n            <button type=\"submit\">Guardar perfil de este cliente</button>\n          </form>\n          <p id=\"memberProfileRestriction\" hidden>Solo el propietario puede modificar el perfil de propietarios y administradores.</p>\n        </section>\n        <section id=\"memberResponsibilitiesPanel\" role=\"tabpanel\" aria-labelledby=\"memberResponsibilitiesTab\" hidden>\n          <h4>Permisos por rol</h4><div id=\"memberPermissions\"></div>\n          <h4>Préstamos asignados</h4><div id=\"memberAssignments\"></div>\n          <p>Las asignaciones determinan la cartera del cobrador. El supervisor supervisa la cartera completa por su rol; no se asigna aquí un supervisor individual.</p>\n          <a href=\"/prestamodesk/cobros\">Administrar asignaciones</a> · <a href=\"/prestamodesk/cobros/supervision\">Supervisión</a>\n        </section>\n        <section id=\"memberHistoryPanel\" role=\"tabpanel\" aria-labelledby=\"memberHistoryTab\" hidden>\n          <p>Últimos 50 cambios de acceso, perfil, recuperación y asignaciones relacionados con este integrante en este cliente.</p>\n          <div id=\"memberHistory\"></div>\n        </section>\n      </section>\n</div></section></main><footer>PréstamoDesk · FieldLookers</footer>", start: function(document, window, fetch, localStorage, location, setTimeout, clearTimeout) {
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

return {canLeave: () => !(typeof collectionWritePending !== "undefined" && collectionWritePending) && !(typeof cashClosingSubmitting !== "undefined" && cashClosingSubmitting) && !(typeof paymentSubmitting !== "undefined" && paymentSubmitting) && !(typeof paymentNeedsReview !== "undefined" && paymentNeedsReview) && (!window.prestamodeskInvitationSharing || window.prestamodeskInvitationSharing.canLeave()) && (!window.prestamodeskLoanCreation || window.prestamodeskLoanCreation.canLeave()) && (!window.prestamodeskBorrowerContact || window.prestamodeskBorrowerContact.canLeave()), confirmLeave: () => typeof collectionWritePending !== "undefined" && collectionWritePending ? false : typeof cashClosingSubmitting !== "undefined" && cashClosingSubmitting ? false : window.prestamodeskLoanCreation && !window.prestamodeskLoanCreation.canLeave() ? false : (typeof paymentSubmitting !== "undefined" && paymentSubmitting) || (typeof paymentNeedsReview !== "undefined" && paymentNeedsReview) ? false : window.prestamodeskBorrowerContact && !window.prestamodeskBorrowerContact.canLeave() ? window.prestamodeskBorrowerContact.confirmLeave() : window.prestamodeskInvitationSharing ? window.prestamodeskInvitationSharing.confirmLeave() : false, leaveMessage: () => typeof collectionWritePending !== "undefined" && collectionWritePending ? "Espere la confirmación de la gestión antes de cambiar de sección." : typeof cashClosingSubmitting !== "undefined" && cashClosingSubmitting ? "Espere la confirmación del cierre de caja antes de cambiar de sección." : window.prestamodeskLoanCreation && !window.prestamodeskLoanCreation.canLeave() ? window.prestamodeskLoanCreation.leaveMessage : window.prestamodeskBorrowerContact && !window.prestamodeskBorrowerContact.canLeave() ? window.prestamodeskBorrowerContact.leaveMessage : window.prestamodeskInvitationSharing ? window.prestamodeskInvitationSharing.leaveMessage : "Revise el resultado del pago en Caja antes de cambiar de sección."};
}},
};
