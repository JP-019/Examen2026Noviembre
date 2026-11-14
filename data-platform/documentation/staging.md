# Staging: zonas, auditoria y cuarentena

- **Tarea:** T04
- **Script:** `database/00_schemas.sql`, `database/01_staging.sql`

---

## 1. Zonas

| Zona | Esquema | Prefijo | Regla de oro |
|---|---|---|---|
| LANDING / RAW | `raw` | `raw.<Entidad>` | Copia fiel de la fuente. **Solo INSERT**. Nunca se actualiza ni borra |
| CLEAN / VALIDATED | `clean` | `clean.<Entidad>` | Tipado, limpieza, estandarizacion y validacion. PK por clave de negocio |
| READY / INTEGRATION | `ready` | `ready.Ventas` | Datos integrados, una fila por linea de factura, listos para el DW |

Cada tabla de `clean` y `ready` conserva:

- La **clave de negocio** de la fuente (`idFactura`, `Id_Factura_Detalle`, etc.).
- `_execution_id`: vinculo con `audit.etl_execution`.
- `_loaded_at`: momento de carga UTC.
- En `ready`, ademas, el detalle de jerarquia de producto y local ya resuelto.

### Mapeo de nombres

La columna `n°Factura` de la fuente se renombra a `NumeroFactura` en `raw` para
evitar identificadores no ASCII. **El valor no se altera**; solo cambia el nombre.
El mapeo queda documentado en el diccionario de datos (T02).

---

## 2. Auditoria

### `audit.etl_execution`

Una fila por **objeto procesado** en una corrida.

| Campo | Tipo | Descripcion |
|---|---|---|
| `execution_id` | bigint identity | Identificador de la corrida del objeto |
| `pipeline_name` | varchar(100) | Nombre del pipeline (`sales_full`, `sales_incremental`) |
| `start_time` | datetime2(3) | Inicio |
| `end_time` | datetime2(3) | Fin |
| `source_object` | varchar(200) | Objeto origen |
| `target_object` | varchar(200) | Objeto destino |
| `rows_read` | int | Filas leidas |
| `rows_inserted` | int | Filas insertadas |
| `rows_updated` | int | Filas actualizadas |
| `rows_rejected` | int | Filas enviadas a cuarentena |
| `status` | varchar(20) | `RUNNING` / `SUCCESS` / `FAILED` / `PARTIAL` |
| `error_detail` | nvarchar(max) | Detalle del error |
| `watermark_start` | datetime2(3) | Watermark al iniciar |
| `watermark_end` | datetime2(3) | Watermark al finalizar |

### `audit.etl_watermark`

Una fila por pipeline + objeto. El watermark se actualiza **solo** cuando la
ejecucion termina en `SUCCESS`. Si falla, se conserva el valor anterior y la
siguiente corrida reprocesa la misma ventana (idempotencia).

### `audit.row_lineage`

Linaje fino para los campos clave: `execution_id`, `source_object`, `target_object`,
`business_key`, `operation` (`INSERT`/`UPDATE`), `load_id`.

---

## 3. Cuarentena

`quarantine.rejected_row` guarda el registro completo (JSON) que no cumplio una
regla, para reprocesar sin volver a la fuente.

| Campo | Descripcion |
|---|---|
| `rejected_id` | PK identity |
| `execution_id` | Corrida que lo rechazo |
| `source_object` | Tabla de origen |
| `rule_code` | Codigo de regla (ej. `DQ-005`) |
| `rule_detail` | Mensaje legible |
| `business_key` | Clave natural del registro |
| `payload` | Fila original serializada en JSON |
| `rejected_at` | Fecha y hora |
| `status` | `PENDIENTE` / `REPROCESADO` / `DESCARTADO` |
| `resolved_at` | Fecha de resolucion |

Ningun registro se descarta en silencio: o entra a `clean/ready`, o queda en
cuarentena con su regla.

---

## 4. Ciclo de vida

1. ETL abre una fila `RUNNING` en `audit.etl_execution`.
2. Extrae a `raw` (append-only).
3. Tipa y valida hacia `clean`; cada fallo escribe en `quarantine`.
4. Integra en `ready`.
5. Actualiza conteos y cierra en `SUCCESS` / `FAILED`.
6. Si `SUCCESS`, actualiza `audit.etl_watermark`.

### Retencion (propuesta)

| Zona | Retencion |
|---|---|
| `raw` | 90 dias |
| `clean` / `ready` | vigente + historico de cargas |
| `quarantine` | hasta resolucion + 30 dias |
| `audit` | permanente (es evidencia) |

---

## 5. Reglas de calidad aplicadas en `clean`

El catalogo completo (DQ-001 a DQ-015) esta en `documentation/calidad_datos.md` y en
`services/etl/app/quality.py`. Resumen:

| Codigo | Regla | Accion |
|---|---|---|
| `DQ-001` | `IdFactura` nulo o invalido | Cuarentena |
| `DQ-002` | `IdFacturaDetalle` nulo o invalido | Cuarentena |
| `DQ-003` | `Cantidad > 0` | Cuarentena |
| `DQ-004` | `PrecioUnitario >= 0` | Cuarentena |
| `DQ-005` | `IdFactura` de detalle existe en cabecera | Cuarentena (huerfano) |
| `DQ-006` | `IdProducto` existe en producto | Cuarentena (huerfano) |
| `DQ-007` | `fecha` dentro de rango razonable (2000-01-01 a hoy+1) | Cuarentena |
| `DQ-008` | Precio fuera de rango razonable | Cuarentena (outlier) |
| `DQ-009` | `NumeroFactura > 0` | Cuarentena |
| `DQ-010` | Fecha futura | Cuarentena |
| `DQ-011` | Nombre de producto no vacio | Cuarentena |
| `DQ-012` | Clave de negocio no nula en dimension | Cuarentena |
| `DQ-013` | Duplicado en el lote | Cuarentena + supervivencia del ultimo |
| `DQ-014` | Jerarquia de producto incompleta | Se completa con `Desconocido` |
| `DQ-015` | `VentaAsociada` no nula | Cuarentena |

---

## 6. Criterios de aceptacion (T04)

- [x] Existen las 3 zonas claramente separadas por esquema.
- [x] La zona raw conserva el dato original sin modificaciones (append-only).
- [x] Tabla de auditoria con todos los campos minimos.
- [x] Tabla de cuarentena operativa y documentada.
- [x] Cada registro preparado conserva claves de negocio y linaje.
- [x] Poblado real de auditoria y cuarentena (evidencia en `evidencias/T06_calidad_reconciliacion.md`).
