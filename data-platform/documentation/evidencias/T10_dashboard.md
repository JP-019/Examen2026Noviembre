# Evidencia T10 - Dashboard web

- **Servicio:** `services/dashboard`
- **Puerto:** 8501
- **Consumo:** solo `core-api` (puerto 8000); sin conexion a SQL Server
- **Recolectado:** 2026-11-13
- **Reproducible:** `python tests/smoke_dashboard.py` y `python tests/test_dashboard_app.py`

## 1. Arranque

```powershell
# Terminal 1
cd services/core-api
uvicorn app.main:app --port 8000

# Terminal 2
cd services/dashboard
streamlit run app.py --server.port 8501
```

Resultado del arranque headless:

```
Local URL: http://localhost:8501
STREAMLIT HEALTH: 200 ok
PAGINA: 200 bytes=7863
```

## 2. Prueba del cliente HTTP (`tests/smoke_dashboard.py`)

```
health          : ok | filas=5 | etl=SUCCESS
filtros         : 4 locales, 2 secciones
kpis            : 6 tarjetas | ventas=696.4
tendencias      : 1 puntos | variacion=None
detalle         : total=5 | filas=3
periodo vacio   : ventas=0.0

RESULTADO: OK
```

Cada llamada queda registrada por la API (`GET /api/v1/...`), lo que demuestra
que el dashboard consume solo HTTP y no la base.

## 3. Prueba de render (`tests/test_dashboard_app.py`)

Se ejecuta la app con `streamlit.testing.v1.AppTest` (sin navegador):

```
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

`11` tarjetas = 6 KPIs + 2 de cabecera + 3 de comparacion de periodo.

## 4. Correspondencia con la consigna

| Requisito | Como se cumple | Evidencia |
|---|---|---|
| 4 a 6 KPIs | 6 tarjetas: ventas, lineas, facturas, ticket, unidades, productos | seccion 2 |
| Filtros de fecha | selector de periodo acotado al rango real de datos | `_sidebar` |
| 2 dimensiones | local, seccion y producto | 4 locales, 2 secciones |
| Tendencias | barras por dia/mes + comparacion con periodo anterior | `/tendencias` |
| Detalle | tabla paginada + CSV | `total=5`, 3 filas en la prueba |
| Estados | cargando, error de API, sin datos, ok | seccion 3 |
| Sin SQL directo | cliente HTTP con `requests`; no importa `pyodbc` | `api_client.py` |

## 5. Controles y limitaciones

- El dashboard **no** calcula cifras por su cuenta: muestra lo que devuelve la API.
- La fecha de actualizacion proviene de `audit.etl_execution`, no del reloj del servidor.
- No hay capturas de pantalla en esta evidencia porque el agente no dispone de
  navegador: la verificacion se hizo con health check y `AppTest`. Para el video
  de T15, abrir <http://localhost:8501> y mostrar filtros, grafico y tabla.
- Con la fuente actual (5 lineas) la tendencia tiene un solo punto. La app ya
  soporta multiples periodos; se vera completa cuando la fuente crezca.
