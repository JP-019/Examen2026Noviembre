# genai (T12)

## Responsabilidad

Responder preguntas en lenguaje natural sobre las ventas usando **solo** un
catalogo de consultas aprobadas. No ejecuta SQL libre, no se conecta a SQL Server
y no inventa cifras: cada respuesta declara el endpoint de `core-api` que la
respalda.

## Como evita inventar datos

1. La pregunta se normaliza y se clasifica con reglas deterministas
   (`app/intents.py`); no hay generacion libre de texto.
2. El catalogo de intenciones se publica desde `app/query_catalog.py`; sus
   handlers usan endpoints fijos de `core-api` en `app/queries.py`.
3. Si la pregunta esta fuera de alcance o no hay datos, responde `grounded=false`
   y no devuelve numeros.
4. Toda respuesta incluye `fuentes` con servicio, endpoint y `data_updated_at`.

## Ejecucion

Con `core-api` corriendo en el puerto 8000:

```powershell
cd services/genai
python -m pip install -r requirements.txt
uvicorn app.main:app --port 8003 --reload
```

| Recurso | URL |
|---|---|
| Swagger | <http://localhost:8003/docs> |
| Salud | <http://localhost:8003/health> |
| Preguntar | `POST /ask` con `{"pregunta": "cuanto vendimos en total"}` |
| Catalogo | <http://localhost:8003/queries> |
| Pruebas | <http://localhost:8003/tests> y `POST /tests/run` |

CLI:

```powershell
python -m app ask "ventas por local"
python -m app queries
python -m app test
```

## Consultas aprobadas

| Intención | Ruta API | Ejemplo |
|---|---|---|
| `ventas_totales` | `GET /api/v1/kpis` | cuanto vendimos en total |
| `facturas` | `GET /api/v1/kpis` | cuantas facturas hay |
| `ticket_promedio` | `GET /api/v1/kpis` | cual es el ticket promedio |
| `unidades` | `GET /api/v1/kpis` | cuantas unidades se vendieron |
| `top_productos` | `GET /api/v1/agrupado?dimension=producto` | ranking de productos |
| `ventas_por_local` | `GET /api/v1/agrupado?dimension=local` | ventas por local |
| `ventas_por_seccion` | `GET /api/v1/agrupado?dimension=seccion` | ventas por seccion |
| `ventas_por_producto` | `GET /api/v1/kpis?producto=...` | cuanto vendio Mini Lorito |
| `tendencia` | `GET /api/v1/tendencias?granularidad=mes` | tendencia mensual |
| `comparacion` | `GET /api/v1/kpis` (dos periodos) | comparar 2007 vs 2008 |
| `no_data` | (ninguno) | preguntas fuera de alcance |

## Indice de funciones

| Archivo | Funcion | Que hace |
|---|---|---|
| `app/api_client.py` | `CoreApi._get` | GET a core-api con timeout y errores tipados |
| `app/api_client.py` | `CoreApi.agrupado` | Totales por local, seccion o producto |
| `app/intents.py` | `normalizar` | Quita acentos, minusculas y espacios extra |
| `app/intents.py` | `interpretar` | Clasifica la pregunta y extrae filtros y anios |
| `app/intents.py` | `periodo_legible` | Redacta el periodo en lenguaje natural |
| `app/queries.py` | `responder` | Ejecuta la consulta aprobada de la intencion |
| `app/query_catalog.py` | `QUERY_CATALOG` | Catalogo publicado en `/queries` |
| `app/checks.py` | `CASES` | Las 10 pruebas documentadas |
| `app/checks.py` | `run` | Ejecuta y evalua las 10 pruebas |
| `app/main.py` | `/ask` | Pregunta en lenguaje natural con fuentes |
| `app/main.py` | `/tests/run` | Corre las pruebas y devuelve el resumen |

## Definicion de terminado

- [x] 10 pruebas documentadas y ejecutables (`/tests`, `/tests/run`).
- [x] Respuestas con `fuentes` y `grounded`.
- [x] Rechazo explicito de preguntas fuera de alcance.
- [x] Sin SQL libre ni acceso directo a SQL Server.
- [x] Sin cifras cuando no hay datos (comparacion sin anio base, periodos vacios).
