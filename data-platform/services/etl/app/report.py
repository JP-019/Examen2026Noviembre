"""Reporte de calidad y reconciliacion entre capas (evidencia T06 / T08)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pyodbc

from . import db
from .config import PLATFORM_ROOT

DEFAULT_OUTPUT = PLATFORM_ROOT / "documentation" / "evidencias" / "T06_calidad_reconciliacion.md"

LATEST_RUNS_SQL = """
SELECT pipeline_name, source_object, target_object, status,
       rows_read, rows_inserted, rows_updated, rows_rejected,
       start_time, end_time, error_detail
FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY pipeline_name, source_object ORDER BY execution_id DESC) AS rn
    FROM audit.etl_execution
) x
WHERE rn = 1
ORDER BY pipeline_name, source_object
"""

QUARANTINE_SQL = """
SELECT rule_code, COUNT(*) AS rechazos
FROM quarantine.rejected_row
GROUP BY rule_code
ORDER BY rule_code
"""

RECONCILIATION_SQL = """
SELECT 'Fuente Venta.dbo.Factura_Detalle' AS capa, COUNT(*) AS filas,
       CAST(SUM(CAST(Cantidad AS decimal(18,2)) * PrecioSinImporte) AS decimal(18,2)) AS importe
FROM Venta.dbo.Factura_Detalle
UNION ALL
SELECT 'clean.FacturaDetalle', COUNT(*), CAST(SUM(ImporteLinea) AS decimal(18,2)) FROM clean.FacturaDetalle
UNION ALL
SELECT 'ready.Ventas', COUNT(*), CAST(SUM(ImporteLinea) AS decimal(18,2)) FROM ready.Ventas
UNION ALL
SELECT 'dw.FactVentas', COUNT(*), CAST(SUM(ImporteLinea) AS decimal(18,2)) FROM dw.FactVentas
"""

COUNTS_SQL = """
SELECT 'raw' AS capa, COUNT(*) AS filas FROM (
    SELECT 1 AS x FROM raw.Factura UNION ALL SELECT 1 FROM raw.FacturaDetalle
    UNION ALL SELECT 1 FROM raw.Producto UNION ALL SELECT 1 FROM raw.Local
    UNION ALL SELECT 1 FROM raw.[Version] UNION ALL SELECT 1 FROM raw.Seccion
    UNION ALL SELECT 1 FROM raw.Rubro UNION ALL SELECT 1 FROM raw.Categoria
    UNION ALL SELECT 1 FROM raw.Familia UNION ALL SELECT 1 FROM raw.SubFamilia
) r
UNION ALL SELECT 'clean', COUNT(*) FROM (
    SELECT 1 AS x FROM clean.Factura UNION ALL SELECT 1 FROM clean.FacturaDetalle
    UNION ALL SELECT 1 FROM clean.Producto UNION ALL SELECT 1 FROM clean.Local
    UNION ALL SELECT 1 FROM clean.[Version] UNION ALL SELECT 1 FROM clean.Seccion
    UNION ALL SELECT 1 FROM clean.Rubro UNION ALL SELECT 1 FROM clean.Categoria
    UNION ALL SELECT 1 FROM clean.Familia UNION ALL SELECT 1 FROM clean.SubFamilia
) c
UNION ALL SELECT 'ready', COUNT(*) FROM ready.Ventas
UNION ALL SELECT 'dw.FactVentas', COUNT(*) FROM dw.FactVentas
UNION ALL SELECT 'dw.DimProducto', COUNT(*) FROM dw.DimProducto
UNION ALL SELECT 'dw.DimLocal', COUNT(*) FROM dw.DimLocal
UNION ALL SELECT 'dw.DimVersion', COUNT(*) FROM dw.DimVersion
"""

WATERMARK_SQL = """
SELECT pipeline_name, source_object, watermark_column, watermark_value, updated_at
FROM audit.etl_watermark
ORDER BY source_object
"""


def _table(headers: list[str], rows: list[dict[str, Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        cells = []
        for header in headers:
            value = row.get(header)
            if value is None:
                value = ""
            cells.append(str(value).replace("|", "\\|"))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def build(conn: pyodbc.Connection, output: Path = DEFAULT_OUTPUT) -> Path:
    latest = db.fetch_all(conn, LATEST_RUNS_SQL)
    quarantine = db.fetch_all(conn, QUARANTINE_SQL)
    reconciliation = db.fetch_all(conn, RECONCILIATION_SQL)
    counts = db.fetch_all(conn, COUNTS_SQL)
    watermarks = db.fetch_all(conn, WATERMARK_SQL)

    generated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    parts: list[str] = [
        "# Reporte de calidad y reconciliacion",
        "",
        f"Generado: {generated}",
        "",
        "Evidencia automatica de T05 (extraccion), T06 (calidad) y T08 (reconciliacion).",
        "Se regenera con `python -m app quality-report`.",
        "",
        "## 1. Ultima ejecucion por objeto",
        "",
        _table(
            ["pipeline", "origen", "destino", "estado", "leidas", "insertadas", "actualizadas", "rechazadas"],
            [
                {
                    "pipeline": r["pipeline_name"],
                    "origen": r["source_object"],
                    "destino": r["target_object"],
                    "estado": r["status"],
                    "leidas": r["rows_read"],
                    "insertadas": r["rows_inserted"],
                    "actualizadas": r["rows_updated"],
                    "rechazadas": r["rows_rejected"],
                }
                for r in latest
            ],
        ),
        "",
        "## 2. Rechazos por regla (cuarentena)",
        "",
        "Sin rechazos registrados." if not quarantine else _table(["regla", "rechazos"], [
            {"regla": r["rule_code"], "rechazos": r["rechazos"]} for r in quarantine
        ]),
        "",
        "## 3. Reconciliacion entre capas",
        "",
        _table(["capa", "filas", "importe"], reconciliation),
        "",
        "La diferencia de filas entre la fuente y `clean` se explica por registros en",
        "cuarentena. La diferencia entre `ready` y `dw.FactVentas` debe ser cero.",
        "",
        "## 4. Volumen por capa",
        "",
        _table(["capa", "filas"], counts),
        "",
        "## 5. Watermarks",
        "",
        "Sin watermarks registrados." if not watermarks else _table(
            ["pipeline", "objeto", "columna", "valor", "actualizado"],
            [
                {
                    "pipeline": r["pipeline_name"],
                    "objeto": r["source_object"],
                    "columna": r["watermark_column"],
                    "valor": r["watermark_value"],
                    "actualizado": r["updated_at"],
                }
                for r in watermarks
            ],
        ),
        "",
    ]

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(parts), encoding="utf-8")
    return output
