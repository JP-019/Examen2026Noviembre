# Examen 2026 - Noviembre

Entrega de la **Plataforma Integral de Ingenieria de Datos y Analitica
Inteligente**, proyecto del curso desarrollado con SCRUM adaptado a 3 dias.

| Campo | Valor |
|---|---|
| Proceso de negocio | VENTAS |
| Periodo | 11 al 14 de noviembre de 2026 |
| Metodologia | SCRUM (S0 Fundaciones, S1 Datos, S2 Analitica, S3 Cierre) |
| Tareas | 15 (T01 a T15), 76 story points |
| Estado | 13 tareas cerradas, T01 y T15 parciales |

## Estructura del repositorio

```
Examen2026Noviembre/
  data-platform/     Plataforma de datos: ETL, DW, API, dashboard, ML, GenAI y alertas
  Tareas_SCRUM/      Backlog, plan de sprints, tarjetas T01-T15 y guia del proyecto
  bot-telegram/      Proyecto de ejemplo: bot de Telegram con panel web (Node.js)
  README.md          Este archivo
```

### `data-platform/`

Contiene el codigo y la documentacion de la plataforma, con un commit por tarea
SCRUM. Documentos de entrada:

- `documentation/informe_final.md`: informe de cierre, estado por tarea y
  trazabilidad con la rubrica.
- `README.md`: puesta en marcha y estructura interna.
- `INDEX.md`: indice generado de servicios y documentos.

### `Tareas_SCRUM/`

Artefactos de gestion: `Product_Backlog.txt`, `Sprint_Plan.txt`, la guia del
proyecto en PDF y las tarjetas `Tarea01.txt` a `Tarea15.txt`.

### `bot-telegram/`

Proyecto independiente en Node.js: bot de Telegram para un restaurante con
carrito, pedidos, reservas y panel web de administracion. No consume el Data
Warehouse ni `core-api`.

```powershell
cd bot-telegram
npm install
Copy-Item .env.example .env   # completar BOT_TOKEN, ADMIN_CHAT_ID, DASHBOARD_PORT, DASHBOARD_TOKEN y BOT_USERNAME
npm start
```

## Puesta en marcha de la plataforma

```powershell
cd data-platform
Copy-Item .env.example .env
sqlcmd -S localhost -E -C -f 65001 -i database/00_schemas.sql
cd services/etl ; py -m app full
cd ../../services/core-api ; py -m uvicorn app.main:app --port 8000
```

El detalle completo, los comandos por servicio y las credenciales de entorno
estan en `data-platform/README.md` y `data-platform/documentation/manual.md`.

## Estado de las tareas

| Tarea | Entregable | Estado |
|---|---|---|
| T01 | Entorno y fuente reproducible | Parcial (Docker no ejecutado) |
| T02 | Inventario, ERD y diccionario | Cerrada |
| T03 | Arquitectura y decisiones | Cerrada |
| T04 | Staging en tres zonas | Cerrada |
| T05 | Extraccion incremental idempotente | Cerrada |
| T06 | Reglas de calidad | Cerrada |
| T07 | Modelo dimensional | Cerrada |
| T08 | Carga al DW y reconciliacion | Cerrada |
| T09 | API de KPIs | Cerrada |
| T10 | Dashboard web | Cerrada |
| T11 | Modelo ML con baseline | Cerrada |
| T12 | Asistente GenAI | Cerrada |
| T13 | Alertas y monitoreo | Cerrada |
| T14 | Documentacion y pruebas | Cerrada |
| T15 | Video y ensayo de demo | Parcial (video pendiente) |

## Seguridad

- No se versionan `.env`, `orders.json`, `node_modules/` ni archivos con tokens.
- Los valores de ejemplo viven en los archivos `.env.example`.
- Si un token estuvo expuesto alguna vez, debe revocarse en el proveedor antes
  de publicar el repositorio.
