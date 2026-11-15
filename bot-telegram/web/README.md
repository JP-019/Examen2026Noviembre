# 🌐 web/ — Panel web de pedidos (dashboard)

**Propósito:** ver y gestionar todos los pedidos desde el navegador, en tiempo real.

## Cómo funciona
- Se monta **dentro del mismo proceso** del bot (`bot.js` llama a `startDashboard`).
- Comparte el `store` (memoria + `orders.json`), así que el panel y el bot ven lo mismo.
- La interfaz consulta la API cada **5 segundos** (auto-refresco).
- Al cambiar el estado desde la web, se avisa al cliente por Telegram.

## Archivos
| Archivo | Qué hace |
|---------|----------|
| `dashboard.js` | Servidor Express: API REST + autenticación por token + archivos estáticos. |
| `public/index.html` | Interfaz (HTML + CSS + JS) del panel. |

## Configuración (`.env`)
| Variable | Descripción |
|----------|-------------|
| `DASHBOARD_PORT` | Puerto del panel (por defecto `3000`). |
| `DASHBOARD_TOKEN` | Token de acceso. Se pasa en la URL: `?token=...` |

## Endpoints
| Método | Endpoint | Qué hace |
|--------|----------|----------|
| GET | `/api/health` | Estado del servidor. |
| GET | `/api/config` | Nombre del restaurante y moneda. |
| GET | `/api/orders?status=` | Lista pedidos (filtro opcional). |
| GET | `/api/stats` | Totales por estado y ventas. |
| GET | `/api/export/xlsx?date=&status=` | Descarga un **Excel (.xlsx)** con formato y total. |
| GET | `/api/export/csv?date=&status=` | Descarga un **CSV** (compatible con Excel). |
| PATCH | `/api/orders/:number/status` | Cambia el estado y avisa al cliente. |

> Todas las rutas `/api/*` (salvo `health`) requieren el token.
> `date` usa formato `YYYY-MM-DD` para exportar el cierre de un día.

## Acceso
```
http://localhost:3000/?token=TU_TOKEN
```
Desde el móvil en la misma red: `http://IP_DE_TU_PC:3000/?token=TU_TOKEN`.

## Seguridad
- Sin `DASHBOARD_TOKEN`, el panel queda **abierto**: úsalo solo en local.
- No expongas el puerto a Internet sin HTTPS y token.
- En el futuro: login con usuario/contraseña y roles.

## Por qué está dentro del bot (y no como microservicio aún)
Compartir el `store` en el mismo proceso evita inconsistencias entre el bot y la
web. En la arquitectura objetivo será un servicio aparte que consulte a
`order-service` por API (ver [`../docs/arquitectura.md`](../docs/arquitectura.md)).
