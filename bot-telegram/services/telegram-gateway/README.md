# 🤖 telegram-gateway

**Propósito:** ser la única puerta de entrada de Telegram. Recibe los updates
(mensajes, botones) y responde al usuario.

## Responsabilidad
- Recibir updates por **polling** (hoy) o **webhook** (futuro).
- Traducir Telegram ↔ servicios internos (menú, pedidos, reservas).
- Gestionar **sesiones** de conversación (checkout, reserva).
- Renderizar teclados y mensajes.
- Validar que quien ejecuta acciones de admin realmente lo sea.

## Entradas / Salidas
- **Entrada:** `Update` de Telegram (comando, callback, texto).
- **Salida:** mensajes a Telegram + llamadas HTTP/eventos a otros servicios.

## Qué NO debe hacer
- No calcula totales ni guarda pedidos (eso es `order-service`).
- No conoce el catálogo (eso es `menu-service`).

## Código actual
Todo vive en `bot.js`: `bot.onText`, `bot.on("callback_query")`, `bot.on("message")`,
`mainKeyboard`, `categoriesKeyboard`, etc.

## Estructura futura sugerida
```
telegram-gateway/
├── src/
│   ├── index.js          # arranque del bot
│   ├── handlers/         # comandos, callbacks, mensajes
│   ├── keyboards/        # teclados inline
│   ├── sessions/         # estado conversacional
│   └── clients/          # clientes HTTP de los otros servicios
└── README.md
```

## Migración desde el monolito
1. Extraer teclados a `keyboards/`.
2. Extraer handlers por comando/callback.
3. Reemplazar llamadas directas a `menu.js`/`store.js` por clientes HTTP.
4. Mantener las sesiones aquí (son estado de conversación, no de negocio).
