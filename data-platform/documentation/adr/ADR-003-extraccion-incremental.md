# ADR-003 - Extraccion batch incremental con watermark

- **Estado:** Aceptada
- **Fecha:** 2026-11-11

## Contexto

La fuente tiene bajas de ventas con fecha de operacion, pero no todas las tablas
exponen una columna de auditoria confiable (`UpdatedAt`). El pipeline debe ser
idempotente y auditable, y el volumen no justifica CDC ni streaming.

## Decision

1. **Carga inicial:** extraccion completa de las tablas del proceso de ventas.
2. **Carga incremental:** por columna de watermark cuando exista
   (`fecha` en `Factura`); para dimensiones pequeñas, comparacion por hash de fila.
3. **Watermark** persistido en `audit.etl_watermark` y actualizado **solo** si la
   ejecucion termina en estado `SUCCESS`.
4. **Ventana de solapamiento** de 1 dia para tolerar registros tardios.
5. **Idempotencia** por `MERGE` sobre la clave de negocio en `clean` y por
   `NOT EXISTS` sobre la clave de negocio + hash en `ready`.
6. **Eliminaciones:** la fuente no expone borrados logicos; se documenta que no se
   propagan eliminaciones y se detectan por reconciliacion de conteos.
7. Toda corrida escribe en `audit.etl_execution` con conteos y error detail.

## Consecuencias

- Positivas: reejecutar un lote no duplica filas ni altera resultados.
- Negativas: la deteccion de cambios en dimensiones por hash agrega costo de
  lectura completa; aceptable con el volumen actual.

## Alternativas descartadas

| Alternativa | Motivo de descarte |
|---|---|
| Full load diario | Innecesario y no demuestra incrementalidad |
| CDC de SQL Server | Requiere habilitar CDC y agentes; sobredimensionado |
| Streaming | Contradice el alcance batch declarado |
