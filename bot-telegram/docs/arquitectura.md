# 🏗️ Arquitectura

## 1. Estado actual (monolito)

Todo el bot corre en un solo proceso Node.js:

```
Telegram API
    │  polling (getUpdates)
    ▼
┌──────────────────────────────────────────────┐
│ bot.js                                        │
│  ├── comandos (/start, /menu, /pedidos, ...)  │
│  ├── callbacks (botones inline)               │
│  ├── sesiones y carritos (en memoria)         │
│  ├── menú      ──► menu.js                    │
│  └── pedidos   ──► store.js ──► orders.json   │
└──────────────────────────────────────────────┘
    │ sendMessage
    ▼
Admin (ADMIN_CHAT_ID) y cliente
```

**Ventajas:** simple, rápido de arrancar, un solo despliegue.
**Desventajas:** `bot.js` concentra demasiadas responsabilidades; difícil de testear
y de escalar por partes; los datos están acoplados al proceso.

## 2. Estado objetivo (microservicios)

```
                        ┌──────────────────────────┐
   Telegram  ─────────► │  telegram-gateway        │
                        │  (polling / webhook)     │
                        └───────────┬──────────────┘
                                    │ HTTP / eventos
        ┌───────────────┬───────────┼───────────────┬───────────────────┐
        ▼               ▼           ▼               ▼                   ▼
 ┌────────────┐  ┌────────────┐ ┌──────────────┐ ┌──────────────────┐
 │menu-service│  │order-service│ │reservation-  │ │notification-     │
 │            │  │            │ │service       │ │service           │
 └────────────┘  └─────┬──────┘ └──────────────┘ └──────────────────┘
                       │
                       ▼
                 ┌──────────┐
                 │   BD     │
                 └──────────┘
```

### Responsabilidades
- **telegram-gateway:** recibe updates, maneja sesiones, responde. Sin reglas de negocio.
- **menu-service:** catálogo y datos del local. Solo lectura.
- **order-service:** carrito, pedidos, estados. Dueño de la BD de pedidos.
- **reservation-service:** reservas y disponibilidad.
- **notification-service:** envía avisos (Telegram u otros canales).

### Comunicación
- **Síncrona (HTTP/REST)** para consultas: el gateway pide el menú o crea un pedido.
- **Asíncrona (eventos/cola)** para efectos secundarios: `order.created` →
  notification-service envía el aviso.
- **Contratos compartidos** en `packages/common` (modelos y validaciones).

### Reglas
- Cada servicio es dueño de sus datos; nadie lee la BD de otro.
- El gateway no calcula totales ni conoce precios.
- Fallos de notificación no deben romper la creación de un pedido (desacople).

## 3. Estrategia de migración (sin romper el bot)

1. **Refactor interno** del monolito en módulos (`handlers/`, `keyboards/`, `services/`).
2. Extraer **menu-service** (sin estado, bajo riesgo).
3. Extraer **order-service** y mover persistencia a base de datos.
4. Extraer **notification-service** y conectar por eventos.
5. Extraer **reservation-service** (y persistir reservas).
6. Convertir `bot.js` en **telegram-gateway** que consume los servicios.

Cada paso debe mantener el bot funcionando y con tests que lo respalden.

## 4. Decisiones y pendientes
- **Persistencia:** hoy `orders.json`; objetivo PostgreSQL (transacciones) o MongoDB.
- **Sesiones:** en memoria; en producción conviene un store (Redis) para sobrevivir reinicios.
- **Autenticación admin:** hoy por `ADMIN_CHAT_ID`; futuro roles/permisos.
- **Observabilidad:** falta logging estructurado y métricas.
