"""Pruebas del catalogo de calidad y de la supervivencia ante duplicados (T06, T14).

No requieren base de datos: validan las funciones puras que usa el ETL antes de
escribir en `clean` o en `quarantine`. Los valores reales de la fuente se
verifican aparte con `python -m app quality-report` y `database/99_verify.sql`.

Uso:
    python tests/test_quality_rules.py
"""

from __future__ import annotations

import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services" / "etl"))

from app import quality, staging  # noqa: E402
from app.specs import EXTRACT_SPECS  # noqa: E402

SPECS = {spec.name: spec for spec in EXTRACT_SPECS}
CTX = {"facturas": {1, 2}, "productos": {1, 2}}


def reglas(spec_name: str, row: dict) -> set[str]:
    return {code for code, _ in quality.validate(SPECS[spec_name], row, CTX)}


def main() -> int:
    fallos = 0

    def check(nombre: str, condicion: bool, detalle: str = "") -> None:
        nonlocal fallos
        estado = "OK" if condicion else "FALLO"
        print(f"  {nombre:<56} {estado}{'' if condicion else ' -> ' + detalle}")
        if not condicion:
            fallos += 1

    print("Caso 1: nulos en dimensiones")
    encontradas = reglas("Producto", {"IdProducto": None, "NombreProducto": "  "})
    print(f"  reglas: {sorted(encontradas)}")
    check("clave de dimension nula -> DQ-012", "DQ-012" in encontradas)
    check("nombre de producto vacio -> DQ-011", "DQ-011" in encontradas)

    print("\nCaso 2: cabecera de factura invalida")
    encontradas = reglas(
        "Factura",
        {
            "IdFactura": None,
            "NumeroFactura": 0,
            "VentaAsociada": None,
            "Fecha": date.today() + timedelta(days=10),
        },
    )
    print(f"  reglas: {sorted(encontradas)}")
    check("clave de factura nula -> DQ-001", "DQ-001" in encontradas)
    check("numero de factura invalido -> DQ-009", "DQ-009" in encontradas)
    check("importe de cabecera nulo -> DQ-015", "DQ-015" in encontradas)
    check("fecha fuera de rango -> DQ-007", "DQ-007" in encontradas)
    check("fecha futura -> DQ-010", "DQ-010" in encontradas)

    print("\nCaso 3: linea de factura invalida")
    encontradas = reglas(
        "FacturaDetalle",
        {
            "IdFacturaDetalle": 99,
            "IdFactura": 999,
            "IdProducto": 999,
            "Cantidad": 0,
            "PrecioUnitario": Decimal("-1.00"),
        },
    )
    print(f"  reglas: {sorted(encontradas)}")
    check("cantidad <= 0 -> DQ-003", "DQ-003" in encontradas)
    check("precio negativo -> DQ-004", "DQ-004" in encontradas)
    check("factura inexistente -> DQ-005", "DQ-005" in encontradas)
    check("producto inexistente -> DQ-006", "DQ-006" in encontradas)

    encontradas = reglas(
        "FacturaDetalle",
        {
            "IdFacturaDetalle": 100,
            "IdFactura": 1,
            "IdProducto": 1,
            "Cantidad": 1,
            "PrecioUnitario": Decimal("2000000.00"),
        },
    )
    check("precio fuera de rango -> DQ-008", "DQ-008" in encontradas)

    print("\nCaso 4: linea valida")
    encontradas = reglas(
        "FacturaDetalle",
        {
            "IdFacturaDetalle": 101,
            "IdFactura": 1,
            "IdProducto": 1,
            "Cantidad": 10,
            "PrecioUnitario": Decimal("8.20"),
        },
    )
    check("no devuelve errores", encontradas == set(), str(encontradas))

    print("\nCaso 5: normalizacion antes de validar")
    limpio = quality.to_clean_row(
        SPECS["Producto"],
        {"IdProducto": 3, "NombreProducto": "Mini Lorito ", "IdSubFamilia": 3},
    )
    check("quita espacio final", limpio["NombreProducto"] == "Mini Lorito", repr(limpio["NombreProducto"]))
    limpio = quality.to_clean_row(
        SPECS["FacturaDetalle"],
        {
            "IdFacturaDetalle": 1,
            "IdProducto": 1,
            "IdFactura": 1,
            "PrecioSinImporte": Decimal("8.2"),
            "Cantidad": 10,
        },
    )
    check("precio con 2 decimales", limpio["PrecioUnitario"] == Decimal("8.20"), str(limpio["PrecioUnitario"]))

    print("\nCaso 6: duplicados en el lote (supervivencia: ultimo)")
    filas = [
        {"IdProducto": 1, "NombreProducto": "primero"},
        {"IdProducto": 2, "NombreProducto": "unico"},
        {"IdProducto": 1, "NombreProducto": "ultimo"},
    ]
    unicas, duplicadas = staging.dedupe(filas, "IdProducto")
    check("quedan 2 claves unicas", len(unicas) == 2, str(len(unicas)))
    check("se detecta 1 duplicado", len(duplicadas) == 1, str(len(duplicadas)))
    check(
        "sobrevive la ultima aparicion",
        next(r for r in unicas if r["IdProducto"] == 1)["NombreProducto"] == "ultimo",
    )
    check("el duplicado reportado es el anterior", duplicadas[0]["NombreProducto"] == "primero")

    print("\nCaso 7: catalogo de reglas completo")
    check("15 reglas DQ catalogadas", len(quality.RULES) == 15, str(len(quality.RULES)))
    check("DQ-013 documenta duplicados", "DQ-013" in quality.RULES)

    print("")
    if fallos:
        print(f"RESULTADO: {fallos} verificaciones fallaron")
        return 1
    print("RESULTADO: OK - reglas de calidad y duplicados verificados")
    return 0


if __name__ == "__main__":
    sys.exit(main())
