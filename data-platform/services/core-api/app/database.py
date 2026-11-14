"""Acceso a datos de solo lectura.

Todas las consultas son parametrizadas: los valores viajan como `?` y nunca se
concatena texto del usuario al SQL.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator, Sequence

import pyodbc

from .config import settings


@contextmanager
def connect() -> Iterator[pyodbc.Connection]:
    conn = pyodbc.connect(settings.connection_string(), autocommit=True, timeout=15)
    try:
        yield conn
    finally:
        conn.close()


def query(sql: str, params: Sequence[Any] = ()) -> list[dict[str, Any]]:
    with connect() as conn:
        cur = conn.cursor()
        try:
            cur.execute(sql, *params)
            columns = [c[0] for c in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
        finally:
            cur.close()


def scalar(sql: str, params: Sequence[Any] = ()) -> Any:
    rows = query(sql, params)
    if not rows:
        return None
    return next(iter(rows[0].values()))
