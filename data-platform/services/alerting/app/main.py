"""Motor de alertas y monitoreo operativo (T13).

Evalua reglas de negocio, ML y calidad, registra alertas sin duplicarlas,
registra la entrega al canal dashboard y publica una vista de monitoreo.

Ejecucion (desde services/alerting):
    uvicorn app.main:app --port 8004
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import asdict
from datetime import datetime, timezone
from ipaddress import ip_address
from typing import Annotated, Any, Literal

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel, Field

from . import monitor, rules, views
from .clients import CoreApi, MlApi, ServiceError
from .config import ALERT_DB_PATH
from .store import AlertStore

logger = logging.getLogger("alerting_service")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Motor de alertas - ventas",
    version="1.0.0",
    description=(
        "Reglas de negocio, ML y calidad con registro de generacion y entrega, "
        "anti-duplicado y vista de monitoreo."
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


store = AlertStore()
core = CoreApi()
ml = MlApi()


class SimulateRequest(BaseModel):
    rule_code: str = "SIMULACION"
    severity: Literal["info", "warning", "critical"] = "warning"
    indicator: str = "ventas_totales"
    entity: str | None = "demo"
    observed_value: float | None = None
    threshold: float | None = None
    period: str | None = None
    explanation: str = Field(
        default="Evento simulado para probar el canal de notificaciones.",
        max_length=1000,
    )
    action: str = Field(
        default="Verificar la vista de monitoreo y reconocer la alerta.",
        max_length=1000,
    )


class EvaluationResponse(BaseModel):
    evaluado_en: str
    periodo: str
    umbrales: dict[str, float | int]
    reglas_evaluadas: int
    disparadas: int
    nuevas: int
    duplicadas: int
    detalle: list[dict[str, Any]]


def _evaluar() -> EvaluationResponse:
    try:
        contexto = rules.construir_contexto(core, ml)
    except ServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    umbrales = rules.Umbrales()
    disparadas = rules.evaluar(contexto, umbrales)

    detalle: list[dict[str, Any]] = []
    nuevas = duplicadas = 0
    for alerta in disparadas:
        alert_id, creada = store.add(alerta)
        if creada:
            store.deliver(alert_id, "dashboard", "delivered", "Publicada en /monitor")
            nuevas += 1
        else:
            duplicadas += 1
        detalle.append(
            {
                "alert_id": alert_id,
                "rule_code": alerta.rule_code,
                "severity": alerta.severity,
                "indicator": alerta.indicator,
                "observed_value": alerta.observed_value,
                "threshold": alerta.threshold,
                "period": alerta.period,
                "nueva": creada,
            }
        )

    logger.info(
        "evaluacion: %s reglas, %s disparadas, %s nuevas, %s duplicadas",
        len(rules.REGLAS),
        len(disparadas),
        nuevas,
        duplicadas,
    )
    return EvaluationResponse(
        evaluado_en=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        periodo=contexto.periodo,
        umbrales=asdict(umbrales),
        reglas_evaluadas=len(rules.REGLAS),
        disparadas=len(disparadas),
        nuevas=nuevas,
        duplicadas=duplicadas,
        detalle=detalle,
    )


@app.get("/", include_in_schema=False)
def root() -> dict[str, Any]:
    return {
        "service": "alerting",
        "docs": "/docs",
        "monitor": "/monitor",
        "endpoints": [
            "/rules",
            "/alerts",
            "/alerts/{id}",
            "/alerts/{id}/ack",
            "/alerts/evaluate",
            "/alerts/simulate",
            "/monitor",
            "/monitor.json",
            "/health",
        ],
        "alert_db": str(ALERT_DB_PATH),
    }


@app.get("/health", summary="Estado del motor, core-api y ML")
def health() -> dict[str, Any]:
    estado: dict[str, Any] = {"service": "alerting", "status": "ok", "alert_db": str(ALERT_DB_PATH)}
    try:
        estado["core_api"] = core.health().get("status")
    except ServiceError as exc:
        estado["core_api"] = f"error: {exc}"
        estado["status"] = "degraded"
    try:
        estado["ml"] = ml.model().get("status")
    except ServiceError as exc:
        estado["ml"] = f"error: {exc}"
        estado["status"] = "degraded"
    estado["alertas"] = store.stats()
    return estado


@app.get("/rules", summary="Reglas y umbrales vigentes")
def listar_reglas() -> dict[str, Any]:
    return {
        "total": len(rules.REGLAS),
        "umbrales": asdict(rules.Umbrales()),
        "reglas": [
            {
                "code": r.code,
                "tipo": r.alert_type,
                "severidad": r.severity,
                "indicador": r.indicator,
                "descripcion": r.descripcion,
            }
            for r in rules.REGLAS
        ],
    }


@app.post("/alerts/evaluate", response_model=EvaluationResponse, summary="Evalua reglas y registra alertas")
def evaluar() -> EvaluationResponse:
    return _evaluar()


@app.get("/alerts", summary="Listado de alertas con estado")
def listar_alertas(
    status: Annotated[Literal["open", "acknowledged", "closed"] | None, Query()] = None,
    severity: Annotated[Literal["info", "warning", "critical"] | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    incluir_simuladas: Annotated[bool, Query()] = True,
) -> dict[str, Any]:
    alertas = store.list(status, severity, limit, incluir_simuladas)
    return {"total": len(alertas), "alertas": alertas}


@app.get("/alerts/{alert_id}", summary="Detalle y estado de una alerta")
def detalle_alerta(alert_id: int) -> dict[str, Any]:
    alerta = store.get(alert_id)
    if alerta is None:
        raise HTTPException(status_code=404, detail=f"Alerta {alert_id} no encontrada")
    return alerta


@app.post("/alerts/{alert_id}/ack", summary="Reconoce una alerta")
def reconocer_alerta(alert_id: int) -> dict[str, Any]:
    if store.get(alert_id) is None:
        raise HTTPException(status_code=404, detail=f"Alerta {alert_id} no encontrada")
    return store.acknowledge(alert_id) or {}


@app.post("/alerts/simulate", summary="Genera una alerta simulada identificada")
def simular(body: SimulateRequest) -> dict[str, Any]:
    alerta = rules.Alerta(
        rule_code=body.rule_code,
        alert_type="simulacion",
        severity=body.severity,
        entity=body.entity,
        indicator=body.indicator,
        observed_value=body.observed_value,
        threshold=body.threshold,
        period=body.period,
        source="POST /alerts/simulate",
        explanation=body.explanation,
        action=body.action,
        event_key=f"SIM|{uuid.uuid4()}",
        simulated=True,
    )
    alert_id, _ = store.add(alerta)
    store.deliver(alert_id, "dashboard", "delivered", "Alerta simulada visible en /monitor")
    return store.get(alert_id) or {}


@app.get("/monitor.json", summary="Snapshot de monitoreo en JSON")
def monitor_json() -> dict[str, Any]:
    try:
        return monitor.snapshot(store, core, ml)
    except ServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/monitor", response_class=HTMLResponse, summary="Vista de monitoreo operativo")
def monitor_html() -> HTMLResponse:
    try:
        snapshot = monitor.snapshot(store, core, ml)
    except ServiceError as exc:
        return HTMLResponse(
            f"<!doctype html><meta charset='utf-8'><h1>Monitoreo no disponible</h1>"
            f"<p>{exc}</p><p>Verificar core-api en el puerto 8000.</p>",
            status_code=503,
        )
    return HTMLResponse(views.render(snapshot))
