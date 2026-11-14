# Calidad de datos y transformaciones (T06)

- **Implementacion:** `services/etl/app/quality.py`
- **Evidencia:** `documentation/evidencias/T06_calidad_reconciliacion.md`

---

## 1. Catalogo de reglas

| Codigo | Regla | Tabla | Accion |
|---|---|---|---|
| DQ-001 | `IdFactura` nulo o invalido | Factura | Cuarentena |
| DQ-002 | `IdFacturaDetalle` nulo o invalido | Factura_Detalle | Cuarentena |
| DQ-003 | `Cantidad <= 0` | Factura_Detalle | Cuarentena |
| DQ-004 | `PrecioUnitario < 0` | Factura_Detalle | Cuarentena |
| DQ-005 | `IdFactura` no existe en cabecera | Factura_Detalle | Cuarentena (huerfano) |
| DQ-006 | `IdProducto` no existe | Factura_Detalle | Cuarentena (huerfano) |
| DQ-007 | Fecha nula o fuera de `[2000-01-01, hoy+1]` | Factura | Cuarentena |
| DQ-008 | `PrecioUnitario > 1.000.000` | Factura_Detalle | Cuarentena (outlier) |
| DQ-009 | `NumeroFactura <= 0` | Factura | Cuarentena |
| DQ-010 | Fecha futura | Factura | Cuarentena |
| DQ-011 | `NombreProducto` vacio | Producto | Cuarentena |
| DQ-012 | Clave de negocio nula en dimension | Dimensiones | Cuarentena |
| DQ-013 | Duplicado en el lote | Todas | Cuarentena del duplicado |
| DQ-014 | Jerarquia de producto incompleta | Producto | Se completa con `Desconocido` |
| DQ-015 | `VentaAsociada` nula | Factura | Cuarentena |

El codigo y la documentacion usan el mismo catalogo (`quality.RULES`): si se agrega
una regla, se agrega en ambos lugares.

---

## 2. Politica de nulos

No se reemplazan todos los nulos por cero. Se clasifican:

| Tipo de nulo | Ejemplo | Tratamiento |
|---|---|---|
| No aplica | `IdLocal` en una venta sin local | Se mapea al miembro desconocido del DW |
| Desconocido | Nombre de jerarquia ausente | Se completa con `Desconocido` y se marca |
| Pendiente | Registro en cuarentena | Se reprocesa al corregir la fuente |
| Error | `IdFactura` nulo | Cuarentena, nunca se carga |
| Medida | `Cantidad` nula | Cuarentena |

`Cantidad` y `PrecioUnitario` **nunca** se imputan con cero: distorsionarian los KPIs.

---

## 3. Duplicados

- **Clave de duplicidad:** la clave natural de cada tabla (`IdFactura`,
  `IdFacturaDetalle`, `IdProducto`, etc.).
- **Regla de supervivencia:** se conserva la **ultima** aparicion dentro del lote
  (la extraccion es ordenada por la consulta de origen) y el duplicado se registra
  en cuarentena con `DQ-013`.
- Nunca se elimina un duplicado sin dejar registro.

---

## 4. Estandarizacion y tipos

| Transformacion | Implementacion |
|---|---|
| Espacios y vacios | `strip()`; texto vacio pasa a `NULL` |
| Fechas | Conversion explicita a `date` |
| Decimales | `Decimal` con cuantizacion a 2 decimales |
| Identificadores | Enteros, sin cast implícito |
| Nombres de columna | `nºFactura` -> `NumeroFactura` (solo metadatos) |
| Zona horaria | Fechas de negocio sin hora; auditoria en UTC |

No se trunca precision: `decimal(8,2)` se promueve a `decimal(18,2)`.

---

## 5. Integridad referencial

| Caso | Tratamiento |
|---|---|
| Detalle sin factura | Cuarentena `DQ-005` |
| Detalle sin producto | Cuarentena `DQ-006` |
| Producto sin jerarquia | Se completa `Desconocido` (`DQ-014`) y se revisa |
| Local o version ausente | Miembro desconocido (clave `0`) en el DW |

El DW tiene claves foraneas fisicas: un hecho huerfano es imposible de insertar.

---

## 6. Outliers

- Regla `DQ-008` marca precios fuera de rango razonable.
- Un outlier **no se elimina automaticamente**: se investiga (puede ser una venta
  real). Solo se rechaza si viola el rango declarado.
- Los outliers validos se cargan y quedan visibles para el analisis.

---

## 7. Reglas de negocio

| Regla | Implementacion |
|---|---|
| Cantidad positiva | `DQ-003` + `CHECK` en clean, ready y DW |
| Precio no negativo | `DQ-004` + `CHECK` |
| Importe coherente | Columna calculada persistida en `clean` y `CHECK` en el DW |
| Fecha dentro de rango | `DQ-007` / `DQ-010` |

---

## 8. Integracion sin multiplicar medidas

- El grano de `ready.Ventas` es la **linea de factura**.
- Los joins a jerarquia son 1:1 (producto -> subfamilia -> ... -> seccion), no 1:N.
- No se une la cabecera de factura con el detalle sin agregar antes.
- La reconciliacion (`ready` vs `dw.FactVentas`) verifica que no se dupliquen importes.

---

## 9. Linaje

| Nivel | Donde se registra |
|---|---|
| Corrida | `audit.etl_execution` (conteos, estado, watermark) |
| Registro | `audit.row_lineage` (clave de negocio, origen, destino, operacion) |
| Rechazo | `quarantine.rejected_row` (regla, detalle y payload JSON) |
| Columna | Documentada en `documentation/modelo_dimensional.md` y en `specs.py` |

---

## 10. Reporte antes / despues

`python -m app quality-report` genera
`documentation/evidencias/T06_calidad_reconciliacion.md` con:

1. Ultima ejecucion por objeto (leidas, insertadas, actualizadas, rechazadas).
2. Rechazos por regla.
3. Reconciliacion fuente -> clean -> ready -> DW.
4. Volumen por capa.
5. Watermarks.

### Resultado actual (fuente de muestra)

| Capa | Filas | Importe |
|---|---|---|
| Fuente `Venta.dbo.Factura_Detalle` | 5 | 696.40 |
| `clean.FacturaDetalle` | 5 | 696.40 |
| `ready.Ventas` | 5 | 696.40 |
| `dw.FactVentas` | 5 | 696.40 |

Cero rechazos en el lote actual y cero diferencias entre capas.

---

## 11. Limitaciones conocidas

- El volumen de la fuente es muy bajo (5 facturas): las metricas de calidad son
  correctas pero poco representativas.
- `Factura.VentaAsociada` no coincide con la suma de sus lineas (hallazgo de
  perfilado); se conserva como dato de cabecera y **no** se usa como medida.
- No hay deteccion de eliminaciones en la fuente: se documenta y se controla por
  reconciliacion de conteos.
