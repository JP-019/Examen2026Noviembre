# Contexto del proyecto

Bot de Telegram para el restaurante "El Gordo" (Node.js) con panel web de pedidos
(Express). Módulos principales: `bot.js` (flujos), `menu.js` (catálogo),
`store.js` (persistencia en `orders.json`), `web/dashboard.js` (API + exportaciones).

- Instalar: `npm install`
- Ejecutar: `npm start`
- Nunca versionar `.env`, `orders.json` ni `node_modules`.

# Convención de commits

- Mensajes en español con Conventional Commits: `tipo(alcance): [Sprint N] descripción`.
- Agrupar en bloques/sprints lógicos y mantener el historial trazable.

# Informes y reportes

Cuando el usuario pida un **informe**, **reporte**, **documento APA 7**, **trabajo en
Word** o un **.docx**, usa la skill `informe-apa`
(`.opencode/skills/informe-apa/SKILL.md`) y su script
`.opencode/skills/informe-apa/scripts/html-to-apa-docx.ps1`.

Estructura y orden obligatorio del documento:

1. Hoja en blanco (sin numeración).
2. Portada (APA 7).
3. Índice automático con números de página.
4. Introducción.
5. Objetivos (general y específicos).
6. Cuerpo.
7. Anexos.
8. Conclusiones.
9. Bibliografía.

Formato: APA 7, tamaño carta, márgenes de 1", Times New Roman 12, doble espacio,
párrafos justificados con sangría de 0.5", títulos jerárquicos (`h1`/`h2`/`h3`),
tablas numeradas y referencias con sangría francesa. Sin emojis y en español formal.
