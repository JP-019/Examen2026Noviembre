# 📅 reservation-service

**Propósito:** gestionar las reservas de mesa.

## Responsabilidad
- Recibir fecha, hora, cantidad de personas y nombre.
- Validar disponibilidad (futuro).
- Confirmar o cancelar la reserva.
- Notificar al restaurante.

## Entradas / Salidas
- **Entrada:** `POST /reservations`, `PATCH /reservations/:id/status`.
- **Salida:** reserva creada/actualizada + evento `reservation.created`.

## Datos que posee
- Reservas (hoy **no** se persisten: solo se notifican al admin).

## Código actual
`bot.js`: callback `reserve`, `res:confirm`, `res:cancel` y el flujo de texto
(fecha → hora → personas → nombre).

## Por qué separarlo
Es un dominio distinto al de pedidos y con reglas propias (capacidad, horarios).

## Futuro
- Persistir reservas (hoy se pierden al no guardarse).
- Calendario y control de capacidad por franja horaria.
- Recordatorio automático al cliente.
