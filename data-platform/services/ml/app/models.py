"""Entrenamiento, evaluacion temporal y prediccion de ventas mensuales.

Reglas:
- Division **temporal**: el modelo nunca se evalua con datos de entrenamiento.
- Baseline obligatorio: naive (ultimo valor) o naive estacional (12 meses).
- Si no hay periodos suficientes, se informa `insufficient_data` en lugar de
  publicar metricas sin respaldo.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from typing import Any

import joblib
import numpy as np
from sklearn.linear_model import LinearRegression

from .config import (
    METADATA_PATH,
    MIN_TEST_PERIODS,
    MIN_TRAIN_PERIODS,
    MODEL_PATH,
    TEST_FRACTION,
)
from .dataset import Punto

MODEL_NAME = "regresion_lineal_tendencia_estacional"


@dataclass
class Evaluation:
    mae: float | None = None
    rmse: float | None = None
    mape: float | None = None

    def as_dict(self) -> dict[str, float | None]:
        return {"mae": self.mae, "rmse": self.rmse, "mape": self.mape}


@dataclass
class Training:
    status: str
    message: str
    version: str | None = None
    model: Any | None = None
    train_periods: int = 0
    test_periods: int = 0
    metrics: Evaluation = field(default_factory=Evaluation)
    baseline: Evaluation = field(default_factory=Evaluation)
    parameters: dict[str, float | str] = field(default_factory=dict)
    series: list[Punto] = field(default_factory=list)
    predictions: list[dict[str, Any]] = field(default_factory=list)
    experiment_id: int | None = None

    @property
    def trained(self) -> bool:
        return self.status == "trained"

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "message": self.message,
            "version": self.version,
            "trained_at": self.parameters.get("trained_at"),
            "model": MODEL_NAME if self.trained else None,
            "train_periods": self.train_periods,
            "test_periods": self.test_periods,
            "evaluated_on": "test",
            "parameters": self.parameters,
            "metrics": self.metrics.as_dict(),
            "baseline": self.baseline.as_dict(),
            "experiment_id": self.experiment_id,
            "observed_periods": [
                {"periodo": p.etiqueta, "ventas": round(p.ventas, 2)} for p in self.series
            ],
        }


def _features(periodos: list[date], inicio: date) -> np.ndarray:
    rows = []
    for periodo in periodos:
        t = (periodo.year - inicio.year) * 12 + (periodo.month - inicio.month)
        mes = periodo.month
        rows.append([t, np.sin(2 * np.pi * mes / 12), np.cos(2 * np.pi * mes / 12)])
    return np.array(rows, dtype=float)


def _metrics(real: list[float], pred: list[float]) -> Evaluation:
    if not real:
        return Evaluation()
    errores = np.array(real, dtype=float) - np.array(pred, dtype=float)
    mae = float(np.mean(np.abs(errores)))
    rmse = float(np.sqrt(np.mean(errores**2)))
    con_base = [abs(e) / r * 100 for e, r in zip(errores, real) if r]
    mape = float(np.mean(con_base)) if con_base else None
    return Evaluation(mae=round(mae, 2), rmse=round(rmse, 2), mape=round(mape, 2) if mape is not None else None)


def _baseline_pred(test: list[Punto], train: list[Punto]) -> list[float]:
    """Naive estacional si hay 12+ meses; si no, ultimo valor observado."""
    if len(train) >= 12:
        por_mes = {p.periodo.month: p.ventas for p in train}
        return [por_mes.get(p.periodo.month, train[-1].ventas) for p in test]
    return [train[-1].ventas for _ in test]


def train(series: list[Punto]) -> Training:
    total = len(series)
    if total < MIN_TRAIN_PERIODS + MIN_TEST_PERIODS:
        return Training(
            status="insufficient_data",
            message=(
                f"Se necesitan al menos {MIN_TRAIN_PERIODS + MIN_TEST_PERIODS} meses con ventas "
                f"para dividir en entrenamiento y prueba; hay {total}. No se publican metricas."
            ),
            series=series,
            train_periods=max(total - max(1, round(total * TEST_FRACTION)), 0),
            test_periods=total - max(total - max(1, round(total * TEST_FRACTION)), 0),
        )

    test_size = max(MIN_TEST_PERIODS, round(total * TEST_FRACTION))
    test_size = min(test_size, total - MIN_TRAIN_PERIODS)
    train_series = series[: total - test_size]
    test_series = series[total - test_size :]

    inicio = train_series[0].periodo
    x_train = _features([p.periodo for p in train_series], inicio)
    y_train = np.array([p.ventas for p in train_series], dtype=float)

    model = LinearRegression()
    model.fit(x_train, y_train)

    x_test = _features([p.periodo for p in test_series], inicio)
    pred_model = model.predict(x_test).tolist()
    pred_base = _baseline_pred(test_series, train_series)

    real = [p.ventas for p in test_series]
    metrics = _metrics(real, pred_model)
    baseline = _metrics(real, pred_base)

    version = f"v{date.today():%Y%m%d}-{total}p"
    parameters: dict[str, float | str] = {
        "trained_at": date.today().isoformat(),
        "test_fraction": TEST_FRACTION,
        "features": "tendencia + seno/coseno mensual",
        "min_train_periods": MIN_TRAIN_PERIODS,
        "min_test_periods": MIN_TEST_PERIODS,
        "fit_intercept": float(bool(model.fit_intercept)),
        "coeficientes": ";".join(f"{c:.4f}" for c in model.coef_),
        "intercepto": f"{model.intercept_:.4f}",
    }

    predictions = [
        {
            "periodo": p.etiqueta,
            "real": round(p.ventas, 2),
            "modelo": round(pred, 2),
            "baseline": round(base, 2),
        }
        for p, pred, base in zip(test_series, pred_model, pred_base)
    ]

    return Training(
        status="trained",
        message=(
            "Modelo entrenado y evaluado solo sobre el bloque de prueba temporal. "
            "El baseline se calcula con el mismo corte."
        ),
        version=version,
        model=model,
        train_periods=len(train_series),
        test_periods=len(test_series),
        metrics=metrics,
        baseline=baseline,
        parameters=parameters,
        series=series,
        predictions=predictions,
    )


def forecast(series: list[Punto], model: Any, periods: int) -> list[dict[str, Any]]:
    """Predice los siguientes `periods` meses a partir del ultimo observado."""
    if not series:
        return []
    inicio = series[0].periodo
    ultimo = series[-1].periodo
    futuros = []
    anio, mes = ultimo.year, ultimo.month
    for _ in range(periods):
        mes += 1
        if mes > 12:
            mes = 1
            anio += 1
        futuros.append(date(anio, mes, 1))

    x = _features(futuros, inicio)
    valores = model.predict(x).tolist()
    return [
        {"periodo": p.strftime("%Y-%m"), "prediccion": round(max(v, 0.0), 2)}
        for p, v in zip(futuros, valores)
    ]


def save(training: Training) -> None:
    if not training.trained or training.model is None:
        return
    METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": training.model, "version": training.version}, MODEL_PATH)
    METADATA_PATH.write_text(
        json.dumps(training.as_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
    )


def load() -> tuple[Any | None, dict[str, Any] | None]:
    if not MODEL_PATH.exists() or not METADATA_PATH.exists():
        return None, None
    payload = joblib.load(MODEL_PATH)
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    return payload.get("model"), metadata
