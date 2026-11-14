"""Verifica que la confianza automatica solo permita certificados locales."""

from __future__ import annotations

import importlib
import os
import sys
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICES = ("core-api", "ml", "etl")
TrustServerCertificateCheck = Callable[[str, str], bool]


def load_trust_helper(service: str) -> TrustServerCertificateCheck:
    service_path = str(ROOT / "services" / service)
    sys.path.insert(0, service_path)
    try:
        for name in tuple(sys.modules):
            if name == "app" or name.startswith("app."):
                del sys.modules[name]
        module = importlib.import_module("app.config")
        return module._trust_server_certificate
    finally:
        sys.path.remove(service_path)
        for name in tuple(sys.modules):
            if name == "app" or name.startswith("app."):
                del sys.modules[name]


def main() -> int:
    failures = 0
    variable = "TEST_TLS_TRUST_SERVER_CERTIFICATE"
    original_value = os.environ.get(variable)

    try:
        for service in SERVICES:
            trust = load_trust_helper(service)
            for value, server, expected in (
                ("auto", "localhost", True),
                ("auto", "db.example.com", False),
                ("yes", "db.example.com", True),
                ("no", "localhost", False),
            ):
                os.environ[variable] = value
                obtained = trust(variable, server)
                passed = obtained is expected
                print(
                    f"{service:<10} modo={value:<4} servidor={server:<15} "
                    f"esperado={expected} obtenido={obtained} {'OK' if passed else 'FALLO'}"
                )
                failures += not passed
    finally:
        if original_value is None:
            os.environ.pop(variable, None)
        else:
            os.environ[variable] = original_value

    print("RESULTADO:", "OK" if not failures else f"{failures} fallos")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
