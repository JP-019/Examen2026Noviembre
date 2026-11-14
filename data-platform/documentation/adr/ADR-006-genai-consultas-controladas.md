# ADR-006 - GenAI con consultas aprobadas

- **Estado:** Aceptada
- **Fecha:** 2026-11-11

## Contexto

El asistente debe responder en lenguaje natural sobre los datos sin inventar cifras
y sin ejecutar SQL arbitrario con privilegios elevados. Ademas, no hay presupuesto
para un servicio externo de LLM.

## Decision

1. El modelo **nunca** recibe acceso al motor: el backend expone un catalogo de
   **consultas aprobadas** (vistas y consultas parametrizadas con nombre).
2. El modelo solo puede elegir una consulta del catalogo y sus parametros validados.
3. La respuesta se arma con los resultados reales y cita periodo y fuente.
4. Si no hay consulta aplicable o no hay filas, responde
   **"no hay datos suficientes"**.
5. **Ollama local** como motor generativo; si no esta disponible, un modo
   determinista por reglas mantiene la demo funcionando y se identifica como tal.
6. Se registran pregunta, consulta elegida, parametros y tiempo, sin datos personales.

## Consecuencias

- Positivas: cero riesgo de SQL injection por parte del modelo, respuestas
  verificables, funciona sin internet ni API keys.
- Negativas: cobertura limitada a las preguntas del catalogo; se documenta como
  limite explicito.

## Alternativas descartadas

| Alternativa | Motivo de descarte |
|---|---|
| Text-to-SQL libre | Riesgo de injection y de cifras inventadas |
| LLM cloud con API key | Costo, secreto en el repo y dependencia de red |
| Respuestas precalculadas fijas | No demuestra integracion con el DW |
