# Guion del video y checklist de demo (T15)

- **Tarea:** T15
- **Duracion objetivo:** 5 minutos
- **Modalidad:** ejecucion real, no solo diapositivas
- **Estado:** guion y checklist listos; la grabacion la realiza el equipo

> El agente no puede grabar video ni capturar la pantalla. Este documento entrega
> el guion minuto a minuto, los comandos exactos, el checklist y el plan B para
> que el equipo grabe y ensaye sin improvisar.

---

## 1. Preparacion previa (30 minutos antes)

### 1.1 Ambiente

```powershell
# 1. Base y datos
sqlcmd -S localhost -E -C -f 65001 -i database/99_verify.sql

# 2. ETL al dia
cd services/etl
python -m app incremental
python -m app status
cd ../..

# 3. Alertas en base limpia para la demo (opcional, recomendado)
$env:ALERT_DB_PATH="$env:TEMP\demo_alerts.db"
Remove-Item $env:ALERT_DB_PATH -ErrorAction SilentlyContinue
```

### 1.2 Servicios (6 terminales)

| Terminal | Carpeta | Comando |
|---|---|---|
| 1 | `services/core-api` | `uvicorn app.main:app --port 8000` |
| 2 | `services/catalog` | `uvicorn app.main:app --port 8001` |
| 3 | `services/ml` | `uvicorn app.main:app --port 8002` |
| 4 | `services/genai` | `uvicorn app.main:app --port 8003` |
| 5 | `services/alerting` | `uvicorn app.main:app --port 8004` |
| 6 | `services/dashboard` | `streamlit run app.py --server.port 8501` |

### 1.3 Ventanas y pestanas listas

1. Navegador, pestana A: <http://localhost:8501> (dashboard).
2. Navegador, pestana B: <http://localhost:8004/monitor> (monitoreo).
3. Navegador, pestana C: <http://localhost:8000/docs> (Swagger de la API).
4. Navegador, pestana D: <http://localhost:8001/index.md> (indice vivo).
5. Terminal del ETL con la salida visible y fuente grande.
6. Terminal del GenAI para `python -m app ask "ventas por local"`.
7. Editor mostrando `documentation/arquitectura.md` o el diagrama.

### 1.4 Reglas de la grabacion

- No mostrar `.env`, tokens, contrasenas ni rutas con datos personales.
- Cerrar notificaciones y pestanas ajenas.
- Aumentar el zoom del navegador y de la terminal.
- Identificar cualquier evento simulado como **simulado**.
- Grabar en 1080p; audio claro; hablar pausado.

---

## 2. Guion minuto a minuto

### 0:00 - 0:40 | Caso, arquitectura y tecnologias

**Pantalla:** `documentation/arquitectura.md` o el diagrama de capas.

**Narracion sugerida:**

> "Este proyecto toma las ventas de la base `Venta` y las convierte en una
> plataforma de analitica. La fuente se copia a una zona raw, se limpia y valida,
> se integra una fila por linea de factura y se carga en un Data Warehouse en
> estrella. Sobre ese DW hay una API, un dashboard, un modelo predictivo, un
> asistente y un motor de alertas. Cada componente es un microservicio: solo la
> API y el ETL hablan con SQL Server; el resto consume HTTP. El stack es SQL
> Server, Python, FastAPI y Streamlit."

**Mostrar:** 7 carpetas de `services/` y el indice `INDEX.md`.

---

### 0:40 - 1:30 | ETL: extraccion, staging, transformacion y controles

**Pantalla:** terminal del ETL.

**Comandos:**

```powershell
cd services/etl
python -m app status
python -m app incremental
```

**Narracion sugerida:**

> "El ETL extrae 10 tablas. Raw es append-only: nunca se actualiza ni borra. En
> clean se tipa, se recortan espacios y se validan 15 reglas de calidad; lo que
> falla va a cuarentena con su codigo y payload, no se descarta en silencio. En
> ready queda una fila por linea de factura. El incremental usa un watermark y
> solo avanza si la corrida termina en SUCCESS."

**Mostrar:** `filas rechazadas: 0`, `huerfanos: 0`, la tabla de ultimas
ejecuciones y el watermark.

---

### 1:30 - 2:15 | Modelo dimensional, carga y consulta de validacion

**Pantalla:** `documentation/modelo_dimensional.md` (diagrama) y luego SQL.

**Comando:**

```powershell
sqlcmd -S localhost -E -C -d DataPlatform -W -s "|" -Q "SET NOCOUNT ON; SELECT TOP 5 NumeroFactura, Fecha, NombreProducto, NombreLocal, Cantidad, ImporteLinea FROM dw.vw_Ventas ORDER BY NumeroFactura"
```

**Narracion sugerida:**

> "El grano es una linea de factura. Tenemos DimTiempo, DimProducto, DimLocal y
> DimVersion, con miembro desconocido para no perder hechos. La medida es
> Cantidad por PrecioUnitario. La cabecera VentaAsociada no se usa porque no
> cuadra con el detalle: la suma de lineas es 696.40 y la cabecera 455.00. Esa
> decision esta documentada."

**Mostrar:** 5 filas, importe total 696.40, 0 huerfanos.

---

### 2:15 - 3:00 | Dashboard: KPIs, filtros y analisis historico

**Pantalla:** <http://localhost:8501>.

**Acciones:**

1. Mostrar las 6 tarjetas: ventas, lineas, facturas, ticket promedio, unidades, productos.
2. Cambiar el rango de fechas y un filtro de local.
3. Mostrar la tendencia y la comparacion.
4. Abrir el detalle y descargar el CSV.

**Narracion sugerida:**

> "El dashboard no calcula nada por su cuenta: consume la API. Los seis KPIs son
> consistentes con el DW. Los filtros se traducen a SQL parametrizado y el
> detalle se puede exportar. Si la API se cae, el tablero muestra el error, no
> una pantalla vacia."

---

### 3:00 - 3:45 | Modelo predictivo y explicacion de una metrica

**Pantalla:** <http://localhost:8002/docs> y respuesta de `/model`.

**Acciones:**

```powershell
Invoke-RestMethod http://localhost:8002/model | ConvertTo-Json -Depth 4
```

**Narracion sugerida:**

> "El modelo se divide de forma temporal: entrena con el pasado y evalua con los
> ultimos meses; nunca con los datos de entrenamiento. Compara contra un baseline
> naive. Con la fuente actual hay un solo mes, asi que el servicio responde
> `insufficient_data` y no publica metricas ni predicciones. Eso es correcto: no
> inventamos un MAE. El algoritmo se verifica con una serie sintetica de 24 meses
> en las pruebas, y esas cifras se identifican como sinteticas."

**Mostrar:** `status=insufficient_data`, metricas `null`, y el test sintetico con
MAE 38.9 vs baseline 480.0 (aclarando que es sintetico).

---

### 3:45 - 4:25 | Consulta al asistente generativo

**Pantalla:** terminal del GenAI.

```powershell
cd services/genai
python -m app ask "ventas por local"
python -m app ask "quien gano el mundial"
```

**Narracion sugerida:**

> "El asistente no ejecuta SQL libre ni usa un LLM externo. Clasifica la pregunta
> en un catalogo de 10 consultas aprobadas, llama a la API y arma la respuesta con
> los datos recibidos. Devuelve `fuentes` y `grounded=true`. Si la pregunta esta
> fuera de alcance, responde `grounded=false` y no inventa cifras."

**Mostrar:** respuesta con S/ por local y fuentes; luego el rechazo explicito.

---

### 4:25 - 5:00 | Disparo y visualizacion de una alerta

**Pantalla:** terminal de alertas y <http://localhost:8004/monitor>.

```powershell
cd services/alerting
python -m app evaluate
python -m app evaluate
```

**Narracion sugerida:**

> "El motor evalua 6 reglas: ventas bajas, ticket bajo, caida de ventas, modelo
> sin entrenar, MAE alto y rechazos altos. Con los datos actuales dispara tres
> alertas. La segunda evaluacion no duplica: la clave unica por regla, entidad,
> periodo y version de datos lo impide. Cada alerta registra valor observado,
> umbral, origen, explicacion, accion y entrega al canal. Esta es la vista de
> monitoreo con la ultima carga, fallas, rechazos y estado del modelo."

**Cierre (10 segundos):**

> "Queda funcionando el pipeline, el DW, la API, el dashboard, el modelo honesto,
> el asistente con fuentes y las alertas sin duplicados. La documentacion y las 12
> pruebas estan en el repositorio."

**Mostrar:** 3 nuevas, luego 0 nuevas / 3 duplicadas, y `/monitor`.

---

## 3. Checklist de la demo en vivo

### Antes de empezar

- [ ] SQL Server arriba y `99_verify.sql` sin huerfanos.
- [ ] ETL `incremental` ejecutado y en `SUCCESS`.
- [ ] Los 6 servicios responden health.
- [ ] Dashboard abre con 6 KPIs.
- [ ] `/monitor` abre sin alertas viejas (o con la base aislada).
- [ ] `.env` cerrado y notificaciones silenciadas.
- [ ] Zoom y fuente legibles.
- [ ] Plan B disponible (video/capturas).

### Durante la demo

- [ ] Mostrar al menos un pipeline o lote real.
- [ ] Mostrar el dashboard y una consulta analitica.
- [ ] Ejecutar una prediccion con version identificable o explicar por que no hay.
- [ ] Hacer una pregunta al asistente y mostrar la fuente.
- [ ] Disparar una alerta, mostrarla y demostrar el anti-duplicado.
- [ ] Identificar cualquier simulacion como simulada.
- [ ] Explicar como se recupera una ejecucion fallida (watermark no avanza).

### Despues

- [ ] Verificar que no se mostraron secretos.
- [ ] Guardar el video y las capturas.
- [ ] Revisar audio y legibilidad.
- [ ] Confirmar duracion cercana a 5 minutos.

---

## 4. Plan B

| Falla | Plan B |
|---|---|
| SQL Server no responde | Mostrar el video grabado y las capturas de `documentation/evidencias/` |
| Un servicio no levanta | Reiniciar ese servicio; si no, usar las capturas y el video |
| Dashboard lento | Mostrar el video del recorrido y la respuesta JSON de la API |
| Proyector o red falla | Presentar desde el video local y el PDF de arquitectura |
| Pregunta fuera de catalogo | Es una demostracion del rechazo honesto, no un error |
| Alerta ya evaluada | Usar `POST /alerts/simulate` y aclarar que es simulada |

**Material de respaldo mínimo:**

1. Video de 5 minutos.
2. Capturas del dashboard, `/monitor`, Swagger y la salida del ETL.
3. `documentation/arquitectura.md` y `documentation/plan_pruebas.md` en PDF.
4. `INDEX.md` para mostrar el mapa de la plataforma.

---

## 5. Grabacion: estructura de archivos sugerida

```
demo/
  video_5min.mp4
  capturas/
    01_arquitectura.png
    02_etl_status.png
    03_dw_consulta.png
    04_dashboard_kpis.png
    05_ml_insufficient_data.png
    06_genai_respuesta.png
    07_alerta_monitor.png
  guion.md              (este documento)
```

No versionar videos pesados en git; guardarlos en el almacenamiento del equipo y
referenciarlos desde el README de la entrega.

---

## 6. Estado de T15

| Condicion | Estado |
|---|---|
| Guion de 5 minutos | Listo (este documento) |
| Checklist de demo | Listo |
| Plan B | Listo |
| Ensayo completo | A cargo del equipo |
| Video grabado | A cargo del equipo (el agente no puede grabar) |

La demo se considera aprobada cuando el equipo graba el video, lo revisa y marca
el checklist sin errores criticos.
