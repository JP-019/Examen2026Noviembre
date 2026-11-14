"""Carga del Data Warehouse: dimensiones (SCD Tipo 1) y hechos."""

from __future__ import annotations

from typing import Any

import pyodbc

from . import audit, db, staging

DIM_PRODUCTO_SQL = """
SET NOCOUNT ON;
DECLARE @acc TABLE (accion nvarchar(10));

MERGE dw.DimProducto AS t
USING
(
    SELECT
        p.IdProducto,
        p.NombreProducto,
        COALESCE(sf.NombreSubFamilia, 'Desconocido') AS SubFamilia,
        COALESCE(fa.NombreFamilia, 'Desconocido')    AS Familia,
        COALESCE(c.NombreCategoria, 'Desconocido')   AS Categoria,
        COALESCE(r.NombreRubro, 'Desconocido')       AS Rubro,
        COALESCE(s.NombreSeccion, 'Desconocido')     AS Seccion,
        COALESCE(s.NombreSeccion, 'Desconocido') + ' > ' +
        COALESCE(r.NombreRubro, 'Desconocido') + ' > ' +
        COALESCE(c.NombreCategoria, 'Desconocido') + ' > ' +
        COALESCE(fa.NombreFamilia, 'Desconocido') + ' > ' +
        COALESCE(sf.NombreSubFamilia, 'Desconocido') + ' > ' +
        p.NombreProducto AS JerarquiaCompleta
    FROM clean.Producto p
    LEFT JOIN clean.SubFamilia sf ON sf.IdSubFamilia = p.IdSubFamilia
    LEFT JOIN clean.Familia fa    ON fa.IdFamilia = sf.IdFamilia
    LEFT JOIN clean.Categoria c   ON c.IdCategoria = fa.IdCategoria
    LEFT JOIN clean.Rubro r       ON r.IdRubro = c.IdRubro
    LEFT JOIN clean.Seccion s     ON s.IdSeccion = r.IdSeccion
) AS src
ON t.ProductoNaturalKey = src.IdProducto
WHEN MATCHED THEN UPDATE SET
    NombreProducto = src.NombreProducto,
    SubFamilia = src.SubFamilia,
    Familia = src.Familia,
    Categoria = src.Categoria,
    Rubro = src.Rubro,
    Seccion = src.Seccion,
    JerarquiaCompleta = src.JerarquiaCompleta,
    EsVigente = 1,
    FilaHasta = NULL,
    EsDesconocido = 0
WHEN NOT MATCHED THEN INSERT
    (ProductoNaturalKey, NombreProducto, SubFamilia, Familia, Categoria,
     Rubro, Seccion, JerarquiaCompleta, EsVigente, FilaDesde, EsDesconocido)
VALUES
    (src.IdProducto, src.NombreProducto, src.SubFamilia, src.Familia, src.Categoria,
     src.Rubro, src.Seccion, src.JerarquiaCompleta, 1, SYSUTCDATETIME(), 0)
OUTPUT $action INTO @acc;

SELECT accion, COUNT(*) AS n FROM @acc GROUP BY accion;
"""

DIM_LOCAL_SQL = """
SET NOCOUNT ON;
DECLARE @acc TABLE (accion nvarchar(10));

MERGE dw.DimLocal AS t
USING (SELECT IdLocal, NombreLocal FROM clean.Local) AS src
ON t.LocalNaturalKey = src.IdLocal
WHEN MATCHED THEN UPDATE SET
    NombreLocal = src.NombreLocal,
    EsDesconocido = 0
WHEN NOT MATCHED THEN INSERT (LocalNaturalKey, NombreLocal, EsDesconocido)
VALUES (src.IdLocal, src.NombreLocal, 0)
OUTPUT $action INTO @acc;

SELECT accion, COUNT(*) AS n FROM @acc GROUP BY accion;
"""

DIM_VERSION_SQL = """
SET NOCOUNT ON;
DECLARE @acc TABLE (accion nvarchar(10));

MERGE dw.DimVersion AS t
USING (SELECT IdVersion, NombreVersion FROM clean.[Version]) AS src
ON t.VersionNaturalKey = src.IdVersion
WHEN MATCHED THEN UPDATE SET
    NombreVersion = src.NombreVersion,
    EsDesconocido = 0
WHEN NOT MATCHED THEN INSERT (VersionNaturalKey, NombreVersion, EsDesconocido)
VALUES (src.IdVersion, src.NombreVersion, 0)
OUTPUT $action INTO @acc;

SELECT accion, COUNT(*) AS n FROM @acc GROUP BY accion;
"""

FACT_SQL = """
SET NOCOUNT ON;
DECLARE @acc TABLE (accion nvarchar(10));

MERGE dw.FactVentas AS t
USING
(
    SELECT
        v.IdFacturaDetalle,
        COALESCE(tm.TiempoKey, 0)   AS TiempoKey,
        COALESCE(p.ProductoKey, 0)  AS ProductoKey,
        COALESCE(l.LocalKey, 0)     AS LocalKey,
        COALESCE(ve.VersionKey, 0)  AS VersionKey,
        v.NumeroFactura,
        v.Cantidad,
        v.PrecioUnitario,
        CAST(0.00 AS decimal(18,2)) AS Descuento,
        v.ImporteLinea
    FROM ready.Ventas v
    LEFT JOIN dw.DimTiempo   tm ON tm.Fecha = v.Fecha
    LEFT JOIN dw.DimProducto p  ON p.ProductoNaturalKey = v.IdProducto
    LEFT JOIN dw.DimLocal    l  ON l.LocalNaturalKey = v.IdLocal
    LEFT JOIN dw.DimVersion  ve ON ve.VersionNaturalKey = v.IdVersion
) AS src
ON t.IdFacturaDetalle = src.IdFacturaDetalle
WHEN MATCHED THEN UPDATE SET
    TiempoKey = src.TiempoKey,
    ProductoKey = src.ProductoKey,
    LocalKey = src.LocalKey,
    VersionKey = src.VersionKey,
    NumeroFactura = src.NumeroFactura,
    Cantidad = src.Cantidad,
    PrecioUnitario = src.PrecioUnitario,
    Descuento = src.Descuento,
    ImporteLinea = src.ImporteLinea,
    ExecutionId = ?
WHEN NOT MATCHED THEN INSERT
    (TiempoKey, ProductoKey, LocalKey, VersionKey, IdFacturaDetalle, NumeroFactura,
     Cantidad, PrecioUnitario, Descuento, ImporteLinea, ExecutionId)
VALUES
    (src.TiempoKey, src.ProductoKey, src.LocalKey, src.VersionKey, src.IdFacturaDetalle, src.NumeroFactura,
     src.Cantidad, src.PrecioUnitario, src.Descuento, src.ImporteLinea, ?)
OUTPUT $action INTO @acc;

SELECT accion, COUNT(*) AS n FROM @acc GROUP BY accion;
"""


def load(conn: pyodbc.Connection) -> dict[str, dict[str, int]]:
    """Carga dimensiones y hechos. Idempotente por clave natural."""
    summary: dict[str, dict[str, int]] = {}

    for name, table, sql in (
        ("DimProducto", "clean.Producto", DIM_PRODUCTO_SQL),
        ("DimLocal", "clean.Local", DIM_LOCAL_SQL),
        ("DimVersion", "clean.[Version]", DIM_VERSION_SQL),
    ):
        with audit.run("sales_dw_dim", table, f"dw.{name}") as (execution_id, counts):
            counts.read = int(db.fetch_scalar(conn, f"SELECT COUNT(*) FROM {table}") or 0)
            counts.inserted, counts.updated = staging._merge_counts(conn, sql, ())
            conn.commit()
        summary[name] = {"inserted": counts.inserted, "updated": counts.updated}

    with audit.run("sales_dw_fact", "ready.Ventas", "dw.FactVentas") as (execution_id, counts):
        counts.read = int(db.fetch_scalar(conn, "SELECT COUNT(*) FROM ready.Ventas") or 0)
        counts.inserted, counts.updated = staging._merge_counts(conn, FACT_SQL, (execution_id, execution_id))
        conn.commit()
    summary["FactVentas"] = {"inserted": counts.inserted, "updated": counts.updated}

    return summary


def orphan_facts(conn: pyodbc.Connection) -> int:
    return int(
        db.fetch_scalar(
            conn,
            """
            SELECT COUNT(*)
            FROM dw.FactVentas f
            LEFT JOIN dw.DimTiempo   t ON t.TiempoKey   = f.TiempoKey
            LEFT JOIN dw.DimProducto p ON p.ProductoKey = f.ProductoKey
            LEFT JOIN dw.DimLocal    l ON l.LocalKey    = f.LocalKey
            LEFT JOIN dw.DimVersion  v ON v.VersionKey  = f.VersionKey
            WHERE t.TiempoKey IS NULL OR p.ProductoKey IS NULL
               OR l.LocalKey IS NULL OR v.VersionKey IS NULL
            """,
        )
        or 0
    )
