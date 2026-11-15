# 🧭 routes/ — Índice de puntos de entrada

Aquí se documenta **cada "ruta" o punto de entrada** del bot: comandos, botones
(callbacks) y mensajes de texto. Por cada uno se indica **quién lo maneja hoy** y
**a qué servicio debería ir** cuando se migre a microservicios, y **por qué**.

> En un bot de Telegram no hay rutas HTTP, pero los comandos y callbacks funcionan
> como rutas: son los puntos por donde entra una acción del usuario. Cuando existan
> APIs REST entre microservicios, sus endpoints también se indexarán aquí.

## Comandos

| Ruta | Handler actual | Servicio futuro | Por qué |
|------|----------------|-----------------|---------|
| `/start` | `bot.js` | `telegram-gateway` | Solo presenta la bienvenida y el menú. |
| `/menu` | `bot.js` → `menu.js` | `menu-service` | Devuelve el catálogo. |
| `/carrito` | `bot.js` | `order-service` | El carrito es parte del pedido. |
| `/cancelar` | `bot.js` | `telegram-gateway` | Cancela la sesión conversacional. |
| `/compartir` | `bot.js` | `telegram-gateway` | Genera el enlace para reenviar el bot. |
| `/miid` | `bot.js` | `telegram-gateway` | Utilidad de Telegram, sin negocio. |
| `/pedidos` | `bot.js` → `store.js` | `order-service` | Consulta y gestiona pedidos. |
| `/pendientes` | `bot.js` → `store.js` | `order-service` | Filtro de pedidos por estado. |

## Callbacks (botones)

| Ruta (`callback_data`) | Handler actual | Servicio futuro | Por qué |
|------------------------|----------------|-----------------|---------|
| `menu` | `bot.js` | `menu-service` | Muestra categorías. |
| `cat:<id>` | `bot.js` | `menu-service` | Muestra platos de una categoría. |
| `add:<itemId>` | `bot.js` | `order-service` | Agrega al carrito. |
| `cart` | `bot.js` | `order-service` | Ver carrito. |
| `cart:inc:<id>` / `cart:dec:<id>` / `cart:del:<id>` / `cart:clear` | `bot.js` | `order-service` | Mutaciones del carrito. |
| `checkout` | `bot.js` | `order-service` | Inicia el flujo de pedido. |
| `order:type:delivery\|pickup` | `bot.js` | `order-service` | Define modalidad de entrega. |
| `order:confirm` | `bot.js` | `order-service` + `notification-service` | Crea el pedido y notifica. |
| `order:cancel` | `bot.js` | `order-service` | Cancela el flujo. |
| `reserve` | `bot.js` | `reservation-service` | Inicia reserva. |
| `res:confirm` / `res:cancel` | `bot.js` | `reservation-service` + `notification-service` | Confirma/cancela y notifica. |
| `admin:list` / `admin:filter:<estado>` | `bot.js` → `store.js` | `order-service` | Panel del administrador. |
| `admin:view:<num>` | `bot.js` → `store.js` | `order-service` | Ver detalle de un pedido. |
| `admin:status:<num>:<estado>` | `bot.js` → `store.js` | `order-service` + `notification-service` | Cambia estado y avisa al cliente. |
| `info` / `contact` | `bot.js` | `menu-service` (config) | Datos del restaurante; `contact` incluye botón para compartir el bot. |
| `back:main` | `bot.js` | `telegram-gateway` | Navegación. |
| `noop` | `bot.js` | `telegram-gateway` | Botón sin acción. |

## Mensajes de texto (sesiones)

| Contexto | Handler actual | Servicio futuro | Por qué |
|----------|----------------|-----------------|---------|
| Checkout (nombre, tipo, ubicación GPS, teléfono) | `bot.js` | `order-service` | Datos del pedido. |
| Reserva (fecha, hora, personas, nombre) | `bot.js` | `reservation-service` | Datos de la reserva. |

## Panel web (dashboard) — endpoints actuales

Implementados en `web/dashboard.js`. Requieren token (`?token=` o header
`x-dashboard-token`), salvo `health`.

| Método | Endpoint | Servicio/módulo | Por qué |
|--------|----------|-----------------|---------|
| GET | `/api/health` | `web/dashboard` | Verificar que el panel está arriba. |
| GET | `/api/config` | `web/dashboard` → `menu.js` | Nombre del restaurante y moneda. |
| GET | `/api/orders?status=` | `web/dashboard` → `store.js` | Listar/filtrar pedidos. |
| GET | `/api/stats` | `web/dashboard` → `store.js` | Totales por estado y ventas. |
| GET | `/api/export/xlsx?date=&status=` | `web/dashboard` → `store.js` | Exportar el día a Excel. |
| GET | `/api/export/csv?date=&status=` | `web/dashboard` → `store.js` | Exportar el día a CSV. |
| PATCH | `/api/orders/:number/status` | `web/dashboard` → `store.js` + notificación | Cambiar estado y avisar al cliente. |
| DELETE | `/api/orders/:number` | `web/dashboard` → `store.js` | Eliminar un pedido del panel. |

## Endpoints REST previstos (futuro)

| Método | Endpoint | Servicio | Por qué |
|--------|----------|----------|---------|
| GET | `/menu` | `menu-service` | Catálogo completo. |
| GET | `/menu/:categoryId` | `menu-service` | Platos por categoría. |
| POST | `/orders` | `order-service` | Crear pedido. |
| GET | `/orders` | `order-service` | Listar/filtrar pedidos. |
| PATCH | `/orders/:id/status` | `order-service` | Cambiar estado. |
| POST | `/reservations` | `reservation-service` | Crear reserva. |
| POST | `/notify` | `notification-service` | Enviar aviso. |

> Al agregar una ruta nueva, **añádela a esta tabla** con su servicio y el motivo.
