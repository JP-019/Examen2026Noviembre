# APIs y contratos de datos

- **Tarea:** T14
- **Estilo:** REST + JSON sobre FastAPI
- **Regla de oro:** solo `core-api` (y el ETL) hablan con SQL Server. Dashboard,
  GenAI y alertas consumen HTTP.

---

## 1. Mapa de servicios

| Servicio | Puerto | Rol | Consume | Expone |
|---|---|---|---|---|
| `core-api` | 8000 | Unica puerta de lectura del DW | `dw.vw_Ventas`, `dw.FactVentas` | KPIs, tendencias, detalle, filtros, agrupado, monitor |
| `catalog` | 8001 | Indice vivo de la plataforma | `catalog/platform.json` | indice JSON/Markdown, mapa, rutas |
| `ml` | 8002 | Prediccion mensual | DW (solo lectura) | modelo, metricas, serie, prediccion, entrenamiento |
| `genai` | 8003 | Preguntas en lenguaje natural | `core-api` | respuesta con fuentes y `grounded` |
| `alerting` | 8004 | Reglas y monitoreo | `core-api`, `ml` | alertas, entregas, monitor |
| `dashboard` | 8501 | UI Streamlit | `core-api` | pantalla web |

Convenciones:

- Fechas `YYYY-MM-DD`; timestamps ISO 8601 UTC.
- Importes en soles (S/) con 2 decimales.
- Listas paginadas incluyen `page`, `page_size`, `total`.
- Solicitud remota a servicios sensibles: **403**.
- Errores de validacion: **422** con `detail` de FastAPI.
- Base caida o dependencia no disponible: **503** con mensaje legible.
- Recurso inexistente: **404**.

Los servicios `core-api`, `ml`, `genai` y `alerting` aceptan solo clientes de
loopback; las solicitudes remotas reciben **403**. Es una proteccion para uso
local, no autenticacion para produccion. Un proxy local debe autenticar y
autorizar a sus clientes; el despliegue remoto requiere tambien TLS y limites de
solicitudes.

---

## 2. `core-api` (8000)

Base: `/api/v1`. Swagger: <http://localhost:8000/docs>.

| Metodo | Ruta | Parametros | Respuesta |
|---|---|---|---|
| GET | `/health` | - | `status`, `database`, `data_updated_at`, `last_etl_status`, `fact_rows` |
| GET | `/kpis` | `desde`, `hasta`, `local`, `seccion`, `producto` | 6 KPIs |
| GET | `/tendencias` | filtros + `granularidad=dia\|mes` | `serie`, `comparacion` |
| GET | `/detalle` | filtros + `page`, `page_size` | filas + total |
| GET | `/filtros` | - | rango, locales, secciones, productos |
| GET | `/agrupado` | filtros + `dimension=local\|seccion\|producto`, `limit` 1-50 | grupos |
| GET | `/monitor` | - | ultima carga, fallas, rechazos, hecho |

### Contrato `KpisResponse`

```json
{
  "periodo": {"desde": "2008-08-03", "hasta": "2008-08-15", "etiqueta": "..."},
  "filtros": {"local": null, "seccion": null, "producto": null},
  "data_updated_at": "2026-11-14T02:47:00.789000",
  "kpis": [
    {"code": "ventas", "label": "Ventas", "value": 696.4, "unit": "S/"},
    {"code": "ticket_promedio", "label": "Ticket promedio", "value": 174.1, "unit": "S/"}
  ]
}
```

Los 6 codigos son `ventas`, `lineas`, `facturas`, `ticket_promedio`, `unidades`,
`productos`. Los calculos salen de `dw.vw_Ventas`; el dashboard no recalcula.

### Contrato `AgrupadoResponse`

```json
{
  "dimension": "producto",
  "total_grupos": 4,
  "grupos": [
    {"valor": "Mini Lorito", "ventas": 339.0, "lineas": 1, "facturas": 1, "unidades": 30}
  ]
}
```

`dimension` es un `Literal` y `limit` esta acotado: cualquier otro valor devuelve
422 y nunca llega al SQL.

### Contrato `MonitorResponse`

```json
{
  "data_updated_at": "2026-11-14T02:47:00.789000",
  "fact_rows": 5,
  "last_etl": {"execution_id": 150, "pipeline_name": "sales_dw_fact", "status": "SUCCESS"},
  "etl_runs_24h": 150,
  "etl_failures_24h": 0,
  "rejected_total": 0,
  "rejected_open": 0,
  "rejected_by_rule": [],
  "recent_failures": []
}
```

---

## 3. `catalog` (8001)

| Metodo | Ruta | Respuesta |
|---|---|---|
| GET | `/` | resumen (servicios, implementados, tareas) |
| GET | `/index` | indice completo JSON |
| GET | `/index.md` | indice Markdown |
| GET | `/map` | carpetas y proposito |
| GET | `/services` | lista de servicios |
| GET | `/services/{id}` | detalle con funciones y endpoints |
| GET | `/routes` | todas las rutas HTTP de la plataforma |
| GET | `/health` | estado del catalogo |

El contrato del indice es `catalog/platform.json`; `scripts/build_index.py`
genera `INDEX.md` desde ese archivo. Si un servicio cambia, se actualiza el
manifiesto, no el indice a mano.

---

## 4. `ml` (8002)

| Metodo | Ruta | Respuesta |
|---|---|---|
| GET | `/model` | estado, version, parametros, `train_periods`, `test_periods` |
| GET | `/metrics` | metricas de prueba + baseline + detalle |
| GET | `/series` | serie mensual observada |
| POST | `/predict` | prediccion de N meses (solo si `trained`) |
| POST | `/train` | entrena, evalua y versiona |
| GET | `/health` | estado + filas |

Estados posibles: `trained` y `insufficient_data`. Con la fuente actual siempre
responde `insufficient_data` y **no** publica metricas; es el contrato de
honestidad, no una falla.

---

## 5. `genai` (8003)

| Metodo | Ruta | Respuesta |
|---|---|---|
| POST | `/ask` | `pregunta`, `intent`, `respuesta`, `datos`, `fuentes`, `grounded` |
| GET | `/queries` | catalogo de consultas aprobadas |
| GET | `/tests` | las 10 pruebas documentadas |
| POST | `/tests/run` | ejecuta y resume |
| GET | `/health` | estado + core-api |

Contrato de respuesta:

```json
{
  "pregunta": "ventas por local",
  "intent": "ventas_por_local",
  "respuesta": "Ventas por local del periodo completo: ...",
  "datos": {"grupos": []},
  "fuentes": [{"servicio": "core-api", "endpoint": "/api/v1/agrupado?dimension=local", "data_updated_at": "..."}],
  "grounded": true,
  "interpretacion": ""
}
```

Si la pregunta esta fuera de alcance: `grounded=false`, `datos={}`, `fuentes=[]`.
No existe endpoint que reciba SQL.

---

## 6. `alerting` (8004)

| Metodo | Ruta | Respuesta |
|---|---|---|
| GET | `/health` | estado propio + core-api + ML + alertas |
| GET | `/rules` | 6 reglas y umbrales |
| POST | `/alerts/evaluate` | `reglas_evaluadas`, `disparadas`, `nuevas`, `duplicadas`, `detalle` |
| GET | `/alerts` | alertas (`status`, `severity`, `limit`, `incluir_simuladas`) |
| GET | `/alerts/{id}` | alerta + entregas |
| POST | `/alerts/{id}/ack` | estado `acknowledged` |
| POST | `/alerts/simulate` | alerta de prueba (`simulated=1`) |
| GET | `/monitor` | HTML de monitoreo |
| GET | `/monitor.json` | snapshot JSON |

Contrato de alerta:

```json
{
  "alert_id": 1,
  "event_key": "VENTAS_BAJAS|ventas|2008-08-03..2008-08-15|2026-11-14T02:47:00.789000",
  "rule_code": "VENTAS_BAJAS",
  "alert_type": "regla_negocio",
  "severity": "warning",
  "entity": "ventas",
  "indicator": "ventas_totales",
  "observed_value": 696.4,
  "threshold": 1000.0,
  "period": "2008-08-03..2008-08-15",
  "source": "core-api /api/v1/kpis",
  "status": "open",
  "simulated": 0,
  "deliveries": [{"channel": "dashboard", "status": "delivered"}]
}
```

---

## 7. Contratos de error

| Situacion | Codigo | Cuerpo |
|---|---|---|
| Query invalida | 422 | `{"detail": [{"loc": [...], "msg": "..."}]}` |
| Recurso inexistente | 404 | `{"detail": "Alerta 99 no encontrada"}` |
| Dependencia caida | 503 | `{"detail": "No se pudo conectar con ..."}` |
| Base caida | 503 | `{"detail": "No se pudo leer el Data Warehouse."}` |

El dashboard y el GenAI tratan 503 como estado visible, no como exito vacio.
