# documentation

Indice de la documentacion tecnica. Cada documento declara su tarea de origen.

| Archivo | Contenido | Tarea |
|---|---|---|
| `requerimientos.md` | Requerimientos funcionales, no funcionales y no-alcance | T14 |
| `arquitectura.md` | Alcance, capas, diagrama, stack, frecuencia y riesgos | T03 |
| `adr/` | 7 decisiones de arquitectura justificadas | T03 |
| `fuente_datos.md` | Inventario, ERD, claves, diccionario y perfilado de la fuente | T02, T14 |
| `fuente_datos.dbml` | ERD editable de la fuente en dbdiagram.io | T02, T14 |
| `diccionario_fuente.csv` | Diccionario de la fuente en formato tabular | T02, T14 |
| `staging.md` | Zonas raw/clean/ready, auditoria, cuarentena y linaje | T04 |
| `modelo_dimensional.md` | Grano, dimensiones, hechos, medidas y SCD | T07 |
| `modelo_dimensional.dbml` | Diagrama dimensional editable en dbdiagram.io | T02, T07 |
| `calidad_datos.md` | Catalogo DQ-001 a DQ-015 y politica de nulos | T06 |
| `etl.md` | Extraccion, transformacion, carga, orquestacion y recuperacion | T14 |
| `api_contratos.md` | APIs, contratos JSON, errores y mapa de servicios | T14 |
| `ml.md` | Modelo, corte temporal, baseline, metricas y limites | T14 |
| `genai.md` | Consultas aprobadas, anti-alucinacion y contratos | T14 |
| `alertas.md` | Reglas, anti-duplicado, canal, automatizacion y monitoreo | T14 |
| `plan_pruebas.md` | Las 12 pruebas de la rubrica con evidencia | T14 |
| `manual.md` | Instalacion, despliegue, operacion, recuperacion y usuario | T14 |
| `demo.md` | Guion del video y checklist de demo en vivo | T15 |
| `evidencias/` | Salidas reales de verificacion y reportes | T04 a T14 |

## Orden de lectura recomendado

1. `requerimientos.md` para saber que se prometio.
2. `arquitectura.md` para entender el sistema.
3. `adr/` para entender por que se eligio cada tecnologia.
4. `fuente_datos.md`, `staging.md` y `modelo_dimensional.md` para el diseno de datos.
5. `calidad_datos.md` y `etl.md` para las reglas y el pipeline.
6. `api_contratos.md`, `ml.md`, `genai.md` y `alertas.md` para los servicios.
7. `manual.md` para instalarlo y operarlo.
8. `plan_pruebas.md` y `evidencias/` para comprobar que funciona.
9. `demo.md` para presentarlo.

## Evidencias

| Archivo | Generado por |
|---|---|
| `evidencias/T04_T07_verificacion.txt` | `database/99_verify.sql` |
| `evidencias/T06_calidad_reconciliacion.md` | `python -m app quality-report` |
| `evidencias/T09_api_kpis.md` | `python tests/smoke_core_api.py` + capturas de la API |
| `evidencias/T10_dashboard.md` | `python tests/test_dashboard_app.py` (AppTest) |
| `evidencias/T11_ml.md` | `python -m app train` + `python tests/test_ml_model.py` |
| `evidencias/T12_genai.md` | `python -m app test` + `POST /tests/run` |
| `evidencias/T13_alerting.md` | `python tests/test_alerting_rules.py` + `python tests/smoke_alerting.py` |

Las evidencias se regeneran; no se editan a mano.
