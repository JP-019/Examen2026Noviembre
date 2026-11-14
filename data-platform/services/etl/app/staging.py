"""Etapas de extraccion, limpieza e integracion del pipeline de ventas."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

import pyodbc

from . import audit, db, quality
from .config import OVERLAP_DAYS
from .specs import EXTRACT_SPECS, TableSpec


@dataclass
class Extracted:
    spec: TableSpec
    execution_id: int
    rows: list[dict[str, Any]]
    watermark_end: datetime | None


def extract(
    source: pyodbc.Connection,
    target: pyodbc.Connection,
    mode: str = "full",
    overlap_days: int = OVERLAP_DAYS,
) -> list[Extracted]:
    """Copia la fuente a raw. Raw es append-only: nunca se actualiza ni borra."""
    results: list[Extracted] = []
    for spec in EXTRACT_SPECS:
        watermark = None
        if mode == "incremental" and spec.watermark_column:
            watermark = audit.get_watermark(spec.source_object)

        params: tuple[Any, ...] = ()
        sql = spec.select_full
        if watermark and spec.select_incremental:
            sql = spec.select_incremental
            params = (watermark - timedelta(days=overlap_days),)

        with audit.run(f"sales_extract_{mode}", spec.source_object, spec.raw_table, watermark) as (execution_id, counts):
            rows = db.fetch_all(source, sql, params)
            counts.read = len(rows)
            if rows:
                values = [
                    tuple(row[column] for column in spec.raw_columns) + (execution_id,)
                    for row in rows
                ]
                db.executemany(target, spec.raw_insert_sql, values)
                counts.inserted = len(rows)
            target.commit()

            watermark_end = None
            if spec.watermark_column and rows:
                watermark_end = max(row[spec.watermark_column] for row in rows)

        # Solo se avanza el watermark si la corrida cerro en SUCCESS.
        if watermark_end is not None:
            audit.set_watermark(
                execution_id,
                spec.source_object,
                spec.watermark_column,
                watermark_end,
            )

        results.append(Extracted(spec, execution_id, rows, watermark_end))
    return results


def _upsert(conn: pyodbc.Connection, table: str, key_column: str, data: dict[str, Any], execution_id: int) -> str:
    """UPSERT por clave de negocio. Devuelve 'INSERT' o 'UPDATE'."""
    columns = list(data.keys())
    assignments = ", ".join(f"[{column}] = ?" for column in columns)
    cur = conn.cursor()
    try:
        cur.execute(
            f"UPDATE {table} SET {assignments}, _execution_id = ?, _loaded_at = SYSUTCDATETIME() "
            f"WHERE [{key_column}] = ?",
            [data[column] for column in columns] + [execution_id, data[key_column]],
        )
        if cur.rowcount > 0:
            return "UPDATE"
        column_list = ", ".join(f"[{column}]" for column in columns)
        placeholders = ", ".join("?" for _ in columns)
        cur.execute(
            f"INSERT INTO {table} ({column_list}, _execution_id, _loaded_at) "
            f"VALUES ({placeholders}, ?, SYSUTCDATETIME())",
            [data[column] for column in columns] + [execution_id],
        )
        return "INSERT"
    finally:
        cur.close()


def dedupe(rows: list[dict[str, Any]], key_column: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Conserva la ultima aparicion de cada clave y devuelve los duplicados.

    La fuente puede entregar la misma clave mas de una vez en un lote. Se queda
    con la ultima fila (supervivencia) y las anteriores se registran como DQ-013.
    """
    seen: dict[Any, dict[str, Any]] = {}
    duplicates: list[dict[str, Any]] = []
    for row in rows:
        key = row[key_column]
        if key in seen:
            # La aparicion anterior es la que se descarta; la ultima sobrevive.
            duplicates.append(seen[key])
        seen[key] = row
    return list(seen.values()), duplicates


def clean(target: pyodbc.Connection, extracted: list[Extracted]) -> dict[str, dict[str, int]]:
    """Valida y carga la zona clean. Cada regla fallida va a cuarentena."""
    by_name = {item.spec.name: item for item in extracted}
    summary: dict[str, dict[str, int]] = {}
    ctx: dict[str, set[Any]] = {"facturas": set(), "productos": set()}

    for spec in EXTRACT_SPECS:
        item = by_name.get(spec.name)
        if item is None:
            continue

        with audit.run("sales_clean", spec.raw_table, spec.clean_table) as (execution_id, counts):
            counts.read = len(item.rows)
            unique_rows, duplicates = dedupe(item.rows, spec.key_column)

            for row in duplicates:
                quality.reject(
                    target,
                    execution_id,
                    spec.source_object,
                    "DQ-013",
                    "Registro duplicado en el lote; se conserva la ultima aparicion",
                    row[spec.key_column],
                    row,
                )
                counts.rejected += 1

            for row in unique_rows:
                data = quality.to_clean_row(spec, row)
                errors = quality.validate(spec, data, ctx)
                if errors:
                    for rule_code, detail in errors:
                        quality.reject(
                            target,
                            execution_id,
                            spec.source_object,
                            rule_code,
                            detail,
                            data[spec.key_column],
                            row,
                        )
                    counts.rejected += 1
                    continue

                action = _upsert(target, spec.clean_table, spec.key_column, data, execution_id)
                if action == "INSERT":
                    counts.inserted += 1
                else:
                    counts.updated += 1
                audit.add_lineage(
                    target,
                    execution_id,
                    spec.source_object,
                    spec.clean_table,
                    row[spec.key_column],
                    action,
                )

            target.commit()

        summary[spec.name] = {
            "read": counts.read,
            "inserted": counts.inserted,
            "updated": counts.updated,
            "rejected": counts.rejected,
            "execution_id": execution_id,
        }

        if spec.name == "Producto":
            ctx["productos"] = {
                row["IdProducto"] for row in db.fetch_all(target, "SELECT IdProducto FROM clean.Producto")
            }
        if spec.name == "Factura":
            ctx["facturas"] = {
                row["IdFactura"] for row in db.fetch_all(target, "SELECT IdFactura FROM clean.Factura")
            }

    return summary


READY_MERGE_SQL = """
SET NOCOUNT ON;
DECLARE @acc TABLE (accion nvarchar(10));

MERGE ready.Ventas AS t
USING
(
    SELECT
        d.IdFacturaDetalle,
        f.IdFactura,
        f.NumeroFactura,
        f.Fecha,
        p.IdProducto,
        p.NombreProducto,
        p.IdSubFamilia,
        COALESCE(sf.NombreSubFamilia, 'Desconocido') AS NombreSubFamilia,
        sf.IdFamilia,
        COALESCE(fa.NombreFamilia, 'Desconocido') AS NombreFamilia,
        fa.IdCategoria,
        COALESCE(c.NombreCategoria, 'Desconocido') AS NombreCategoria,
        c.IdRubro,
        COALESCE(r.NombreRubro, 'Desconocido') AS NombreRubro,
        r.IdSeccion,
        COALESCE(s.NombreSeccion, 'Desconocido') AS NombreSeccion,
        f.IdLocal,
        COALESCE(l.NombreLocal, 'Desconocido') AS NombreLocal,
        f.IdVersion,
        COALESCE(v.NombreVersion, 'Desconocido') AS NombreVersion,
        d.Cantidad,
        d.PrecioUnitario,
        d.ImporteLinea
    FROM clean.FacturaDetalle d
    JOIN clean.Factura f       ON f.IdFactura = d.IdFactura
    JOIN clean.Producto p      ON p.IdProducto = d.IdProducto
    LEFT JOIN clean.SubFamilia sf ON sf.IdSubFamilia = p.IdSubFamilia
    LEFT JOIN clean.Familia fa    ON fa.IdFamilia = sf.IdFamilia
    LEFT JOIN clean.Categoria c   ON c.IdCategoria = fa.IdCategoria
    LEFT JOIN clean.Rubro r       ON r.IdRubro = c.IdRubro
    LEFT JOIN clean.Seccion s     ON s.IdSeccion = r.IdSeccion
    LEFT JOIN clean.Local l       ON l.IdLocal = f.IdLocal
    LEFT JOIN clean.[Version] v   ON v.IdVersion = f.IdVersion
) AS src
ON t.IdFacturaDetalle = src.IdFacturaDetalle
WHEN MATCHED THEN UPDATE SET
    IdFactura = src.IdFactura,
    NumeroFactura = src.NumeroFactura,
    Fecha = src.Fecha,
    IdProducto = src.IdProducto,
    NombreProducto = src.NombreProducto,
    IdSubFamilia = src.IdSubFamilia,
    NombreSubFamilia = src.NombreSubFamilia,
    IdFamilia = src.IdFamilia,
    NombreFamilia = src.NombreFamilia,
    IdCategoria = src.IdCategoria,
    NombreCategoria = src.NombreCategoria,
    IdRubro = src.IdRubro,
    NombreRubro = src.NombreRubro,
    IdSeccion = src.IdSeccion,
    NombreSeccion = src.NombreSeccion,
    IdLocal = src.IdLocal,
    NombreLocal = src.NombreLocal,
    IdVersion = src.IdVersion,
    NombreVersion = src.NombreVersion,
    Cantidad = src.Cantidad,
    PrecioUnitario = src.PrecioUnitario,
    ImporteLinea = src.ImporteLinea,
    _execution_id = ?,
    _loaded_at = SYSUTCDATETIME()
WHEN NOT MATCHED THEN INSERT
    (IdFacturaDetalle, IdFactura, NumeroFactura, Fecha,
     IdProducto, NombreProducto, IdSubFamilia, NombreSubFamilia,
     IdFamilia, NombreFamilia, IdCategoria, NombreCategoria,
     IdRubro, NombreRubro, IdSeccion, NombreSeccion,
     IdLocal, NombreLocal, IdVersion, NombreVersion,
     Cantidad, PrecioUnitario, ImporteLinea, _execution_id, _loaded_at)
VALUES
    (src.IdFacturaDetalle, src.IdFactura, src.NumeroFactura, src.Fecha,
     src.IdProducto, src.NombreProducto, src.IdSubFamilia, src.NombreSubFamilia,
     src.IdFamilia, src.NombreFamilia, src.IdCategoria, src.NombreCategoria,
     src.IdRubro, src.NombreRubro, src.IdSeccion, src.NombreSeccion,
     src.IdLocal, src.NombreLocal, src.IdVersion, src.NombreVersion,
     src.Cantidad, src.PrecioUnitario, src.ImporteLinea, ?, SYSUTCDATETIME())
OUTPUT $action INTO @acc;

SELECT accion, COUNT(*) AS n FROM @acc GROUP BY accion;
"""


def _merge_counts(conn: pyodbc.Connection, sql: str, params: tuple[Any, ...]) -> tuple[int, int]:
    cur = conn.cursor()
    try:
        cur.execute(sql, *params)
        inserted = updated = 0
        for action, count in cur.fetchall():
            if action == "INSERT":
                inserted = int(count)
            elif action == "UPDATE":
                updated = int(count)
        return inserted, updated
    finally:
        cur.close()


def build_ready(target: pyodbc.Connection) -> dict[str, int]:
    """Integra clean en ready (una fila por linea de factura)."""
    with audit.run("sales_ready", "clean.FacturaDetalle", "ready.Ventas") as (execution_id, counts):
        counts.read = int(db.fetch_scalar(target, "SELECT COUNT(*) FROM clean.FacturaDetalle") or 0)
        counts.inserted, counts.updated = _merge_counts(target, READY_MERGE_SQL, (execution_id, execution_id))
        target.commit()
    return {"read": counts.read, "inserted": counts.inserted, "updated": counts.updated}
