"""Configuracion del servicio ETL.

Lee variables de entorno (.env en la raiz de data-platform) y expone
las conexiones a la fuente y a la plataforma. Sin credenciales en codigo.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# services/etl/app/config.py -> data-platform
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
class DbConfig:
    server: str
    database: str
    driver: str
    trusted: bool
    trust_cert: bool
    user: str | None = None
    password: str | None = None

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


SOURCE = DbConfig(
    server=os.getenv("SOURCE_SERVER", "localhost"),
    database=os.getenv("SOURCE_DATABASE", "Venta"),
    driver=os.getenv("SOURCE_DRIVER", "ODBC Driver 18 for SQL Server"),
    trusted=_flag("SOURCE_TRUSTED_CONNECTION"),
    trust_cert=_trust_server_certificate(
        "SOURCE_TRUST_SERVER_CERTIFICATE",
        os.getenv("SOURCE_SERVER", "localhost"),
    ),
    user=os.getenv("SOURCE_USER") or None,
    password=os.getenv("SOURCE_PASSWORD") or None,
)

DW = DbConfig(
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
)

OVERLAP_DAYS = int(os.getenv("ETL_OVERLAP_DAYS", "1"))
BATCH_SIZE = int(os.getenv("ETL_BATCH_SIZE", "1000"))
LOG_LEVEL = os.getenv("ETL_LOG_LEVEL", "INFO").upper()
