# Reporte de calidad y reconciliacion

Generado: 2026-11-13 21:44:36

Evidencia automatica de T05 (extraccion), T06 (calidad) y T08 (reconciliacion).
Se regenera con `python -m app quality-report`.

## 1. Ultima ejecucion por objeto

| pipeline | origen | destino | estado | leidas | insertadas | actualizadas | rechazadas |
|---|---|---|---|---|---|---|---|
| sales_clean | raw.[Version] | clean.[Version] | SUCCESS | 2 | 0 | 2 | 0 |
| sales_clean | raw.Categoria | clean.Categoria | SUCCESS | 5 | 0 | 5 | 0 |
| sales_clean | raw.Factura | clean.Factura | SUCCESS | 5 | 0 | 5 | 0 |
| sales_clean | raw.FacturaDetalle | clean.FacturaDetalle | SUCCESS | 5 | 0 | 5 | 0 |
| sales_clean | raw.Familia | clean.Familia | SUCCESS | 4 | 0 | 4 | 0 |
| sales_clean | raw.Local | clean.Local | SUCCESS | 4 | 0 | 4 | 0 |
| sales_clean | raw.Producto | clean.Producto | SUCCESS | 4 | 0 | 4 | 0 |
| sales_clean | raw.Rubro | clean.Rubro | SUCCESS | 4 | 0 | 4 | 0 |
| sales_clean | raw.Seccion | clean.Seccion | SUCCESS | 4 | 0 | 4 | 0 |
| sales_clean | raw.SubFamilia | clean.SubFamilia | SUCCESS | 4 | 0 | 4 | 0 |
| sales_dw_dim | clean.[Version] | dw.DimVersion | SUCCESS | 2 | 0 | 2 | 0 |
| sales_dw_dim | clean.Local | dw.DimLocal | SUCCESS | 4 | 0 | 4 | 0 |
| sales_dw_dim | clean.Producto | dw.DimProducto | SUCCESS | 4 | 0 | 4 | 0 |
| sales_dw_fact | ready.Ventas | dw.FactVentas | SUCCESS | 5 | 0 | 5 | 0 |
| sales_extract_full | Venta.dbo.Categoria | raw.Categoria | SUCCESS | 5 | 5 | 0 | 0 |
| sales_extract_full | Venta.dbo.Factura | raw.Factura | SUCCESS | 5 | 5 | 0 | 0 |
| sales_extract_full | Venta.dbo.Factura_Detalle | raw.FacturaDetalle | SUCCESS | 5 | 5 | 0 | 0 |
| sales_extract_full | Venta.dbo.Familia | raw.Familia | SUCCESS | 4 | 4 | 0 | 0 |
| sales_extract_full | Venta.dbo.Local | raw.Local | SUCCESS | 4 | 4 | 0 | 0 |
| sales_extract_full | Venta.dbo.Producto | raw.Producto | SUCCESS | 4 | 4 | 0 | 0 |
| sales_extract_full | Venta.dbo.Rubro | raw.Rubro | SUCCESS | 4 | 4 | 0 | 0 |
| sales_extract_full | Venta.dbo.Seccion | raw.Seccion | SUCCESS | 4 | 4 | 0 | 0 |
| sales_extract_full | Venta.dbo.SubFamilia | raw.SubFamilia | SUCCESS | 4 | 4 | 0 | 0 |
| sales_extract_full | Venta.dbo.Version | raw.[Version] | SUCCESS | 2 | 2 | 0 | 0 |
| sales_extract_incremental | Venta.dbo.Categoria | raw.Categoria | SUCCESS | 5 | 5 | 0 | 0 |
| sales_extract_incremental | Venta.dbo.Factura | raw.Factura | SUCCESS | 1 | 1 | 0 | 0 |
| sales_extract_incremental | Venta.dbo.Factura_Detalle | raw.FacturaDetalle | SUCCESS | 1 | 1 | 0 | 0 |
| sales_extract_incremental | Venta.dbo.Familia | raw.Familia | SUCCESS | 4 | 4 | 0 | 0 |
| sales_extract_incremental | Venta.dbo.Local | raw.Local | SUCCESS | 4 | 4 | 0 | 0 |
| sales_extract_incremental | Venta.dbo.Producto | raw.Producto | SUCCESS | 4 | 4 | 0 | 0 |
| sales_extract_incremental | Venta.dbo.Rubro | raw.Rubro | SUCCESS | 4 | 4 | 0 | 0 |
| sales_extract_incremental | Venta.dbo.Seccion | raw.Seccion | SUCCESS | 4 | 4 | 0 | 0 |
| sales_extract_incremental | Venta.dbo.SubFamilia | raw.SubFamilia | SUCCESS | 4 | 4 | 0 | 0 |
| sales_extract_incremental | Venta.dbo.Version | raw.[Version] | SUCCESS | 2 | 2 | 0 | 0 |
| sales_ready | clean.FacturaDetalle | ready.Ventas | SUCCESS | 5 | 0 | 5 | 0 |

## 2. Rechazos por regla (cuarentena)

Sin rechazos registrados.

## 3. Reconciliacion entre capas

| capa | filas | importe |
|---|---|---|
| Fuente Venta.dbo.Factura_Detalle | 5 | 696.40 |
| clean.FacturaDetalle | 5 | 696.40 |
| ready.Ventas | 5 | 696.40 |
| dw.FactVentas | 5 | 696.40 |

La diferencia de filas entre la fuente y `clean` se explica por registros en
cuarentena. La diferencia entre `ready` y `dw.FactVentas` debe ser cero.

## 4. Volumen por capa

| capa | filas |
|---|---|
| raw | 460 |
| clean | 41 |
| ready | 5 |
| dw.FactVentas | 5 |
| dw.DimProducto | 5 |
| dw.DimLocal | 5 |
| dw.DimVersion | 3 |

## 5. Watermarks

| pipeline | objeto | columna | valor | actualizado |
|---|---|---|---|---|
| sales_incremental | Venta.dbo.Factura | Fecha | 2008-08-15 00:00:00 | 2026-11-14 03:44:36.182000 |
| sales_incremental | Venta.dbo.Factura_Detalle | Fecha | 2008-08-15 00:00:00 | 2026-11-14 03:44:36.186000 |
