# Guion del video de demostración (5 minutos)

| Campo | Valor |
|---|---|
| Duración objetivo | 5:00 |
| Formato | Captura de pantalla con audio |
| Proyecto | Plataforma de datos + bot de Telegram |
| Audiencia | Docente y compañeros del curso |
| Regla | Mostrar ejecución real, nunca diapositivas |

---

## 1. Antes de grabar

| Verificación | Cómo |
|---|---|
| SQL Server responde | `sqlcmd -S localhost -E -C -Q "SELECT @@VERSION"` |
| Datos cargados | `py -m app status` en `services/etl`: 5 filas y S/ 696.40 |
| Servicios arriba | Puertos 8000 a 8004 y 8501 respondiendo |
| Alertas evaluadas | `py -m app evaluate` en `services/alerting` |
| Bot con un pedido de prueba | Pedido visible en el panel del bot |
| Secretos ocultos | Cerrar `.env`, terminales con tokens y notificaciones |
| Pantalla | 1080p, zoom al 110 %, sin pestañas personales |
| Plan B | Capturas de dashboard, monitor y asistente por si falla algo |

Consejo: graba primero el recorrido completo sin audio para medir el tiempo y
detectar ventanas que no cargan. Después graba la voz sobre el recorrido.

---

## 2. Cómo ejecutar el proyecto completo

Los comandos se ejecutan desde `Examen2026Noviembre/data-platform` salvo que se
indique otra carpeta. En este equipo `python` abre la Microsoft Store; usa `py`.

### 2.1 Preparar

```powershell
git clone https://github.com/JP-019/Examen2026Noviembre.git
cd Examen2026Noviembre\data-platform
Copy-Item .env.example .env
```

La base fuente `Venta` debe existir en la instancia local. El repositorio crea la
base `DataPlatform` con sus esquemas; no crea la fuente.

### 2.2 Crear la base de la plataforma

```powershell
sqlcmd -S localhost -E -C -f 65001 -i database\00_schemas.sql
sqlcmd -S localhost -E -C -f 65001 -i database\01_staging.sql
sqlcmd -S localhost -E -C -f 65001 -i database\02_dw.sql
sqlcmd -S localhost -E -C -f 65001 -i database\03_ml.sql
sqlcmd -S localhost -E -C -f 65001 -i database\99_verify.sql
```

`99_verify.sql` debe cerrar con 0 huérfanos y las cuatro dimensiones con su
miembro desconocido.

### 2.3 Ejecutar el ETL

```powershell
cd services\etl
py -m pip install -r requirements.txt
py -m app full
py -m app status
py -m app quality-report
cd ..\..
```

Resultado esperado: 10 tablas extraídas, 5 filas en `ready.Ventas` y en
`dw.FactVentas`, S/ 696.40 y 0 rechazos.

### 2.4 Levantar los servicios

Una terminal por servicio, en este orden:

```powershell
# Terminal 1
cd services\core-api
py -m pip install -r requirements.txt
py -m uvicorn app.main:app --port 8000

# Terminal 2
cd services\catalog
py -m uvicorn app.main:app --port 8001

# Terminal 3
cd services\ml
py -m uvicorn app.main:app --port 8002

# Terminal 4
cd services\genai
py -m uvicorn app.main:app --port 8003

# Terminal 5
cd services\alerting
py -m uvicorn app.main:app --port 8004

# Terminal 6
cd services\dashboard
py -m streamlit run app.py --server.port 8501
```

> `scripts\start_all.ps1` solo inicia el catálogo en esta versión; los demás
> servicios se abren a mano.

### 2.5 Verificar que todo responde

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/health
Invoke-RestMethod http://localhost:8001/
Invoke-RestMethod http://localhost:8002/model
Invoke-RestMethod http://localhost:8003/health
Invoke-RestMethod http://localhost:8004/health
```

### 2.6 Evaluar alertas y abrir el panel

```powershell
cd services\alerting
py -m app evaluate
cd ..\..
```

Paneles: <http://localhost:8501> (ventas) y
<http://localhost:8004/monitor> (avisos y monitoreo).

### 2.7 Prueba de punta a punta

```powershell
py tests\e2e_smoke.py
```

### 2.8 Bot de Telegram

```powershell
cd bot-telegram
npm install
Copy-Item .env.example .env
# Completar BOT_TOKEN, ADMIN_CHAT_ID, DASHBOARD_TOKEN y BOT_USERNAME
npm start
```

Panel del bot: `http://localhost:3000/?token=TU_TOKEN`. En el video no muestres
el token ni el archivo `.env`.

---

## 3. Guion cronometrado

### 0:00 – 0:40 | Presentación y arquitectura

**En pantalla:** README del repositorio y diagrama de capas.

**Narración:**

> Este proyecto construye una plataforma de datos de punta a punta sobre las
> ventas de una empresa. La fuente es SQL Server; un pipeline en Python lleva los
> datos por tres zonas de staging hasta un Data Warehouse en estrella. Sobre ese
> almacén se publican seis indicadores por API, un panel en Streamlit, un modelo
> predictivo, un asistente con consultas aprobadas y seis reglas de aviso. La
> regla central es una: solo la API y el ETL hablan con la base.

### 0:40 – 1:30 | ETL y calidad

**En pantalla:** terminales con `py -m app full` y `py -m app status`.

**Narración:**

> Empiezo por el ETL. La extracción tiene dos modos: completa e incremental por
> marca de agua, con solapamiento para absorber correcciones. Cada fila pasa por
> raw, clean y ready. En raw se conserva la copia fiel; en clean se tipa y se
> validan quince reglas de calidad; en ready se resuelven las dimensiones. Si una
> fila no cumple una regla, no se borra: va a cuarentena con su código. Aquí
> ejecuto la carga y reviso el estado.

### 1:30 – 2:15 | Data Warehouse y reconciliación

**En pantalla:** resultado de `99_verify.sql` y la tabla de reconciliación.

**Narración:**

> El Data Warehouse usa cuatro dimensiones —tiempo, producto, local y versión— y
> una tabla de hechos con grano de línea de factura. El grano de línea permite
> analizar productos y secciones; el costo es cuidar la reconciliación de
> importes. Esta consulta suma el importe en cada capa: fuente, clean, ready y
> hecho. Las cuatro coinciden en cinco filas y 696.40 soles, con cero huérfanos.
> Esa igualdad es la prueba de que el modelo no perdió ni inventó datos.

### 2:15 – 3:00 | Panel de ventas

**En pantalla:** <http://localhost:8501>, aplicar un filtro y abrir el detalle.

**Narración:**

> El panel consume solo HTTP: no toca SQL. Muestra seis indicadores, filtros por
> fecha, local, sección y producto, tendencia, comparación y detalle paginado. Si
> el periodo no tiene datos, lo dice y conserva los filtros; no muestra ceros. La
> exportación a CSV reproduce exactamente las filas filtradas. Aquí aplico un
> filtro y abro el detalle.

### 3:00 – 3:45 | Modelo predictivo

**En pantalla:** `http://localhost:8002/model` y `/metrics`.

**Narración:**

> El modelo predice ventas mensuales con división temporal, nunca aleatoria, y se
> compara contra una línea base. Con los datos reales hay un solo mes: el servicio
> responde `insufficient_data` y no publica métricas inventadas. La verificación
> del algoritmo se hizo con una serie sintética identificada, donde el error
> absoluto medio fue 38.9 frente a 480 de la línea base. Prefiero un sistema que
> reconozca su límite a uno que finja precisión.

### 3:45 – 4:25 | Asistente de lenguaje natural

**En pantalla:** pestaña Asistente del dashboard; una pregunta válida y una fuera
de alcance.

**Narración:**

> El asistente no ejecuta SQL libre. Normaliza la pregunta, la clasifica en una de
> diez intenciones aprobadas y llama al endpoint correspondiente. Cada respuesta
> incluye fuentes y si está verificada. Si la pregunta está fuera de alcance,
> responde que no hay datos. Aquí pregunto cuánto vendimos y luego algo fuera de
> alcance, para mostrar ambos comportamientos.

### 4:25 – 5:00 | Avisos, monitoreo y cierre

**En pantalla:** disparo de la evaluación y <http://localhost:8004/monitor>.

**Narración:**

> El motor evalúa seis reglas sobre ventas, modelo y calidad. Cada aviso registra
> severidad, valor observado, umbral y acción sugerida; la deduplicación evita
> repetir el mismo evento. Aquí disparo una evaluación y abro el monitoreo. En
> resumen, lo aprendido: la trazabilidad importa más que el volumen; la calidad se
> demuestra con reglas y cuarentena; una API única evita cifras duplicadas; la
> honestidad del modelo es parte del diseño; y sin documentación reproducible no
> hay entrega. Todo está en el repositorio y se levanta con los comandos de esta
> guía.

---

## 4. Lo aprendido en cinco frases

1. **La trazabilidad es el producto.** Un total sin forma de reconstruirlo no
   sirve para decidir; por eso cada fila conserva su clave y su ejecución.
2. **La calidad no se declara, se demuestra.** Quince reglas con código y una
   cuarentena visible valen más que un informe que dice "datos limpios".
3. **Un solo contrato evita cifras distintas.** Panel, asistente y avisos leen la
   misma API; ninguno recalcula por su cuenta.
4. **La honestidad es parte del modelo.** `insufficient_data` es una respuesta
   válida y preferible a una métrica inventada.
5. **Sin reproducibilidad no hay entrega.** Si otra persona no puede ejecutar el
   proyecto, el resultado no existe para efectos prácticos.

### Errores que se evitaron

| Error frecuente | Qué se hizo en su lugar |
|---|---|
| Imputar ceros o promedios | Enviar la fila a cuarentena y reportarla |
| División aleatoria en series | División temporal: entrenar con el pasado |
| Panel que suma por su cuenta | Consumir la API y replicar sus filtros |
| Asistente con SQL libre | Diez consultas aprobadas y parametrizadas |
| Publicar el token en el repo | Leerlo del entorno y excluir `.env` |

---

## 5. Después de grabar

- [ ] El video dura cinco minutos o menos.
- [ ] El audio es claro y la pantalla se lee.
- [ ] Se muestra ejecución real, no diapositivas.
- [ ] No aparecen tokens, contraseñas ni datos personales.
- [ ] Los eventos simulados se identifican como simulación.
- [ ] El cierre dice qué está funcionando y qué queda pendiente.
- [ ] Existe una copia de respaldo con capturas por si falla la red.

---

## 6. Nota sobre el alcance

El video debe decir la verdad sobre lo que no se cumplió: no hay
`docker-compose.yml`, el ambiente depende de una instancia local de SQL Server y
no hay un usuario técnico con permisos mínimos. La demo de T15 tampoco cubre el
bot de Telegram, que es un proyecto independiente y se puede mostrar aparte en
treinta segundos si sobra tiempo.
