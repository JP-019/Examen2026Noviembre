"""Prueba de humo de core-api (T09).

No requiere dependencias externas: usa la libreria estandar. Espera que la API
este corriendo (por defecto en http://localhost:8000).

Uso:
    python tests/smoke_core_api.py
    python tests/smoke_core_api.py http://localhost:8000
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000").rstrip("/")

CASES: list[tuple[str, str, int]] = [
    ("health", "/api/v1/health", 200),
    ("kpis", "/api/v1/kpis", 200),
    ("kpis con filtro", "/api/v1/kpis?local=PLAZA%20VEA%20JOCKEY", 200),
    ("kpis periodo vacio", "/api/v1/kpis?desde=1990-01-01&hasta=1990-12-31", 200),
    ("tendencias dia", "/api/v1/tendencias?granularidad=dia", 200),
    ("tendencias mes", "/api/v1/tendencias?granularidad=mes", 200),
    ("detalle", "/api/v1/detalle?page=1&page_size=2", 200),
    ("detalle fuera de rango", "/api/v1/detalle?page=999", 200),
    ("filtros", "/api/v1/filtros", 200),
    ("agrupado producto", "/api/v1/agrupado?dimension=producto&limit=3", 200),
    ("agrupado seccion", "/api/v1/agrupado?dimension=seccion", 200),
    ("agrupado dimension invalida", "/api/v1/agrupado?dimension=cliente", 422),
    ("monitor", "/api/v1/monitor", 200),
    ("rango invalido", "/api/v1/kpis?desde=2020-01-01&hasta=2019-01-01", 422),
    ("pagina invalida", "/api/v1/detalle?page=0", 422),
]


def call(path: str) -> tuple[int, dict | None]:
    try:
        with urllib.request.urlopen(f"{BASE}{path}", timeout=15) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, None


def main() -> int:
    failures = 0
    print(f"Prueba de humo core-api -> {BASE}")
    print(f"{'caso':<24} {'esperado':>8} {'obtenido':>8}  resultado")
    for name, path, expected in CASES:
        status, _ = call(path)
        ok = status == expected
        failures += 0 if ok else 1
        print(f"{name:<24} {expected:>8} {status:>8}  {'OK' if ok else 'FALLO'}")

    _, kpis = call("/api/v1/kpis")
    _, health = call("/api/v1/health")
    print("")
    if kpis and health:
        print(f"KPIs devueltos: {len(kpis['kpis'])}")
        print(f"Ventas totales: {kpis['kpis'][0]['value']}")
        print(f"Filas en el hecho: {health['fact_rows']}")
        print(f"data_updated_at: {health['data_updated_at']}")
    if not kpis or len(kpis["kpis"]) < 4:
        failures += 1
        print("FALLO: se esperaban al menos 4 KPIs")

    print("")
    print("RESULTADO:", "OK" if failures == 0 else f"{failures} FALLOS")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
