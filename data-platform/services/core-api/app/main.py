"""API de KPIs (T09).

Unica puerta de lectura al Data Warehouse. Ningun frontend, asistente o alerta
se conecta directo a SQL Server.

Ejecucion (desde services/core-api):
    uvicorn app.main:app --port 8000 --reload
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from datetime import date
from ipaddress import ip_address
from typing import Annotated, Literal

import pyodbc
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse, Response

from . import services
from .config import settings
from .filters import Filter
from .schemas import (
    AgrupadoResponse,
    DetalleResponse,
    FiltrosResponse,
    Health,
    KpisResponse,
    MonitorResponse,
    TendenciasResponse,
)

logger = logging.getLogger("core_api")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="API de KPIs - Plataforma de ventas",
    version="1.0.0",
    description=(
        "KPIs, tendencias y detalle sobre el Data Warehouse. "
        "Todas las consultas son parametrizadas y de solo lectura."
    ),
)


@app.middleware("http")
async def local_access_only(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    client = request.client
    try:
        is_local = client is not None and ip_address(client.host).is_loopback
    except ValueError:
        is_local = False
    if not is_local:
        return JSONResponse(
            status_code=403,
            content={"detail": "Acceso permitido solo desde localhost."},
        )
    return await call_next(request)


def _filter(
    desde: Annotated[date | None, Query(description="Fecha inicial (YYYY-MM-DD)")] = None,
    hasta: Annotated[date | None, Query(description="Fecha final (YYYY-MM-DD)")] = None,
    local: Annotated[str | None, Query(description="Nombre exacto del local")] = None,
    seccion: Annotated[str | None, Query(description="Seccion comercial")] = None,
    producto: Annotated[str | None, Query(description="Nombre exacto del producto")] = None,
) -> Filter:
    if desde and hasta and desde > hasta:
        raise HTTPException(status_code=422, detail="`desde` no puede ser posterior a `hasta`")
    return Filter(desde=desde, hasta=hasta, local=local, seccion=seccion, producto=producto)


def _db_guard(exc: Exception) -> HTTPException:
    logger.exception("Error de base de datos")
    return HTTPException(
        status_code=503,
        detail=(
            "No se pudo consultar el Data Warehouse. "
            "Verificar que la base DataPlatform exista y que el ETL haya corrido."
        ),
    )


@app.get("/", include_in_schema=False)
def root() -> dict[str, object]:
    return {
        "service": settings.service_name,
        "docs": "/docs",
        "health": "/api/v1/health",
        "endpoints": [
            "/api/v1/kpis",
            "/api/v1/tendencias",
            "/api/v1/detalle",
            "/api/v1/filtros",
            "/api/v1/agrupado",
            "/api/v1/monitor",
        ],
    }


@app.get("/api/v1/health", response_model=Health, summary="Estado del servicio y de los datos")
def health() -> Health:
    try:
        return Health(
            status="ok",
            service=settings.service_name,
            database=settings.database,
            data_updated_at=services.data_updated_at(),
            last_etl_status=services.last_etl_status(),
            fact_rows=services.fact_rows(),
        )
    except pyodbc.Error as exc:
        raise _db_guard(exc) from exc


@app.get("/api/v1/kpis", response_model=KpisResponse, summary="4 a 6 KPIs del periodo")
def kpis(
    desde: Annotated[date | None, Query(description="Fecha inicial (YYYY-MM-DD)")] = None,
    hasta: Annotated[date | None, Query(description="Fecha final (YYYY-MM-DD)")] = None,
    local: Annotated[str | None, Query(description="Nombre exacto del local")] = None,
    seccion: Annotated[str | None, Query(description="Seccion comercial")] = None,
    producto: Annotated[str | None, Query(description="Nombre exacto del producto")] = None,
) -> KpisResponse:
    filtro = _filter(desde, hasta, local, seccion, producto)
    try:
        return services.kpis(filtro)
    except pyodbc.Error as exc:
        raise _db_guard(exc) from exc


@app.get("/api/v1/tendencias", response_model=TendenciasResponse, summary="Serie temporal y comparacion")
def tendencias(
    desde: Annotated[date | None, Query(description="Fecha inicial (YYYY-MM-DD)")] = None,
    hasta: Annotated[date | None, Query(description="Fecha final (YYYY-MM-DD)")] = None,
    local: Annotated[str | None, Query()] = None,
    seccion: Annotated[str | None, Query()] = None,
    producto: Annotated[str | None, Query()] = None,
    granularidad: Annotated[Literal["dia", "mes"], Query()] = "dia",
) -> TendenciasResponse:
    filtro = _filter(desde, hasta, local, seccion, producto)
    try:
        return services.tendencias(filtro, granularidad)
    except pyodbc.Error as exc:
        raise _db_guard(exc) from exc


@app.get("/api/v1/detalle", response_model=DetalleResponse, summary="Detalle paginado de lineas")
def detalle(
    desde: Annotated[date | None, Query(description="Fecha inicial (YYYY-MM-DD)")] = None,
    hasta: Annotated[date | None, Query(description="Fecha final (YYYY-MM-DD)")] = None,
    local: Annotated[str | None, Query()] = None,
    seccion: Annotated[str | None, Query()] = None,
    producto: Annotated[str | None, Query()] = None,
    page: Annotated[int, Query(ge=1, description="Pagina (1-based)")] = 1,
    page_size: Annotated[int, Query(ge=1, description="Filas por pagina")] = 25,
) -> DetalleResponse:
    filtro = _filter(desde, hasta, local, seccion, producto)
    try:
        return services.detalle(filtro, page, page_size)
    except pyodbc.Error as exc:
        raise _db_guard(exc) from exc


@app.get("/api/v1/filtros", response_model=FiltrosResponse, summary="Valores disponibles para filtrar")
def filtros() -> FiltrosResponse:
    try:
        return services.filtros()
    except pyodbc.Error as exc:
        raise _db_guard(exc) from exc


@app.get("/api/v1/agrupado", response_model=AgrupadoResponse, summary="Totales por dimension")
def agrupado(
    desde: Annotated[date | None, Query(description="Fecha inicial (YYYY-MM-DD)")] = None,
    hasta: Annotated[date | None, Query(description="Fecha final (YYYY-MM-DD)")] = None,
    local: Annotated[str | None, Query()] = None,
    seccion: Annotated[str | None, Query()] = None,
    producto: Annotated[str | None, Query()] = None,
    dimension: Annotated[
        Literal["local", "seccion", "producto"],
        Query(description="Dimension por la que agrupar"),
    ] = "local",
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> AgrupadoResponse:
    filtro = _filter(desde, hasta, local, seccion, producto)
    try:
        return services.agrupado(filtro, dimension, limit)
    except pyodbc.Error as exc:
        raise _db_guard(exc) from exc


@app.get("/api/v1/monitor", response_model=MonitorResponse, summary="Estado operativo del pipeline")
def monitor() -> MonitorResponse:
    try:
        return services.monitor()
    except pyodbc.Error as exc:
        raise _db_guard(exc) from exc
