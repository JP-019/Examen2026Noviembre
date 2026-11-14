"""Acceso a datos. Capa unica de conexion y helpers sobre pyodbc."""

from __future__ import annotations

from typing import Any, Iterable, Sequence

import pyodbc

from .config import DbConfig


def connect(cfg: DbConfig, autocommit: bool = False) -> pyodbc.Connection:
    """Abre una conexion ODBC. El llamador es responsable de cerrarla."""
    return pyodbc.connect(cfg.connection_string(), autocommit=autocommit, timeout=30)


def fetch_all(conn: pyodbc.Connection, sql: str, params: Sequence[Any] = ()) -> list[dict[str, Any]]:
    cur = conn.cursor()
    try:
        cur.execute(sql, *params)
        columns = [c[0] for c in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]
    finally:
        cur.close()


def fetch_one(conn: pyodbc.Connection, sql: str, params: Sequence[Any] = ()) -> dict[str, Any] | None:
    rows = fetch_all(conn, sql, params)
    return rows[0] if rows else None


def fetch_scalar(conn: pyodbc.Connection, sql: str, params: Sequence[Any] = ()) -> Any:
    row = fetch_one(conn, sql, params)
    if not row:
        return None
    return next(iter(row.values()))


def execute(conn: pyodbc.Connection, sql: str, params: Sequence[Any] = ()) -> int:
    cur = conn.cursor()
    try:
        cur.execute(sql, *params)
        return cur.rowcount
    finally:
        cur.close()


def executemany(conn: pyodbc.Connection, sql: str, rows: Iterable[Sequence[Any]]) -> int:
    cur = conn.cursor()
    try:
        cur.fast_executemany = True
        cur.executemany(sql, list(rows))
        return cur.rowcount
    finally:
        cur.close()


def table_counts(conn: pyodbc.Connection, tables: Iterable[str]) -> dict[str, int]:
    """Conteo rapido por tabla usando metadatos (sin escanear)."""
    result: dict[str, int] = {}
    for table in tables:
        schema, name = table.split(".", 1)
        result[table] = int(
            fetch_scalar(
                conn,
                """
                SELECT COALESCE(SUM(p.rows), 0)
                FROM sys.partitions p
                JOIN sys.objects o ON o.object_id = p.object_id
                JOIN sys.schemas s ON s.schema_id = o.schema_id
                WHERE s.name = ? AND o.name = ? AND p.index_id IN (0, 1)
                """,
                (schema, name.strip("[]")),
            )
            or 0
        )
    return result
