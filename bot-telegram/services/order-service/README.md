# 🧾 order-service

**Propósito:** gestionar el carrito, la creación de pedidos y sus estados. Es el
servicio más crítico del negocio.

## Responsabilidad
- Mantener el **carrito** por usuario.
- Calcular **subtotal, envío y total**.
- Crear el pedido con un **número único**.
- Cambiar estado: `pendiente` → `en_preparacion` → `entregado` / `cancelado`.
- Listar y filtrar pedidos para el administrador.

## Entradas / Salidas
- **Entrada:** `POST /orders`, `GET /orders?status=`, `PATCH /orders/:id/status`.
- **Salida:** pedido creado/actualizado + evento `order.created` / `order.status_changed`.

## Datos que posee
- Pedidos (hoy en `orders.json`, vía `store.js`).

## Código actual
- `bot.js`: carrito (`carts`), `cartSubtotal`, `buildOrder`, `checkoutSummary`,
  panel admin (`adminList`, `adminOrderKeyboard`).
- `store.js`: `addOrder`, `getAll`, `getByNumber`, `updateStatus`.

## Por qué separarlo
Los pedidos cambian de estado constantemente y necesitan persistencia real. Aislarlo
permite escalarlo y cambiar de `orders.json` a base de datos sin tocar el bot.

## Futuro
- Base de datos con transacciones.
- Estados como máquina de estados validada.
- Evento al crear/cambiar estado para que `notification-service` avise.
- Idempotencia para no duplicar pedidos por doble clic.
