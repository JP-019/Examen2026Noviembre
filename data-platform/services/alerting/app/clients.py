"""Clientes HTTP del motor de alertas.

Las metricas de negocio salen de core-api; el estado del modelo, del servicio ML.
Ningun cliente abre conexion a SQL Server.
"""

from __future__ import annotations

from typing import Any

import requests

from .config import CORE_API_URL, HTTP_TIMEOUT, ML_URL


class ServiceError(RuntimeError):
    """Servicio externo caido o respuesta invalida."""


def _get(base: str, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    clean = {k: v for k, v in (params or {}).items() if v not in (None, "")}
    try:
        response = requests.get(f"{base.rstrip('/')}{path}", params=clean, timeout=HTTP_TIMEOUT)
    except requests.RequestException as exc:
        raise ServiceError(f"No se pudo conectar con {base}: {exc}") from exc
    if response.status_code >= 400:
        raise ServiceError(f"{base}{path} devolvio {response.status_code}: {response.text[:200]}")
    return response.json()


class CoreApi:
    def __init__(self, base: str | None = None) -> None:
        self.base = base or CORE_API_URL

    def health(self) -> dict[str, Any]:
        return _get(self.base, "/api/v1/health")

    def filtros(self) -> dict[str, Any]:
        return _get(self.base, "/api/v1/filtros")

    def kpis(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return _get(self.base, "/api/v1/kpis", params)

    def tendencias(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return _get(self.base, "/api/v1/tendencias", {**(params or {}), "granularidad": "mes"})

    def monitor(self) -> dict[str, Any]:
        return _get(self.base, "/api/v1/monitor")


class MlApi:
    def __init__(self, base: str | None = None) -> None:
        self.base = base or ML_URL

    def model(self) -> dict[str, Any]:
        return _get(self.base, "/model")
