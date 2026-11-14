"""Prueba end-to-end de la plataforma (T14).

Requiere los 6 servicios levantados y una base de alertas aislada:

    core-api 8000, catalog 8001, ml 8002, genai 8003, alerting 8004, dashboard 8501

Verifica el recorrido completo: datos -> API -> dashboard, asistente, modelo y
alertas, incluyendo el anti-duplicado.

Uso:
    python tests/e2e_smoke.py
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

CORE = "http://localhost:8000"
CATALOG = "http://localhost:8001"
ML = "http://localhost:8002"
GENAI = "http://localhost:8003"
ALERT = "http://localhost:8004"
DASHBOARD = "http://localhost:8501"


def _request(method: str, url: str, body: dict | None = None) -> tuple[int, object]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"} if data else {},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8", errors="replace")
            if "json" in response.headers.get("Content-Type", ""):
                return response.status, json.loads(raw)
            return response.status, raw
    except urllib.error.HTTPError as exc:
        return exc.code, None


def get(url: str) -> tuple[int, object]:
    return _request("GET", url)


def post(url: str, body: dict | None = None) -> tuple[int, object]:
    return _request("POST", url, body)


def main() -> int:
    fallos = 0

    def check(nombre: str, condicion: bool, detalle: str = "") -> None:
        nonlocal fallos
        estado = "OK" if condicion else "FALLO"
        print(f"  {nombre:<52} {estado}{'' if condicion else ' -> ' + detalle}")
        if not condicion:
            fallos += 1

    print("End-to-end: fuente -> DW -> API -> dashboard / GenAI / ML / alertas")

    status, health = get(f"{CORE}/api/v1/health")
    check("core-api responde health", status == 200 and health["status"] == "ok")  # type: ignore[index]
    print(f"    filas={health.get('fact_rows')} etl={health.get('last_etl_status')}")  # type: ignore[union-attr]

    status, kpis = get(f"{CORE}/api/v1/kpis")
    ventas = next(k["value"] for k in kpis["kpis"] if k["code"] == "ventas")  # type: ignore[index]
    check("KPIs devuelven ventas reales (696.40)", status == 200 and round(ventas, 2) == 696.40, str(ventas))

    status, catalog = get(f"{CATALOG}/")
    check(
        "catalogo declara 7/7 servicios",
        status == 200 and catalog["services"] == 7 and catalog["implemented"] == 7,  # type: ignore[index]
    )

    status, model = get(f"{ML}/model")
    check(
        "ML informa insufficient_data sin inventar metricas",
        status == 200
        and model["status"] == "insufficient_data"  # type: ignore[index]
        and model["metrics"]["mae"] is None,  # type: ignore[index]
    )

    status, ml_root = get(f"{ML}/")
    check(
        "ML publica correctamente su ruta de inicio",
        status == 200 and "/train" in ml_root["endpoints"],  # type: ignore[index]
    )

    status, genai = post(f"{GENAI}/ask", {"pregunta": "ventas por local"})
    check(
        "GenAI responde con fuentes y grounded",
        status == 200
        and genai["grounded"] is True  # type: ignore[index]
        and len(genai["fuentes"]) == 1  # type: ignore[index]
        and "S/" in genai["respuesta"],  # type: ignore[index]
    )

    status, primera = post(f"{ALERT}/alerts/evaluate")
    check(
        "primera evaluacion genera 3 alertas nuevas",
        status == 200 and primera["nuevas"] == 3,  # type: ignore[index]
    )
    status, segunda = post(f"{ALERT}/alerts/evaluate")
    check(
        "segunda evaluacion no duplica",
        status == 200 and segunda["nuevas"] == 0 and segunda["duplicadas"] == 3,  # type: ignore[index]
    )

    status, monitor = get(f"{ALERT}/monitor.json")
    check(
        "monitor integra pipeline y alertas",
        status == 200
        and monitor["pipeline"]["fact_rows"] == 5  # type: ignore[index]
        and monitor["notificaciones"]["total"] >= 3,  # type: ignore[index]
    )

    status, dashboard = get(f"{DASHBOARD}/_stcore/health")
    check(
        "dashboard responde health",
        status == 200 and str(dashboard).strip().lower() == "ok",  # type: ignore[arg-type]
    )

    print("")
    print("RESULTADO:", "OK" if not fallos else f"{fallos} verificaciones fallaron")
    return 0 if not fallos else 1


if __name__ == "__main__":
    raise SystemExit(main())
