"""Pruebas de reglas, anti-duplicado y registro de entregas del motor de alertas (T13).

No requieren servicios levantados: evaluan las reglas puras y el `AlertStore`
sobre un SQLite temporal. Las metricas reales las mide el motor desde core-api.

Uso:
    python tests/test_alerting_rules.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services" / "alerting"))

from app.rules import Alerta, Contexto, Umbrales, evaluar  # noqa: E402
from app.store import AlertStore  # noqa: E402


def contexto_real() -> Contexto:
    """Valores medidos en la fuente actual (un mes, 4 facturas, S/ 696.40)."""
    return Contexto(
        ventas=696.40,
        facturas=4,
        ticket=174.10,
        variacion_pct=None,
        periodo="2008-08-01..2008-08-31",
        data_updated_at="2026-11-14T02:47:00",
        ml_status="insufficient_data",
        ml_periodos=1,
        ml_message="Se necesitan al menos 8 meses; hay 1.",
        rechazos_abiertos=0,
        ultimo_etl_status="SUCCESS",
    )


def contexto_sano() -> Contexto:
    return Contexto(
        ventas=5000.0,
        facturas=20,
        ticket=250.0,
        variacion_pct=5.0,
        periodo="2024-06-01..2024-06-30",
        data_updated_at="2026-11-14T03:00:00",
        ml_status="trained",
        ml_mae=100.0,
        ml_periodos=24,
        rechazos_abiertos=2,
        ultimo_etl_status="SUCCESS",
    )


def contexto_critico() -> Contexto:
    return Contexto(
        ventas=800.0,
        facturas=10,
        ticket=80.0,
        variacion_pct=-22.5,
        periodo="2024-07-01..2024-07-31",
        data_updated_at="2026-11-14T04:00:00",
        ml_status="trained",
        ml_mae=900.0,
        ml_periodos=24,
        rechazos_abiertos=15,
        ultimo_etl_status="SUCCESS",
    )


def reglas_disparadas(ctx: Contexto) -> set[str]:
    return {a.rule_code for a in evaluar(ctx, Umbrales())}


def main() -> int:
    fallos = 0

    def check(nombre: str, condicion: bool, detalle: str = "") -> None:
        nonlocal fallos
        estado = "OK" if condicion else "FALLO"
        print(f"  {nombre:<52} {estado}{'' if condicion else ' -> ' + detalle}")
        if not condicion:
            fallos += 1

    print("Caso 1: datos reales (ventas bajas, ticket bajo, modelo sin entrenar)")
    disparadas = reglas_disparadas(contexto_real())
    print(f"  reglas disparadas: {sorted(disparadas)}")
    check("VENTAS_BAJAS se dispara", "VENTAS_BAJAS" in disparadas)
    check("TICKET_BAJO se dispara", "TICKET_BAJO" in disparadas)
    check("MODELO_SIN_ENTRENAR se dispara", "MODELO_SIN_ENTRENAR" in disparadas)
    check("CAIDA_VENTAS no se dispara sin periodo previo", "CAIDA_VENTAS" not in disparadas)
    check("MAE_ALTO no se dispara sin modelo", "MAE_ALTO" not in disparadas)
    check("RECHAZOS_ALTOS no se dispara con 0 rechazos", "RECHAZOS_ALTOS" not in disparadas)
    check("son exactamente 3 alertas", len(disparadas) == 3, str(disparadas))

    print("\nCaso 2: contexto sano (no debe disparar ninguna regla)")
    disparadas = reglas_disparadas(contexto_sano())
    print(f"  reglas disparadas: {sorted(disparadas)}")
    check("ninguna regla se dispara", disparadas == set(), str(disparadas))

    print("\nCaso 3: contexto critico (caida, MAE alto y rechazos)")
    disparadas = reglas_disparadas(contexto_critico())
    print(f"  reglas disparadas: {sorted(disparadas)}")
    check("CAIDA_VENTAS se dispara", "CAIDA_VENTAS" in disparadas)
    check("MAE_ALTO se dispara", "MAE_ALTO" in disparadas)
    check("RECHAZOS_ALTOS se dispara", "RECHAZOS_ALTOS" in disparadas)
    severidades = {a.rule_code: a.severity for a in evaluar(contexto_critico(), Umbrales())}
    check("CAIDA_VENTAS es critical", severidades.get("CAIDA_VENTAS") == "critical")
    check("RECHAZOS_ALTOS es critical", severidades.get("RECHAZOS_ALTOS") == "critical")

    print("\nCaso 4: contenido minimo de una alerta")
    alerta = next(a for a in evaluar(contexto_real(), Umbrales()) if a.rule_code == "VENTAS_BAJAS")
    for campo in (
        "rule_code",
        "alert_type",
        "severity",
        "indicator",
        "observed_value",
        "threshold",
        "period",
        "source",
        "explanation",
        "action",
        "event_key",
    ):
        check(f"campo {campo} presente", getattr(alerta, campo) not in (None, "", 0.0))
    check("umbral de ventas es 1000", alerta.threshold == 1000.0)
    check("valor observado es 696.40", alerta.observed_value == 696.40)

    print("\nCaso 5: anti-duplicado en SQLite temporal")
    with tempfile.TemporaryDirectory() as tmp:
        store = AlertStore(Path(tmp) / "alerts.db")

        id_1, creada_1 = store.add(alerta)
        entregada = store.deliver(id_1, "dashboard", "delivered", "Publicada en /monitor")
        id_2, creada_2 = store.add(alerta)
        store.deliver(id_2, "dashboard", "delivered", "Publicada en /monitor")

        check("primer registro es nuevo", creada_1 is True)
        check("segundo registro es duplicado", creada_2 is False)
        check("mismo alert_id", id_1 == id_2, f"{id_1} != {id_2}")
        check("listado tiene 1 alerta", len(store.list()) == 1)
        check("entrega registrada como delivered", entregada["status"] == "delivered")
        check("entrega no se duplica", len(store.get(id_1)["deliveries"]) == 1)

        print("\nCaso 6: reconocimiento y estadisticas")
        ack = store.acknowledge(id_1)
        check("estado pasa a acknowledged", ack and ack["status"] == "acknowledged")
        check("tiene fecha de reconocimiento", bool(ack and ack["acknowledged_at"]))
        stats = store.stats()
        print(f"  stats: {stats}")
        check("total = 1", stats["total"] == 1)
        check("entregadas = 1", stats["entregadas"] == 1)
        check("por estado acknowledged = 1", stats["por_estado"].get("acknowledged") == 1)

    print("\nCaso 7: alerta simulada identificada")
    with tempfile.TemporaryDirectory() as tmp:
        store = AlertStore(Path(tmp) / "alerts.db")
        simulada = Alerta(
            rule_code="SIMULACION",
            alert_type="simulacion",
            severity="warning",
            entity="demo",
            indicator="ventas_totales",
            observed_value=500.0,
            threshold=1000.0,
            period="demo",
            source="POST /alerts/simulate",
            explanation="Evento simulado para probar el canal.",
            action="Verificar /monitor y reconocer la alerta.",
            event_key="SIM|prueba-1",
            simulated=True,
        )
        sid, creada = store.add(simulada)
        store.deliver(sid, "dashboard", "delivered", "Alerta simulada visible en /monitor")
        stats = store.stats()
        check("simulada registrada", creada is True)
        check("marcada como simulada en la fila", store.get(sid)["simulated"] == 1)
        check("stats.simuladas = 1", stats["simuladas"] == 1)
        check(
            "se excluye con incluir_simuladas=False",
            store.list(include_simulated=False) == [],
        )

    print("")
    if fallos:
        print(f"RESULTADO: {fallos} verificaciones fallaron")
        return 1
    print("RESULTADO: OK - reglas, deduplicacion y entregas verificadas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
