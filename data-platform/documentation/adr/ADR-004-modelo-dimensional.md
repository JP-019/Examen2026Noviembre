# ADR-004 - Modelo dimensional estrella

- **Estado:** Aceptada
- **Fecha:** 2026-11-11

## Contexto

El proceso de negocio es la venta minorista. La fuente registra cabecera de factura
y lineas de detalle, con jerarquia de producto, local y version de sistema.

## Decision

- **Grano:** una fila de `dw.FactVentas` = **una linea de factura**.
- **Dimensiones:** `DimTiempo`, `DimProducto`, `DimLocal`, `DimVersion`.
- **Claves sustitutas** enteras por dimension; la clave natural se conserva como
  atributo para trazabilidad.
- **Miembro desconocido** con clave `0` en cada dimension.
- **SCD Tipo 1**: la fuente no publica historial de cambios; el Tipo 2 se documenta
  como evolucion posible (columnas `FilaDesde`/`FilaHasta`/`EsVigente` ya previstas).
- No se crean `DimCliente` ni `DimEmpleado` porque la fuente no las contiene: se
  documenta la desviacion respecto de la plantilla de la consigna.

## Consecuencias

- Positivas: consultas simples, KPIs aditivos confiables, reconciliacion clara.
- Negativas: sin historial de atributos no se puede analizar "como era el producto
  cuando se vendio"; se acepta por alcance y se deja preparado para Tipo 2.

## Alternativas descartadas

| Alternativa | Motivo de descarte |
|---|---|
| Copo de nieve | Mas joins sin beneficio analitico |
| Modelo normalizado 3FN | No apto para BI |
| SCD Tipo 2 inmediato | La fuente no provee historial; seria historial inventado |
| Grano cabecera de factura | Impide analisis por producto |
