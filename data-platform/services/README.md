# Servicios (microservicios)

Cada carpeta es un servicio desplegable por separado. Todos se comunican por HTTP
o por la base, nunca por importacion directa de codigo de otro servicio.

| Servicio | Carpeta | Tipo | Puerto | Estado | Tarea |
|---|---|---|---|---|---|
| ETL de ventas | `etl/` | batch | - | implementado | T05, T06 |
| Catalogo | `catalog/` | HTTP | 8001 | implementado | T03 |
| API de KPIs | `core-api/` | HTTP | 8000 | implementado | T09 |
| Dashboard | `dashboard/` | frontend | 8501 | implementado | T10 |
| Machine Learning | `ml/` | HTTP | 8002 | implementado | T11 |
| Asistente GenAI | `genai/` | HTTP | 8003 | implementado | T12 |
| Alertas | `alerting/` | HTTP | 8004 | implementado | T13 |

## Contratos

- `core-api` es la **unica** puerta al Data Warehouse para el resto de los servicios.
- `dashboard`, `genai` y `alerting` consumen `core-api`; nunca SQL Server.
- `etl` es el unico servicio que escribe en `raw`, `clean`, `ready` y `dw`.

## Indice vivo

El servicio `catalog` publica el estado real de todos los servicios y sus rutas:
`http://localhost:8001/index.md`.

## Convencion de carpetas

```
services/<id>/
  app/               codigo del servicio
  README.md          indice: responsabilidad, funciones, endpoints, variables
  requirements.txt   dependencias fijadas
```

El manifiesto `catalog/platform.json` es la fuente de verdad de esta tabla.
