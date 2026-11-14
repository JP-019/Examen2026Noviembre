"""Servicio de Machine Learning (T11).

Predice ventas mensuales con un baseline y un modelo simple, evaluados sobre un
bloque de prueba temporal. Publica metricas reales o informa datos insuficientes.

Ejecucion (desde services/ml):
    uvicorn app.main:app --port 8002
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from ipaddress import ip_address
from typing import Any

import pyodbc
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from . import dataset, models
from .config import ARTIFACTS_DIR

logger = logging.getLogger("ml_service")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Servicio de Machine Learning - ventas",
    version="1.0.0",
    description=(
        "Prediccion de ventas mensuales con division temporal, baseline obligatorio "
        "y metricas calculadas solo sobre el bloque de prueba."
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


class PredictRequest(BaseModel):
    periodos: int = Field(default=3, ge=1, le=12, description="Meses a predecir (1 a 12)")


class TrainResponse(BaseModel):
    status: str
    message: str
    version: str | None
    train_periods: int
    test_periods: int
    metrics: dict[str, float | None]
    baseline: dict[str, float | None]
    experiment_id: int | None
    saved: bool


def _current() -> tuple[Any, dict[str, Any]]:
    """Modelo guardado o, si no hay artefacto, el diagnostico del entrenamiento."""
    model, metadata = models.load()
    if model is not None and metadata is not None:
        return model, metadata
    training = models.train(dataset.load_series())
    return training.model, training.as_dict()


@app.get("/", include_in_schema=False)
def root() -> dict[str, Any]:
    return {
        "service": "ml",
        "docs": "/docs",
        "endpoints": ["/model", "/metrics", "/predict", "/series", "/train"],
    }


@app.get("/model", summary="Version, parametros y estado del modelo")
def model_info() -> dict[str, Any]:
    try:
        _, metadata = _current()
    except pyodbc.Error as exc:
        raise HTTPException(status_code=503, detail="No se pudo leer el Data Warehouse.") from exc
    return {
        **metadata,
        "data_updated_at": dataset.data_updated_at(),
        "artifacts_dir": str(ARTIFACTS_DIR),
    }


@app.get("/metrics", summary="Metricas del modelo y del baseline (solo prueba)")
def metrics() -> dict[str, Any]:
    try:
        _, metadata = _current()
    except pyodbc.Error as exc:
        raise HTTPException(status_code=503, detail="No se pudo leer el Data Warehouse.") from exc
    return {
        "status": metadata["status"],
        "message": metadata["message"],
        "version": metadata["version"],
        "evaluated_on": "test",
        "train_periods": metadata["train_periods"],
        "test_periods": metadata["test_periods"],
        "results": [
            {"modelo": "baseline", **metadata["baseline"]},
            {"modelo": "modelo", **metadata["metrics"]},
        ],
        "detalle_prueba": metadata.get("predictions", []),
    }


@app.get("/series", summary="Serie mensual observada")
def series() -> dict[str, Any]:
    try:
        puntos = dataset.load_series()
    except pyodbc.Error as exc:
        raise HTTPException(status_code=503, detail="No se pudo leer el Data Warehouse.") from exc
    return {
        "total": len(puntos),
        "data_updated_at": dataset.data_updated_at(),
        "serie": [{"periodo": p.etiqueta, "ventas": round(p.ventas, 2)} for p in puntos],
    }


@app.post("/predict", summary="Prediccion de los proximos meses")
def predict(body: PredictRequest | None = None) -> dict[str, Any]:
    periodos = body.periodos if body else 3
    try:
        model, metadata = _current()
        puntos = dataset.load_series()
    except pyodbc.Error as exc:
        raise HTTPException(status_code=503, detail="No se pudo leer el Data Warehouse.") from exc

    if model is None or metadata.get("status") != "trained":
        raise HTTPException(
            status_code=409,
            detail=(
                "No hay modelo entrenado: "
                + (metadata.get("message") or "datos insuficientes")
                + " Ejecutar POST /train cuando haya mas periodos."
            ),
        )

    return {
        "version": metadata.get("version"),
        "ultimo_observado": puntos[-1].etiqueta if puntos else None,
        "predicciones": models.forecast(puntos, model, periodos),
        "advertencia": (
            "Las predicciones son estimaciones del modelo, no ventas observadas. "
            "Interpretar junto con las metricas de error."
        ),
    }


@app.post("/train", response_model=TrainResponse, summary="Entrena y versiona el modelo")
def train() -> TrainResponse:
    try:
        puntos = dataset.load_series()
    except pyodbc.Error as exc:
        raise HTTPException(status_code=503, detail="No se pudo leer el Data Warehouse.") from exc

    training = models.train(puntos)
    saved = False
    experiment_id = None

    if training.trained:
        models.save(training)
        saved = True
        experiment_id = dataset.save_experiment(
            version=training.version or "sin-version",
            model_name=models.MODEL_NAME,
            train_periods=training.train_periods,
            test_periods=training.test_periods,
            metrics=training.metrics.as_dict(),
            baseline=training.baseline.as_dict(),
            parameters=str(training.parameters),
            notes=training.message,
        )
        logger.info(
            "modelo %s entrenado: MAE=%.2f baseline MAE=%.2f",
            training.version,
            training.metrics.mae or 0,
            training.baseline.mae or 0,
        )

    return TrainResponse(
        status=training.status,
        message=training.message,
        version=training.version,
        train_periods=training.train_periods,
        test_periods=training.test_periods,
        metrics=training.metrics.as_dict(),
        baseline=training.baseline.as_dict(),
        experiment_id=experiment_id,
        saved=saved,
    )
