"""Catalogo de reglas de calidad y validadores.

Cada regla que falla genera una fila en quarantine.rejected_row.
El catalogo es la fuente unica para el codigo y para la documentacion.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

import pyodbc

from . import db
from .specs import TableSpec

MIN_DATE = date(2000, 1, 1)
MAX_PRICE = Decimal("1000000.00")
MAX_FUTURE_DAYS = 1

RULES: dict[str, str] = {
    "DQ-001": "Clave de factura nula o invalida",
    "DQ-002": "Clave de linea nula o invalida",
    "DQ-003": "Cantidad menor o igual a cero",
    "DQ-004": "Precio unitario negativo",
    "DQ-005": "Factura inexistente en la cabecera (huerfano)",
    "DQ-006": "Producto inexistente (huerfano)",
    "DQ-007": "Fecha nula o fuera del rango permitido",
    "DQ-008": "Precio unitario fuera de rango razonable",
    "DQ-009": "Numero de factura invalido",
    "DQ-010": "Fecha futura",
    "DQ-011": "Nombre de producto vacio",
    "DQ-012": "Clave de negocio nula en dimension",
    "DQ-013": "Duplicado en el lote (supervivencia: ultimo registro)",
    "DQ-014": "Jerarquia de producto incompleta (se completa con Desconocido)",
    "DQ-015": "Importe de factura nulo",
}


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def to_clean_row(spec: TableSpec, row: dict[str, Any]) -> dict[str, Any]:
    """Aplica conversiones explicitas sin truncar precision."""
    out: dict[str, Any] = {}
    for dest, src in spec.clean_map:
        value = row.get(src)
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                value = None
        if dest == "Fecha" and value is not None and hasattr(value, "date"):
            value = value.date()
        if dest in {"VentaAsociada", "PrecioUnitario"} and value is not None:
            value = Decimal(value).quantize(Decimal("0.01"))
        out[dest] = value
    return out


def validate(spec: TableSpec, row: dict[str, Any], ctx: dict[str, set[Any]]) -> list[tuple[str, str]]:
    """Devuelve la lista de (regla, detalle) incumplidas por la fila."""
    errors: list[tuple[str, str]] = []
    key = row.get(spec.key_column)
    today = date.today()

    if spec.kind == "dimension":
        if key is None:
            errors.append(("DQ-012", f"{spec.key_column} nulo"))
        if spec.name == "Producto" and _is_blank(row.get("NombreProducto")):
            errors.append(("DQ-011", "NombreProducto vacio"))
        return errors

    if spec.kind == "factura":
        if key is None:
            errors.append(("DQ-001", "IdFactura nulo"))
        if _is_blank(row.get("NumeroFactura")) or int(row["NumeroFactura"]) <= 0:
            errors.append(("DQ-009", f"NumeroFactura={row.get('NumeroFactura')}"))
        if row.get("VentaAsociada") is None:
            errors.append(("DQ-015", "VentaAsociada nula"))
        fecha = row.get("Fecha")
        if fecha is None:
            errors.append(("DQ-007", "Fecha nula"))
        else:
            f = fecha.date() if hasattr(fecha, "date") else fecha
            if f < MIN_DATE or f > today + timedelta(days=MAX_FUTURE_DAYS):
                errors.append(("DQ-007", f"Fecha fuera de rango: {f}"))
            if f > today + timedelta(days=MAX_FUTURE_DAYS):
                errors.append(("DQ-010", f"Fecha futura: {f}"))
        return errors

    # detalle de factura
    if key is None:
        errors.append(("DQ-002", "IdFacturaDetalle nulo"))
    cantidad = row.get("Cantidad")
    if cantidad is None or int(cantidad) <= 0:
        errors.append(("DQ-003", f"Cantidad={cantidad}"))
    precio = row.get("PrecioUnitario")
    if precio is None or Decimal(precio) < 0:
        errors.append(("DQ-004", f"PrecioUnitario={precio}"))
    elif Decimal(precio) > MAX_PRICE:
        errors.append(("DQ-008", f"PrecioUnitario={precio} excede {MAX_PRICE}"))
    if row.get("IdFactura") is not None and row["IdFactura"] not in ctx.get("facturas", set()):
        errors.append(("DQ-005", f"IdFactura={row['IdFactura']} no existe"))
    if row.get("IdProducto") is not None and row["IdProducto"] not in ctx.get("productos", set()):
        errors.append(("DQ-006", f"IdProducto={row['IdProducto']} no existe"))
    return errors


def reject(
    conn: pyodbc.Connection,
    execution_id: int,
    source_object: str,
    rule_code: str,
    detail: str,
    business_key: Any,
    payload: dict[str, Any],
) -> None:
    """Registra una fila rechazada conservando el payload original."""
    db.execute(
        conn,
        """
        INSERT INTO quarantine.rejected_row
            (execution_id, source_object, rule_code, rule_detail, business_key, payload)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            execution_id,
            source_object,
            rule_code,
            detail[:500],
            None if business_key is None else str(business_key),
            json.dumps(payload, default=str, ensure_ascii=False),
        ),
    )
