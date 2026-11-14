"""Catalogo de consultas aprobadas y su ejecucion contra core-api.

No hay texto a SQL: cada intencion mapea a un endpoint fijo y a parametros
validados. Toda cifra de la respuesta proviene de la API y se declara la fuente.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .api_client import ApiError, CoreApi
from .intents import Interpretacion, periodo_legible

ALLOWED_PARAMS = ("desde", "hasta", "local", "seccion", "producto")


def _params(filtros: dict[str, str]) -> dict[str, str]:
    """Solo deja pasar parametros que core-api acepta."""
    return {k: v for k, v in filtros.items() if k in ALLOWED_PARAMS}


def _money(valor: float) -> str:
    return f"S/ {valor:,.2f}"


def _entero(valor: float) -> str:
    return f"{valor:,.0f}"


def _fuente(endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "servicio": "core-api",
        "endpoint": endpoint,
        "data_updated_at": payload.get("data_updated_at"),
    }


@dataclass
class Respuesta:
    intent: str
    respuesta: str
    datos: dict[str, Any] = field(default_factory=dict)
    fuentes: list[dict[str, Any]] = field(default_factory=list)
    grounded: bool = True

    def as_dict(self, pregunta: str, interpretacion: Interpretacion) -> dict[str, Any]:
        return {
            "pregunta": pregunta,
            "intent": self.intent,
            "respuesta": self.respuesta,
            "datos": self.datos,
            "fuentes": self.fuentes,
            "grounded": self.grounded,
            "interpretacion": interpretacion.detalle,
        }


def _kpis(api: CoreApi, filtros: dict[str, str]) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    payload = api.kpis(_params(filtros))
    return payload, {k["code"]: k for k in payload["kpis"]}


def _ventas_totales(api: CoreApi, interp: Interpretacion) -> Respuesta:
    payload, kpis = _kpis(api, interp.filtros)
    ventas = kpis["ventas"]["value"]
    return Respuesta(
        intent="ventas_totales",
        respuesta=(
            f"Las ventas {periodo_legible(interp.filtros)} suman {_money(ventas)}, "
            f"en {_entero(kpis['lineas']['value'])} lineas y "
            f"{_entero(kpis['facturas']['value'])} facturas."
        ),
        datos={"ventas": ventas, **{k: kpis[k]["value"] for k in ("lineas", "facturas", "unidades")}},
        fuentes=[_fuente("/api/v1/kpis", payload)],
    )


def _facturas(api: CoreApi, interp: Interpretacion) -> Respuesta:
    payload, kpis = _kpis(api, interp.filtros)
    facturas = kpis["facturas"]["value"]
    return Respuesta(
        intent="facturas",
        respuesta=(
            f"Hay {_entero(facturas)} facturas {periodo_legible(interp.filtros)}, "
            f"por un total de {_money(kpis['ventas']['value'])}."
        ),
        datos={"facturas": facturas, "ventas": kpis["ventas"]["value"]},
        fuentes=[_fuente("/api/v1/kpis", payload)],
    )


def _ticket_promedio(api: CoreApi, interp: Interpretacion) -> Respuesta:
    payload, kpis = _kpis(api, interp.filtros)
    ticket = kpis["ticket_promedio"]["value"]
    if kpis["facturas"]["value"] == 0:
        return Respuesta(
            intent="ticket_promedio",
            respuesta=f"No hay facturas {periodo_legible(interp.filtros)}; el ticket promedio no es calculable.",
            datos={"ticket_promedio": 0.0, "facturas": 0},
            fuentes=[_fuente("/api/v1/kpis", payload)],
        )
    return Respuesta(
        intent="ticket_promedio",
        respuesta=(
            f"El ticket promedio {periodo_legible(interp.filtros)} es {_money(ticket)} "
            f"sobre {_entero(kpis['facturas']['value'])} facturas."
        ),
        datos={"ticket_promedio": ticket, "facturas": kpis["facturas"]["value"]},
        fuentes=[_fuente("/api/v1/kpis", payload)],
    )


def _unidades(api: CoreApi, interp: Interpretacion) -> Respuesta:
    payload, kpis = _kpis(api, interp.filtros)
    unidades = kpis["unidades"]["value"]
    return Respuesta(
        intent="unidades",
        respuesta=(
            f"Se vendieron {_entero(unidades)} unidades {periodo_legible(interp.filtros)}, "
            f"en {_entero(kpis['productos']['value'])} productos distintos."
        ),
        datos={"unidades": unidades, "productos": kpis["productos"]["value"]},
        fuentes=[_fuente("/api/v1/kpis", payload)],
    )


def _top_productos(api: CoreApi, interp: Interpretacion) -> Respuesta:
    filtros = {**_params(interp.filtros), "dimension": "producto", "limit": "5"}
    payload = api.agrupado(filtros)
    grupos = payload["grupos"]
    if not grupos:
        return Respuesta(
            intent="top_productos",
            respuesta=f"No hay ventas por producto {periodo_legible(interp.filtros)}.",
            datos={"grupos": []},
            fuentes=[_fuente("/api/v1/agrupado", payload)],
        )
    detalle = "; ".join(f"{g['valor']} {_money(g['ventas'])}" for g in grupos)
    return Respuesta(
        intent="top_productos",
        respuesta=f"Productos mas vendidos {periodo_legible(interp.filtros)}: {detalle}.",
        datos={"grupos": grupos, "total_grupos": payload["total_grupos"]},
        fuentes=[_fuente("/api/v1/agrupado?dimension=producto", payload)],
    )


def _por_dimension(dimension: str, etiqueta: str) -> Callable[[CoreApi, Interpretacion], Respuesta]:
    def handler(api: CoreApi, interp: Interpretacion) -> Respuesta:
        filtros = {**_params(interp.filtros), "dimension": dimension, "limit": "10"}
        payload = api.agrupado(filtros)
        grupos = payload["grupos"]
        if not grupos:
            return Respuesta(
                intent=f"ventas_por_{dimension}",
                respuesta=f"No hay ventas por {etiqueta} {periodo_legible(interp.filtros)}.",
                datos={"grupos": []},
                fuentes=[_fuente(f"/api/v1/agrupado?dimension={dimension}", payload)],
            )
        detalle = "; ".join(f"{g['valor']} {_money(g['ventas'])}" for g in grupos)
        return Respuesta(
            intent=f"ventas_por_{dimension}",
            respuesta=f"Ventas por {etiqueta} {periodo_legible(interp.filtros)}: {detalle}.",
            datos={"grupos": grupos, "total_grupos": payload["total_grupos"]},
            fuentes=[_fuente(f"/api/v1/agrupado?dimension={dimension}", payload)],
        )

    return handler


def _ventas_por_producto(api: CoreApi, interp: Interpretacion) -> Respuesta:
    producto = interp.filtros.get("producto")
    if not producto:
        return Respuesta(
            intent="no_data",
            respuesta="No pude identificar el producto. Probar con el nombre exacto del catalogo.",
            grounded=False,
        )
    payload, kpis = _kpis(api, interp.filtros)
    ventas = kpis["ventas"]["value"]
    return Respuesta(
        intent="ventas_por_producto",
        respuesta=(
            f"{producto} vendio {_money(ventas)} {periodo_legible(interp.filtros)}, "
            f"en {_entero(kpis['unidades']['value'])} unidades y "
            f"{_entero(kpis['lineas']['value'])} lineas."
        ),
        datos={"producto": producto, "ventas": ventas, "unidades": kpis["unidades"]["value"]},
        fuentes=[_fuente("/api/v1/kpis", payload)],
    )


def _tendencia(api: CoreApi, interp: Interpretacion) -> Respuesta:
    payload = api.tendencias(_params(interp.filtros), "mes")
    serie = payload["serie"]
    if not serie:
        return Respuesta(
            intent="tendencia",
            respuesta=f"No hay ventas registradas {periodo_legible(interp.filtros)}.",
            datos={"serie": []},
            fuentes=[_fuente("/api/v1/tendencias?granularidad=mes", payload)],
        )
    detalle = "; ".join(f"{p['periodo']} {_money(p['ventas'])}" for p in serie)
    return Respuesta(
        intent="tendencia",
        respuesta=f"Ventas por mes {periodo_legible(interp.filtros)}: {detalle}.",
        datos={"serie": serie, "comparacion": payload.get("comparacion", {})},
        fuentes=[_fuente("/api/v1/tendencias?granularidad=mes", payload)],
    )


def _comparacion(api: CoreApi, interp: Interpretacion) -> Respuesta:
    desde = interp.filtros.get("desde")
    hasta = interp.filtros.get("hasta")
    if not desde or not hasta:
        return Respuesta(
            intent="no_data",
            respuesta="Para comparar necesito dos anios (por ejemplo: 2007 y 2008).",
            grounded=False,
        )
    anio_a = desde[:4]
    anio_b = hasta[:4]
    base = _params(interp.filtros)
    base.pop("desde", None)
    base.pop("hasta", None)

    payload_a = api.kpis({**base, "desde": f"{anio_a}-01-01", "hasta": f"{anio_a}-12-31"})
    payload_b = api.kpis({**base, "desde": f"{anio_b}-01-01", "hasta": f"{anio_b}-12-31"})
    ventas_a = next(k["value"] for k in payload_a["kpis"] if k["code"] == "ventas")
    ventas_b = next(k["value"] for k in payload_b["kpis"] if k["code"] == "ventas")

    variacion = None
    if ventas_a:
        variacion = round((ventas_b - ventas_a) / ventas_a * 100, 2)
    if variacion is None:
        texto_var = "La variacion no es calculable porque el anio base no tiene ventas."
    else:
        texto_var = f"La variacion es {variacion:+.2f}%."

    return Respuesta(
        intent="comparacion",
        respuesta=(
            f"Ventas {anio_a}: {_money(ventas_a)}. Ventas {anio_b}: {_money(ventas_b)}. "
            f"{texto_var}"
        ),
        datos={
            "anio_a": anio_a,
            "ventas_a": ventas_a,
            "anio_b": anio_b,
            "ventas_b": ventas_b,
            "variacion_pct": variacion,
        },
        fuentes=[
            _fuente(f"/api/v1/kpis?desde={anio_a}-01-01&hasta={anio_a}-12-31", payload_a),
            _fuente(f"/api/v1/kpis?desde={anio_b}-01-01&hasta={anio_b}-12-31", payload_b),
        ],
    )


def _no_data(api: CoreApi, interp: Interpretacion) -> Respuesta:
    return Respuesta(
        intent="no_data",
        respuesta=(
            "No puedo responder esa pregunta con los datos de ventas de la plataforma. "
            "Puedo consultar ventas, facturas, ticket promedio, unidades, productos, "
            "locales, secciones, tendencias y comparaciones entre anios."
        ),
        datos={},
        fuentes=[],
        grounded=False,
    )


HANDLERS: dict[str, Callable[[CoreApi, Interpretacion], Respuesta]] = {
    "ventas_totales": _ventas_totales,
    "facturas": _facturas,
    "ticket_promedio": _ticket_promedio,
    "unidades": _unidades,
    "top_productos": _top_productos,
    "ventas_por_local": _por_dimension("local", "local"),
    "ventas_por_seccion": _por_dimension("seccion", "seccion"),
    "ventas_por_producto": _ventas_por_producto,
    "tendencia": _tendencia,
    "comparacion": _comparacion,
    "no_data": _no_data,
}

def responder(api: CoreApi, interp: Interpretacion) -> Respuesta:
    handler = HANDLERS.get(interp.intent)
    if handler is None:
        return _no_data(api, interp)
    try:
        return handler(api, interp)
    except ApiError as exc:
        return Respuesta(
            intent=interp.intent,
            respuesta=f"No pude obtener datos verificables: {exc}",
            datos={},
            fuentes=[],
            grounded=False,
        )
