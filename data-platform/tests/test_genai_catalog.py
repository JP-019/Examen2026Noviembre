"""Comprueba que cada consulta publicada tenga un manejador ejecutable."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICE_PATH = str(ROOT / "services" / "genai")
sys.path.insert(0, SERVICE_PATH)
try:
    QUERY_CATALOG = importlib.import_module("app.query_catalog").QUERY_CATALOG
    HANDLERS = importlib.import_module("app.queries").HANDLERS
finally:
    sys.path.remove(SERVICE_PATH)
    for name in tuple(sys.modules):
        if name == "app" or name.startswith("app."):
            del sys.modules[name]


def main() -> int:
    published = {entry["intent"] for entry in QUERY_CATALOG}
    implemented = set(HANDLERS)
    if published != implemented:
        print("FALLO: el catalogo y los manejadores no coinciden")
        print("Sin manejador:", sorted(published - implemented))
        print("Sin entrada de catalogo:", sorted(implemented - published))
        return 1
    print(f"RESULTADO: OK - {len(published)} intenciones catalogadas y ejecutables")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
