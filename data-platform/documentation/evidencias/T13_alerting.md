# Evidencia T13 - Alertas end-to-end, reglas y monitoreo

- **Servicio:** `services/alerting`
- **Puerto:** 8004
- **Dependencias:** `core-api` (8000) y `ml` (8002); sin conexion a SQL Server
- **Registro de alertas:** SQLite local (`services/alerting/data/alerts.db`)
- **Recolectado:** 2026-11-13
- **Reproducible:** `python tests/test_alerting_rules.py` y `python tests/smoke_alerting.py`

## 1. Arranque

```powershell
# Terminal 1
cd services/core-api
uvicorn app.main:app --port 8000

# Terminal 2
cd services/ml
uvicorn app.main:app --port 8002

# Terminal 3
cd services/alerting
uvicorn app.main:app --port 8004
```

```json
GET /health
{
  "service": "alerting",
  "status": "ok",
  "alert_db": "...\\services\\alerting\\data\\alerts.db",
  "core_api": "ok",
  "ml": "insufficient_data"
}
```

## 2. Reglas y umbrales

`GET /rules` devuelve 6 reglas y sus umbrales vigentes:

| Codigo | Tipo | Severidad | Condicion | Origen |
|---|---|---|---|---|
| `VENTAS_BAJAS` | regla_negocio | warning | Ventas < S/ 1000 | `core-api /api/v1/kpis` |
| `TICKET_BAJO` | regla_negocio | warning | Ticket promedio < S/ 200 | `core-api /api/v1/kpis` |
| `CAIDA_VENTAS` | regla_negocio | critical | Caida > 15% vs periodo anterior | `core-api /api/v1/tendencias` |
| `MODELO_SIN_ENTRENAR` | umbral_ml | info | Menos de 8 periodos o estado distinto de `trained` | `ml /model` |
| `MAE_ALTO` | umbral_ml | warning | MAE > 500 | `ml /model` |
| `RECHAZOS_ALTOS` | calidad_datos | critical | Rechazos abiertos > 10 | `core-api /api/v1/monitor` |

```json
{
  "ventas_min": 1000.0, "ticket_min": 200.0, "caida_pct": 15.0,
  "mae_max": 500.0, "rechazos_max": 10, "ml_periodos_min": 8
}
```

## 3. Primera evaluacion (genera alertas)

```json
POST /alerts/evaluate
{
  "periodo": "2008-08-03..2008-08-15",
  "reglas_evaluadas": 6,
  "disparadas": 3,
  "nuevas": 3,
  "duplicadas": 0,
  "detalle": [
    {"alert_id": 1, "rule_code": "VENTAS_BAJAS", "severity": "warning", "observed_value": 696.4, "threshold": 1000.0},
    {"alert_id": 2, "rule_code": "TICKET_BAJO", "severity": "warning", "observed_value": 174.1, "threshold": 200.0},
    {"alert_id": 3, "rule_code": "MODELO_SIN_ENTRENAR", "severity": "info", "observed_value": 1.0, "threshold": 8.0}
  ]
}
```

Con los datos reales se disparan exactamente las tres condiciones esperadas:

- Ventas del periodo **S/ 696.40** por debajo de S/ 1000.
- Ticket promedio **S/ 174.10** (696.40 / 4 facturas) por debajo de S/ 200.
- Modelo en `insufficient_data` con **1** periodo y **8** requeridos.

No se disparan `CAIDA_VENTAS` (no hay periodo anterior comparable),
`MAE_ALTO` (no hay modelo entrenado) ni `RECHAZOS_ALTOS` (0 rechazos).

## 4. Segunda evaluacion (anti-duplicado)

```json
POST /alerts/evaluate
{
  "reglas_evaluadas": 6,
  "disparadas": 3,
  "nuevas": 0,
  "duplicadas": 3
}
```

La clave unica es:

```
event_key = regla | entidad | periodo | data_updated_at
```

Ejemplo real:

```
VENTAS_BAJAS|ventas|2008-08-03..2008-08-15|2026-11-14T02:47:00.789000
```

Al reevaluar sobre los mismos datos, `INSERT OR IGNORE` no inserta y tampoco se
registra una segunda entrega (`UNIQUE (alert_id, channel)`).

## 5. Contenido de una alerta

```json
GET /alerts/3
{
  "alert_id": 3,
  "event_key": "MODELO_SIN_ENTRENAR|modelo_ml|2008-08-03..2008-08-15|2026-11-14T02:47:00.789000",
  "rule_code": "MODELO_SIN_ENTRENAR",
  "alert_type": "umbral_ml",
  "severity": "info",
  "entity": "modelo_ml",
  "indicator": "periodos_disponibles",
  "observed_value": 1.0,
  "threshold": 8.0,
  "period": "2008-08-03..2008-08-15",
  "source": "ml /model",
  "explanation": "El modelo no esta entrenado (insufficient_data): hay 1 periodos y se requieren 8. ...",
  "action": "Acumular mas meses de ventas y ejecutar POST /train; no usar predicciones mientras tanto.",
  "status": "open",
  "simulated": 0,
  "created_at": "2026-11-14T03:28:39+00:00",
  "acknowledged_at": null,
  "deliveries": [
    {"channel": "dashboard", "status": "delivered", "detail": "Publicada en /monitor"}
  ]
}
```

Cumple el contenido minimo: id, fecha/hora, tipo, severidad, indicador/entidad,
valor observado, umbral, periodo, origen, explicacion, accion y estado.

## 6. Reconocimiento

```json
POST /alerts/3/ack
{"alert_id": 3, "status": "acknowledged", "acknowledged_at": "2026-11-14T03:24:56+00:00"}
```

## 7. Alerta simulada

```json
POST /alerts/simulate {"severity": "critical"}
{
  "alert_id": 7,
  "rule_code": "SIMULACION",
  "alert_type": "simulacion",
  "severity": "critical",
  "simulated": 1,
  "source": "POST /alerts/simulate",
  "status": "open"
}
```

La simulacion se marca con `simulated=1`, se excluye con
`GET /alerts?incluir_simuladas=false` y no se confunde con una alerta real.

## 8. Vista de monitoreo

```json
GET /monitor.json
{
  "pipeline": {
    "data_updated_at": "2026-11-14T02:47:00.789000",
    "fact_rows": 5,
    "ultima_carga": {"execution_id": 150, "pipeline": "sales_dw_fact", "estado": "SUCCESS",
                     "filas_leidas": 5, "filas_rechazadas": 0},
    "ejecuciones_24h": 150,
    "fallas_24h": 0,
    "rechazos_total": 0,
    "rechazos_abiertos": 0,
    "rechazos_por_regla": []
  },
  "modelo": {
    "estado": "insufficient_data",
    "version": null,
    "mae": null,
    "periodos_train": 0,
    "periodos_test": 1,
    "mensaje": "Se necesitan al menos 8 meses con ventas ...; hay 1. No se publican metricas."
  },
  "notificaciones": {
    "total": 3,
    "simuladas": 0,
    "por_severidad": {"info": 1, "warning": 2},
    "por_estado": {"open": 3},
    "entregadas": 3
  },
  "ultimas_alertas": [ ... ]
}
```

`GET /monitor` devuelve la misma informacion como HTML autocontenido (200,
~3.5 KB), con refresco cada 30 s y enlaces a `/monitor.json` y `/alerts`.

## 9. Pruebas automatizadas

### Reglas y registro (`tests/test_alerting_rules.py`)

No requiere servicios: evalua reglas puras y `AlertStore` sobre SQLite temporal.

```
Caso 1: datos reales            -> VENTAS_BAJAS, TICKET_BAJO, MODELO_SIN_ENTRENAR (3)
Caso 2: contexto sano           -> ninguna
Caso 3: contexto critico        -> CAIDA_VENTAS, MAE_ALTO, RECHAZOS_ALTOS (+ 2 de negocio)
Caso 4: contenido minimo        -> 13 campos presentes, umbral 1000, observado 696.40
Caso 5: anti-duplicado          -> 1 nueva, 1 duplicada, mismo alert_id, 1 entrega
Caso 6: reconocimiento          -> acknowledged + stats coherentes
Caso 7: simulada                -> simulated=1 y excluida del listado real

RESULTADO: OK - reglas, deduplicacion y entregas verificadas
```

### Prueba de humo (`tests/smoke_alerting.py`)

Con los tres servicios arriba y `ALERT_DB_PATH` aislado:

```
GET /health                                    OK  (core-api=ok, ml=insufficient_data)
GET /rules devuelve 6 reglas                   OK
POST /alerts/evaluate                          OK  (3 nuevas)
segunda evaluacion no duplica alertas          OK  (0 nuevas, 3 duplicadas)
GET /alerts responde                           OK
POST /alerts/{id}/ack                          OK
GET /alerts/{id} registra entrega              OK
POST /alerts/simulate marca simulated          OK
GET /monitor.json trae pipeline, modelo y alertas OK
GET /monitor devuelve HTML                     OK

RESULTADO: OK
```

## 10. Controles aplicados

1. **Sin acceso directo a SQL Server:** las metricas se leen por HTTP de
   `core-api` y `ml`; el unico almacenamiento propio es el registro de alertas.
2. **Sin duplicados:** `event_key` unico y `(alert_id, channel)` unico.
3. **Trazabilidad:** cada alerta guarda origen, periodo, valor, umbral,
   explicacion, accion y fecha; cada entrega queda registrada.
4. **Simulaciones identificadas:** `simulated=1`, separables del listado real.
5. **Umbrales configurables:** por `.env`, sin recompilar.
6. **Fallo controlado:** si `core-api` no responde, `/health` queda `degraded` y
   `/alerts/evaluate` devuelve 503 (no inventa alertas).

## 11. Limitaciones

- El canal es la vista dashboard (`/monitor`) mas el registro de entrega. No se
  configuro SMTP ni WebSocket; la tarjeta pide uno de los canales.
- La evaluacion es bajo demanda (`POST /alerts/evaluate`) y desde la CLI. No hay
  scheduler propio: en produccion se dispararia desde el orquestador del ETL o
  un cron.
- `CAIDA_VENTAS` queda muda mientras exista un solo periodo con ventas; es el
  comportamiento correcto (no se inventa una comparacion).
- SQLite reserva el autonumerico aunque `INSERT OR IGNORE` no inserte; por eso
  una simulacion posterior puede recibir un id mayor que el total de alertas.
