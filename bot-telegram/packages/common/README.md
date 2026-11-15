# 🧰 packages/common

**Propósito:** utilidades y contratos compartidos por todos los servicios.

## Qué irá aquí
- `money()` — formateo de precios.
- `esc()` — escape de Markdown para Telegram.
- Modelos/contratos: `Order`, `OrderItem`, `Reservation`, `MenuItem`.
- Constantes: `STATUS_LABELS`, estados válidos.
- Validaciones: teléfono, cantidad, estados.
- Configuración validada (ver `config/`).

## Código actual relacionado
Funciones `money` y `esc` en `bot.js`; etiquetas `STATUS_LABELS`.

## Por qué
Evita que cada servicio reimplemente el formateo de precios o el escape de texto,
y mantiene los **contratos** iguales entre servicios.

## Futuro
- Publicarlo como paquete interno (workspace de npm).
- Añadir tipos (JSDoc o TypeScript).
