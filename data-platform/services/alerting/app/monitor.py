"""Vista de monitoreo: pipeline, calidad, modelo y estado de notificaciones."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .clients import CoreApi, MlApi, ServiceError
from .store import AlertStore


def snapshot(store: AlertStore, core: CoreApi, ml: MlApi) -> dict[str, Any]:
    monitoreo = core.monitor()
    try:
        modelo = ml.model()
    except ServiceError as exc:
        modelo = {"status": "unavailable", "message": str(exc)}

    ultimo = monitoreo.get("last_etl") or {}
    stats = store.stats()
    recientes = store.list(limit=10)

    return {
        "generado_en": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pipeline": {
            "data_updated_at": monitoreo.get("data_updated_at"),
            "fact_rows": monitoreo.get("fact_rows"),
            "ultima_carga": {
                "execution_id": ultimo.get("execution_id"),
                "pipeline": ultimo.get("pipeline_name"),
                "estado": ultimo.get("status"),
                "fin": ultimo.get("end_time"),
                "filas_leidas": ultimo.get("rows_read"),
                "filas_rechazadas": ultimo.get("rows_rejected"),
                "error": ultimo.get("error_detail"),
            }
            if ultimo
            else None,
            "ejecuciones_24h": monitoreo.get("etl_runs_24h"),
            "fallas_24h": monitoreo.get("etl_failures_24h"),
            "rechazos_total": monitoreo.get("rejected_total"),
            "rechazos_abiertos": monitoreo.get("rejected_open"),
            "rechazos_por_regla": monitoreo.get("rejected_by_rule", []),
            "fallas_recientes": monitoreo.get("recent_failures", []),
        },
        "modelo": {
            "estado": modelo.get("status"),
            "version": modelo.get("version"),
            "mae": (modelo.get("metrics") or {}).get("mae"),
            "rmse": (modelo.get("metrics") or {}).get("rmse"),
            "mae_baseline": (modelo.get("baseline") or {}).get("mae"),
            "periodos_train": modelo.get("train_periods"),
            "periodos_test": modelo.get("test_periods"),
            "mensaje": modelo.get("message"),
        },
        "notificaciones": stats,
        "ultimas_alertas": recientes,
    }
