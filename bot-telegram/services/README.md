# 🧩 services/ — Microservicios

Cada carpeta es un **microservicio** con un único dominio (bounded context). La
idea es que cada uno sea independiente: su propio código, sus datos y su forma de
exponerse (HTTP o eventos).

| Servicio | Responsabilidad | Datos que posee | Código actual relacionado |
|----------|-----------------|-----------------|---------------------------|
| [`telegram-gateway/`](telegram-gateway/README.md) | Recibe updates de Telegram y responde al usuario. | Sesiones de conversación. | `bot.js` (handlers de entrada) |
| [`menu-service/`](menu-service/README.md) | Catálogo de platos, precios y datos del local. | Menú. | `menu.js` |
| [`order-service/`](order-service/README.md) | Carrito, pedidos y estados. | Pedidos. | `bot.js` (carrito/checkout) + `store.js` |
| [`reservation-service/`](reservation-service/README.md) | Reservas de mesa. | Reservas. | `bot.js` (flujo reserva) |
| [`notification-service/`](notification-service/README.md) | Enviar avisos a admin y cliente. | Historial de envíos. | `notifyAdmins`, `notifyCustomerStatus` |

## Reglas entre servicios
- Un servicio **no** lee la base de datos de otro: pide por API o escucha eventos.
- El `telegram-gateway` **no** tiene reglas de negocio; solo orquesta llamadas.
- Los contratos compartidos viven en [`packages/common/`](../packages/common/README.md).
- Cada servicio nuevo debe incluir su `README.md` con: propósito, entradas/salidas,
  datos y plan de migración.

## Orden sugerido de extracción
1. `menu-service` (es el más simple y sin estado).
2. `order-service` (el más crítico; primero separar lógica de `bot.js`).
3. `notification-service` (desacopla los avisos).
4. `reservation-service`.
5. `telegram-gateway` al final, cuando los demás ya tengan API.
