# Plataforma Integral de Ingeniería de Datos y Analítica Inteligente: informe final

| Campo | Valor |
|---|---|
| Proyecto | Plataforma Integral de Ingeniería de Datos y Analítica Inteligente |
| Proceso de negocio | Ventas |
| Metodología | Scrum adaptado a tres días con buffer |
| Periodo | 11 al 14 de noviembre de 2026 |
| Repositorio | `Examen2026Noviembre` |
| Versión del informe | 1.0 |

---

## Introducción

El proyecto consistió en construir una plataforma de datos de punta a punta
sobre el proceso de ventas de una empresa minorista. El trabajo abarcó la
extracción desde el sistema transaccional, la preparación de los datos en zonas
de staging, la carga de un Data Warehouse dimensional, la publicación de
indicadores por medio de una API, un panel web, un modelo predictivo, un
asistente de lenguaje natural y un motor de avisos.

La entrega se complementa con un proyecto de ejemplo independiente: un bot de
Telegram para la gestión de pedidos y reservas de un restaurante, con su propio
panel web de administración.

El informe describe qué se construyó, con qué decisiones técnicas, qué resultados
se obtuvieron y qué queda pendiente. Todas las cifras provienen de ejecuciones
reales registradas en la carpeta de evidencias del repositorio; no se reportan
resultados no medidos.

---

## Objetivos

### Objetivo general

Diseñar e implementar una plataforma de datos reproducible que permita analizar
las ventas con indicadores confiables, predicciones honestas, consultas en
lenguaje natural y avisos automáticos, sin que ningún consumidor acceda
directamente a la base transaccional.

### Objetivos específicos

- Preparar un ambiente reproducible con la fuente de datos y los esquemas
  separados de staging y Data Warehouse.
- Documentar el inventario, el modelo entidad-relación, el diccionario y los
  indicadores del proceso de ventas.
- Implementar un ETL con zonas de staging, auditoría, cuarentena e idempotencia.
- Construir un modelo dimensional en esquema estrella y reconciliar sus totales
  con la fuente.
- Publicar los indicadores mediante una API y un panel web con filtros,
  tendencias y detalle exportable.
- Entrenar y evaluar un modelo predictivo con línea base y división temporal.
- Implementar un asistente con consultas aprobadas que no ejecute SQL libre.
- Generar avisos automáticos con deduplicación y una vista de monitoreo.
- Documentar, probar y demostrar la solución de punta a punta.

---

## 1. Marco del proyecto

### 1.1 Metodología y roles

Se aplicó Scrum con sprints comprimidos y un buffer final. La tabla 1 resume los
roles y las tareas asignadas.

Tabla 1

*Roles del equipo y responsabilidades*

| Rol | Responsabilidad | Tareas |
|---|---|---|
| Product Owner | Alcance, indicadores y prioridad | Aprobación del backlog |
| Scrum Master | Ceremonias, desbloqueo y tiempos | T03 y coordinación |
| Data Engineer | Fuente, staging, ETL y calidad | T01, T02, T04, T05, T06 |
| DW / BI Developer | Modelo, API y panel | T03, T07, T08, T09, T10 |
| ML Engineer | Modelo predictivo y métricas | T11 |
| GenAI / Automation | Asistente y avisos | T12, T13 |
| QA / Documentación | Documentación, pruebas y demo | T14, T15 |

### 1.2 Sprints y ceremonias

Tabla 2

*Calendario de sprints*

| Sprint | Fecha | Meta | Tareas |
|---|---|---|---|
| S0 Fundaciones | 11 de noviembre | Repositorio, fuente y arquitectura | T01, T02, T03 |
| S1 Datos confiables | 12 de noviembre | ETL, calidad y Data Warehouse | T04 a T08 |
| S2 Analítica inteligente | 13 de noviembre | Panel, modelo, asistente y avisos | T09 a T13 |
| S3 Cierre y demo | 14 de noviembre | Documentación, pruebas y ensayo | T14, T15 |

Se realizaron las ceremonias previstas: planificación al inicio de cada sprint,
reunión diaria, revisión con evidencia y retrospectiva. La regla de recorte no
fue necesaria, salvo en las dos tareas que se explican en la sección 8.

---

## 2. Arquitectura de la solución

### 2.1 Capas

La solución se organiza en capas con responsabilidades separadas:

1. **Fuente:** base transaccional `Venta` en SQL Server.
2. **Staging:** zonas `raw`, `clean` y `ready`, con auditoría y cuarentena.
3. **Data Warehouse:** esquema estrella con dimensiones y una tabla de hechos.
4. **Servicios:** API de indicadores, panel, modelo, asistente, avisos y
   catálogo.
5. **Consumo:** navegador del usuario y bot de Telegram como proyecto de ejemplo.

La regla de oro del proyecto es que **solo la API y el ETL hablan con SQL
Server**. El panel y el asistente consumen HTTP.

### 2.2 Stack tecnológico

Tabla 3

*Tecnologías utilizadas*

| Componente | Herramienta |
|---|---|
| Motor de datos | SQL Server 2025 local |
| ETL | Python 3.12, pyodbc y pandas |
| API | FastAPI, Uvicorn y Pydantic |
| Panel | Streamlit y Plotly |
| Modelo predictivo | scikit-learn |
| Asistente | Capa determinista de consultas aprobadas y modelo local opcional |
| Avisos | Python con almacenamiento SQLite y vista de monitoreo |
| Bot de ejemplo | Node.js, Express y API de Telegram |
| Versionado | Git |

### 2.3 Decisiones de arquitectura

Tabla 4

*Decisiones registradas*

| Documento | Decisión |
|---|---|
| ADR-001 | Usar SQL Server con la base `Venta` como fuente |
| ADR-002 | Separar las capas por esquemas en una instancia local |
| ADR-003 | Extracción incremental por marca de agua con idempotencia |
| ADR-004 | Modelo estrella con granularidad de línea de factura |
| ADR-005 | API como única puerta de lectura del Data Warehouse |
| ADR-006 | Asistente con consultas aprobadas, sin SQL libre |
| ADR-007 | Microservicios desplegables de forma independiente |

---

## 3. Gestión y calidad de datos

### 3.1 Fuente y staging

La fuente tiene diez tablas del proceso de ventas. El staging conserva una copia
fiel en `raw`, aplica conversiones y validaciones en `clean`, y deja los datos
integrados en `ready`. Cada fila preparada mantiene su clave de negocio y el
identificador de ejecución que permite reconstruir su linaje.

La tabla de auditoría registra, por ejecución, el origen, el destino, las filas
leídas, insertadas, actualizadas y rechazadas, además del estado y el detalle del
error.

### 3.2 Reglas de calidad

Se catalogaron quince reglas de calidad, con identificador, condición y acción.
Las filas que no cumplen una regla se derivan a cuarentena en lugar de
descartarse en silencio. Las medidas nunca se imputan con cero, porque eso
distorsionaría los indicadores.

### 3.3 Modelo dimensional y reconciliación

El modelo usa cuatro dimensiones: tiempo, producto, local y versión. La tabla de
hechos conserva la clave natural y usa el miembro desconocido con clave cero
cuando no puede resolver una dimensión.

Tabla 5

*Reconciliación entre capas*

| Capa | Filas | Importe |
|---|---|---|
| Fuente `Venta.dbo.Factura_Detalle` | 5 | S/ 696.40 |
| `clean.FacturaDetalle` | 5 | S/ 696.40 |
| `ready.Ventas` | 5 | S/ 696.40 |
| `dw.FactVentas` | 5 | S/ 696.40 |

Los huérfanos en la tabla de hechos son cero y no quedaron diferencias sin
justificar.

---

## 4. Analítica y servicios

### 4.1 API de indicadores

La API expone seis endpoints de negocio, además del estado y el monitoreo. Usa
consultas parametrizadas, una lista permitida de dimensiones y un límite máximo
de paginación de doscientas filas. Los errores de base se devuelven como errores
explícitos.

### 4.2 Panel web

El panel muestra seis indicadores, filtros por fecha y tres dimensiones,
tendencia histórica, comparación entre periodos, agrupados, tabla de detalle
paginada y exportación a CSV. También informa la fecha de última actualización
tomada de la auditoría del ETL.

### 4.3 Modelo predictivo

El modelo se entrenó con división temporal, nunca aleatoria, y se comparó contra
una línea base. Con los datos reales existe un solo mes, por lo que el servicio
responde que los datos son insuficientes y no publica métricas inventadas. La
verificación del algoritmo se realizó con una serie sintética identificada como
tal, en la que el error absoluto medio fue de 38.9 frente a 480.0 de la línea
base.

### 4.4 Asistente de lenguaje natural

El asistente normaliza la pregunta, la clasifica en una de las diez intenciones
aprobadas y consulta el endpoint correspondiente de la API. Cada respuesta
incluye las fuentes y un indicador de verificabilidad. Cuando la pregunta está
fuera de alcance, responde que no hay datos. El modelo de lenguaje no ejecuta SQL
ni genera cifras.

### 4.5 Avisos y monitoreo

El motor evalúa seis reglas sobre los indicadores, el estado del modelo y las
filas rechazadas. Cada aviso incluye severidad, valor observado, umbral y acción
sugerida. La deduplicación por clave de evento evita notificaciones repetidas y
la vista de monitoreo integra el estado del pipeline, del modelo y de los avisos.

---

## 5. Proyecto de ejemplo: bot de Telegram

El repositorio incluye un bot de Telegram para el restaurante "El Gordo",
desarrollado en Node.js con Express. Permite consultar el menú, armar un
carrito, confirmar pedidos de delivery o retiro, solicitar reservas y recibir
avisos de cambio de estado.

El administrador dispone de comandos para consultar pedidos y de un panel web con
actualización automática, filtros, cambio de estado y exportación a Excel y CSV.
El bot no consume el Data Warehouse ni la API de indicadores: es un proyecto
independiente que se entrega como ejemplo de integración con un canal de
mensajería.

---

## 6. Pruebas y resultados

Tabla 6

*Pruebas de la rúbrica*

| N.º | Prueba | Resultado |
|---|---|---|
| 1 | Carga inicial | Correcta |
| 2 | Carga incremental | Correcta |
| 3 | Idempotencia | Correcta |
| 4 | Nulos y duplicados | Correcta |
| 5 | Integridad referencial | Correcta |
| 6 | Recuperación ante falla | Correcta |
| 7 | Reconciliación entre capas | Correcta |
| 8 | Panel web | Correcta |
| 9 | Modelo predictivo | Correcta |
| 10 | Asistente, diez de diez | Correcta |
| 11 | Avisos, disparo y deduplicación | Correcta |
| 12 | Flujo de punta a punta | Correcta |

La prueba de recuperación demuestra que una falla de conexión no avanza la marca
de agua y que el reintento termina con los conteos intactos. La prueba de punta a
punta recorre la fuente, el Data Warehouse, la API, el panel, el asistente, el
modelo y los avisos.

Tabla 7

*Resultados técnicos*

| Componente | Resultado |
|---|---|
| Tablas de la fuente inventariadas | 10 |
| Reglas de calidad catalogadas | 15 |
| Indicadores publicados | 6 |
| Microservicios desplegables | 7 |
| Reglas de aviso | 6 |
| Filas reconciliadas | 5 por capa, S/ 696.40 |
| Huérfanos en el hecho | 0 |
| Secretos versionados | 0 |

---

## 7. Trazabilidad con la rúbrica

Tabla 8

*Correspondencia entre criterios, tareas y evidencias*

| Criterio | Peso | Tareas | Evidencia |
|---|---|---|---|
| Análisis y arquitectura | 10 % | T01 a T03 | Arquitectura, ADR y fuente de datos |
| ETL, staging y calidad | 20 % | T04 a T06 | Scripts de staging y catálogo de calidad |
| Modelo dimensional y Data Warehouse | 15 % | T07 y T08 | Esquema estrella y reconciliación |
| Panel y API | 15 % | T09 y T10 | API, panel y contratos |
| Machine Learning | 10 % | T11 | Servicio, métricas y evidencia |
| Generative AI | 10 % | T12 | Asistente y diez pruebas |
| Automatización | 5 % | T13 | Motor de avisos y monitoreo |
| Pruebas y documentación | 10 % | T14 | Plan de pruebas y evidencias |
| Demo y comunicación | 5 % | T15 | Guion de demo |

---

## 8. Riesgos y limitaciones

Tabla 9

*Riesgos y deuda técnica*

| Elemento | Situación | Impacto | Plan |
|---|---|---|---|
| Docker no instalado | La vía con contenedores está documentada pero no se ejecutó | T01 parcial | Instalar Docker o mantener la vía local |
| Fuente con cinco líneas y un mes | No hay historia suficiente | El modelo responde datos insuficientes | Ampliar la ventana de datos |
| Video y ensayo | No grabados | T15 parcial | Grabar con el guion de la demo |
| Avisos solo en el panel | Sin correo ni WebSocket | Cobertura parcial del canal | Agregar el canal que pida el negocio |
| Dimensión de tipo 1 | Sin historial de atributos | No permite analizar cambios | Evolucionar a tipo 2 |
| Autenticación básica | Propia del despliegue local | No apta para producción | Integrar un proveedor de identidad |
| Fuente desnormalizada | Sin clientes, empleados ni geografía | Dimensiones no aplicables | Declarado como restricción |

---

## Anexos

### Anexo A. Estructura del repositorio

```text
Examen2026Noviembre/
  data-platform/     ETL, Data Warehouse, API, panel, modelo, asistente y avisos
  Tareas_SCRUM/      Backlog, plan de sprints y tarjetas T01 a T15
  bot-telegram/      Bot de Telegram con panel web de pedidos
  README.md          Estructura y puesta en marcha
  documentacion/     Este informe y el manual de usuario
```

### Anexo B. Estado de las tareas

Tabla 10

*Estado del backlog*

| Tarea | Entregable | Estado |
|---|---|---|
| T01 | Entorno y fuente reproducible | Parcial |
| T02 | Inventario, modelo y diccionario | Cerrada |
| T03 | Arquitectura y decisiones | Cerrada |
| T04 | Staging en tres zonas | Cerrada |
| T05 | Extracción incremental idempotente | Cerrada |
| T06 | Reglas de calidad | Cerrada |
| T07 | Modelo dimensional | Cerrada |
| T08 | Carga y reconciliación | Cerrada |
| T09 | API de indicadores | Cerrada |
| T10 | Panel web | Cerrada |
| T11 | Modelo con línea base | Cerrada |
| T12 | Asistente de lenguaje natural | Cerrada |
| T13 | Avisos y monitoreo | Cerrada |
| T14 | Documentación y pruebas | Cerrada |
| T15 | Video y ensayo | Parcial |

### Anexo C. Comandos de verificación

```powershell
cd data-platform
Copy-Item .env.example .env
sqlcmd -S localhost -E -C -f 65001 -i database/00_schemas.sql
cd services/etl ; py -m app full
py -m app idempotency-check
py -m app quality-report
sqlcmd -S localhost -E -C -f 65001 -i database/99_verify.sql
py tests/e2e_smoke.py
```

### Anexo D. Control de secretos

El repositorio no versiona archivos de entorno ni credenciales. La configuración
se documenta en archivos de ejemplo con valores vacíos y las credenciales se leen
del entorno local. Los datos de pedidos del bot y las dependencias instaladas
también quedan fuera del control de versiones.

---

## Conclusiones

La plataforma entrega un flujo completo y verificable sobre el proceso de ventas:
extracción, staging con trazabilidad, Data Warehouse reconciliado, indicadores
publicados por API, panel web, modelo predictivo, asistente con consultas
aprobadas y motor de avisos.

El resultado más importante no es la cantidad de componentes, sino la coherencia
entre ellos. Los totales de la fuente, del staging y del Data Warehouse
coinciden; el panel y el asistente no calculan cifras por su cuenta; el modelo no
publica métricas cuando no tiene historia suficiente; y el asistente declara sus
fuentes o reconoce que no tiene datos.

Las dos tareas parciales están acotadas y justificadas. La primera depende de la
instalación de Docker, que no estaba disponible en el equipo. La segunda depende
de la grabación del video y del ensayo formal. Ninguna afecta los criterios no
recortables de la rúbrica.

Como siguiente paso se recomienda ampliar la ventana de datos para habilitar el
análisis histórico y el modelo predictivo, agregar el canal de avisos que defina
el negocio y automatizar la verificación de punta a punta con un solo comando.

---

## Bibliografía

American Psychological Association. (2020). *Publication manual of the American Psychological Association* (7.ª ed.). American Psychological Association.

Beck, K., Beedle, M., van Bennekum, A., Cockburn, A., Cunningham, W., Fowler, M., Grenning, J., Highsmith, J., Hunt, A., Jeffries, R., Kern, J., Marick, B., Martin, R. C., Mellor, S., Schwaber, K., Sutherland, J., & Thomas, D. (2001). *Manifesto for agile software development*. https://agilemanifesto.org

FastAPI. (2024). *FastAPI documentation*. https://fastapi.tiangolo.com

Kimball, R., & Ross, M. (2013). *The data warehouse toolkit: The definitive guide to dimensional modeling* (3.ª ed.). Wiley.

Microsoft. (2024). *SQL Server documentation*. https://learn.microsoft.com/sql

Provost, F., & Fawcett, T. (2013). *Data science for business*. O'Reilly Media.

Schwaber, K., & Sutherland, J. (2020). *The Scrum Guide*. https://scrumguides.org

scikit-learn developers. (2024). *scikit-learn user guide*. https://scikit-learn.org

Streamlit. (2024). *Streamlit documentation*. https://docs.streamlit.io

Telegram. (2024). *Bot API*. https://core.telegram.org/bots/api
