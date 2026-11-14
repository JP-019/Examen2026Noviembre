"""Serie mensual de ventas leida del Data Warehouse."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

import pyodbc

from .config import DW


@dataclass(frozen=True)
class Punto:
    periodo: date  # primer dia del mes
    ventas: float

    @property
    def etiqueta(self) -> str:
        return self.periodo.strftime("%Y-%m")


def connect() -> pyodbc.Connection:
    return pyodbc.connect(DW.connection_string(), autocommit=True, timeout=30)


def load_series() -> list[Punto]:
    """Ventas mensuales observadas. Una fila por mes con datos."""
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT DATEFROMPARTS(YEAR(Fecha), MONTH(Fecha), 1) AS periodo,
                   SUM(ImporteLinea) AS ventas
            FROM dw.vw_Ventas
            GROUP BY DATEFROMPARTS(YEAR(Fecha), MONTH(Fecha), 1)
            ORDER BY periodo
            """
        )
        return [
            Punto(periodo=row[0], ventas=float(row[1] or Decimal("0")))
            for row in cur.fetchall()
        ]
    finally:
        conn.close()


def data_updated_at() -> str | None:
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT MAX(end_time)
            FROM audit.etl_execution
            WHERE status = 'SUCCESS' AND target_object LIKE 'dw.%'
            """
        )
        row = cur.fetchone()
        return row[0].isoformat() if row and row[0] else None
    finally:
        conn.close()


def save_experiment(
    version: str,
    model_name: str,
    train_periods: int,
    test_periods: int,
    metrics: dict[str, float | None],
    baseline: dict[str, float | None],
    parameters: str,
    notes: str,
) -> int | None:
    """Registra la corrida en audit.ml_experiment (si la tabla existe)."""
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO audit.ml_experiment
                (version, model_name, train_periods, test_periods,
                 mae, rmse, baseline_mae, baseline_rmse, parameters, notes)
            OUTPUT INSERTED.experiment_id
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            version,
            model_name,
            train_periods,
            test_periods,
            metrics.get("mae"),
            metrics.get("rmse"),
            baseline.get("mae"),
            baseline.get("rmse"),
            parameters,
            notes,
        )
        experiment_id = int(cur.fetchone()[0])
        conn.commit()
        return experiment_id
    except pyodbc.Error:
        return None
    finally:
        conn.close()
