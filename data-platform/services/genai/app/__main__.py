"""CLI del asistente (T12).

Uso (desde services/genai, con core-api corriendo):
    python -m app ask "cuanto vendimos en total"
    python -m app queries
    python -m app test
"""

from __future__ import annotations

import argparse
import json
import sys

from . import checks, queries
from .api_client import CoreApi
from .intents import interpretar
from .query_catalog import QUERY_CATALOG


def command_ask(pregunta: str) -> int:
    api = CoreApi()
    interpretacion = interpretar(pregunta, api)
    respuesta = queries.responder(api, interpretacion)
    print(json.dumps(respuesta.as_dict(pregunta, interpretacion), indent=2, ensure_ascii=False))
    return 0 if respuesta.grounded else 3


def command_queries() -> int:
    for item in QUERY_CATALOG:
        print(f"{item['intent']:<20} {item['descripcion']}")
        print(f"{'':<20} endpoint: {item['endpoint']}")
        print(f"{'':<20} ejemplo : {item['ejemplo']}")
    return 0


def command_test() -> int:
    resultados = checks.run(CoreApi())
    print(f"{'id':<8} {'intent':<20} {'obtenido':<20} resultado")
    for r in resultados:
        estado = "OK" if r["passed"] else f"FALLO ({r['detalle']})"
        print(f"{r['id']:<8} {r['intent_esperado']:<20} {r['intent_obtenido']:<20} {estado}")
    passed = sum(1 for r in resultados if r["passed"])
    print("")
    print(f"RESULTADO: {passed}/{len(resultados)} pruebas OK")
    return 0 if passed == len(resultados) else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="genai", description="Asistente de ventas")
    sub = parser.add_subparsers(dest="command", required=True)
    ask = sub.add_parser("ask", help="Pregunta en lenguaje natural")
    ask.add_argument("pregunta")
    sub.add_parser("queries", help="Catalogo de consultas aprobadas")
    sub.add_parser("test", help="Ejecuta las 10 pruebas documentadas")

    args = parser.parse_args(argv)
    if args.command == "ask":
        return command_ask(args.pregunta)
    if args.command == "queries":
        return command_queries()
    if args.command == "test":
        return command_test()
    return 1


if __name__ == "__main__":
    sys.exit(main())
