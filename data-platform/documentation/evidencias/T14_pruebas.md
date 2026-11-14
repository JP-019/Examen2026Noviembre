# Evidencia T14 - Plan de pruebas ejecutado

- **Tarea:** T14
- **Fecha:** 2026-11-13/14
- **Ambiente:** Windows, SQL Server 2025 local, Python 3.12.10
- **Base:** `DataPlatform` (fuente `Venta`, solo lectura)
- **Plan asociado:** `documentation/plan_pruebas.md`

Este archivo guarda las salidas reales de las 12 pruebas de la rubrica. Se
regenera ejecutando los comandos indicados; no se edita a mano.

---

## 0. Ambiente

```
Python 3.12.10
Microsoft SQL Server 2025 (RTM-GDR) (KB5132748) - 17.0.1155.
Base fuente: Venta (10 tablas de negocio)
Base plataforma: DataPlatform (raw, clean, ready, dw, audit, quarantine)
```

Estado del DW al cierre de la ejecucion:

```
ready.Ventas     : 5 filas | S/ 696.40
dw.FactVentas    : 5 filas | S/ 696.40
dw.DimTiempo     : 13150 filas (2000-01-01 a 2035-12-31 + desconocido)
dw.DimProducto   : 5
dw.DimLocal      : 5
dw.DimVersion    : 3
```

---

## 1. Carga inicial

```powershell
cd services/etl
python -m app full
```

```
[1/4] Extrayendo (full) desde Venta -> DataPlatform ...
      tablas extraidas: 10
[2/4] Limpiando y validando (clean) ...
[3/4] Integrando (ready) ...
[4/4] Cargando Data Warehouse (dimensiones + hechos) ...

Resumen
  filas rechazadas : 0
  ready.Ventas     : insertadas=0 actualizadas=5
  dw.DimProducto   : insertadas=0 actualizadas=4
  dw.DimLocal      : insertadas=0 actualizadas=4
  dw.DimVersion    : insertadas=0 actualizadas=2
  dw.FactVentas    : insertadas=0 actualizadas=5
  huerfanos en hecho: 0
```

La base ya estaba cargada, por eso el comando actualiza y no inserta. La primera
carga historica (T05/T08) inserto las 5 lineas; el resultado estable es el mismo:
5 filas y S/ 696.40.

```powershell
sqlcmd -S localhost -E -C -f 65001 -i database/99_verify.sql
```

Salida relevante:

```
=== 3. Miembros desconocidos (clave 0) ===
DimTiempo 1 | DimProducto 1 | DimLocal 1 | DimVersion 1

=== 4. Cobertura de DimTiempo ===
2000-01-01 a 2035-12-31 (13149 dias)

=== 5. Huerfanos en el hecho (debe devolver 0 filas) ===
hechos_huerfanos = 0

=== 6. Consulta de validacion sobre la vista de consumo ===
5 lineas, importe total 696.40
```

---

## 2. Carga incremental

```powershell
cd services/etl
python -m app incremental
```

Salida resumida:

```
[1/4] Extrayendo (incremental) desde Venta -> DataPlatform ...
[2/4] Limpiando y validando (clean) ...
[3/4] Integrando (ready) ...
[4/4] Cargando Data Warehouse ...

  filas rechazadas : 0
  ready.Ventas     : insertadas=0 actualizadas=5
  dw.FactVentas    : insertadas=0 actualizadas=5
  huerfanos en hecho: 0
```

En `audit.etl_execution` la corrida incremental extrae solo la ventana nueva:

```
sales_extract_incremental | Venta.dbo.Factura         | 1 fila
sales_extract_incremental | Venta.dbo.Factura_Detalle | 1 fila
sales_extract_incremental | dimensiones               | 4/5/2 filas
```

Watermark vigente:

```
sales_incremental | Venta.dbo.Factura         | Fecha | 2008-08-15 00:00:00
sales_incremental | Venta.dbo.Factura_Detalle | Fecha | 2008-08-15 00:00:00
```

---

## 3. Idempotencia

```powershell
cd services/etl
python -m app idempotency-check
```

```
== Segunda ejecucion (mismo lote) ==
[1/4] Extrayendo (full) ... tablas extraidas: 10
[2/4] Limpiando y validando (clean) ...
[3/4] Integrando (ready) ...
[4/4] Cargando Data Warehouse ...

tabla (capas estables)            antes        1ra        2da   estado
clean.Factura                         5          5          5       OK
clean.FacturaDetalle                  5          5          5       OK
clean.Producto                        4          4          4       OK
dw.FactVentas                         5          5          5       OK
importe_dw_centavos               69640      69640      69640       OK
ready.Ventas                          5          5          5       OK

Capas append-only (crecimiento esperado, no afectan idempotencia):
  raw.Factura                      27 ->       37
  raw.FacturaDetalle               27 ->       37

RESULTADO: IDEMPOTENTE (los conteos de las capas estables no cambian)
```

---

## 4. Nulos y duplicados

Consulta de control:

```sql
SELECT 'ready' capa, COUNT(*) filas,
       SUM(CASE WHEN IdFacturaDetalle IS NULL THEN 1 ELSE 0 END) nulos_pk,
       SUM(CASE WHEN Cantidad IS NULL OR PrecioUnitario IS NULL OR ImporteLinea IS NULL THEN 1 ELSE 0 END) nulos_medidas,
       COUNT(*) - COUNT(DISTINCT IdFacturaDetalle) duplicados_pk
  FROM ready.Ventas;

SELECT 'dw' capa, COUNT(*) filas,
       SUM(CASE WHEN TiempoKey=0 OR ProductoKey=0 OR LocalKey=0 OR VersionKey=0 THEN 1 ELSE 0 END) claves_desconocidas,
       SUM(CASE WHEN Cantidad IS NULL OR ImporteLinea IS NULL THEN 1 ELSE 0 END) nulos_medidas,
       COUNT(*) - COUNT(DISTINCT IdFacturaDetalle) duplicados_pk,
       SUM(CASE WHEN ImporteLinea <> Cantidad*PrecioUnitario - Descuento THEN 1 ELSE 0 END) importe_incoherente
  FROM dw.FactVentas;

SELECT COUNT(*) total, SUM(CASE WHEN status='PENDIENTE' THEN 1 ELSE 0 END) pendientes
  FROM quarantine.rejected_row;
```

Resultado:

```
capa  | filas | nulos_pk | nulos_medidas | duplicados_pk
ready |     5 |        0 |             0 |             0

capa | filas | claves_desconocidas | nulos_medidas | duplicados_pk | importe_incoherente
dw   |     5 |                   0 |             0 |             0 |                   0

cuarentena: total=0
```

Prueba unitaria del catalogo y de la supervivencia ante duplicados:

```powershell
python tests/test_quality_rules.py
```

```
Caso 1: nulos en dimensiones          -> DQ-011, DQ-012
Caso 2: cabecera invalida             -> DQ-001, DQ-007, DQ-009, DQ-010, DQ-015
Caso 3: linea invalida                -> DQ-003, DQ-004, DQ-005, DQ-006, DQ-008
Caso 4: linea valida                  -> sin errores
Caso 5: normalizacion                 -> "Mini Lorito " -> "Mini Lorito", 8.2 -> 8.20
Caso 6: duplicados                    -> 2 unicas, 1 duplicado, sobrevive la ultima
Caso 7: catalogo                      -> 15 reglas, DQ-013 presente

RESULTADO: OK - reglas de calidad y duplicados verificados
```

---

## 5. Integridad referencial

```sql
SELECT COUNT(*) huerfanos
  FROM dw.FactVentas f
 WHERE NOT EXISTS (SELECT 1 FROM dw.DimTiempo t   WHERE t.TiempoKey  = f.TiempoKey)
    OR NOT EXISTS (SELECT 1 FROM dw.DimProducto p WHERE p.ProductoKey = f.ProductoKey)
    OR NOT EXISTS (SELECT 1 FROM dw.DimLocal l    WHERE l.LocalKey    = f.LocalKey)
    OR NOT EXISTS (SELECT 1 FROM dw.DimVersion v  WHERE v.VersionKey  = f.VersionKey);
```

```
huerfanos = 0
claves_desconocidas en el hecho = 0
importe_incoherente = 0
miembros desconocidos disponibles: DimTiempo, DimProducto, DimLocal, DimVersion
```

---

## 6. Recuperacion ante falla

Se forzo una base fuente inexistente. La corrida falla y **no** avanza el
watermark:

```powershell
cd services/etl
$env:SOURCE_DATABASE="VentaNoExiste"
python -m app incremental
```

```
pyodbc.InterfaceError: ('28000', ... Cannot open database "VentaNoExiste" ...)
EXIT=1
```

Watermark antes y despues de la falla:

```
pipeline_name     | source_object               | watermark
sales_incremental | Venta.dbo.Factura           | 2008-08-15T00:00:00
sales_incremental | Venta.dbo.Factura_Detalle   | 2008-08-15T00:00:00
```

La falla ocurre al conectar, antes de abrir la corrida en `audit`, por lo que no
se escribe en `raw`. Luego se restaura la variable y se reintenta:

```powershell
Remove-Item Env:\SOURCE_DATABASE
python -m app incremental
```

```
ready.Ventas     : insertadas=0 actualizadas=5
dw.FactVentas    : insertadas=0 actualizadas=5
filas rechazadas : 0
huerfanos en hecho: 0
EXIT=0
```

---

## 7. Reconciliacion entre capas

```powershell
cd services/etl
python -m app quality-report
```

```
| capa                              | filas | importe |
|-----------------------------------|-------|---------|
| Fuente Venta.dbo.Factura_Detalle  |     5 |  696.40 |
| clean.FacturaDetalle              |     5 |  696.40 |
| ready.Ventas                      |     5 |  696.40 |
| dw.FactVentas                     |     5 |  696.40 |
```

Rechazos por regla: sin rechazos registrados.

Hallazgo: `SUM(Factura.VentaAsociada)` = 455.00, distinto de
`SUM(Cantidad * PrecioSinImporte)` = 696.40. La cabecera no se usa como medida.

---

## 8. Dashboard

```powershell
python tests/smoke_dashboard.py
python tests/test_dashboard_app.py
```

```
health          : ok | filas=5 | etl=SUCCESS
filtros         : 4 locales, 2 secciones
kpis            : 6 tarjetas | ventas=696.4
tendencias      : 1 puntos | variacion=None
detalle         : total=5 | filas=3
periodo vacio   : ventas=0.0
RESULTADO: OK

excepciones      : 0
mensajes error   : 0
tarjetas (metric): 11
tablas           : 1
titulo           : ['Ventas - Plataforma integral de datos']

API caida        :
  excepciones    : 0
  errores        : ['No se pudo conectar con la API en http://localhost:9. Verifi']
RESULTADO: OK
```

---

## 9. Modelo ML

```powershell
python tests/test_ml_model.py
```

```
Caso 1: serie con 24 meses (entrenamiento posible)
  estado        : trained
  train / test  : 18 / 6
  MAE modelo    : 38.9
  RMSE modelo   : 44.66
  MAE baseline  : 480.0
  INFO: el modelo mejora al baseline en la serie sintetica

Caso 2: serie con 1 mes (datos insuficientes)
  estado        : insufficient_data
  metricas      : {'mae': None, 'rmse': None, 'mape': None}

RESULTADO: OK
```

Servicio con la fuente real:

```powershell
cd services/ml
python -m app train
```

```
status          : insufficient_data
message         : Se necesitan al menos 8 meses con ventas para dividir en
                  entrenamiento y prueba; hay 1. No se publican metricas.
periodos train  : 0
periodos test   : 1
MAE modelo      : None
MAE baseline    : None
```

`POST /predict` responde 409 mientras no haya modelo entrenado.

---

## 10. GenAI

```powershell
cd services/genai
python -m app test
```

```
id       intent               obtenido             resultado
T12-01   ventas_totales       ventas_totales       OK
T12-02   facturas             facturas             OK
T12-03   ticket_promedio      ticket_promedio      OK
T12-04   top_productos        top_productos        OK
T12-05   ventas_por_local     ventas_por_local     OK
T12-06   ventas_por_seccion   ventas_por_seccion   OK
T12-07   ventas_por_producto  ventas_por_producto  OK
T12-08   tendencia            tendencia            OK
T12-09   comparacion          comparacion          OK
T12-10   no_data              no_data              OK

RESULTADO: 10/10 pruebas OK
```

Ejemplo real de respuesta respaldada:

```json
{
  "pregunta": "ventas por local",
  "intent": "ventas_por_local",
  "grounded": true,
  "fuentes": [{"servicio": "core-api", "endpoint": "/api/v1/agrupado?dimension=local"}]
}
```

---

## 11. Alertas

```powershell
python tests/test_alerting_rules.py
python tests/smoke_alerting.py
```

```
Reglas: 6
Primera evaluacion : disparadas=3 nuevas=3 duplicadas=0
  VENTAS_BAJAS        warning  obs=696.4  umbral=1000
  TICKET_BAJO         warning  obs=174.1  umbral=200
  MODELO_SIN_ENTRENAR info     obs=1.0    umbral=8

Segunda evaluacion: nuevas=0 duplicadas=3
POST /alerts/{id}/ack        -> acknowledged
POST /alerts/simulate        -> simulated=1
GET /monitor.json            -> pipeline + modelo + alertas
GET /monitor                 -> HTML 200

RESULTADO: OK - reglas, deduplicacion y entregas verificadas
RESULTADO: OK
```

Reglas que no se disparan con los datos actuales: `CAIDA_VENTAS` (no hay periodo
previo comparable), `MAE_ALTO` (no hay modelo) y `RECHAZOS_ALTOS` (0 rechazos).

---

## 12. End-to-end

Con los 6 servicios arriba y `ALERT_DB_PATH` aislado:

```powershell
python tests/e2e_smoke.py
```

```
End-to-end: fuente -> DW -> API -> dashboard / GenAI / ML / alertas
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

---

## 13. Control de secretos

```powershell
git rev-list --all --objects | Select-String "(^|/)\.env$"
git ls-files | Select-String "(^|/)\.env$"
git log --all --oneline -- .env
```

```
(vacio en los tres casos: .env nunca se versiono)
```

```powershell
git grep -n -I -E "(password|secret|token|api[_-]?key)\s*[:=]\s*[^#[:space:]]+"
```

Solo devuelve lecturas de variables de entorno (`os.getenv("DW_PASSWORD")`) y
comentarios vacios en `.env.example`. No hay credenciales reales.

---

## 14. Resultado global

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
| 10 | GenAI | OK |
| 11 | Alertas | OK |
| 12 | End-to-end | OK |

Todas las pruebas se ejecutaron sobre datos reales, salvo el algoritmo ML, que se
verifica con una serie sintetica **identificada como tal** porque la fuente no
tiene historia suficiente.
