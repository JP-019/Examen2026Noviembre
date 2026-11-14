# ADR-002 - Separacion de capas por esquemas en una instancia local

- **Estado:** Aceptada
- **Fecha:** 2026-11-11

## Contexto

La consigna pide bases o esquemas separados para fuente, staging y DW, con
trazabilidad entre capas. Docker Compose no esta instalado en el equipo.

## Decision

Una unica base `DataPlatform` con esquemas separados:

| Esquema | Rol |
|---|---|
| `raw` | copia fiel de la fuente, solo inserciones |
| `clean` | datos tipados, validados y estandarizados |
| `ready` | integracion lista para el DW |
| `dw` | modelo dimensional publicado |
| `audit` | ejecuciones, watermarks y linaje |
| `quarantine` | registros rechazados por reglas de calidad |

La base fuente `Venta` permanece **intacta** y separada, como solo-lectura.
Se entrega ademas un `docker-compose.yml` como via reproducible alternativa para
quien si tenga Docker, pero **no es requisito para la demo**.

## Consecuencias

- Positivas: separacion logica clara, permisos por esquema, respaldo simple,
  funciona hoy mismo en el equipo.
- Negativas: no hay aislamiento fisico entre staging y DW; un `DROP SCHEMA` mal
  ejecutado afecta a ambos. Se mitiga con permisos minimos y scripts idempotentes.
- El usuario tecnico de aplicacion tendra solo `SELECT` sobre `Venta`, `SELECT/INSERT/UPDATE`
  sobre `raw`, `clean`, `ready`, `audit`, `quarantine` y `SELECT` sobre `dw`.

## Alternativas descartadas

| Alternativa | Motivo de descarte |
|---|---|
| Tres bases separadas | Overhead de conexiones y despliegue sin beneficio en el alcance |
| Un solo esquema `dbo` | Sin trazabilidad ni separacion de responsabilidades |
| Docker obligatorio | No disponible en el equipo; bloquearia el Sprint 0 |
