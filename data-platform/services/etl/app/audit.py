"""Auditoria de ejecuciones, watermarks y linaje.

Cada etapa del pipeline abre una fila en audit.etl_execution con estado
RUNNING y la cierra en SUCCESS o FAILED. La auditoria usa su propia
conexion (autocommit) para sobrevivir al rollback de la etapa de datos.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Iterator

import pyodbc

from . import db
from .config import DW


@dataclass
class Counts:
    read: int = 0
    inserted: int = 0
    updated: int = 0
    rejected: int = 0


def start(pipeline: str, source_object: str, target_object: str, watermark_start: datetime | None = None) -> int:
    conn = db.connect(DW, autocommit=True)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO audit.etl_execution
                (pipeline_name, source_object, target_object, status, watermark_start)
            OUTPUT INSERTED.execution_id
            VALUES (?, ?, ?, 'RUNNING', ?)
            """,
            pipeline,
            source_object,
            target_object,
            watermark_start,
        )
        execution_id = int(cur.fetchone()[0])
        cur.close()
        return execution_id
    finally:
        conn.close()


def finish(
    execution_id: int,
    status: str,
    counts: Counts,
    error: str | None = None,
    watermark_end: datetime | None = None,
) -> None:
    conn = db.connect(DW, autocommit=True)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE audit.etl_execution
               SET end_time = SYSUTCDATETIME(),
                   rows_read = ?,
                   rows_inserted = ?,
                   rows_updated = ?,
                   rows_rejected = ?,
                   status = ?,
                   error_detail = ?,
                   watermark_end = ?
             WHERE execution_id = ?
            """,
            counts.read,
            counts.inserted,
            counts.updated,
            counts.rejected,
            status,
            error,
            watermark_end,
            execution_id,
        )
        cur.close()
    finally:
        conn.close()


@contextmanager
def run(pipeline: str, source_object: str, target_object: str, watermark_start: datetime | None = None) -> Iterator[tuple[int, Counts]]:
    """Context manager que garantiza cierre de la fila de auditoria."""
    execution_id = start(pipeline, source_object, target_object, watermark_start)
    counts = Counts()
    try:
        yield execution_id, counts
    except Exception as exc:  # noqa: BLE001 - se registra y se propaga
        finish(execution_id, "FAILED", counts, error=f"{type(exc).__name__}: {exc}")
        raise
    else:
        finish(execution_id, "SUCCESS", counts, watermark_end=watermark_start)


def get_watermark(source_object: str, pipeline: str = "sales_incremental") -> datetime | None:
    conn = db.connect(DW)
    try:
        return db.fetch_scalar(
            conn,
            """
            SELECT watermark_value
              FROM audit.etl_watermark
             WHERE pipeline_name = ? AND source_object = ?
            """,
            (pipeline, source_object),
        )
    finally:
        conn.close()


def set_watermark(
    execution_id: int,
    source_object: str,
    watermark_column: str,
    watermark_value: datetime,
    pipeline: str = "sales_incremental",
) -> None:
    conn = db.connect(DW, autocommit=True)
    try:
        db.execute(
            conn,
            """
            MERGE audit.etl_watermark AS t
            USING (SELECT ? AS pipeline_name, ? AS source_object) AS s
               ON t.pipeline_name = s.pipeline_name AND t.source_object = s.source_object
            WHEN MATCHED THEN
                UPDATE SET watermark_column = ?, watermark_value = ?,
                           last_execution_id = ?, updated_at = SYSUTCDATETIME()
            WHEN NOT MATCHED THEN
                INSERT (pipeline_name, source_object, watermark_column, watermark_value, last_execution_id, updated_at)
                VALUES (?, ?, ?, ?, ?, SYSUTCDATETIME());
            """,
            (
                pipeline,
                source_object,
                watermark_column,
                watermark_value,
                execution_id,
                pipeline,
                source_object,
                watermark_column,
                watermark_value,
                execution_id,
            ),
        )
    finally:
        conn.close()


def add_lineage(
    conn: pyodbc.Connection,
    execution_id: int,
    source_object: str,
    target_object: str,
    business_key: object,
    operation: str,
) -> None:
    db.execute(
        conn,
        """
        INSERT INTO audit.row_lineage (execution_id, source_object, target_object, business_key, operation)
        VALUES (?, ?, ?, ?, ?)
        """,
        (execution_id, source_object, target_object, str(business_key), operation),
    )
