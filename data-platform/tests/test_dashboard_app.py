"""Prueba de render del dashboard con Streamlit AppTest (T10).

Ejecuta `services/dashboard/app.py` sin navegador y verifica que:
- no haya excepciones,
- se rendericen KPIs, titulo y tabla de detalle,
- no aparezcan mensajes de error.

Requiere `core-api` corriendo (por defecto en http://localhost:8000) y las
dependencias del dashboard instaladas:

    python tests/test_dashboard_app.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "services" / "dashboard" / "app.py"
CHAT_APP = APP.parent / "pages" / "1_Asistente.py"


def _check_ok() -> int:
    at = AppTest.from_file(str(APP), default_timeout=45).run()

    print(f"excepciones      : {len(at.exception)}")
    print(f"mensajes error   : {len(at.error)}")
    print(f"tarjetas (metric): {len(at.metric)}")
    print(f"tablas           : {len(at.dataframe)}")
    print(f"titulo           : {[t.value for t in at.title]}")
    print(f"subtitulos       : {[h.value for h in at.subheader]}")

    for exc in at.exception:
        print(f"  EXCEPCION: {exc.value}")
    for err in at.error:
        print(f"  ERROR: {err.value}")

    fallos = 0
    if at.exception:
        fallos += 1
    if at.error:
        fallos += 1
    if len(at.metric) < 4:
        fallos += 1
        print("  FALLO: se esperaban al menos 4 tarjetas de KPI")
    if not at.title:
        fallos += 1
        print("  FALLO: no se renderizo el titulo")
    if "Productos con más ventas" in [h.value for h in at.subheader]:
        fallos += 1
        print("  FALLO: el grafico de productos solicitado aun aparece")
    return fallos


def _check_api_caida() -> int:
    """Con la API inalcanzable el dashboard debe avisar, no romperse."""
    os.environ["CORE_API_URL"] = "http://localhost:9"
    try:
        at = AppTest.from_file(str(APP), default_timeout=45).run()
        print("")
        print("API caida        :")
        print(f"  excepciones    : {len(at.exception)}")
        print(f"  errores        : {[e.value[:60] for e in at.error]}")
        fallos = 0
        if at.exception:
            fallos += 1
            print("  FALLO: el dashboard no debe lanzar excepcion")
        if not at.error:
            fallos += 1
            print("  FALLO: se esperaba un mensaje de error visible")
        return fallos
    finally:
        os.environ.pop("CORE_API_URL", None)


def _check_chat_page() -> int:
    """La pagina conversacional debe renderizar sin llamar a GenAI."""
    previous_directory = Path.cwd()
    previous_path = sys.path.copy()
    try:
        os.chdir(APP.parent)
        sys.path.insert(0, str(APP.parent))
        at = AppTest.from_file(str(CHAT_APP), default_timeout=45).run()
    finally:
        os.chdir(previous_directory)
        sys.path[:] = previous_path

    print("")
    print("Pagina de chat:")
    print(f"  excepciones    : {len(at.exception)}")
    print(f"  errores        : {len(at.error)}")
    print(f"  titulo         : {[title.value for title in at.title]}")
    print(f"  campos de chat : {len(at.chat_input)}")
    print(f"  modos de chat  : {len(at.radio)}")
    if at.exception:
        for exc in at.exception:
            print(f"  EXCEPCION: {exc.value}")
    return int(bool(at.exception or at.error or not at.chat_input or not at.radio))


def main() -> int:
    fallos = _check_ok() + _check_api_caida() + _check_chat_page()

    print("")
    print("RESULTADO:", "OK" if fallos == 0 else f"{fallos} FALLOS")
    return 0 if fallos == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
