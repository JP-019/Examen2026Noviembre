"""Calculo de KPIs, tendencias, detalle y filtros sobre `dw.vw_Ventas`.

Toda la logica de negocio vive aca; `main.py` solo valida parametros HTTP.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from . import database
from .config import settings
from .filters import Filter
from .schemas import (
    AgrupadoResponse,
    Comparacion,
    ContadorRegla,
    DetalleResponse,
    EtlRun,
    FiltrosResponse,
    Grupo,
    KpiValor,
    KpisResponse,
    LineaDetalle,
    MonitorResponse,
    Periodo,
    PuntoSerie,
    TendenciasResponse,
    to_float,
)

VIEW = "dw.vw_Ventas"
FACT = "dw.FactVentas"


def data_updated_at() -> datetime | None:
    return database.scalar(
        """
        SELECT MAX(end_time)
        FROM audit.etl_execution
        WHERE status = 'SUCCESS' AND target_object LIKE 'dw.%'
        """
    )


def last_etl_status() -> str | None:
    return database.scalar("SELECT TOP 1 status FROM audit.etl_execution ORDER BY execution_id DESC")


def fact_rows() -> int:
    return int(database.scalar(f"SELECT COUNT(*) FROM {FACT}") or 0)


def _periodo(filtro: Filter) -> Periodo:
    return Periodo(desde=filtro.desde, hasta=filtro.hasta)


def kpis(filtro: Filter) -> KpisResponse:
    where, params = filtro.build()
    row = database.query(
        f"""
        SELECT
            COUNT(*)                       AS lineas,
            COUNT(DISTINCT NumeroFactura)  AS facturas,
            COALESCE(SUM(ImporteLinea), 0) AS ventas,
            COALESCE(SUM(Cantidad), 0)     AS unidades,
            COUNT(DISTINCT ProductoKey)    AS productos,
            COUNT(DISTINCT LocalKey)       AS locales
        FROM {VIEW}
        {where}
        """,
        params,
    )[0]

    ventas = to_float(row["ventas"])
    lineas = int(row["lineas"])
    facturas = int(row["facturas"])
    ticket = ventas / facturas if facturas else 0.0

    valores = [
        KpiValor(code="ventas", label="Ventas totales", value=round(ventas, 2), unit="ARS", format="currency"),
        KpiValor(code="lineas", label="Lineas de venta", value=lineas, unit="lineas", format="integer"),
        KpiValor(code="facturas", label="Facturas", value=facturas, unit="facturas", format="integer"),
        KpiValor(code="ticket_promedio", label="Ticket promedio", value=round(ticket, 2), unit="ARS", format="currency"),
        KpiValor(code="unidades", label="Unidades vendidas", value=int(row["unidades"]), unit="unidades", format="integer"),
        KpiValor(code="productos", label="Productos distintos", value=int(row["productos"]), unit="productos", format="integer"),
    ]

    return KpisResponse(
        periodo=_periodo(filtro),
        filtros=filtro.as_dict(),
        data_updated_at=data_updated_at(),
        kpis=valores,
    )


def _ventas(filtro: Filter) -> float:
    where, params = filtro.build()
    return to_float(
        database.scalar(f"SELECT COALESCE(SUM(ImporteLinea), 0) FROM {VIEW} {where}", params)
    )


def tendencias(filtro: Filter, granularidad: str = "dia") -> TendenciasResponse:
    trunc = "CONVERT(date, Fecha)" if granularidad == "dia" else "DATEFROMPARTS(YEAR(Fecha), MONTH(Fecha), 1)"
    fmt = "CONVERT(varchar(10), {0}, 23)" if granularidad == "dia" else "CONVERT(varchar(7), {0}, 23)"
    where, params = filtro.build()

    rows = database.query(
        f"""
        SELECT
            {fmt.format(trunc)} AS periodo,
            COALESCE(SUM(ImporteLinea), 0) AS ventas,
            COUNT(*) AS lineas
        FROM {VIEW}
        {where}
        GROUP BY {trunc}
        ORDER BY {trunc}
        """,
        params,
    )

    serie = [
        PuntoSerie(periodo=r["periodo"], ventas=round(to_float(r["ventas"]), 2), lineas=int(r["lineas"]))
        for r in rows
    ]

    actual_total = round(sum(p.ventas for p in serie), 2)
    anterior_total = 0.0
    variacion = None
    # La comparacion solo tiene sentido con un rango explicito de fechas.
    if filtro.desde and filtro.hasta:
        anterior_total = round(_ventas(filtro.previous_period()), 2)
        if anterior_total:
            variacion = round((actual_total - anterior_total) / anterior_total * 100, 2)

    return TendenciasResponse(
        granularidad=granularidad,
        periodo=_periodo(filtro),
        filtros=filtro.as_dict(),
        data_updated_at=data_updated_at(),
        serie=serie,
        comparacion=Comparacion(actual=actual_total, anterior=anterior_total, variacion_pct=variacion),
    )


def detalle(filtro: Filter, page: int = 1, page_size: int = 25) -> DetalleResponse:
    page = max(1, page)
    page_size = max(1, min(page_size, settings.max_page_size))
    where, params = filtro.build()

    total = int(database.scalar(f"SELECT COUNT(*) FROM {VIEW} {where}", params) or 0)
    rows = database.query(
        f"""
        SELECT VentaKey, NumeroFactura, Fecha, NombreProducto, NombreLocal,
               NombreVersion, Cantidad, PrecioUnitario, ImporteLinea
        FROM {VIEW}
        {where}
        ORDER BY Fecha DESC, NumeroFactura DESC, VentaKey DESC
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """,
        [*params, (page - 1) * page_size, page_size],
    )

    total_pages = (total + page_size - 1) // page_size
    return DetalleResponse(
        periodo=_periodo(filtro),
        filtros=filtro.as_dict(),
        data_updated_at=data_updated_at(),
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        rows=[
            LineaDetalle(
                id_factura_detalle=int(r["VentaKey"]),
                numero_factura=int(r["NumeroFactura"]),
                fecha=r["Fecha"],
                producto=r["NombreProducto"],
                local=r["NombreLocal"],
                version=r["NombreVersion"],
                cantidad=int(r["Cantidad"]),
                precio_unitario=to_float(r["PrecioUnitario"]),
                importe_linea=to_float(r["ImporteLinea"]),
            )
            for r in rows
        ],
    )


def _distinct(column: str) -> list[str]:
    rows = database.query(
        f"SELECT DISTINCT [{column}] AS valor FROM {VIEW} WHERE [{column}] IS NOT NULL ORDER BY [{column}]"
    )
    return [str(r["valor"]) for r in rows]


def filtros() -> FiltrosResponse:
    rango: dict[str, Any] = database.query(
        f"SELECT MIN(Fecha) AS desde, MAX(Fecha) AS hasta FROM {VIEW}"
    )[0]
    return FiltrosResponse(
        desde=rango["desde"],
        hasta=rango["hasta"],
        locales=_distinct("NombreLocal"),
        secciones=_distinct("Seccion"),
        productos=_distinct("NombreProducto"),
        data_updated_at=data_updated_at(),
    )


# Dimensiones permitidas para agrupar. La columna nunca viene del usuario.
GROUP_COLUMNS = {
    "local": "NombreLocal",
    "seccion": "Seccion",
    "producto": "NombreProducto",
}


def agrupado(filtro: Filter, dimension: str, limit: int = 10) -> AgrupadoResponse:
    column = GROUP_COLUMNS[dimension]
    where, params = filtro.build()
    limit = max(1, min(limit, 50))

    rows = database.query(
        f"""
        SELECT [{column}] AS valor,
               COALESCE(SUM(ImporteLinea), 0) AS ventas,
               COUNT(*) AS lineas,
               COUNT(DISTINCT NumeroFactura) AS facturas,
               COALESCE(SUM(Cantidad), 0) AS unidades
        FROM {VIEW}
        {where}
        GROUP BY [{column}]
        ORDER BY ventas DESC
        OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY
        """,
        [*params, limit],
    )
    total = int(
        database.scalar(
            f"SELECT COUNT(DISTINCT [{column}]) FROM {VIEW} {where}", params
        )
        or 0
    )

    return AgrupadoResponse(
        dimension=dimension,
        periodo=_periodo(filtro),
        filtros=filtro.as_dict(),
        data_updated_at=data_updated_at(),
        total_grupos=total,
        grupos=[
            Grupo(
                valor=str(r["valor"]),
                ventas=round(to_float(r["ventas"]), 2),
                lineas=int(r["lineas"]),
                facturas=int(r["facturas"]),
                unidades=int(r["unidades"]),
            )
            for r in rows
        ],
    )


def _etl_run(row: dict[str, Any]) -> EtlRun:
    return EtlRun(
        execution_id=int(row["execution_id"]),
        pipeline_name=str(row["pipeline_name"]),
        status=str(row["status"]),
        end_time=row["end_time"],
        rows_read=int(row["rows_read"] or 0),
        rows_rejected=int(row["rows_rejected"] or 0),
        error_detail=row["error_detail"],
    )


def monitor() -> MonitorResponse:
    """Estado operativo del pipeline, la calidad y el hecho, para alertas."""
    last_rows = database.query(
        """
        SELECT TOP 1 execution_id, pipeline_name, status, end_time,
                     rows_read, rows_rejected, error_detail
        FROM audit.etl_execution
        ORDER BY execution_id DESC
        """
    )
    run_24h = database.query(
        """
        SELECT COUNT(*) AS total,
               COALESCE(SUM(CASE WHEN status <> 'SUCCESS' THEN 1 ELSE 0 END), 0) AS fallas
        FROM audit.etl_execution
        WHERE start_time >= DATEADD(hour, -24, SYSDATETIME())
        """
    )[0]
    rechazos = database.query(
        """
        SELECT COUNT(*) AS total,
               COALESCE(SUM(CASE WHEN status = 'OPEN' THEN 1 ELSE 0 END), 0) AS abiertos
        FROM quarantine.rejected_row
        """
    )[0]
    por_regla = database.query(
        """
        SELECT rule_code, COUNT(*) AS total
        FROM quarantine.rejected_row
        GROUP BY rule_code
        ORDER BY total DESC
        """
    )
    fallas = database.query(
        """
        SELECT TOP 5 execution_id, pipeline_name, status, end_time,
                     rows_read, rows_rejected, error_detail
        FROM audit.etl_execution
        WHERE status <> 'SUCCESS'
        ORDER BY execution_id DESC
        """
    )

    return MonitorResponse(
        data_updated_at=data_updated_at(),
        fact_rows=fact_rows(),
        last_etl=_etl_run(last_rows[0]) if last_rows else None,
        etl_runs_24h=int(run_24h["total"] or 0),
        etl_failures_24h=int(run_24h["fallas"] or 0),
        rejected_total=int(rechazos["total"] or 0),
        rejected_open=int(rechazos["abiertos"] or 0),
        rejected_by_rule=[
            ContadorRegla(rule_code=str(r["rule_code"]), total=int(r["total"])) for r in por_regla
        ],
        recent_failures=[_etl_run(r) for r in fallas],
    )
