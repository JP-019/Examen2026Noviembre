# 🔔 notification-service

**Propósito:** centralizar el envío de avisos al administrador y al cliente.

## Responsabilidad
- Avisar al admin cuando entra un pedido o una reserva.
- Avisar al cliente cuando su pedido cambia de estado.
- Reintentar envíos fallidos (futuro).
- Registrar qué se envió y a quién (futuro).

## Entradas / Salidas
- **Entrada:** `POST /notify` o eventos (`order.created`, `order.status_changed`,
  `reservation.created`).
- **Salida:** mensajes de Telegram.

## Código actual
`bot.js`: `notifyAdmins`, `notifyCustomerStatus`, y el armado del texto de pedido
(`orderDetailText`).

## Por qué separarlo
El envío de mensajes es una preocupación transversal. Separarlo permite cambiar de
canal (Telegram, WhatsApp, email) sin tocar pedidos ni reservas.

## Futuro
- Cola de mensajes con reintentos.
- Soporte de varios canales.
- Plantillas de mensajes versionadas.
