"""Cliente HTTP del dashboard.

El dashboard **nunca** abre una conexion a SQL Server: solo habla con core-api.
"""

from __future__ import annotations

import os
from typing import Any

import requests

DEFAULT_BASE = os.getenv("CORE_API_URL", "http://localhost:8000")
TIMEOUT = float(os.getenv("DASHBOARD_HTTP_TIMEOUT", "10"))


class ApiError(RuntimeError):
    """Error de comunicacion o de negocio devuelto por core-api."""


class CoreApi:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or os.getenv("CORE_API_URL", DEFAULT_BASE)).rstrip("/")

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        clean = {k: v for k, v in (params or {}).items() if v not in (None, "")}
        try:
            response = requests.get(f"{self.base_url}{path}", params=clean, timeout=TIMEOUT)
        except requests.RequestException as exc:
            raise ApiError(
                f"No se pudo conectar con la API en {self.base_url}. "
                "Verificar que core-api este corriendo."
            ) from exc
        if response.status_code >= 500:
            raise ApiError(f"La API devolvio {response.status_code}: {response.text[:200]}")
        if response.status_code >= 400:
            detail = "Error de validacion"
            try:
                detail = response.json().get("detail", detail)
            except ValueError:
                pass
            raise ApiError(f"La API rechazo la solicitud: {detail}")
        return response.json()

    def health(self) -> dict[str, Any]:
        return self._get("/api/v1/health")

    def filtros(self) -> dict[str, Any]:
        return self._get("/api/v1/filtros")

    def kpis(self, filtros: dict[str, Any]) -> dict[str, Any]:
        return self._get("/api/v1/kpis", filtros)

    def tendencias(self, filtros: dict[str, Any], granularidad: str = "mes") -> dict[str, Any]:
        return self._get("/api/v1/tendencias", {**filtros, "granularidad": granularidad})

    def detalle(self, filtros: dict[str, Any], page: int, page_size: int) -> dict[str, Any]:
        return self._get("/api/v1/detalle", {**filtros, "page": page, "page_size": page_size})

    def agrupado(self, filtros: dict[str, Any], dimension: str) -> dict[str, Any]:
        return self._get("/api/v1/agrupado", {**filtros, "dimension": dimension})
