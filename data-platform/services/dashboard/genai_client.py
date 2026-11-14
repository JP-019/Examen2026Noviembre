"""Cliente HTTP del asistente GenAI para la interfaz del dashboard."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

DEFAULT_BASE = os.getenv("GENAI_URL", "http://localhost:8003")
TIMEOUT = float(os.getenv("GENAI_HTTP_TIMEOUT", "10"))


class GenAiClientError(RuntimeError):
    """Error de comunicacion, respuesta o negocio del asistente."""


class GenAiClient:
    def __init__(self, base_url: str | None = None, timeout: float = TIMEOUT) -> None:
        self.base_url = (base_url or os.getenv("GENAI_URL", DEFAULT_BASE)).rstrip("/")
        self.timeout = timeout

    def ask(self, question: str) -> dict[str, Any]:
        try:
            response = requests.post(
                f"{self.base_url}/ask",
                json={"pregunta": question},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise GenAiClientError(
                f"No se pudo conectar con GenAI en {self.base_url}. "
                "Verifica que el servicio esté iniciado."
            ) from exc

        if response.status_code >= 400:
            detail = response.text[:200]
            try:
                error_payload = response.json()
            except ValueError:
                pass
            else:
                if isinstance(error_payload, dict):
                    detail = str(error_payload.get("detail", detail))[:200]
            raise GenAiClientError(f"GenAI devolvió {response.status_code}: {detail}")

        try:
            payload = response.json()
        except ValueError as exc:
            raise GenAiClientError("GenAI devolvió una respuesta que no es JSON válido.") from exc

        if (
            not isinstance(payload, dict)
            or not isinstance(payload.get("respuesta"), str)
            or not isinstance(payload.get("grounded"), bool)
            or not isinstance(payload.get("fuentes"), list)
        ):
            raise GenAiClientError("GenAI devolvió una respuesta con formato inesperado.")
        return payload
