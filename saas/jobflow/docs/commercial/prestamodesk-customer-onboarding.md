# PréstamoDesk — Incorporación de clientes comerciales

Estado: Borrador interno
Fecha: 2026-10-24

## Antes de aceptar el cliente

- Confirmar negocio, responsable autorizado y correo del propietario.
- Confirmar tamaño de cartera, usuarios y funciones necesarias.
- Verificar que el alcance cabe en la capacidad validada del servicio.
- Entregar precio final, alcance, condiciones y aviso de privacidad.
- Acordar soporte, cancelación y devolución de datos.
- Registrar aceptación y decisión de facturación de forma privada.
- No solicitar contraseñas, tarjetas ni credenciales bancarias.

No iniciar cobros mientras existan condiciones comerciales sin resolver.

## Configuración

- Usar el procedimiento existente de invitación y aprovisionamiento.
- Confirmar producto PréstamoDesk y negocio correcto.
- Verificar la identidad del propietario antes de conceder acceso.
- Confirmar moneda DOP y zona horaria del negocio.
- Crear usuarios individuales con los permisos mínimos necesarios.
- No compartir cuentas entre propietario, cajero y cobrador.
- Verificar recuperación de contraseña sin compartir enlaces de recuperación.
- Mantener los datos de cada cliente fuera del repositorio público.

## Cartera inicial

- Acordar si el negocio comienza vacío o necesita migración.
- Cotizar y validar cualquier migración por separado.
- Usar un canal privado aprobado para recibir datos.
- Revisar importes, fechas, cuotas, pagos y mora con el propietario.
- Obtener aceptación de los saldos antes de operar con la cartera.
- No crear pagos ficticios en producción para demostrar el sistema.

## Capacitación

Realizar la demostración con datos sintéticos en un entorno separado:

- Crear prestatario y préstamo.
- Consultar cuotas y saldo.
- Registrar un abono y consultar el recibo.
- Revisar correcciones y trazabilidad.
- Completar cierre de caja con el rol autorizado.
- Consultar cartera y seguimiento de cobros.
- Mostrar gestión de usuarios y permisos.
- Explicar qué hacer ante un envío de pago con resultado incierto:
  consultar historial antes de intentar un nuevo registro.

## Inicio del servicio

- Confirmar acceso del propietario y de los usuarios autorizados.
- Confirmar estado de facturación según el acuerdo.
- Entregar enlace del espacio de trabajo e instrucciones de soporte.
- Registrar fecha de inicio y próxima revisión.
- Confirmar monitoreo y respaldo operativo.
- Aplicar los límites comerciales mediante el procedimiento verificado.
- No prometer funciones, capacidad ni disponibilidad no demostradas.

## Seguimiento inicial

- Revisar incidencias, recibos y conciliación con el cliente.
- Registrar tiempo de soporte y trabajo de configuración.
- Confirmar que el precio cubre el servicio prestado.
- Separar errores de producto de nuevas solicitudes de funciones.
- Registrar la decisión de renovación o cancelación.

## Cancelación

- Verificar autoridad de quien solicita la cancelación.
- Confirmar fecha de fin y condiciones aplicables.
- Ofrecer devolución de datos por el procedimiento validado.
- Suspender acceso mediante el flujo administrativo existente.
- Aplicar la política aprobada de retención y eliminación.
- No borrar datos o respaldos de forma improvisada.

## Evidencia

Guardar acuerdos, facturas, aceptación de saldos y comunicaciones
en registros privados. Este documento no prueba que un cliente
haya completado los pasos.
