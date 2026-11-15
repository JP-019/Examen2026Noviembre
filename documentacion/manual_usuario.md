# Manual de usuario de la plataforma de ventas y del bot de Telegram

| Campo | Valor |
|---|---|
| Versión | 1.0 |
| Fecha | 14 de noviembre de 2026 |
| Alcance | Panel de ventas, asistente, avisos y bot de Telegram |
| Audiencia | Usuarios de negocio, administradores del restaurante y personal de operación |

---

## Introducción

Este manual explica cómo usar la plataforma de análisis de ventas y el bot de
Telegram que se entregan en el repositorio. No requiere conocimientos de
programación: describe qué hace cada pantalla, qué significan los indicadores y
qué hacer cuando algo no funciona.

La plataforma tiene dos partes independientes:

1. **Plataforma de datos.** Toma las ventas del sistema transaccional, las
   organiza y las publica en un panel web, un asistente de preguntas y un módulo
   de avisos.
2. **Bot de Telegram.** Gestiona pedidos y reservas del restaurante "El Gordo" y
   ofrece un panel web para el administrador.

El bot es un proyecto de ejemplo: **no lee el Data Warehouse ni se conecta a la
plataforma de datos**. Se puede usar de forma separada.

---

## 1. Antes de empezar

### 1.1 Requisitos

| Elemento | Requisito |
|---|---|
| Navegador | Chrome, Edge o Firefox actualizado |
| Plataforma de datos | Python 3.12 y SQL Server con la base `DataPlatform` |
| Bot de Telegram | Node.js 18 o superior y un bot creado en BotFather |
| Red | Acceso a `localhost` en el mismo equipo donde corren los servicios |

### 1.2 Servicios y direcciones

| Servicio | Dirección | Para qué sirve |
|---|---|---|
| Panel de ventas | `http://localhost:8501` | Ver indicadores, tendencias y detalle |
| API de datos | `http://localhost:8000/api/v1/health` | Comprobar que los datos están disponibles |
| Asistente | `http://localhost:8003` | Responder preguntas sobre ventas |
| Avisos | `http://localhost:8004/monitor` | Revisar alertas y estado del sistema |
| Catálogo | `http://localhost:8001` | Ver el índice de servicios y documentos |
| Panel del bot | `http://localhost:3000` | Gestionar pedidos del restaurante |

### 1.3 Cómo saber si el sistema está disponible

Abra `http://localhost:8000/api/v1/health`. Una respuesta correcta indica el
estado de la base y la última actualización de los datos. Si el servicio no
responde, el panel mostrará un mensaje de error y no inventará cifras.

---

## 2. Panel de ventas

### 2.1 Acceso

1. Abra `http://localhost:8501` en el navegador.
2. Espere a que carguen las tarjetas del periodo.
3. Verifique la fecha de última actualización que aparece en la cabecera.

### 2.2 Filtros

| Filtro | Qué hace |
|---|---|
| Fecha desde / hasta | Limita el periodo analizado al rango real de datos |
| Local | Muestra solo uno de los locales disponibles |
| Sección | Filtra por sección comercial |
| Producto | Limita el análisis a un producto concreto |

Los filtros se combinan entre sí. Si el resultado queda vacío, el panel lo
indica y mantiene los filtros aplicados para que pueda corregirlos.

### 2.3 Los seis indicadores

| Indicador | Definición | Cómo interpretarlo |
|---|---|---|
| Ventas | Suma de los importes de las líneas | Cuánto se vendió en el periodo |
| Líneas | Cantidad de líneas de venta | Volumen de operaciones registradas |
| Facturas | Facturas distintas emitidas | Cantidad de compras, no de productos |
| Ticket promedio | Ventas divididas entre facturas | Gasto medio por compra |
| Unidades | Suma de las cantidades vendidas | Volumen físico vendido |
| Productos | Productos distintos vendidos | Variedad de la canasta |

Las cifras se calculan siempre sobre el Data Warehouse. El panel no recalcula
nada por su cuenta: muestra lo que devuelve la API.

### 2.4 Tendencias y comparación

La sección de tendencias muestra la evolución por día o por mes y compara el
periodo actual con el anterior de igual duración. Si no existe un periodo previo
comparable, la comparación aparece vacía y se indica que no hay base de
comparación.

### 2.5 Detalle y exportación

La tabla de detalle lista las líneas del periodo con paginación. El botón de
descarga genera un archivo CSV con exactamente las filas filtradas, listo para
abrir en Excel.

### 2.6 Mensajes del panel

| Situación | Qué verá | Qué hacer |
|---|---|---|
| Cargando | Indicador de carga | Esperar |
| API caída | Mensaje de error de conexión | Verificar que la API esté iniciada |
| Sin datos | Aviso de periodo vacío | Ampliar el rango de fechas o quitar filtros |
| Datos desactualizados | Fecha de actualización antigua | Revisar la última ejecución del ETL |

---

## 3. Asistente de ventas

### 3.1 Cómo hacer una pregunta

1. Abra la página **Asistente de ventas** del panel.
2. Escriba la pregunta en lenguaje natural, por ejemplo: "¿cuánto vendimos en
   total?".
3. Pulse Enviar y lea la respuesta junto con sus fuentes.

### 3.2 Consultas que entiende

| Consulta | Ejemplo |
|---|---|
| Ventas totales | ¿Cuánto vendimos en total? |
| Facturas | ¿Cuántas facturas hay? |
| Ticket promedio | ¿Cuál es el ticket promedio? |
| Unidades | ¿Cuántas unidades se vendieron? |
| Ranking de productos | ¿Cuáles son los productos más vendidos? |
| Ventas por local | Ventas por local |
| Ventas por sección | Ventas por sección |
| Ventas por producto | ¿Cuánto vendió Mini Lorito? |
| Tendencia | Tendencia mensual de ventas |
| Comparación | Comparar 2007 con 2008 |

### 3.3 Cómo leer la respuesta

Cada respuesta incluye tres elementos:

- **Respuesta:** el texto con las cifras.
- **Fuentes:** el servicio y el endpoint de donde provienen los datos.
- **Verificada:** indica si la respuesta está respaldada por el Data Warehouse.

Si la respuesta indica que no está verificada, no use esas cifras para tomar
decisiones: el asistente no encontró datos que las respalden.

### 3.4 Preguntas fuera de alcance

Si la pregunta no corresponde a ninguna consulta aprobada, el asistente responde
que no hay datos disponibles. Esto es intencional: el asistente no ejecuta SQL
libre ni improvisa cifras.

### 3.5 Modo general

El panel ofrece además un modo de conversación general que utiliza un modelo
local. Sus respuestas se muestran separadas y marcadas como **no verificadas**,
porque no provienen del Data Warehouse.

---

## 4. Avisos y monitoreo

### 4.1 Qué es un aviso

Un aviso es una notificación automática que se genera cuando un indicador cruza
un umbral definido. Cada aviso incluye fecha, tipo, severidad, valor observado,
umbral y una acción sugerida. Los avisos repetidos se agrupan para no generar
notificaciones duplicadas.

### 4.2 Reglas configuradas

| Código | Severidad | Condición | Acción sugerida |
|---|---|---|---|
| `VENTAS_BAJAS` | Advertencia | Ventas del periodo menores a S/ 1000 | Revisar surtido y campañas; confirmar la carga |
| `TICKET_BAJO` | Advertencia | Ticket promedio menor a S/ 200 | Revisar mezcla de productos y precios |
| `CAIDA_VENTAS` | Crítica | Caída mayor al 15 % frente al periodo anterior | Revisar locales y productos con mayor caída |
| `MODELO_SIN_ENTRENAR` | Informativa | Menos de 8 periodos o modelo no entrenado | Acumular historia antes de predecir |
| `MAE_ALTO` | Advertencia | Error del modelo mayor a 500 | Reentrenar y no publicar predicciones |
| `RECHAZOS_ALTOS` | Crítica | Más de 10 filas rechazadas sin resolver | Corregir la causa y reprocesar |

### 4.3 Dónde consultarlos

1. Abra `http://localhost:8004/monitor`.
2. Revise la lista ordenada por fecha y severidad.
3. Cada fila muestra el indicador, el valor observado y el umbral.

### 4.4 Reconocer un aviso

Cuando una persona ya revisó un aviso, puede marcarlo como reconocido. El aviso
deja de aparecer como pendiente, pero se conserva el registro histórico.

### 4.5 Simular un aviso

Para comprobar que el canal funciona sin esperar una condición real, el sistema
permite generar un aviso de prueba. Estos avisos quedan marcados como simulados y
se pueden excluir de los listados.

### 4.6 Qué hacer según la severidad

| Severidad | Tiempo de respuesta | Acción |
|---|---|---|
| Crítica | Inmediata | Revisar la causa y confirmar que los datos estén completos |
| Advertencia | Mismo día | Analizar la tendencia y documentar la decisión |
| Informativa | Cuando haya historia | Planificar la siguiente carga o el entrenamiento |

---

## 5. Bot de Telegram del restaurante

### 5.1 Acceso

1. Abra el enlace del bot que le entregó el administrador.
2. Pulse **Iniciar** o envíe `/start`.
3. Use el menú de botones para navegar sin escribir comandos.

### 5.2 Comandos del cliente

| Comando | Para qué sirve |
|---|---|
| `/start` | Abrir el menú principal |
| `/menu` | Ver las categorías y los platos |
| `/carrito` | Revisar y modificar el pedido |
| `/cancelar` | Cancelar el pedido en curso |
| `/compartir` | Obtener el enlace para compartir el bot |
| `/miid` | Ver el identificador de Telegram del usuario |

### 5.3 Categorías del menú

El catálogo incluye entradas, económicos, clásicas, salsas, especiales, alitas y
boneless, loaded fries, sándwiches de pollo, combo familiar, mamalonas, bebidas y
promociones. Los precios se expresan en lempiras (L.).

### 5.4 Hacer un pedido

1. Abra el menú y elija una categoría.
2. Seleccione un plato para agregarlo al carrito.
3. Ajuste cantidades o elimine productos desde el carrito.
4. Pulse **Finalizar pedido**.
5. Elija **Delivery** o **Retiro en local**.
6. Confirme el pedido. El bot envía el resumen al administrador y muestra el
   número de pedido al cliente.

Antes de confirmar, el bot valida que el carrito no esté vacío. Si el pedido se
cancela, no se registra ninguna venta.

### 5.5 Reservas

Desde el menú principal puede iniciar una reserva. El bot solicita los datos
necesarios y envía la solicitud al administrador para su confirmación.

### 5.6 Panel web de pedidos

El administrador puede abrir `http://localhost:3000/?token=SU_TOKEN`.

| Función | Descripción |
|---|---|
| Lista de pedidos | Se actualiza automáticamente cada cinco segundos |
| Filtros | Por estado y por fecha |
| Cambio de estado | Avisa al cliente por Telegram |
| Exportación | Descarga Excel o CSV del cierre del día |
| Estadísticas | Totales por estado y ventas del periodo |

El token del panel es personal. No lo comparta ni lo publique en capturas.

### 5.7 Comandos del administrador

| Comando | Para qué sirve |
|---|---|
| `/pedidos` | Ver los pedidos recientes |
| `/pendientes` | Ver solo los pedidos pendientes |
| `/compartir` | Enviar el enlace del bot a un cliente |

### 5.8 Estados de un pedido

| Estado | Significado |
|---|---|
| `pendiente` | Recibido y aún no iniciado |
| `en_preparacion` | En preparación en cocina |
| `entregado` | Entregado al cliente |
| `cancelado` | Anulado por el administrador |

Cada cambio de estado se refleja en el panel y se notifica al cliente por
Telegram.

---

## 6. Problemas frecuentes

| Síntoma | Causa probable | Solución |
|---|---|---|
| El panel no carga | La API no está iniciada | Iniciar `core-api` en el puerto 8000 |
| "No se pudo conectar con la API" | Dirección o puerto incorrecto | Revisar la variable `CORE_API_URL` |
| Periodo vacío | Fechas fuera del rango de datos | Ampliar el rango o quitar filtros |
| El asistente responde "sin datos" | Pregunta fuera de las consultas aprobadas | Usar una de las consultas de la sección 3.2 |
| No aparecen avisos | No se ha evaluado el motor | Ejecutar la evaluación del servicio |
| El bot no responde | Token inválido o proceso detenido | Revisar `.env` y reiniciar el bot |
| El bot no avisa al cliente | Identificador de chat incorrecto | Verificar `ADMIN_CHAT_ID` y el estado del pedido |
| El panel del bot rechaza el acceso | Token ausente o incorrecto | Abrir la URL con `?token=` correcto |
| El modelo no predice | Historia insuficiente | Acumular más periodos de ventas |

---

## 7. Glosario

| Término | Definición |
|---|---|
| Data Warehouse | Base organizada para analizar datos históricos |
| ETL | Proceso de extracción, transformación y carga |
| KPI | Indicador clave de desempeño |
| Staging | Zona intermedia donde se preparan los datos |
| Watermark | Marca que indica hasta dónde se cargaron los datos |
| Cuarentena | Lugar donde se guardan las filas rechazadas |
| Grounded | Respuesta respaldada por datos verificables |
| Aviso | Notificación automática por umbral superado |

---

## 8. Buenas prácticas y límites

- **No inventar cifras.** Si el panel, el asistente o el modelo no tienen datos,
  lo indican de forma explícita.
- **Revisar la fecha de actualización.** Una cifra correcta pero antigua puede
  llevar a una decisión equivocada.
- **Usar los filtros.** Los totales sin filtro mezclan locales y secciones.
- **Respetar el alcance de los datos.** La fuente actual tiene cinco líneas y un
  solo mes; el modelo predictivo responde "datos insuficientes" y no publica
  métricas inventadas.
- **Proteger los accesos.** El token del panel del bot y las credenciales del
  entorno son personales.

---

## 9. Dónde encontrar más ayuda

| Documento | Contenido |
|---|---|
| `data-platform/README.md` | Puesta en marcha del proyecto |
| `data-platform/documentation/manual.md` | Instalación, operación y recuperación |
| `data-platform/documentation/informe_final.md` | Resultados y trazabilidad |
| `data-platform/documentation/api_contratos.md` | Contratos de la API |
| `data-platform/documentation/genai.md` | Alcance del asistente |
| `data-platform/documentation/alertas.md` | Reglas y canal de avisos |
| `bot-telegram/README.md` | Detalle del bot y su arquitectura |
| `bot-telegram/web/README.md` | Panel web de pedidos y su API |
