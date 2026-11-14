# dashboard (T10)

## Responsabilidad

Presentar los KPIs, tendencias, filtros y detalle; incluye modos de chat para
ventas verificadas con `genai` y conversacion general con Ollama local. No
importa `pyodbc`: ni el dashboard ni el chat abren conexiones a SQL Server.

## Ejecucion

Con `core-api` (8000) y `genai` (8003) corriendo:

```powershell
cd services/dashboard
python -m pip install -r requirements.txt
streamlit run app.py --server.port 8501
```

Abrir <http://localhost:8501> y elegir **Asistente de ventas** en la navegacion.

La URL de GenAI se configura con `GENAI_URL` en el `.env` de la plataforma
(por defecto `http://localhost:8003`). El chat conserva el historial solo durante
la sesion del navegador y permite iniciar una conversacion nueva. El chat ofrece
modos separados: ventas verificadas con GenAI o conversacion general con Ollama
local. Las respuestas de Ollama se identifican como no verificadas y el modo
general bloquea preguntas de ventas. Ollama solo hace falta para ese modo. Si
el servicio no está iniciado, ejecuta `ollama serve` y descarga el modelo:

```powershell
ollama serve
ollama pull llama3.2:1b
```

La URL, el modelo y el timeout se pueden cambiar con `OLLAMA_URL`,
`OLLAMA_MODEL` y `OLLAMA_HTTP_TIMEOUT`.
El tablero usa un tema oscuro con KPIs, tendencia, distribucion por local y
detalle de ventas.

## Secciones

| Seccion | Contenido |
|---|---|
| Cabecera | Filas en el DW, ultima actualizacion y estado del ETL |
| KPIs | 6 tarjetas: ventas, lineas, facturas, ticket promedio, unidades, productos |
| Tendencias | Barras por mes o dia y comparacion con el periodo anterior |
| Detalle | Tabla paginada con filtros y descarga CSV |
| Asistente | Modos separados para ventas verificadas (GenAI) y consultas generales (Ollama) |

## Indice de funciones

| Archivo | Funcion | Que hace |
|---|---|---|
| `api_client.py` | `CoreApi._get` | GET con timeout, limpieza de filtros y errores tipados |
| `api_client.py` | `CoreApi.health` | Estado del servicio y de los datos |
| `api_client.py` | `CoreApi.filtros` | Valores disponibles para los selectores |
| `api_client.py` | `CoreApi.kpis` | KPIs del periodo filtrado |
| `api_client.py` | `CoreApi.tendencias` | Serie por dia o mes |
| `api_client.py` | `CoreApi.detalle` | Detalle paginado |
| `app.py` | `_sidebar` | Construye los filtros y persiste la seleccion |
| `app.py` | `_kpi_cards` | Tarjetas de KPIs |
| `app.py` | `_seccion_tendencias` | Grafico y comparacion |
| `app.py` | `_seccion_detalle` | Tabla paginada y CSV |
| `app.py` | `main` | Orquesta estados: cargando, error, sin datos, ok |
| `genai_client.py` | `GenAiClient.ask` | Consulta `/ask` con timeout y valida el contrato |
| `ollama_client.py` | `OllamaClient.ask` | Consulta Ollama local para conversación general |
| `pages/1_Asistente.py` | pagina Asistente de ventas | Historial de chat, respuestas y fuentes |

## Estados cubiertos

1. **API caida:** mensaje con el comando para arrancar `core-api`.
2. **Periodo sin datos:** aviso, sin tarjetas en cero ni graficos vacios.
3. **Error de validacion:** se muestra el detalle devuelto por la API.
4. **Datos desactualizados:** la fecha sale de la auditoria del ETL, no del reloj.
5. **GenAI u Ollama caido:** el chat muestra un error claro y conserva la conversacion existente.

## Definicion de terminado

- [x] KPIs validados contra `dw.FactVentas` (696.40).
- [x] Filtros de fecha + 3 dimensiones (local, seccion, producto).
- [x] Tabla de detalle con paginacion y descarga.
- [x] Sin conexion del dashboard a SQL Server.
- [x] Chat conectado al servicio GenAI, con fuentes y errores visibles.
- [ ] Capturas en `documentation/evidencias/` (requiere navegador).
