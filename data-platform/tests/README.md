# tests

Pruebas automatizadas y evidencias (T14).

## Estado

| Suite | Estado | Tarea |
|---|---|---|
| Prueba de idempotencia del ETL | implementada (CLI) | T05 |
| Reporte de calidad y reconciliacion | implementado (CLI) | T06, T08 |
| Prueba de humo de core-api | implementada | T09 |
| Prueba de humo y render del dashboard | implementada | T10 |
| Pruebas del modelo ML (serie sintetica) | implementada | T11 |
| Pruebas de API formales (pytest) | no requerida (scripts de humo) | T09 |
| Pruebas de GenAI (10 casos) | implementada | T12 |
| Pruebas de alertas y monitoreo | implementada | T13 |
| Pruebas de reglas de calidad y duplicados | implementada | T06, T14 |
| Pruebas end-to-end | implementada | T14 |
| Restriccion de acceso HTTP y confianza TLS | implementada | Seguridad |
| Correspondencia del catalogo GenAI y manejadores | implementada | T12 |
| Cliente HTTP del chat de ventas | implementada | T10, T12 |
| Cliente local de Ollama | implementada | T10, T12 |

## Pruebas disponibles hoy

```powershell
cd services/etl
python -m app idempotency-check     # reejecuta y compara conteos
python -m app quality-report        # calidad + reconciliacion
sqlcmd -S localhost -E -C -i ../../database/99_verify.sql

# Con core-api corriendo en el puerto 8000
python tests/smoke_core_api.py
python tests/smoke_dashboard.py
python tests/test_dashboard_app.py
python tests/test_ml_model.py

# Con core-api corriendo, las 10 pruebas del asistente
cd services/genai
python -m app test
cd ../..

# Con core-api, ml y alerting corriendo
python tests/test_alerting_rules.py
python tests/smoke_alerting.py

# Reglas de calidad y duplicados (sin servicios)
python tests/test_quality_rules.py
python tests/test_endpoint_access.py
python tests/test_tls_config.py
python tests/test_genai_catalog.py
python tests/test_dashboard_genai_client.py
python tests/test_dashboard_ollama_client.py

# Con los 6 servicios corriendo (incluye dashboard en 8501)
python tests/e2e_smoke.py
```

## Plan y resultados (T14)

El plan completo, con objetivo, precondicion, pasos, esperado y obtenido, esta en
[`documentation/plan_pruebas.md`](../documentation/plan_pruebas.md). Las salidas
crudas estan en [`documentation/evidencias/T14_pruebas.md`](../documentation/evidencias/T14_pruebas.md).

Cobertura de la rubrica: carga inicial, incremental, idempotencia, nulos y
duplicados, integridad, recuperacion, reconciliacion, dashboard, ML, GenAI,
alertas y end-to-end.
