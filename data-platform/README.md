# Data Platform - Ingenieria de Datos y Analitica Inteligente

Proceso de negocio: **VENTAS**. Stack: SQL Server + Python + FastAPI + Streamlit.

Estado actual: **T02 a T14 cerradas; T01 y T15 parciales**. Arquitectura de
microservicios, staging, modelo dimensional, ETL con calidad e idempotencia,
catalogo de plataforma, API de KPIs, dashboard web, servicio de ML, asistente
GenAI y motor de alertas verificados, con documentacion completa y las 12 pruebas
ejecutadas. T01 queda parcial porque el despliegue con Docker no se ejecuto (Docker
no esta instalado); T15 queda parcial porque falta la grabacion del video y el
ensayo, a cargo del equipo.

## Indice

- **Indice raiz:** [`INDEX.md`](INDEX.md) (generado desde `catalog/platform.json`).
- **Indice vivo:** `services/catalog` en <http://localhost:8001/index.md>.
- **Decisiones:** `documentation/adr/`.

## Estructura

```
data-platform/
  documentation/          Arquitectura, ADR, staging, modelo, calidad y evidencias
  database/               Scripts SQL de esquemas, staging y DW
  services/               Un microservicio por carpeta
    etl/                  Extraccion, calidad, staging y DW (T05, T06)
    catalog/              Indice vivo de servicios y rutas (T03)
    core-api/             API de KPIs (T09, implementado)
    dashboard/            Dashboard Streamlit (T10, implementado)
    ml/                   Modelo predictivo (T11, implementado)
    genai/                Asistente con consultas aprobadas (T12, implementado)
    alerting/             Alertas y monitoreo (T13, implementado)
  catalog/                Manifiesto de la plataforma (platform.json)
  scripts/                Generador de indice y arranque local
  tests/                  Pruebas y evidencias (T14)
  deployment/             Despliegue local y contenedores
  INDEX.md                Indice generado
  README.md               Este archivo
```

## Arranque paso a paso (de cero a demo)

Los comandos se ejecutan desde la raiz `data-platform` salvo que se indique otra
carpeta. Cada servicio usa un puerto fijo.

### 0. Preparar el entorno

```powershell
Copy-Item .env.example .env
# Editar .env solo si la instancia o la base cambian.
# .env no se versiona y no debe contener credenciales en el repositorio.

python --version        # debe ser 3.12+
sqlcmd -S localhost -E -C -Q "SELECT @@VERSION"
```

> Si `python` abre la Microsoft Store, usar la ruta completa del interprete
> instalado (por ejemplo `C:\Users\<usuario>\AppData\Local\Programs\Python\Python312\python.exe`).

### 1. Crear la base de la plataforma

```powershell
sqlcmd -S localhost -E -C -f 65001 -i database/00_schemas.sql
sqlcmd -S localhost -E -C -f 65001 -i database/01_staging.sql
sqlcmd -S localhost -E -C -f 65001 -i database/02_dw.sql
sqlcmd -S localhost -E -C -f 65001 -i database/03_ml.sql
sqlcmd -S localhost -E -C -f 65001 -i database/99_verify.sql
```

`99_verify.sql` debe cerrar con 0 huerfanos y las 4 dimensiones con miembro
desconocido.

### 2. Instalar dependencias y ejecutar el ETL

```powershell
cd services/etl
python -m pip install -r requirements.txt
python -m app full
python -m app status
cd ../..
```

Resultado esperado con la fuente actual: 10 tablas extraidas, 5 lineas en
`ready.Ventas` y en `dw.FactVentas`, S/ 696.40 y 0 rechazos.

### 3. Levantar los servicios (una terminal por servicio)

| Terminal | Carpeta | Comando | URL |
|---|---|---|---|
| 1 | `services/core-api` | `uvicorn app.main:app --port 8000` | <http://localhost:8000/docs> |
| 2 | `services/catalog` | `uvicorn app.main:app --port 8001` | <http://localhost:8001/index.md> |
| 3 | `services/ml` | `uvicorn app.main:app --port 8002` | <http://localhost:8002/docs> |
| 4 | `services/genai` | `uvicorn app.main:app --port 8003` | <http://localhost:8003/docs> |
| 5 | `services/alerting` | `uvicorn app.main:app --port 8004` | <http://localhost:8004/monitor> |
| 6 | `services/dashboard` | `streamlit run app.py --server.port 8501` | <http://localhost:8501> |

Antes de cada uno, instalar sus dependencias:

```powershell
cd services/<servicio>
python -m pip install -r requirements.txt
```

Orden recomendado: `core-api` primero (los demas dependen de el), luego `ml`,
`genai`, `alerting`, `catalog` y por ultimo `dashboard`.

### 4. Verificar que todo responde

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/health
Invoke-RestMethod http://localhost:8001/
Invoke-RestMethod http://localhost:8002/model
Invoke-RestMethod http://localhost:8003/health
Invoke-RestMethod http://localhost:8004/health
```

### 5. Recorrido funcional

1. Abrir el dashboard en <http://localhost:8501>: 6 KPIs, filtros, tendencia y detalle.
2. Abrir el monitoreo en <http://localhost:8004/monitor>.
3. Evaluar alertas: `POST /alerts/evaluate` (o `python -m app evaluate` desde `services/alerting`).
4. Abrir **Asistente de ventas** en la navegación del dashboard. El modo de ventas consulta GenAI;
   el modo general usa Ollama local y bloquea preguntas de ventas.

### 6. Ejecutar las pruebas

```powershell
python tests/smoke_core_api.py
python tests/smoke_dashboard.py
python tests/test_dashboard_app.py
python tests/test_ml_model.py
python tests/test_alerting_rules.py
python tests/smoke_alerting.py
python tests/test_endpoint_access.py
python tests/test_tls_config.py
python tests/test_genai_catalog.py
python tests/test_dashboard_genai_client.py
python tests/test_dashboard_ollama_client.py
```

El detalle de cada prueba, con resultado esperado y obtenido, esta en
[`documentation/plan_pruebas.md`](documentation/plan_pruebas.md).

## Requisitos

| Requisito | Version | Verificacion |
|---|---|---|
| SQL Server | 2019+ | `sqlcmd -S localhost -E -C -Q "SELECT @@VERSION"` |
| Python | 3.12+ | `python --version` |
| Git | 2.x | `git --version` |
| Docker | opcional | solo para la via contenedor (no instalado en este equipo) |

## Base de datos

La fuente es la base `Venta` (solo lectura, ya existente en la instancia local).
La plataforma vive en la base `DataPlatform` con esquemas `raw`, `clean`, `ready`,
`dw`, `audit` y `quarantine`.

### Crear / recrear desde cero

```powershell
cd data-platform
sqlcmd -S localhost -E -C -f 65001 -i database/00_schemas.sql
sqlcmd -S localhost -E -C -f 65001 -i database/01_staging.sql
sqlcmd -S localhost -E -C -f 65001 -i database/02_dw.sql
sqlcmd -S localhost -E -C -f 65001 -i database/03_ml.sql
```

`-C` acepta el certificado autofirmado del SQL Server local.
`-f 65001` interpreta los scripts como UTF-8.

### Verificar el resultado

```powershell
sqlcmd -S localhost -E -C -f 65001 -i database/99_verify.sql
```

Debe mostrar: 0 huerfanos, miembros desconocidos en las 4 dimensiones y
`DimTiempo` cubriendo 2000-01-01 a 2035-12-31.

## Pipeline ETL

```powershell
cd services/etl
python -m pip install -r requirements.txt
python -m app full                # carga inicial
python -m app incremental         # por watermark
python -m app idempotency-check   # prueba de reejecucion
python -m app quality-report      # calidad y reconciliacion
python -m app status              # ultimas ejecuciones
```

`raw` es append-only por diseno: crece en cada extraccion. La idempotencia se
garantiza en `clean`, `ready` y `dw` por clave de negocio.

## Indice vivo

```powershell
cd services/catalog
python -m pip install -r requirements.txt
uvicorn app.main:app --port 8001
```

| Recurso | URL |
|---|---|
| Indice legible | <http://localhost:8001/index.md> |
| Indice JSON | <http://localhost:8001/index> |
| Mapa de carpetas | <http://localhost:8001/map> |
| Rutas de la plataforma | <http://localhost:8001/routes> |
| Swagger | <http://localhost:8001/docs> |

Si cambia un servicio, se actualiza `catalog/platform.json` y se regenera:
`python scripts/build_index.py`.

## API de KPIs (T09)

```powershell
cd services/core-api
python -m pip install -r requirements.txt
uvicorn app.main:app --port 8000
```

| Recurso | URL |
|---|---|
| Swagger | <http://localhost:8000/docs> |
| Salud | <http://localhost:8000/api/v1/health> |
| KPIs | <http://localhost:8000/api/v1/kpis> |
| Tendencias | <http://localhost:8000/api/v1/tendencias?granularidad=mes> |
| Detalle | <http://localhost:8000/api/v1/detalle?page=1&page_size=25> |
| Filtros | <http://localhost:8000/api/v1/filtros> |

Prueba de humo (con la API arriba):

```powershell
python tests/smoke_core_api.py
```

## Dashboard (T10)
```powershell
cd services/dashboard
python -m pip install -r requirements.txt
streamlit run app.py --server.port 8501
```

Abrir <http://localhost:8501>. El tablero consume solo `core-api`; nunca se
conecta a SQL Server. Pruebas: `python tests/smoke_dashboard.py` y
`python tests/test_dashboard_app.py`.

## Modelo ML (T11)

```powershell
cd services/ml
python -m pip install -r requirements.txt
python -m app train            # entrena, evalua y versiona
python -m app status
uvicorn app.main:app --port 8002
```

Con la fuente actual (un solo mes con ventas) el servicio informa
`insufficient_data` y no publica metricas. Es el comportamiento correcto: no se
evalua con datos de entrenamiento ni se inventan cifras. El algoritmo se verifica
con una serie sintetica en `tests/test_ml_model.py`.

## Asistente GenAI (T12)

```powershell
cd services/genai
python -m pip install -r requirements.txt
uvicorn app.main:app --port 8003
```

Con `core-api` arriba. Preguntar:

```powershell
python -m app ask "ventas por local"
python -m app test            # 10 pruebas documentadas
```

El asistente no ejecuta SQL libre y no inventa cifras: clasifica la pregunta en
un catalogo de consultas aprobadas, llama a `core-api` y devuelve `fuentes` y
`grounded`. Si la pregunta esta fuera de alcance, responde sin datos.

El dashboard también ofrece el modo general con Ollama local. Para habilitarlo,
instala Ollama, ejecuta `ollama serve` si el servicio aún no está activo y descarga
el modelo con `ollama pull llama3.2:1b`. El modo general no consulta el DW ni se
debe usar para cifras de ventas.

## Alertas y monitoreo (T13)

```powershell
cd services/alerting
python -m pip install -r requirements.txt
uvicorn app.main:app --port 8004
```

Con `core-api` (8000) y `ml` (8002) arriba:

```powershell
python -m app evaluate        # evalua las 6 reglas
python -m app alerts          # alertas registradas
python -m app simulate        # alerta de prueba marcada como simulada
```

| Vista | URL |
|---|---|
| Monitoreo | <http://localhost:8004/monitor> |
| Monitoreo JSON | <http://localhost:8004/monitor.json> |
| Alertas | <http://localhost:8004/alerts> |
| Reglas y umbrales | <http://localhost:8004/rules> |

Las metricas salen de `core-api` y del servicio `ml`; el registro de alertas y
entregas vive en `services/alerting/data/alerts.db` (SQLite, fuera del repo). El
`event_key` unico evita notificar dos veces el mismo evento. El canal es la vista
`/monitor`, con entrega registrada por alerta.

### Reiniciar el ambiente (desarrollo)

```powershell
sqlcmd -S localhost -E -C -f 65001 -i database/98_reset.sql
# luego repetir los tres scripts de creacion
```

> `98_reset.sql` borra la base `DataPlatform` completa. No ejecutar en la demo.

## Documentacion clave

| Documento | Contenido |
|---|---|
| `documentation/requerimientos.md` | Requerimientos funcionales y no funcionales |
| `documentation/arquitectura.md` | Alcance, capas, diagrama, stack, frecuencia |
| `documentation/adr/` | 7 decisiones de arquitectura justificadas |
| `documentation/fuente_datos.md` | ERD, claves, diccionario y perfilado de la fuente |
| `documentation/staging.md` | Zonas, auditoria, cuarentena y linaje |
| `documentation/modelo_dimensional.md` | Grano, dimensiones, medidas y SCD |
| `documentation/calidad_datos.md` | Catalogo DQ-001 a DQ-015 |
| `documentation/etl.md` | Extraccion, transformacion, carga y recuperacion |
| `documentation/api_contratos.md` | APIs, contratos y errores |
| `documentation/ml.md` | Modelo, evaluacion temporal y limites |
| `documentation/genai.md` | Consultas aprobadas y anti-alucinacion |
| `documentation/alertas.md` | Reglas, anti-duplicado y monitoreo |
| `documentation/plan_pruebas.md` | Las 12 pruebas con evidencia |
| `documentation/manual.md` | Instalacion, operacion y recuperacion |
| `documentation/demo.md` | Guion del video y checklist de demo |

## Reglas del proyecto

1. Un solo proceso de negocio: ventas.
2. El frontend nunca se conecta directo a SQL Server; siempre pasa por la API.
3. Los KPIs descriptivos salen del Data Warehouse.
4. Ningun modelo se evalua con datos de entrenamiento.
5. La IA no inventa cifras: solo consultas aprobadas.
6. El batch nocturno no es tiempo real.

## Seguridad de los servicios HTTP

`core-api`, `ml`, `genai` y `alerting` aceptan solicitudes solo desde direcciones
de loopback; una solicitud desde otra direccion recibe HTTP 403. Esta proteccion
es para desarrollo local y no reemplaza la autenticacion en un despliegue. No
exponer estos servicios directamente a una red o a Internet; un despliegue remoto
requiere autenticacion, autorizacion, TLS y limites de solicitudes en un proxy
confiable. Un proxy local sin autenticacion puede hacer que las solicitudes
remotas parezcan locales y eludir esta restriccion.

La validacion de certificados SQL Server se exige por defecto para servidores
remotos. El valor `auto` solo confia en un certificado autofirmado cuando el
servidor esta configurado como `localhost`, `127.0.0.1` o `::1`. No activar
`DW_TRUST_SERVER_CERTIFICATE=yes` para una conexion remota.

## Credenciales

No hay secretos en el repositorio. En desarrollo se usa autenticacion de Windows.
Si se incorporan usuarios tecnicos, las credenciales se leen de `.env`,
versionado solo como `.env.example`. El historial se revisa con
`git log -p -- .env` (no debe devolver contenido) y con busqueda de patrones
`password`, `secret`, `token` y cadenas de conexion.
