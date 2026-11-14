# Evidencia T12 - Asistente GenAI con consultas aprobadas

- **Servicio:** `services/genai`
- **Puerto:** 8003
- **Dependencia:** `core-api` (puerto 8000); sin conexion a SQL Server
- **Recolectado:** 2026-11-13
- **Reproducible:** `python -m app test` y `POST /tests/run`

## 1. Arranque

```powershell
# Terminal 1
cd services/core-api
uvicorn app.main:app --port 8000

# Terminal 2
cd services/genai
uvicorn app.main:app --port 8003
```

```json
GET /health
{
  "status": "ok",
  "service": "genai",
  "core_api": "ok",
  "data_updated_at": "2026-11-14T02:47:00.789000",
  "fact_rows": 5
}
```

## 2. Catalogo de consultas aprobadas

```json
GET /queries
{"total": 11, "queries": [...]}
```

| Intención | Ruta API | Ejemplo |
|---|---|---|
| `ventas_totales` | `/api/v1/kpis` | cuanto vendimos en total |
| `facturas` | `/api/v1/kpis` | cuantas facturas hay |
| `ticket_promedio` | `/api/v1/kpis` | cual es el ticket promedio |
| `unidades` | `/api/v1/kpis` | cuantas unidades se vendieron |
| `top_productos` | `/api/v1/agrupado?dimension=producto` | ranking de productos |
| `ventas_por_local` | `/api/v1/agrupado?dimension=local` | ventas por local |
| `ventas_por_seccion` | `/api/v1/agrupado?dimension=seccion` | ventas por seccion |
| `ventas_por_producto` | `/api/v1/kpis?producto=...` | cuanto vendio Mini Lorito |
| `tendencia` | `/api/v1/tendencias?granularidad=mes` | tendencia mensual |
| `comparacion` | `/api/v1/kpis` (dos periodos) | comparar 2007 vs 2008 |
| `no_data` | (ninguno) | preguntas fuera de alcance |

Son 11 entradas: 10 consultas de negocio mas el rechazo explicito `no_data`.

## 3. Respuesta de ejemplo (`POST /ask`)

Pregunta: `"ventas por local"`.

```json
{
  "pregunta": "ventas por local",
  "intent": "ventas_por_local",
  "respuesta": "Ventas por local del periodo completo: VIVANDA BENAVIDES S/ 339.00; PLAZA VEA JOCKEY S/ 249.00; PLAZA VEA SAN BORJA S/ 82.00; VIVANDA JAVIER PRADO S/ 26.40.",
  "datos": {
    "grupos": [
      {"valor": "VIVANDA BENAVIDES", "ventas": 339.0, "lineas": 1, "facturas": 1, "unidades": 30},
      {"valor": "PLAZA VEA JOCKEY", "ventas": 249.0, "lineas": 2, "facturas": 2, "unidades": 21},
      {"valor": "PLAZA VEA SAN BORJA", "ventas": 82.0, "lineas": 1, "facturas": 1, "unidades": 10},
      {"valor": "VIVANDA JAVIER PRADO", "ventas": 26.4, "lineas": 1, "facturas": 1, "unidades": 2}
    ],
    "total_grupos": 4
  },
  "fuentes": [
    {
      "servicio": "core-api",
      "endpoint": "/api/v1/agrupado?dimension=local",
      "data_updated_at": "2026-11-14T02:47:00.789000"
    }
  ],
  "grounded": true,
  "interpretacion": ""
}
```

La suma de los cuatro locales (339 + 249 + 82 + 26.4) es **696.40**, el mismo
total de `dw.FactVentas`.

## 4. Las 10 pruebas documentadas

`GET /tests` publica el listado. `POST /tests/run` lo ejecuta contra la API viva:

```
T12-01 | ventas_totales      | ventas_totales      | OK
T12-02 | facturas            | facturas            | OK
T12-03 | ticket_promedio     | ticket_promedio     | OK
T12-04 | top_productos       | top_productos       | OK
T12-05 | ventas_por_local    | ventas_por_local    | OK
T12-06 | ventas_por_seccion  | ventas_por_seccion  | OK
T12-07 | ventas_por_producto | ventas_por_producto | OK
T12-08 | tendencia           | tendencia           | OK
T12-09 | comparacion         | comparacion         | OK
T12-10 | no_data             | no_data             | OK

RESULTADO: 10/10 pruebas OK
```

| # | Pregunta | Que verifica |
|---|---|---|
| 01 | ¿Cuánto vendimos en total? | importe y fuentes de KPIs |
| 02 | ¿Cuántas facturas hay? | conteo de facturas |
| 03 | ¿Cuál es el ticket promedio? | ticket sobre facturas |
| 04 | Ranking de productos más vendidos | agrupado por producto |
| 05 | Ventas por local | agrupado por local |
| 06 | Ventas por sección | agrupado por seccion |
| 07 | ¿Cuánto vendió Mini Lorito? | entidad del catalogo reconocida |
| 08 | Tendencia mensual de ventas | serie mensual no vacia |
| 09 | Comparar 2007 vs 2008 | dos periodos consultados |
| 10 | ¿Cómo va el clima mañana? | rechazo sin datos ni fuentes |

## 5. Comparacion entre anios

```json
POST /ask {"pregunta": "comparar 2007 vs 2008"}
{
  "intent": "comparacion",
  "respuesta": "Ventas 2007: S/ 0.00. Ventas 2008: S/ 696.40. La variacion no es calculable porque el anio base no tiene ventas.",
  "datos": {"anio_a": "2007", "ventas_a": 0.0, "anio_b": "2008", "ventas_b": 696.4, "variacion_pct": null},
  "fuentes": [
    {"endpoint": "/api/v1/kpis?desde=2007-01-01&hasta=2007-12-31"},
    {"endpoint": "/api/v1/kpis?desde=2008-01-01&hasta=2008-12-31"}
  ],
  "grounded": true
}
```

No se publica un porcentaje cuando la base es cero: `variacion_pct` queda en
`null` y la respuesta lo explica.

## 6. Pregunta fuera de alcance

```json
POST /ask {"pregunta": "¿Cómo va el clima mañana?"}
{
  "intent": "no_data",
  "respuesta": "No puedo responder esa pregunta con los datos de ventas de la plataforma. ...",
  "datos": {},
  "fuentes": [],
  "grounded": false
}
```

## 7. Controles aplicados

1. **Sin SQL libre:** la pregunta nunca se convierte en SQL; se clasifica en una
   intencion y se llama a un endpoint fijo.
2. **Sin cifras inventadas:** si no hay datos o la pregunta esta fuera de alcance,
   `grounded=false` y `datos={}`.
3. **Fuentes declaradas:** cada respuesta incluye el endpoint y la fecha de
   actualizacion del dato.
4. **Entidades del catalogo:** locales, secciones y productos se reconocen contra
   `/api/v1/filtros`; no se aceptan nombres inventados.
5. **Parametros acotados:** solo `desde`, `hasta`, `local`, `seccion` y `producto`
   llegan a la API (`ALLOWED_PARAMS`).
6. **Sin acceso directo a la base:** el asistente solo usa HTTP contra `core-api`.

## 8. Limitaciones

- La interpretacion es determinista por reglas, no un LLM generativo. Se eligio
  para cumplir la restriccion de no inventar cifras ni ejecutar SQL libre.
- Con la fuente actual (un mes) la tendencia tiene un solo punto y la comparacion
  entre anios tiene un anio sin ventas; ambos casos se informan sin adornos.
- El reconocimiento de entidades exige el nombre del catalogo (por ejemplo
  `Mini Lorito`), no variantes coloquiales.
