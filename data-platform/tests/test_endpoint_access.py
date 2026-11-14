"""Verifica que los servicios HTTP sensibles solo acepten clientes locales."""

from __future__ import annotations

import asyncio
import importlib
import os
import sys
import tempfile
from collections.abc import Awaitable, Callable
from pathlib import Path

from starlette.requests import Request
from starlette.responses import Response

ROOT = Path(__file__).resolve().parents[1]
SERVICES = ("core-api", "ml", "genai", "alerting")
MiddlewareHandler = Callable[
    [Request, Callable[[Request], Awaitable[Response]]],
    Awaitable[Response],
]


def load_middleware(service: str) -> MiddlewareHandler:
    service_path = str(ROOT / "services" / service)
    sys.path.insert(0, service_path)
    try:
        for name in tuple(sys.modules):
            if name == "app" or name.startswith("app."):
                del sys.modules[name]
        module = importlib.import_module("app.main")
        return module.local_access_only
    finally:
        sys.path.remove(service_path)
        for name in tuple(sys.modules):
            if name == "app" or name.startswith("app."):
                del sys.modules[name]


async def continue_request(_request: Request) -> Response:
    return Response(status_code=204)


def main() -> int:
    failures = 0
    original_alert_db = os.environ.get("ALERT_DB_PATH")
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            os.environ["ALERT_DB_PATH"] = str(Path(temp_dir) / "alerts.db")

            for service in SERVICES:
                middleware = load_middleware(service)
                for host, expected in (
                    ("127.0.0.1", 204),
                    ("::1", 204),
                    ("192.0.2.10", 403),
                    ("not-an-ip", 403),
                ):
                    request = Request({"type": "http", "client": (host, 12345)})
                    response = asyncio.run(middleware(request, continue_request))
                    passed = response.status_code == expected
                    print(
                        f"{service:<10} {host:<15} esperado={expected} "
                        f"obtenido={response.status_code} {'OK' if passed else 'FALLO'}"
                    )
                    failures += not passed
    finally:
        if original_alert_db is None:
            os.environ.pop("ALERT_DB_PATH", None)
        else:
            os.environ["ALERT_DB_PATH"] = original_alert_db

    print("RESULTADO:", "OK" if not failures else f"{failures} fallos")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
