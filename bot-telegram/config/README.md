# ⚙️ config/ — Configuración

**Propósito:** centralizar la configuración y validar las variables de entorno.

## Qué irá aquí
- `env.js` — lee y valida `BOT_TOKEN`, `ADMIN_CHAT_ID`, puertos, URLs de servicios.
- Valores por defecto y mensajes de error claros si falta algo.
- Separación por entorno (dev / prod).

## Código actual relacionado
- `.env` (raíz) con `BOT_TOKEN` y `ADMIN_CHAT_ID`.
- Lectura con `dotenv` al inicio de `bot.js`.

## Por qué
Hoy la configuración se lee dispersa. Centralizarla evita errores como arrancar sin
token o sin admin, y facilita usar distintos valores por entorno.

## Futuro
- Validación con esquema (p. ej. `zod` o `joi`).
- Secretos fuera del repositorio (gestor de secretos en producción).
- Nunca versionar `.env` (ya está en `.gitignore`).
