# Plataforma Integral de Ingenieria de Datos y Analitica Inteligente

**Proceso de negocio:** VENTAS  
**Arquitectura:** microservicios  
**Versión del índice:** 1.0.0  
**Actualizado:** 2026-11-13

> Este archivo se genera desde `catalog/platform.json`.
> No editarlo a mano: ejecutar `python scripts/build_index.py`.

## Como navegar este repositorio

1. Para entender el sistema completo: este indice.
2. Para ver el indice en vivo: `uvicorn app.main:app --port 8001` desde
   `services/catalog` y abrir <http://localhost:8001/index.md>.
3. Para los detalles tecnicos: `documentation/`.
4. Para el codigo: `services/<nombre>/README.md`.

Flujo de datos:

```
Venta (SQL Server)
  -> raw -> clean -> ready            (services/etl)
  -> dw (estrella)                    (services/etl)
  -> core-api -> dashboard            (Sprint 2)
  -> ml / genai / alerting            (Sprint 2)
```

## Servicios

| id | servicio | carpeta | tipo | estado | puerto | tareas |
|---|---|---|---|---|---|---|
| etl | ETL de ventas | services/etl | proceso por lotes | implementado | - | T05, T06 |
| catalog | Catalogo de la plataforma | services/catalog | HTTP | implementado | 8001 | T03 |
| core-api | API de KPIs | services/core-api | HTTP | implementado | 8000 | T09 |
| dashboard | Dashboard web | services/dashboard | interfaz web | implementado | 8501 | T10 |
| ml | Servicio de Machine Learning | services/ml | HTTP | implementado | 8002 | T11 |
| genai | Asistente GenAI | services/genai | HTTP | implementado | 8003 | T12 |
| alerting | Motor de alertas | services/alerting | HTTP | implementado | 8004 | T13 |

## Carpetas y proposito

| carpeta | proposito | contiene |
|---|---|---|
| documentation | Requerimientos, arquitectura, decisiones, datos, servicios, manual, demo y evidencias. | requerimientos.md, arquitectura.md, adr/, fuente_datos.md, staging.md, modelo_dimensional.md, calidad_datos.md, etl.md, api_contratos.md, ml.md, genai.md, alertas.md, plan_pruebas.md, manual.md, demo.md, evidencias/ |
| database | Scripts SQL de creacion y verificacion de esquemas. | 00_schemas.sql, 01_staging.sql, 02_dw.sql, 98_reset.sql, 99_verify.sql |
| services | Un directorio por microservicio, con su propio README, codigo y dependencias. | etl/, catalog/, core-api/, dashboard/, ml/, genai/, alerting/ |
| services/etl | Ingesta batch: fuente a raw, clean, ready y DW con auditoria y cuarentena. | app/, README.md, requirements.txt |
| services/catalog | Indice vivo de la plataforma: servicios, carpetas, funciones y rutas. | app/, README.md, requirements.txt |
| services/core-api | API de KPIs sobre el DW, unica puerta de lectura (T09). | app/, README.md, requirements.txt |
| services/dashboard | Dashboard de KPIs y modos de chat GenAI/Ollama sin acceso directo a SQL Server (T10, T12). | app.py, api_client.py, genai_client.py, ollama_client.py, pages/, README.md, requirements.txt |
| services/ml | Entrenamiento y prediccion de ventas mensuales con baseline (T11). | app/, artifacts/, README.md, requirements.txt |
| services/genai | Asistente con catalogo de consultas aprobadas y 10 pruebas (T12). | app/, README.md, requirements.txt |
| services/alerting | Reglas, alertas sin duplicados, entregas y monitoreo operativo (T13). | app/, README.md, requirements.txt |
| catalog | Manifiesto unico de la plataforma que consume el servicio de catalogo. | platform.json |
| scripts | Utilidades de desarrollo: generacion del indice y arranque local. | build_index.py, start_all.ps1 |
| tests | Pruebas automatizadas, end-to-end y plan de pruebas (Sprint 3). | smoke_core_api.py, smoke_dashboard.py, e2e_smoke.py, test_quality_rules.py, README.md |
| deployment | Despliegue local y contenedores (alternativa no probada sin Docker). | README.md |

## Rutas HTTP

| servicio | metodo | ruta | descripcion | estado |
|---|---|---|---|---|
| catalog | GET | / | Resumen de la plataforma y enlaces. | implementado |
| catalog | GET | /health | Estado del servicio. | implementado |
| catalog | GET | /index | Indice completo (servicios, carpetas, funciones, rutas). | implementado |
| catalog | GET | /index.md | Mismo indice en Markdown. | implementado |
| catalog | GET | /map | Carpetas con su proposito y contenido. | implementado |
| catalog | GET | /services | Lista de microservicios y estado. | implementado |
| catalog | GET | /services/{service_id} | Detalle de un servicio con sus funciones. | implementado |
| catalog | GET | /routes | Todas las rutas HTTP de la plataforma. | implementado |
| core-api | GET | /api/v1/health | Estado y ultima actualizacion de datos. | implementado |
| core-api | GET | /api/v1/kpis | 4 a 6 KPIs con filtros de fecha y dimension. | implementado |
| core-api | GET | /api/v1/tendencias | Serie temporal y comparacion entre periodos. | implementado |
| core-api | GET | /api/v1/detalle | Detalle paginado de lineas de venta. | implementado |
| core-api | GET | /api/v1/filtros | Valores disponibles para los filtros. | implementado |
| core-api | GET | /api/v1/agrupado | Totales por local, seccion o producto. | implementado |
| core-api | GET | /api/v1/monitor | Estado operativo del pipeline, calidad y hecho. | implementado |
| ml | GET | /model | Version, parametros y metricas del modelo activo. | implementado |
| ml | POST | /predict | Prediccion para N meses (1 a 12). | implementado |
| ml | GET | /metrics | MAE/RMSE del modelo y del baseline. | implementado |
| ml | GET | /series | Serie mensual observada. | implementado |
| ml | POST | /train | Entrena, versiona y registra el experimento. | implementado |
| genai | POST | /ask | Pregunta en lenguaje natural con respuesta respaldada. | implementado |
| genai | GET | /queries | Catalogo de consultas aprobadas. | implementado |
| genai | GET | /tests | Tabla de las 10 pruebas documentadas. | implementado |
| genai | POST | /tests/run | Ejecuta las 10 pruebas y devuelve el resultado. | implementado |
| genai | GET | /health | Estado del asistente y de core-api. | implementado |
| alerting | GET | /health | Estado del motor, core-api y ML. | implementado |
| alerting | GET | /rules | Reglas y umbrales vigentes. | implementado |
| alerting | POST | /alerts/evaluate | Evalua las reglas y registra solo alertas nuevas. | implementado |
| alerting | GET | /alerts | Listado de alertas con estado y filtros. | implementado |
| alerting | GET | /alerts/{id} | Detalle de una alerta y sus entregas. | implementado |
| alerting | POST | /alerts/{id}/ack | Reconoce una alerta. | implementado |
| alerting | POST | /alerts/simulate | Genera una alerta simulada identificada. | implementado |
| alerting | GET | /monitor | Vista HTML de monitoreo operativo. | implementado |
| alerting | GET | /monitor.json | Snapshot de monitoreo en JSON. | implementado |

## Documentacion

| documento | titulo | tarea |
|---|---|---|
| documentation/requerimientos.md | Requerimientos funcionales y no funcionales | T14 |
| documentation/arquitectura.md | Arquitectura de la solucion | T03 |
| documentation/adr/ | Decisiones de arquitectura (ADR) | T03 |
| documentation/fuente_datos.md | ERD, claves, diccionario y perfilado de la fuente | T02, T14 |
| documentation/fuente_datos.dbml | ERD editable de la fuente | T02, T14 |
| documentation/diccionario_fuente.csv | Diccionario de la fuente en CSV | T02, T14 |
| documentation/staging.md | Staging, auditoria y cuarentena | T04 |
| documentation/modelo_dimensional.md | Modelo dimensional y grano | T07 |
| documentation/calidad_datos.md | Catalogo de reglas de calidad | T06 |
| documentation/etl.md | Extraccion, transformacion, carga y recuperacion | T14 |
| documentation/api_contratos.md | APIs, contratos JSON y errores | T14 |
| documentation/ml.md | Modelo predictivo, corte temporal y limites | T14 |
| documentation/genai.md | Asistente con consultas aprobadas y anti-alucinacion | T14 |
| documentation/alertas.md | Reglas, anti-duplicado y monitoreo | T14 |
| documentation/plan_pruebas.md | Plan y resultados de las 12 pruebas | T14 |
| documentation/manual.md | Instalacion, operacion, recuperacion y uso | T14 |
| documentation/demo.md | Guion del video y checklist de demo | T15 |
| documentation/evidencias/T04_T07_verificacion.txt | Evidencia de staging y DW | T04, T07 |
| documentation/evidencias/T06_calidad_reconciliacion.md | Reporte de calidad y reconciliacion | T05, T06, T08 |
| documentation/evidencias/T09_api_kpis.md | Evidencia de la API de KPIs y pruebas de humo | T09 |
| documentation/evidencias/T10_dashboard.md | Evidencia del dashboard y pruebas de render | T10 |
| documentation/evidencias/T11_ml.md | Evidencia del modelo ML, baseline y limitaciones | T11 |
| documentation/evidencias/T12_genai.md | Evidencia del asistente GenAI y las 10 pruebas | T12 |
| documentation/evidencias/T13_alerting.md | Evidencia de reglas, anti-duplicado y monitoreo | T13 |
| documentation/evidencias/T14_pruebas.md | Salidas reales de las 12 pruebas y control de secretos | T14 |

## Trazabilidad de tareas SCRUM

| tarea | titulo | estado | artefactos |
|---|---|---|---|
| T01 | Entorno y fuente reproducible | parcial | database/00_schemas.sql, README.md, .env.example |
| T02 | Inventario, ERD y diccionario | completada | documentation/fuente_datos.md, documentation/fuente_datos.dbml, documentation/diccionario_fuente.csv |
| T03 | Arquitectura y decisiones | completada | documentation/arquitectura.md, documentation/adr/ |
| T04 | Staging 3 zonas + auditoria + cuarentena | completada | database/01_staging.sql, documentation/staging.md |
| T05 | Extraccion inicial e incremental | completada | services/etl/app/staging.py |
| T06 | Reglas de calidad y transformaciones | completada | services/etl/app/quality.py, documentation/calidad_datos.md |
| T07 | Modelo dimensional | completada | database/02_dw.sql, documentation/modelo_dimensional.md |
| T08 | Carga al DW y reconciliacion | completada | services/etl/app/dw.py, services/etl/app/report.py |
| T09 | API de KPIs | completada | services/core-api/app/main.py, services/core-api/app/services.py, documentation/evidencias/T09_api_kpis.md |
| T10 | Dashboard web | completada | services/dashboard/app.py, services/dashboard/api_client.py, documentation/evidencias/T10_dashboard.md |
| T11 | Modelo ML | completada | services/ml/app/models.py, database/03_ml.sql, documentation/evidencias/T11_ml.md |
| T12 | Asistente GenAI | completada | services/genai/app/query_catalog.py, services/genai/app/queries.py, services/genai/app/checks.py, documentation/evidencias/T12_genai.md |
| T13 | Alertas y monitoreo | completada | services/alerting/app/rules.py, services/alerting/app/store.py, documentation/evidencias/T13_alerting.md |
| T14 | Documentacion y pruebas | completada | documentation/requerimientos.md, documentation/fuente_datos.md, documentation/etl.md, documentation/api_contratos.md, documentation/ml.md, documentation/genai.md, documentation/alertas.md, documentation/plan_pruebas.md, documentation/manual.md, documentation/evidencias/T14_pruebas.md, tests/e2e_smoke.py, tests/test_quality_rules.py, README.md |
| T15 | Video y demo | parcial | documentation/demo.md |

## Arranque rapido

```powershell
# 1. Base de datos (una sola vez)
sqlcmd -S localhost -E -C -i database/00_schemas.sql
sqlcmd -S localhost -E -C -i database/01_staging.sql
sqlcmd -S localhost -E -C -i database/02_dw.sql

# 2. Pipeline ETL
cd services/etl
python -m pip install -r requirements.txt
python -m app full

# 3. Indice vivo
cd ../catalog
python -m pip install -r requirements.txt
uvicorn app.main:app --port 8001
```

Puertos: catalog 8001, core-api 8000, ml 8002, genai 8003, alerting 8004, dashboard 8501.
