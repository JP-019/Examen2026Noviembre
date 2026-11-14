"""Configuracion del motor de alertas.

Las metricas se leen de core-api y del servicio ML. El registro operativo de
alertas vive en un SQLite local (no en SQL Server).
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PLATFORM_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PLATFORM_ROOT / ".env")

CORE_API_URL = os.getenv("CORE_API_URL", "http://localhost:8000")
ML_URL = os.getenv("ML_URL", "http://localhost:8002")
HTTP_TIMEOUT = float(os.getenv("ALERT_HTTP_TIMEOUT", "10"))

ALERT_DB_PATH = Path(
    os.getenv(
        "ALERT_DB_PATH",
        str(Path(__file__).resolve().parents[1] / "data" / "alerts.db"),
    )
)

# Umbrales de las reglas (configurables por .env).
VENTAS_MIN = float(os.getenv("ALERT_VENTAS_MIN", "1000"))
TICKET_MIN = float(os.getenv("ALERT_TICKET_MIN", "200"))
CAIDA_PCT = float(os.getenv("ALERT_CAIDA_PCT", "15"))
MAE_MAX = float(os.getenv("ALERT_MAE_MAX", "500"))
RECHAZOS_MAX = int(os.getenv("ALERT_RECHAZOS_MAX", "10"))
ML_PERIODOS_MIN = int(os.getenv("ML_MIN_TRAIN_PERIODS", "6")) + int(
    os.getenv("ML_MIN_TEST_PERIODS", "2")
)
