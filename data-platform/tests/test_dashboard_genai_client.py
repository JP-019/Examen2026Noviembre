"""Pruebas del cliente HTTP usado por el chat de ventas."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "dashboard"))

from genai_client import GenAiClient, GenAiClientError  # noqa: E402


class GenAiClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = GenAiClient("http://genai.test", timeout=2)

    @patch("genai_client.requests.post")
    def test_sends_question_and_returns_grounded_sources(self, post: Mock) -> None:
        response = post.return_value
        response.status_code = 200
        response.json.return_value = {
            "respuesta": "Las ventas totalizaron S/ 696.40.",
            "grounded": True,
            "fuentes": [{"servicio": "core-api", "endpoint": "/api/v1/kpis"}],
        }

        result = self.client.ask("ventas por local")

        self.assertTrue(result["grounded"])
        self.assertEqual(len(result["fuentes"]), 1)
        post.assert_called_once_with(
            "http://genai.test/ask",
            json={"pregunta": "ventas por local"},
            timeout=2,
        )

    @patch("genai_client.requests.post")
    def test_reports_api_validation_error(self, post: Mock) -> None:
        response = post.return_value
        response.status_code = 422
        response.text = '{"detail":"pregunta demasiado corta"}'
        response.json.return_value = {"detail": "pregunta demasiado corta"}

        with self.assertRaisesRegex(GenAiClientError, "422"):
            self.client.ask("x")

    @patch("genai_client.requests.post")
    def test_reports_unavailable_genai_service(self, post: Mock) -> None:
        post.side_effect = requests.ConnectionError("offline")

        with self.assertRaisesRegex(GenAiClientError, "No se pudo conectar con GenAI"):
            self.client.ask("ventas por local")

    @patch("genai_client.requests.post")
    def test_rejects_unexpected_response_shape(self, post: Mock) -> None:
        response = post.return_value
        response.status_code = 200
        response.json.return_value = {"respuesta": "Falta el estado grounded."}

        with self.assertRaisesRegex(GenAiClientError, "formato inesperado"):
            self.client.ask("ventas por local")


if __name__ == "__main__":
    unittest.main()
