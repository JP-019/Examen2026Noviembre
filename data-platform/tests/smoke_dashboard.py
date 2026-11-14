"""Prueba de humo del cliente del dashboard (T10).

Verifica que el dashboard solo necesita core-api: llama a cada metodo del
cliente HTTP y valida la forma de la respuesta. No importa pyodbc.

Uso (con core-api corriendo):
    python tests/smoke_dashboard.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services" / "dashboard"))

from api_client import ApiError, CoreApi  # noqa: E402


def main() -> int:
    api = CoreApi()
    fallos = 0

    try:
        health = api.health()
        print(f"health          : {health['status']} | filas={health['fact_rows']} | etl={health['last_etl_status']}")
    except ApiError as exc:
        print(f"health          : FALLO -> {exc}")
        return 1

    filtros = api.filtros()
    print(f"filtros         : {len(filtros['locales'])} locales, {len(filtros['secciones'])} secciones")
    if not filtros["locales"]:
        fallos += 1
        print("  FALLO: no hay locales para los selectores")

    kpis = api.kpis({"desde": filtros["desde"], "hasta": filtros["hasta"]})
    print(f"kpis            : {len(kpis['kpis'])} tarjetas | ventas={kpis['kpis'][0]['value']}")
    if len(kpis["kpis"]) < 4:
        fallos += 1
        print("  FALLO: se esperaban al menos 4 KPIs")

    tendencias = api.tendencias({"desde": filtros["desde"], "hasta": filtros["hasta"]}, "mes")
    print(f"tendencias      : {len(tendencias['serie'])} puntos | variacion={tendencias['comparacion']['variacion_pct']}")

    detalle = api.detalle({}, page=1, page_size=3)
    print(f"detalle         : total={detalle['total']} | filas={len(detalle['rows'])}")
    if not detalle["rows"]:
        fallos += 1
        print("  FALLO: el detalle no devolvio filas")

    vacio = api.kpis({"desde": "1990-01-01", "hasta": "1990-12-31"})
    print(f"periodo vacio   : ventas={vacio['kpis'][0]['value']}")
    if vacio["kpis"][0]["value"] != 0:
        fallos += 1
        print("  FALLO: un periodo sin datos debe devolver 0")

    print("")
    print("RESULTADO:", "OK" if fallos == 0 else f"{fallos} FALLOS")
    return 0 if fallos == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
