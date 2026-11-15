# Convierte un HTML de informe a .docx con formato APA 7 (Windows + Microsoft Word).
# Uso:
#   powershell -NoProfile -ExecutionPolicy Bypass -File html-to-apa-docx.ps1 `
#     -HtmlPath "C:\ruta\informe.html" -DocxPath "C:\ruta\INFORME.docx"
#
# El HTML debe incluir un parrafo con el marcador exacto [[TOC]] donde se
# insertara el indice automatico.

param(
  [Parameter(Mandatory = $true)][string]$HtmlPath,
  [Parameter(Mandatory = $true)][string]$DocxPath
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $HtmlPath)) {
  throw "No existe el HTML: $HtmlPath"
}

$word = $null
$doc = $null

try {
  $word = New-Object -ComObject Word.Application
  $word.Visible = $false
  $word.DisplayAlerts = 0

  $doc = $word.Documents.Open($HtmlPath)

  # ---- Pagina carta y margenes de 1 pulgada (APA 7) ----
  $ps = $doc.PageSetup
  $ps.PageWidth = 612
  $ps.PageHeight = 792
  $ps.TopMargin = 72
  $ps.BottomMargin = 72
  $ps.LeftMargin = 72
  $ps.RightMargin = 72

  # ---- Tipografia base: Times New Roman 12, doble espacio ----
  $doc.Content.Font.Name = "Times New Roman"
  $doc.Content.Font.Size = 12
  $doc.Content.ParagraphFormat.SpaceBefore = 0
  $doc.Content.ParagraphFormat.SpaceAfter = 0

  # ---- Estilos de titulos (constantes integradas: -1 Normal, -2 H1, -3 H2, -4 H3) ----
  $styles = $doc.Styles
  $normal = $styles.Item(-1)
  $normal.Font.Name = "Times New Roman"
  $normal.Font.Size = 12
  $normal.ParagraphFormat.LineSpacingRule = 2
  $normal.ParagraphFormat.SpaceBefore = 0
  $normal.ParagraphFormat.SpaceAfter = 0

  $headingSpecs = @(
    @{ Id = -2; Align = 1; Italic = $false },
    @{ Id = -3; Align = 0; Italic = $false },
    @{ Id = -4; Align = 0; Italic = $true }
  )
  foreach ($spec in $headingSpecs) {
    $st = $styles.Item($spec.Id)
    $st.Font.Name = "Times New Roman"
    $st.Font.Size = 12
    $st.Font.Bold = $true
    $st.Font.Italic = $spec.Italic
    $st.Font.Color = 0
    $st.ParagraphFormat.Alignment = $spec.Align
    $st.ParagraphFormat.LineSpacingRule = 2
    $st.ParagraphFormat.SpaceBefore = 0
    $st.ParagraphFormat.SpaceAfter = 0
    $st.ParagraphFormat.FirstLineIndent = 0
    $st.ParagraphFormat.KeepWithNext = $true
  }

  # ---- Estilos del indice (TOC/TDC) en doble espacio, si existen ----
  foreach ($st in $styles) {
    try {
      if ($st.NameLocal -match '(?i)^(TOC|TDC)\s*[1-3]$') {
        $st.Font.Name = "Times New Roman"
        $st.Font.Size = 12
        $st.ParagraphFormat.LineSpacingRule = 2
        $st.ParagraphFormat.SpaceBefore = 0
        $st.ParagraphFormat.SpaceAfter = 0
      }
    } catch {}
  }

  # ---- Reemplazar [[TOC]] por un indice automatico ----
  $tocInserted = $false
  $rng = $doc.Content
  $find = $rng.Find
  $find.ClearFormatting()
  $find.Text = "[[TOC]]"
  $find.Forward = $true
  $find.Wrap = 1
  $find.MatchCase = $true
  $find.MatchWildcards = $false
  if ($find.Execute()) {
    $rng.Text = ""
    $rng.Collapse(1)
    $doc.TablesOfContents.Add($rng, $true, 1, 3) | Out-Null
    $tocInserted = $true
  }

  # ---- Interlineado doble fuera de tablas (APA) ----
  foreach ($p in $doc.Paragraphs) {
    $inTable = $false
    try { $inTable = [bool]$p.Range.Information(12) } catch { $inTable = $false }
    if ($inTable) {
      $p.Format.LineSpacingRule = 0
    } else {
      $p.Format.LineSpacingRule = 2
    }
    $p.Format.SpaceBefore = 0
    $p.Format.SpaceAfter = 0
  }

  # ---- Tablas mas compactas para evitar desbordes ----
  foreach ($t in $doc.Tables) {
    $t.Range.Font.Name = "Times New Roman"
    $t.Range.Font.Size = 10
    $t.Range.ParagraphFormat.LineSpacingRule = 0
    $t.Range.ParagraphFormat.SpaceBefore = 0
    $t.Range.ParagraphFormat.SpaceAfter = 0
  }

  # ---- Marcadores de estructura: portada e indice ----
  foreach ($marker in @("[[PORTADA]]", "[[INDICE]]")) {
    $mr = $doc.Content
    $mf = $mr.Find
    $mf.ClearFormatting()
    $mf.Text = $marker
    $mf.Forward = $true
    $mf.Wrap = 1
    $mf.MatchCase = $true
    $mf.MatchWildcards = $false
    if ($mf.Execute()) {
      $mpara = $mr.Paragraphs.Item(1)
      $mr.Text = ""
      $mpara.Format.PageBreakBefore = $true
    }
  }

  # ---- Salto de pagina antes de cada titulo de nivel 1 ----
  foreach ($p in $doc.Paragraphs) {
    try {
      if ($p.Style.NameLocal -eq "Heading 1") { $p.Format.PageBreakBefore = $true }
    } catch {}
  }

  # ---- Encabezado: numero de pagina a la derecha; sin numero en la hoja en blanco ----
  $section = $doc.Sections.Item(1)
  $section.PageSetup.DifferentFirstPageHeaderFooter = $true
  $header = $section.Headers.Item(1)
  $header.LinkToPrevious = $false
  $header.Range.Text = ""
  $header.Range.ParagraphFormat.Alignment = 2
  $header.Range.Font.Name = "Times New Roman"
  $header.Range.Font.Size = 12
  $header.Range.Fields.Add($header.Range, 33) | Out-Null

  # ---- Actualizar indice y campos con la paginacion final ----
  if ($tocInserted) {
    try {
      $toc = $doc.TablesOfContents.Item(1)
      $toc.Update()
    } catch {}
  }
  $doc.Fields.Update() | Out-Null

  # ---- Guardar como .docx (wdFormatXMLDocument = 16) ----
  if (Test-Path -LiteralPath $DocxPath) {
    Remove-Item -LiteralPath $DocxPath -Force
  }
  $doc.SaveAs2($DocxPath, 16)
  $doc.Close([ref]$false)
  $doc = $null

  Write-Output ("OK: " + $DocxPath)
}
finally {
  if ($doc) {
    try { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($doc) | Out-Null } catch {}
  }
  if ($word) {
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
  }
  [GC]::Collect()
  [GC]::WaitForPendingFinalizers()
}
