# alerting (T13)

## Responsabilidad

Evaluar condiciones de negocio, ML y calidad de datos; generar alertas **sin
duplicados**, registrar la generacion y la entrega al canal y publicar una vista
de monitoreo operativo.

No se conecta a SQL Server. Las metricas las lee de `core-api` y del servicio
`ml`; el registro operativo de alertas vive en un SQLite local
(`services/alerting/data/alerts.db`, fuera del repositorio).

## Reglas implementadas

| Codigo | Tipo | Severidad | Condicion | Origen |
|---|---|---|---|---|
| `VENTAS_BAJAS` | regla_negocio | warning | Ventas del periodo < S/ 1000 | `core-api /api/v1/kpis` |
| `TICKET_BAJO` | regla_negocio | warning | Ticket promedio < S/ 200 | `core-api /api/v1/kpis` |
| `CAIDA_VENTAS` | regla_negocio | critical | Caida > 15% vs periodo anterior | `core-api /api/v1/tendencias` |
| `MODELO_SIN_ENTRENAR` | umbral_ml | info | Menos de 8 periodos o estado distinto de `trained` | `ml /model` |
| `MAE_ALTO` | umbral_ml | warning | MAE del modelo > 500 | `ml /model` |
| `RECHAZOS_ALTOS` | calidad_datos | critical | Rechazos abiertos > 10 | `core-api /api/v1/monitor` |

Los umbrales se configuran por `.env` (`ALERT_VENTAS_MIN`, `ALERT_TICKET_MIN`,
`ALERT_CAIDA_PCT`, `ALERT_MAE_MAX`, `ALERT_RECHAZOS_MAX`).

## Contenido de una alerta

`alert_id`, `created_at`, `rule_code`, `alert_type`, `severity`, `entity`,
`indicator`, `observed_value`, `threshold`, `period`, `source`, `explanation`,
`action`, `status` (`open` / `acknowledged`), `simulated` y `event_key`.

## Anti-duplicado

`event_key = regla | entidad | periodo | data_updated_at`. La columna es `UNIQUE`
en SQLite: si la misma condicion se evalua dos veces sobre los mismos datos, la
segunda evaluacion informa `duplicadas` y no crea una alerta nueva ni otra
entrega. `alert_delivery` tambien es unica por `(alert_id, channel)`.

## Canal de notificacion

Canal implementado: **dashboard** (`GET /monitor`), con registro de entrega en
`alert_delivery` (`channel='dashboard'`, `status='delivered'`). Cada alerta nueva
queda visible en la vista y en `/alerts`.

## Ejecucion

Con `core-api` (8000) y `ml` (8002) corriendo:

```powershell
cd services/alerting
python -m pip install -r requirements.txt
uvicorn app.main:app --port 8004
```

| Recurso | URL |
|---|---|
| Swagger | <http://localhost:8004/docs> |
| Salud | <http://localhost:8004/health> |
| Reglas | <http://localhost:8004/rules> |
| Evaluar | `POST /alerts/evaluate` |
| Alertas | <http://localhost:8004/alerts> (`status`, `severity`, `limit`, `incluir_simuladas`) |
| Reconocer | `POST /alerts/{id}/ack` |
| Simular | `POST /alerts/simulate` (alerta marcada `simulated=1`) |
| Monitoreo | <http://localhost:8004/monitor> (HTML) y `/monitor.json` |

CLI:

```powershell
python -m app evaluate
python -m app rules
python -m app alerts --limit 10
python -m app simulate --severity critical
python -m app monitor
```

## Indice de funciones

| Archivo | Funcion | Que hace |
|---|---|---|
| `app/config.py` | constantes | URLs, umbrales y ruta del SQLite |
| `app/clients.py` | `CoreApi` | KPIs, tendencias, filtros y monitoreo desde core-api |
| `app/clients.py` | `MlApi.model` | Estado y metricas del modelo |
| `app/rules.py` | `Umbrales` | Limites configurables de las 6 reglas |
| `app/rules.py` | `Contexto` | Metricas medidas que consumen las reglas |
| `app/rules.py` | `evaluar` | Aplica las 6 reglas puras y devuelve las alertas |
| `app/rules.py` | `construir_contexto` | Mide core-api + ML y arma el `Contexto` |
| `app/store.py` | `AlertStore.add` | Inserta con `event_key` unico (anti-duplicado) |
| `app/store.py` | `AlertStore.deliver` | Registra la entrega al canal dashboard |
| `app/store.py` | `AlertStore.acknowledge` | Pasa la alerta a `acknowledged` |
| `app/store.py` | `AlertStore.stats` | Totales por severidad, estado y entregas |
| `app/monitor.py` | `snapshot` | Pipeline, calidad, modelo y notificaciones |
| `app/views.py` | `render` | HTML autocontenido de `/monitor` |
| `app/main.py` | `evaluar` | Evalua, registra y entrega alertas nuevas |
| `app/main.py` | `simular` | Alerta de prueba identificada como simulada |

## Definicion de terminado

- [x] 6 disparadores: 3 reglas de negocio, 2 umbrales de ML y 1 de calidad.
- [x] Canal dashboard con registro de entrega.
- [x] Contenido minimo completo (id, fecha/hora, tipo, severidad, indicador,
      valor, umbral, periodo, origen, explicacion, accion, estado).
- [x] Anti-duplicado verificado (segunda evaluacion: 0 nuevas, 3 duplicadas).
- [x] Reconocimiento de alertas y alerta simulada identificada.
- [x] Vista de monitoreo con ultima carga, fallas, rechazos, modelo y alertas.
- [x] Pruebas: `tests/test_alerting_rules.py` y `tests/smoke_alerting.py`.
