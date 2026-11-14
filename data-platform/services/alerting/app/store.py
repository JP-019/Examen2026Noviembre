"""Registro operativo de alertas y entregas en SQLite.

SQLite se usa solo para el registro de alertas (generacion y entrega). Las
metricas siguen viniendo de core-api. La clave `event_key` es unica: evita
notificar dos veces el mismo evento.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import ALERT_DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS alert (
    alert_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    event_key       TEXT NOT NULL UNIQUE,
    rule_code       TEXT NOT NULL,
    alert_type      TEXT NOT NULL,
    severity        TEXT NOT NULL,
    entity          TEXT,
    indicator       TEXT NOT NULL,
    observed_value  REAL,
    threshold       REAL,
    period          TEXT,
    source          TEXT NOT NULL,
    explanation     TEXT NOT NULL,
    action          TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'open',
    simulated       INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL,
    acknowledged_at TEXT
);

CREATE TABLE IF NOT EXISTS alert_delivery (
    delivery_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id     INTEGER NOT NULL REFERENCES alert(alert_id),
    channel      TEXT NOT NULL,
    status       TEXT NOT NULL,
    attempted_at TEXT NOT NULL,
    delivered_at TEXT,
    detail       TEXT,
    UNIQUE (alert_id, channel)
);

CREATE INDEX IF NOT EXISTS ix_alert_created ON alert (created_at DESC);
CREATE INDEX IF NOT EXISTS ix_alert_status ON alert (status);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class AlertStore:
    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path or ALERT_DB_PATH)

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.executescript(SCHEMA)
        return conn

    def add(self, alerta: Any) -> tuple[int, bool]:
        """Inserta la alerta si el evento es nuevo. Devuelve (id, creada)."""
        conn = self._connect()
        try:
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO alert
                    (event_key, rule_code, alert_type, severity, entity, indicator,
                     observed_value, threshold, period, source, explanation, action,
                     status, simulated, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?, ?)
                """,
                (
                    alerta.event_key,
                    alerta.rule_code,
                    alerta.alert_type,
                    alerta.severity,
                    alerta.entity,
                    alerta.indicator,
                    alerta.observed_value,
                    alerta.threshold,
                    alerta.period,
                    alerta.source,
                    alerta.explanation,
                    alerta.action,
                    1 if alerta.simulated else 0,
                    _now(),
                ),
            )
            created = cur.rowcount == 1
            conn.commit()
            if created:
                return int(cur.lastrowid), True
            row = conn.execute(
                "SELECT alert_id FROM alert WHERE event_key = ?", (alerta.event_key,)
            ).fetchone()
            return int(row["alert_id"]), False
        finally:
            conn.close()

    def deliver(
        self,
        alert_id: int,
        channel: str = "dashboard",
        status: str = "delivered",
        detail: str | None = None,
    ) -> dict[str, Any]:
        """Registra el intento de entrega. Idempotente por (alerta, canal)."""
        conn = self._connect()
        try:
            attempted = _now()
            delivered = attempted if status == "delivered" else None
            conn.execute(
                """
                INSERT OR IGNORE INTO alert_delivery
                    (alert_id, channel, status, attempted_at, delivered_at, detail)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (alert_id, channel, status, attempted, delivered, detail),
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM alert_delivery WHERE alert_id = ? AND channel = ?",
                (alert_id, channel),
            ).fetchone()
            return dict(row)
        finally:
            conn.close()

    def get(self, alert_id: int) -> dict[str, Any] | None:
        conn = self._connect()
        try:
            row = conn.execute("SELECT * FROM alert WHERE alert_id = ?", (alert_id,)).fetchone()
            if row is None:
                return None
            alerta = dict(row)
            entregas = conn.execute(
                "SELECT * FROM alert_delivery WHERE alert_id = ? ORDER BY delivery_id",
                (alert_id,),
            ).fetchall()
            alerta["deliveries"] = [dict(e) for e in entregas]
            return alerta
        finally:
            conn.close()

    def list(
        self,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 50,
        include_simulated: bool = True,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if status:
            clauses.append("status = ?")
            params.append(status)
        if severity:
            clauses.append("severity = ?")
            params.append(severity)
        if not include_simulated:
            clauses.append("simulated = 0")
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        params.append(max(1, min(limit, 200)))
        conn = self._connect()
        try:
            rows = conn.execute(
                f"SELECT * FROM alert {where} ORDER BY alert_id DESC LIMIT ?", params
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def acknowledge(self, alert_id: int) -> dict[str, Any] | None:
        conn = self._connect()
        try:
            conn.execute(
                """
                UPDATE alert
                SET status = 'acknowledged', acknowledged_at = ?
                WHERE alert_id = ? AND status = 'open'
                """,
                (_now(), alert_id),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM alert WHERE alert_id = ?", (alert_id,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def stats(self) -> dict[str, Any]:
        conn = self._connect()
        try:
            por_severidad = {
                r["severity"]: r["total"]
                for r in conn.execute(
                    "SELECT severity, COUNT(*) AS total FROM alert GROUP BY severity"
                ).fetchall()
            }
            por_estado = {
                r["status"]: r["total"]
                for r in conn.execute(
                    "SELECT status, COUNT(*) AS total FROM alert GROUP BY status"
                ).fetchall()
            }
            total = conn.execute("SELECT COUNT(*) AS n FROM alert").fetchone()["n"]
            simuladas = conn.execute(
                "SELECT COUNT(*) AS n FROM alert WHERE simulated = 1"
            ).fetchone()["n"]
            entregadas = conn.execute(
                "SELECT COUNT(*) AS n FROM alert_delivery WHERE status = 'delivered'"
            ).fetchone()["n"]
            return {
                "total": total,
                "simuladas": simuladas,
                "por_severidad": por_severidad,
                "por_estado": por_estado,
                "entregadas": entregadas,
            }
        finally:
            conn.close()
