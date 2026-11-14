"""Cliente HTTP del asistente. Solo habla con core-api; no ejecuta SQL."""

from __future__ import annotations

import os
from typing import Any

import requests

DEFAULT_BASE = os.getenv("CORE_API_URL", "http://localhost:8000")
TIMEOUT = float(os.getenv("GENAI_HTTP_TIMEOUT", "10"))


class ApiError(RuntimeError):
    pass


class CoreApi:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or os.getenv("CORE_API_URL", DEFAULT_BASE)).rstrip("/")

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        clean = {k: v for k, v in (params or {}).items() if v not in (None, "")}
        try:
            response = requests.get(f"{self.base_url}{path}", params=clean, timeout=TIMEOUT)
        except requests.RequestException as exc:
            raise ApiError(
                f"No se pudo conectar con core-api en {self.base_url}. "
                "El asistente no responde sin datos verificables."
            ) from exc
        if response.status_code >= 400:
            raise ApiError(f"core-api devolvio {response.status_code}: {response.text[:200]}")
        return response.json()

    def health(self) -> dict[str, Any]:
        return self._get("/api/v1/health")

    def filtros(self) -> dict[str, Any]:
        return self._get("/api/v1/filtros")

    def kpis(self, filtros: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._get("/api/v1/kpis", filtros)

    def tendencias(self, filtros: dict[str, Any] | None = None, granularidad: str = "mes") -> dict[str, Any]:
        return self._get("/api/v1/tendencias", {**(filtros or {}), "granularidad": granularidad})

    def detalle(self, filtros: dict[str, Any] | None = None, page: int = 1, page_size: int = 10) -> dict[str, Any]:
        return self._get("/api/v1/detalle", {**(filtros or {}), "page": page, "page_size": page_size})

    def agrupado(self, filtros: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._get("/api/v1/agrupado", filtros or {})
