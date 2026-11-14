"""Configuracion del servicio core-api.

Lee `.env` desde la raiz de data-platform y expone la conexion de solo lectura
al Data Warehouse. Sin credenciales en codigo.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PLATFORM_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PLATFORM_ROOT / ".env")


def _flag(name: str, default: str = "yes") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "yes", "true", "y", "si"}


def _trust_server_certificate(name: str, server: str) -> bool:
    value = os.getenv(name, "auto").strip().lower()
    if value == "auto":
        return server.strip().lower() in {"localhost", "127.0.0.1", "::1"}
    return value in {"1", "yes", "true", "y", "si"}


@dataclass(frozen=True)
class Settings:
    server: str
    database: str
    driver: str
    trusted: bool
    trust_cert: bool
    user: str | None
    password: str | None
    max_page_size: int
    service_name: str = "core-api"

    def connection_string(self) -> str:
        parts = [
            f"DRIVER={{{self.driver}}}",
            f"SERVER={self.server}",
            f"DATABASE={self.database}",
            "Encrypt=yes",
        ]
        if self.trusted:
            parts.append("Trusted_Connection=yes")
        else:
            parts.append(f"UID={self.user}")
            parts.append(f"PWD={self.password}")
        if self.trust_cert:
            parts.append("TrustServerCertificate=yes")
        return ";".join(parts) + ";"


settings = Settings(
    server=os.getenv("DW_SERVER", "localhost"),
    database=os.getenv("DW_DATABASE", "DataPlatform"),
    driver=os.getenv("DW_DRIVER", "ODBC Driver 18 for SQL Server"),
    trusted=_flag("DW_TRUSTED_CONNECTION"),
    trust_cert=_trust_server_certificate(
        "DW_TRUST_SERVER_CERTIFICATE",
        os.getenv("DW_SERVER", "localhost"),
    ),
    user=os.getenv("DW_USER") or None,
    password=os.getenv("DW_PASSWORD") or None,
    max_page_size=int(os.getenv("CORE_API_MAX_PAGE_SIZE", "200")),
)
