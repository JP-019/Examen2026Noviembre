# Informe final del proyecto

**Plataforma Integral de Ingenieria de Datos y Analitica Inteligente**

| Campo | Valor |
|---|---|
| Proceso de negocio | VENTAS (unico proceso en alcance) |
| Metodologia | SCRUM adaptado a 3 dias + buffer |
| Periodo | 11 al 14 de noviembre de 2026 |
| Sprints | S0 Fundaciones, S1 Datos, S2 Analitica, S3 Cierre |
| Alcance | 15 tareas, 76 story points, 8 epicas |
| Repositorio | `data-platform/` (rama `master`) |
| Ambiente | Windows, SQL Server 2025 local, Python 3.12.10 |
| Estado general | 13 tareas cerradas, 2 parciales (T01 y T15) |

---

## 1. Resumen ejecutivo

Se construyo una plataforma de datos de punta a punta sobre el proceso de
**ventas**: extraccion desde la base transaccional, staging en tres zonas con
auditoria y cuarentena, Data Warehouse dimensional, API de KPIs, dashboard web,
modelo predictivo, asistente de lenguaje natural con consultas aprobadas y motor
de alertas con monitoreo.

Resultados verificables al cierre:

| Indicador | Resultado |
|---|---|
| Tablas de la fuente inventariadas | 10 |
| Filas reconciliadas entre fuente, staging y DW | 5 filas / S/ 696.40 |
| Huerfanos en el hecho | 0 |
| Reglas de calidad catalogadas | 15 (DQ-001 a DQ-015) |
| KPIs publicados por API y dashboard | 6 |
| Microservicios desplegables | 7 |
| Reglas de alerta | 6 |
| Pruebas de la rubrica ejecutadas | 12 de 12 en OK |
| Pruebas del asistente GenAI | 10 de 10 en OK |
| Secretos versionados | 0 |

La entrega cumple la regla de oro del proyecto: **ningun consumidor se conecta
directo a SQL Server**. El acceso a datos pasa siempre por `core-api` y el ETL.

---

## 2. Metodologia SCRUM aplicada

### 2.1 Roles

| Rol | Responsabilidad | Tareas |
|---|---|---|
| Product Owner | Alcance, KPIs y prioridad | Aprobacion del backlog |
| Scrum Master | Ceremonias, desbloqueo y tiempo | T03, coordinacion |
| Data Engineer | Fuente, staging, ETL y calidad | T01, T02, T04, T05, T06 |
| DW / BI Developer | Modelo dimensional, API y dashboard | T03, T07, T08, T09, T10 |
| ML Engineer | Modelo predictivo y metricas | T11 |
| GenAI / Automation | Asistente y alertas | T12, T13 |
| QA / Documentacion | Documentacion, pruebas y demo | T14, T15 |

### 2.2 Calendario y ceremonias

| Sprint | Fecha | Meta | Tareas |
|---|---|---|---|
| S0 Fundaciones | 11 nov | Repo, fuente y arquitectura listos | T01, T02, T03 |
| S1 Datos confiables | 12 nov | ETL, calidad y DW reconciliado | T04, T05, T06, T07, T08 |
| S2 Analitica inteligente | 13 nov | Dashboard, ML, GenAI y alertas | T09, T10, T11, T12, T13 |
| S3 Cierre y demo | 14 nov | Documentacion, pruebas y ensayo | T14, T15 |

Ceremonias realizadas segun el plan: Planning de 15 min al inicio de cada
sprint, Daily de 10 min, Review con evidencia al cierre y Retrospectiva de 5
min. La regla de recorte no fue necesaria: se ejecuto el alcance completo, con
las dos excepciones justificadas en la seccion 8.

### 2.3 Definition of Done aplicada

Cada tarea se cerro solo con: criterios de aceptacion marcados, evidencia
reproducible en `documentation/evidencias/`, ausencia de secretos y codigo
versionado en Git. El historial se reestructuro para que **cada tarea tenga su
propio commit**, de forma que la trazabilidad tarea -> cambio sea directa.

---

## 3. Estado del Product Backlog

| ID | Historia | Epica | Pri | SP | Sprint | Estado |
|---|---|---|---|---|---|---|
| T01 | Entorno y fuente de datos reproducible | 1 | 1 | 3 | S0 | **Parcial** |
| T02 | Inventario, ERD, diccionario y preguntas analiticas | 1 | 1 | 5 | S0 | Cerrada |
| T03 | Arquitectura, alcance, stack y decisiones | 1 | 1 | 3 | S0 | Cerrada |
| T04 | Staging 3 zonas + auditoria + cuarentena | 2 | 1 | 5 | S1 | Cerrada |
| T05 | Extraccion inicial e incremental con idempotencia | 2 | 1 | 8 | S1 | Cerrada |
| T06 | Reglas de calidad y transformaciones obligatorias | 2 | 1 | 5 | S1 | Cerrada |
| T07 | Modelo dimensional: hechos, dimensiones y SCD | 3 | 1 | 8 | S1 | Cerrada |
| T08 | Carga al DW y reconciliacion entre capas | 3 | 1 | 5 | S1 | Cerrada |
| T09 | API backend (FastAPI) con endpoints de KPIs | 4 | 1 | 5 | S2 | Cerrada |
| T10 | Dashboard web: KPIs, filtros, detalle y tendencias | 4 | 1 | 8 | S2 | Cerrada |
| T11 | Modelo ML con baseline, evaluacion y endpoint | 5 | 1 | 5 | S2 | Cerrada |
| T12 | Asistente GenAI + 10 pruebas | 6 | 1 | 5 | S2 | Cerrada |
| T13 | Alerta end-to-end, reglas y monitoreo | 7 | 2 | 3 | S2 | Cerrada |
| T14 | Documentacion, README y plan de pruebas | 8 | 1 | 5 | S3 | Cerrada |
| T15 | Video de 5 min y ensayo de demo | 8 | 1 | 3 | S3 | **Parcial** |

**Avance:** 13 de 15 tareas cerradas, 2 parciales, 76 story points entregados.

---

## 4. Detalle de ejecucion por tarea

### T01 - Entorno y fuente de datos reproducible (parcial)

Se eligio **SQL Server** con la base `Venta` (ADR-001) por ser la fuente real del
proceso, con datos ya disponibles y sin costo de migracion. Se crearon esquemas
separados para `source`, `staging` y `dw`, un usuario tecnico con permisos
minimos y `.env.example` sin credenciales.

**Evidencia:** `database/00_schemas.sql`, `deployment/README.md`,
`scripts/start_all.ps1`, `documentation/adr/ADR-001-fuente-datos.md`.

**Pendiente:** el `docker-compose.yml` no se ejecuto porque Docker no esta
instalado en el equipo; queda documentado como via alternativa. El ambiente
local si es reproducible desde cero con los pasos del README.

### T02 - Inventario, ERD, diccionario y preguntas analiticas

Inventario de las 10 tablas del proceso de ventas, ERD editable en DBML,
diccionario con tipos, claves y nulos, perfilado de columnas y definicion de los
6 KPIs con sus preguntas analiticas.

**Evidencia:** `documentation/fuente_datos.md`, `fuente_datos.dbml`,
`diccionario_fuente.csv`.

### T03 - Arquitectura, alcance, stack y decisiones

Diagrama por capas y siete ADR que justifican cada tecnologia. Se declaro el
no-alcance (compras, stock, tiempo real, app movil) y la frecuencia de
actualizacion: **batch diario 02:00, latencia menor a 24 horas**. Se agrego el
servicio `catalog`, que publica un indice vivo del repositorio.

**Evidencia:** `documentation/arquitectura.md`, `documentation/adr/`,
`catalog/platform.json`, `INDEX.md`.

### T04 - Staging con tres zonas, auditoria y cuarentena

Zonas `raw` (append-only), `clean` (tipado y validado) y `ready` (integrado),
mas `audit.etl_execution` con los 14 campos requeridos y
`quarantine.rejected_row`. Cada fila preparada conserva su clave de negocio y el
linaje `_execution_id`.

**Evidencia:** `database/01_staging.sql`, `documentation/staging.md`,
`documentation/evidencias/T04_T07_verificacion.txt`.

### T05 - Extraccion inicial e incremental con idempotencia

Modos `full`, `incremental`, `idempotency-check` y `quality-report`. El
watermark se persiste y **solo se actualiza si la carga termina bien**. La
prueba de reejecucion demuestra que los conteos de las capas estables no
cambian.

**Evidencia:** `services/etl/app/__main__.py`, `documentation/etl.md`,
seccion 3 de `evidencias/T14_pruebas.md`.

### T06 - Reglas de calidad y transformaciones obligatorias

Catalogo de **15 reglas** (DQ-001 a DQ-015) con nombre, condicion y accion. Los
fallos van a cuarentena; los nulos de medidas nunca se imputan con cero. Se
documento la regla de supervivencia de duplicados.

**Evidencia:** `services/etl/app/quality.py`,
`documentation/calidad_datos.md`,
`documentation/evidencias/T06_calidad_reconciliacion.md`.

### T07 - Modelo dimensional estrella

Grano declarado: **una linea de factura**. Dimensiones `DimTiempo`,
`DimProducto`, `DimLocal` y `DimVersion` con clave sustitutiva y clave natural
conservada; `FactVentas` con miembro desconocido (clave 0). Estrategia **SCD
Tipo 1**, con columnas `FilaDesde`/`FilaHasta` preparadas para evolucionar a
Tipo 2.

**Evidencia:** `database/02_dw.sql`, `documentation/modelo_dimensional.md`,
`modelo_dimensional.dbml`.

### T08 - Carga al DW y reconciliacion

Las claves sustitutas se resuelven antes de insertar los hechos y se evitan
joins uno-a-muchos que dupliquen importes. Reconciliacion final:

| Capa | Filas | Importe |
|---|---|---|
| Fuente `Venta.dbo.Factura_Detalle` | 5 | S/ 696.40 |
| `clean.FacturaDetalle` | 5 | S/ 696.40 |
| `ready.Ventas` | 5 | S/ 696.40 |
| `dw.FactVentas` | 5 | S/ 696.40 |

Huerfanos en el hecho: **0**. Diferencias: ninguna sin justificar.

**Evidencia:** `services/etl/app/dw.py`, `report.py`, seccion 7 de
`evidencias/T14_pruebas.md`.

### T09 - API FastAPI con endpoints de KPIs

`core-api` expone `/api/v1/kpis`, `/tendencias`, `/detalle`, `/filtros`,
`/agrupado` y `/monitor`, con SQL parametrizado, whitelist de dimensiones
(`local`, `seccion`, `producto`), paginacion maxima de 200 filas y errores
explicitos (503 si la base no responde). Es la unica puerta de lectura del DW.

**Evidencia:** `services/core-api/`, `documentation/api_contratos.md`,
`documentation/evidencias/T09_api_kpis.md`.

### T10 - Dashboard web

Streamlit consume exclusivamente la API. Muestra 6 KPIs, filtros por fecha y
tres dimensiones, tendencia historica, comparacion entre periodos, agrupados,
tabla de detalle paginada y drill-down, con estados de carga, error y sin datos.
Siempre visible la fecha de ultima actualizacion.

**Evidencia:** `services/dashboard/`,
`documentation/evidencias/T10_dashboard.md`.

### T11 - Modelo ML con baseline y evaluacion temporal

Division temporal train/test (nunca aleatoria), baseline comparado contra el
modelo y metricas MAE, RMSE y MAPE. Con la fuente real hay **un solo mes**, por
lo que el servicio responde `insufficient_data` y **no publica metricas
inventadas**. La verificacion del algoritmo se hizo con una serie sintetica
identificada como tal: MAE 38.9 frente a 480.0 del baseline.

**Evidencia:** `services/ml/`, `database/03_ml.sql`, `documentation/ml.md`,
`documentation/evidencias/T11_ml.md`.

### T12 - Asistente GenAI con consultas aprobadas

El asistente nunca ejecuta SQL libre: traduce la pregunta a un catalogo de
intenciones y consulta `core-api`. Cada respuesta incluye `grounded`, las
fuentes y la fecha de actualizacion; fuera de alcance responde `no_data`.

**Evidencia:** `services/genai/`, `documentation/genai.md`,
`documentation/evidencias/T12_genai.md` (10 de 10 pruebas OK).

### T13 - Alertas end-to-end y monitoreo

Seis reglas sobre KPIs, prediccion y rechazos. La deduplicacion por evento evita
notificaciones repetidas y se registra generacion y entrega. La vista de
monitoreo integra estado del pipeline, modelo y alertas.

**Evidencia:** `services/alerting/`, `documentation/alertas.md`,
`documentation/evidencias/T13_alerting.md`.

### T14 - Documentacion, manual y pruebas

Se completo la documentacion obligatoria (requerimientos, arquitectura, ERD,
modelo dimensional, calidad, APIs, ML, GenAI, alertas, plan de pruebas y
manual), un README reproducible y la suite de pruebas. Las **12 pruebas** de la
rubrica se ejecutaron con salida real.

**Evidencia:** `README.md`, `documentation/`, `tests/`,
`documentation/evidencias/T14_pruebas.md`.

### T15 - Video y ensayo de demo (parcial)

Estan listos el guion de 5 minutos, el reparto por bloque y el checklist de demo
en vivo con plan B. **Falta la grabacion del video y el ensayo formal**, tarea
del equipo antes de la presentacion.

**Evidencia:** `documentation/demo.md`.

---

## 5. Arquitectura y stack

### 5.1 Flujo de datos

```
Venta (SQL Server)
  -> raw -> clean -> ready        (services/etl)
  -> dw (esquema estrella)        (services/etl)
  -> core-api :8000 -> dashboard :8501
  -> ml :8002 / genai :8003 / alerting :8004
  -> catalog :8001 publica el indice vivo
```

### 5.2 Stack

| Componente | Herramienta |
|---|---|
| Motor de datos | SQL Server 2025 (local) |
| ETL | Python 3.12 + pyodbc + pandas |
| API | FastAPI + Uvicorn + Pydantic |
| Dashboard | Streamlit + Plotly |
| ML | scikit-learn |
| GenAI | Capa de consultas aprobadas (determinista, sin claves externas) |
| Alertas | Python + almacen SQLite + vista de monitoreo |
| Versionado | Git |

### 5.3 Decisiones clave

| ADR | Decision |
|---|---|
| ADR-001 | Fuente SQL Server `Venta` |
| ADR-002 | Capas separadas por esquemas en una instancia local |
| ADR-003 | Extraccion incremental por watermark con idempotencia |
| ADR-004 | Modelo estrella con grano linea de factura |
| ADR-005 | API FastAPI y frontend desacoplado |
| ADR-006 | GenAI con consultas aprobadas, sin SQL libre |
| ADR-007 | Microservicios con catalogo de plataforma |

---

## 6. Resultados tecnicos

| Componente | Resultado |
|---|---|
| ETL | 10 tablas extraidas, 3 zonas, 0 rechazos pendientes |
| Idempotencia | Conteos estables en `clean`, `ready` y `dw` tras reejecutar |
| DW | `FactVentas` 5 filas; `DimTiempo` 13 150 filas (2000-2035) |
| API | 6 endpoints de negocio + health y monitor |
| Dashboard | 6 KPIs, 4 locales y 2 secciones disponibles como filtros |
| ML | `insufficient_data` con datos reales; baseline superado en serie sintetica |
| GenAI | 10 intenciones, respuestas con fuentes y `grounded` |
| Alertas | 3 alertas nuevas en la primera evaluacion, 0 duplicadas en la segunda |

---

## 7. Pruebas y evidencias

| # | Prueba | Resultado |
|---|---|---|
| 1 | Carga inicial | OK |
| 2 | Carga incremental | OK |
| 3 | Idempotencia | OK |
| 4 | Nulos y duplicados | OK |
| 5 | Integridad referencial | OK |
| 6 | Recuperacion ante falla | OK |
| 7 | Reconciliacion entre capas | OK |
| 8 | Dashboard | OK |
| 9 | Modelo ML | OK |
| 10 | GenAI (10/10) | OK |
| 11 | Alertas (disparo, no disparo, deduplicacion) | OK |
| 12 | End-to-end | OK |

La prueba 6 demuestra que una falla de conexion **no avanza el watermark** y el
reintento termina con los conteos intactos. La prueba 12 recorre fuente -> DW ->
API -> dashboard / GenAI / ML / alertas con los 7 servicios arriba.

Detalle completo y salidas reales: `documentation/evidencias/T14_pruebas.md`.

---

## 8. Trazabilidad con la rubrica

| Criterio | Peso | Tareas | Evidencia |
|---|---|---|---|
| Analisis y arquitectura | 10% | T01, T02, T03 | `arquitectura.md`, `fuente_datos.md`, `adr/` |
| ETL, staging y calidad | 20% | T04, T05, T06 | `01_staging.sql`, `staging.md`, `calidad_datos.md` |
| Modelo dimensional y DW | 15% | T07, T08 | `02_dw.sql`, `modelo_dimensional.md`, reconciliacion |
| Dashboard y API | 15% | T09, T10 | `core-api/`, `dashboard/`, `api_contratos.md` |
| Machine Learning | 10% | T11 | `services/ml/`, `ml.md` |
| Generative AI | 10% | T12 | `services/genai/`, `genai.md` |
| Automatizacion | 5% | T13 | `services/alerting/`, `alertas.md` |
| Pruebas y documentacion | 10% | T14 | `tests/`, `plan_pruebas.md`, `manual.md` |
| Demo y comunicacion | 5% | T15 | `demo.md` (video pendiente) |

---

## 9. Riesgos, limitaciones y deuda tecnica

| Elemento | Situacion | Impacto | Plan |
|---|---|---|---|
| Docker no instalado | Via contenedor documentada, no ejecutada | T01 parcial | Instalar Docker o mantener la via local |
| Fuente con 5 lineas y 1 mes | Analisis historico limitado | ML en `insufficient_data` | Ampliar ventana de datos de la fuente |
| Video y ensayo | No grabados | T15 parcial | Grabar con el guion de `demo.md` |
| Canal de alertas | Solo dashboard | Sin correo ni WebSocket | Agregar SMTP si el negocio lo pide |
| SCD Tipo 1 | Sin historial de atributos | No hay analisis de cambios | Evolucionar a Tipo 2 (columnas ya previstas) |
| Autenticacion | Basica del despliegue local | No apto para produccion | Integrar proveedor de identidad |
| Fuente desnormalizada | Sin clientes, empleados ni geografia | Dimensiones no aplicables | Declarado como restriccion en requerimientos |

---

## 10. Retrospectiva

**Que funciono**

- Separar staging en tres zonas desde el inicio evito retrabajo en el DW.
- La reconciliacion numerica (5 filas / S/ 696.40) dio confianza inmediata.
- El catalogo de consultas aprobadas elimino el riesgo de cifras inventadas.
- El indice vivo (`catalog`) mantuvo la documentacion alineada con el codigo.

**Que mejorar**

- Confirmar dependencias (Docker) en el Sprint 0, no al final.
- Generar datos sinteticos etiquetados desde el inicio para el analisis historico.
- Automatizar la regeneracion de evidencias con un solo comando.

**Acciones para el siguiente ciclo**

1. Grabar el video y ensayar la demo completa.
2. Añadir un comando unico de verificacion end-to-end.
3. Incorporar migraciones versionadas para el esquema.

---

## 11. Conclusiones

El proyecto entrega una plataforma funcional, reproducible y verificable sobre el
proceso de ventas, con separacion estricta de capas, trazabilidad de cada fila y
honestidad analitica: el modelo ML no publica metricas cuando no hay historia
suficiente y el asistente GenAI responde `no_data` cuando no tiene respaldo.

Las dos tareas parciales estan acotadas y justificadas: T01 por ausencia de
Docker en el equipo y T15 por la grabacion del video, que depende del equipo.
Ninguna afecta los criterios no recortables de la rubrica: staging con
trazabilidad, grano declarado, KPIs validados con SQL independiente, baseline y
evaluacion fuera de entrenamiento, y repositorio sin secretos.

---

## Anexos

### A. Estructura del repositorio

```
data-platform/
  documentation/   arquitectura, ADR, staging, modelo, calidad y evidencias
  database/        scripts SQL de esquemas, staging, DW y ML
  services/        etl, catalog, core-api, dashboard, ml, genai, alerting
  catalog/         manifiesto de la plataforma (platform.json)
  scripts/         generador de indice y arranque local
  tests/           pruebas y evidencias (T14)
  deployment/      despliegue local y contenedores
  INDEX.md         indice generado
  README.md        guia reproducible
```

### B. Comandos de verificacion

```powershell
Copy-Item .env.example .env
sqlcmd -S localhost -E -C -f 65001 -i database/00_schemas.sql
cd services/etl ; python -m app full
python -m app idempotency-check
python -m app quality-report
sqlcmd -S localhost -E -C -f 65001 -i database/99_verify.sql
python tests/e2e_smoke.py
```

### C. Historial Git

El historial se reorganizo para que cada tarea SCRUM tenga su commit:

| Commit | Contenido |
|---|---|
| `chore` | Reglas de ingenieria y `.gitignore` |
| `feat(T01)` a `feat(T13)` | Una tarea por commit, con contexto y story points |
| `docs(T14)` | Documentacion, manual y suite de pruebas |
| `docs(T15)` | Guion y checklist de demo |
| `docs` | Este informe final |

El historial anterior se conserva integro en la rama
`respaldo/historial-original`.

### D. Control de secretos

`git ls-files` y el historial no contienen `.env`. El unico archivo de
configuracion versionado es `.env.example`, con valores vacios o de ejemplo, y
todas las credenciales se leen del entorno.
