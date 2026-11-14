# database

Scripts SQL de la plataforma. Se ejecutan en orden y son idempotentes.

| Archivo | Que hace | Tarea |
|---|---|---|
| `00_schemas.sql` | Crea `DataPlatform` y los esquemas `raw`, `clean`, `ready`, `dw`, `audit`, `quarantine` | T01, T04 |
| `01_staging.sql` | Crea tablas de staging, auditoria, watermark, linaje y cuarentena | T04 |
| `02_dw.sql` | Crea dimensiones, `FactVentas`, miembro desconocido y `vw_Ventas` | T07 |
| `03_ml.sql` | Crea `audit.ml_experiment` (registro de entrenamientos) | T11 |
| `99_verify.sql` | Evidencia: objetos, columnas, miembros 0, huerfanos y consulta de validacion | T04, T07 |
| `98_reset.sql` | Borra `DataPlatform` para reiniciar el ambiente (solo desarrollo) | T01 |

## Orden de ejecucion

```powershell
sqlcmd -S localhost -E -C -f 65001 -i database/00_schemas.sql
sqlcmd -S localhost -E -C -f 65001 -i database/01_staging.sql
sqlcmd -S localhost -E -C -f 65001 -i database/02_dw.sql
sqlcmd -S localhost -E -C -f 65001 -i database/03_ml.sql
sqlcmd -S localhost -E -C -f 65001 -i database/99_verify.sql
```

## Convenciones

- `-C` acepta el certificado autofirmado local.
- `-f 65001` lee los archivos como UTF-8.
- Toda tabla de `clean`/`ready` lleva `_execution_id` y `_loaded_at`.
- Ningun script contiene credenciales.

## Modelo de esquemas

| Esquema | Rol | Escritura |
|---|---|---|
| `raw` | Copia fiel, append-only | ETL |
| `clean` | Tipado y validado | ETL |
| `ready` | Integrado, listo para DW | ETL |
| `dw` | Modelo estrella publicado | ETL |
| `audit` | Ejecuciones, watermarks y linaje | ETL |
| `quarantine` | Registros rechazados | ETL |
