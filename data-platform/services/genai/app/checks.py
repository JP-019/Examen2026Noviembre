"""Las 10 pruebas documentadas del asistente (T12).

Cada prueba envia una pregunta en lenguaje natural, verifica que se clasifique en
la intencion esperada y que la respuesta este respaldada por datos de core-api.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .api_client import CoreApi
from .intents import interpretar
from .queries import responder


def _ok(condicion: bool, mensaje: str) -> str | None:
    return None if condicion else mensaje


def _grupos_no_vacios(r: dict[str, Any]) -> str | None:
    grupos = r["datos"].get("grupos") or []
    return _ok(bool(grupos) and grupos[0]["ventas"] > 0, "no hay grupos con ventas")


@dataclass(frozen=True)
class Case:
    id: str
    pregunta: str
    intent: str
    grounded: bool
    validar: Callable[[dict[str, Any]], str | None]


CASES: list[Case] = [
    Case(
        "T12-01",
        "¿Cuánto vendimos en total?",
        "ventas_totales",
        True,
        lambda r: _ok(
            r["datos"].get("ventas", 0) > 0 and "S/" in r["respuesta"],
            "la respuesta no trae un importe de ventas",
        ),
    ),
    Case(
        "T12-02",
        "¿Cuántas facturas hay?",
        "facturas",
        True,
        lambda r: _ok(r["datos"].get("facturas", 0) > 0, "no se informaron facturas"),
    ),
    Case(
        "T12-03",
        "¿Cuál es el ticket promedio?",
        "ticket_promedio",
        True,
        lambda r: _ok(r["datos"].get("ticket_promedio", 0) > 0, "ticket promedio no calculado"),
    ),
    Case(
        "T12-04",
        "Ranking de productos más vendidos",
        "top_productos",
        True,
        _grupos_no_vacios,
    ),
    Case(
        "T12-05",
        "Ventas por local",
        "ventas_por_local",
        True,
        _grupos_no_vacios,
    ),
    Case(
        "T12-06",
        "Ventas por sección",
        "ventas_por_seccion",
        True,
        _grupos_no_vacios,
    ),
    Case(
        "T12-07",
        "¿Cuánto vendió Mini Lorito?",
        "ventas_por_producto",
        True,
        lambda r: _ok(
            r["datos"].get("producto") == "Mini Lorito" and r["datos"].get("ventas", 0) > 0,
            "no se identifico el producto del catalogo o no hay ventas",
        ),
    ),
    Case(
        "T12-08",
        "Tendencia mensual de ventas",
        "tendencia",
        True,
        lambda r: _ok(bool(r["datos"].get("serie")), "la serie mensual vino vacia"),
    ),
    Case(
        "T12-09",
        "Comparar 2007 vs 2008",
        "comparacion",
        True,
        lambda r: _ok(
            len(r["fuentes"]) == 2 and "ventas_b" in r["datos"],
            "la comparacion no consulto los dos periodos",
        ),
    ),
    Case(
        "T12-10",
        "¿Cómo va el clima mañana?",
        "no_data",
        False,
        lambda r: _ok(
            r["fuentes"] == [] and "No puedo responder" in r["respuesta"],
            "una pregunta fuera de alcance no debe devolver datos",
        ),
    ),
]


def run(api: CoreApi) -> list[dict[str, Any]]:
    resultados: list[dict[str, Any]] = []
    for case in CASES:
        interpretacion = interpretar(case.pregunta, api)
        respuesta = responder(api, interpretacion)
        cuerpo = respuesta.as_dict(case.pregunta, interpretacion)

        motivos: list[str] = []
        if interpretacion.intent != case.intent:
            motivos.append(f"intent {interpretacion.intent} != {case.intent}")
        if respuesta.grounded != case.grounded:
            motivos.append(f"grounded {respuesta.grounded} != {case.grounded}")
        motivo = case.validar(cuerpo)
        if motivo:
            motivos.append(motivo)

        resultados.append(
            {
                "id": case.id,
                "pregunta": case.pregunta,
                "intent_esperado": case.intent,
                "intent_obtenido": interpretacion.intent,
                "grounded": respuesta.grounded,
                "passed": not motivos,
                "detalle": "OK" if not motivos else "; ".join(motivos),
            }
        )
    return resultados
