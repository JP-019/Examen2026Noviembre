# Reglas de código limpio

## 1. Propósito y claridad
- Escribe código que explique su intención sin necesidad de comentarios largos.
- Cada función debe hacer una sola cosa bien y con un nombre claro.
- Evita duplicación de lógica; si aparece el mismo patrón tres veces, extrae una función o utilidad.

## 2. Nombres
- Usa nombres descriptivos para variables, funciones, clases, archivos y constantes.
- Evita abreviaturas innecesarias (`tmp`, `datax`, `obj`, `val`) salvo que sean estándar y ampliamente entendidas.
- Los booleanos deben leerse como frases afirmativas: `isReady`, `hasAccess`, `canPublish`.
- Los nombres deben reflejar el dominio del problema, no la implementación técnica.

## 3. Funciones y métodos
- Las funciones deben ser pequeñas y seguir una sola responsabilidad.
- Preferible pocas entradas, bien definidas, y sin efectos secundarios ocultos.
- Si una función necesita demasiados parámetros, probablemente esté haciendo demasiado.
- No dejes lógica profunda anidada; extrae condiciones y validaciones a funciones separadas.
- Evita funciones con más de una responsabilidad o más de una razón para cambiar.

## 4. Comentarios y documentación
- El código debe ser legible por sí mismo.
- Comenta solo lo que no puede inferirse fácilmente: decisiones de negocio, restricciones, razones no obvias.
- Evita comentarios que repitan lo que ya dice el nombre.
- Si un comentario necesita explicar el código, probablemente el código necesita mejorarse.

## 5. Estructura y organización
- Mantén un orden lógico dentro de archivos y módulos.
- Agrupa funciones relacionadas y separa responsabilidades por dominio o capa.
- No mezcles infraestructura, lógica de negocio y presentación en la misma sección sin justificación clara.
- Mantén archivos y carpetas con nombres consistentes.

## 6. Manejo de errores
- No ocultes errores ni los ignores silenciosamente.
- Maneja excepciones con mensajes claros y contextuales.
- Valida entradas, casos límite y condiciones de fallo antes de ejecutar lógica crítica.
- Si algo puede fallar, debe quedar explícito cómo se comporta.

## 7. Testing y validación
- Escribe pruebas para la lógica no trivial.
- Los tests deben validar comportamiento, no detalles de implementación.
- Si corriges un bug, añade una prueba que lo cubra.
- El código debe poder verificarse con pruebas automáticas y ejecuciones reproducibles.

## 8. Simplicidad y mantenibilidad
- Prefiere soluciones simples y directas sobre soluciones ingeniosas.
- Elimina código muerto, duplicado y condiciones innecesarias.
- Si una solución se vuelve difícil de seguir, probablemente no es la mejor opción.
- El objetivo es que el siguiente desarrollador entienda el código sin esfuerzo.

## 9. Consistencia del proyecto
- Sigue el estilo del repositorio y las convenciones ya existentes.
- Si se cambia una convención, hazla de manera intencional y consistente.
- Revisa el código antes de cerrarlo: nombres, estructura, legibilidad, validación y pruebas.

## 10. Regla final
- Un código limpio no es un código “bonito” sólo a la vista; es un código fácil de leer, mantener, probar y cambiar sin miedo.
