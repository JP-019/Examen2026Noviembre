"""Contratos de respuesta de la API.

Se declaran explicitamente para que Swagger documente que devuelve cada endpoint
y para que el dashboard y GenAI tengan un contrato estable.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class Health(BaseModel):
    status: str
    service: str
    database: str
    data_updated_at: datetime | None
    last_etl_status: str | None
    fact_rows: int


class Periodo(BaseModel):
    desde: date | None = None
    hasta: date | None = None


class KpiValor(BaseModel):
    code: str
    label: str
    value: float
    unit: str
    format: str = "number"


class KpisResponse(BaseModel):
    periodo: Periodo
    filtros: dict[str, str | None] = Field(default_factory=dict)
    data_updated_at: datetime | None
    kpis: list[KpiValor]


class PuntoSerie(BaseModel):
    periodo: str
    ventas: float
    lineas: int


class Comparacion(BaseModel):
    actual: float
    anterior: float
    variacion_pct: float | None


class TendenciasResponse(BaseModel):
    granularidad: str
    periodo: Periodo
    filtros: dict[str, str | None] = Field(default_factory=dict)
    data_updated_at: datetime | None
    serie: list[PuntoSerie]
    comparacion: Comparacion


class LineaDetalle(BaseModel):
    id_factura_detalle: int
    numero_factura: int
    fecha: date
    producto: str
    local: str
    version: str
    cantidad: int
    precio_unitario: float
    importe_linea: float


class DetalleResponse(BaseModel):
    periodo: Periodo
    filtros: dict[str, str | None] = Field(default_factory=dict)
    data_updated_at: datetime | None
    page: int
    page_size: int
    total: int
    total_pages: int
    rows: list[LineaDetalle]


class FiltrosResponse(BaseModel):
    desde: date | None
    hasta: date | None
    locales: list[str]
    secciones: list[str]
    productos: list[str]
    data_updated_at: datetime | None


class Grupo(BaseModel):
    valor: str
    ventas: float
    lineas: int
    facturas: int
    unidades: int


class AgrupadoResponse(BaseModel):
    dimension: str
    periodo: Periodo
    filtros: dict[str, str | None] = Field(default_factory=dict)
    data_updated_at: datetime | None
    total_grupos: int
    grupos: list[Grupo]


class EtlRun(BaseModel):
    execution_id: int
    pipeline_name: str
    status: str
    end_time: datetime | None
    rows_read: int
    rows_rejected: int
    error_detail: str | None = None


class ContadorRegla(BaseModel):
    rule_code: str
    total: int


class MonitorResponse(BaseModel):
    data_updated_at: datetime | None
    fact_rows: int
    last_etl: EtlRun | None
    etl_runs_24h: int
    etl_failures_24h: int
    rejected_total: int
    rejected_open: int
    rejected_by_rule: list[ContadorRegla]
    recent_failures: list[EtlRun]


def to_float(value: Decimal | float | int | None) -> float:
    if value is None:
        return 0.0
    return float(value)
