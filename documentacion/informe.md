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

El punto de partida fue una base transaccional heredada, con nombres de columnas
inconsistentes, una sola ventana de datos y sin una capa intermedia que separara
la operación diaria del análisis. En ese contexto, el problema no era solo
consultar cifras, sino garantizar que las cifras consultadas fueran las mismas que
las de la fuente y que cualquier diferencia pudiera explicarse. Por eso el
proyecto se diseñó alrededor de la trazabilidad: cada fila conserva su clave de
negocio y el identificador de la ejecución que la produjo, y cada total se
reconcilia entre capas antes de publicarse.

El documento se organiza en nueve secciones. Las dos primeras describen el marco
de trabajo y la arquitectura; la tercera explica cómo se gobernaron los datos; la
cuarta recorre los servicios analíticos; la quinta documenta el bot de Telegram
como proyecto independiente; la sexta presenta las pruebas y los resultados; la
séptima relaciona el trabajo con la rúbrica; la octava enumera los riesgos; y la
novena declara, sin matices, los requisitos que no se cumplieron. Se incluyen
además cuatro anexos con la estructura del repositorio, el estado de las tareas,
los comandos de verificación y el control de secretos.

---

## Objetivos

### Objetivo general

Diseñar e implementar una plataforma de datos reproducible que permita analizar
las ventas con indicadores confiables, predicciones honestas, consultas en
lenguaje natural y avisos automáticos, sin que ningún consumidor acceda
directamente a la base transaccional.

El objetivo general se entiende cumplido cuando una persona distinta de quien
construyó el sistema puede seguir las instrucciones del repositorio, ejecutar el
pipeline, abrir el panel y obtener los mismos totales que la fuente. Esa
condición de reproducibilidad es la que guía las decisiones de arquitectura y la
que explica por qué el proyecto invierte tanto en auditoría y reconciliación.

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

La compresión del calendario obligó a tomar dos decisiones de método. La primera
fue asignar un responsable único por tarea, con un rol de apoyo para revisión, de
modo que ninguna actividad quedara sin dueño. La segunda fue fijar la evidencia
como criterio de cierre: una tarea no se consideraba terminada por haber escrito
código, sino por haber dejado un archivo reproducible en la carpeta de evidencias.
Esa regla evitó discusiones sobre el estado del trabajo y permitió que la revisión
de sprint se hiciera sobre resultados concretos.

Los roles se mantuvieron separados aunque el equipo fuera pequeño, porque la
separación obliga a explicar las decisiones. El Product Owner defendió el alcance
y la prioridad; el Scrum Master protegió el tiempo y desbloqueó dependencias; los
roles técnicos se repartieron por dominio de datos, analítica y automatización; y
el rol de calidad concentró la documentación y las pruebas. En la práctica, una
misma persona cubrió más de un rol, pero la responsabilidad quedó declarada para
cada entregable.

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

El sprint S0 se dedicó a reducir la incertidumbre: verificar la conexión con SQL
Server, inventariar las tablas, dibujar el modelo entidad-relación y registrar las
decisiones de arquitectura antes de escribir el ETL. Esa inversión inicial evitó
retrabajo, porque las reglas de calidad y el grano del hecho se definieron sobre
el modelo y no sobre el código. El sprint S1 convirtió ese diseño en un pipeline
ejecutable con tres zonas, auditoría y cuarentena. El sprint S2 agregó la capa de
consumo y la automatización. El sprint S3 se reservó para pruebas, documentación y
demo, con un buffer que absorbió las tareas que no dependían solo del equipo.

La revisión de cada sprint se hizo contra la carpeta de evidencias y no contra
diapositivas. En S0 se revisaron el inventario y los ADR; en S1, los conteos de
cada capa y la reconciliación; en S2, las capturas de la API, el panel, el modelo,
el asistente y los avisos; y en S3, el plan de pruebas y los documentos finales.
La retrospectiva se centró en dos preguntas: qué evidencia faltó y qué decisión
habría que revertir si el alcance cambiara. Ambas preguntas alimentaron la sección
de riesgos y la lista de pendientes.

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

Esa separación tiene una consecuencia práctica: cualquier consumidor nuevo, sea
un cuaderno de análisis o una aplicación móvil, se conecta a la API y hereda los
mismos filtros, los mismos límites y las mismas validaciones. También permite
razonar sobre el rendimiento por separado, porque la base atiende un número
acotado de consultas y no la suma de todos los clientes.

El recorrido de una fila ilustra el diseño. La fila nace en la tabla de detalle de
factura, se copia sin transformación a `raw`, se tipa y valida en `clean`, se
integra con sus dimensiones en `ready` y se inserta en `dw.FactVentas` con las
claves sustitutas. En cada salto se registra el identificador de ejecución, de
modo que un total se puede descomponer hasta la fila original. Si una fila no
supera una validación, no desaparece: se copia a cuarentena con el código de la
regla que la rechazó.

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

La elección del stack respondió a tres criterios: que las herramientas ya
estuvieran disponibles en el equipo, que permitieran ejecutar todo en local sin
servicios en la nube y que tuvieran documentación suficiente para justificar cada
decisión. SQL Server se conservó porque la fuente ya vivía en esa instancia y
migrarla habría agregado un riesgo innecesario. Python concentró el ETL, la API,
el modelo y el asistente para reducir el número de lenguajes. Streamlit permitió
publicar un panel sin construir un frontend completo, y Git sostuvo la
trazabilidad de los entregables.

La contrapartida fue aceptar dependencias pesadas. Streamlit y scikit-learn
agregan librerías que una solución más liviana no requeriría, y el modelo local
opcional suma una dependencia externa que se puede desactivar. Esa contrapartida
se documentó en el manual de instalación para que quien reproduzca el proyecto
sepa qué necesita y qué puede omitir.

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

Las decisiones se registraron como ADR porque el proyecto tenía alternativas
razonables en casi todos los puntos. Elegir una base distinta, un modelo
dimensional con otro grano o un asistente con SQL libre habría producido un
sistema defendible pero con riesgos diferentes. El ADR deja constancia del
contexto y de la consecuencia, de modo que una revisión posterior pueda discutir
la decisión sin reconstruirla.

La decisión con mayor impacto fue el grano del hecho: línea de factura. Un grano
de cabecera habría simplificado los conteos, pero habría impedido analizar
productos y secciones. El grano de línea conserva esa capacidad y obliga a cuidar
la reconciliación de importes, porque una factura se reparte en varias filas. Esa
consecuencia se verificó en la práctica: la suma de las líneas coincide en todas
las capas con el total de la fuente de detalle.

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

La extracción admite dos modos. El modo `full` recorre todas las filas y se usa
para la carga inicial o para reconstruir el ambiente. El modo `incremental` lee
la marca de agua, aplica un solapamiento de días para no perder registros que
llegaron tarde y vuelve a procesar ese tramo. El solapamiento es deliberado: en
lugar de suponer que la fuente nunca cambia, el pipeline asume que puede
haber cambios retroactivos y los absorbe sin duplicar.

La zona `raw` es de solo anexar. No se actualiza ni se borra, de modo que siempre
existe una copia fiel de lo que la fuente entregó en cada ejecución. Esa
decisión tiene un costo de almacenamiento y un beneficio claro: si una
transformación se equivoca, se puede volver a procesar sin pedirle nada a la
fuente. La zona `clean` tipa los campos, normaliza nombres y aplica las reglas de
calidad; la zona `ready` resuelve las dimensiones y deja las filas listas para el
hecho.

### 3.2 Reglas de calidad

Se catalogaron quince reglas de calidad, con identificador, condición y acción.
Las filas que no cumplen una regla se derivan a cuarentena en lugar de
descartarse en silencio. Las medidas nunca se imputan con cero, porque eso
distorsionaría los indicadores.

El catálogo cubre claves nulas, cantidades no positivas, precios negativos o
fuera de rango, facturas huérfanas, productos inexistentes, fechas nulas o
futuras, números de factura inválidos, nombres vacíos, duplicados en el lote y
jerarquías incompletas. Cada regla tiene un código estable, de `DQ-001` a
`DQ-015`, que se guarda junto con la fila rechazada. Así, cuando el reporte de
calidad muestra un rechazo, se puede identificar la regla y la fila sin ambigüedad.

La política de cuarentena es conservadora. Un rechazo no se corrige en el momento
ni se reemplaza por un valor promedio: la fila se aparta y se informa. Esa
decisión retrasa la carga, pero evita que un dato inventado se propague al Data
Warehouse y llegue al panel como si fuera real. El comando de reporte de calidad
reconstruye el conteo por regla, el total de rechazos y la reconciliación entre
capas, de modo que la revisión se puede repetir en cualquier momento.

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

El esquema estrella se eligió por su legibilidad para el negocio. Una consulta de
ventas por local, por producto o por mes se resuelve con un `JOIN` a una
dimensión y una suma sobre el hecho, sin cadenas de subconsultas. Esa simplicidad
importa porque el panel y el asistente consumen la misma estructura: si el modelo
fuera más complejo, cada consumidor tendría que replicar la lógica y las cifras
podrían divergir.

La tabla de hechos conserva la clave natural de la línea además de las claves
sustitutas. Esa duplicidad permite reconstruir el origen y auditar una fila sin
depender de los identificadores internos. Cuando una dimensión no se resuelve, se
usa el miembro desconocido con clave cero; la alternativa, descartar la fila,
habría reducido el total y roto la reconciliación sin dejar rastro.

La verificación se hizo con una consulta que suma el importe en cada capa y
compara los resultados. La tabla 5 muestra que las cuatro capas coinciden en
cinco filas y S/ 696.40. El número es pequeño porque la fuente de práctica tiene
un solo mes, pero la prueba es la misma que se aplicaría a un volumen mayor: si
una capa difiere, la diferencia se investiga antes de publicar.

---

## 4. Analítica y servicios

### 4.1 API de indicadores

La API expone seis endpoints de consulta (indicadores, tendencias, detalle,
filtros, agrupado y monitoreo), además del estado del servicio y la raíz. Usa
consultas parametrizadas, una lista permitida de dimensiones y un límite máximo
de paginación de doscientas filas. Los errores de base se devuelven como errores
explícitos.

El contrato se organiza por preguntas de negocio. `kpis` devuelve los seis
indicadores del periodo; `tendencias` entrega la serie y la variación frente al
periodo anterior; `detalle` lista las líneas con paginación; `filtros` publica los
valores disponibles para fecha, local, sección y producto; `agrupado` resume por
una dimensión permitida; y `monitor` informa el estado del pipeline y de la
calidad. `health` y la raíz completan el servicio sin exponer datos de negocio.

La seguridad de la API se apoya en tres controles. Las consultas usan parámetros y
nunca concatenan texto del usuario; las dimensiones de agrupación se validan
contra una lista permitida; y la paginación tiene un tope. Cuando la base no
responde, la API devuelve un error explícito en lugar de una lista vacía, porque
una lista vacía se confundiría con un periodo sin ventas y llevaría a una
conclusión equivocada.

### 4.2 Panel web

El panel muestra seis indicadores, filtros por fecha y tres dimensiones,
tendencia histórica, comparación entre periodos, agrupados, tabla de detalle
paginada y exportación a CSV. También informa la fecha de última actualización
tomada de la auditoría del ETL.

La interfaz se pensó para que el usuario no tenga que conocer el modelo. Los
filtros se presentan como listas de valores reales, no como campos de texto
libre, y se combinan entre sí. Si una combinación no devuelve filas, el panel lo
indica y conserva los filtros para que la persona los corrija en lugar de
reiniciarlos. Esa decisión evita el bucle de volver a seleccionar todo desde cero.

El panel no calcula cifras. Cada tarjeta, serie y tabla proviene de una llamada
HTTP a la API, y la exportación a CSV reproduce exactamente las filas filtradas.
Esa restricción es intencional: si el panel sumara por su cuenta, existirían dos
definiciones de ventas y la reconciliación dejaría de tener sentido. La fecha de
última actualización se lee de la auditoría del ETL, de modo que una cifra
correcta pero antigua se puede detectar a simple vista.

### 4.3 Modelo predictivo

El modelo se entrenó con división temporal, nunca aleatoria, y se comparó contra
una línea base. Con los datos reales existe un solo mes, por lo que el servicio
responde que los datos son insuficientes y no publica métricas inventadas. La
verificación del algoritmo se realizó con una serie sintética identificada como
tal, en la que el error absoluto medio fue de 38.9 frente a 480.0 de la línea
base.

La división temporal es la decisión metodológica más importante del componente.
Una división aleatoria habría mezclado meses futuros con meses pasados y habría
producido métricas optimistas que no se sostienen en producción. Al entrenar con
el pasado y evaluar con el tramo siguiente, la métrica refleja el uso real: predecir
un periodo que el modelo no vio.

La línea base cumple una función de control. Si el modelo no supera a una regla
simple, no hay razón para desplegarlo. En la serie sintética el modelo mejora de
forma clara, pero esa comparación no se traslada a las ventas reales porque no hay
historia suficiente. El servicio declara el estado `insufficient_data` y se niega
a publicar un número que no puede sostener; esa negativa es parte del diseño, no
un fallo.

El modelo se versiona y se guarda con sus parámetros. Cada artefacto registra la
versión, los periodos de entrenamiento y prueba y las métricas obtenidas, de modo
que una predicción se puede asociar con el experimento que la produjo. Cuando no
existe un artefacto válido, el endpoint devuelve el diagnóstico del entrenamiento
en lugar de una predicción vacía.

### 4.4 Asistente de lenguaje natural

El asistente normaliza la pregunta, la clasifica en una de las diez intenciones
aprobadas y consulta el endpoint correspondiente de la API. Cada respuesta
incluye las fuentes y un indicador de verificabilidad. Cuando la pregunta está
fuera de alcance, responde que no hay datos. El modelo de lenguaje no ejecuta SQL
ni genera cifras.

La normalización elimina acentos, unifica mayúsculas y espacios y extrae
parámetros como años, locales o productos. La clasificación es determinista: una
lista de palabras clave asigna la intención y, si hay ambigüedad, se aplican
reglas de prioridad. Esa simplicidad es una ventaja para auditar: ante una
respuesta, se puede explicar exactamente por qué se eligió esa consulta.

El indicador de verificabilidad distingue una respuesta respaldada por el Data
Warehouse de una respuesta general. Si la consulta aprobada devuelve datos, la
respuesta se marca como verificada y cita el servicio y el endpoint de origen. Si
no hay datos, la respuesta lo dice. En el modo general, el texto del modelo local
se muestra separado y marcado como no verificado, porque no proviene de la base.

El asistente tampoco acepta SQL libre. Esa restricción reduce la flexibilidad,
pero elimina dos riesgos: la inyección de consultas y la generación de cifras que
nadie puede reconstruir. En las diez preguntas de prueba, el intérprete acertó la
intención y la respuesta coincidió con el endpoint previsto, lo que demuestra que
el asistente traduce la pregunta y no inventa cifras.

### 4.5 Avisos y monitoreo

El motor evalúa seis reglas sobre los indicadores, el estado del modelo y las
filas rechazadas. Cada aviso incluye severidad, valor observado, umbral y acción
sugerida. La deduplicación por clave de evento evita notificaciones repetidas y
la vista de monitoreo integra el estado del pipeline, del modelo y de los avisos.

Las reglas cubren dos dimensiones del negocio. Las de ventas comparan el periodo
con umbrales absolutos y con el periodo anterior: ventas bajas, ticket bajo y
caída mayor al quince por ciento. Las de modelo y calidad vigilan la salud del
sistema: modelo sin entrenar, error alto y rechazos sin resolver. Separar ambos
grupos permite distinguir un problema de negocio de un problema operativo.

La deduplicación usa una clave compuesta por el código de la regla, la entidad, el
periodo y la fecha de actualización de los datos. Si la misma condición se evalúa
dos veces sobre los mismos datos, el aviso no se duplica; si los datos se cargan
de nuevo, se genera un evento nuevo. Esa decisión evita el ruido de notificaciones
repetidas sin ocultar un cambio real en la magnitud del desvío.

El registro de entregas guarda cada intento por alerta y canal, de modo que se
puede saber qué se generó, qué se entregó y qué falló. La vista de monitoreo
reúne el estado del pipeline, del modelo y de los avisos en una sola página. Los
eventos simulados se identifican como tales para que una prueba no se confunda con
una alerta real.

---

## 5. Proyecto de ejemplo: bot de Telegram

El repositorio incluye, además de la plataforma de datos, un bot de Telegram para
el restaurante "El Gordo", desarrollado en Node.js con Express. Es un proyecto
independiente: **no consume el Data Warehouse ni la API de indicadores** y se
entrega como ejemplo de integración con un canal de mensajería.

La independencia es deliberada. El bot resuelve un proceso transaccional
—recibir un pedido, prepararlo y entregarlo— y no un proceso analítico. Mezclar
ambos habría exigido que el bot escribiera en el Data Warehouse o que la
plataforma dependiera de un servicio externo para arrancar. Al mantenerlos
separados, cada uno se puede demostrar por su cuenta y la entrega no arrastra las
credenciales de Telegram a la plataforma de datos.

### 5.1 Componentes

- `bot.js`: flujos de conversación, menús, carrito, pedidos, reservas y comandos.
- `menu.js`: catálogo del restaurante, con categorías, platos, descripciones y
  precios en lempiras.
- `store.js`: persistencia de pedidos en memoria y en `orders.json`, que no se
  versiona.
- `web/dashboard.js`: servidor Express con la API de pedidos, la autenticación por
  token y los archivos estáticos del panel.
- `web/public/`: interfaz del panel de administración.

La separación de archivos sigue el mismo criterio que la plataforma: una unidad
por responsabilidad. `bot.js` conoce la conversación y no la persistencia;
`store.js` guarda y recupera pedidos sin conocer Telegram; y el panel consume el
mismo almacén a través de una API. Esa frontera evita duplicar la lógica de
pedidos y permite que el bot y el panel muestren exactamente el mismo estado.

La persistencia usa memoria y un archivo `orders.json`. La memoria mantiene la
lectura rápida y el archivo sobrevive al reinicio. El archivo no se versiona
porque contiene datos de clientes y cambia con cada pedido; su exclusión está
declarada en `.gitignore` y en el manual.

### 5.2 Flujo del cliente

1. El cliente abre el bot y pulsa **Iniciar** o envía `/start`.
2. Recorre las categorías, elige un plato y lo agrega al carrito.
3. Ajusta cantidades o elimina productos desde el carrito.
4. Finaliza el pedido y elige **Delivery** o **Retiro en local**.
5. Confirma; el bot valida que el carrito no esté vacío, registra el pedido,
   envía el resumen al administrador y devuelve el número de pedido.

El bot también admite reservas, que llegan al administrador para su confirmación.

### 5.3 Comandos

Tabla 6

*Comandos del bot de Telegram*

| Comando | Uso |
|---|---|
| `/start` | Abrir el menú principal |
| `/menu` | Ver categorías y platos |
| `/carrito` | Revisar y modificar el pedido |
| `/cancelar` | Cancelar el pedido en curso |
| `/compartir` | Obtener el enlace para compartir el bot |
| `/miid` | Ver el identificador de Telegram del usuario |
| `/pedidos` | Administrador: pedidos recientes |
| `/pendientes` | Administrador: solo pedidos pendientes |

### 5.4 Panel web de pedidos

El panel se monta dentro del mismo proceso del bot y comparte el mismo
almacén, de modo que el bot y el panel ven los mismos pedidos. Se actualiza cada
cinco segundos, permite filtrar por estado y fecha, cambiar el estado de un
pedido, avisar al cliente por Telegram y exportar el cierre del día a Excel o
CSV. El acceso requiere un token configurado en el entorno.

Los estados posibles son `pendiente`, `en_preparacion`, `entregado` y
`cancelado`; cada cambio se refleja en el panel y se notifica al cliente.

El control de acceso usa un token en la URL, adecuado para un panel local pero no
para producción. La recomendación es no compartir el enlace con el token y
rotarlo si se filtró. La exportación genera Excel y CSV a partir del mismo
conjunto filtrado, de modo que el cierre del día se puede archivar o enviar sin
volver a capturar datos.

El panel también concentra la operación del restaurante: muestra los pedidos
recientes, permite filtrar por estado y fecha, y conserva el historial aunque el
bot se reinicie. Esa continuidad importa porque un pedido a medio preparar no
puede perderse si el proceso se cae.

### 5.5 Alcance

El bot demuestra un flujo completo de pedidos y reservas, pero no forma parte de
los criterios de la rúbrica de ingeniería de datos. Su dependencia es un token de
BotFather y la red; las credenciales y los pedidos quedan fuera del control de
versiones.

La decisión de incluirlo responde a una razón pedagógica: mostrar que los datos
pueden alimentar canales distintos. El bot no analiza ventas, pero su panel
produce un cierre diario que, en un escenario real, podría integrarse al pipeline
como una fuente transaccional más. Esa integración no se implementó y se declara
como trabajo futuro, porque habría exigido definir un contrato de datos y un
proceso de calidad para pedidos.

El bot se verificó con un recorrido manual del flujo de compra y con un plan de
pruebas documentado en `tests/README.md`. Ese plan define casos unitarios para el
catálogo, el carrito y el almacén, y casos de integración para el checkout, el
cambio de estado, las reservas y el panel. Los archivos de prueba no se
implementaron, de modo que el plan quedó como especificación y no como suite
automatizada. Tampoco se ejecutó una prueba de carga ni una auditoría de seguridad
del panel, así que su alcance es demostrativo.

---

## 6. Pruebas y resultados

Tabla 7

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

Las pruebas se agruparon por lo que demuestran, no por la herramienta que las
ejecuta. Las cinco primeras validan el comportamiento del pipeline: que la carga
inicial deje los conteos esperados, que la incremental no duplique, que la
reejecución sea idempotente, que los nulos y duplicados se detecten y que las
claves foráneas se respeten. La sexta prueba el peor escenario: una conexión que
falla a mitad de la carga. Las siguientes verifican la reconciliación, el panel,
el modelo, el asistente, los avisos y el recorrido completo.

Cada evidencia quedó en un archivo de la carpeta `documentation/evidencias`, con
el comando ejecutado y la salida obtenida. Esa decisión permite que un revisor
repita la prueba y compare. También obliga a que la evidencia sea de una ejecución
real: si el comando no se puede volver a correr, la evidencia no sirve.

La prueba de idempotencia merece una nota aparte. Se ejecuta dos veces el mismo
lote y se comparan los conteos antes y después. Si la segunda ejecución inserta
filas nuevas, el pipeline no es idempotente y el error se detecta en la prueba y
no en producción. Ese control es el que permite decir que la carga incremental es
segura de repetir.

La prueba de punta a punta es la más costosa y la más informativa. Recorre todos
los componentes en orden y falla si alguno devuelve un contrato distinto al
esperado. No reemplaza a las pruebas específicas, pero detecta incompatibilidades
entre servicios que las pruebas aisladas no ven.

Tabla 8

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

Los resultados se leen en dos niveles. En el nivel de cobertura, el proyecto
completa los siete componentes, las quince reglas de calidad y las seis reglas de
aviso. En el nivel de calidad, la reconciliación sin diferencias y la ausencia de
huérfanos indican que el modelo no perdió filas al integrarse. La ausencia de
secretos versionados es también un resultado: se verificó que el repositorio no
contiene tokens ni credenciales.

El número de filas es pequeño y no debe interpretarse como una medida de escala.
La fuente de práctica tiene cinco líneas y un mes; el valor de la evidencia está
en que las cuatro capas coinciden exactamente y en que el procedimiento se puede
repetir con más datos sin cambiar el código.

---

## 7. Trazabilidad con la rúbrica

La trazabilidad responde a una pregunta concreta: qué evidencia sostiene cada
criterio de evaluación. La tabla 9 relaciona los nueve criterios con las tareas
del backlog y con el artefacto que permite verificarlos. No se asigna a un
criterio una tarea que no haya producido evidencia.

Tabla 9

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

La tabla muestra dos asimetrías que conviene explicar. La primera es que el
criterio de pruebas y documentación depende de una sola tarea (T14) pero concentra
evidencias de todas las demás; por eso su peso no refleja el esfuerzo, sino la
verificación final. La segunda es que la demo (T15) tiene peso bajo y, aun así,
quedó parcial: no se grabó el video ni se ensayó la presentación. Esa brecha no
cambia el funcionamiento del sistema, pero sí la evidencia de comunicación.

El criterio de análisis y arquitectura se sostiene con los ADR y con el modelo
entidad-relación. El de ETL y calidad, con los scripts de staging y el catálogo
de reglas. El de modelo dimensional, con el esquema estrella y la reconciliación.
El de panel y API, con los contratos y las capturas de las pruebas. El de Machine
Learning, con la evidencia del modelo y su línea base. El de Generative AI, con
las diez preguntas documentadas. Y el de automatización, con el motor de avisos y
la vista de monitoreo.

---

## 8. Riesgos y limitaciones

Tabla 10

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

Los riesgos se clasificaron por su efecto sobre la entrega. Dos afectan el
cumplimiento formal (Docker y la demo); dos afectan la profundidad del análisis
(la ventana de datos y la dimensión de tipo 1); y tres son decisiones de alcance
que conviene declarar (canal de avisos, autenticación y fuente desnormalizada).
Ninguno de los riesgos compromete la exactitud de los totales, que es la propiedad
central del proyecto.

La gestión del riesgo fue explícita. Cada riesgo tiene un plan y un responsable
implícito en la tarea asociada. Los que dependían de una instalación externa
—Docker— se aceptaron como parciales en lugar de simular una solución. Los que
dependían de datos —la historia insuficiente— se resolvieron haciendo que el
sistema reconozca el límite y no publique métricas sin sustento.

El riesgo con mayor probabilidad de materializarse es el de la demo. Un video sin
grabar y un ensayo no realizado dejan poco margen ante un fallo de red o de base.
La mitigación natural es grabar con anticipación y preparar capturas de respaldo;
ambas acciones quedaron pendientes y se declaran en la sección 9.

---

## 9. Requisitos no cumplidos y pendientes

Esta sección enumera de forma explícita lo que **no** se cumplió. No se presenta
como terminado lo que quedó parcial ni se sustituyen evidencias faltantes con
texto descriptivo.

La revisión se hizo criterio por criterio contra las tarjetas del backlog y contra
el contenido real del repositorio. Cuando una tarjeta pedía un archivo, se buscó
el archivo; cuando pedía una captura, se buscó la captura; cuando pedía un
comando, se ejecutó el comando. Esa verificación es la que permite distinguir una
tarea cerrada de una tarea declarada como cerrada.

### 9.1 Criterios de aceptación no cumplidos

La tabla 11 recoge los seis criterios que no se cumplieron. Tres pertenecen a T01
y tres a T15, las dos únicas tareas que quedaron parciales.

Tabla 11

*Criterios de aceptación que no se cumplieron*

| Tarea | Criterio | Situación real | Impacto |
|---|---|---|---|
| T01 | La base fuente se levanta con un comando documentado | No existe `docker-compose.yml` ni un script que cree y cargue la base `Venta`; el README indica que la fuente ya existe en la instancia local | El ambiente no se reconstruye desde cero en otro equipo |
| T01 | Usuario de aplicación con permisos mínimos | Los scripts no crean `LOGIN`, `USER` ni `GRANT`; la conexión usa autenticación integrada de Windows (`sqlcmd -E`) | Se opera con una cuenta administrativa |
| T01 | Evidencia de `docker-compose.yml` o script de restauración | No se incluyó ninguno de los dos | T01 queda parcial |
| T15 | Video de cinco minutos | No se grabó | El 5 % de la rúbrica queda sin evidencia |
| T15 | Ensayo completo de la demo y checklist marcado | No se realizaron | Riesgo de errores en la presentación |
| T15 | Plan B con capturas o video | No se preparó | Sin respaldo ante una falla de red o de base |

Las consecuencias de estas brechas son distintas. En T01, la ausencia de
contenedores y de un usuario técnico significa que el ambiente depende de una
instalación previa de SQL Server y de una cuenta con privilegios. Quien reciba el
repositorio puede ejecutar el pipeline, pero no reconstruir la fuente desde cero
con un solo comando. En T15, la ausencia de video y de ensayo no impide que el
sistema funcione, pero reduce la evidencia disponible para la evaluación de
comunicación.

Ninguna de las brechas se ocultó con una solución aparente. No se agregó un
`docker-compose.yml` vacío para marcar el criterio, ni se declaró un usuario
técnico que no existe, ni se presentó un video de diapositivas como demostración.
La decisión fue declarar la brecha y explicar qué haría falta para cerrarla.

### 9.2 Pendientes técnicos no incluidos

La tabla 12 distingue los pendientes estrictamente técnicos de las mejoras que
quedaron fuera del alcance acordado. Son ocho elementos: un canal de avisos
externo, la predicción con datos reales, las métricas sobre ventas reales, la
autenticación, la dimensión de tipo 2, la fuente desnormalizada, el despliegue con
contenedores y la rotación del token del bot.

Tabla 12

*Pendientes y mejoras fuera del alcance entregado*

| Elemento | Estado | Motivo | Acción recomendada |
|---|---|---|---|
| Canal de avisos externo (correo o Telegram) | Solo panel y registro interno | La versión publicada no configura un canal saliente | Definir el canal con el negocio e integrarlo |
| Predicción con datos reales | No disponible | Un solo mes y cinco líneas; el servicio responde `insufficient_data` | Ampliar la ventana histórica |
| Métricas del modelo sobre ventas reales | No disponibles | El MAE de 38.9 frente a 480.0 se midió en una serie sintética identificada | Reentrenar y evaluar con historia real |
| Autenticación en la API y el panel | Sin inicio de sesión en la versión publicada | Quedó fuera del alcance acordado | Integrar un proveedor de identidad |
| Dimensión de tipo 2 | Solo tipo 1 | El alcance fijó tipo 1 | Versionar atributos para analizar cambios |
| Fuente desnormalizada | Sin clientes, empleados ni geografía | Limitación de la fuente | Mantenerla documentada como restricción |
| Despliegue con contenedores | No ejecutado | Docker no estaba instalado | Probar el despliegue y registrar la evidencia |
| Rotación del token del bot | Pendiente | Se detectó un token en el historial de un repositorio de trabajo, no en la entrega publicada | Revocarlo y generar uno nuevo en BotFather |

Los pendientes tienen distinto costo de cierre. La rotación del token es inmediata
y no requiere código. El canal de avisos y la autenticación requieren decisiones
de producto. La predicción con datos reales y la dimensión de tipo 2 dependen de
una fuente más rica. El despliegue con contenedores depende de una instalación
externa. Ordenarlos por costo evita tratar todos los pendientes como si tuvieran
la misma prioridad.

La lista también cumple una función de transparencia. Un lector puede tomar
cualquiera de estos puntos y verificar que no está implementado, en lugar de
suponerlo por lo que dice el resto del informe. En ese sentido, la sección 9 es la
contraparte de la sección 6: una muestra lo que se probó y la otra lo que falta.

### 9.3 Cumplimiento global

De los quince entregables, trece se cerraron y dos quedaron parciales (T01 y
T15). Las brechas de T01 afectan la reproducibilidad del ambiente, no la calidad
de los datos procesados; las de T15 afectan la evidencia de la demo, no el
funcionamiento del sistema. El resto de los pendientes son mejoras declaradas y
no requisitos incumplidos.

Si se mira la rúbrica, el criterio de análisis y arquitectura (10 %) sigue
respaldado por T02 y T03, que sí se cerraron; lo que falta en T01 es la
reproducibilidad del ambiente, no el análisis. El criterio de demo y comunicación
(5 %) queda sin evidencia porque depende del video y del ensayo. Los demás
criterios conservan su evidencia y no se ven afectados por estas brechas.

Cerrar T01 exige dos acciones concretas: publicar un `docker-compose.yml` o un
script que cree y cargue la base fuente, y definir un usuario de aplicación con
permisos mínimos. Cerrar T15 exige grabar el video de cinco minutos, ensayar la
demo y preparar capturas de respaldo. Ninguna de las dos acciones cambia el
código de la plataforma; ambas son trabajo de empaquetado y de comunicación.

La conclusión de esta sección es que el proyecto prefiere una entrega verificable
con brechas declaradas antes que una entrega aparentemente completa. Esa
preferencia es coherente con el resto del sistema: el modelo no publica métricas
sin datos, el asistente no inventa cifras y el pipeline no imputa valores. El
informe aplica el mismo criterio a su propio cumplimiento.

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

Tabla 13

*Estado del backlog*

| Tarea | Entregable | Estado | Observación |
|---|---|---|---|
| T01 | Entorno y fuente reproducible | Parcial | Sin contenedores ni usuario técnico; ver 9.1 |
| T02 | Inventario, modelo y diccionario | Cerrada | |
| T03 | Arquitectura y decisiones | Cerrada | |
| T04 | Staging en tres zonas | Cerrada | |
| T05 | Extracción incremental idempotente | Cerrada | |
| T06 | Reglas de calidad | Cerrada | |
| T07 | Modelo dimensional | Cerrada | |
| T08 | Carga y reconciliación | Cerrada | |
| T09 | API de indicadores | Cerrada | |
| T10 | Panel web | Cerrada | |
| T11 | Modelo con línea base | Cerrada | Métricas sobre serie sintética; ver 9.2 |
| T12 | Asistente de lenguaje natural | Cerrada | |
| T13 | Avisos y monitoreo | Cerrada | Solo canal de panel; ver 9.2 |
| T14 | Documentación y pruebas | Cerrada | |
| T15 | Video y ensayo | Parcial | Sin video ni ensayo; ver 9.1 |

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

Durante el desarrollo se detectó un token de bot en el historial de un repositorio
de trabajo que no forma parte de esta entrega. El token no está publicado aquí,
pero se recomienda revocarlo en BotFather y generar uno nuevo antes de reutilizar
el bot.

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

Esa coherencia se apoya en decisiones que se tomaron antes de escribir código: un
solo punto de acceso a la base, un grano de hecho explícito, reglas de calidad con
código estable y una política de cuarentena que no imputa valores. Si alguna de
esas decisiones se hubiera relajado para avanzar más rápido, el sistema habría
producido cifras con apariencia de verdad y sin forma de auditarlas. El costo de
la disciplina fue un poco más de trabajo en el ETL; el beneficio es que cada total
se puede reconstruir.

El proyecto también deja una lección sobre el alcance. La tentación de agregar
funciones —un canal de correo, un inicio de sesión completo, una dimensión
histórica— habría mejorado la demostración y habría debilitado la evidencia,
porque cada función nueva exige pruebas y documentación que no estaban
presupuestadas. La lista de pendientes de la sección 9 es, en ese sentido, una
decisión de honestidad y no una omisión accidental.

Las dos tareas parciales están acotadas y justificadas en la sección 9. La
primera depende de la instalación de Docker y de un usuario técnico con permisos
mínimos, que no estaban disponibles. La segunda depende de la grabación del video
y del ensayo formal. Ninguna afecta los criterios no recortables de la rúbrica,
pero se declaran para que la evaluación no suponga un cumplimiento que no existe.

El balance técnico es positivo. La plataforma procesa datos reales, reconcilia
capas, publica indicadores, responde preguntas y genera avisos en un entorno
local sin depender de servicios pagos. El bot de Telegram agrega un canal de
negocio distinto y demuestra que la arquitectura de servicios se puede extender
sin tocar el Data Warehouse. Y la documentación permite que otra persona repita
el recorrido sin asistencia.

Como siguiente paso se recomienda ampliar la ventana de datos para habilitar el
análisis histórico y el modelo predictivo, agregar el canal de avisos que defina
el negocio, completar el video y el ensayo, y automatizar la verificación de punta
a punta con un solo comando.

Si se prioriza una sola mejora, debería ser la ampliación de la ventana de datos.
Con más historia, el modelo predictivo deja de ser una demostración metodológica y
se convierte en una herramienta útil; además, el panel gana comparaciones
interanuales y los avisos de tendencia adquieren sentido. Las demás mejoras son
valiosas, pero ninguna desbloquea tantas capacidades a la vez.

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
