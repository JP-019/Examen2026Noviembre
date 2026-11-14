# Servicio ETL (T05 / T06)

Microservicio de ingesta batch. No expone HTTP: se ejecuta por CLI o por cron/scheduler.
Escribe en la base `DataPlatform` (esquemas `raw`, `clean`, `ready`, `dw`, `audit`, `quarantine`).

## Responsabilidad

| Etapa | Entrada | Salida | Auditoria |
|---|---|---|---|
| Extraccion | `Venta.dbo.*` | `raw.*` | `sales_extract_full` / `sales_extract_incremental` |
| Limpieza | `raw.*` | `clean.*` + cuarentena | `sales_clean` |
| Integracion | `clean.*` | `ready.Ventas` | `sales_ready` |
| Dimensiones | `clean.*` | `dw.Dim*` | `sales_dw_dim` |
| Hechos | `ready.Ventas` | `dw.FactVentas` | `sales_dw_fact` |

## Indice de funciones

| Archivo | Funcion | Que hace |
|---|---|---|
| `app/config.py` | `DbConfig.connection_string` | Arma la cadena ODBC sin secretos en codigo |
| `app/db.py` | `connect` | Abre conexion pyodbc |
| `app/db.py` | `fetch_all` / `fetch_one` / `fetch_scalar` | Consultas parametrizadas |
| `app/db.py` | `executemany` | Insercion masiva en raw |
| `app/db.py` | `table_counts` | Conteo por metadatos (sin escanear) |
| `app/audit.py` | `run` | Context manager: abre y cierra `audit.etl_execution` |
| `app/audit.py` | `get_watermark` / `set_watermark` | Watermark persistido, solo en exito |
| `app/audit.py` | `add_lineage` | Linaje por clave de negocio |
| `app/specs.py` | `EXTRACT_SPECS` | Definicion declarativa de las 10 tablas |
| `app/quality.py` | `RULES` | Catalogo DQ-001 a DQ-015 |
| `app/quality.py` | `validate` | Aplica reglas por tipo de tabla |
| `app/quality.py` | `to_clean_row` | Conversiones explicitas |
| `app/quality.py` | `reject` | Escribe en cuarentena con payload JSON |
| `app/staging.py` | `extract` | Carga full o incremental a raw |
| `app/staging.py` | `clean` | Deduplica, valida y hace UPSERT a clean |
| `app/staging.py` | `build_ready` | MERGE a `ready.Ventas` |
| `app/dw.py` | `load` | MERGE de dimensiones (SCD1) y hechos |
| `app/dw.py` | `orphan_facts` | Verifica cero huerfanos |
| `app/report.py` | `build` | Reporte de calidad y reconciliacion |

## Ejecucion

Desde `services/etl`:

```powershell
python -m pip install -r requirements.txt
python -m app full
python -m app incremental
python -m app status
python -m app quality-report
python -m app idempotency-check
python -m app list-rules
```

## Variables de entorno

| Variable | Default | Uso |
|---|---|---|
| `SOURCE_SERVER` | `localhost` | Instancia de la fuente |
| `SOURCE_DATABASE` | `Venta` | Base transaccional |
| `DW_SERVER` | `localhost` | Instancia de la plataforma |
| `DW_DATABASE` | `DataPlatform` | Staging + DW |
| `DW_TRUSTED_CONNECTION` | `yes` | Autenticacion Windows |
| `ETL_OVERLAP_DAYS` | `1` | Ventana de solapamiento |

## Garantias

- **Idempotencia:** UPSERT/MERGE por clave de negocio; reejecutar no duplica.
- **Trazabilidad:** toda corrida deja fila en `audit.etl_execution` y linaje en `audit.row_lineage`.
- **Calidad:** ninguna fila se descarta en silencio; o entra, o queda en cuarentena con su regla.
- **Sin secretos:** credenciales solo por `.env` (no versionado).
