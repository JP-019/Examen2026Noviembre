# Evidencia T09 - API de KPIs (core-api)

- **Servicio:** `services/core-api`
- **Puerto:** 8000
- **Base:** `DataPlatform` (`dw.vw_Ventas`)
- **Recolectado:** 2026-11-13
- **Reproducible:** `python tests/smoke_core_api.py` con la API corriendo

## 1. Arranque

```powershell
cd services/core-api
uvicorn app.main:app --port 8000
```

Swagger disponible en <http://localhost:8000/docs>.

## 2. Respuesta de `/api/v1/health`

```json
{
  "status": "ok",
  "service": "core-api",
  "database": "DataPlatform",
  "data_updated_at": "2026-11-14T02:47:00.789000",
  "last_etl_status": "SUCCESS",
  "fact_rows": 5
}
```

La API no inventa la fecha de actualizacion: la toma de `audit.etl_execution`.

## 3. Respuesta de `/api/v1/kpis`

```json
{
  "periodo": {"desde": null, "hasta": null},
  "filtros": {"desde": null, "hasta": null, "local": null, "seccion": null, "producto": null},
  "data_updated_at": "2026-11-14T02:47:00.789000",
  "kpis": [
    {"code": "ventas", "label": "Ventas totales", "value": 696.4, "unit": "ARS", "format": "currency"},
    {"code": "lineas", "label": "Lineas de venta", "value": 5, "unit": "lineas", "format": "integer"},
    {"code": "facturas", "label": "Facturas", "value": 4, "unit": "facturas", "format": "integer"},
    {"code": "ticket_promedio", "label": "Ticket promedio", "value": 174.1, "unit": "ARS", "format": "currency"},
    {"code": "unidades", "label": "Unidades vendidas", "value": 63, "unit": "unidades", "format": "integer"},
    {"code": "productos", "label": "Productos distintos", "value": 4, "unit": "productos", "format": "integer"}
  ]
}
```

Validacion independiente:

```sql
SELECT COUNT(*) AS lineas,
       COUNT(DISTINCT NumeroFactura) AS facturas,
       SUM(ImporteLinea) AS ventas,
       SUM(Cantidad) AS unidades
FROM dw.FactVentas;
-- lineas = 5 | facturas = 4 | ventas = 696.40 | unidades = 63
```

Los valores de la API coinciden con el DW: **696.40** de ventas en 5 lineas.

## 4. Respuesta de `/api/v1/tendencias?granularidad=mes`

```json
{
  "granularidad": "mes",
  "serie": [{"periodo": "2008-08", "ventas": 696.4, "lineas": 5}],
  "comparacion": {"actual": 696.4, "anterior": 0.0, "variacion_pct": null}
}
```

`variacion_pct` es `null` cuando el periodo anterior no tiene ventas; no se
inventa un porcentaje. Con fechas explicitas (`desde`/`hasta`) se calcula contra
el periodo inmediatamente anterior de igual duracion.

## 5. Respuesta de `/api/v1/filtros`

```json
{
  "desde": "2008-08-03",
  "hasta": "2008-08-15",
  "locales": ["PLAZA VEA JOCKEY", "PLAZA VEA SAN BORJA", "VIVANDA BENAVIDES", "VIVANDA JAVIER PRADO"],
  "secciones": ["Comestibles", "Utiles"],
  "productos": ["Cifrut Piña Granadilla", "Gloria hierro y calcio", "Jamonada de 13 tajadas", "Mini Lorito"],
  "data_updated_at": "2026-11-14T02:47:00.789000"
}
```

## 6. Prueba de humo (`tests/smoke_core_api.py`)

```
Prueba de humo core-api -> http://localhost:8000
caso                     esperado obtenido  resultado
health                        200      200  OK
kpis                          200      200  OK
kpis con filtro               200      200  OK
kpis periodo vacio            200      200  OK
tendencias dia                200      200  OK
tendencias mes                200      200  OK
detalle                       200      200  OK
detalle fuera de rango        200      200  OK
filtros                       200      200  OK
agrupado producto             200      200  OK
agrupado seccion              200      200  OK
agrupado dimension invalida   422      422  OK
monitor                       200      200  OK
rango invalido                422      422  OK
pagina invalida               422      422  OK

KPIs devueltos: 6
Ventas totales: 696.4
Filas en el hecho: 5
data_updated_at: 2026-11-14T02:47:00.789000

RESULTADO: OK
```

## 7. Casos borde verificados

| Caso | Entrada | Resultado |
|---|---|---|
| Periodo sin datos | `desde=1990-01-01&hasta=1990-12-31` | 200 con KPIs en 0 |
| Rango invertido | `desde=2020-01-01&hasta=2019-01-01` | 422 |
| Pagina invalida | `page=0` | 422 |
| Pagina fuera de rango | `page=999` | 200 con `rows=[]` y `total` real |
| Filtro por local | `local=PLAZA VEA JOCKEY` | 200, 2 lineas |
| Limite de pagina | `page_size` mayor al maximo | Se recorta a `CORE_API_MAX_PAGE_SIZE` (200) |

### Agrupado por dimension (agregado para T12)

`GET /api/v1/agrupado?dimension=producto&limit=5`:

```json
{
  "dimension": "producto",
  "total_grupos": 4,
  "grupos": [
    {"valor": "Mini Lorito", "ventas": 339.0, "lineas": 1, "facturas": 1, "unidades": 30},
    {"valor": "Jamonada de 13 tajadas", "ventas": 204.0, "lineas": 1, "facturas": 1, "unidades": 3},
    {"valor": "Gloria hierro y calcio", "ventas": 82.0, "lineas": 1, "facturas": 1, "unidades": 2},
    {"valor": "Cifrut Piña Granadilla", "ventas": 71.4, "lineas": 2, "facturas": 1, "unidades": 28}
  ]
}
```

La dimension sale de `GROUP_COLUMNS` (local, seccion, producto): un valor fuera
de esa lista devuelve 422 y nunca llega al SQL. La suma por producto coincide con
`dw.FactVentas` (339 + 204 + 82 + 71.4 = 696.4).

## 8. Controles aplicados

1. **Consultas parametrizadas:** los valores viajan como `?`; las columnas
   filtrables salen de `ALLOWED_COLUMNS` (`app/filters.py`), nunca del texto
   recibido.
2. **Solo lectura:** el servicio no ejecuta INSERT/UPDATE/DELETE.
3. **Sin secretos:** cadena ODBC armada desde `.env`.
4. **Trazabilidad del dato:** toda respuesta incluye `data_updated_at`.
5. **Paginacion obligatoria:** `OFFSET/FETCH` con maximo configurable.
6. **Sin acceso directo del frontend:** el dashboard y GenAI consumiran esta API.
