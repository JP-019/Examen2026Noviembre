"""Interpretacion determinista de preguntas.

No hay SQL libre ni generacion de cifras: la pregunta se clasifica en una
consulta aprobada y los parametros se extraen del texto con reglas explicitas.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date

from .api_client import CoreApi


def normalizar(texto: str) -> str:
    sin_acentos = "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"\s+", " ", sin_acentos.lower()).strip()


@dataclass
class Interpretacion:
    intent: str
    filtros: dict[str, str] = field(default_factory=dict)
    detalle: str = ""


KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("comparacion", ("comparar", "comparacion", "versus", " vs ", "variacion", "contra")),
    ("tendencia", ("tendencia", "evolucion", "por mes", "mensual", "serie")),
    ("ticket_promedio", ("ticket", "promedio por factura", "gasto promedio")),
    ("facturas", ("factura", "facturas", "boletas")),
    ("unidades", ("unidades", "cantidad vendida", "volumen")),
    ("top_productos", ("ranking", "top", "mas vendido", "mas vendidos", "mejores productos")),
    ("ventas_por_local", ("local", "locales", "tienda", "tiendas", "sede", "sucursal")),
    ("ventas_por_seccion", ("seccion", "secciones", "rubro", "categoria")),
    ("ventas_por_producto", ("producto", "productos")),
    ("ventas_totales", ("cuanto vendi", "cuanto vendimos", "ventas totales", "total de ventas", "ventas")),
]

FUERA_DE_ALCANCE = (
    "clima",
    "temperatura",
    "presidente",
    "eleccion",
    "chiste",
    "poema",
    "traduce",
    "receta",
    "futbol",
    "partido",
    "accion de la bolsa",
    "dolar",
)


def _anios(texto: str) -> list[int]:
    return [int(a) for a in re.findall(r"\b(19\d{2}|20\d{2}|21\d{2})\b", texto) if 2000 <= int(a) <= 2100]


def _menciona(texto: str, valores: list[str]) -> list[str]:
    """Busca nombres conocidos (local/producto/seccion) dentro de la pregunta."""
    encontrados = []
    for valor in valores:
        if normalizar(valor) in texto:
            encontrados.append(valor)
    return encontrados


def interpretar(pregunta: str, api: CoreApi) -> Interpretacion:
    texto = normalizar(pregunta)
    # Rellena espacios para detectar " vs " al inicio/fin.
    acolchado = f" {texto} "

    if not texto:
        return Interpretacion("no_data", detalle="La pregunta esta vacia.")

    if any(palabra in texto for palabra in FUERA_DE_ALCANCE):
        return Interpretacion(
            "no_data",
            detalle="La pregunta no corresponde al proceso de ventas de la plataforma.",
        )

    intent = "no_data"
    for nombre, claves in KEYWORDS:
        if any(clave in acolchado for clave in claves):
            intent = nombre
            break

    filtros: dict[str, str] = {}
    detalle = ""

    try:
        opciones = api.filtros()
    except Exception:  # noqa: BLE001 - sin catalogo no se pueden extraer entidades
        opciones = {"locales": [], "secciones": [], "productos": []}

    locales = _menciona(texto, opciones.get("locales", []))
    productos = _menciona(texto, opciones.get("productos", []))
    secciones = _menciona(texto, opciones.get("secciones", []))

    anios = _anios(texto)

    if intent == "ventas_por_producto" or productos:
        if productos:
            filtros["producto"] = productos[0]
            detalle = f"producto={productos[0]}"
            if intent in {"no_data", "ventas_totales"}:
                intent = "ventas_por_producto"
        elif intent == "ventas_por_producto":
            # Sin producto identificable no se responde con un total generico.
            return Interpretacion(
                "no_data",
                detalle="No pude identificar el producto. Probar con el nombre exacto del catalogo.",
            )

    if locales:
        filtros["local"] = locales[0]
        detalle = f"local={locales[0]}"
    if secciones:
        filtros["seccion"] = secciones[0]
        detalle = f"seccion={secciones[0]}"

    if intent == "comparacion":
        if len(anios) < 2:
            return Interpretacion(
                "no_data",
                detalle="Para comparar necesito dos anios (por ejemplo: 2007 y 2008).",
            )
        filtros["desde"] = f"{min(anios)}-01-01"
        filtros["hasta"] = f"{max(anios)}-12-31"
        filtros["anio_a"] = str(min(anios))
        filtros["anio_b"] = str(max(anios))
        detalle = f"{min(anios)} vs {max(anios)}"
        return Interpretacion(intent, filtros, detalle)

    if len(anios) == 1:
        filtros["desde"] = f"{anios[0]}-01-01"
        filtros["hasta"] = f"{anios[0]}-12-31"
        detalle = f"anio={anios[0]}"
    elif len(anios) >= 2:
        filtros["desde"] = f"{min(anios)}-01-01"
        filtros["hasta"] = f"{max(anios)}-12-31"
        detalle = f"anios={min(anios)}-{max(anios)}"

    if intent == "no_data":
        return Interpretacion(
            "no_data",
            detalle=(
                "No encontre una consulta aprobada para esa pregunta. "
                "Puedo responder sobre ventas, facturas, ticket, productos, locales, "
                "secciones y tendencias."
            ),
        )

    return Interpretacion(intent, filtros, detalle)


def periodo_legible(filtros: dict[str, str]) -> str:
    desde = filtros.get("desde")
    hasta = filtros.get("hasta")
    if desde and hasta:
        if desde.endswith("-01-01") and hasta.endswith("-12-31") and desde[:4] == hasta[:4]:
            return f"del anio {desde[:4]}"
        return f"del {desde} al {hasta}"
    return "del periodo completo"


def hoy() -> str:
    return date.today().isoformat()
