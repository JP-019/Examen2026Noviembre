# ADR-007 - Arquitectura de microservicios

- **Estado:** Aceptada
- **Fecha:** 2026-11-13
- **Reemplaza parcialmente:** ADR-005 (un solo backend)

## Contexto

La primera version concentraba todo en un backend unico. El proyecto necesita
que cada componente (ingesta, API, dashboard, ML, GenAI, alertas) pueda entenderse,
probarse y evolucionar por separado, y que el evaluador pueda descubrir que hace
cada carpeta sin leer todo el codigo. Ademas, el equipo trabaja en paralelo sobre
tareas distintas.

## Decision

Adoptar **microservicios por capacidad de negocio**, con un servicio de catalogo
que publica el indice vivo de la plataforma.

| Servicio | Carpeta | Puerto | Responsabilidad | Tarea |
|---|---|---|---|---|
| `etl` | `services/etl` | - | Ingesta batch, staging, calidad, DW | T05, T06 |
| `catalog` | `services/catalog` | 8001 | Indice de servicios, carpetas y rutas | T03 |
| `core-api` | `services/core-api` | 8000 | Unica puerta de lectura al DW | T09 |
| `dashboard` | `services/dashboard` | 8501 | UI de KPIs y tendencias | T10 |
| `ml` | `services/ml` | 8002 | Entrenamiento y prediccion | T11 |
| `genai` | `services/genai` | 8003 | Preguntas con consultas aprobadas | T12 |
| `alerting` | `services/alerting` | 8004 | Reglas, alertas y monitoreo | T13 |

Reglas de convivencia:

1. Cada servicio tiene su propio `README.md`, `requirements.txt` y carpeta `app/`.
2. La comunicacion es por HTTP o por la base; nunca por importacion de codigo ajeno.
3. `core-api` es la unica puerta al DW para los servicios de consumo.
4. `etl` es el unico que escribe en `raw`, `clean`, `ready` y `dw`.
5. `catalog/platform.json` es la fuente de verdad del indice.
6. Sin secretos: cada servicio lee `.env`.

## Consecuencias

- Positivas: responsabilidades acotadas, desarrollo en paralelo, despliegue
  independiente, indice centralizado y trazabilidad tarea -> servicio.
- Negativas: mas procesos en la demo; se resuelve con `scripts/start_all.ps1`.
  Mayor complejidad de red local (puertos fijos documentados).
- La latencia entre servicios es aceptable para un batch diario y una demo local.

## Alternativas descartadas

| Alternativa | Motivo de descarte |
|---|---|
| Monolito FastAPI | Acopla tareas y dificulta el trabajo paralelo |
| Serverless | Sin infraestructura cloud ni presupuesto |
| Contenedores obligatorios | Docker no esta instalado en el equipo |
