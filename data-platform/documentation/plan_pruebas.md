# Plan y resultados de pruebas

- **Tarea:** T14
- **Alcance:** las 12 pruebas de la rubrica, de la carga inicial al end-to-end
- **Ambiente:** SQL Server local (`localhost`), Python 3.12, Windows
- **Fecha de ejecucion:** 2026-11-13/14
- **Evidencia cruda:** `documentation/evidencias/T14_pruebas.md` y las evidencias
  por tarea en `documentation/evidencias/`

---

## 1. Resumen

| # | Prueba | Resultado | Evidencia principal |
|---|---|---|---|
| 1 | Carga inicial | OK | `T06_calidad_reconciliacion.md` |
| 2 | Carga incremental | OK | `T06_calidad_reconciliacion.md` (watermarks) |
| 3 | Idempotencia | OK | `T14_pruebas.md` §3 |
| 4 | Nulos y duplicados | OK | `T14_pruebas.md` §4 + `tests/test_quality_rules.py` |
| 5 | Integridad referencial | OK | `99_verify.sql` + `T14_pruebas.md` §5 |
| 6 | Recuperacion ante falla | OK | `T14_pruebas.md` §6 |
| 7 | Reconciliacion entre capas | OK | `T06_calidad_reconciliacion.md` §3 |
| 8 | Dashboard | OK | `T10_dashboard.md` + `tests/test_dashboard_app.py` |
| 9 | Modelo ML | OK | `T11_ml.md` + `tests/test_ml_model.py` |
| 10 | GenAI | OK | `T12_genai.md` + `python -m app test` |
| 11 | Alertas | OK | `T13_alerting.md` + `tests/smoke_alerting.py` |
| 12 | End-to-end | OK | `tests/e2e_smoke.py` + `T14_pruebas.md` §12 |

Regla de honestidad aplicada en todas: si un dato no existe, la prueba lo informa
como limitacion; no se completa con valores inventados.

---

## 2. Prueba 1 - Carga inicial

**Objetivo:** extraer las 10 tablas de ventas y dejarlas integradas en el DW.

**Precondicion:** base `Venta` disponible, `DataPlatform` creada con los scripts
`00` a `03`, `.env` configurado.

**Pasos:**

```powershell
cd services/etl
python -m app full
python -m app status
sqlcmd -S localhost -E -C -f 65001 -i ../../database/99_verify.sql
```

**Esperado:** 10 tablas extraidas, 5 lineas en `ready.Ventas` y `dw.FactVentas`,
importe S/ 696.40, 0 rechazos y 0 huerfanos.

**Obtenido:**

```
[1/4] Extrayendo (full) ... tablas extraidas: 10
[2/4] Limpiando y validando (clean) ...
[3/4] Integrando (ready) ...
[4/4] Cargando Data Warehouse ...
  filas rechazadas : 0
  ready.Ventas     : 5
  dw.FactVentas    : 5
  huerfanos en hecho: 0
```

`99_verify.sql`: 5 lineas, S/ 696.40, 4 dimensiones con miembro desconocido,
`DimTiempo` 2000-01-01 a 2035-12-31.

**Nota:** la primera carga historica inserto las filas; en la reejecucion sobre
una base ya cargada el mismo comando informa `actualizadas=5` y no duplica. Eso
es correcto y se prueba en la prueba 3.

**Evidencia:** `documentation/evidencias/T06_calidad_reconciliacion.md` §1, §3 y §4.

---

## 3. Prueba 2 - Carga incremental

**Objetivo:** traer solo la ventana nueva usando el watermark, sin perder bordes.

**Precondicion:** carga inicial hecha; watermark en `audit.etl_watermark`.

**Pasos:**

```powershell
cd services/etl
python -m app incremental
python -m app status
```

**Esperado:** extraer solo las facturas y lineas desde el watermark menos el
solapamiento (`ETL_OVERLAP_DAYS=1`), y actualizar el DW sin duplicar.

**Obtenido:**

```
sales_extract_incremental  Venta.dbo.Factura          1 fila
sales_extract_incremental  Venta.dbo.Factura_Detalle  1 fila
sales_extract_incremental  dimensiones                4/5/2 filas (completas)
ready.Ventas     : insertadas=0 actualizadas=5
dw.FactVentas    : insertadas=0 actualizadas=5
watermark Factura / Factura_Detalle = 2008-08-15 00:00:00
```

**Evidencia:** `T06_calidad_reconciliacion.md` §1 (pipeline
`sales_extract_incremental`) y §5 (watermarks).

---

## 4. Prueba 3 - Idempotencia

**Objetivo:** demostrar que reejecutar el mismo lote no altera las capas estables.

**Precondicion:** base cargada.

**Pasos:**

```powershell
cd services/etl
python -m app idempotency-check
```

**Esperado:** los conteos de `clean`, `ready` y `dw` no cambian; solo crece `raw`
(append-only por diseno).

**Obtenido:**

```
tabla (capas estables)            antes        1ra        2da   estado
clean.Factura                         5          5          5       OK
clean.FacturaDetalle                  5          5          5       OK
clean.Producto                        4          4          4       OK
dw.FactVentas                         5          5          5       OK
importe_dw_centavos               69640      69640      69640       OK
ready.Ventas                          5          5          5       OK

Capas append-only (crecimiento esperado):
  raw.Factura                      27 ->       37
  raw.FacturaDetalle               27 ->       37

RESULTADO: IDEMPOTENTE
```

**Evidencia:** `documentation/evidencias/T14_pruebas.md` §3.

---

## 5. Prueba 4 - Nulos y duplicados

**Objetivo:** verificar que no hay claves ni medidas nulas, ni filas duplicadas,
y que el ETL sabe descartar duplicados cuando aparecen.

**Precondicion:** DW cargado.

**Pasos:**

```powershell
# Consultas de control
sqlcmd -S localhost -E -C -d DataPlatform -W -s "|" -Q @"
SELECT COUNT(*) filas,
       SUM(CASE WHEN IdFacturaDetalle IS NULL THEN 1 ELSE 0 END) nulos_pk,
       SUM(CASE WHEN Cantidad IS NULL OR PrecioUnitario IS NULL OR ImporteLinea IS NULL THEN 1 ELSE 0 END) nulos_medidas,
       COUNT(*) - COUNT(DISTINCT IdFacturaDetalle) duplicados_pk
  FROM ready.Ventas;
"@

# Prueba unitaria del catalogo y de la supervivencia
python tests/test_quality_rules.py
```

**Esperado:** 0 nulos, 0 duplicados; el catalogo detecta los 15 codigos DQ y ante
un duplicado conserva la ultima aparicion y reporta la anterior.

**Obtenido:**

```
ready: filas=5  nulos_pk=0  nulos_medidas=0  duplicados_pk=0
dw:    filas=5  claves_desconocidas=0  nulos_medidas=0  duplicados_pk=0
cuarentena: total=0
```

`tests/test_quality_rules.py`:

```
DQ-011/012 (dimensiones), DQ-001/007/009/010/015 (cabecera),
DQ-003/004/005/006/008 (linea), DQ-013 (duplicado)
quedan 2 claves unicas, 1 duplicado, sobrevive la ultima aparicion
RESULTADO: OK
```

**Evidencia:** `documentation/evidencias/T14_pruebas.md` §4 y
`tests/test_quality_rules.py`.

---

## 6. Prueba 5 - Integridad referencial

**Objetivo:** garantizar que todo hecho apunta a dimensiones existentes y que las
medidas son coherentes.

**Precondicion:** DW cargado.

**Pasos:**

```powershell
sqlcmd -S localhost -E -C -f 65001 -i database/99_verify.sql
```

Mas la consulta de claves desconocidas y coherencia de importe:

```sql
SELECT COUNT(*) huerfanos FROM dw.FactVentas f
 WHERE NOT EXISTS (SELECT 1 FROM dw.DimTiempo t WHERE t.TiempoKey = f.TiempoKey)
    OR NOT EXISTS (SELECT 1 FROM dw.DimProducto p WHERE p.ProductoKey = f.ProductoKey)
    OR NOT EXISTS (SELECT 1 FROM dw.DimLocal l WHERE l.LocalKey = f.LocalKey)
    OR NOT EXISTS (SELECT 1 FROM dw.DimVersion v WHERE v.VersionKey = f.VersionKey);
```

**Esperado:** 0 huerfanos; claves `0` disponibles en las 4 dimensiones; ningun
importe incoherente.

**Obtenido:**

```
Miembros desconocidos: DimTiempo=1, DimProducto=1, DimLocal=1, DimVersion=1
Huerfanos en el hecho: 0
dw: claves_desconocidas=0, importe_incoherente=0
```

**Evidencia:** `database/99_verify.sql` y `T14_pruebas.md` §5.

---

## 7. Prueba 6 - Recuperacion ante falla

**Objetivo:** comprobar que una corrida fallida no avanza el watermark y que la
siguiente corrida recupera el estado.

**Precondicion:** base cargada, watermark en `2008-08-15`.

**Pasos:**

```powershell
cd services/etl
$env:SOURCE_DATABASE="VentaNoExiste"
python -m app incremental        # debe fallar
Remove-Item Env:\SOURCE_DATABASE
python -m app incremental        # debe recuperar
```

**Esperado:** la corrida fallida termina con error, no escribe en `raw` y deja el
watermark intacto; la corrida siguiente cierra en `SUCCESS` con los mismos
conteos.

**Obtenido:**

```
pyodbc.InterfaceError: Cannot open database "VentaNoExiste" ... (exit 1)

Watermark antes:  Factura 2008-08-15T00:00:00 | Factura_Detalle 2008-08-15T00:00:00
Watermark despues: Factura 2008-08-15T00:00:00 | Factura_Detalle 2008-08-15T00:00:00

Recuperacion: incremental -> ready 5 actualizadas, dw 5 actualizadas,
             0 rechazos, 0 huerfanos, exit 0
```

**Evidencia:** `T14_pruebas.md` §6.

---

## 8. Prueba 7 - Reconciliacion entre capas

**Objetivo:** confirmar que fuente, `clean`, `ready` y `dw` coinciden en filas e
importe.

**Precondicion:** ETL ejecutado.

**Pasos:**

```powershell
cd services/etl
python -m app quality-report
```

**Esperado:** 5 filas y S/ 696.40 en las cuatro capas.

**Obtenido:**

```
| capa                              | filas | importe |
| Fuente Venta.dbo.Factura_Detalle  |     5 |  696.40 |
| clean.FacturaDetalle              |     5 |  696.40 |
| ready.Ventas                      |     5 |  696.40 |
| dw.FactVentas                     |     5 |  696.40 |
```

> La cabecera `Factura.VentaAsociada` suma S/ 455.00 y **no** se usa como medida:
> no cuadra con el detalle. La medida oficial es `Cantidad * PrecioUnitario`.

**Evidencia:** `documentation/evidencias/T06_calidad_reconciliacion.md` §3.

---

## 9. Prueba 8 - Dashboard

**Objetivo:** verificar que el tablero muestra los KPIs y se comporta bien ante
errores, consumiendo solo `core-api`.

**Precondicion:** `core-api` y dashboard arriba.

**Pasos:**

```powershell
python tests/smoke_dashboard.py
python tests/test_dashboard_app.py
```

**Esperado:** 6 KPIs, filtros con 4 locales y 2 secciones, 1 punto de tendencia,
detalle paginado y un estado de error visible si la API cae.

**Obtenido:**

```
health          : ok | filas=5 | etl=SUCCESS
filtros         : 4 locales, 2 secciones
kpis            : 6 tarjetas | ventas=696.4
tendencias      : 1 puntos | variacion=None
detalle         : total=5 | filas=3
periodo vacio   : ventas=0.0
RESULTADO: OK

AppTest: excepciones=0, mensajes error=0, tarjetas=11, tablas=1
API caida: 'No se pudo conectar con la API...' visible
RESULTADO: OK
```

**Evidencia:** `documentation/evidencias/T10_dashboard.md`.

---

## 10. Prueba 9 - Modelo ML

**Objetivo:** verificar el corte temporal, el baseline y la honestidad cuando no
hay datos suficientes.

**Precondicion:** `dw.vw_Ventas` disponible.

**Pasos:**

```powershell
python tests/test_ml_model.py
cd services/ml
python -m app train
python -m app status
```

**Esperado:** con 24 meses sinteticos entrena y evalua solo en prueba; con la
fuente real (1 mes) informa `insufficient_data` y no publica metricas.

**Obtenido:**

```
Caso 1 (24 meses sinteticos): trained, 18/6, MAE 38.9 vs baseline 480.0
Caso 2 (1 mes): insufficient_data, metricas null
RESULTADO: OK

Servicio real: status=insufficient_data, train=0, test=1, MAE=null
POST /predict -> 409 (no hay modelo entrenado)
```

**Evidencia:** `documentation/evidencias/T11_ml.md`.

---

## 11. Prueba 10 - GenAI

**Objetivo:** verificar que responde con datos, fuentes y rechazo explicito sin
inventar cifras.

**Precondicion:** `core-api` y `genai` arriba.

**Pasos:**

```powershell
cd services/genai
python -m app test
```

**Esperado:** 10/10 casos; 9 con datos y `grounded=true`, 1 fuera de alcance con
`grounded=false` y sin datos.

**Obtenido:**

```
T12-01 ventas_totales       OK
T12-02 facturas             OK
T12-03 ticket_promedio      OK
T12-04 top_productos        OK
T12-05 ventas_por_local     OK
T12-06 ventas_por_seccion   OK
T12-07 ventas_por_producto  OK
T12-08 tendencia            OK
T12-09 comparacion          OK
T12-10 no_data              OK
RESULTADO: 10/10 pruebas OK
```

**Evidencia:** `documentation/evidencias/T12_genai.md`.

---

## 12. Prueba 11 - Alertas

**Objetivo:** generar alertas, no duplicarlas y registrar la entrega.

**Precondicion:** `core-api`, `ml` y `alerting` arriba; `ALERT_DB_PATH` aislado
para la prueba.

**Pasos:**

```powershell
python tests/test_alerting_rules.py
python tests/smoke_alerting.py
```

**Esperado:** 6 reglas; con los datos reales se disparan 3; la segunda evaluacion
no crea nuevas; reconocimiento y alerta simulada funcionan.

**Obtenido:**

```
Reglas: 6 (3 negocio, 2 ML, 1 calidad)
Primera evaluacion: disparadas=3 nuevas=3 duplicadas=0
  VENTAS_BAJAS 696.4 < 1000
  TICKET_BAJO 174.1 < 200
  MODELO_SIN_ENTRENAR 1 < 8
Segunda evaluacion: nuevas=0 duplicadas=3
ACK -> acknowledged
Simulada -> simulated=1
/monitor.json y /monitor -> OK
RESULTADO: OK
```

**Evidencia:** `documentation/evidencias/T13_alerting.md`.

---

## 13. Prueba 12 - End-to-end

**Objetivo:** recorrer la plataforma completa con los 6 servicios levantados.

**Precondicion:** base cargada; `core-api`, `catalog`, `ml`, `genai`, `alerting` y
dashboard arriba; `ALERT_DB_PATH` aislado.

**Pasos:**

```powershell
python tests/e2e_smoke.py
```

**Esperado:** health, KPIs, catalogo, ML, GenAI, alertas, monitor y dashboard en
el mismo recorrido.

**Obtenido:**

```
core-api responde health                             OK  (filas=5, etl=SUCCESS)
KPIs devuelven ventas reales (696.40)                OK
catalogo declara 7/7 servicios                       OK
ML informa insufficient_data sin inventar metricas   OK
GenAI responde con fuentes y grounded                OK
primera evaluacion genera 3 alertas nuevas           OK
segunda evaluacion no duplica                        OK
monitor integra pipeline y alertas                   OK
dashboard responde health                            OK

RESULTADO: OK
```

**Evidencia:** `tests/e2e_smoke.py` y `T14_pruebas.md` §12.

---

## 14. Limitaciones declaradas

| Limitacion | Efecto en las pruebas |
|---|---|
| La fuente tiene 5 lineas y un solo mes | No se prueba volumen ni estacionalidad real |
| No hay Docker en el equipo | La via contenedor no se ejecuta |
| No hay navegador automatizado | El dashboard se verifica con `AppTest` y health, no con captura |
| El video no lo puede grabar el agente | La T15 entrega guion y checklist, no el archivo de video |

Ninguna limitacion se oculta: cada una tiene su evidencia y su plan alternativo.

## 15. Verificaciones de seguridad y estructura

Estas verificaciones complementan las 12 pruebas de la rubrica:

```powershell
python tests/test_endpoint_access.py
python tests/test_tls_config.py
python tests/test_genai_catalog.py
```

Resultado verificado:

- Los cuatro servicios sensibles permiten clientes IPv4/IPv6 locales y rechazan
  clientes remotos con HTTP 403.
- La confianza automatica de certificados solo se activa para SQL Server local;
  para un servidor remoto se valida el certificado.
- Todas las intenciones publicadas por GenAI tienen un manejador ejecutable.
