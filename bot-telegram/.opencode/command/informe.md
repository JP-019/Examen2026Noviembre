---
description: Genera un informe en Word con formato APA 7 y la estructura estándar del proyecto.
agent: build
---

Genera un informe en Word (.docx) sobre el siguiente tema o proyecto:

$ARGUMENTS

Carga y sigue estrictamente la skill `informe-apa`. En particular:

1. Analiza primero el código, documentos o datos reales del tema.
2. Redacta el contenido en español formal, sin emojis, con citas y referencias APA 7.
3. Respeta este orden exacto: hoja en blanco, portada, índice, introducción, objetivos, cuerpo, anexos, conclusiones y bibliografía.
4. Crea el HTML temporal con los marcadores `[[PORTADA]]`, `[[INDICE]]` y `[[TOC]]`.
5. Convierte a .docx con el script de la skill.
6. Verifica páginas, índice y que no queden marcadores.
7. Si faltan datos de la portada (autor, institución, curso, instructor), usa corchetes y avísalo.

Al terminar, informa la ruta del .docx, el número de páginas y un resumen breve.
