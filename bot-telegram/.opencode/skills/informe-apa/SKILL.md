---
name: informe-apa
description: Genera informes y reportes en Word (.docx) con estructura fija y normas APA 7 (hoja en blanco, portada, índice automático, introducción, objetivos, cuerpo, anexos, conclusiones y bibliografía). Úsala cuando el usuario pida un informe, reporte, documento APA, trabajo en Word o un .docx con esa estructura.
---

# Informe APA 7 en Word

## Cuándo usar esta skill
- El usuario pide un **informe**, **reporte**, **documento APA 7**, **trabajo en Word** o un archivo **.docx**.
- Se necesita una estructura académica fija y un índice con números de página.
- Se trabaja en Windows con Microsoft Word instalado.

## Estructura y orden obligatorio
El documento debe llevar exactamente este orden:

1. **Hoja en blanco** (hoja de respeto, sin numeración).
2. **Portada** (APA 7).
3. **Índice** (automático, con números de página).
4. **Introducción**.
5. **Objetivos** (general y específicos).
6. **Cuerpo** (desarrollo con subtítulos).
7. **Anexos**.
8. **Conclusiones**.
9. **Bibliografía**.

Cada título de nivel 1 comienza en una página nueva. No agregar secciones fuera de este orden.

## Reglas de formato (APA 7)
- Tamaño carta, márgenes de 1 pulgada.
- Times New Roman 12, interlineado doble, sin espacio antes/después de párrafo.
- Párrafos justificados con sangría de primera línea de 0.5 pulgadas.
- Jerarquía de títulos (se controla con `h1`, `h2`, `h3`):
  - Nivel 1 (`h1`): centrado, negrita.
  - Nivel 2 (`h2`): alineado a la izquierda, negrita.
  - Nivel 3 (`h3`): alineado a la izquierda, negrita y cursiva.
- Tablas numeradas (Tabla 1, Tabla 2, ...). Número en negrita y título en cursiva arriba de la tabla. Fuente 10, líneas horizontales, sin cuadrícula completa.
- Bibliografía en orden alfabético con sangría francesa.
- Redacción en español formal, sin emojis. Citas y referencias en formato APA 7.

## Flujo de trabajo en Windows (obligatorio)

### 1. Analizar el objeto del informe
Revisa el código, documentos o datos reales antes de redactar. No inventes métricas, archivos, endpoints ni funcionalidades.

### 2. Crear el HTML del informe
Escribe el contenido en un archivo temporal, por ejemplo:

`C:\Users\<usuario>\AppData\Local\Temp\opencode\informe.html`

Usa exactamente este esqueleto (respeta los marcadores):

```html
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<style>
  @page { size: 8.5in 11in; margin: 1in; }
  body { font-family: "Times New Roman", Times, serif; font-size: 12pt; }
  p { margin: 0; line-height: 2; text-align: justify; }
  p.body { text-indent: 0.5in; }
  p.center { text-align: center; text-indent: 0; }
  p.ref { text-indent: -0.5in; margin-left: 0.5in; text-align: left; line-height: 2; }
  h1 { font-size: 12pt; font-weight: bold; text-align: center; margin: 0; line-height: 2; }
  h2 { font-size: 12pt; font-weight: bold; text-align: left; margin: 0; line-height: 2; }
  h3 { font-size: 12pt; font-weight: bold; font-style: italic; text-align: left; margin: 0; line-height: 2; }
  .cap { font-weight: bold; text-indent: 0; line-height: 2; }
  .capt { font-style: italic; text-indent: 0; line-height: 2; }
  table { border-collapse: collapse; width: 100%; font-size: 10pt; line-height: 1.15; }
  th { text-align: left; padding: 2pt 4pt; border-top: 1pt solid #000; border-bottom: 1pt solid #000; }
  td { padding: 2pt 4pt; }
  tr.last td { border-bottom: 1pt solid #000; }
  pre { font-family: "Courier New", monospace; font-size: 10pt; line-height: 1.15; }
</style>
</head>
<body>

<!-- 1. Hoja en blanco: debe ser el primer elemento -->
<p class="center">&nbsp;</p>

<!-- 2. Portada: el marcador [[PORTADA]] fuerza el salto de pagina -->
<p class="center" style="margin-top: 1.1in; font-weight: bold;">[[PORTADA]]Título del informe</p>
<p class="center">&nbsp;</p>
<p class="center">Nombre del autor</p>
<p class="center">Institución</p>
<p class="center">Curso</p>
<p class="center">Instructor</p>
<p class="center">Fecha</p>

<!-- 3. Índice: [[INDICE]] fuerza el salto y [[TOC]] se reemplaza por el índice -->
<p class="center" style="font-weight: bold;">[[INDICE]]Índice</p>
<p class="center">&nbsp;</p>
<p>[[TOC]]</p>

<!-- 4. Introducción -->
<h1>Introducción</h1>
<p class="body">...</p>

<!-- 5. Objetivos -->
<h1>Objetivos</h1>
<h2>Objetivo general</h2>
<p class="body">...</p>
<h2>Objetivos específicos</h2>
<ul>
  <li>...</li>
</ul>

<!-- 6. Cuerpo -->
<h1>Cuerpo</h1>
<h2>...</h2>
<p class="body">...</p>

<!-- 7. Anexos -->
<h1>Anexos</h1>
<h2>Anexo A. ...</h2>
<p class="body">...</p>

<!-- 8. Conclusiones -->
<h1>Conclusiones</h1>
<p class="body">...</p>

<!-- 9. Bibliografía -->
<h1>Bibliografía</h1>
<p class="ref">Autor. (Año). <i>Título</i>. Fuente.</p>

</body>
</html>
```

Reglas de los marcadores:
- `[[PORTADA]]`: va al inicio del texto del título de la portada. El script lo borra y fuerza el salto de página.
- `[[INDICE]]`: va al inicio del texto "Índice". El script lo borra y fuerza el salto de página.
- `[[TOC]]`: se reemplaza por el índice automático de Word (niveles 1 a 3).
- Los marcadores deben quedar eliminados al final. Verifícalo.

### 3. Convertir a .docx con el script incluido
Ejecuta (desde la raíz del proyecto):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".opencode\skills\informe-apa\scripts\html-to-apa-docx.ps1" `
  -HtmlPath "C:\Users\<usuario>\AppData\Local\Temp\opencode\informe.html" `
  -DocxPath "C:\ruta\del\proyecto\INFORME.docx"
```

El script aplica automáticamente: tamaño carta, márgenes de 1", Times New Roman 12, doble espacio, tablas compactas, numeración de página en el encabezado (sin número en la hoja en blanco), salto antes de la portada, el índice y cada título de nivel 1, e inserta/actualiza el índice automático.

### 4. Verificar el resultado
Abre el .docx con Word (COM) y comprueba:
- Número de páginas y de palabras.
- Que exista 1 índice (`TablesOfContents.Count`).
- Que los números del índice coincidan con las páginas reales.
- Que no queden los marcadores `[[PORTADA]]`, `[[INDICE]]` ni `[[TOC]]`.

Ejemplo de verificación:

```powershell
$f = "C:\ruta\del\proyecto\INFORME.docx"
$w = New-Object -ComObject Word.Application
$w.Visible = $false
$d = $w.Documents.Open($f, [ref]$false, [ref]$true)
$d.Repaginate()
"Paginas: " + $d.ComputeStatistics(2)
"Palabras: " + $d.ComputeStatistics(0)
"TOC: " + $d.TablesOfContents.Count
$d.Close([ref]$false)
$w.Quit()
```

## Notas importantes
- Si el usuario no dio nombre, institución, curso o instructor, usa marcadores entre corchetes en la portada y avísale que debe editarlos.
- La hoja en blanco cuenta como página 1 sin numeración; por eso la portada se muestra como página 2. Mantén la numeración natural para que el índice coincida con los encabezados.
- No cambies el orden de las secciones ni agregues un resumen/abstract salvo que el usuario lo pida expresamente.
- Si Word no está instalado o falla COM, informa el problema y entrega al menos el HTML con el contenido completo.
