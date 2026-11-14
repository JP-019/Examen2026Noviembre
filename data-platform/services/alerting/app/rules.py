"""Reglas de alerta y construccion del contexto.

Cada regla es una funcion pura sobre un `Contexto` medido por los servicios.
La clave `event_key` hace que el mismo evento no genere mas de una alerta.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .clients import CoreApi, MlApi, ServiceError
from .config import CAIDA_PCT, MAE_MAX, ML_PERIODOS_MIN, RECHAZOS_MAX, TICKET_MIN, VENTAS_MIN


@dataclass(frozen=True)
class Umbrales:
    ventas_min: float = VENTAS_MIN
    ticket_min: float = TICKET_MIN
    caida_pct: float = CAIDA_PCT
    mae_max: float = MAE_MAX
    rechazos_max: int = RECHAZOS_MAX
    ml_periodos_min: int = ML_PERIODOS_MIN


@dataclass
class Contexto:
    ventas: float = 0.0
    facturas: int = 0
    ticket: float = 0.0
    variacion_pct: float | None = None
    periodo: str = "sin-periodo"
    data_updated_at: str | None = None
    ml_status: str = "unknown"
    ml_version: str | None = None
    ml_mae: float | None = None
    ml_periodos: int = 0
    ml_message: str = ""
    rechazos_abiertos: int = 0
    ultimo_etl_status: str | None = None


@dataclass
class Alerta:
    rule_code: str
    alert_type: str
    severity: str
    entity: str | None
    indicator: str
    observed_value: float | None
    threshold: float | None
    period: str | None
    source: str
    explanation: str
    action: str
    event_key: str
    simulated: bool = False


@dataclass(frozen=True)
class Regla:
    code: str
    alert_type: str
    severity: str
    indicator: str
    descripcion: str
    evaluar: Callable[[Contexto, Umbrales], Alerta | None]


def _clave(code: str, ctx: Contexto, entity: str) -> str:
    return f"{code}|{entity}|{ctx.periodo}|{ctx.data_updated_at or 'sin-fecha'}"


def _ventas_bajas(ctx: Contexto, u: Umbrales) -> Alerta | None:
    if ctx.facturas == 0 or ctx.ventas >= u.ventas_min:
        return None
    return Alerta(
        rule_code="VENTAS_BAJAS",
        alert_type="regla_negocio",
        severity="warning",
        entity="ventas",
        indicator="ventas_totales",
        observed_value=round(ctx.ventas, 2),
        threshold=u.ventas_min,
        period=ctx.periodo,
        source="core-api /api/v1/kpis",
        explanation=(
            f"Las ventas del periodo ({ctx.ventas:,.2f}) estan por debajo del umbral "
            f"configurado ({u.ventas_min:,.2f})."
        ),
        action="Revisar surtido y campanas del periodo; confirmar que el ETL cargo todas las ventas.",
        event_key=_clave("VENTAS_BAJAS", ctx, "ventas"),
    )


def _ticket_bajo(ctx: Contexto, u: Umbrales) -> Alerta | None:
    if ctx.facturas == 0 or ctx.ticket >= u.ticket_min:
        return None
    return Alerta(
        rule_code="TICKET_BAJO",
        alert_type="regla_negocio",
        severity="warning",
        entity="facturas",
        indicator="ticket_promedio",
        observed_value=round(ctx.ticket, 2),
        threshold=u.ticket_min,
        period=ctx.periodo,
        source="core-api /api/v1/kpis",
        explanation=(
            f"El ticket promedio ({ctx.ticket:,.2f}) esta por debajo del umbral "
            f"({u.ticket_min:,.2f}) sobre {ctx.facturas} facturas."
        ),
        action="Revisar mezcla de productos y promociones; validar el registro de precios.",
        event_key=_clave("TICKET_BAJO", ctx, "facturas"),
    )


def _caida_ventas(ctx: Contexto, u: Umbrales) -> Alerta | None:
    if ctx.variacion_pct is None or ctx.variacion_pct > -u.caida_pct:
        return None
    return Alerta(
        rule_code="CAIDA_VENTAS",
        alert_type="regla_negocio",
        severity="critical",
        entity="ventas",
        indicator="variacion_ventas_pct",
        observed_value=round(ctx.variacion_pct, 2),
        threshold=-u.caida_pct,
        period=ctx.periodo,
        source="core-api /api/v1/tendencias",
        explanation=(
            f"Las ventas cayeron {abs(ctx.variacion_pct):.2f}% respecto del periodo anterior "
            f"(umbral de caida: {u.caida_pct:.2f}%)."
        ),
        action="Revisar locales y productos con mayor caida; verificar si hubo faltantes o cambios de precio.",
        event_key=_clave("CAIDA_VENTAS", ctx, "ventas"),
    )


def _modelo_sin_entrenar(ctx: Contexto, u: Umbrales) -> Alerta | None:
    if ctx.ml_status == "trained":
        return None
    return Alerta(
        rule_code="MODELO_SIN_ENTRENAR",
        alert_type="umbral_ml",
        severity="info",
        entity="modelo_ml",
        indicator="periodos_disponibles",
        observed_value=float(ctx.ml_periodos),
        threshold=float(u.ml_periodos_min),
        period=ctx.periodo,
        source="ml /model",
        explanation=(
            f"El modelo no esta entrenado ({ctx.ml_status}): hay {ctx.ml_periodos} periodos "
            f"y se requieren {u.ml_periodos_min}. {ctx.ml_message}".strip()
        ),
        action="Acumular mas meses de ventas y ejecutar POST /train; no usar predicciones mientras tanto.",
        event_key=_clave("MODELO_SIN_ENTRENAR", ctx, "modelo_ml"),
    )


def _mae_alto(ctx: Contexto, u: Umbrales) -> Alerta | None:
    if ctx.ml_status != "trained" or ctx.ml_mae is None or ctx.ml_mae <= u.mae_max:
        return None
    return Alerta(
        rule_code="MAE_ALTO",
        alert_type="umbral_ml",
        severity="warning",
        entity="modelo_ml",
        indicator="mae_modelo",
        observed_value=round(ctx.ml_mae, 2),
        threshold=u.mae_max,
        period=ctx.periodo,
        source="ml /model",
        explanation=(
            f"El MAE del modelo ({ctx.ml_mae:,.2f}) supera el umbral ({u.mae_max:,.2f}); "
            f"la prediccion no es confiable."
        ),
        action="Reentrenar, revisar el baseline y no publicar predicciones hasta mejorar el error.",
        event_key=_clave("MAE_ALTO", ctx, "modelo_ml"),
    )


def _rechazos_altos(ctx: Contexto, u: Umbrales) -> Alerta | None:
    if ctx.rechazos_abiertos <= u.rechazos_max:
        return None
    return Alerta(
        rule_code="RECHAZOS_ALTOS",
        alert_type="calidad_datos",
        severity="critical",
        entity="quarantine.rejected_row",
        indicator="rechazos_abiertos",
        observed_value=float(ctx.rechazos_abiertos),
        threshold=float(u.rechazos_max),
        period=ctx.periodo,
        source="core-api /api/v1/monitor",
        explanation=(
            f"Hay {ctx.rechazos_abiertos} filas rechazadas sin resolver, por encima del "
            f"umbral de {u.rechazos_max}."
        ),
        action="Revisar quarantine.rejected_row, corregir la causa y reprocesar las filas.",
        event_key=_clave("RECHAZOS_ALTOS", ctx, "calidad"),
    )


REGLAS: list[Regla] = [
    Regla(
        "VENTAS_BAJAS",
        "regla_negocio",
        "warning",
        "ventas_totales",
        "Ventas del periodo por debajo del minimo configurado.",
        _ventas_bajas,
    ),
    Regla(
        "TICKET_BAJO",
        "regla_negocio",
        "warning",
        "ticket_promedio",
        "Ticket promedio por debajo del minimo configurado.",
        _ticket_bajo,
    ),
    Regla(
        "CAIDA_VENTAS",
        "regla_negocio",
        "critical",
        "variacion_ventas_pct",
        "Caida de ventas mayor al porcentaje configurado contra el periodo anterior.",
        _caida_ventas,
    ),
    Regla(
        "MODELO_SIN_ENTRENAR",
        "umbral_ml",
        "info",
        "periodos_disponibles",
        "Modelo ML sin entrenar o con datos insuficientes.",
        _modelo_sin_entrenar,
    ),
    Regla(
        "MAE_ALTO",
        "umbral_ml",
        "warning",
        "mae_modelo",
        "Error del modelo por encima del maximo aceptado.",
        _mae_alto,
    ),
    Regla(
        "RECHAZOS_ALTOS",
        "calidad_datos",
        "critical",
        "rechazos_abiertos",
        "Filas rechazadas sin resolver por encima del umbral.",
        _rechazos_altos,
    ),
]


def evaluar(ctx: Contexto, umbrales: Umbrales | None = None) -> list[Alerta]:
    u = umbrales or Umbrales()
    disparadas: list[Alerta] = []
    for regla in REGLAS:
        alerta = regla.evaluar(ctx, u)
        if alerta is not None:
            disparadas.append(alerta)
    return disparadas


def construir_contexto(core: CoreApi, ml: MlApi) -> Contexto:
    filtros = core.filtros()
    rango = {"desde": filtros.get("desde"), "hasta": filtros.get("hasta")}
    kpis = {k["code"]: k["value"] for k in core.kpis(rango)["kpis"]}
    tendencia = core.tendencias(rango)
    monitoreo = core.monitor()

    try:
        modelo = ml.model()
    except ServiceError as exc:
        modelo = {"status": "unavailable", "message": str(exc)}

    metricas = modelo.get("metrics") or {}
    return Contexto(
        ventas=float(kpis.get("ventas", 0.0)),
        facturas=int(kpis.get("facturas", 0)),
        ticket=float(kpis.get("ticket_promedio", 0.0)),
        variacion_pct=(tendencia.get("comparacion") or {}).get("variacion_pct"),
        periodo=f"{filtros.get('desde')}..{filtros.get('hasta')}",
        data_updated_at=monitoreo.get("data_updated_at") or filtros.get("data_updated_at"),
        ml_status=str(modelo.get("status") or "unknown"),
        ml_version=modelo.get("version"),
        ml_mae=metricas.get("mae"),
        ml_periodos=int(modelo.get("train_periods") or 0) + int(modelo.get("test_periods") or 0),
        ml_message=str(modelo.get("message") or ""),
        rechazos_abiertos=int(monitoreo.get("rejected_open") or 0),
        ultimo_etl_status=(monitoreo.get("last_etl") or {}).get("status"),
    )
