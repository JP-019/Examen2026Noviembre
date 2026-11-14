# core-api (T09)

## Responsabilidad

Unica puerta de acceso al Data Warehouse. El frontend, el asistente GenAI y el
motor de alertas consultan este servicio; ninguno se conecta a SQL Server.

## Ejecucion

Desde `services/core-api`:

```powershell
python -m pip install -r requirements.txt
uvicorn app.main:app --port 8000 --reload
```

| Recurso | URL |
|---|---|
| Swagger | <http://localhost:8000/docs> |
| Salud | <http://localhost:8000/api/v1/health> |
| KPIs | <http://localhost:8000/api/v1/kpis> |
| Tendencias | <http://localhost:8000/api/v1/tendencias> |
| Detalle | <http://localhost:8000/api/v1/detalle> |
| Filtros | <http://localhost:8000/api/v1/filtros> |
| Agrupado | <http://localhost:8000/api/v1/agrupado?dimension=producto> |
| Monitoreo | <http://localhost:8000/api/v1/monitor> |

## Endpoints

| Metodo | Ruta | Descripcion |
|---|---|---|
| GET | `/api/v1/health` | Estado y fecha de ultima actualizacion de datos |
| GET | `/api/v1/kpis` | 4 a 6 KPIs con filtros de fecha y dimension |
| GET | `/api/v1/tendencias` | Serie temporal y comparacion entre periodos |
| GET | `/api/v1/detalle` | Detalle paginado de lineas de venta |
| GET | `/api/v1/filtros` | Valores disponibles para filtros |
| GET | `/api/v1/agrupado` | Totales por local, seccion o producto (dimension en whitelist) |
| GET | `/api/v1/monitor` | Estado operativo: ultima carga, fallas, rechazos y filas del hecho |

Filtros comunes: `desde`, `hasta` (YYYY-MM-DD), `local`, `seccion`, `producto`.

## Reglas de implementacion

1. Consultas **parametrizadas**; prohibido concatenar SQL.
2. Paginacion obligatoria en `/detalle` (limite maximo configurable).
3. Toda respuesta incluye `data_updated_at`.
4. Manejo explicito de periodos sin datos, errores de conexion y carga.
5. Credenciales solo por `.env`.

## Indice de funciones

| Archivo | Funcion | Que hace |
|---|---|---|
| `app/config.py` | `settings` | Lee `.env` y arma la cadena ODBC |
| `app/database.py` | `query` | Ejecuta SQL parametrizado y devuelve dicts |
| `app/database.py` | `scalar` | Devuelve un unico valor |
| `app/schemas.py` | `Kpi*` | Contratos de respuesta |
| `app/filters.py` | `build_where` | Traduce filtros a WHERE parametrizado |
| `app/services.py` | `kpis` | Calcula KPIs del periodo |
| `app/services.py` | `tendencias` | Serie temporal por dia/mes y comparacion |
| `app/services.py` | `detalle` | Detalle paginado |
| `app/services.py` | `filtros` | Valores disponibles |
| `app/services.py` | `agrupado` | Totales por una de las 3 dimensiones permitidas |
| `app/services.py` | `monitor` | Estado operativo del pipeline, la calidad y el hecho |
| `app/main.py` | `health` | Estado + ultima carga del ETL |
