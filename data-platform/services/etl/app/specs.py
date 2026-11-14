"""Especificaciones de extraccion y mapeo fuente -> raw -> clean.

Una unica definicion declarativa por tabla evita duplicar SQL y mantiene
el linaje explicito. El orden de EXTRACT_SPECS respeta dependencias.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TableSpec:
    name: str
    source_object: str
    raw_table: str
    clean_table: str
    raw_columns: tuple[str, ...]
    clean_map: tuple[tuple[str, str], ...]
    key_column: str
    kind: str  # 'dimension' | 'factura' | 'detalle'
    select_full: str
    select_incremental: str | None = None
    watermark_column: str | None = None

    @property
    def raw_insert_sql(self) -> str:
        cols = ", ".join(f"[{c}]" for c in self.raw_columns)
        marks = ", ".join("?" for _ in self.raw_columns)
        return f"INSERT INTO {self.raw_table} ({cols}, _execution_id) VALUES ({marks}, ?)"


EXTRACT_SPECS: tuple[TableSpec, ...] = (
    TableSpec(
        name="Seccion",
        source_object="Venta.dbo.Seccion",
        raw_table="raw.Seccion",
        clean_table="clean.Seccion",
        raw_columns=("IdSeccion", "NombreSeccion"),
        clean_map=(("IdSeccion", "IdSeccion"), ("NombreSeccion", "NombreSeccion")),
        key_column="IdSeccion",
        kind="dimension",
        select_full="SELECT IdSeccion, NombreSeccion FROM dbo.Seccion",
    ),
    TableSpec(
        name="Rubro",
        source_object="Venta.dbo.Rubro",
        raw_table="raw.Rubro",
        clean_table="clean.Rubro",
        raw_columns=("IdRubro", "NombreRubro", "IdSeccion"),
        clean_map=(("IdRubro", "IdRubro"), ("NombreRubro", "NombreRubro"), ("IdSeccion", "IdSeccion")),
        key_column="IdRubro",
        kind="dimension",
        select_full="SELECT IdRubro, NombreRubro, IdSeccion FROM dbo.Rubro",
    ),
    TableSpec(
        name="Categoria",
        source_object="Venta.dbo.Categoria",
        raw_table="raw.Categoria",
        clean_table="clean.Categoria",
        raw_columns=("IdCategoria", "NombreCategoria", "IdRubro"),
        clean_map=(
            ("IdCategoria", "IdCategoria"),
            ("NombreCategoria", "NombreCategoria"),
            ("IdRubro", "IdRubro"),
        ),
        key_column="IdCategoria",
        kind="dimension",
        select_full="SELECT IdCategoria, NombreCategoria, IdRubro FROM dbo.Categoria",
    ),
    TableSpec(
        name="Familia",
        source_object="Venta.dbo.Familia",
        raw_table="raw.Familia",
        clean_table="clean.Familia",
        raw_columns=("IdFamilia", "NombreFamilia", "IdCategoria"),
        clean_map=(
            ("IdFamilia", "IdFamilia"),
            ("NombreFamilia", "NombreFamilia"),
            ("IdCategoria", "IdCategoria"),
        ),
        key_column="IdFamilia",
        kind="dimension",
        select_full="SELECT IdFamilia, NombreFamilia, IdCategoria FROM dbo.Familia",
    ),
    TableSpec(
        name="SubFamilia",
        source_object="Venta.dbo.SubFamilia",
        raw_table="raw.SubFamilia",
        clean_table="clean.SubFamilia",
        raw_columns=("IdSubFamilia", "NombreSubFamilia", "IdFamilia"),
        clean_map=(
            ("IdSubFamilia", "IdSubFamilia"),
            ("NombreSubFamilia", "NombreSubFamilia"),
            ("IdFamilia", "IdFamilia"),
        ),
        key_column="IdSubFamilia",
        kind="dimension",
        select_full="SELECT IdSubFamilia, NombreSubFamilia, IdFamilia FROM dbo.SubFamilia",
    ),
    TableSpec(
        name="Producto",
        source_object="Venta.dbo.Producto",
        raw_table="raw.Producto",
        clean_table="clean.Producto",
        raw_columns=("IdProducto", "NombreProducto", "IdSubFamilia"),
        clean_map=(
            ("IdProducto", "IdProducto"),
            ("NombreProducto", "NombreProducto"),
            ("IdSubFamilia", "IdSubFamilia"),
        ),
        key_column="IdProducto",
        kind="dimension",
        select_full="SELECT IdProducto, NombreProducto, IdSubFamilia FROM dbo.Producto",
    ),
    TableSpec(
        name="Local",
        source_object="Venta.dbo.Local",
        raw_table="raw.Local",
        clean_table="clean.Local",
        raw_columns=("IdLocal", "Nombre"),
        clean_map=(("IdLocal", "IdLocal"), ("NombreLocal", "Nombre")),
        key_column="IdLocal",
        kind="dimension",
        select_full="SELECT IdLocal, Nombre FROM dbo.Local",
    ),
    TableSpec(
        name="Version",
        source_object="Venta.dbo.Version",
        raw_table="raw.[Version]",
        clean_table="clean.[Version]",
        raw_columns=("IdVersion", "Nombre"),
        clean_map=(("IdVersion", "IdVersion"), ("NombreVersion", "Nombre")),
        key_column="IdVersion",
        kind="dimension",
        select_full="SELECT IdVersion, Nombre FROM dbo.[Version]",
    ),
    TableSpec(
        name="Factura",
        source_object="Venta.dbo.Factura",
        raw_table="raw.Factura",
        clean_table="clean.Factura",
        raw_columns=("IdFactura", "VentaAsociada", "Fecha", "NumeroFactura", "IdLocal", "IdVersion"),
        clean_map=(
            ("IdFactura", "IdFactura"),
            ("VentaAsociada", "VentaAsociada"),
            ("Fecha", "Fecha"),
            ("NumeroFactura", "NumeroFactura"),
            ("IdLocal", "IdLocal"),
            ("IdVersion", "IdVersion"),
        ),
        key_column="IdFactura",
        kind="factura",
        select_full=(
            "SELECT IdFactura, VentaAsociada, Fecha, [nºFactura] AS NumeroFactura, IdLocal, IdVersion "
            "FROM dbo.Factura"
        ),
        select_incremental=(
            "SELECT IdFactura, VentaAsociada, Fecha, [nºFactura] AS NumeroFactura, IdLocal, IdVersion "
            "FROM dbo.Factura WHERE Fecha >= ?"
        ),
        watermark_column="Fecha",
    ),
    TableSpec(
        name="FacturaDetalle",
        source_object="Venta.dbo.Factura_Detalle",
        raw_table="raw.FacturaDetalle",
        clean_table="clean.FacturaDetalle",
        raw_columns=("IdFacturaDetalle", "IdProducto", "IdFactura", "PrecioSinImporte", "Cantidad"),
        clean_map=(
            ("IdFacturaDetalle", "IdFacturaDetalle"),
            ("IdProducto", "IdProducto"),
            ("IdFactura", "IdFactura"),
            ("PrecioUnitario", "PrecioSinImporte"),
            ("Cantidad", "Cantidad"),
        ),
        key_column="IdFacturaDetalle",
        kind="detalle",
        select_full=(
            "SELECT d.Id_Factura_Detalle AS IdFacturaDetalle, d.IdProducto, d.IdFactura, "
            "d.PrecioSinImporte, d.Cantidad, f.Fecha "
            "FROM dbo.Factura_Detalle d "
            "JOIN dbo.Factura f ON f.IdFactura = d.IdFactura"
        ),
        select_incremental=(
            "SELECT d.Id_Factura_Detalle AS IdFacturaDetalle, d.IdProducto, d.IdFactura, "
            "d.PrecioSinImporte, d.Cantidad, f.Fecha "
            "FROM dbo.Factura_Detalle d "
            "JOIN dbo.Factura f ON f.IdFactura = d.IdFactura "
            "WHERE f.Fecha >= ?"
        ),
        watermark_column="Fecha",
    ),
)

DIMENSION_SPECS = tuple(s for s in EXTRACT_SPECS if s.kind == "dimension")
FACT_SPECS = tuple(s for s in EXTRACT_SPECS if s.kind in {"factura", "detalle"})
