# ADR-001 - Fuente de datos: SQL Server `Venta`

- **Estado:** Aceptada
- **Fecha:** 2026-11-11

## Contexto

La consigna propone WideWorldImporters (SQL Server) o Pagila (PostgreSQL). El equipo
dispone de una instancia local de SQL Server ya operativa con la base `Venta`, que
modela el proceso de ventas minoristas: facturas, lineas de factura, productos con
jerarquia comercial, locales y versiones de sistema. No hay Docker instalado en el
equipo de desarrollo.

## Decision

Usar la base `Venta` en SQL Server local como fuente del proyecto, accedida por
autenticacion de Windows. La configuracion `auto` de `TrustServerCertificate`
solo confia en certificados autofirmados para servidores loopback; para servidores
remotos se valida el certificado. La carga de WideWorldImporters queda documentada
como alternativa si se necesita mayor volumen.

## Consecuencias

- Positivas: el ambiente ya funciona, no requiere instalacion adicional, el modelo
  de negocio es entendible y el dominio (ventas) coincide con el alcance.
- Negativas: el volumen es muy bajo (~5 facturas, ~5 lineas), insuficiente para
  analisis y para ML. Se mitigara generando datos sinteticos **etiquetados como
  simulacion** y manteniendo separado el dataset real.
- La falta de tablas de cliente y empleado limita el modelo dimensional a las
  dimensiones disponibles (ver ADR-004).

## Alternativas descartadas

| Alternativa | Motivo de descarte |
|---|---|
| WideWorldImporters via Docker | Docker no instalado; restore pesado para 3 dias |
| Pagila (PostgreSQL) | No hay PostgreSQL instalado y no aporta ventajas al alcance |
| CSV planos | Se pierde el ejercicio de extraccion desde un motor relacional |
