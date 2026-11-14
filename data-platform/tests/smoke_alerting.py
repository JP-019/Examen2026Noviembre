"""Prueba de humo del motor de alertas (T13).

Requiere core-api (8000), ml (8002) y alerting (8004) corriendo. Usar una base
SQLite aislada para no mezclar la evidencia:

    $env:ALERT_DB_PATH = "$env:TEMP\\alerts_smoke.db"
    uvicorn app.main:app --port 8004     # desde services/alerting

Uso:
    python tests/smoke_alerting.py
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

BASE = "http://localhost:8004"


def get(path: str) -> tuple[int, object]:
    return _request("GET", path)


def post(path: str, body: dict | None = None) -> tuple[int, object]:
    return _request("POST", path, body)


def _request(method: str, path: str, body: dict | None = None) -> tuple[int, object]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(
        f"{BASE}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"} if data else {},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
            if "json" in response.headers.get("Content-Type", ""):
                return response.status, json.loads(raw)
            return response.status, raw
    except urllib.error.HTTPError as exc:
        return exc.code, None


def main() -> int:
    fallos = 0

    def check(nombre: str, condicion: bool, detalle: str = "") -> None:
        nonlocal fallos
        estado = "OK" if condicion else "FALLO"
        print(f"  {nombre:<46} {estado}{'' if condicion else ' -> ' + detalle}")
        if not condicion:
            fallos += 1

    print(f"Prueba de humo alerting -> {BASE}")

    status, health = get("/health")
    check("GET /health", status == 200 and isinstance(health, dict))
    print(f"    core-api={health.get('core_api')} ml={health.get('ml')}")  # type: ignore[union-attr]

    status, reglas = get("/rules")
    check("GET /rules devuelve 6 reglas", status == 200 and reglas["total"] == 6)  # type: ignore[index]

    status, primera = post("/alerts/evaluate")
    check("POST /alerts/evaluate", status == 200)
    primeras_nuevas = primera["nuevas"]  # type: ignore[index]
    print(f"    disparadas={primera['disparadas']} nuevas={primera['nuevas']} duplicadas={primera['duplicadas']}")  # type: ignore[index]
    for item in primera["detalle"]:  # type: ignore[index]
        print(f"    id={item['alert_id']} {item['rule_code']} {item['severity']} obs={item['observed_value']}")

    status, segunda = post("/alerts/evaluate")
    check(
        "segunda evaluacion no duplica alertas",
        status == 200 and segunda["nuevas"] == 0 and segunda["duplicadas"] == primera["disparadas"],  # type: ignore[index]
    )

    status, listado = get("/alerts?status=open")
    check("GET /alerts responde", status == 200 and isinstance(listado["alertas"], list))  # type: ignore[index]
    if primera["detalle"]:  # type: ignore[index]
        alert_id = primera["detalle"][0]["alert_id"]  # type: ignore[index]
        status, ack = post(f"/alerts/{alert_id}/ack")
        check("POST /alerts/{id}/ack", status == 200 and ack["status"] == "acknowledged")  # type: ignore[index]
        status, detalle = get(f"/alerts/{alert_id}")
        check(
            "GET /alerts/{id} registra entrega",
            status == 200 and len(detalle["deliveries"]) == 1,  # type: ignore[index]
        )

    status, simulada = post("/alerts/simulate", {"severity": "critical", "rule_code": "SIMULACION"})
    check(
        "POST /alerts/simulate marca simulated",
        status == 200 and simulada["simulated"] == 1,  # type: ignore[index]
    )

    status, monitor = get("/monitor.json")
    check(
        "GET /monitor.json trae pipeline, modelo y alertas",
        status == 200
        and monitor["pipeline"]["fact_rows"] > 0  # type: ignore[index]
        and "estado" in monitor["modelo"]  # type: ignore[index]
        and monitor["notificaciones"]["total"] >= primeras_nuevas,  # type: ignore[index]
    )

    status, html = get("/monitor")
    check("GET /monitor devuelve HTML", status == 200 and "Ultimas alertas" in html)  # type: ignore[operator]

    print("")
    print("RESULTADO:", "OK" if not fallos else f"{fallos} verificaciones fallaron")
    return 0 if not fallos else 1


if __name__ == "__main__":
    raise SystemExit(main())
