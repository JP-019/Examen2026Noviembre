"""Cliente HTTP para conversaciones generales con Ollama local."""

from __future__ import annotations

import os
import unicodedata
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

DEFAULT_BASE = os.getenv("OLLAMA_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
TIMEOUT = float(os.getenv("OLLAMA_HTTP_TIMEOUT", "60"))

SYSTEM_PROMPT = (
    "Eres un asistente virtual general del dashboard y respondes en español. "
    "No tienes acceso a ventas, facturas, clientes, inventario ni datos internos. "
    "No inventes cifras ni hechos del negocio; si te preguntan por ellos, indica "
    "que debes usar el asistente de ventas conectado a datos verificados. "
    "Responde de forma clara y concisa."
)
SALES_TERMS = (
    "venta",
    "vend",
    "sales",
    "sold",
    "revenue",
    "factura",
    "ticket",
    "recaud",
    "soles",
    "s/",
    "producto",
    "seccion",
    "importe",
    "monto",
    "unidad",
    "kpi",
    "ganancia",
    "ingreso",
    "por local",
)


class OllamaClientError(RuntimeError):
    """Error de comunicacion, respuesta o modelo de Ollama."""


class OllamaClient:
    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = TIMEOUT,
    ) -> None:
        self.base_url = (base_url or os.getenv("OLLAMA_URL", DEFAULT_BASE)).rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL", DEFAULT_MODEL)
        self.timeout = timeout

    def ask(
        self,
        question: str,
        history: list[dict[str, str]] | None = None,
    ) -> str:
        question = question.strip()
        if not question or len(question) > 500:
            raise OllamaClientError("La pregunta debe tener entre 1 y 500 caracteres.")
        normalized = "".join(
            character
            for character in unicodedata.normalize("NFKD", question.casefold())
            if not unicodedata.combining(character)
        )
        if any(term in normalized for term in SALES_TERMS):
            raise OllamaClientError(
                "Para preguntas de ventas, cambia al modo «Ventas verificadas»."
            )

        messages: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
        if history:
            messages.extend(history[-6:])
        messages.append({"role": "user", "content": question})

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={"model": self.model, "messages": messages, "stream": False},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise OllamaClientError(
                f"No se pudo conectar con Ollama en {self.base_url}. "
                "Verifica que esté iniciado y que el modelo esté descargado."
            ) from exc

        if response.status_code == 404:
            raise OllamaClientError(
                f"No se encontró el modelo '{self.model}'. "
                f"Descárgalo con `ollama pull {self.model}`."
            )
        if response.status_code >= 400:
            detail = response.text[:200]
            raise OllamaClientError(f"Ollama devolvió {response.status_code}: {detail}")

        try:
            payload: Any = response.json()
        except ValueError as exc:
            raise OllamaClientError("Ollama devolvió una respuesta que no es JSON válido.") from exc

        message = payload.get("message") if isinstance(payload, dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str) or not content.strip():
            raise OllamaClientError("Ollama devolvió una respuesta con formato inesperado.")
        return content.strip()
