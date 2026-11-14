# ADR-005 - API FastAPI y frontend Streamlit desacoplado

- **Estado:** Aceptada
- **Fecha:** 2026-11-11

## Contexto

La regla de oro prohibe que el frontend se conecte directo a SQL Server. El tiempo
disponible es de 3 dias y el dashboard debe mostrar KPIs validados.

## Decision

- **Backend:** FastAPI + Uvicorn, acceso al DW con pyodbc y consultas
  **parametrizadas**. Endpoints versionados bajo `/api/v1`.
- **Frontend:** Streamlit consumiendo solo la API por HTTP.
- **Contrato:** esquemas Pydantic para respuestas, `/docs` autogenerado.
- Si falta tiempo, React se reemplaza por Streamlit (ya es la eleccion base).

## Consecuencias

- Positivas: separacion real de responsabilidades, mismo backend sirve al dashboard,
  al asistente GenAI y al motor de alertas.
- Negativas: dos procesos para la demo (API y dashboard); se resuelve con un script
  de arranque unico documentado en el README.

## Alternativas descartadas

| Alternativa | Motivo de descarte |
|---|---|
| Streamlit conectado directo al DW | Viola la regla de oro |
| React + Vite | Mas tiempo de desarrollo y build para 3 dias |
| .NET / Node | El equipo ya usa Python para ETL y ML |
