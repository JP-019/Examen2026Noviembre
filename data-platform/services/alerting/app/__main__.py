"""CLI del motor de alertas (T13).

Uso (desde services/alerting, con core-api y ml corriendo):
    python -m app evaluate
    python -m app rules
    python -m app alerts
    python -m app simulate --severity warning
    python -m app monitor
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid

from . import monitor, rules
from .clients import CoreApi, MlApi
from .store import AlertStore


def _print(data: object) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str))


def command_evaluate() -> int:
    core, ml = CoreApi(), MlApi()
    contexto = rules.construir_contexto(core, ml)
    store = AlertStore()
    disparadas = rules.evaluar(contexto)

    detalle = []
    nuevas = duplicadas = 0
    for alerta in disparadas:
        alert_id, creada = store.add(alerta)
        if creada:
            store.deliver(alert_id, "dashboard", "delivered", "Publicada en /monitor")
            nuevas += 1
        else:
            duplicadas += 1
        detalle.append(
            {
                "alert_id": alert_id,
                "rule_code": alerta.rule_code,
                "severity": alerta.severity,
                "observed_value": alerta.observed_value,
                "threshold": alerta.threshold,
                "nueva": creada,
            }
        )

    _print(
        {
            "periodo": contexto.periodo,
            "reglas_evaluadas": len(rules.REGLAS),
            "disparadas": len(disparadas),
            "nuevas": nuevas,
            "duplicadas": duplicadas,
            "detalle": detalle,
        }
    )
    return 0


def command_rules() -> int:
    from dataclasses import asdict

    _print(
        {
            "total": len(rules.REGLAS),
            "umbrales": asdict(rules.Umbrales()),
            "reglas": [
                {
                    "code": r.code,
                    "tipo": r.alert_type,
                    "severidad": r.severity,
                    "indicador": r.indicator,
                    "descripcion": r.descripcion,
                }
                for r in rules.REGLAS
            ],
        }
    )
    return 0


def command_alerts(limit: int) -> int:
    alertas = AlertStore().list(limit=limit)
    _print({"total": len(alertas), "alertas": alertas})
    return 0


def command_simulate(severity: str) -> int:
    store = AlertStore()
    alerta = rules.Alerta(
        rule_code="SIMULACION",
        alert_type="simulacion",
        severity=severity,
        entity="demo",
        indicator="ventas_totales",
        observed_value=500.0,
        threshold=1000.0,
        period="demo",
        source="CLI python -m app simulate",
        explanation="Evento simulado para probar el canal de notificaciones.",
        action="Verificar /monitor y reconocer la alerta.",
        event_key=f"SIM|{uuid.uuid4()}",
        simulated=True,
    )
    alert_id, _ = store.add(alerta)
    store.deliver(alert_id, "dashboard", "delivered", "Alerta simulada visible en /monitor")
    _print(store.get(alert_id) or {})
    return 0


def command_monitor() -> int:
    _print(monitor.snapshot(AlertStore(), CoreApi(), MlApi()))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="alerting", description="Motor de alertas")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("evaluate", help="Evalua reglas y registra alertas nuevas")
    sub.add_parser("rules", help="Reglas y umbrales vigentes")
    alerts = sub.add_parser("alerts", help="Ultimas alertas registradas")
    alerts.add_argument("--limit", type=int, default=20)
    simulate = sub.add_parser("simulate", help="Genera una alerta simulada identificada")
    simulate.add_argument("--severity", default="warning", choices=["info", "warning", "critical"])
    sub.add_parser("monitor", help="Snapshot de monitoreo en JSON")

    args = parser.parse_args(argv)
    if args.command == "evaluate":
        return command_evaluate()
    if args.command == "rules":
        return command_rules()
    if args.command == "alerts":
        return command_alerts(args.limit)
    if args.command == "simulate":
        return command_simulate(args.severity)
    if args.command == "monitor":
        return command_monitor()
    return 1


if __name__ == "__main__":
    sys.exit(main())
