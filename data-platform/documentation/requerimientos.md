# Requerimientos - Plataforma Integral de Ingenieria de Datos y Analitica

- **Tarea:** T14
- **Proceso de negocio:** ventas
- **Fuente:** base `Venta` (SQL Server)
- **Alcance:** ingesta, calidad, Data Warehouse, API, dashboard, ML, asistente
  GenAI y alertas

---

## 1. Objetivo

Poner a disposicion del negocio un unico conjunto de datos de ventas confiable,
con trazabilidad de origen, indicadores consistentes, analisis historico,
prediccion honesta y alertas operativas, sin que ningun consumidor acceda
directamente a SQL Server.

---

## 2. Actores

| Actor | Necesidad |
|---|---|
| Responsable de operaciones | Ver KPIs y recibir alertas ante desvios |
| Analista de datos | Explorar tendencias, detalle y exportar |
| Data Engineer | Operar y recuperar el pipeline |
| Evaluador / nuevo integrante | Ejecutar y verificar la solucion sin ayuda |
| Asistente GenAI | Responder preguntas con datos verificables |

---

## 3. Requerimientos funcionales

| ID | Requerimiento | Implementacion | Tarea |
|---|---|---|---|
| RF-01 | Extraer las 10 tablas del proceso de ventas a una zona raw append-only | `services/etl` con `pyodbc` | T05 |
| RF-02 | Soportar carga inicial e incremental por watermark | `python -m app full` / `incremental` | T05 |
| RF-03 | Validar y limpiar con reglas catalogadas, enviando fallos a cuarentena | `clean` + `quarantine.rejected_row` | T06 |
| RF-04 | Integrar una fila por linea de factura en `ready` | `ready.Ventas` | T08 |
| RF-05 | Cargar un star schema con dimensiones, hechos y miembro desconocido | `dw` | T07 |
| RF-06 | Exponer KPIs, tendencias, detalle, filtros y agrupados por HTTP | `core-api` | T09 |
| RF-07 | Mostrar 6 KPIs, filtros, tendencia, comparacion y detalle exportable | `dashboard` | T10 |
| RF-08 | Entrenar con corte temporal, comparar contra baseline y versionar | `services/ml` | T11 |
| RF-09 | Responder preguntas en lenguaje natural solo con consultas aprobadas | `services/genai` | T12 |
| RF-10 | Evaluar reglas, deduplicar alertas y registrar entregas | `services/alerting` | T13 |
| RF-11 | Publicar un indice vivo de servicios, carpetas, funciones y rutas | `services/catalog` | T03 |
| RF-12 | Documentar, probar y demostrar la solucion de punta a punta | `documentation/`, `tests/` | T14, T15 |

---

## 4. Requerimientos no funcionales

| ID | Requerimiento | Criterio verificable |
|---|---|---|
| RNF-01 | **Seguridad de acceso a datos** | Ningun frontend, asistente o motor de alertas se conecta a SQL Server; solo `core-api` y el ETL. |
| RNF-02 | **Consultas parametrizadas** | El 100 % del SQL usa parametros; las dimensiones salen de una whitelist (`local`, `seccion`, `producto`). |
| RNF-03 | **Secretos fuera del repositorio** | `.env` ignorado; `.env.example` sin credenciales reales. |
| RNF-04 | **Idempotencia** | Reejecutar el mismo lote no cambia los conteos de `clean`, `ready` ni `dw`. |
| RNF-05 | **Trazabilidad** | Cada fila de `clean/ready` guarda `_execution_id`; cada corrida queda en `audit.etl_execution`. |
| RNF-06 | **Reconciliacion** | Fuente, `clean`, `ready` y `dw` coinciden en filas e importe (S/ 696.40). |
| RNF-07 | **Disponibilidad controlada** | Si la base o un servicio cae, la API responde 503 y el dashboard muestra el error sin romperse. |
| RNF-08 | **Honestidad analitica** | El ML no publica metricas si no hay periodos; el GenAI responde `grounded=false` fuera de alcance. |
| RNF-09 | **Usabilidad** | El dashboard se entiende sin manual; el README permite ejecutar paso a paso. |
| RNF-10 | **Mantenibilidad** | Un directorio por servicio con README e indice de funciones; manifiesto unico `catalog/platform.json`. |
| RNF-11 | **Portabilidad** | Python 3.12, SQL Server 2019+; via contenedor documentada como opcional. |
| RNF-12 | **Rendimiento** | Respuesta de la API < 1 s con el volumen actual; paginacion maxima de 200 filas. |

---

## 5. Restricciones y no-alcance

| Restriccion | Consecuencia |
|---|---|
| La fuente no tiene clientes, empleados, descuentos ni geografia | No se crean `DimCustomer`, `DimEmployee` ni `DimGeography`; `DimLocal` cubre geografia |
| La fuente tiene un solo mes con ventas | El ML informa `insufficient_data`; la comparacion entre anios no calcula variacion |
| Docker no esta instalado en el equipo | La via contenedor queda documentada pero no ejecutada |
| No se usan APIs de LLM externas | El asistente es determinista y no improvisa cifras |
| El canal de alertas es el dashboard | No se configura SMTP ni WebSocket |

---

## 6. Criterios de aceptacion generales

- [x] Flujo fuente -> raw -> clean -> ready -> dw ejecutable con comandos documentados.
- [x] 0 huerfanos y 0 rechazos sin resolver con la fuente actual.
- [x] 6 KPIs disponibles por API y dashboard.
- [x] Modelo ML con corte temporal y baseline, sin evaluar con entrenamiento.
- [x] Asistente con 10 pruebas y fuentes declaradas.
- [x] Alerta generada, no duplicada y reconocible.
- [x] Repositorio sin secretos y con `.env.example`.
- [x] Documentacion completa en `documentation/` y pruebas en `tests/`.
