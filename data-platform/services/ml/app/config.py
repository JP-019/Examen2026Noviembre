"""Configuracion del servicio de Machine Learning.

Solo lee del Data Warehouse y guarda artefactos locales versionados.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PLATFORM_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PLATFORM_ROOT / ".env")

ARTIFACTS_DIR = Path(
    os.getenv("ML_ARTIFACTS_DIR", str(Path(__file__).resolve().parents[1] / "artifacts"))
)
MODEL_PATH = ARTIFACTS_DIR / "model.joblib"
METADATA_PATH = ARTIFACTS_DIR / "model.json"

# Minimos para que una evaluacion temporal tenga sentido. Con menos periodos
# el servicio informa "datos insuficientes" en lugar de inventar metricas.
MIN_TRAIN_PERIODS = int(os.getenv("ML_MIN_TRAIN_PERIODS", "6"))
MIN_TEST_PERIODS = int(os.getenv("ML_MIN_TEST_PERIODS", "2"))
TEST_FRACTION = float(os.getenv("ML_TEST_FRACTION", "0.25"))


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
    user: str | None
    password: str | None

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
