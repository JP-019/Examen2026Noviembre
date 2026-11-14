# Manual de instalacion, despliegue, operacion y uso

- **Tarea:** T14
- **Alcance:** ambiente local Windows con SQL Server, Python 3.12 y Git
- **Audiencia:** quien instala, opera o recupera la plataforma, y quien la usa

---

## 1. Instalacion

### 1.1 Requisitos

| Componente | Version | Verificacion |
|---|---|---|
| SQL Server | 2019+ | `sqlcmd -S localhost -E -C -Q "SELECT @@VERSION"` |
| Python | 3.12+ | `python --version` |
| Git | 2.x | `git --version` |
| Navegador | actual | para dashboard y Swagger |
| Docker | opcional | via contenedor no ejecutada en este equipo |

Si `python` abre la Microsoft Store, usar la ruta completa del interprete
instalado. Verificar tambien el driver `ODBC Driver 18 for SQL Server` en
**Origenes de datos ODBC**.

### 1.2 Obtener el codigo y configurar

```powershell
git clone <url-del-repositorio> data-platform
cd data-platform
Copy-Item .env.example .env
```

Editar `.env` solo si cambian servidor, base o autenticacion. `.env` esta
ignorado por git; `.env.example` no lleva credenciales.

### 1.3 Crear la base de la plataforma

```powershell
sqlcmd -S localhost -E -C -f 65001 -i database/00_schemas.sql
sqlcmd -S localhost -E -C -f 65001 -i database/01_staging.sql
sqlcmd -S localhost -E -C -f 65001 -i database/02_dw.sql
sqlcmd -S localhost -E -C -f 65001 -i database/03_ml.sql
sqlcmd -S localhost -E -C -f 65001 -i database/99_verify.sql
```

`-C` acepta el certificado autofirmado del SQL Server local. `-f 65001` lee los
scripts como UTF-8.

### 1.4 Instalar dependencias por servicio

```powershell
cd services/etl          ; python -m pip install -r requirements.txt ; cd ../..
cd services/catalog      ; python -m pip install -r requirements.txt ; cd ../..
cd services/core-api     ; python -m pip install -r requirements.txt ; cd ../..
cd services/dashboard    ; python -m pip install -r requirements.txt ; cd ../..
cd services/ml           ; python -m pip install -r requirements.txt ; cd ../..
cd services/genai        ; python -m pip install -r requirements.txt ; cd ../..
cd services/alerting     ; python -m pip install -r requirements.txt ; cd ../..
```

Alternativa recomendada: un entorno virtual por servicio
(`python -m venv .venv`, `.\.venv\Scripts\Activate.ps1`).

### 1.5 Primera carga

```powershell
cd services/etl
python -m app full
python -m app status
cd ../..
```

Resultado esperado: 10 tablas extraidas, 5 lineas en `ready.Ventas` y en
`dw.FactVentas`, S/ 696.40, 0 rechazos.

---

## 2. Despliegue local

Cada servicio es un proceso independiente. Orden y puertos:

| Orden | Servicio | Carpeta | Comando | Puerto |
|---|---|---|---|---|
| 1 | API de KPIs | `services/core-api` | `uvicorn app.main:app --port 8000` | 8000 |
| 2 | Catalogo | `services/catalog` | `uvicorn app.main:app --port 8001` | 8001 |
| 3 | ML | `services/ml` | `uvicorn app.main:app --port 8002` | 8002 |
| 4 | GenAI | `services/genai` | `uvicorn app.main:app --port 8003` | 8003 |
| 5 | Alertas | `services/alerting` | `uvicorn app.main:app --port 8004` | 8004 |
| 6 | Dashboard | `services/dashboard` | `streamlit run app.py --server.port 8501` | 8501 |

Verificacion rapida:

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/health
Invoke-RestMethod http://localhost:8001/
Invoke-RestMethod http://localhost:8002/model
Invoke-RestMethod http://localhost:8003/health
Invoke-RestMethod http://localhost:8004/health
```

### 2.1 Despliegue con contenedores (opcional)

`deployment/` incluye la definicion para contenedores, pero **no se ejecuto** en
este equipo porque Docker no esta instalado. La via soportada y verificada es la
local. Si se usa contenedor, montar `.env` y exponer los mismos puertos.

### 2.2 Actualizar el catalogo

```powershell
python scripts/build_index.py
```

Se ejecuta despues de cambiar `catalog/platform.json` (servicios, funciones,
rutas o estado de tareas). `INDEX.md` se genera, no se edita a mano.

---

## 3. Operacion

### 3.1 Rutina diaria

```powershell
cd services/etl
python -m app incremental      # trae solo la ventana nueva
python -m app status           # ultimas ejecuciones y volumen
```

Luego, con `core-api` y `ml` arriba:

```powershell
cd services/alerting
python -m app evaluate         # evalua reglas y registra alertas nuevas
python -m app alerts           # revisa el estado
```

Monitoreo:

- Pipeline y calidad: <http://localhost:8000/api/v1/monitor>
- Alertas y modelo: <http://localhost:8004/monitor>
- Estado de la plataforma: <http://localhost:8001/>

### 3.2 Frecuencia

| Proceso | Frecuencia | Naturaleza |
|---|---|---|
| ETL | diario / manual | batch, no tiempo real |
| Alertas | tras el ETL o por cron | bajo demanda idempotente |
| Modelo | mensual o al acumular historia | batch |
| Dashboard | bajo demanda | lectura |

### 3.3 Logs y evidencia

| Que | Donde |
|---|---|
| Corridas del ETL | `audit.etl_execution` (`status`, `error_detail`) |
| Watermark | `audit.etl_watermark` |
| Rechazos | `quarantine.rejected_row` |
| Linaje | `audit.row_lineage` |
| Experimentos ML | `audit.ml_experiment` + `services/ml/artifacts/` |
| Alertas y entregas | `services/alerting/data/alerts.db` |
| Reporte de calidad | `documentation/evidencias/T06_calidad_reconciliacion.md` |

```powershell
sqlcmd -S localhost -E -C -d DataPlatform -W -s "|" -Q "SET NOCOUNT ON; SELECT TOP 10 execution_id, pipeline_name, status, rows_read, rows_rejected, start_time FROM audit.etl_execution ORDER BY execution_id DESC"
```

---

## 4. Manual de usuario

### 4.1 Dashboard

1. Abrir <http://localhost:8501>.
2. Elegir rango de fechas y, opcionalmente, local, seccion o producto.
3. Leer las 6 tarjetas: ventas, lineas, facturas, ticket promedio, unidades y productos.
4. Ver la tendencia mensual y la comparacion entre periodos.
5. Descargar el detalle filtrado en CSV.

Si la API no responde, el tablero muestra un mensaje de error; no inventa datos.

### 4.2 Asistente

```powershell
curl -X POST http://localhost:8003/ask -H "Content-Type: application/json" -d "{\"pregunta\":\"ventas por local\"}"
```

Cada respuesta trae `respuesta`, `datos`, `fuentes` y `grounded`. Si `grounded`
es `false`, no hay datos que respalden la respuesta.

### 4.3 Alertas

1. Abrir <http://localhost:8004/monitor>.
2. Revisar severidad, valor observado, umbral y accion sugerida.
3. Reconocer la alerta: `POST /alerts/{id}/ack`.
4. Para probar el canal sin generar una alerta real: `POST /alerts/simulate`.

---

## 5. Recuperacion

### 5.1 Reiniciar el pipeline

```powershell
cd services/etl
python -m app status
python -m app incremental
```

Si la ultima corrida quedo `FAILED`, el watermark **no avanzo**: repetir
`incremental` reprocesa la ventana. Si el problema fue un dato, corregir la fuente
o la regla y ampliar la ventana:

```powershell
python -m app incremental --overlap-days 7
```

### 5.2 Restaurar el ambiente desde cero

> Destructivo: borra la base `DataPlatform` completa. Solo en desarrollo.

```powershell
sqlcmd -S localhost -E -C -f 65001 -i database/98_reset.sql
sqlcmd -S localhost -E -C -f 65001 -i database/00_schemas.sql
sqlcmd -S localhost -E -C -f 65001 -i database/01_staging.sql
sqlcmd -S localhost -E -C -f 65001 -i database/02_dw.sql
sqlcmd -S localhost -E -C -f 65001 -i database/03_ml.sql
cd services/etl
python -m app full
```

La base fuente `Venta` **no** se toca: es de solo lectura.

### 5.3 Problemas frecuentes

| Sintoma | Causa probable | Solucion |
|---|---|---|
| `No se pudo conectar con la API` | `core-api` caido o puerto ocupado | Levantarlo en 8000 y revisar el puerto |
| API responde 503 | SQL Server caido o `.env` incorrecto | Verificar `sqlcmd` y las variables `DW_*` |
| `insufficient_data` en ML | Menos de 8 meses con ventas | Es correcto; acumular historia |
| `/predict` responde 409 | No hay modelo entrenado | Ejecutar `/train` cuando haya periodos |
| Alerta duplicada no aparece | `event_key` ya registrado | Es el anti-duplicado esperado |
| Rechazos en cuarentena | Dato invalido en la fuente | Corregir y reprocesar la ventana |
| `python` abre la Store | Stub de Windows | Usar la ruta completa del interprete |
| Mojibake en consola | Codificacion de PowerShell | `$env:PYTHONIOENCODING="utf-8"`; los datos son correctos |

### 5.4 Respaldo

- **Base:** backup de `DataPlatform` con SQL Server Management Studio o
  `BACKUP DATABASE DataPlatform TO DISK = '...'`.
- **Artefactos ML:** copiar `services/ml/artifacts/` (ignorados por git).
- **Alertas:** copiar `services/alerting/data/alerts.db` (ignorado por git).
- **Codigo y documentacion:** el repositorio git.

---

## 6. Seguridad

1. `.env` fuera del repositorio; `.env.example` sin credenciales.
2. Solo `core-api` y el ETL acceden a SQL Server.
3. Todo el SQL es parametrizado; las dimensiones salen de una whitelist.
4. El asistente no acepta SQL ni usa APIs externas.
5. No se muestran tokens ni contrasenas en la demo.
6. Revisar el historial antes de publicar:

```powershell
git log -p -- .env
git log -p -S "password" -- .
git log -p -S "PWD=" -- .
```

Ninguno debe devolver contenido real.

---

## 7. Checklist de instalacion

- [ ] SQL Server responde y la base `Venta` existe.
- [ ] Python 3.12+ y driver ODBC 18 instalados.
- [ ] `.env` creado desde `.env.example`.
- [ ] Los 4 scripts SQL ejecutados sin error.
- [ ] `99_verify.sql` con 0 huerfanos.
- [ ] `python -m app full` con 5 filas y S/ 696.40.
- [ ] Los 6 servicios levantan y responden health.
- [ ] Dashboard abre con 6 KPIs.
- [ ] `POST /alerts/evaluate` genera 3 alertas y la segunda vez 0 nuevas.
- [ ] Pruebas de `tests/` en OK.
